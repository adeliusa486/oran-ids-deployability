#!/usr/bin/env python3
"""EXP-059: how the number of D_A radio sessions depends on the clock-gap rule.

The paper groups the 1 Hz radio records into capture sessions by starting a new
session at every gap of more than 300 s in the clock (EXP-001), which gives 30
sessions. Fard et al. (arXiv 2606.22450) describe the same corpus as 42
experiment runs. This script counts the segments that each gap rule produces,
checks that every segment carries one attack category (and one sub-category),
and checks that the 300 s sessions are unions of whole segments of the finer
rules, so that a finer rule only splits sessions and never regroups them.

Usage:  python experiments/run_session_rule.py
Output: results/EXP-059/processed/session_rule.csv
        results/EXP-059/statistics/provenance.json
"""
from __future__ import annotations

import json
import platform
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/raw/d_a/Lower_Layer_Data.db"
OUT = ROOT / "results/EXP-059"
GAPS_S = [10, 30, 60, 90, 100, 105, 110, 120, 300, 600]
REFERENCE_GAP_S = 300          # the rule of src/oran_ids/data.py (SESSION_GAP_S)


def main() -> int:
    con = sqlite3.connect(DB)
    df = pd.read_sql("SELECT timestamp, attack_category, attack_subcategory "
                     "FROM lower_layer_data", con)
    con.close()
    df["ts"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.sort_values("ts", kind="mergesort").reset_index(drop=True)
    gap = df["ts"].diff().dt.total_seconds()
    ref = (gap > REFERENCE_GAP_S).cumsum()

    rows = []
    for g in GAPS_S:
        seg = (gap > g).cumsum()
        by = df.groupby(seg)
        nested = bool((pd.crosstab(seg, ref) > 0).sum(axis=1).max() == 1) if g <= REFERENCE_GAP_S else None
        rows.append(dict(
            gap_s=g,
            n_segments=int(seg.nunique()),
            n_category_pure=int((by["attack_category"].nunique() == 1).sum()),
            n_subcategory_pure=int((by["attack_subcategory"].nunique() == 1).sum()),
            nested_in_reference=nested,
        ))
    R = pd.DataFrame(rows)
    by_ref = df.groupby(ref)["attack_subcategory"].nunique()
    R["reference_sessions_multi_subcategory"] = int((by_ref > 1).sum())

    (OUT / "processed").mkdir(parents=True, exist_ok=True)
    (OUT / "statistics").mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT / "processed/session_rule.csv", index=False)
    prov = dict(experiment="EXP-059", source_file=DB.name, n_records=int(len(df)),
                reference_gap_s=REFERENCE_GAP_S, python=platform.python_version(),
                pandas=pd.__version__)
    (OUT / "statistics/provenance.json").write_text(json.dumps(prov, indent=2))
    print(R.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
