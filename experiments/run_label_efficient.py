#!/usr/bin/env python3
"""EXP-069 (label-efficient arm): how much labelled target data is needed? (R2.6)

Reviewer 2 asked for an arm that retrains with k labelled target capture files
and plots the result against the bounds of the deployability test. For each
k in {1, 2, 4, 8} and each of R random draws of k files out of the 20 capture
files of 5G-NIDD (byte-corrected, D-035):

  source+k     the D_A training set of one transfer split (EXP-064 design) plus
               up to 60,000 flows sampled from the k labelled files
  target-only  up to 240,000 flows from the k labelled files alone

Each model is evaluated on every flow of the files NOT drawn. The flood copies
of file 5 are relabelled as attack in training when file 5 is drawn (an
operator labelling its own capture would label the flood), and two views of
the evaluation are stored: 'relab' (copies as attack) and 'clean' (copies
removed). Confusion counts at the threshold grid are stored for the held-out
source fold and for the held-out target files (overall and per capture file),
so the revised test (EXP-075) can be applied with the same threshold rules as
the main transfer. k = 0 is the plain transfer of EXP-064, scored on the same
held-out files from its stored per-flow scores.

Usage:  python experiments/run_label_efficient.py [--draws 4]
Output: results/EXP-069/label_efficient/
"""
from __future__ import annotations

import argparse
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

