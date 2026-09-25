#!/usr/bin/env python3
"""EXP-045 part B: how separable are the corpora, and in which features?

Two measurements the reviewed draft either borrowed or promised and never made:

1. A DOMAIN CLASSIFIER. The draft cited Abraheem and Edhirig [16] for a 0.993
   balanced accuracy at telling D_A flows from D_B flows. Here it is measured
   on our own shared space, on the exporter-robust subset of D-022, and one
   feature at a time. Balanced accuracy 0.5 means indistinguishable.

2. EQ. (2), CORRECTED. The draft defined the mean first-order Wasserstein
   distance "after per-corpus quantile normalisation". Normalising each corpus
   by its OWN quantiles maps every marginal to the uniform distribution, so
   that W1 is identically zero. It also fits a transform on the target. Here the
   quantile transform is fitted on SOURCE training data only and applied to
   both corpora, the same rule as every other transform in the pipeline (A2).

Reads unlabelled target features for a diagnostic, never for training a
detector. Logged to the target access log.

Usage:  python experiments/run_exporter_sensitivity.py
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
from scipy.stats import wasserstein_distance  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold, cross_val_score  # noqa: E402
from sklearn.preprocessing import QuantileTransformer  # noqa: E402

from oran_ids.data import load_network_shared, load_target_d_b  # noqa: E402
from oran_ids.features.shared import COLUMNS  # noqa: E402
from experiments.run_transfer_v2 import ROBUST_COLUMNS  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-045"
N_PER_DOMAIN = 100_000
SEED = 7


def main() -> int:
    t0 = time.time()
    for d in ("processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    src = load_network_shared()
    tgt = load_target_d_b(reason="EXP-045 domain classifier and W1, unlabelled "
                                 "features only, no detector trained")
    rng = np.random.default_rng(SEED)
    ia = rng.choice(len(src.y), N_PER_DOMAIN, replace=False)
    ib = rng.choice(len(tgt.y), N_PER_DOMAIN, replace=False)
    A = src.X.iloc[ia].reset_index(drop=True)
    B = tgt.X.iloc[ib].reset_index(drop=True)
    X = pd.concat([A, B], ignore_index=True)
    d = np.r_[np.zeros(len(A), int), np.ones(len(B), int)]

    # ---- 1. domain classifier ------------------------------------------
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    clf = HistGradientBoostingClassifier(max_iter=200, random_state=SEED)
    dom = []
    for name, cols in (("shared (18)", list(COLUMNS)),
                       ("robust (9)", list(ROBUST_COLUMNS))):
        ba = cross_val_score(clf, X[cols], d, cv=cv,
                             scoring="balanced_accuracy")
        dom.append(dict(feature_set=name, n_features=len(cols),
                        balanced_accuracy=float(ba.mean()),
                        ba_sd=float(ba.std(ddof=1))))
        print(f"domain classifier on {name}: balanced accuracy "
              f"{ba.mean():.4f} (sd {ba.std(ddof=1):.4f})", flush=True)

    # ---- 2. per feature: univariate separability and source-fitted W1 ------
    # Fit the quantile map on SOURCE rows only (the A2 rule), apply to both.
    qt = QuantileTransformer(n_quantiles=1000, output_distribution="uniform",
                             subsample=N_PER_DOMAIN, random_state=SEED)
    qt.fit(A[list(COLUMNS)])
    QA = pd.DataFrame(qt.transform(A[list(COLUMNS)]), columns=COLUMNS)
    QB = pd.DataFrame(qt.transform(B[list(COLUMNS)]), columns=COLUMNS)
    feat = []
    for c in COLUMNS:
        auc = roc_auc_score(d, X[c])
        feat.append(dict(feature=c, robust=c in ROBUST_COLUMNS,
                         univariate_domain_auc=float(max(auc, 1 - auc)),
                         w1_source_quantile=float(
                             wasserstein_distance(QA[c], QB[c])),
                         median_d_a=float(A[c].median()),
                         median_d_b=float(B[c].median())))
    F = pd.DataFrame(feat).sort_values("w1_source_quantile", ascending=False)
    F.to_csv(OUT / "processed/feature_shift.csv", index=False)
    pd.DataFrame(dom).to_csv(OUT / "processed/domain_classifier.csv", index=False)
    summary = dict(
        w1_mean_shared=float(F.w1_source_quantile.mean()),
        w1_mean_robust=float(F[F.robust].w1_source_quantile.mean()),
        w1_mean_nonrobust=float(F[~F.robust].w1_source_quantile.mean()))
    print(F.round(4).to_string(index=False))
    print(summary)
    (OUT / "statistics/provenance_sensitivity.json").write_text(json.dumps(dict(
        experiment="EXP-045 part B", n_per_domain=N_PER_DOMAIN, seed=SEED,
        classifier="HistGradientBoosting(max_iter=200), 5-fold stratified CV",
        w1="scipy wasserstein_distance on a QuantileTransformer fitted on "
           "D_A rows only and applied to both corpora (Eq. 2 corrected)",
        domain_classifier=dom, **summary,
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
