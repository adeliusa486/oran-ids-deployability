"""One flow exporter, one pinned version, applied identically to every corpus.

This module exists to remove the confound identified as A3 in
``docs/IMPLEMENTATION_PLAN.md``: if ``D_A`` features come from Zeek and ``D_B``
features come from Argus, then any measured cross-deployment degradation
conflates genuine distribution shift with differences in flow timeout, direction
inference, field semantics and rounding between two exporters. Those are not
separable after the fact.

Everything that could differ between two exporters is therefore a declared
parameter here, and ``EXPORTER_VERSION`` is part of the output manifest. Change
the semantics, change the version, re-extract both corpora. Never mix versions.

Determinism is a requirement, not a nicety: the same input file must produce
byte-identical output. Flows are emitted in a total order that does not depend on
dict iteration, and every float is rounded at a fixed precision.
"""
from __future__ import annotations

import gzip
import hashlib
import math
import socket
import struct
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

# Bump on ANY change to flow keying, timeout handling, direction inference or
# feature definitions. The value lands in the manifest and in every output file.
EXPORTER_VERSION = "1.0.0"

# Rounding applied to every floating-point feature before emission. Without this
# the same computation on two machines can differ in the last bits and break the
# byte-identical-rerun guarantee.
FLOAT_PRECISION = 9

TCP_FLAGS = OrderedDict([
    ("fin", 0x01), ("syn", 0x02), ("rst", 0x04), ("psh", 0x08),
    ("ack", 0x10), ("urg", 0x20), ("ece", 0x40), ("cwr", 0x80),
])


@dataclass(frozen=True)
class ExporterConfig:
    """Every knob that could differ between two flow exporters.

    Defaults mirror ``configs/exporter/default.yaml``. They are repeated here so
    that importing the module without a config file still gives defined
    behaviour, and so that a diff of this file shows the semantics.
    """

    active_timeout_s: float = 120.0
    idle_timeout_s: float = 30.0
    direction_policy: str = "first_packet"   # the only policy implemented
    bidirectional: bool = True
    drop_incomplete_handshakes: bool = False
    # Flows below this packet count are still emitted; the short-flow policy
    # (A12) is applied downstream in features/, not here, so that the drop rate
    # can be reported rather than silently baked in.
    min_packets: int = 1

    def fingerprint(self) -> str:
        """Stable hash of the semantics, for the manifest."""
        payload = "|".join([
            EXPORTER_VERSION,
            f"{self.active_timeout_s:.6f}", f"{self.idle_timeout_s:.6f}",
            self.direction_policy, str(self.bidirectional),
            str(self.drop_incomplete_handshakes), str(self.min_packets),
            f"prec={FLOAT_PRECISION}",
        ])
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


FlowKey = tuple[str, str, int, int, int]  # src, dst, sport, dport, proto


@dataclass
class _Flow:
    """Accumulator for one flow. Direction is fixed by the first packet seen."""

    key: FlowKey
    first_ts: float
    last_ts: float
    # forward = same direction as the first packet
    fwd_pkts: int = 0
    bwd_pkts: int = 0
    fwd_bytes: int = 0          # payload bytes
    bwd_bytes: int = 0
    fwd_ip_bytes: int = 0       # on-wire IP bytes
    bwd_ip_bytes: int = 0
    fwd_ts: list[float] = field(default_factory=list)
    bwd_ts: list[float] = field(default_factory=list)
    pkt_sizes: list[int] = field(default_factory=list)
    ttls: list[int] = field(default_factory=list)
    flag_counts: dict[str, int] = field(default_factory=lambda: {k: 0 for k in TCP_FLAGS})
    saw_syn: bool = False
    saw_synack: bool = False

    def n_packets(self) -> int:
        return self.fwd_pkts + self.bwd_pkts


def _stats(xs: list[float]) -> tuple[float, float, float, float]:
    """mean, population sd, min, max. Empty -> zeros, so the schema is fixed."""
    if not xs:
        return 0.0, 0.0, 0.0, 0.0
    n = len(xs)
    mean = math.fsum(xs) / n
    if n == 1:
        return mean, 0.0, xs[0], xs[0]
    var = math.fsum((x - mean) ** 2 for x in xs) / n
    return mean, math.sqrt(var), min(xs), max(xs)


def _iats(ts: list[float]) -> list[float]:
    return [ts[i] - ts[i - 1] for i in range(1, len(ts))] if len(ts) > 1 else []


