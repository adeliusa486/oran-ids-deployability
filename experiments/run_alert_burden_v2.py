#!/usr/bin/env python3
"""EXP-046: alert burden from POOLED confusion counts, all eight models.

EXP-004 produced Tables IX and X of the reviewed draft. Two defects, both found
in review (R6.2, R6.3, R3.6):

  * it stored per-seed rates, not counts, and the tables averaged PPV across
    folds -- the estimator D-018 withdrew. Table X reported PPV = 0.10 at 60,768
    alerts/hour, when only ~481 attack flows/hour exist at pi = 0.002;
  * it ran five detectors and one floor. The decision tree and the stratified
    floor were missing.

This runner stores tp/fp/tn/fn at every threshold on a fine grid so that the
operating points, and the threshold needed for a precision target, are computed
from pooled counts by analysis/operational_v2.py. Nothing is averaged here.

UNITS, stated because review found them undefined (R3.4, R6.7). A radio-layer
sample is one WINDOW: 16 consecutive 1 Hz KPM records of one UE, i.e. 16 s of
one UE's telemetry. A benign UE therefore yields 225 windows per hour. Rates are
per window, and volumes are reported per benign UE-hour, never per flow.

Protocol identical to EXP-004: group-disjoint on the 30 capture sessions,
split seeds 101-120, model seed 11, threshold swept.

Usage:  python experiments/run_alert_burden_v2.py
"""
from __future__ import annotations

import json
import platform
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.data import load_radio  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402
from experiments.run_transfer_v2 import counts_at  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-046"
SPLIT_SEEDS = list(range(101, 121))
MODEL_SEED = 11
TAU_GRID = np.round(np.concatenate([np.arange(0.01, 1.0, 0.01),
                                    [0.995, 0.999, 0.9995]]), 4)
WINDOW_SECONDS = 16


def main() -> int:
    import argparse
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="results directory (default EXP-046)")
    ap.add_argument("--by-session", action="store_true",
                    help="also store counts per test session (round-2 R1-W4: "
                         "cluster bootstrap over sessions)")
    args = ap.parse_args()
    if args.out:
        OUT = ROOT / args.out
    t0 = time.time()
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    c = load_radio()
    X, y, groups = c.X, c.y, np.asarray(c.groups)
    print(c.summary(), flush=True)

    frames, by_sess = [], []
    for seed in SPLIT_SEEDS:
        sp = group_disjoint_split(y, groups, seed=seed, n_folds=1)[0]
        yte = y[sp.test_idx]
        if len(np.unique(yte)) < 2:
            print(f"  seed {seed}: single-class test fold, recorded as skipped")
            continue
        for key in [m.key for m in LADDER]:
            m = fit_model(key, X.iloc[sp.train_idx], y[sp.train_idx], MODEL_SEED)
            s = predict_scores(m, X.iloc[sp.test_idx])
            cnt = counts_at(yte, s, TAU_GRID)
            cnt.insert(0, "split_seed", seed)
            cnt.insert(0, "model", key)
            frames.append(cnt)
            if args.by_session:
                gte = groups[sp.test_idx]
                for g in np.unique(gte):
                    mk = gte == g
                    cg = counts_at(yte[mk], s[mk], TAU_GRID)
                    cg.insert(0, "session", g)
                    cg.insert(0, "split_seed", seed)
                    cg.insert(0, "model", key)
                    by_sess.append(cg)
        print(f"  seed {seed}: 8 models, test {len(yte)} windows "
              f"({int((yte == 0).sum())} benign)  ({time.time() - t0:.0f}s)",
              flush=True)

    C = pd.concat(frames, ignore_index=True)
    C.to_csv(OUT / "raw/tau_counts_radio.csv", index=False)
    if by_sess:
        pd.concat(by_sess, ignore_index=True).to_csv(
            OUT / "raw/tau_counts_radio_by_session.csv", index=False)
    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment=OUT.name, layer="radio", corpus=c.summary(),
        by_session=bool(args.by_session),
        unit=f"window = {WINDOW_SECONDS} consecutive 1 Hz KPM records of one UE",
        benign_windows_per_ue_hour=3600 // WINDOW_SECONDS,
        split="group_disjoint(session)", split_seeds=SPLIT_SEEDS,
        model_seed=MODEL_SEED, tau_grid=TAU_GRID.tolist(),
        mlp_class_weighting="balanced sample_weight (D-021)",
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2, default=str),
        encoding="utf-8")
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
