#!/usr/bin/env python3
"""EXP-048: do unsupervised detectors transfer better than supervised ones?

Review R4 asked for the model classes most often proposed for IoT and O-RAN
intrusion detection, under the same protocol. Anomaly detectors are the obvious
candidate for a transfer study: they model benign traffic only, so they should
not depend on which attack tools the source deployment happened to use. If they
transfer no better, the failure is not a supervised-learning artefact.

Design, fixed before running (identical splits to EXP-041):
  source     D_A shared space, 300,000-flow subsample per seed, group-disjoint
             on src_ip, split seeds 101-120
  training   source-train BENIGN flows only (novelty detection)
  detectors  IsolationForest (200 trees)                  Liu et al., ICDM 2008
             autoencoder: z-score -> MLP 12-6-12 -> reconstruction MSE
  threshold  the 99th percentile of anomaly scores on the SOURCE-TRAIN benign
             flows, i.e. a nominal 1% false positive rate, fixed before any
             held-out or target score is seen
  reported   threshold-free ROC-AUC and PR-AUC, and macro-F1, balanced
             accuracy, FPR and recall at the fixed threshold, on source held-out
             and on the whole target

Usage:  python experiments/run_unsupervised.py
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
from sklearn.ensemble import IsolationForest  # noqa: E402
from sklearn.neural_network import MLPRegressor  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from oran_ids.data import load_network_shared, load_target_d_b  # noqa: E402
from oran_ids.features.shared import assert_compatible  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402
from experiments.run_transfer import per_category_recall, subsample  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-048"
SPLIT_SEEDS = list(range(101, 121))
MODEL_SEED = 11
SOURCE_SUBSAMPLE = 300_000
QUANTILE = 0.99


class IForest:
    name = "iforest"

    def fit(self, X):
        self.m = IsolationForest(n_estimators=200, random_state=MODEL_SEED,
                                 n_jobs=-1).fit(X)
        return self

    def score(self, X):
        return -self.m.score_samples(X)          # higher = more anomalous


class Autoencoder:
    name = "autoencoder"

    def fit(self, X):
        self.sc = StandardScaler().fit(X)
        Z = self.sc.transform(X)
        self.m = MLPRegressor(hidden_layer_sizes=(12, 6, 12), activation="relu",
                              early_stopping=True, n_iter_no_change=10,
                              max_iter=300, random_state=MODEL_SEED).fit(Z, Z)
        return self

    def score(self, X):
        Z = self.sc.transform(X)
        return np.mean((self.m.predict(Z) - Z) ** 2, axis=1)


def main() -> int:
    t0 = time.time()
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    src = load_network_shared()
    tgt = load_target_d_b(reason="EXP-048 unsupervised detectors, target evaluation")
    assert_compatible(src.X, tgt.X)
    Xt = tgt.X.to_numpy(np.float32)

    rows, cats = [], []
    for si, seed in enumerate(SPLIT_SEEDS):
        Xs, ys, cs, gs = subsample(src.X, src.y, src.category, src.groups,
                                   SOURCE_SUBSAMPLE, seed)
        sp = group_disjoint_split(ys, gs, seed=seed, n_folds=1)[0]
        sp.check_disjoint(gs)
        Xtr = Xs.iloc[sp.train_idx].to_numpy(np.float32)
        ytr = ys[sp.train_idx]
        Xte = Xs.iloc[sp.test_idx].to_numpy(np.float32)
        yte = ys[sp.test_idx]
        benign = Xtr[ytr == 0]
        for Det in (IForest, Autoencoder):
            t1 = time.time()
            det = Det().fit(benign)
            thr = float(np.quantile(det.score(benign), QUANTILE))
            for dom, XX, yy, cc in (("source_heldout", Xte, yte, None),
                                    ("target", Xt, tgt.y, tgt.category)):
                s = det.score(XX)
                m = detection_metrics(yy, s, thr)
                m.pop("brier", None)
                # detection_metrics already records the threshold it applied
                rows.append(dict(model=Det.name, split_seed=seed, domain=dom,
                                 n_benign_train=len(benign), **m))
                if cc is not None:
                    cats.append(dict(model=Det.name, split_seed=seed,
                                     **per_category_recall(yy, cc,
                                                           (s >= thr).astype(int))))
            src_r, tgt_r = rows[-2], rows[-1]
            print(f"  seed {seed} [{si + 1}/20] {Det.name:<11} "
                  f"src F1 {src_r['f1_macro']:.3f} AUC {src_r['roc_auc']:.3f} "
                  f"-> tgt F1 {tgt_r['f1_macro']:.3f} AUC {tgt_r['roc_auc']:.3f}"
                  f"  {time.time() - t1:.1f}s", flush=True)

    pd.DataFrame(rows).to_csv(OUT / "raw/runs.csv", index=False)
    pd.DataFrame(cats).to_csv(OUT / "processed/per_category_recall.csv",
                              index=False)
    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-048", split_seeds=SPLIT_SEEDS, model_seed=MODEL_SEED,
        source_subsample=SOURCE_SUBSAMPLE, training="source-train benign only",
        threshold=f"{QUANTILE:.2f} quantile of source-train benign scores",
        detectors={"iforest": "IsolationForest(n_estimators=200)",
                   "autoencoder": "z-score, MLPRegressor(12,6,12), MSE"},
        source=src.summary(), target=tgt.summary(),
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2, default=str),
        encoding="utf-8")
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
