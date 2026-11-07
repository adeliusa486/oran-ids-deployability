#!/usr/bin/env python3
"""Revision 1 transfer runner: one trained model, every target (EXP-064 ...).

Why a new runner. The first submission left the 14-byte Ethernet header in
every 5G-NIDD byte count (D-035, reviewer R1.9), so every result that puts
5G-NIDD in the shared space is re-measured. The reviewers also asked for
analyses that need more than per-split summaries: copies relabelled as attack
(R2.2e), a deployability test with thresholds fixed without target labels and
intervals on both terms (R1.7), a cluster bootstrap for Delta_BA (R2.4), and
references compared on matched target flows (R2.3). This runner therefore

  * trains each model ONCE per split and scores it on every requested target,
    so the targets are paired by construction (5G-NIDD as exported by Argus,
    5G-NIDD re-extracted with Zeek, and the third corpus D_C);
  * stores confusion counts per threshold per cluster (source addresses or
    capture files; the 5G-NIDD flood copies are their own cluster "5|c");
  * optionally stores every per-flow score (float32, ``scores/``, not
    committed), so later analyses need no retraining;
  * adds two adaptation methods built for distribution shift (R1.12, R2.6):
    importance weighting by a domain classifier and a domain-adversarial
    network (DANN, ``oran_ids.models.dann``).

Unchanged from EXP-026/EXP-041 and not to be changed after seeing a result:
split seeds 101-120, model seed 11, a seeded 300,000-flow source sample, a
group-disjoint split (source address for D_A; capture file for 5G-NIDD as
source), threshold 0.5 for the tables, every target evaluated whole.

Usage (see EXPERIMENTS.md, revision 1):
  python experiments/run_transfer_r1.py --exp EXP-064 --source a --targets b bz c \
      --sweeps --reliability --scores
  python experiments/run_transfer_r1.py --exp EXP-065 --source a --targets b bz c \
      --features robust --sweeps --scores
  python experiments/run_transfer_r1.py --exp EXP-066 --source a --targets b --adapt coral --sweeps
  python experiments/run_transfer_r1.py --exp EXP-067 --source b --targets a c --sweeps --scores
  python experiments/run_transfer_r1.py --exp EXP-069 --source a --targets b --adapt iw --sweeps --scores
  python experiments/run_transfer_r1.py --exp EXP-069 --source a --targets b --adapt dann --sweeps --scores
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
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from sklearn.utils.class_weight import compute_sample_weight  # noqa: E402

from oran_ids.data import (load_network_shared, load_target_d_b,  # noqa: E402
                           load_target_d_b_zeek, load_target_d_c)
from oran_ids.features.shared import assert_compatible  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from oran_ids.models.zoo import build  # noqa: E402
from oran_ids.models.dann import DANN  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402
from experiments.run_transfer import per_category_recall, subsample  # noqa: E402
from experiments.run_transfer_v2 import (Coral, ROBUST_COLUMNS, TAU_GRID,  # noqa: E402
                                         counts_at, reliability_bins)

warnings.filterwarnings("ignore")

SPLIT_SEEDS = list(range(101, 121))
MODEL_SEED = 11
THRESHOLD = 0.5
NONTRIVIAL = ("logreg", "tree", "rf", "xgboost", "hgb", "mlp")
IW_CLIP = (0.01, 0.99)       # weights clipped at these quantiles (D-036)


# ---------------------------------------------------------------- corpora
def load_corpus(name: str, reason: str, as_source: bool):
    if name == "a":
        return load_network_shared()
    if name == "b":
        return load_target_d_b(reason=reason + (" (as SOURCE)" if as_source else ""),
                               groups="capture_file")
    if name == "bz":
        return load_target_d_b_zeek(reason=reason)
    if name == "c":
        return load_target_d_c(reason=reason)
    raise ValueError(name)


def split_groups(corpus, name: str) -> np.ndarray:
    """The group key a SOURCE split is disjoint on."""
    g = np.asarray(corpus.groups).astype(str)
    if name == "b":
        # the copies carry the suffix "|c" for evaluation; a split must keep
        # the whole capture file on one side
        return np.array([s.split("|")[0] for s in g])
    return g


def select(X: pd.DataFrame, features: str) -> pd.DataFrame:
    return X[list(ROBUST_COLUMNS)] if features == "robust" else X


# ---------------------------------------------------------- weighted fits
def importance_weights(Xs: np.ndarray, Xt: np.ndarray, seed: int):
    """Density ratio p_t(x)/p_s(x) from a probabilistic domain classifier.

    Bickel, Brueckner and Scheffer (JMLR 2009); Sugiyama et al. (2012).
    Logistic regression on standardised features, trained on the source
    training rows against an equal-size random sample of target rows, so the
    odds estimate the density ratio up to a constant. Weights are clipped at
    their 1st and 99th percentiles and normalised to mean 1 (declared, D-036).
    """
    rng = np.random.default_rng(seed)
    jt = rng.choice(len(Xt), size=min(len(Xs), len(Xt)), replace=len(Xt) < len(Xs))
    Z = np.vstack([Xs, Xt[jt]])
    d = np.r_[np.zeros(len(Xs)), np.ones(len(jt))]
    sc = StandardScaler().fit(Z)
    clf = LogisticRegression(max_iter=2000).fit(sc.transform(Z), d)
    logit = clf.decision_function(sc.transform(Xs))
    w = np.exp(np.clip(logit, -30, 30))
    lo, hi = np.quantile(w, IW_CLIP)
    w = np.clip(w, lo, hi)
    w = w / w.mean()
    ess = float(w.sum() ** 2 / (w ** 2).sum())
    dom_acc = float(((clf.decision_function(sc.transform(Z)) > 0) == d).mean())
    return w, dict(iw_ess=ess, iw_ess_frac=ess / len(w), iw_domain_acc=dom_acc,
                   iw_w_max=float(w.max()), iw_w_min=float(w.min()))


def fit_weighted(key: str, X, y, seed: int, w: np.ndarray):
    """fit_model with extra per-row weights, keeping each family's class policy."""
    if key in ("majority", "stratified"):
        return fit_model(key, X, y, seed)
    model = build(key, seed)
    if key == "logreg":
        model.fit(X, y, clf__sample_weight=w)          # times class_weight
        return model
    if key == "mlp":
        wb = compute_sample_weight("balanced", np.asarray(y)) * w
        model.fit(X, y, clf__sample_weight=wb)
        return model
    if key == "xgboost":
        n_pos, n_neg = float((y == 1).sum()), float((y == 0).sum())
        if n_pos > 0:
            model.set_params(scale_pos_weight=max(n_neg / n_pos, 1e-6))
    model.fit(X, y, sample_weight=w)                   # times class_weight
    return model


