"""The D_A <-> D_B shared feature space (EXP-026).

The two corpora were produced by different flow exporters -- Zeek for D_A,
Argus for D_B -- and share **no column names at all**. A cross-deployment
evaluation therefore needs a space defined by meaning. That mapping lives in
``configs/features/shared_space.yaml`` and is read, not duplicated, here.

Three things this module is careful about, each of which is a way a transfer
result becomes wrong rather than merely disappointing:

1. **Byte semantics (D-015).** Zeek's ``src_bytes`` is application payload;
   Argus's ``SrcBytes`` is the whole frame. Their medians are 0 and 84. Mapping
   one onto the other manufactures a distribution shift with no deployment
   meaning and inflates every transfer gap. ``src_ip_bytes`` is the counterpart
   that actually matches, at 40 vs 42 bytes per packet.

2. **Fixed one-hot levels.** ``proto`` is expanded against a level list fixed in
   the config, not learned per corpus. A level list learned from each corpus
   would silently produce different matrix widths for source and target.

3. **Column order is asserted, not assumed.** ``build`` returns columns in a
   single canonical order for both corpora, and the caller can assert equality.
   Feeding a model a target matrix whose columns are permuted relative to
   training is silent, total, and produces a plausible-looking number.

No transform here is fitted. Every one is deterministic and parameter-free, so
this module cannot leak target information into source-side preprocessing (A2).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SPEC_PATH = Path("configs/features/shared_space.yaml")

# Canonical column order. Both corpora produce exactly this, in this order.
BASE_NUMERIC = ("duration", "src_bytes", "dst_bytes", "src_pkts", "dst_pkts",
                "tot_pkts", "tot_bytes")
DERIVED = ("mean_pkt_size", "src_mean_pkt_size", "dst_mean_pkt_size",
           "bytes_per_s", "pkts_per_s", "src_byte_ratio", "src_pkt_ratio")
PROTO_LEVELS = ("tcp", "udp", "icmp", "other")
PROTO_COLS = tuple(f"proto_{p}" for p in PROTO_LEVELS)

COLUMNS = BASE_NUMERIC + PROTO_COLS + DERIVED          # 7 + 4 + 7 = 18

DURATION_FLOOR_S = 0.001
LOG1P_COLS = frozenset(BASE_NUMERIC) | {
    "mean_pkt_size", "src_mean_pkt_size", "dst_mean_pkt_size",
    "bytes_per_s", "pkts_per_s"}


def load_spec() -> dict:
    """The committed mapping table. Read so code and paper cannot drift apart."""
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0.0).astype(np.float64)


def _normalise_proto(s: pd.Series) -> pd.Series:
    """Collapse to the fixed shared levels. Everything unknown becomes 'other'.

    Both exporters spell the three shared protocols in lower case already; the
    ``.str.lower()`` is defensive, because a capitalised 'TCP' silently becoming
    'other' would be a distribution shift we invented ourselves.
    """
    v = s.astype(str).str.strip().str.lower()
    return v.where(v.isin(PROTO_LEVELS[:3]), "other")


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    """Derive, one-hot, log1p, order. Identical arithmetic for both corpora."""
    tot_pkts = df["tot_pkts"].clip(lower=1)
    src_pkts = df["src_pkts"].clip(lower=1)
    dst_pkts = df["dst_pkts"].clip(lower=1)
    tot_bytes = df["tot_bytes"].clip(lower=1)
    dur = df["duration"].clip(lower=DURATION_FLOOR_S)

    df["mean_pkt_size"] = df["tot_bytes"] / tot_pkts
    df["src_mean_pkt_size"] = df["src_bytes"] / src_pkts
    df["dst_mean_pkt_size"] = df["dst_bytes"] / dst_pkts
    df["bytes_per_s"] = df["tot_bytes"] / dur
    df["pkts_per_s"] = df["tot_pkts"] / dur
    df["src_byte_ratio"] = df["src_bytes"] / tot_bytes
    df["src_pkt_ratio"] = df["src_pkts"] / tot_pkts

    # Fixed-level one-hot. reindex fills a level absent from this corpus with 0
    # rather than dropping the column, which is what keeps the two matrices
    # compatible even if a corpus happens to contain no ICMP at all.
    oh = pd.get_dummies(df["proto"], prefix="proto", dtype=np.int8)
    oh = oh.reindex(columns=list(PROTO_COLS), fill_value=0)
    df = pd.concat([df.drop(columns=["proto"]), oh], axis=1)

    for c in LOG1P_COLS:
        df[c] = np.log1p(df[c].clip(lower=0))

    out = df[list(COLUMNS)].astype(np.float32)
    out = out.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    assert tuple(out.columns) == COLUMNS, "shared-space column order drifted"
    return out.reset_index(drop=True)


def from_d_a(df: pd.DataFrame) -> pd.DataFrame:
    """Zeek flow records -> shared space.

    Uses ``src_ip_bytes`` / ``dst_ip_bytes``, never ``src_bytes`` / ``dst_bytes``.
    See D-015: the payload columns are median 0 and are not Argus's counterpart.
    """
    missing = {"duration", "src_ip_bytes", "dst_ip_bytes", "src_pkts",
               "dst_pkts", "proto"} - set(df.columns)
    if missing:
        raise KeyError(f"D_A is missing shared-space source columns: {sorted(missing)}")

    out = pd.DataFrame(index=df.index)
    out["duration"] = _num(df["duration"])
    out["src_bytes"] = _num(df["src_ip_bytes"])
    out["dst_bytes"] = _num(df["dst_ip_bytes"])
    out["src_pkts"] = _num(df["src_pkts"])
    out["dst_pkts"] = _num(df["dst_pkts"])
    out["tot_pkts"] = out["src_pkts"] + out["dst_pkts"]
    out["tot_bytes"] = out["src_bytes"] + out["dst_bytes"]
    out["proto"] = _normalise_proto(df["proto"])
    return _finish(out)


def from_d_b(df: pd.DataFrame) -> pd.DataFrame:
    """Argus flow records -> shared space."""
    missing = {"Dur", "SrcBytes", "DstBytes", "SrcPkts", "DstPkts", "TotPkts",
               "TotBytes", "Proto"} - set(df.columns)
    if missing:
        raise KeyError(f"D_B is missing shared-space source columns: {sorted(missing)}")

    out = pd.DataFrame(index=df.index)
    out["duration"] = _num(df["Dur"])
    out["src_bytes"] = _num(df["SrcBytes"])
    out["dst_bytes"] = _num(df["DstBytes"])
    out["src_pkts"] = _num(df["SrcPkts"])
    out["dst_pkts"] = _num(df["DstPkts"])
    out["tot_pkts"] = _num(df["TotPkts"])
    out["tot_bytes"] = _num(df["TotBytes"])
    out["proto"] = _normalise_proto(df["Proto"])
    return _finish(out)


def assert_compatible(a: pd.DataFrame, b: pd.DataFrame) -> None:
    """Fail loudly if the two matrices are not the same space.

    A permuted or differently-sized target matrix does not raise inside
    scikit-learn for tree models -- it predicts, confidently, on nonsense.
    """
    if tuple(a.columns) != tuple(b.columns):
        raise ValueError(
            "shared-space mismatch.\n"
            f"  source: {list(a.columns)}\n  target: {list(b.columns)}")
    if len(a.columns) != len(COLUMNS):
        raise ValueError(f"expected {len(COLUMNS)} columns, got {len(a.columns)}")


__all__ = ["COLUMNS", "BASE_NUMERIC", "DERIVED", "PROTO_LEVELS", "PROTO_COLS",
           "from_d_a", "from_d_b", "assert_compatible", "load_spec",
           "DURATION_FLOOR_S"]