# Column order is part of the contract. Downstream code asserts against it.
FEATURE_COLUMNS: tuple[str, ...] = (
    # identity, not features -- carried for grouping and provenance
    "flow_id", "src_ip", "dst_ip", "src_port", "dst_port", "proto",
    "first_ts", "last_ts",
    # volumetric (10)
    "duration", "fwd_pkts", "bwd_pkts", "total_pkts",
    "fwd_bytes", "bwd_bytes", "total_bytes",
    "fwd_ip_bytes", "bwd_ip_bytes", "total_ip_bytes",
    # rates and ratios (4)
    "pkts_per_s", "bytes_per_s", "bytes_ratio", "pkts_ratio",
    # timing (8)
    "iat_mean", "iat_std", "iat_min", "iat_max",
    "fwd_iat_mean", "fwd_iat_std", "bwd_iat_mean", "bwd_iat_std",
    # packet size (4)
    "pkt_size_mean", "pkt_size_std", "pkt_size_min", "pkt_size_max",
    # header (10)
    "ttl_mean", "ttl_std",
    "flag_fin", "flag_syn", "flag_rst", "flag_psh", "flag_ack", "flag_urg",
    "handshake_complete",
)


def _finalise(flow: _Flow, cfg: ExporterConfig) -> dict | None:
    if flow.n_packets() < cfg.min_packets:
        return None
    if cfg.drop_incomplete_handshakes and flow.key[4] == 6 and not flow.saw_synack:
        return None

    src, dst, sport, dport, proto = flow.key
    dur = flow.last_ts - flow.first_ts
    total_pkts = flow.fwd_pkts + flow.bwd_pkts
    total_bytes = flow.fwd_bytes + flow.bwd_bytes
    total_ip = flow.fwd_ip_bytes + flow.bwd_ip_bytes

    all_ts = sorted(flow.fwd_ts + flow.bwd_ts)
    iat_mean, iat_std, iat_min, iat_max = _stats(_iats(all_ts))
    f_mean, f_std, _, _ = _stats(_iats(flow.fwd_ts))
    b_mean, b_std, _, _ = _stats(_iats(flow.bwd_ts))
    ps_mean, ps_std, ps_min, ps_max = _stats([float(x) for x in flow.pkt_sizes])
    ttl_mean, ttl_std, _, _ = _stats([float(x) for x in flow.ttls])

    # Zero-duration flows are real (a single packet), so rates are defined as 0
    # rather than infinite. Stated here because it is exactly the kind of
    # convention that differs silently between exporters.
    per_s = (lambda x: x / dur if dur > 0 else 0.0)

    row = {
        "flow_id": f"{src}|{dst}|{sport}|{dport}|{proto}|{flow.first_ts:.6f}",
        "src_ip": src, "dst_ip": dst, "src_port": sport, "dst_port": dport,
        "proto": proto,
        "first_ts": flow.first_ts, "last_ts": flow.last_ts,
        "duration": dur,
        "fwd_pkts": flow.fwd_pkts, "bwd_pkts": flow.bwd_pkts, "total_pkts": total_pkts,
        "fwd_bytes": flow.fwd_bytes, "bwd_bytes": flow.bwd_bytes, "total_bytes": total_bytes,
        "fwd_ip_bytes": flow.fwd_ip_bytes, "bwd_ip_bytes": flow.bwd_ip_bytes,
        "total_ip_bytes": total_ip,
        "pkts_per_s": per_s(total_pkts), "bytes_per_s": per_s(total_bytes),
        # +1 smoothing keeps the ratio finite for one-directional flows, which
        # are the overwhelming majority under scanning and flooding traffic.
        "bytes_ratio": flow.fwd_bytes / (flow.bwd_bytes + 1.0),
        "pkts_ratio": flow.fwd_pkts / (flow.bwd_pkts + 1.0),
        "iat_mean": iat_mean, "iat_std": iat_std, "iat_min": iat_min, "iat_max": iat_max,
        "fwd_iat_mean": f_mean, "fwd_iat_std": f_std,
        "bwd_iat_mean": b_mean, "bwd_iat_std": b_std,
        "pkt_size_mean": ps_mean, "pkt_size_std": ps_std,
        "pkt_size_min": ps_min, "pkt_size_max": ps_max,
        "ttl_mean": ttl_mean, "ttl_std": ttl_std,
        "flag_fin": flow.flag_counts["fin"], "flag_syn": flow.flag_counts["syn"],
        "flag_rst": flow.flag_counts["rst"], "flag_psh": flow.flag_counts["psh"],
        "flag_ack": flow.flag_counts["ack"], "flag_urg": flow.flag_counts["urg"],
        "handshake_complete": int(flow.saw_syn and flow.saw_synack),
    }
    for k, v in row.items():
        if isinstance(v, float):
            row[k] = round(v, FLOAT_PRECISION)
    return row