# ------------------------------------------------------------------- run
def run(a) -> None:
    t_start = time.time()
    out = ROOT / "results" / a.exp / a.tag
    for sub in ("raw", "processed", "statistics", "logs"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    if a.scores:
        (out / "scores").mkdir(exist_ok=True)

    reason = f"{a.exp} {a.tag}"
    src = load_corpus(a.source, reason, as_source=True)
    Xsrc_all = select(src.X, a.features)
    gsrc_all = split_groups(src, a.source)
    tgts = {}
    for t in a.targets:
        c = load_corpus(t, reason, as_source=False)
        Xt = select(c.X, a.features)
        if a.features == "shared":
            assert_compatible(Xsrc_all, Xt)
        else:
            assert tuple(Xsrc_all.columns) == tuple(Xt.columns)
        tgts[t] = dict(corpus=c, X=Xt, y=np.asarray(c.y), g=np.asarray(c.groups).astype(str),
                       cat=np.asarray(c.category))
        print(f"[{a.tag}] target {t}: {c.name} {Xt.shape} attack {c.y.mean():.4f}",
              flush=True)
        if a.scores:
            np.savez_compressed(out / "scores" / f"target__{t}__meta.npz",
                                y=tgts[t]["y"], groups=tgts[t]["g"], category=tgts[t]["cat"])
    print(f"[{a.tag}] source {a.source}: {src.name} {Xsrc_all.shape} "
          f"attack {src.y.mean():.4f}", flush=True)

    if a.adapt == "dann":
        models = ["dann"]
    else:
        models = a.models or [m.key for m in LADDER]
    si, sn = (int(x) for x in a.shard.split("/"))
    seeds = SPLIT_SEEDS[: a.seeds][si::sn]
    if a.seed_list:
        seeds = [int(x) for x in a.seed_list]
    rows, cats, sweeps, rel, gcounts, extra = [], [], [], [], [], []

    for si, seed in enumerate(seeds):
        Xs, ys, cs, gs = subsample(Xsrc_all, np.asarray(src.y), np.asarray(src.category),
                                   gsrc_all, a.n_sub, seed)
        sp = group_disjoint_split(ys, gs, seed=seed, n_folds=1)[0]
        sp.check_disjoint(gs)
        Xtr, ytr = Xs.iloc[sp.train_idx], ys[sp.train_idx]
        Xte, yte = Xs.iloc[sp.test_idx], ys[sp.test_idx]
        gte, cte = gs[sp.test_idx], cs[sp.test_idx]
        n_tr_groups, n_te_groups = len(np.unique(gs[sp.train_idx])), len(np.unique(gte))

        evals = {t: d["X"] for t, d in tgts.items()}
        weights, info = None, {}
        if a.adapt in ("coral", "iw", "dann"):
            assert len(tgts) == 1, f"--adapt {a.adapt} adapts to exactly one target"
            (t0name, Xt0), = evals.items()
        if a.adapt == "coral":
            cor = Coral().fit(Xtr.to_numpy(np.float64), Xt0.to_numpy(np.float64))
            cols = list(Xtr.columns)
            Xtr = pd.DataFrame(cor.source(Xtr.to_numpy(np.float64)), columns=cols).astype(np.float32)
            Xte = pd.DataFrame(cor.source(Xte.to_numpy(np.float64)), columns=cols).astype(np.float32)
            evals = {t0name: pd.DataFrame(cor.target(Xt0.to_numpy(np.float64)),
                                          columns=cols).astype(np.float32)}
        elif a.adapt == "iw":
            weights, info = importance_weights(Xtr.to_numpy(np.float64),
                                               Xt0.to_numpy(np.float64), seed)
            extra.append(dict(split_seed=seed, **info))
            print(f"  seed {seed}: IW ESS {info['iw_ess_frac']:.4f} of n, domain acc "
                  f"{info['iw_domain_acc']:.3f}", flush=True)

        seed_scores = {"source_heldout": {}}
        seed_scores.update({t: {} for t in evals})
        for key in models:
            t0 = time.time()
            if key == "dann":
                model = DANN(seed=MODEL_SEED + seed).fit(Xtr.to_numpy(), ytr, Xt0.to_numpy())
                extra.append(dict(split_seed=seed, **{f"dann_{k}": v for k, v in
                                                      model.history[-1].items()}))
            elif weights is not None:
                model = fit_weighted(key, Xtr, ytr, MODEL_SEED, weights)
            else:
                model = fit_model(key, Xtr, ytr, MODEL_SEED)
            s_src = predict_scores(model, Xte)
            domains = [("source_heldout", yte, s_src, cte, gte)]
            for t, Xt in evals.items():
                domains.append((t, tgts[t]["y"], predict_scores(model, Xt),
                                tgts[t]["cat"], tgts[t]["g"]))
            for dom, yy, ss, cc, gg in domains:
                m = detection_metrics(yy, ss, THRESHOLD)
                rows.append(dict(model=key, split_seed=seed, domain=dom,
                                 n_train=len(ytr), n_eval=len(yy),
                                 n_train_groups=n_tr_groups, n_test_groups=n_te_groups,
                                 train_prevalence=float(ytr.mean()), **m))
                if a.sweeps:
                    c = counts_at(yy, ss, TAU_GRID)
                    c.insert(0, "domain", dom)
                    c.insert(0, "split_seed", seed)
                    c.insert(0, "model", key)
                    sweeps.append(c)
                # counts per cluster, for the cluster bootstrap (R2.4)
                order = np.argsort(gg, kind="mergesort")
                gsorted = gg[order]
                cuts = np.flatnonzero(np.r_[True, gsorted[1:] != gsorted[:-1], True])
                for i in range(len(cuts) - 1):
                    idx = order[cuts[i]:cuts[i + 1]]
                    c = counts_at(yy[idx], ss[idx], TAU_GRID)
                    c.insert(0, "group", gsorted[cuts[i]])
                    c.insert(0, "domain", dom)
                    c.insert(0, "split_seed", seed)
                    c.insert(0, "model", key)
                    gcounts.append(c)
                if a.reliability:
                    for b, ms, fr, n in reliability_bins(yy, ss):
                        rel.append(dict(model=key, split_seed=seed, domain=dom, bin=b,
                                        mean_score=ms, attack_freq=fr, n=n))
                pred = (ss >= THRESHOLD).astype(int)
                cats.append(dict(model=key, split_seed=seed, domain=dom,
                                 **per_category_recall(yy, cc, pred)))
                if a.scores and key not in ("majority", "stratified"):
                    seed_scores[dom][key] = ss.astype(np.float32)
            msg = " ".join(f"{r['domain']}={r['balanced_accuracy']:.3f}"
                           for r in rows[-len(domains):])
            print(f"  seed {seed} [{si + 1}/{len(seeds)}] {key:<10} BA {msg}  "
                  f"{time.time() - t0:.1f}s", flush=True)

        if a.scores:
            np.savez_compressed(out / "scores" / f"seed{seed}__source_heldout.npz",
                                y=yte, groups=gte, category=cte,
                                **seed_scores["source_heldout"])
            for t in evals:
                np.savez_compressed(out / "scores" / f"seed{seed}__{t}.npz", **seed_scores[t])
        # checkpoint after every split, so a crash loses at most one split
        pd.DataFrame(rows).to_csv(out / "raw/runs.csv", index=False)

    pd.DataFrame(rows).to_csv(out / "raw/runs.csv", index=False)
    pd.DataFrame(cats).to_csv(out / "processed/per_category_recall.csv", index=False)
    if sweeps:
        pd.concat(sweeps).to_csv(out / "raw/tau_counts.csv", index=False)
    if gcounts:
        pd.concat(gcounts).to_csv(out / "raw/tau_counts_by_group.csv", index=False)
    if rel:
        pd.DataFrame(rel).to_csv(out / "raw/reliability_bins.csv", index=False)
    if extra:
        pd.DataFrame(extra).to_csv(out / "raw/adaptation_diagnostics.csv", index=False)

    prov = dict(
        experiment=a.exp, tag=a.tag, source=a.source, targets=a.targets,
        features=a.features, columns=list(Xsrc_all.columns), adapt=a.adapt,
        models=models, split_seeds=seeds, model_seed=MODEL_SEED, threshold=THRESHOLD,
        source_subsample=a.n_sub, tau_grid=TAU_GRID.tolist(),
        source_split=("group_disjoint(src_ip)" if a.source == "a"
                      else "group_disjoint(capture_file)"),
        d_b_byte_accounting="Ethernet header removed, 14 B per packet (D-035)",
        iw_clip_quantiles=IW_CLIP if a.adapt == "iw" else None,
        dann=("d-64-32 / 32-1 / 32-32-1, Adam 1e-3, batch 256+256, 5 epochs, "
              "Ganin lambda schedule (D-036)") if a.adapt == "dann" else None,
        target_reads_unlabelled_features=a.adapt in ("coral", "iw", "dann"),
        source_summary=src.summary(),
        target_summaries={t: d["corpus"].summary() for t, d in tgts.items()},
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t_start, 1))
    (out / "statistics/provenance.json").write_text(json.dumps(prov, indent=2, default=str),
                                                     encoding="utf-8")
    print(f"\nwrote {out}  ({time.time() - t_start:.0f}s)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True)
    ap.add_argument("--source", choices=["a", "b"], default="a")
    ap.add_argument("--targets", nargs="+", choices=["a", "b", "bz", "c"], required=True)
    ap.add_argument("--features", choices=["shared", "robust"], default="shared")
    ap.add_argument("--adapt", choices=["none", "coral", "iw", "dann"], default="none")
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--n-sub", type=int, default=300_000)
    ap.add_argument("--sweeps", action="store_true")
    ap.add_argument("--reliability", action="store_true")
    ap.add_argument("--scores", action="store_true")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--shard", default="0/1", help="i/n: run every n-th split seed from i")
    ap.add_argument("--seed-list", nargs="*", default=None,
                    help="explicit split seeds (own output path, see --tag)")
    a = ap.parse_args()
    if a.source in a.targets:
        raise SystemExit("source and target must differ")
    a.tag = a.tag or "__".join([f"{a.source}_to_{'_'.join(a.targets)}", a.features]
                               + ([a.adapt] if a.adapt != "none" else [])
                               + ([f"n{a.n_sub}"] if a.n_sub != 300_000 else []))
    if a.shard != "0/1":
        a.tag += "__shard{}of{}".format(*a.shard.split("/"))   # own path (D-014)
    if a.seed_list:
        a.tag += "__seeds{}-{}".format(a.seed_list[0], a.seed_list[-1])   # own path
    run(a)


if __name__ == "__main__":
    main()
