#!/usr/bin/env python3
"""EXP-068: in-target references on 5G-NIDD, with intervals (R1.4, R1.5, R2.3).

The first submission's references (EXP-054) used one to three training samples
per protocol and reported no intervals; its capture-file reference never held
out a UDP-flood file; and it trained on the published labels, so models learned
the flood copies as benign. This runner, on the byte-corrected shared space
(D-035), measures three designs:

  random   a seeded 300,000-flow sample split 80/20, 20 split seeds (the
           optimistic reference, same seeds as the transfer)
  lofo     leave one capture file out: each of the 20 files is held out once,
           so both UDP-flood files are held out; the pooled predictions cover
           every flow of 5G-NIDD exactly once, which makes them comparable flow
           for flow with the transfer evaluation (R2.3)
  station  train on one base station's ten files, test on the other's, with
           repeated training samples

and two label variants:

  clean    the 281,5xx benign-labelled flood copies (EXP-057/062) are removed
           from training; they are also excluded from the 'clean' evaluation
  relab    the copies are relabelled as attack in training and evaluation
           (Reviewer 2, R2.2e), which keeps the traffic a detector would see

Every model trains on 240,000 flows, the size of the transfer training sets
(80% of the 300,000-flow source sample), so the references and the transfer
use the same amount of labelled data (R2.8).

Usage:
  python experiments/run_target_reference_r1.py --design random  --labels clean --seeds 20
  python experiments/run_target_reference_r1.py --design lofo    --labels clean --scores
  python experiments/run_target_reference_r1.py --design lofo    --labels relab --scores
  python experiments/run_target_reference_r1.py --design station --labels clean --seeds 10 --scores
  python experiments/run_target_reference_r1.py --design station --labels relab --seeds 5 --scores
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

from oran_ids.data import load_target_d_b  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from experiments.run_transfer_v2 import TAU_GRID, counts_at  # noqa: E402

warnings.filterwarnings("ignore")

MODEL_SEED = 11
SPLIT_SEEDS = list(range(101, 121))
SUBSAMPLE = 300_000
N_TRAIN = 240_000
THRESHOLD = 0.5


def load():
    c = load_target_d_b(reason="EXP-068 in-target references (5G-NIDD as SOURCE and target)",
                        groups="capture_file")
    g = np.asarray(c.groups).astype(str)
    is_copy = np.char.endswith(g, "|c")
    file_id = np.array([int(s.split("|")[0]) for s in g])
    station = np.where(file_id <= 10, 1, 2)
    return c, np.asarray(c.y).astype(np.int8), g, is_copy, file_id, station


def views(y_pub, is_copy):
    """Evaluation views of one test set: masks and labels."""
    y_rel = np.where(is_copy, 1, y_pub).astype(np.int8)
    return {"all": (np.ones(len(y_pub), bool), y_pub),
            "clean": (~is_copy, y_pub),
            "relab": (np.ones(len(y_pub), bool), y_rel)}


def training_labels(y_pub, is_copy, labels: str):
    """(row mask, labels) of the training pool under a label variant."""
    if labels == "clean":
        return ~is_copy, y_pub
    return np.ones(len(y_pub), bool), np.where(is_copy, 1, y_pub).astype(np.int8)


def draw(idx: np.ndarray, n: int, seed: int) -> np.ndarray:
    if len(idx) <= n:
        return idx
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(idx, size=n, replace=False))


def run(a) -> None:
    t_start = time.time()
    tag = f"{a.design}__{a.labels}"
    si, sn = (int(x) for x in a.shard.split("/"))
    if sn > 1:
        tag += f"__shard{si}of{sn}"     # own output path per shard (D-014)
    out = ROOT / "results" / a.exp / tag
    for sub in ("raw", "statistics", "logs"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    if a.scores:
        (out / "scores").mkdir(exist_ok=True)

    c, y_pub, g, is_copy, file_id, station = load()
    X = c.X
    pool_mask, y_train_all = training_labels(y_pub, is_copy, a.labels)
    print(f"[{tag}] 5G-NIDD {X.shape}, copies {is_copy.sum():,}, "
          f"training pool {pool_mask.sum():,}", flush=True)

    # (unit id, train indices, test indices)
    units = []
    if a.design == "random":
        pool = np.flatnonzero(pool_mask)
        for seed in SPLIT_SEEDS[: a.seeds]:
            s = draw(pool, SUBSAMPLE, seed)
            rng = np.random.default_rng(seed)
            perm = rng.permutation(len(s))
            cut = int(0.8 * len(s))
            units.append((f"seed{seed}", np.sort(s[perm[:cut]]), np.sort(s[perm[cut:]])))
    elif a.design == "lofo":
        for f in range(1, 21):
            tr_pool = np.flatnonzero(pool_mask & (file_id != f))
            units.append((f"file{f}", draw(tr_pool, N_TRAIN, 100 + f),
                          np.flatnonzero(file_id == f)))
    else:  # station
        for direction, (s_tr, s_te) in (("s1_to_s2", (1, 2)), ("s2_to_s1", (2, 1))):
            tr_pool = np.flatnonzero(pool_mask & (station == s_tr))
            te = np.flatnonzero(station == s_te)
            for seed in SPLIT_SEEDS[: a.seeds]:
                units.append((f"{direction}__seed{seed}", draw(tr_pool, N_TRAIN, seed), te))

    units = units[si::sn]
    models = a.models or [m.key for m in LADDER]
    rows, gcounts = [], []
    for ui, (unit, tr, te) in enumerate(units):
        Xtr, ytr = X.iloc[tr], y_train_all[tr]
        Xte = X.iloc[te]
        vws = views(y_pub[te], is_copy[te])
        if a.design == "random":
            # the random test set is drawn from the variant's own pool
            vws = {("clean" if a.labels == "clean" else "relab"):
                   (np.ones(len(te), bool), y_train_all[te])}
        unit_scores = {}
        for key in models:
            t0 = time.time()
            if len(np.unique(ytr)) < 2:
                print(f"  {unit}: one class in training, skipped", flush=True)
                break
            model = fit_model(key, Xtr, ytr, MODEL_SEED)
            s = predict_scores(model, Xte)
            for vname, (mk, yv) in vws.items():
                if mk.sum() == 0:
                    continue
                yy, ss, gg = yv[mk], s[mk], g[te][mk]
                m = (detection_metrics(yy, ss, THRESHOLD) if len(np.unique(yy)) > 1
                     else dict(n=int(len(yy)), fpr=float((ss[yy == 0] >= THRESHOLD).mean())
                               if (yy == 0).any() else float("nan"),
                               recall=float((ss[yy == 1] >= THRESHOLD).mean())
                               if (yy == 1).any() else float("nan")))
                rows.append(dict(design=a.design, labels=a.labels, unit=unit, model=key,
                                 view=vname, n_train=len(tr), n_eval=int(mk.sum()),
                                 train_prevalence=float(ytr.mean()),
                                 eval_prevalence=float(yy.mean()), **m))
                order = np.argsort(gg, kind="mergesort")
                gs = gg[order]
                cuts = np.flatnonzero(np.r_[True, gs[1:] != gs[:-1], True])
                for i in range(len(cuts) - 1):
                    ix = order[cuts[i]:cuts[i + 1]]
                    cc = counts_at(yy[ix], ss[ix], TAU_GRID)
                    cc.insert(0, "group", gs[cuts[i]])
                    cc.insert(0, "view", vname)
                    cc.insert(0, "unit", unit)
                    cc.insert(0, "model", key)
                    gcounts.append(cc)
            if a.scores and key not in ("majority", "stratified"):
                unit_scores[key] = s.astype(np.float32)
            ba = {r["view"]: r.get("balanced_accuracy", float("nan"))
                  for r in rows[-len(vws):]}
            print(f"  [{ui + 1}/{len(units)}] {unit:<22} {key:<10} "
                  + " ".join(f"{k}={v:.3f}" for k, v in ba.items())
                  + f"  {time.time() - t0:.1f}s", flush=True)
        if a.scores and unit_scores:
            np.savez_compressed(out / "scores" / f"{unit}.npz", test_idx=te, **unit_scores)
        pd.DataFrame(rows).to_csv(out / "raw/runs.csv", index=False)

    pd.DataFrame(rows).to_csv(out / "raw/runs.csv", index=False)
    if gcounts:
        pd.concat(gcounts).to_csv(out / "raw/tau_counts_by_group.csv", index=False)
    prov = dict(experiment=a.exp, design=a.design, labels=a.labels, models=models,
                units=[u for u, _, _ in units], model_seed=MODEL_SEED,
                n_train=N_TRAIN, random_subsample=SUBSAMPLE, threshold=THRESHOLD,
                tau_grid=TAU_GRID.tolist(),
                d_b_byte_accounting="Ethernet header removed, 14 B per packet (D-035)",
                n_copies=int(is_copy.sum()), corpus=c.summary(),
                python=platform.python_version(), platform=platform.platform(),
                runtime_s=round(time.time() - t_start, 1))
    (out / "statistics/provenance.json").write_text(json.dumps(prov, indent=2, default=str),
                                                     encoding="utf-8")
    print(f"\nwrote {out}  ({time.time() - t_start:.0f}s)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="EXP-068")
    ap.add_argument("--design", choices=["random", "lofo", "station"], required=True)
    ap.add_argument("--labels", choices=["clean", "relab"], default="clean")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--scores", action="store_true")
    ap.add_argument("--shard", default="0/1", help="i/n: run every n-th unit from i")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