from oran_ids.data import load_network_shared, load_target_d_b  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402
from experiments.run_transfer import subsample  # noqa: E402
from experiments.run_transfer_v2 import TAU_GRID, counts_at  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-069" / "label_efficient"
MODEL_SEED = 11
KS = (1, 2, 4, 8)
N_TGT_WITH_SOURCE = 60_000
N_TGT_ONLY = 240_000
MODELS = ("logreg", "tree", "rf", "xgboost", "hgb", "mlp")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=4)
    ap.add_argument("--variants", nargs="+", default=["source+k", "target-only"])
    ap.add_argument("--models", nargs="*", default=list(MODELS))
    ap.add_argument("--shard", default="0/1", help="i/n: every n-th (k, draw) config")
    a = ap.parse_args()
    si, sn = (int(x) for x in a.shard.split("/"))
    global OUT
    if sn > 1:
        OUT = OUT.parent / f"label_efficient__shard{si}of{sn}"   # own path (D-014)
    t_start = time.time()
    for d in ("raw", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    src = load_network_shared()
    b = load_target_d_b(reason="EXP-069 label-efficient arm (labelled target files)",
                        groups="capture_file")
    gb = np.asarray(b.groups).astype(str)
    is_copy = np.char.endswith(gb, "|c")
    file_id = np.array([int(s.split("|")[0]) for s in gb])
    y_pub = np.asarray(b.y).astype(np.int8)
    y_rel = np.where(is_copy, 1, y_pub).astype(np.int8)

    rows, sweeps, gcounts, draws_log = [], [], [], []
    configs = [(k, r) for k in KS for r in range(a.draws)][si::sn]
    for k in KS:
        for r in range(a.draws):
            if (k, r) not in configs:
                continue
            seed = 101 + r                       # the transfer split this draw uses
            rng = np.random.default_rng(10_000 * k + r)
            drawn = np.sort(rng.choice(np.arange(1, 21), size=k, replace=False))
            held = np.setdiff1d(np.arange(1, 21), drawn)
            draws_log.append(dict(k=k, draw=r, split_seed=seed, drawn=drawn.tolist()))
            lab = np.flatnonzero(np.isin(file_id, drawn))
            te = np.flatnonzero(np.isin(file_id, held))

            # D_A training set and held-out fold of transfer split `seed`
            Xs, ys, cs, gs = subsample(src.X, np.asarray(src.y), np.asarray(src.category),
                                       np.asarray(src.groups).astype(str), 300_000, seed)
            sp = group_disjoint_split(ys, gs, seed=seed, n_folds=1)[0]
            Xa_tr, ya_tr = Xs.iloc[sp.train_idx], ys[sp.train_idx]
            Xa_te, ya_te = Xs.iloc[sp.test_idx], ys[sp.test_idx]

            for variant in a.variants:
                n_t = N_TGT_WITH_SOURCE if variant == "source+k" else N_TGT_ONLY
                rs = np.random.default_rng(20_000 * k + 100 * r + (variant == "source+k"))
                pick = np.sort(rs.choice(lab, size=min(n_t, len(lab)), replace=False))
                Xt_tr, yt_tr = b.X.iloc[pick], y_rel[pick]
                if variant == "source+k":
                    Xtr = pd.concat([Xa_tr, Xt_tr], ignore_index=True)
                    ytr = np.r_[ya_tr, yt_tr]
                else:
                    Xtr, ytr = Xt_tr.reset_index(drop=True), yt_tr
                if len(np.unique(ytr)) < 2:
                    print(f"  k={k} draw {r} {variant}: one class only, skipped", flush=True)
                    continue
                for key in a.models:
                    t0 = time.time()
                    model = fit_model(key, Xtr, ytr, MODEL_SEED)
                    s_src = predict_scores(model, Xa_te)
                    s_te = predict_scores(model, b.X.iloc[te])
                    doms = [("source_heldout", ya_te, s_src, np.full(len(ya_te), "src")),
                            ("target_relab", y_rel[te], s_te, gb[te]),
                            ("target_clean", y_pub[te][~is_copy[te]], s_te[~is_copy[te]],
                             gb[te][~is_copy[te]])]
                    for dom, yy, ss, gg in doms:
                        m = detection_metrics(yy, ss, 0.5)
                        base = dict(k=k, draw=r, variant=variant, model=key, split_seed=seed,
                                    domain=dom, n_train=len(ytr), n_train_target=len(pick),
                                    n_eval=len(yy))
                        rows.append({**base, **m})
                        c = counts_at(yy, ss, TAU_GRID)
                        for kk, vv in list(base.items())[::-1]:
                            if kk not in ("n_eval",):
                                c.insert(0, kk, vv)
                        sweeps.append(c)
                        if dom != "source_heldout":
                            for g in np.unique(gg):
                                mk = gg == g
                                cg = counts_at(yy[mk], ss[mk], TAU_GRID)
                                cg.insert(0, "group", g)
                                for kk in ("domain", "model", "variant", "draw", "k"):
                                    cg.insert(0, kk, base[kk])
                                gcounts.append(cg)
                    print(f"  k={k} draw {r} {variant:<11} {key:<8} BA src "
                          f"{rows[-3]['balanced_accuracy']:.3f} relab "
                          f"{rows[-2]['balanced_accuracy']:.3f} clean "
                          f"{rows[-1]['balanced_accuracy']:.3f}  {time.time() - t0:.1f}s",
                          flush=True)
                pd.DataFrame(rows).to_csv(OUT / "raw/runs.csv", index=False)

    pd.DataFrame(rows).to_csv(OUT / "raw/runs.csv", index=False)
    pd.concat(sweeps).to_csv(OUT / "raw/tau_counts.csv", index=False)
    pd.concat(gcounts).to_csv(OUT / "raw/tau_counts_by_group.csv", index=False)
    pd.DataFrame(draws_log).to_csv(OUT / "raw/draws.csv", index=False)
    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-069 label-efficient", ks=KS, draws=a.draws, variants=a.variants,
        models=a.models, n_target_with_source=N_TGT_WITH_SOURCE, n_target_only=N_TGT_ONLY,
        copies_in_training="relabelled as attack", model_seed=MODEL_SEED,
        d_b_byte_accounting="Ethernet header removed, 14 B per packet (D-035)",
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t_start, 1)), indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {OUT}  ({time.time() - t_start:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