def _iter_packets(path: Path) -> Iterator[tuple[float, bytes]]:
    """Yield (timestamp, ethernet frame) from a pcap or pcapng file."""
    import dpkt

    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as fh:
        head = fh.read(4)
        fh.seek(0)
        if head == b"\x0a\x0d\x0d\x0a":
            reader = dpkt.pcapng.Reader(fh)
        else:
            reader = dpkt.pcap.Reader(fh)
        for ts, buf in reader:
            yield float(ts), buf


def export_file(path: Path, cfg: ExporterConfig | None = None) -> list[dict]:
    """Extract flow records from one capture file.

    Emission order is by (first_ts, flow_id), which is total and independent of
    hash iteration order, so two runs over the same file agree byte for byte.
    """
    import dpkt

    cfg = cfg or ExporterConfig()
    if cfg.direction_policy != "first_packet":
        raise ValueError(f"unimplemented direction_policy: {cfg.direction_policy!r}")

    active: dict[FlowKey, _Flow] = {}
    done: list[dict] = []

    def expire(now: float, force: bool = False) -> None:
        for key in [k for k, f in active.items()
                    if force
                    or (now - f.last_ts) > cfg.idle_timeout_s
                    or (now - f.first_ts) > cfg.active_timeout_s]:
            row = _finalise(active.pop(key), cfg)
            if row is not None:
                done.append(row)

    n_seen = 0
    for ts, buf in _iter_packets(path):
        try:
            eth = dpkt.ethernet.Ethernet(buf)
            ip = eth.data
            if not isinstance(ip, (dpkt.ip.IP, dpkt.ip6.IP6)):
                continue
        except Exception:
            continue

        n_seen += 1
        if n_seen % 4096 == 0:
            expire(ts)

        v6 = isinstance(ip, dpkt.ip6.IP6)
        fam = socket.AF_INET6 if v6 else socket.AF_INET
        src = socket.inet_ntop(fam, ip.src)
        dst = socket.inet_ntop(fam, ip.dst)
        proto = ip.nxt if v6 else ip.p
        ttl = ip.hlim if v6 else ip.ttl

        l4 = ip.data
        if isinstance(l4, dpkt.tcp.TCP):
            sport, dport, flags = l4.sport, l4.dport, l4.flags
            payload = len(l4.data)
        elif isinstance(l4, dpkt.udp.UDP):
            sport, dport, flags = l4.sport, l4.dport, 0
            payload = len(l4.data)
        else:
            sport = dport = 0
            flags = 0
            payload = len(bytes(l4)) if l4 else 0

        fwd_key: FlowKey = (src, dst, sport, dport, proto)
        rev_key: FlowKey = (dst, src, dport, sport, proto)

        flow = active.get(fwd_key)
        forward = True
        if flow is None and cfg.bidirectional:
            flow = active.get(rev_key)
            forward = False
        if flow is None:
            flow = _Flow(key=fwd_key, first_ts=ts, last_ts=ts)
            active[fwd_key] = flow
            forward = True
        elif (ts - flow.first_ts) > cfg.active_timeout_s or (ts - flow.last_ts) > cfg.idle_timeout_s:
            row = _finalise(active.pop(flow.key), cfg)
            if row is not None:
                done.append(row)
            flow = _Flow(key=fwd_key, first_ts=ts, last_ts=ts)
            active[fwd_key] = flow
            forward = True

        flow.last_ts = max(flow.last_ts, ts)
        ip_len = len(bytes(ip))
        if forward:
            flow.fwd_pkts += 1
            flow.fwd_bytes += payload
            flow.fwd_ip_bytes += ip_len
            flow.fwd_ts.append(ts)
        else:
            flow.bwd_pkts += 1
            flow.bwd_bytes += payload
            flow.bwd_ip_bytes += ip_len
            flow.bwd_ts.append(ts)
        flow.pkt_sizes.append(ip_len)
        flow.ttls.append(ttl)

        if proto == 6:
            for name, bit in TCP_FLAGS.items():
                if flags & bit:
                    flow.flag_counts[name] += 1
            syn, ack = bool(flags & 0x02), bool(flags & 0x10)
            if syn and not ack:
                flow.saw_syn = True
            if syn and ack:
                flow.saw_synack = True

    expire(0.0, force=True)
    done.sort(key=lambda r: (r["first_ts"], r["flow_id"]))
    return done


__all__ = ["EXPORTER_VERSION", "FEATURE_COLUMNS", "ExporterConfig", "export_file"]
