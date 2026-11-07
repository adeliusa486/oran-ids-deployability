#!/usr/bin/env python3
"""EXP-070: the radio protocol comparison under two group keys (R1.2).

Reviewer 1: the random-split gain on the radio layer (0.13, corrected interval
-0.01 to 0.27, p = 0.06) is not significant, and with 30 five-minute sessions
the test has little power. One option is to group by the 42 documented
experiment runs instead (Fard et al.; EXP-059 recovers them with a 100 s clock
gap) and report how the result depends on that choice.

This runner repeats EXP-042 exactly (three protocols, 20 split seeds, 2 model
seeds, the full ladder, the 1-NN probe) for both group keys:

  sessions  clock gap > 300 s, 30 groups (the first submission)
  runs      clock gap > 100 s, 42 groups, each one run and one category

Windows are rebuilt within each group, so no window straddles a boundary. The
number of groups on each side of every split is recorded, so the Nadeau-Bengio
correction can be computed from group counts as well as window counts (R2.4).

Usage:  python experiments/run_leakage_r1.py
Output: results/EXP-070/
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
from sklearn.metrics import f1_score  # noqa: E402
from sklearn.neighbors import NearestNeighbors  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from oran_ids.data import load_radio  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from experiments.run_leakage_v2 import make_split  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-070"
SPLIT_SEEDS = list(range(101, 121))
MODEL_SEEDS = [11, 22]
GROUPINGS = {"sessions": 300.0, "runs": 100.0}


def main() -> int:
    t0 = time.time()
    for d in ("raw", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    rows, nn_rows, corp = [], [], {}
    for gname, gap in GROUPINGS.items():
        c = load_radio(session_gap_s=gap)
        X, y, groups, cat = c.X, np.asarray(c.y), np.asarray(c.groups), np.asarray(c.category)
        corp[gname] = c.summary()
        print(gname, c.summary(), flush=True)
        for proto in ("random", "group_disjoint", "stratified_group"):
            for seed in SPLIT_SEEDS:
                sp = make_split(proto, y, groups, cat, seed)
                tr, te = sp.train_idx, sp.test_idx
                if proto != "random":
                    sp.check_disjoint(groups)
                Xtr, ytr, Xte, yte = X.iloc[tr], y[tr], X.iloc[te], y[te]
                unseen = sorted((set(cat[te]) - set(cat[tr])) - {"benign"})
                n_tr_g, n_te_g = len(np.unique(groups[tr])), len(np.unique(groups[te]))
                sc = StandardScaler().fit(Xtr)
                nn = NearestNeighbors(n_neighbors=1).fit(sc.transform(Xtr))
                _, idx = nn.kneighbors(sc.transform(Xte))
                j = tr[idx[:, 0]]
                nn_rows.append(dict(
                    grouping=gname, protocol=proto, split_seed=seed,
                    n_train=len(tr), n_test=len(te), n_train_groups=n_tr_g,
                    n_test_groups=n_te_g, n_unseen_test_categories=len(unseen),
                    nn_same_group=float((groups[j] == groups[te]).mean()),
                    nn1_f1_macro=float(f1_score(yte, y[j], average="macro", zero_division=0))))
                for key in [m.key for m in LADDER]:
                    for ms in MODEL_SEEDS:
                        m = fit_model(key, Xtr, ytr, ms)
                        met = detection_metrics(yte, predict_scores(m, Xte), 0.5)
                        rows.append(dict(grouping=gname, protocol=proto, model=key,
                                         split_seed=seed, model_seed=ms,
                                         n_train=len(tr), n_test=len(te),
                                         n_train_groups=n_tr_g, n_test_groups=n_te_g,
                                         n_unseen_test_categories=len(unseen), **met))
                print(f"  {gname:<8} {proto:<17} seed {seed}: groups {n_tr_g}/{n_te_g} "
                      f"unseen={unseen} ({time.time() - t0:.0f}s)", flush=True)
        pd.DataFrame(rows).to_csv(OUT / "raw/leakage_runs.csv", index=False)
        pd.DataFrame(nn_rows).to_csv(OUT / "raw/nn_probe.csv", index=False)

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-070", groupings=GROUPINGS, corpora=corp,
        protocols=["random", "group_disjoint", "stratified_group"],
        split_seeds=SPLIT_SEEDS, model_seeds=MODEL_SEEDS,
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
