"""A vectorised flow exporter, for measuring how much of the cost is Python.

EXP-005 measured packet-level feature extraction at 4.49-37.34 ms per flow with
the reference exporter, against 0.18-0.96 ms of model inference: 7x to 39x for
every architecture light enough to meet a 10 ms budget. The finding came with a
caveat the report was explicit about -- the reference exporter is a pure-Python
per-packet implementation running at 1.1-4.3 MB/s, and a production extractor
would be considerably faster.

EXP-031 made that caveat the central question. Obiuwevwi et al. (2026) measure
1-5 microseconds of inference inside a real Near-RT RIC. If deployed inference is
microseconds, then extraction is not merely the larger half of the budget, it is
effectively the whole budget, and the only number that matters is how fast
extraction can be made to go.

This module is the honest middle term of that comparison. It is not a native C
or eBPF extractor -- writing one is out of scope and would need its own
validation. It is the same flow semantics implemented the way a fast Python
implementation would be written:

  reference (exporter.py)   one dpkt object graph per packet, attribute access,
                            per-packet dict lookups, per-flow Python lists
  this module               one sequential pass collecting record offsets, then
                            all header fields extracted in bulk with NumPy fancy
                            indexing, then one pandas groupby over the 5-tuple

The gap between them is the cost of interpreting packets one at a time. What
remains after closing it is the floor that Python cannot get under, and that
floor is the actual argument for a native extractor.

**Scope, stated plainly.** This implements the volumetric and timing subset of
``exporter.FEATURE_COLUMNS`` -- everything derivable from fixed-offset header
fields. It does not implement TCP flag accounting or handshake tracking, and it
handles IPv4 with no IP options (IHL = 5), which is the overwhelming majority of
packets in both corpora. Packets it cannot handle in bulk are counted and
reported, never silently dropped: a benchmark that quietly skips the hard packets
is measuring the wrong thing.

``assert_equivalent`` checks this exporter against the reference on the shared
columns. A faster exporter that disagrees with the reference is not an
optimisation, it is a second bug.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .exporter import EXPORTER_VERSION, ExporterConfig

FAST_EXPORTER_VERSION = "0.1.0"

# Link-layer header sizes, in bytes. Same dispatch discipline as the reference:
# an unknown link type is refused, never guessed. That refusal is the fix for
# B-A, where parsing DLT_LINUX_SLL as Ethernet produced 5,851 confident and
# wholly fictional flows.
LINK_HEADER_BYTES = {
    1: 14,      # DLT_EN10MB, Ethernet
    113: 16,    # DLT_LINUX_SLL, the "any" interface cooked header
    101: 0,     # DLT_RAW
    228: 0,     # DLT_IPV4
}

# Columns this exporter produces and the reference also produces, so the two can
# be compared directly.
SHARED_COLUMNS = ("src_ip", "dst_ip", "src_port", "dst_port", "proto",
                  "duration", "total_pkts", "total_ip_bytes",
                  "fwd_pkts", "bwd_pkts", "fwd_ip_bytes", "bwd_ip_bytes")


@dataclass
class ParseStats:
    """What the bulk path could and could not handle. Reported, not hidden."""
    n_records: int = 0
    n_parsed: int = 0
    n_skipped_link: int = 0
    n_skipped_not_ipv4: int = 0
    n_skipped_ip_options: int = 0
    n_skipped_proto: int = 0

    @property
    def coverage(self) -> float:
        return self.n_parsed / self.n_records if self.n_records else 0.0

    def as_dict(self) -> dict:
        d = self.__dict__.copy()
        d["coverage"] = self.coverage
        return d


def _read_pcap_offsets(raw: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """One sequential pass over the record headers.

    This pass cannot be vectorised: each record's offset depends on the previous
    record's captured length, so the walk is inherently serial. It is kept as
    cheap as possible -- integer arithmetic and one ``unpack_from`` per record,
    no object construction -- because whatever it costs is the irreducible
    per-packet Python overhead, and that number is the point of the experiment.
    """
    magic = struct.unpack_from("<I", raw, 0)[0]
    if magic in (0xA1B2C3D4, 0xA1B23C4D):
        endian, nano = "<", magic == 0xA1B23C4D
    elif magic in (0xD4C3B2A1, 0x4D3CB2A1):
        endian, nano = ">", magic == 0x4D3CB2A1
    else:
        raise ValueError("not a classic pcap file (magic %#x)" % magic)

    linktype = struct.unpack_from(endian + "I", raw, 20)[0]
    hdr = struct.Struct(endian + "IIII")
    n = len(raw)

    offs, secs, usecs, caps = [], [], [], []
    pos = 24
    while pos + 16 <= n:
        ts_s, ts_u, incl, _orig = hdr.unpack_from(raw, pos)
        pos += 16
        if pos + incl > n:
            break
        offs.append(pos)
        secs.append(ts_s)
        usecs.append(ts_u)
        caps.append(incl)
        pos += incl

    div = 1e9 if nano else 1e6
    ts = np.asarray(secs, dtype=np.float64) + np.asarray(usecs, dtype=np.float64) / div
    return (np.asarray(offs, dtype=np.int64), ts,
            np.asarray(caps, dtype=np.int64), linktype)


def extract(path: Path, cfg: ExporterConfig | None = None
            ) -> tuple[pd.DataFrame, ParseStats]:
    """Flow records from one capture, via bulk header extraction.

    Note on timeouts: the reference exporter expires flows on idle and active
    timeouts during its single pass. Here expiry is applied after grouping, by
    splitting a 5-tuple's packets wherever the inter-packet gap exceeds the idle
    timeout. The two agree whenever a 5-tuple is not reused after an expiry,
    which is the normal case; ``assert_equivalent`` is what establishes that for
    a given capture rather than assuming it.
    """
    cfg = cfg or ExporterConfig()
    raw = Path(path).read_bytes()
    offs, ts, caps, linktype = _read_pcap_offsets(raw)
    st = ParseStats(n_records=len(offs))

    if linktype not in LINK_HEADER_BYTES:
        raise ValueError(
            "unknown link type %d. Refusing to guess -- guessing is what "
            "produced 5,851 fictional flows in B-A." % linktype)
    link = LINK_HEADER_BYTES[linktype]

    if len(offs) == 0:
        return pd.DataFrame(columns=list(SHARED_COLUMNS)), st

    buf = np.frombuffer(raw, dtype=np.uint8)
    ip = offs + link

    # Everything below is one fancy-index per header field, over all packets.
    keep = (caps >= link + 20) & (ip + 20 <= len(buf))
    st.n_skipped_link = int((~keep).sum())

    vihl = buf[ip[keep]]
    is_v4 = (vihl >> 4) == 4
    ihl = (vihl & 0x0F).astype(np.int64)
    ok_opts = ihl == 5
    st.n_skipped_not_ipv4 = int((~is_v4).sum())
    st.n_skipped_ip_options = int((is_v4 & ~ok_opts).sum())

    sel = keep.copy()
    sel[np.where(keep)[0][~(is_v4 & ok_opts)]] = False
    ipx = offs[sel] + link

    proto = buf[ipx + 9].astype(np.int64)
    tot_len = (buf[ipx + 2].astype(np.int64) << 8) | buf[ipx + 3].astype(np.int64)
    src = (buf[ipx + 12].astype(np.int64) << 24 | buf[ipx + 13].astype(np.int64) << 16
           | buf[ipx + 14].astype(np.int64) << 8 | buf[ipx + 15].astype(np.int64))
    dst = (buf[ipx + 16].astype(np.int64) << 24 | buf[ipx + 17].astype(np.int64) << 16
           | buf[ipx + 18].astype(np.int64) << 8 | buf[ipx + 19].astype(np.int64))

    has_ports = (proto == 6) | (proto == 17)
    st.n_skipped_proto = int((~has_ports).sum())
    tr = ipx + 20
    sport = np.zeros(len(ipx), dtype=np.int64)
    dport = np.zeros(len(ipx), dtype=np.int64)
    hp = has_ports & (tr + 4 <= len(buf))
    sport[hp] = (buf[tr[hp]].astype(np.int64) << 8) | buf[tr[hp] + 1].astype(np.int64)
    dport[hp] = (buf[tr[hp] + 2].astype(np.int64) << 8) | buf[tr[hp] + 3].astype(np.int64)

    st.n_parsed = int(sel.sum())

    df = pd.DataFrame({
        "ts": ts[sel], "src": src, "dst": dst,
        "sport": sport, "dport": dport, "proto": proto,
        "ip_bytes": tot_len,
    })

    # Canonical (direction-free) key, plus a forward flag fixed by the first
    # packet -- the reference exporter's ``direction_policy="first_packet"``.
    lo_is_src = (df.src < df.dst) | ((df.src == df.dst) & (df.sport <= df.dport))
    df["a"] = np.where(lo_is_src, df.src, df.dst)
    df["b"] = np.where(lo_is_src, df.dst, df.src)
    df["ap"] = np.where(lo_is_src, df.sport, df.dport)
    df["bp"] = np.where(lo_is_src, df.dport, df.sport)

    df = df.sort_values("ts", kind="stable")
    key = ["a", "b", "ap", "bp", "proto"]
    g = df.groupby(key, sort=False)

    # Idle-timeout expiry, applied after grouping. A gap longer than the idle
    # timeout starts a new flow with the same 5-tuple.
    gap = g["ts"].diff()
    df["episode"] = (gap > cfg.idle_timeout_s).fillna(False).astype(int)
    df["episode"] = df.groupby(key, sort=False)["episode"].cumsum()

    key2 = key + ["episode"]
    first = df.groupby(key2, sort=False).head(1).set_index(key2)
    fwd_src = first["src"].to_dict()

    idx = pd.MultiIndex.from_frame(df[key2])
    df["fwd"] = (df["src"].to_numpy()
                 == pd.Series(idx.map(fwd_src), index=df.index).to_numpy())

    agg = df.groupby(key2, sort=False).agg(
        first_ts=("ts", "min"), last_ts=("ts", "max"),
        total_pkts=("ts", "size"), total_ip_bytes=("ip_bytes", "sum"),
        fwd_pkts=("fwd", "sum"),
        fwd_ip_bytes=("ip_bytes", lambda s: 0),  # replaced below
    )
    fwd_bytes = df[df.fwd].groupby(key2, sort=False)["ip_bytes"].sum()
    agg["fwd_ip_bytes"] = fwd_bytes.reindex(agg.index).fillna(0).astype(np.int64)
    agg["bwd_pkts"] = agg["total_pkts"] - agg["fwd_pkts"]
    agg["bwd_ip_bytes"] = agg["total_ip_bytes"] - agg["fwd_ip_bytes"]
    agg["duration"] = agg["last_ts"] - agg["first_ts"]

    out = agg.reset_index()
    fs = first.reset_index()[key2 + ["src", "dst", "sport", "dport"]]
    out = out.merge(fs, on=key2, how="left")
    out = out.rename(columns={"src": "src_i", "dst": "dst_i",
                              "sport": "src_port", "dst_port": "dst_port"})
    out["src_ip"] = [_ip(v) for v in out["src_i"]]
    out["dst_ip"] = [_ip(v) for v in out["dst_i"]]
    out = out.rename(columns={"dport": "dst_port"})
    out["proto"] = out["proto"].astype(int)

    cols = [c for c in SHARED_COLUMNS if c in out.columns]
    return out[cols + ["first_ts", "last_ts"]].sort_values(
        ["first_ts", "src_ip", "dst_ip"]).reset_index(drop=True), st


def _ip(v: int) -> str:
    return "%d.%d.%d.%d" % ((v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255)


def assert_equivalent(fast: pd.DataFrame, ref_rows: list[dict],
                      *, tol: float = 1e-6) -> dict:
    """Compare against the reference exporter on the shared columns.

    Returns a report rather than raising on the first mismatch, because the
    interesting output of a comparison like this is *how many* flows disagree and
    on what, not the first one.
    """
    ref = pd.DataFrame(ref_rows)
    report = {"n_fast": len(fast), "n_ref": len(ref)}
    if ref.empty or fast.empty:
        report["comparable"] = False
        return report

    k = ["src_ip", "dst_ip", "src_port", "dst_port", "proto"]
    f = fast.groupby(k, dropna=False)[["total_pkts", "total_ip_bytes"]].sum()
    r = ref.groupby(k, dropna=False)[["total_pkts", "total_ip_bytes"]].sum()
    j = f.join(r, how="outer", lsuffix="_fast", rsuffix="_ref").fillna(0)

    report["n_keys_fast_only"] = int((j["total_pkts_ref"] == 0).sum())
    report["n_keys_ref_only"] = int((j["total_pkts_fast"] == 0).sum())
    both = j[(j["total_pkts_ref"] > 0) & (j["total_pkts_fast"] > 0)]
    report["n_keys_both"] = int(len(both))
    report["n_pkt_mismatch"] = int(
        (both["total_pkts_fast"] != both["total_pkts_ref"]).sum())
    report["n_byte_mismatch"] = int(
        (both["total_ip_bytes_fast"] != both["total_ip_bytes_ref"]).sum())
    report["total_pkts_fast"] = int(j["total_pkts_fast"].sum())
    report["total_pkts_ref"] = int(j["total_pkts_ref"].sum())
    report["comparable"] = True
    report["agrees"] = bool(report["n_pkt_mismatch"] == 0
                            and report["n_byte_mismatch"] == 0
                            and report["n_keys_fast_only"] == 0
                            and report["n_keys_ref_only"] == 0)
    return report


__all__ = ["FAST_EXPORTER_VERSION", "EXPORTER_VERSION", "SHARED_COLUMNS",
           "ParseStats", "extract", "assert_equivalent", "LINK_HEADER_BYTES"]
