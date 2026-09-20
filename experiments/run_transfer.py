#!/usr/bin/env python3
"""EXP-026 (X2): cross-deployment transfer. RQ1, the paper's headline.

The question the title promises and the project has never been able to answer:
**does a detector trained on one O-RAN deployment work on another?**

Design, pre-registered here before the first run:

  source          D_A = NetsLab-5GORAN-IDD, CU flow records (Zeek)
  target          D_B = 5G-NIDD, flow records (Argus), transfer-only
  space           the 18-column shared space, configs/features/shared_space.yaml
  split (source)  group-disjoint on src_ip, 20 split seeds (D-012 standing n)
  normalisation   fitted on SOURCE training data only, inside the pipeline (A2)
  threshold       fixed at 0.5. Never tuned on the target.
  models          the full ladder, including both trivial floors
  primary         macro-F1. Delta_F1 = source_heldout - target, per architecture
  controls        (a) source held-out under the SAME space and protocol, so the
                      gap is not an artefact of the projection onto 18 columns
                  (b) the trivial floor evaluated on the target, so a collapse
                      can be read against what guessing scores there
  CIs             paired t-interval over split means (D-012: never bootstrap
                  below n=30)

H-transfer: macro-F1 on D_B is materially below macro-F1 on held-out D_A.
Falsified if: the 95% CI on the per-model difference includes 0 for all models.

**A NEGATIVE RESULT HERE IS THE RESULT.** If transfer collapses, that is
reported and kept. It is never re-run until it improves (campaign rule 4).

MANDATORY WORDING (D-004, D-010, and now D-015). The A3 single-exporter control
is NOT applied. D_A is exported by Zeek and D_B by Argus, and the two disagree
about where a flow ends. Every Delta_F1 below is therefore an UPPER BOUND on
deployment shift, spanning an independently collected deployment AND an
independent feature-extraction pipeline. It must never be described as being
"due to deployment shift".

Usage:  python experiments/run_transfer.py [--quick] [--reverse]
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats as _st  # noqa: E402

from oran_ids.data import load_network_shared, load_target_d_b  # noqa: E402
from oran_ids.features.shared import COLUMNS, assert_compatible  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split, random_split  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT = Path("results/EXP-026")
SPLIT_SEEDS = list(range(101, 121))          # 20, the standing choice (D-012)
MODEL_SEED = 11
PRIMARY = "f1_macro"
SOURCE_SUBSAMPLE = 300_000                   # declared; matches EXP-002
THRESHOLD = 0.5
# D_A has six canonical categories, D_B has three. These three exist only on the
# source side and CANNOT be tested in transfer. Reported, never quietly dropped.
UNTESTABLE = ("ddos", "bruteforce", "web")


def interval(vals):
    """Paired t-interval over split means. D-012 forbids bootstrap below n=30."""
    v = np.asarray(vals, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) < 2:
        return (float(v[0]) if len(v) else float("nan")), float("nan"), float("nan")
    if v.std(ddof=1) == 0:
        return float(v.mean()), float(v.mean()), float(v.mean())
    lo, hi = _st.t.interval(0.95, len(v) - 1, loc=v.mean(), scale=_st.sem(v))
    return float(v.mean()), float(lo), float(hi)


def subsample(X, y, cat, groups, n, seed):
    if len(y) <= n:
        return X, y, cat, groups
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.choice(len(y), size=n, replace=False))
    return X.iloc[idx].reset_index(drop=True), y[idx], cat[idx], groups[idx]


def per_category_recall(y, cat, pred) -> dict:
    """Recall within each canonical category. Benign gets specificity instead."""
    out = {}
    for c in sorted(set(cat)):
        m = cat == c
        if c == "benign":
            out[c] = float((pred[m] == 0).mean())      # specificity
        else:
            out[c] = float((pred[m] == 1).mean())      # recall
        out[c + "__n"] = int(m.sum())
    return out


def guard_no_clobber(path: Path, n_seeds: int) -> None:
    """D-014: a completed run must never silently replace a better one."""
    if not path.exists():
        return
    try:
        prev = pd.read_csv(path)
    except Exception:
        return
    if "split_seed" in prev.columns:
        prev_n = prev["split_seed"].nunique()
        if prev_n > n_seeds:
            raise SystemExit(
                "REFUSING to overwrite " + str(path) + ": it holds "
                + str(prev_n) + " split seeds and this run has only "
                + str(n_seeds) + ". Delete it deliberately or use another "
                "tag. (D-014)")


def run(direction: str, quick: bool) -> None:
    seeds = SPLIT_SEEDS[:3] if quick else SPLIT_SEEDS
    n_sub = 40_000 if quick else SOURCE_SUBSAMPLE
    # Both CSVs are ordered by attack category, so reading the first N rows
    # yields a single-class corpus. --quick therefore loads everything and
    # relies on the seeded random subsample below instead of a row cap.
    cap = None
    tag = direction
    t_start = time.time()

    for sub in ("raw", "processed", "statistics", "logs"):
        OUT.joinpath(sub).mkdir(parents=True, exist_ok=True)

    raw_path = OUT / ("raw/transfer_runs__" + tag + ".csv")
    if not quick:
        guard_no_clobber(raw_path, len(seeds))

    print("[" + tag + "] loading corpora ...", flush=True)
    if direction == "a_to_b":
        src = load_network_shared(nrows=cap)
        tgt = load_target_d_b(
            nrows=cap, reason="EXP-026 final evaluation, direction=" + tag)
        src_groups, use_group_split = src.groups, True
    else:
        # Secondary symmetry check (D-017). D_B has no identifier columns and
        # therefore no group key, so its own held-out reference is a RANDOM
        # split and is an optimistic bound. Stated, not hidden.
        src = load_target_d_b(
            nrows=cap, reason="EXP-026 reverse direction, direction=" + tag)
        tgt = load_network_shared(nrows=cap)
        src_groups, use_group_split = np.arange(len(src.y)), False

    assert_compatible(src.X, tgt.X)
    print("[%s] source %s: %s, attack %.2f%%"
          % (tag, src.name, src.X.shape, src.y.mean() * 100), flush=True)
    print("[%s] target %s: %s, attack %.2f%%"
          % (tag, tgt.name, tgt.X.shape, tgt.y.mean() * 100), flush=True)

    tgt_present = sorted(set(tgt.category))
    untestable_here = [c for c in UNTESTABLE
                       if c in set(src.category) and c not in set(tgt.category)]
    print("[%s] target categories: %s" % (tag, tgt_present), flush=True)
    print("[%s] untestable here: %s" % (tag, untestable_here), flush=True)

    rows, cat_rows = [], []
    for si, seed in enumerate(seeds):
        Xs, ys, cats, gs = subsample(src.X, src.y, src.category, src_groups,
                                     n_sub, seed)
        if use_group_split:
            sp = group_disjoint_split(ys, gs, seed=seed, n_folds=1)[0]
            sp.check_disjoint(gs)
        else:
            sp = random_split(ys, gs, seed=seed, n_folds=1)[0]

        Xtr, ytr = Xs.iloc[sp.train_idx], ys[sp.train_idx]
        Xte, yte = Xs.iloc[sp.test_idx], ys[sp.test_idx]

        if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
            raise SystemExit(
                "seed " + str(seed) + ": a fold carries a single class "
                "(train=" + str(np.unique(ytr).tolist()) + ", test="
                + str(np.unique(yte).tolist()) + "). Every metric below "
                "would be undefined or trivially 1.0. Fix the split or "
                "the subsample -- do not report this.")

        for spec in LADDER:
            t0 = time.time()
            model = fit_model(spec.key, Xtr, ytr, MODEL_SEED)

            # (a) held-out SOURCE, same space, same protocol: the reference the
            #     transfer number is subtracted from.
            m_src = detection_metrics(yte, predict_scores(model, Xte), THRESHOLD)
            # (b) the TARGET, whole, once.
            s_tgt = predict_scores(model, tgt.X)
            m_tgt = detection_metrics(tgt.y, s_tgt, THRESHOLD)

            for domain, m in (("source_heldout", m_src), ("target", m_tgt)):
                rows.append(dict(direction=tag, model=spec.key, level=spec.level,
                                 split_seed=seed, model_seed=MODEL_SEED,
                                 domain=domain, n_train=len(ytr), **m))

            pred_t = (s_tgt >= THRESHOLD).astype(int)
            cat_rows.append(dict(direction=tag, model=spec.key, split_seed=seed,
                                 **per_category_recall(tgt.y, tgt.category,
                                                       pred_t)))

            print("  seed %d [%d/%d] %-10s src %.3f -> tgt %.3f  (delta %+.3f)"
                  "  %.1fs" % (seed, si + 1, len(seeds), spec.key,
                               m_src[PRIMARY], m_tgt[PRIMARY],
                               m_src[PRIMARY] - m_tgt[PRIMARY],
                               time.time() - t0), flush=True)

    runs = pd.DataFrame(rows)
    runs.to_csv(raw_path, index=False)
    pd.DataFrame(cat_rows).to_csv(
        OUT / ("processed/per_category_recall__" + tag + ".csv"), index=False)

    # ---- summarise -------------------------------------------------------
    summary = []
    for key in [m.key for m in LADDER]:
        sub = runs[runs.model == key]
        per_seed = sub.pivot_table(index="split_seed", columns="domain",
                                   values=PRIMARY)
        if not {"source_heldout", "target"}.issubset(per_seed.columns):
            continue
        d = (per_seed["source_heldout"] - per_seed["target"]).to_numpy()
        s_mean, s_lo, s_hi = interval(per_seed["source_heldout"].to_numpy())
        t_mean, t_lo, t_hi = interval(per_seed["target"].to_numpy())
        d_mean, d_lo, d_hi = interval(d)
        if len(d) >= 2 and np.nanstd(d, ddof=1) > 0:
            tstat, p = _st.ttest_rel(per_seed["source_heldout"],
                                     per_seed["target"])
            dz = float(np.nanmean(d) / np.nanstd(d, ddof=1))
        else:
            tstat, p, dz = float("nan"), float("nan"), float("nan")
        row = dict(direction=tag, model=key, n_seeds=int(len(d)),
                   source_f1=s_mean, source_lo=s_lo, source_hi=s_hi,
                   target_f1=t_mean, target_lo=t_lo, target_hi=t_hi,
                   delta_f1=d_mean, delta_lo=d_lo, delta_hi=d_hi,
                   d_z=dz, t=float(tstat), p_raw=float(p))
        for extra in ("pr_auc", "pr_auc_benign", "precision", "recall", "fpr",
                      "fnr", "brier", "balanced_accuracy", "roc_auc"):
            for dom, short in (("source_heldout", "src"), ("target", "tgt")):
                row[short + "_" + extra] = float(
                    sub[sub.domain == dom][extra].mean())
        summary.append(row)

    sm = pd.DataFrame(summary)
    # Holm correction over the non-trivial models only.
    nt = sm[~sm.model.isin(["majority", "stratified"])].copy()
    pvals = nt["p_raw"].to_numpy()
    order = np.argsort(pvals)
    m_tests = len(nt)
    holm = np.empty(m_tests)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m_tests - rank) * pvals[i])
        holm[i] = min(running, 1.0)
    nt["p_holm"] = holm
    sm = sm.merge(nt[["model", "p_holm"]], on="model", how="left")
    sm["significant"] = sm["p_holm"] < 0.05
    sm.to_csv(OUT / ("processed/transfer_summary__" + tag + ".csv"), index=False)

    prov = dict(
        experiment="EXP-026", direction=tag, quick=quick,
        source=src.summary(), target=tgt.summary(),
        shared_space_columns=list(COLUMNS), n_features=len(COLUMNS),
        split_seeds=seeds, model_seed=MODEL_SEED, threshold=THRESHOLD,
        source_subsample=n_sub, primary_metric=PRIMARY,
        source_split=("group_disjoint(src_ip)" if use_group_split else
                      "random (D_B has no group key; optimistic bound)"),
        untestable_categories=untestable_here,
        target_categories_present=tgt_present,
        a3_single_exporter_control_applied=False,
        exporter_source="Zeek" if direction == "a_to_b" else "Argus",
        exporter_target="Argus" if direction == "a_to_b" else "Zeek",
        interpretation_constraint=(
            "Delta_F1 is an UPPER BOUND on deployment shift. It spans an "
            "independently collected deployment AND an independent "
            "feature-extraction pipeline. Never describe it as due to "
            "deployment shift alone."),
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t_start, 1))
    (OUT / ("statistics/provenance__" + tag + ".json")).write_text(
        json.dumps(prov, indent=2), encoding="utf-8")

    print("\n=== " + tag + ": macro-F1 ===")
    cols = ["model", "source_f1", "target_f1", "delta_f1", "delta_lo",
            "delta_hi", "d_z", "p_holm", "significant"]
    print(sm[cols].to_string(index=False,
                             float_format=lambda v: "%.4f" % v))
    print("\nwrote %s  (%.0fs)" % (raw_path, time.time() - t_start))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--reverse", action="store_true",
                    help="also run D_B -> D_A as a symmetry check (D-017)")
    ap.add_argument("--only-reverse", action="store_true")
    a = ap.parse_args()
    if not a.only_reverse:
        run("a_to_b", a.quick)
    if a.reverse or a.only_reverse:
        run("b_to_a", a.quick)


if __name__ == "__main__":
    main()
