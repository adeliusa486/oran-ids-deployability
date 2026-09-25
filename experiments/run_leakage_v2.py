#!/usr/bin/env python3
"""EXP-042: is random-split inflation memorisation, or unseen attack scenarios?

EXP-002 found that a random split inflates radio-layer macro-F1 by 0.09-0.17
over a run-disjoint split, and read the trivial baselines' null gain as
identifying memorisation. Review R2.4 is right that this does not follow: a
classifier that ignores its inputs cannot distinguish memorisation from a
harder task. And Section X of the paper concedes the radio session key is
perfectly aligned with attack category (purity 1.000), so a run-disjoint test
fold can hold out a whole attack scenario.

Design, fixed before running:

  protocols   random            windows split ignoring sessions
              group_disjoint    whole sessions held out (EXP-002's protocol)
              stratified_group  whole sessions held out, but every attack
                                category keeps sessions on BOTH sides, so no
                                test category is unseen in training
  data        D_A radio layer, 16-record windows, 30 label-pure sessions
  seeds       20 split seeds x 2 model seeds, as EXP-002
  models      the full ladder, MLP weighted (D-021)

Reading:
  * random >> stratified_group ~ group_disjoint: the inflation survives holding
    out runs while keeping every category in training. It is about the runs.
  * random ~ stratified_group >> group_disjoint: the drop was unseen scenarios.

A direct probe, independent of any model: for each test window, is its nearest
training window (z-scored on train) from the SAME capture session? Under a
random split that is what memorisation would exploit.

Usage:  python experiments/run_leakage_v2.py
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

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402
from sklearn.neighbors import NearestNeighbors  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from oran_ids.data import load_radio  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from oran_ids.splits import (group_disjoint_split, random_split,  # noqa: E402
                             stratified_group_split)

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-042"
SPLIT_SEEDS = list(range(101, 121))
MODEL_SEEDS = [11, 22]


def make_split(proto, y, groups, cat, seed):
    if proto == "random":
        return random_split(y, groups, seed=seed, n_folds=1)[0]
    if proto == "group_disjoint":
        return group_disjoint_split(y, groups, seed=seed, n_folds=1)[0]
    return stratified_group_split(y, groups, cat, seed=seed, n_folds=1)[0]


def main() -> int:
    t0 = time.time()
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    c = load_radio()
    X, y, groups, cat = c.X, c.y, np.asarray(c.groups), np.asarray(c.category)
    print(c.summary(), flush=True)

    rows, nn_rows = [], []
    for proto in ("random", "group_disjoint", "stratified_group"):
        for seed in SPLIT_SEEDS:
            sp = make_split(proto, y, groups, cat, seed)
            tr, te = sp.train_idx, sp.test_idx
            Xtr, ytr, Xte, yte = X.iloc[tr], y[tr], X.iloc[te], y[te]
            cats_tr, cats_te = set(cat[tr]), set(cat[te])
            unseen = sorted((cats_te - cats_tr) - {"benign"})

            # --- model-free proximity probe --------------------------------
            sc = StandardScaler().fit(Xtr)
            nn = NearestNeighbors(n_neighbors=1).fit(sc.transform(Xtr))
            _, idx = nn.kneighbors(sc.transform(Xte))
            j = tr[idx[:, 0]]
            same_sess = float((groups[j] == groups[te]).mean())
            nn_pred = y[j]
            nn_rows.append(dict(
                protocol=proto, split_seed=seed, n_train=len(tr),
                n_test=len(te), test_prevalence=float(yte.mean()),
                n_test_sessions=int(len(np.unique(groups[te]))),
                unseen_test_categories=";".join(unseen),
                n_unseen_test_categories=len(unseen),
                nn_same_session=same_sess,
                nn1_f1_macro=float(f1_score(yte, nn_pred, average="macro",
                                            zero_division=0)),
                nn1_label_agreement=float((nn_pred == yte).mean())))

            for key in [m.key for m in LADDER]:
                for ms in MODEL_SEEDS:
                    m = fit_model(key, Xtr, ytr, ms)
                    met = detection_metrics(yte, predict_scores(m, Xte), 0.5)
                    rows.append(dict(protocol=proto, model=key, split_seed=seed,
                                     model_seed=ms, n_train=len(tr),
                                     n_test=len(te),
                                     train_prevalence=float(ytr.mean()),
                                     test_prevalence=float(yte.mean()),
                                     n_unseen_test_categories=len(unseen),
                                     **met))
            print(f"  {proto:<17} seed {seed}: nn_same_session={same_sess:.3f}"
                  f" unseen={unseen}  ({time.time() - t0:.0f}s)", flush=True)

    R = pd.DataFrame(rows)
    N = pd.DataFrame(nn_rows)
    R.to_csv(OUT / "raw/leakage_runs_radio.csv", index=False)
    N.to_csv(OUT / "raw/nn_probe_radio.csv", index=False)

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-042", layer="radio", corpus=c.summary(),
        protocols=["random", "group_disjoint", "stratified_group"],
        split_seeds=SPLIT_SEEDS, model_seeds=MODEL_SEEDS,
        mlp_class_weighting="balanced sample_weight (D-021)",
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2, default=str),
        encoding="utf-8")
    print("\nproximity probe (mean over seeds):")
    print(N.groupby("protocol")[["nn_same_session", "nn1_f1_macro",
                                 "n_unseen_test_categories"]].mean())
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
