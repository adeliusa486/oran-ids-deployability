#!/usr/bin/env python3
"""EXP-027: does the operational-precision finding survive the base rate we chose?

EXP-004 reported that deployment PPV spans roughly 6x across detectors whose
corpus precision is flat within 0.007, at a single declared base rate pi = 0.002
and a single declared benign arrival rate lambda_b = 240,000 flows/hour. Neither
parameter is a measurement. A finding that holds only at one arbitrary point on a
sweep is not a finding, so this experiment asks whether it holds anywhere else.

It does not, and the reason is an estimator bug rather than a choice of pi. See
B-E below. The finding that *does* survive is stronger and simpler.

---------------------------------------------------------------------------
B-E -- why this experiment does not average per-fold PPV
---------------------------------------------------------------------------
PPV is a strongly non-linear function of FPR near FPR = 0:

    PPV = TPR.pi / (TPR.pi + FPR.(1-pi))

At pi = 0.002 a fold with FPR = 0 yields PPV = 1.000 exactly, whatever TPR is.
Under a group-disjoint split on 30 radio sessions, a test fold holds only 112-171
benign windows, and several folds genuinely produce zero false positives. Those
are real zeros, not divide-by-zero artefacts -- but observing 0/113 does not mean
the deployment FPR is 0. It means it is somewhere below about 2.6% (rule of
three). Substituting the point estimate 0 into the formula asserts perfect
precision against 240,000 flows per hour on the strength of 113 samples.

Averaging those folds is what produced the "6x spread". XGBoost drew five
zero-FPR folds out of twenty, MLP drew none, and the reported difference between
the two architectures was mostly that count. Measured three ways:

    spread across the five detectors      pooled 1.08x   median 1.36x   mean 4.65x

The mean is the outlier, and it is the one that was published.

This experiment therefore uses the **pooled (micro) estimator** as primary: sum
the confusion counts over all folds, form one (TPR, FPR), then apply the base
rate. That is what a deployment actually experiences -- it does not run twenty
parallel universes and average their precisions. Per-fold mean and median are
computed alongside, explicitly, so the size of the artefact stays visible instead
of being quietly corrected away.

---------------------------------------------------------------------------
Two structural facts, which are why no model is refitted here
---------------------------------------------------------------------------
    PPV  = TPR.pi / (TPR.pi + FPR.(1-pi))         depends on pi, NOT lambda_b
    alerts/hour = (TPR.pi/(1-pi) + FPR).lambda_b  scales LINEARLY in lambda_b

So PPV, NPV and FDR are one-dimensional in pi and every volume is separable. The
two-dimensional grid is produced because the brief asks for it, and separability
is then verified numerically rather than asserted.

Everything is computed from confusion counts already committed by EXP-002 and
EXP-026, so nothing here can drift from what those experiments reported.

Usage:  python experiments/run_prevalence_sensitivity.py
"""
from __future__ import annotations

import json
import platform
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats as _st  # noqa: E402

warnings.filterwarnings("ignore")

OUT = Path("results/EXP-027")

PI_SWEEP = [0.0001, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.05, 0.1, 0.2, 0.5]
PI_PRIMARY = 0.002

# Benign flow arrival rate. All four are DECLARED. 240k/h is EXP-004's figure,
# kept as the reference; the others bracket it by two orders of magnitude each
# way so a reader can locate their own deployment on the curve.
LAMBDA_SWEEP = [24_000.0, 240_000.0, 2_400_000.0, 24_000_000.0]
LAMBDA_PRIMARY = 240_000.0

