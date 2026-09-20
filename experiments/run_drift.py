#!/usr/bin/env python3
"""EXP-034: does a detector trained on early captures still work on later ones?

`D_A`'s radio layer spans **52.96 days** (2025-05-09 to 2025-07-01) and EXP-001
recovered **30 label-pure capture sessions** from the clock. Session identifiers
are assigned by a cumulative sum over time-sorted records, so the session index
*is* a temporal index: session 0 is the earliest, session 29 the latest. That
makes a genuine time-disjoint evaluation possible on real data, with no
simulation of drift.

The network layer carries **no time column at all** (EXP-001), so this experiment
is radio-only and says so rather than inventing an ordering.

Design:

  temporal        train on the earliest K sessions, test on the latest.
                  The gap between them is swept, so degradation can be read
                  against how far apart the two windows are.
  control         a group-disjoint split with the SAME number of train and test
                  sessions, drawn at random rather than by time. Without this
                  control a temporal drop is indistinguishable from the ordinary
                  variance of which sessions land in test -- and EXP-027 found
                  that variance is enormous here, with fold FPR ranging 0.000 to
                  0.890.
  reverse         train on the LATEST sessions and test on the earliest. If
                  drift is directional, forward and reverse differ; if the
                  temporal effect is really session heterogeneity, they match.

Measured: macro-F1, recall, FPR, Brier and ECE (calibration drift), and alert
burden at the declared base rate.

The honest prior: with 30 sessions there is very little room. A 60/40 temporal
split leaves 18 training sessions and 12 test sessions, and the control will have
wide spread. This experiment is powered to detect a large effect and nothing
subtler, which is stated here rather than discovered in review.

Usage:  python experiments/run_drift.py [--reps N]
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

from oran_ids.data import load_radio  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import fit_model, predict_scores  # noqa: E402

warnings.filterwarnings("ignore")

OUT = Path("results/EXP-034")
MODELS = ("logreg", "tree", "rf", "xgboost", "hgb", "mlp", "stratified", "majority")
MODEL_SEED = 11
PI, LAMBDA_B = 0.002, 240_000.0
TRAIN_FRACS = (0.4, 0.5, 0.6, 0.7)


def ece(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> float:
    p = np.clip(np.asarray(p, dtype=np.float64), 0, 1)
    n = len(p)
    if n == 0:
        return float("nan")
    tot = 0.0
    for idx in np.array_split(np.argsort(p), min(n_bins, n)):
        if len(idx):
            tot += len(idx) / n * abs(p[idx].mean() - y[idx].mean())
    return float(tot)


def evaluate(key, Xtr, ytr, Xte, yte) -> dict:
    m = fit_model(key, Xtr, ytr, MODEL_SEED)
    s = predict_scores(m, Xte)
    d = detection_metrics(yte, s, 0.5)
    lam_a = LAMBDA_B * PI / (1 - PI)
    tp_h, fp_h = d["recall"] * lam_a, d["fpr"] * LAMBDA_B
    al = tp_h + fp_h
    return dict(f1_macro=d["f1_macro"], recall=d["recall"], fpr=d["fpr"],
                precision=d["precision"], pr_auc=d["pr_auc"],
                brier=d["brier"], ece=ece(yte, s),
                alerts_per_hour=al, false_alerts_per_hour=fp_h,
                ppv_deploy=float(tp_h / al) if al > 0 else float("nan"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20,
                    help="random control repetitions per configuration")
    args = ap.parse_args()
    t0 = time.time()
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    c = load_radio()
    sessions = np.asarray(c.groups)
    order = np.sort(np.unique(sessions))          # session id == time order
    n_sess = len(order)
    print("radio: %d windows, %d sessions, attack %.4f"
          % (len(c.y), n_sess, c.y.mean()), flush=True)

    rows = []
    for frac in TRAIN_FRACS:
        k = int(round(frac * n_sess))
        if k < 2 or n_sess - k < 2:
            continue
        early, late = order[:k], order[k:]

        for direction, tr_s, te_s in (("forward", early, late),
                                      ("reverse", late, early)):
            m_tr = np.isin(sessions, tr_s)
            m_te = np.isin(sessions, te_s)
            ytr, yte = c.y[m_tr], c.y[m_te]
            if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
                print("  frac %.1f %s: a side is single-class, skipped"
                      % (frac, direction), flush=True)
                continue
            Xtr, Xte = c.X[m_tr], c.X[m_te]
            for key in MODELS:
                rows.append(dict(
                    protocol="temporal", direction=direction, train_frac=frac,
                    rep=0, model=key, n_train_sessions=len(tr_s),
                    n_test_sessions=len(te_s), n_train=int(m_tr.sum()),
                    n_test=int(m_te.sum()),
                    train_prevalence=float(ytr.mean()),
                    test_prevalence=float(yte.mean()),
                    **evaluate(key, Xtr, ytr, Xte, yte)))
            print("  temporal %s frac=%.1f done" % (direction, frac), flush=True)

        # Control: the same session counts, drawn at random rather than by time.
        for rep in range(args.reps):
            rng = np.random.default_rng(1000 + rep)
            perm = rng.permutation(order)
            tr_s, te_s = perm[:k], perm[k:]
            m_tr, m_te = np.isin(sessions, tr_s), np.isin(sessions, te_s)
            ytr, yte = c.y[m_tr], c.y[m_te]
            if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
                continue
            Xtr, Xte = c.X[m_tr], c.X[m_te]
            for key in MODELS:
                rows.append(dict(
                    protocol="random_sessions", direction="n/a",
                    train_frac=frac, rep=rep, model=key,
                    n_train_sessions=len(tr_s), n_test_sessions=len(te_s),
                    n_train=int(m_tr.sum()), n_test=int(m_te.sum()),
                    train_prevalence=float(ytr.mean()),
                    test_prevalence=float(yte.mean()),
                    **evaluate(key, Xtr, ytr, Xte, yte)))
        print("  control frac=%.1f: %d reps done (%.0fs)"
              % (frac, args.reps, time.time() - t0), flush=True)

    R = pd.DataFrame(rows)
    R.to_csv(OUT / "raw/drift_runs.csv", index=False)

    # Temporal against the control distribution, per model and fraction.
    comp = []
    for (frac, key), g in R.groupby(["train_frac", "model"]):
        ctrl = g[g.protocol == "random_sessions"]["f1_macro"].to_numpy()
        if len(ctrl) < 3:
            continue
        for direction in ("forward", "reverse"):
            tg = g[(g.protocol == "temporal") & (g.direction == direction)]
            if not len(tg):
                continue
            v = float(tg["f1_macro"].iloc[0])
            # Where does the temporal score sit in the control distribution?
            pct = float((ctrl < v).mean())
            z = float((v - ctrl.mean()) / ctrl.std(ddof=1)) if ctrl.std(ddof=1) > 0 else float("nan")
            comp.append(dict(
                train_frac=frac, model=key, direction=direction,
                temporal_f1=v, control_mean=float(ctrl.mean()),
                control_sd=float(ctrl.std(ddof=1)),
                control_min=float(ctrl.min()), control_max=float(ctrl.max()),
                delta=v - float(ctrl.mean()), z=z, percentile_in_control=pct,
                outside_control_range=bool(v < ctrl.min() or v > ctrl.max()),
                n_control=len(ctrl)))
    C = pd.DataFrame(comp)
    C.to_csv(OUT / "processed/temporal_vs_control.csv", index=False)

    summ = (R.groupby(["protocol", "direction", "train_frac", "model"])
            .agg(f1_macro=("f1_macro", "mean"), f1_sd=("f1_macro", "std"),
                 recall=("recall", "mean"), fpr=("fpr", "mean"),
                 brier=("brier", "mean"), ece=("ece", "mean"),
                 ppv_deploy=("ppv_deploy", "mean"),
                 false_alerts_per_hour=("false_alerts_per_hour", "mean"),
                 n=("f1_macro", "size")).reset_index())
    summ.to_csv(OUT / "processed/drift_summary.csv", index=False)

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-034", layer="radio (network layer has NO time column)",
        n_sessions=int(n_sess), time_span_days=52.96,
        train_fracs=list(TRAIN_FRACS), control_reps=args.reps,
        models=list(MODELS), pi=PI, lambda_b=LAMBDA_B,
        session_ordering=("session id is assigned by cumsum over time-sorted "
                          "records, so it IS the temporal order"),
        power_note=("30 sessions is a small population. This design detects a "
                    "large temporal effect and nothing subtler."),
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2), encoding="utf-8")

    print("\n=== temporal score against the random-session control ===")
    nt = C[~C.model.isin(["majority", "stratified"])]
    print(nt[["train_frac", "model", "direction", "temporal_f1", "control_mean",
              "control_sd", "delta", "z", "outside_control_range"]].to_string(
                  index=False, float_format=lambda v: "%.4f" % v))
    out = nt[nt.outside_control_range]
    print("\ntemporal configurations falling OUTSIDE the control range: %d of %d"
          % (len(out), len(nt)))
    print("\nwrote %s  (%.0fs)" % (OUT, time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
