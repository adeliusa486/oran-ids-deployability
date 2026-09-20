"""Cross-layer windowing and the CU/DU join.

EXP-001 established that ``D_A``'s published *summary* artefacts cannot be
joined: the network CSV carries no time column. EXP-001c works from the raw
per-category archives instead, where both layers do carry absolute timestamps:

    <Category>/Network_Layer/<run>.pcap   packet captures, DLT_LINUX_SLL
    <Category>/Lower_Layer/<run>.txt      JSON lines, epoch-ms timestamps

The **file stem is the run identifier**, which is what makes run-disjoint
splitting possible and is the same unit prior work (Fard et al., IEEE CSR 2026)
calls a "run".

Both layers are projected onto one absolute-time window grid per run, and joined
on the window index. Windows are **non-overlapping** by default; see
``WindowSpec`` for why that differs from prior work.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# The 22 PHY/MAC fields the DU exports. Fixed here so that a corpus that drops
# or renames one is caught at load rather than silently producing NaN features.
RADIO_FIELDS: tuple[str, ...] = (
    "dlBytes", "dlMcs", "dlBler", "ulBytes", "ulMcs", "ulBler",
    "ri", "phr", "pcmax", "rsrq", "sinr", "rsrp", "rssi", "cqi",
    "pucchSnr", "puschSnr",
)
# Cumulative counters. Differencing them into per-second rates before
# aggregation is not cosmetic: a monotonically rising counter aggregated as a
# mean encodes the absolute time of the capture, which is a deployment
# fingerprint and would leak run identity straight into the features.
RADIO_CUMULATIVE: frozenset[str] = frozenset({"dlBytes", "ulBytes"})

# Network flow columns aggregated per window.
NETWORK_NUMERIC: tuple[str, ...] = (
    "duration", "fwd_pkts", "bwd_pkts", "total_pkts",
    "fwd_bytes", "bwd_bytes", "total_bytes",
    "fwd_ip_bytes", "bwd_ip_bytes", "total_ip_bytes",
    "pkts_per_s", "bytes_per_s", "bytes_ratio", "pkts_ratio",
    "iat_mean", "iat_std", "iat_min", "iat_max",
    "fwd_iat_mean", "fwd_iat_std", "bwd_iat_mean", "bwd_iat_std",
    "pkt_size_mean", "pkt_size_std", "pkt_size_min", "pkt_size_max",
    "ttl_mean", "ttl_std",
    "flag_fin", "flag_syn", "flag_rst", "flag_psh", "flag_ack", "flag_urg",
    "handshake_complete",
)
# Skewed by orders of magnitude under flooding traffic; log1p before aggregation
# so that a window mean is not dominated by one flow.
NETWORK_LOG1P: frozenset[str] = frozenset({
    "fwd_bytes", "bwd_bytes", "total_bytes",
    "fwd_ip_bytes", "bwd_ip_bytes", "total_ip_bytes",
    "fwd_pkts", "bwd_pkts", "total_pkts",
    "pkts_per_s", "bytes_per_s", "bytes_ratio", "pkts_ratio",
})


@dataclass(frozen=True)
class WindowSpec:
    """The time grid both layers are projected onto.

    ``width_s = 16`` matches ``configs/base.yaml``'s ``window_records: 16`` at
    the DU's measured 1 Hz sampling rate, so "16 records" and "16 seconds" are
    the same window and the manuscript can state it as a duration.

    ``stride_s = width_s`` makes windows **non-overlapping**, which departs from
    Fard et al. (W in {5,10} s, stride 2 s, so 60-80% overlap). Overlapping
    windows multiply the apparent sample count without adding independent
    observations, and adjacent windows share most of their packets. Under
    run-disjoint splitting that is not train/test leakage, but it does inflate
    the denominator of every confidence interval. Given that this corpus has
    only tens of runs, an honest sample count matters more than a large one.
    Set ``stride_s`` below ``width_s`` only for a declared sensitivity analysis.
    """

    width_s: float = 16.0
    stride_s: float = 16.0
    # A window with no flows is dropped: there is nothing to classify. The drop
    # rate is reported (A12) rather than silently absorbed.
    require_network: bool = True
    require_radio: bool = True

    @property
    def overlapping(self) -> bool:
        return self.stride_s < self.width_s


def parse_radio_file(path: Path) -> list[dict]:
    """Read one DU telemetry file. JSON lines, epoch-ms timestamps.

    Malformed lines are counted, not skipped silently: a corpus that starts
    emitting broken telemetry should show up as a number, not as a quiet
    shrinkage of the dataset.
    """
    records, malformed = [], 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if "timestamp" not in obj:
                malformed += 1
                continue
            obj["_ts"] = obj["timestamp"] / 1000.0
            records.append(obj)
    records.sort(key=lambda r: (r["_ts"], r.get("ue_id", 0)))
    if records:
        records[0]["_malformed_in_file"] = malformed
    return records


def _mean_sd(xs: list[float]) -> tuple[float, float]:
    xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    if not xs:
        return float("nan"), float("nan")
    n = len(xs)
    mean = math.fsum(xs) / n
    if n == 1:
        return mean, 0.0
    return mean, math.sqrt(math.fsum((x - mean) ** 2 for x in xs) / n)


def difference_counters(records: list[dict]) -> list[dict]:
    """Turn cumulative byte counters into per-second rates, per UE.

    A reset or a wrap yields a negative delta; those are clamped to 0 rather
    than propagated, and the clamp count is attached so it can be reported.
    """
    by_ue: dict[object, dict] = {}
    clamped = 0
    out = []
    for r in records:
        r = dict(r)
        ue = r.get("ue_id")
        prev = by_ue.get(ue)
        for field in RADIO_CUMULATIVE:
            cur = r.get(field)
            if cur is None:
                r[f"{field}_rate"] = float("nan")
                continue
            if prev is None or prev.get(field) is None:
                r[f"{field}_rate"] = float("nan")
            else:
                dt = r["_ts"] - prev["_ts"]
                delta = cur - prev[field]
                if delta < 0:
                    delta = 0.0
                    clamped += 1
                r[f"{field}_rate"] = delta / dt if dt > 0 else float("nan")
        by_ue[ue] = r
        out.append(r)
    if out:
        out[0]["_counter_clamps"] = clamped
    return out


def window_grid(t0: float, t1: float, spec: WindowSpec) -> list[tuple[int, float, float]]:
    """(index, start, end) windows covering [t0, t1] on an absolute-time grid."""
    if t1 < t0:
        return []
    out, i, start = [], 0, t0
    while start < t1 or i == 0:
        out.append((i, start, start + spec.width_s))
        i += 1
        start = t0 + i * spec.stride_s
        if i > 10_000_000:  # pathological input guard
            break
    return out


def aggregate_network(flows: Iterable[dict], win_start: float, win_end: float) -> dict:
    """Per-window aggregation of flow records.

    A flow is assigned to a window by its **start** timestamp, matching prior
    work. A long flow therefore contributes to one window only; its duration
    feature already carries the fact that it outlived the window.
    """
    sel = [f for f in flows if win_start <= f["first_ts"] < win_end]
    out: dict[str, float] = {"net_n_flows": float(len(sel))}
    if not sel:
        for col in NETWORK_NUMERIC:
            out[f"net_{col}_mean"] = float("nan")
            out[f"net_{col}_sd"] = float("nan")
            out[f"net_{col}_sum"] = float("nan")
        return out
    for col in NETWORK_NUMERIC:
        vals = [float(f[col]) for f in sel if f.get(col) is not None]
        if col in NETWORK_LOG1P:
            vals = [math.log1p(v) if v >= 0 else -math.log1p(-v) for v in vals]
        mean, sd = _mean_sd(vals)
        out[f"net_{col}_mean"] = mean
        out[f"net_{col}_sd"] = sd
        out[f"net_{col}_sum"] = math.fsum(vals) if vals else float("nan")
    # Cardinality features: what a flow-count aggregate cannot express.
    out["net_n_dst_ports"] = float(len({f["dst_port"] for f in sel}))
    out["net_n_dst_ips"] = float(len({f["dst_ip"] for f in sel}))
    out["net_n_src_ips"] = float(len({f["src_ip"] for f in sel}))
    out["net_n_protos"] = float(len({f["proto"] for f in sel}))
    return out


def aggregate_radio(records: Iterable[dict], win_start: float, win_end: float) -> dict:
    sel = [r for r in records if win_start <= r["_ts"] < win_end]
    out: dict[str, float] = {"radio_n_records": float(len(sel)),
                             "radio_n_ues": float(len({r.get("ue_id") for r in sel}))}
    fields = [f for f in RADIO_FIELDS if f not in RADIO_CUMULATIVE]
    fields += [f"{f}_rate" for f in sorted(RADIO_CUMULATIVE)]
    if not sel:
        for f in fields:
            out[f"radio_{f}_mean"] = float("nan")
            out[f"radio_{f}_sd"] = float("nan")
        return out
    for f in fields:
        vals = []
        for r in sel:
            v = r.get(f)
            if isinstance(v, (int, float)):
                vals.append(float(v))
        mean, sd = _mean_sd(vals)
        out[f"radio_{f}_mean"] = mean
        out[f"radio_{f}_sd"] = sd
    return out


__all__ = [
    "RADIO_FIELDS", "RADIO_CUMULATIVE", "NETWORK_NUMERIC", "NETWORK_LOG1P",
    "WindowSpec", "parse_radio_file", "difference_counters", "window_grid",
    "aggregate_network", "aggregate_radio",
]
