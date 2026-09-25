#!/usr/bin/env python3
"""Why Platt scaling inverted the decision tree in one EXP-044 seed.

Round-2 review R2: a change in ROC-AUC of 0.95 means the ranking was fully
inverted, which needs a cause. This rebuilds, deterministically, the split and
the tree of the affected seed (and of one unaffected seed for comparison) with
EXP-044's own code: same subsample, same three-way group split, same model seed.
It reports how well the tree ranks the calibration fold and the test fold, and
the slope Platt scaling fits on the calibration fold.

Writes results/EXP-044/processed/platt_inversion_diagnosis.csv.

Usage:  python analysis/platt_diagnosis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from oran_ids.data import load_network_shared  # noqa: E402
from oran_ids.models import fit_model, predict_scores  # noqa: E402
import experiments.run_calibration as rc  # noqa: E402

OUT = ROOT / "results" / "EXP-044" / "processed" / "platt_inversion_diagnosis.csv"


def main() -> int:
    runs = pd.read_csv(ROOT / "results/EXP-044/raw/calibration_runs.csv")
    raw = runs[runs.calibrator == "raw"].set_index(["seed", "model", "domain"]).roc_auc
    pl = runs[runs.calibrator == "platt"].set_index(["seed", "model", "domain"]).roc_auc
    flips = (pl - raw)[(pl - raw).abs() > 0.5]
    seeds = sorted({s for s, m, _ in flips.index if m == "tree"})
    if not seeds:
        raise SystemExit("no inversion in EXP-044")
    control = min(s for s in runs.seed.unique() if s not in seeds)
    src = load_network_shared()
    rows = []
    for seed in seeds + [control]:
        rng = np.random.default_rng(seed)
        idx = np.sort(rng.choice(len(src.y), size=min(rc.SUBSAMPLE, len(src.y)),
                                 replace=False))
        X, y, g = src.X.iloc[idx].reset_index(drop=True), src.y[idx], src.groups[idx]
        tr, cal, te = rc.three_way_group_split(g, seed)
        m = fit_model("tree", X.iloc[tr], y[tr], rc.MODEL_SEED)
        s_cal, s_te = predict_scores(m, X.iloc[cal]), predict_scores(m, X.iloc[te])
        lr = LogisticRegression(max_iter=1000).fit(
            np.clip(s_cal, 1e-6, 1 - 1e-6).reshape(-1, 1), y[cal])
        rows.append(dict(seed=int(seed), inverted=seed in seeds, n_cal=int(len(cal)),
                         cal_groups=int(len(set(g[cal]))), cal_prevalence=float(y[cal].mean()),
                         auc_cal=float(roc_auc_score(y[cal], s_cal)),
                         auc_test=float(roc_auc_score(y[te], s_te)),
                         platt_slope=float(lr.coef_[0][0]),
                         auc_test_logged=float(raw.loc[(seed, "tree", "source_test")])))
    D = pd.DataFrame(rows)
    if not np.allclose(D.auc_test, D.auc_test_logged, atol=1e-9):
        raise AssertionError("rebuilt tree does not reproduce EXP-044's test AUC")
    D.to_csv(OUT, index=False)
    print(D.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
