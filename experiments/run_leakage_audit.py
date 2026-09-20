#!/usr/bin/env python3
"""EXP-002 (X1a): how much does the split protocol inflate the result?

The Phase 2 gate. Most published NIDS results use a random split over flow
records. Under a random split, flows from the same host -- often from the same
attack burst -- appear in both train and test, so the model can memorise the
host rather than learn the attack. A group-disjoint split removes that.

The *difference* between the two is the leakage magnitude, and it is a
reportable result rather than a diagnostic: it says how much of a typical
published number survives a protocol that reflects deployment.

Design (pre-registered before running):
  protocols   random, group_disjoint
  layers      network (src_ip groups), radio (session groups)
  models      the full ladder, including the majority-class floor
  seeds       20 split seeds x 2 model seeds  (plan A5 two-level; n raised from
              5 to 20 by D-012 on a power calculation made before the tests)
  primary     macro-F1 and PR-AUC-benign, NOT accuracy: the corpus is 76.5%
              attack at window level, so accuracy is uninformative
  CIs         paired t-interval over SPLIT means. NOT a percentile bootstrap:
              at n=5 that was anti-conservative and reported four significant
              effects the correct paired test does not support (D-012)

Hypothesis H-leak: group-disjoint scores are materially lower than random-split
scores for every non-trivial model.
Falsified if: the 95% CI on the per-model difference includes 0 for all models.

Usage:  python experiments/run_leakage_audit.py [--quick] [--layers network radio]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.data import load_network, load_radio  # noqa: E402
from oran_ids.metrics import bootstrap_ci, detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split, random_split  # noqa: E402
from scipy import stats as _st  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def interval(vals):
    """Paired t-interval, not a percentile bootstrap.

    D-012: a percentile bootstrap resampling n=5 points with replacement is
    anti-conservative -- it can only span the observed values, so it
    systematically understates uncertainty at small n. It reported four
    significant leakage effects that the correct paired test does not support.
    Bootstrap is used only when n >= 30.
    """
    v = np.asarray(vals, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) < 2:
        return (float(v[0]) if len(v) else float("nan")), float("nan"), float("nan")
    if len(v) >= 30:
        return bootstrap_ci(v, seed=7)
    if v.std(ddof=1) == 0:
        return float(v.mean()), float(v.mean()), float(v.mean())
    lo, hi = _st.t.interval(0.95, len(v) - 1, loc=v.mean(), scale=_st.sem(v))
    return float(v.mean()), float(lo), float(hi)


OUT = Path("results/EXP-002")
# D-012: raised from 5 to 20 on a power calculation written BEFORE the tests ran.
# n=20 gives 80% power at alpha=0.05 for d_z=0.63, below the smallest non-trivial
# effect observed at n=5. Run exactly 20 and report whatever results -- the
# stopping rule must not depend on the outcome.
SPLIT_SEEDS = list(range(101, 121))
MODEL_SEEDS = [11, 22]
PRIMARY = "f1_macro"
# The network layer has 1.64M rows; fitting the full ladder on all of it for
# every seed is hours of compute for a result that a stratified subsample
# settles. The subsample is declared, seeded, and its size reported.
NETWORK_SUBSAMPLE = 300_000


def subsample(X, y, cat, groups, n, seed):
    if len(y) <= n:
        return X, y, cat, groups
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(len(y), size=n, replace=False))
    return X.iloc[idx].reset_index(drop=True), y[idx], cat[idx], groups[idx]


def run_layer(name: str, corpus, models: list[str], quick: bool) -> pd.DataFrame:
    X, y, cat, groups = corpus.X, corpus.y, corpus.category, corpus.groups
    if name == "network":
        X, y, cat, groups = subsample(X, y, cat, groups, NETWORK_SUBSAMPLE, 0)
        print(f"  subsampled to {len(y):,} rows (declared, seed 0)")

    split_seeds = SPLIT_SEEDS[:2] if quick else SPLIT_SEEDS
    model_seeds = MODEL_SEEDS[:1] if quick else MODEL_SEEDS

    rows = []
    for proto_name, proto in (("random", random_split),
                              ("group_disjoint", group_disjoint_split)):
        for s_seed in split_seeds:
            try:
                splits = proto(y, groups, seed=s_seed, n_folds=1)
            except ValueError as exc:
                print(f"    {proto_name} seed={s_seed}: SKIPPED ({exc})")
                continue
            sp = splits[0]
            Xtr, ytr = X.iloc[sp.train_idx], y[sp.train_idx]
            Xte, yte = X.iloc[sp.test_idx], y[sp.test_idx]
            if len(np.unique(yte)) < 2:
                print(f"    {proto_name} seed={s_seed}: degenerate test fold "
                      f"(prevalence {sp.test_prevalence:.3f}); recorded, not dropped")
            for key in models:
                for m_seed in model_seeds:
                    t0 = time.perf_counter()
                    try:
                        model = fit_model(key, Xtr, ytr, m_seed)
                        sc = predict_scores(model, Xte)
                        met = detection_metrics(yte, sc)
                    except Exception as exc:  # a crash is a result to record
                        rows.append({"layer": name, "protocol": proto_name,
                                     "model": key, "split_seed": s_seed,
                                     "model_seed": m_seed, "status": f"ERROR: {exc}"})
                        continue
                    rows.append({
                        "layer": name, "protocol": proto_name, "model": key,
                        "split_seed": s_seed, "model_seed": m_seed, "status": "ok",
                        "n_train": len(ytr), "n_test": len(yte),
                        "train_prevalence": sp.train_prevalence,
                        "test_prevalence": sp.test_prevalence,
                        "n_train_groups": sp.n_train_groups,
                        "n_test_groups": sp.n_test_groups,
                        "fit_seconds": round(time.perf_counter() - t0, 2),
                        **met,
                    })
            print(f"    {proto_name} seed={s_seed}: done "
                  f"({len(models)}x{len(model_seeds)} fits)")
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[df.status == "ok"]
    out = []
    for (layer, model), g in ok.groupby(["layer", "model"]):
        rec = {"layer": layer, "model": model}
        for proto in ("random", "group_disjoint"):
            gp = g[g.protocol == proto]
            if gp.empty:
                continue
            # average over model seeds within a split seed, then bootstrap over
            # SPLIT means -- the dominant source of variance (plan A5)
            per_split = gp.groupby("split_seed")[PRIMARY].mean().to_numpy()
            m, lo, hi = interval(per_split)
            rec[f"{proto}_{PRIMARY}"] = m
            rec[f"{proto}_lo"] = lo
            rec[f"{proto}_hi"] = hi
            rec[f"{proto}_n_splits"] = len(per_split)
            for extra in ("pr_auc_benign", "balanced_accuracy", "fpr", "recall"):
                rec[f"{proto}_{extra}"] = gp.groupby("split_seed")[extra].mean().mean()
        if f"random_{PRIMARY}" in rec and f"group_disjoint_{PRIMARY}" in rec:
            rec["leakage_delta"] = rec[f"random_{PRIMARY}"] - rec[f"group_disjoint_{PRIMARY}"]
            # paired over split seeds where both protocols ran
            r = g[g.protocol == "random"].groupby("split_seed")[PRIMARY].mean()
            d = g[g.protocol == "group_disjoint"].groupby("split_seed")[PRIMARY].mean()
            common = r.index.intersection(d.index)
            if len(common) >= 2:
                diffs = (r.loc[common] - d.loc[common]).to_numpy()
                dm, dlo, dhi = interval(diffs)
                rec.update(delta_mean=dm, delta_lo=dlo, delta_hi=dhi,
                           delta_excludes_zero=bool(dlo > 0 or dhi < 0))
        out.append(rec)
    return pd.DataFrame(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--layers", nargs="*", default=["radio", "network"])
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()

    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    models = args.models or [m.key for m in LADDER]
    frames, prov = [], {}
    for layer in args.layers:
        print(f"\n=== layer: {layer} ===")
        corpus = load_radio() if layer == "radio" else load_network()
        prov[layer] = corpus.summary()
        print(f"  {corpus.summary()['n_rows']:,} rows, "
              f"{corpus.summary()['n_features']} features, "
              f"{corpus.summary()['n_groups']} groups, "
              f"{corpus.summary()['attack_prevalence_pct']}% attack")
        frames.append(run_layer(layer, corpus, models, args.quick))

    raw = pd.concat(frames, ignore_index=True)
    raw.to_csv(OUT / "raw" / "leakage_runs.csv", index=False)
    summ = summarise(raw)
    summ.to_csv(OUT / "processed" / "leakage_summary.csv", index=False)
    (OUT / "statistics" / "provenance.json").write_text(
        json.dumps({"corpora": prov, "split_seeds": SPLIT_SEEDS,
                    "model_seeds": MODEL_SEEDS, "primary_metric": PRIMARY,
                    "network_subsample": NETWORK_SUBSAMPLE,
                    "quick": args.quick}, indent=2), encoding="utf-8")

    print("\n=== LEAKAGE AUDIT ===")
    print(f"primary metric: {PRIMARY}; CIs bootstrapped over split means\n")
    for layer in summ.layer.unique():
        s = summ[summ.layer == layer].sort_values("group_disjoint_" + PRIMARY,
                                                  ascending=False)
        print(f"--- {layer} ---")
        print(f"{'model':<12}{'random':>9}{'grouped':>10}{'delta':>9}"
              f"{'95% CI on delta':>22}{'excl 0':>8}")
        for _, r in s.iterrows():
            ci = (f"[{r.get('delta_lo', float('nan')):+.4f}, "
                  f"{r.get('delta_hi', float('nan')):+.4f}]")
            print(f"{r.model:<12}{r.get('random_'+PRIMARY, float('nan')):>9.4f}"
                  f"{r.get('group_disjoint_'+PRIMARY, float('nan')):>10.4f}"
                  f"{r.get('leakage_delta', float('nan')):>+9.4f}{ci:>22}"
                  f"{str(r.get('delta_excludes_zero','-')):>8}")
        print()
    print(f"raw     -> {OUT/'raw'/'leakage_runs.csv'}")
    print(f"summary -> {OUT/'processed'/'leakage_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