TRIVIAL = ("majority", "stratified")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval. Chosen because it stays sensible at k = 0.

    A normal-approximation interval at k = 0 has zero width, which is exactly the
    overconfidence B-E is about.
    """
    if n <= 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float(max(0.0, (c - hw) / d)), float(min(1.0, (c + hw) / d))


def ppv_of(tpr: float, fpr: float, pi: float) -> float:
    num = tpr * pi
    den = num + fpr * (1 - pi)
    return float(num / den) if den > 0 else float("nan")


def operational(tpr: float, fpr: float, pi: float, lam: float) -> dict:
    lam_attack = lam * pi / max(1 - pi, 1e-12)
    tp_h, fp_h = tpr * lam_attack, fpr * lam
    alerts = tp_h + fp_h
    fn_h, tn_h = (1 - tpr) * lam_attack, (1 - fpr) * lam
    ppv = tp_h / alerts if alerts > 0 else float("nan")
    npv = tn_h / (tn_h + fn_h) if (tn_h + fn_h) > 0 else float("nan")
    return dict(pi=pi, lambda_b=lam, ppv=ppv, npv=npv,
                fdr=(1 - ppv) if ppv == ppv else float("nan"),
                alerts_per_hour=alerts, true_alerts_per_hour=tp_h,
                false_alerts_per_hour=fp_h, alerts_per_day=alerts * 24,
                alerts_per_100k_benign=fpr * 1e5 + tpr * 1e5 * pi / max(1 - pi, 1e-12),
                missed_attacks_per_hour=fn_h)


def load_folds() -> pd.DataFrame:
    """Per-fold confusion counts at tau = 0.5, from committed results.

    'surface' names the evaluation setting. An alert burden computed on held-out
    source data and one computed on an independent deployment are different
    claims and are never pooled together.
    """
    frames = []
    p = Path("results/EXP-002/raw/leakage_runs.csv")
    if p.exists():
        d = pd.read_csv(p)
        d = d[(d.protocol == "group_disjoint") & (d.threshold == 0.5)]
        for layer, g in d.groupby("layer"):
            frames.append(pd.DataFrame({
                "surface": "d_a_%s_heldout" % layer, "model": g.model,
                "split_seed": g.split_seed, "tp": g.tp, "fp": g.fp,
                "tn": g.tn, "fn": g.fn, "corpus_precision": g.precision}))

    p = Path("results/EXP-026/raw/transfer_runs__a_to_b.csv")
    if p.exists():
        d = pd.read_csv(p)
        d = d[d.threshold == 0.5]
        for dom, name in (("source_heldout", "d_a_network_heldout_shared"),
                          ("target", "d_b_target")):
            g = d[d.domain == dom]
            if len(g):
                frames.append(pd.DataFrame({
                    "surface": name, "model": g.model,
                    "split_seed": g.split_seed, "tp": g.tp, "fp": g.fp,
                    "tn": g.tn, "fn": g.fn, "corpus_precision": g.precision}))

    if not frames:
        raise SystemExit("no confusion counts found; run EXP-002 or EXP-026 first")
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    folds = load_folds()
    print("confusion counts loaded:")
    for s, g in folds.groupby("surface"):
        print("  %-28s %d models x %d seeds, %d folds"
              % (s, g.model.nunique(), g.split_seed.nunique(), len(g)))

    # ---- pooled operating point per (surface, model) ---------------------
    pooled = []
    for (surface, model), g in folds.groupby(["surface", "model"]):
        tp, fp, tn, fn = int(g.tp.sum()), int(g.fp.sum()), int(g.tn.sum()), int(g.fn.sum())
        n_pos, n_neg = tp + fn, fp + tn
        tpr = tp / n_pos if n_pos else float("nan")
        fpr = fp / n_neg if n_neg else float("nan")
        fpr_lo, fpr_hi = wilson(fp, n_neg)
        tpr_lo, tpr_hi = wilson(tp, n_pos)
        per_fold_fpr = (g.fp / (g.fp + g.tn).clip(lower=1)).to_numpy()
        pooled.append(dict(
            surface=surface, model=model, n_folds=len(g),
            tp=tp, fp=fp, tn=tn, fn=fn, n_benign=n_neg, n_attack=n_pos,
            tpr=tpr, fpr=fpr, tpr_lo=tpr_lo, tpr_hi=tpr_hi,
            fpr_lo=fpr_lo, fpr_hi=fpr_hi,
            lr_plus=tpr / fpr if fpr > 0 else float("inf"),
            corpus_precision=float(g.corpus_precision.mean()),
            fold_fpr_min=float(per_fold_fpr.min()),
            fold_fpr_max=float(per_fold_fpr.max()),
            fold_fpr_median=float(np.median(per_fold_fpr)),
            n_folds_with_zero_fp=int((g.fp == 0).sum()),
            benign_per_fold_median=float(np.median((g.fp + g.tn).to_numpy()))))
    P = pd.DataFrame(pooled)
    P.to_csv(OUT / "processed/pooled_operating_points.csv", index=False)

    # ---- B-E: quantify the estimator artefact, do not hide it ------------
    est = []
    for (surface, model), g in folds.groupby(["surface", "model"]):
        p = P[(P.surface == surface) & (P.model == model)].iloc[0]
        f_tpr = (g.tp / (g.tp + g.fn).clip(lower=1)).to_numpy()
        f_fpr = (g.fp / (g.fp + g.tn).clip(lower=1)).to_numpy()
        per_fold_ppv = np.array([ppv_of(a, b, PI_PRIMARY)
                                 for a, b in zip(f_tpr, f_fpr)])
        est.append(dict(
            surface=surface, model=model, pi=PI_PRIMARY,
            ppv_pooled=ppv_of(p.tpr, p.fpr, PI_PRIMARY),
            ppv_mean_of_folds=float(np.nanmean(per_fold_ppv)),
            ppv_median_of_folds=float(np.nanmedian(per_fold_ppv)),
            n_folds_ppv_equals_1=int((per_fold_ppv >= 0.999).sum()),
            n_folds=len(g)))
    E = pd.DataFrame(est)
    E.to_csv(OUT / "processed/estimator_comparison.csv", index=False)

    print("\n=== B-E: three estimators of the same quantity, pi=0.002 ===")
    for surface, g in E.groupby("surface"):
        nt = g[~g.model.isin(TRIVIAL)]
        if len(nt) < 2:
            continue
        print("\n  %s" % surface)
        print(nt[["model", "ppv_pooled", "ppv_median_of_folds",
                  "ppv_mean_of_folds", "n_folds_ppv_equals_1"]].to_string(
                      index=False, float_format=lambda v: "%.4f" % v))
        for col, lab in (("ppv_pooled", "pooled"),
                         ("ppv_median_of_folds", "median"),
                         ("ppv_mean_of_folds", "mean  ")):
            v = nt[col][nt[col] > 0]
            if len(v) >= 2:
                print("      spread %s : %.2fx" % (lab, v.max() / v.min()))

    # ---- the pi x lambda_b grid, on pooled operating points --------------
    rows = []
    for r in P.itertuples():
        for pi in PI_SWEEP:
            for lam in LAMBDA_SWEEP:
                rows.append(dict(surface=r.surface, model=r.model,
                                 tpr=r.tpr, fpr=r.fpr,
                                 corpus_precision=r.corpus_precision,
                                 ppv_lo=ppv_of(r.tpr_lo, r.fpr_hi, pi),
                                 ppv_hi=ppv_of(r.tpr_hi, r.fpr_lo, pi),
                                 **operational(r.tpr, r.fpr, pi, lam)))
    grid = pd.DataFrame(rows)
    grid.to_csv(OUT / "raw/pi_lambda_grid.csv", index=False)
    print("\ngrid: %d rows (%d surfaces, %d pi, %d lambda_b)"
          % (len(grid), P.surface.nunique(), len(PI_SWEEP), len(LAMBDA_SWEEP)))

    # ---- verify separability numerically ---------------------------------
    key = ["surface", "model", "pi"]
    ppv_var = float(grid.groupby(key)["ppv"].agg(lambda v: np.nanmax(v) - np.nanmin(v)).max())
    base = grid[grid.lambda_b == LAMBDA_PRIMARY].set_index(key)["alerts_per_hour"]
    lin_err = 0.0
    for lam in LAMBDA_SWEEP:
        cur = grid[grid.lambda_b == lam].set_index(key)["alerts_per_hour"]
        lin_err = max(lin_err, float((cur - base * (lam / LAMBDA_PRIMARY)).abs().max()))
    separable = bool(ppv_var < 1e-12 and lin_err < 1e-6)
    print("\nseparability: max PPV variation across lambda_b = %.2e, "
          "max deviation from linearity = %.2e -> %s"
          % (ppv_var, lin_err, separable))

    # ---- spread across detectors at every pi -----------------------------
    ref = grid[grid.lambda_b == LAMBDA_PRIMARY]
    spread = []
    for (surface, pi), g in ref.groupby(["surface", "pi"]):
        nt = g[(~g.model.isin(TRIVIAL)) & np.isfinite(g.ppv) & (g.ppv > 0)]
        if len(nt) < 2:
            continue
        spread.append(dict(
            surface=surface, pi=pi, n_models=len(nt),
            ppv_min=float(nt.ppv.min()), ppv_max=float(nt.ppv.max()),
            ppv_ratio=float(nt.ppv.max() / nt.ppv.min()),
            corpus_precision_min=float(nt.corpus_precision.min()),
            corpus_precision_max=float(nt.corpus_precision.max()),
            corpus_precision_range=float(nt.corpus_precision.max()
                                         - nt.corpus_precision.min()),
            collapse_factor=float(nt.corpus_precision.mean() / nt.ppv.mean()),
            best_model=str(nt.loc[nt.ppv.idxmax(), "model"]),
            false_alerts_per_hour_median=float(nt.false_alerts_per_hour.median())))
    S = pd.DataFrame(spread)
    S.to_csv(OUT / "processed/ppv_spread_vs_prevalence.csv", index=False)

    # ---- rank stability across pi ----------------------------------------
    rank = []
    for surface, g in ref.groupby("surface"):
        nt = g[~g.model.isin(TRIVIAL)]
        piv = nt.pivot_table(index="model", columns="pi", values="ppv").dropna()
        if piv.shape[0] < 3 or PI_PRIMARY not in piv.columns:
            continue
        for pi in piv.columns:
            tau, p = _st.kendalltau(piv[PI_PRIMARY], piv[pi])
            rank.append(dict(surface=surface, pi=float(pi),
                             kendall_tau_vs_primary=float(tau), p=float(p),
                             best_model=str(piv[pi].idxmax())))
    pd.DataFrame(rank).to_csv(
        OUT / "processed/rank_stability_vs_prevalence.csv", index=False)

    # ---- what base rate would a detector need to be usable? --------------
    cross = []
    for (surface, model), g in ref.groupby(["surface", "model"]):
        g = g.sort_values("pi")
        for bar in (0.25, 0.5, 0.9):
            ok = g[g.ppv >= bar]
            cross.append(dict(surface=surface, model=model, ppv_bar=bar,
                              pi_required=float(ok.pi.min()) if len(ok) else float("nan"),
                              reachable_within_sweep=bool(len(ok))))
    pd.DataFrame(cross).to_csv(OUT / "processed/pi_required_for_ppv.csv", index=False)

    prov = dict(
        experiment="EXP-027",
        method="analytic sweep over POOLED confusion counts from committed results",
        models_refitted=0, primary_estimator="pooled (micro) over folds",
        estimator_note=("per-fold mean is reported but NOT used: it is the "
                        "artefact documented as B-E"),
        pi_sweep=PI_SWEEP, pi_primary=PI_PRIMARY,
        lambda_sweep=LAMBDA_SWEEP, lambda_primary=LAMBDA_PRIMARY, tau=0.5,
        surfaces=sorted(P.surface.unique()),
        separability_verified=separable,
        max_ppv_variation_across_lambda=ppv_var,
        max_linearity_deviation=lin_err,
        declared_not_measured=["pi", "lambda_b"],
        source_files=["results/EXP-002/raw/leakage_runs.csv",
                      "results/EXP-026/raw/transfer_runs__a_to_b.csv"],
        python=platform.python_version(), platform=platform.platform())
    (OUT / "statistics/provenance.json").write_text(
        json.dumps(prov, indent=2), encoding="utf-8")

    for surface in sorted(S.surface.unique()):
        s = S[S.surface == surface]
        print("\n=== %s: PPV vs base rate, pooled, tau=0.5 ===" % surface)
        print(s[["pi", "ppv_min", "ppv_max", "ppv_ratio",
                 "corpus_precision_range", "collapse_factor",
                 "false_alerts_per_hour_median"]].to_string(
                     index=False, float_format=lambda v: "%.4f" % v))

    print("\n=== fold-to-fold FPR variability (group-disjoint) ===")
    print(P[["surface", "model", "fpr", "fold_fpr_min", "fold_fpr_median",
             "fold_fpr_max", "n_folds_with_zero_fp", "benign_per_fold_median"]]
          .to_string(index=False, float_format=lambda v: "%.4f" % v))

    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
