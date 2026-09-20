#!/usr/bin/env python3
"""EXP-001: artefact-level verification of D_A (NetsLab-5GORAN-IDD).

Gate G1 cannot pass on a landing page. This script establishes, from the artefact
itself, the facts the split design (A4) and the windowing policy (A12) depend on:

  - file integrity (SHA-256, byte size) recorded in data/provenance/
  - schema, null rates, label semantics and class balance for both layers
  - candidate group keys, and whether any supports 5 disjoint folds
  - the sampling rate and time span
  - capture-session recovery from the time axis, and whether sessions are label-pure
  - the number of complete windows that survive the A12 policy
  - the CU / DU join feasibility, quantified

Everything it prints is derived from the data. Nothing is asserted.
Outputs: results/EXP-001/{processed,statistics,logs}/

Usage:  python scripts/exp001_profile_corpus.py
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw/d_a")
OUT = Path("results/EXP-001")
PROV = Path("data/provenance")

# Pre-registered analysis parameters. Fixed before looking at results.
SESSION_GAP_S = 300      # idle gap that separates two capture runs
WINDOW_RECORDS = 16      # A12, from configs/base.yaml
MIN_FOLDS = 5            # configs/base.yaml split_seeds
JOIN_TOLERANCE_S = 1.0   # CU/DU alignment tolerance to test first


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record_provenance(files: list[Path]) -> dict:
    prov = {}
    for f in files:
        if not f.exists():
            prov[f.name] = {"status": "MISSING"}
            continue
        prov[f.name] = {
            "status": "present",
            "bytes": f.stat().st_size,
            "sha256": sha256(f),
            "source": "https://zenodo.org/api/records/18923275",
        }
    return prov


def profile_frame(df: pd.DataFrame, name: str) -> dict:
    """Schema, null rates and duplicate rate. No interpretation."""
    return {
        "name": name,
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "columns": {c: str(df[c].dtype) for c in df.columns},
        "null_rate_pct": {c: round(float(df[c].isna().mean() * 100), 4)
                          for c in df.columns if df[c].isna().any()},
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "exact_duplicate_pct": round(float(df.duplicated().mean() * 100), 4),
    }


def group_key_feasibility(df: pd.DataFrame, candidates: list[str]) -> pd.DataFrame:
    """A group key is usable only if it has enough distinct values for MIN_FOLDS
    disjoint folds AND no single group dominates (which would make one fold huge)."""
    rows = []
    for k in candidates:
        if k not in df.columns:
            rows.append({"key": k, "verdict": "ABSENT"})
            continue
        vc = df[k].value_counts()
        n = int(df[k].nunique())
        largest = float(vc.iloc[0] / len(df)) if n else 1.0
        if n < MIN_FOLDS:
            verdict = "TOO FEW"
        elif n < 2 * MIN_FOLDS:
            verdict = "TIGHT"
        elif largest > 0.5:
            verdict = "IMBALANCED"
        else:
            verdict = "OK"
        rows.append({"key": k, "n_groups": n,
                     "null_pct": round(float(df[k].isna().mean() * 100), 3),
                     "largest_group_share": round(largest, 4),
                     "verdict": verdict})
    return pd.DataFrame(rows)


def recover_sessions(df: pd.DataFrame, ts_col: str, gap_s: int) -> pd.DataFrame:
    """A capture run is a maximal stretch with no idle gap longer than gap_s.
    Label purity of the recovered sessions is the test of whether this is a real
    run identifier or an artefact of the segmentation threshold."""
    d = df.sort_values(ts_col).reset_index(drop=True)
    gaps = d[ts_col].diff().dt.total_seconds()
    d["session"] = (gaps > gap_s).cumsum()
    return d


def main() -> int:
    for sub in ("processed", "statistics", "logs", "config", "figures", "tables", "raw"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    PROV.mkdir(parents=True, exist_ok=True)

    radio_p = RAW / "Lower_Layer_Data.db"
    net_p = RAW / "Network_Dataset.csv"

    report: dict = {"experiment": "EXP-001", "params": {
        "session_gap_s": SESSION_GAP_S, "window_records": WINDOW_RECORDS,
        "min_folds": MIN_FOLDS, "join_tolerance_s": JOIN_TOLERANCE_S}}

    # ---- provenance -------------------------------------------------------
    report["provenance"] = record_provenance([radio_p, net_p])
    (PROV / "d_a_files.json").write_text(
        json.dumps(report["provenance"], indent=2), encoding="utf-8")
    print("provenance written ->", PROV / "d_a_files.json")

    if not radio_p.exists():
        print("FAIL: radio DB missing", file=sys.stderr)
        return 1

    # ---- radio layer ------------------------------------------------------
    con = sqlite3.connect(radio_p)
    radio = pd.read_sql("SELECT * FROM lower_layer_data", con)
    con.close()
    report["radio"] = profile_frame(radio, "lower_layer_data")

    radio["ts"] = pd.to_datetime(radio["timestamp"], unit="ms")
    span = radio["ts"].max() - radio["ts"].min()
    gaps = radio.sort_values("ts")["ts"].diff().dt.total_seconds()
    report["radio"]["time"] = {
        "epoch_unit": "milliseconds",
        "start": str(radio["ts"].min()), "end": str(radio["ts"].max()),
        "span_days": round(span.total_seconds() / 86400, 2),
        "inter_record_gap_s": {
            "median": round(float(gaps.median()), 4),
            "p95": round(float(gaps.quantile(0.95)), 4),
            "p99": round(float(gaps.quantile(0.99)), 4),
            "max": round(float(gaps.max()), 1)},
        "implied_sampling_hz": round(1.0 / float(gaps.median()), 4) if gaps.median() else None,
    }
    report["radio"]["labels"] = {
        "traffic_type": {str(k): int(v) for k, v in radio["traffic_type"].value_counts().items()},
        "attack_category": {str(k): int(v) for k, v in radio["attack_category"].value_counts().items()},
        "attack_subcategory_n": int(radio["attack_subcategory"].nunique()),
        "attack_prevalence_pct": round(float((radio["traffic_type"] == 1).mean() * 100), 2),
    }

    radio = recover_sessions(radio, "ts", SESSION_GAP_S)
    sess = radio.groupby("session").agg(
        n=("ts", "size"), start=("ts", "min"), end=("ts", "max"),
        n_categories=("attack_category", "nunique"),
        category=("attack_category", lambda x: x.mode().iat[0]))
    report["radio"]["sessions"] = {
        "gap_threshold_s": SESSION_GAP_S,
        "n_sessions": int(len(sess)),
        "label_pure": int((sess.n_categories == 1).sum()),
        "label_pure_pct": round(float((sess.n_categories == 1).mean() * 100), 2),
        "records_per_session": {"median": float(sess.n.median()),
                                "min": int(sess.n.min()), "max": int(sess.n.max())},
        "sessions_per_category": {str(k): int(v) for k, v in sess.groupby("category").size().items()},
        "sensitivity": {str(t): int((radio.sort_values("ts")["ts"].diff().dt.total_seconds() > t).sum() + 1)
                        for t in (30, 60, 300, 900)},
    }
    sess.to_csv(OUT / "processed" / "radio_sessions.csv")

    feas = group_key_feasibility(radio, ["ue_id", "cellid", "rnti", "attack_subcategory", "session"])
    feas.to_csv(OUT / "statistics" / "group_key_feasibility.csv", index=False)
    report["radio"]["group_keys"] = feas.to_dict("records")

    win = radio.groupby(["session", "ue_id"]).size()
    report["radio"]["windowing_A12"] = {
        "policy": f"min_records={WINDOW_RECORDS}, short_flow_policy=drop",
        "grouping": "(session, ue_id)",
        "n_groups": int(len(win)),
        "groups_with_enough_records": int((win >= WINDOW_RECORDS).sum()),
        "complete_windows": int((win // WINDOW_RECORDS).sum()),
        "records_dropped_by_policy": int(len(radio) - (win // WINDOW_RECORDS).sum() * WINDOW_RECORDS),
        "drop_rate_pct": round(100 * (1 - (win // WINDOW_RECORDS).sum() * WINDOW_RECORDS / len(radio)), 2),
    }

    # ---- network layer ----------------------------------------------------
    if net_p.exists() and net_p.stat().st_size > 200_000_000:
        net = pd.read_csv(net_p, low_memory=False)
        report["network"] = profile_frame(net, "Network_Dataset.csv")
        for col in net.columns:
            lc = col.lower()
            if lc in ("label", "attack_category", "traffic_type", "attack_subcategory"):
                report["network"].setdefault("labels", {})[col] = {
                    str(k): int(v) for k, v in net[col].value_counts().head(30).items()}
        report["network"]["group_keys"] = group_key_feasibility(
            net, [c for c in ["uid", "id.orig_h", "src_ip", "ue_id", "attack_subcategory"]
                  if c in net.columns]).to_dict("records")
    else:
        report["network"] = {"status": "NOT YET DOWNLOADED OR INCOMPLETE",
                             "bytes_present": net_p.stat().st_size if net_p.exists() else 0,
                             "bytes_expected": 227_180_000}

    out = OUT / "processed" / "exp001_profile.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("profile written ->", out)

    # ---- gate summary -----------------------------------------------------
    print("\n=== G1 CRITERIA ===")
    checks = [
        ("artefact downloaded and checksummed",
         all(v.get("status") == "present" for v in report["provenance"].values())),
        (f"a group key supports {MIN_FOLDS} disjoint folds",
         any(r.get("verdict") == "OK" for r in report["radio"]["group_keys"])),
        ("recovered sessions are label-pure",
         report["radio"]["sessions"]["label_pure_pct"] == 100.0),
        ("a usable time axis exists",
         report["radio"]["time"]["span_days"] > 1),
        ("network layer profiled",
         "n_rows" in report.get("network", {})),
    ]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
