#!/usr/bin/env python3
"""EXP-028: can calibration rescue operational precision?

Two findings make this the right next question.

**Threshold saturation.** EXP-004 found that four of five detectors cannot reach
PPV = 0.50 at any threshold: their scores pile up near 1.0 under a group-disjoint
split, so raising tau barely moves alert volume -- HGB still emits 53,632
alerts/hour at tau = 0.99. A threshold is the only runtime control an operator
has, and it does not work. That is a symptom of miscalibration, not of a bad
threshold choice, and the two have different fixes.

**Prior shift.** `D_A` is 94.63% attack and `D_B` is 60.71%. A model fitted under
one prior and thresholded at 0.5 is not calibrated for the other, so part of the
EXP-026 transfer gap may be prior shift rather than concept shift. Those are very
different findings for a practitioner: prior shift is correctable with unlabelled
target data, concept shift is not.

Design:

  split        source groups are partitioned THREE ways, group-disjoint
               throughout: train / calibration / test. The calibrator never sees
               the test set, and no calibrator is ever fitted on the target.
  calibrators  raw scores, Platt (sigmoid), isotonic, temperature scaling
  evaluated on source test AND the whole target
  metrics      Brier, ECE (15 equal-mass bins), macro-F1, PPV at the declared
               base rate, recall, alerts/hour, and the tau needed to reach an
               operational PPV bar

  oracle       a prior-corrected variant that rescales scores by the KNOWN target
               prior. This uses target information and is therefore NOT a
               deployable method. It is reported, clearly labelled, as an upper
               bound: it answers "how much of the gap is prior shift?" and
               nothing else. Any claim built on it would be target leakage.

The question is not whether calibration improves Brier score -- it will, that is
what fitting a calibrator does. The question is whether it moves the operational
numbers enough to matter, and whether it does so on a corpus the calibrator has
never seen.

Usage:  python experiments/run_calibration.py [--seeds N] [--quick]
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
from sklearn.isotonic import IsotonicRegression  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

from oran_ids.data import load_network_shared, load_target_d_b  # noqa: E402
from oran_ids.features.shared import assert_compatible  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402

warnings.filterwarnings("ignore")

OUT = Path("results/EXP-028")
SPLIT_SEEDS = list(range(101, 121))
MODEL_SEED = 11
SUBSAMPLE = 300_000
PI = 0.002
LAMBDA_B = 240_000.0
TAU_GRID = np.concatenate([np.arange(0.05, 1.0, 0.05), [0.95, 0.99, 0.995, 0.999]])
MODELS = ("logreg", "tree", "rf", "xgboost", "hgb", "mlp")


def ece(y: np.ndarray, p: np.ndarray, n_bins: int = 15) -> float:
    """Expected calibration error over EQUAL-MASS bins.

    Equal-width bins are the common choice and are misleading here: scores pile
    up near 1.0, so most equal-width bins are empty and the ones that are not
    dominate silently. Equal-mass bins put the same number of points in each.
    """
    p = np.clip(p, 0, 1)
    n = len(p)
    if n == 0:
        return float("nan")
    order = np.argsort(p)
    edges = np.array_split(order, min(n_bins, n))
    tot = 0.0
    for idx in edges:
        if len(idx) == 0:
            continue
        tot += len(idx) / n * abs(p[idx].mean() - y[idx].mean())
    return float(tot)


def fit_calibrator(kind: str, s_cal: np.ndarray, y_cal: np.ndarray):
    """Return a function mapping raw scores to calibrated probabilities."""
    s = np.clip(s_cal, 1e-6, 1 - 1e-6)
    if kind == "raw":
        return lambda x: np.clip(x, 0.0, 1.0)
    if kind == "platt":
        lr = LogisticRegression(max_iter=1000)
        lr.fit(s.reshape(-1, 1), y_cal)
        return lambda x: lr.predict_proba(
            np.clip(x, 1e-6, 1 - 1e-6).reshape(-1, 1))[:, 1]
    if kind == "isotonic":
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(s, y_cal)
        return lambda x: iso.predict(np.clip(x, 0.0, 1.0))
    if kind == "temperature":
        # One parameter fitted on the calibration logits by grid search on NLL.
        # A single scalar cannot change the ranking, so AUC is invariant -- which
        # is exactly why it is worth reporting separately from isotonic.
        logit = np.log(s / (1 - s))
        best, best_nll = 1.0, np.inf
        for T in np.geomspace(0.05, 20.0, 120):
            q = 1.0 / (1.0 + np.exp(-logit / T))
            q = np.clip(q, 1e-9, 1 - 1e-9)
            nll = -np.mean(y_cal * np.log(q) + (1 - y_cal) * np.log(1 - q))
            if nll < best_nll:
                best, best_nll = T, nll

        def apply(x, T=best):
            x = np.clip(x, 1e-6, 1 - 1e-6)
            lg = np.log(x / (1 - x))
            return 1.0 / (1.0 + np.exp(-lg / T))
        return apply
    raise ValueError(kind)


def prior_correct(p: np.ndarray, pi_src: float, pi_tgt: float) -> np.ndarray:
    """Rescale calibrated probabilities from a source prior to a target prior.

    ORACLE ONLY. It consumes the target prior, which is target information.
    Reported as an upper bound on what prior correction could buy; never as a
    deployable method and never attached to a claim.
    """
    p = np.clip(p, 1e-9, 1 - 1e-9)
    r = (pi_tgt / (1 - pi_tgt)) / (pi_src / (1 - pi_src))
    odds = p / (1 - p) * r
    return odds / (1 + odds)


def ppv_at(tpr: float, fpr: float, pi: float = PI) -> float:
    den = tpr * pi + fpr * (1 - pi)
    return float(tpr * pi / den) if den > 0 else float("nan")


def _roc_at(y: np.ndarray, s: np.ndarray, taus: np.ndarray):
    """(TPR, FPR) at each threshold, from one sort instead of one pass each.

    ``predicted positive`` is ``s >= tau``, matching ``detection_metrics``. With
    scores sorted descending, the count at or above a threshold is a
    ``searchsorted`` into the sorted array, and the positives among them are a
    cumulative sum. On 1.2M target rows this replaces 24 full metric
    computations per calibrator with a single sort.
    """
    y = np.asarray(y).astype(np.int64)
    order = np.argsort(-s, kind="stable")
    s_sorted = s[order]
    cum_pos = np.concatenate([[0], np.cumsum(y[order])])
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    # number of scores >= tau, for descending order
    k = np.searchsorted(-s_sorted, -np.asarray(taus, dtype=float), side="right")
    tp = cum_pos[k]
    fp = k - tp
    tpr = tp / n_pos if n_pos else np.full(len(taus), np.nan)
    fpr = fp / n_neg if n_neg else np.full(len(taus), np.nan)
    return tpr, fpr


def three_way_group_split(groups: np.ndarray, seed: int,
                          fracs=(0.6, 0.2, 0.2)):
    """Whole groups to exactly one of train / calibration / test."""
    rng = np.random.default_rng(seed)
    uniq = rng.permutation(np.unique(groups))
    sizes = pd.Series(groups).value_counts()
    target = np.array(fracs) * len(groups)
    buckets: list[list] = [[], [], []]
    have = np.zeros(3)
    for g in uniq:
        j = int(np.argmax(target - have))
        buckets[j].append(g)
        have[j] += sizes[g]
    masks = [np.isin(groups, b) for b in buckets]
    return [np.where(m)[0] for m in masks]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    seeds = SPLIT_SEEDS[:2] if args.quick else SPLIT_SEEDS[:args.seeds]
    n_sub = 40_000 if args.quick else SUBSAMPLE
    models = ("logreg", "tree") if args.quick else MODELS

    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    src = load_network_shared()
    tgt = load_target_d_b(reason="EXP-028 calibration, target evaluation only")
    assert_compatible(src.X, tgt.X)
    pi_src_corpus = float(src.y.mean())
    pi_tgt_corpus = float(tgt.y.mean())
    print("source %s attack %.4f | target %s attack %.4f"
          % (src.X.shape, pi_src_corpus, tgt.X.shape, pi_tgt_corpus), flush=True)

    rows, sweep = [], []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        idx = np.sort(rng.choice(len(src.y), size=min(n_sub, len(src.y)),
                                 replace=False))
        X, y, g = src.X.iloc[idx].reset_index(drop=True), src.y[idx], src.groups[idx]
        tr, cal, te = three_way_group_split(g, seed)
        assert not (set(g[tr]) & set(g[cal])), "train/cal group overlap"
        assert not (set(g[tr]) & set(g[te])), "train/test group overlap"
        assert not (set(g[cal]) & set(g[te])), "cal/test group overlap"
        if min(len(np.unique(y[tr])), len(np.unique(y[cal])),
               len(np.unique(y[te]))) < 2:
            print("  seed %d: a fold is single-class, skipped" % seed, flush=True)
            continue

        for key in models:
            t0 = time.time()
            model = fit_model(key, X.iloc[tr], y[tr], MODEL_SEED)
            s_cal = predict_scores(model, X.iloc[cal])
            s_te = predict_scores(model, X.iloc[te])
            s_tg = predict_scores(model, tgt.X)

            for kind in ("raw", "platt", "isotonic", "temperature"):
                f = fit_calibrator(kind, s_cal, y[cal])
                for dom, yy, ss in (("source_test", y[te], f(s_te)),
                                    ("target", tgt.y, f(s_tg))):
                    m = detection_metrics(yy, ss, 0.5)
                    rows.append(dict(
                        seed=seed, model=key, calibrator=kind, domain=dom,
                        oracle=False, brier=m["brier"], ece=ece(yy, ss),
                        f1_macro=m["f1_macro"], recall=m["recall"],
                        fpr=m["fpr"], precision=m["precision"],
                        pr_auc=m["pr_auc"], roc_auc=m["roc_auc"],
                        ppv_deploy=ppv_at(m["recall"], m["fpr"]),
                        alerts_per_hour=m["fpr"] * LAMBDA_B
                        + m["recall"] * LAMBDA_B * PI / (1 - PI),
                        mean_score=float(np.mean(ss))))
                    # The sweep needs only TPR and FPR. Calling
                    # detection_metrics here would recompute ROC-AUC and
                    # average precision on 1.2M target rows at every one of 24
                    # thresholds, for every calibrator -- minutes of work to
                    # obtain two numbers that are a pair of comparisons.
                    # Sorting once and reading the curve off a cumulative sum
                    # gives identical values.
                    tpr_g, fpr_g = _roc_at(yy, ss, TAU_GRID)
                    for t, tp_r, fp_r in zip(TAU_GRID, tpr_g, fpr_g):
                        sweep.append(dict(
                            seed=seed, model=key, calibrator=kind, domain=dom,
                            tau=float(t), recall=float(tp_r), fpr=float(fp_r),
                            ppv_deploy=ppv_at(tp_r, fp_r),
                            alerts_per_hour=fp_r * LAMBDA_B
                            + tp_r * LAMBDA_B * PI / (1 - PI)))

                # ORACLE prior correction on the target only. Labelled, never claimed.
                if kind in ("platt", "isotonic"):
                    p = prior_correct(f(s_tg), pi_src_corpus, pi_tgt_corpus)
                    m = detection_metrics(tgt.y, p, 0.5)
                    rows.append(dict(
                        seed=seed, model=key, calibrator=kind + "+prior_ORACLE",
                        domain="target", oracle=True, brier=m["brier"],
                        ece=ece(tgt.y, p), f1_macro=m["f1_macro"],
                        recall=m["recall"], fpr=m["fpr"],
                        precision=m["precision"], pr_auc=m["pr_auc"],
                        roc_auc=m["roc_auc"],
                        ppv_deploy=ppv_at(m["recall"], m["fpr"]),
                        alerts_per_hour=m["fpr"] * LAMBDA_B
                        + m["recall"] * LAMBDA_B * PI / (1 - PI),
                        mean_score=float(np.mean(p))))

            print("  seed %d %-8s done %.1fs" % (seed, key, time.time() - t0),
                  flush=True)

    R = pd.DataFrame(rows)
    R.to_csv(OUT / "raw/calibration_runs.csv", index=False)
    S = pd.DataFrame(sweep)
    S.to_csv(OUT / "raw/calibration_tau_sweep.csv", index=False)

    summ = (R.groupby(["domain", "model", "calibrator", "oracle"])
            .agg(brier=("brier", "mean"), ece=("ece", "mean"),
                 f1_macro=("f1_macro", "mean"), recall=("recall", "mean"),
                 fpr=("fpr", "mean"), pr_auc=("pr_auc", "mean"),
                 roc_auc=("roc_auc", "mean"),
                 ppv_deploy=("ppv_deploy", "mean"),
                 alerts_per_hour=("alerts_per_hour", "mean"),
                 mean_score=("mean_score", "mean"),
                 n=("brier", "size")).reset_index())
    summ.to_csv(OUT / "processed/calibration_summary.csv", index=False)

    # Can any calibrator reach an operational PPV bar, and at what recall?
    cross = []
    for (dom, mdl, cal), gg in S.groupby(["domain", "model", "calibrator"]):
        a = gg.groupby("tau").agg(ppv=("ppv_deploy", "mean"),
                                  rec=("recall", "mean"),
                                  al=("alerts_per_hour", "mean")).reset_index()
        for bar in (0.25, 0.5):
            ok = a[a.ppv >= bar]
            cross.append(dict(
                domain=dom, model=mdl, calibrator=cal, ppv_bar=bar,
                reachable=bool(len(ok)),
                tau=float(ok.tau.min()) if len(ok) else float("nan"),
                recall_there=float(ok.loc[ok.tau.idxmin(), "rec"]) if len(ok) else float("nan"),
                alerts_there=float(ok.loc[ok.tau.idxmin(), "al"]) if len(ok) else float("nan")))
    C = pd.DataFrame(cross)
    C.to_csv(OUT / "processed/ppv_reachability.csv", index=False)

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-028", seeds=list(seeds), models=list(models),
        subsample=n_sub, pi=PI, lambda_b=LAMBDA_B,
        split="group-disjoint three-way train/calibration/test on src_ip",
        calibrators=["raw", "platt", "isotonic", "temperature"],
        oracle_note=("prior-corrected variants consume the TARGET prior and are "
                     "an upper bound, not a deployable method"),
        pi_source_corpus=pi_src_corpus, pi_target_corpus=pi_tgt_corpus,
        ece_bins="15 equal-mass",
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t_start, 1)), indent=2), encoding="utf-8")

    for dom in ("source_test", "target"):
        d = summ[summ.domain == dom]
        if not len(d):
            continue
        print("\n=== %s ===" % dom)
        print(d[["model", "calibrator", "brier", "ece", "f1_macro", "recall",
                 "fpr", "ppv_deploy", "alerts_per_hour"]].to_string(
                     index=False, float_format=lambda v: "%.4f" % v))

    print("\n=== can PPV >= 0.25 be reached at any threshold? ===")
    r = C[C.ppv_bar == 0.25].pivot_table(
        index=["domain", "model"], columns="calibrator", values="reachable")
    print(r.to_string())
    print("\nwrote %s  (%.0fs)" % (OUT, time.time() - t_start))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
