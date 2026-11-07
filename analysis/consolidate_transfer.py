#!/usr/bin/env python3
"""Consolidate a revision-1 transfer experiment from its per-flow scores.

The transfer runs of revision 1 (EXP-064, -065, -067, -066, -069) were split
over several processes (``--seed-list``/``--shard``), each writing its own
output folder (D-014). Every process stores the per-flow scores of every split,
so this script rebuilds all per-split outputs from the scores, in one place and
in one way, whatever process produced them:

  runs.csv                  metrics at tau = 0.5 per model, split, domain, view
  tau_counts_by_group.parquet  confusion counts per cluster on a fine threshold
                            grid (clusters: source addresses or capture files;
                            the 5G-NIDD copies are cluster '5|c')
  per_category_recall.csv   recall per attack category at tau = 0.5
  reliability_bins.csv      equal-mass bins (15) per model, split, domain

Views of the 5G-NIDD targets (b, bz): 'all' (published labels), 'clean' (the
benign-labelled flood copies removed), 'relab' (copies relabelled as attack,
Reviewer 2 R2.2e). Other domains have one view, 'all'.

The trivial baselines store no scores; their rows come from the runners'
runs.csv checkpoints.

Usage:  python analysis/consolidate_transfer.py EXP-064 a_to_b_bz_c__shared
Output: results/<EXP>/consolidated__<tag>/
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.metrics import detection_metrics  # noqa: E402
from experiments.run_transfer import per_category_recall  # noqa: E402
from experiments.run_transfer_v2 import counts_at, reliability_bins  # noqa: E402

# fine grid: 0.005 steps, plus thresholds close to 1 where the alert bound bites
TAU_FINE = np.unique(np.round(np.r_[np.linspace(0.0, 1.0, 201),
                                    1.0 - np.logspace(-6, -2, 25)], 8))
TRIVIAL = ("majority", "stratified")


def views_for(domain: str, y: np.ndarray, groups: np.ndarray):
    if domain in ("b", "bz"):
        copy = np.char.endswith(groups.astype(str), "|c")
        return {"all": (np.ones(len(y), bool), y),
                "clean": (~copy, y),
                "relab": (np.ones(len(y), bool), np.where(copy, 1, y).astype(np.int8))}
    return {"all": (np.ones(len(y), bool), y)}


def grouped_counts(y, s, g, taus):
    order = np.argsort(g, kind="mergesort")
    gs = g[order]
    cuts = np.flatnonzero(np.r_[True, gs[1:] != gs[:-1], True])
    out = []
    for i in range(len(cuts) - 1):
        ix = order[cuts[i]:cuts[i + 1]]
        c = counts_at(y[ix], s[ix], taus)
        c.insert(0, "group", gs[cuts[i]])
        out.append(c)
    return pd.concat(out, ignore_index=True)


def main(exp: str, base_tag: str, reliability: bool = True) -> int:
    root = ROOT / "results" / exp
    dirs = sorted(d for d in root.glob(base_tag + "*") if (d / "scores").is_dir()
                  and not d.name.startswith("consolidated"))
    if not dirs:
        raise SystemExit(f"no score folders under {root}/{base_tag}*")
    out = root / f"consolidated__{base_tag}"
    out.mkdir(exist_ok=True)

    meta = {}
    for d in dirs:
        for f in (d / "scores").glob("target__*__meta.npz"):
            t = f.name.split("__")[1]
            meta.setdefault(t, dict(np.load(f, allow_pickle=True)))
    seed_files = {}
    for d in dirs:
        for f in (d / "scores").glob("seed*__source_heldout.npz"):
            seed = int(re.match(r"seed(\d+)__", f.name).group(1))
            seed_files.setdefault(seed, d / "scores")
    seeds = sorted(seed_files)
    print(f"{exp}/{base_tag}: {len(dirs)} folder(s), splits {seeds}", flush=True)

    trivial = []
    for d in dirs:
        p = d / "raw/runs.csv"
        if p.exists():
            r = pd.read_csv(p)
            trivial.append(r[r.model.isin(TRIVIAL)])
    trivial = (pd.concat(trivial).drop_duplicates(["model", "split_seed", "domain"])
               if trivial else pd.DataFrame())

    from concurrent.futures import ProcessPoolExecutor
    jobs = [(seed, seed_files[seed], meta, reliability) for seed in seeds]
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        parts = list(ex.map(_one_seed, jobs))
    rows = [r for p in parts for r in p[0]]
    gcounts = [g for p in parts for g in p[1]]
    cats = [c for p in parts for c in p[2]]
    rel = [r for p in parts for r in p[3]]
    _write(out, rows, gcounts, cats, rel, trivial)
    return 0


def _one_seed(job):
    seed, sdir, meta, reliability = job
    rows, gcounts, cats, rel = [], [], [], []
    if True:
        src = dict(np.load(sdir / f"seed{seed}__source_heldout.npz", allow_pickle=True))
        models = [k for k in src if k not in ("y", "groups", "category")]
        domains = {"source_heldout": (src["y"], src["groups"].astype(str), src["category"],
                                      {m: src[m] for m in models})}
        for t, mt in meta.items():
            f = sdir / f"seed{seed}__{t}.npz"
            if f.exists():
                sc = dict(np.load(f))
                domains[t] = (mt["y"], mt["groups"].astype(str), mt["category"], sc)
        for dom, (y, g, cat, scores) in domains.items():
            for m, s in scores.items():
                s = s.astype(np.float64)
                for vname, (mk, yv) in views_for(dom, y, g).items():
                    yy, ss, gg = yv[mk], s[mk], g[mk]
                    met = detection_metrics(yy, ss, 0.5)
                    rows.append(dict(model=m, split_seed=seed, domain=dom, view=vname,
                                     n_eval=int(mk.sum()), **met))
                    c = grouped_counts(yy, ss, gg, TAU_FINE)
                    c.insert(0, "view", vname)
                    c.insert(0, "domain", dom)
                    c.insert(0, "split_seed", seed)
                    c.insert(0, "model", m)
                    gcounts.append(c)
                    if vname == "all":
                        pred = (ss >= 0.5).astype(int)
                        cats.append(dict(model=m, split_seed=seed, domain=dom,
                                         **per_category_recall(yy, cat[mk], pred)))
                    if reliability and vname in ("all", "clean"):
                        for b, ms, fr, n in reliability_bins(yy, ss):
                            rel.append(dict(model=m, split_seed=seed, domain=dom, view=vname,
                                            bin=b, mean_score=ms, attack_freq=fr, n=n))
        print(f"  split {seed}: {len(models)} models, domains {list(domains)}", flush=True)
    return rows, gcounts, cats, rel


def _write(out, rows, gcounts, cats, rel, trivial):
    runs = pd.DataFrame(rows)
    if len(trivial):
        tv = trivial.copy()
        tv["view"] = "all"
        runs = pd.concat([runs, tv[[c for c in tv.columns if c in runs.columns or c == "view"]]],
                         ignore_index=True)
    runs.to_csv(out / "runs.csv", index=False)
    pd.concat(gcounts, ignore_index=True).to_parquet(out / "tau_counts_by_group.parquet",
                                                     index=False)
    pd.DataFrame(cats).to_csv(out / "per_category_recall.csv", index=False)
    if rel:
        pd.DataFrame(rel).to_csv(out / "reliability_bins.csv", index=False)
    print(f"wrote {out}")


WORKERS = 4

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2],
                  reliability=not (len(sys.argv) > 3 and sys.argv[3] == "--no-reliability")))
