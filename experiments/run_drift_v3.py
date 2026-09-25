#!/usr/bin/env python3
"""EXP-053: time-ordered splits of the radio layer, with category coverage.

The round-2 review (R1-W2, R1-W3, R1-W6, R2-C4) found three problems in the
EXP-051 drift analysis:

  1. drift was measured in macro-F1 across a prevalence shift: forward splits
     trained on 50-67% attack windows and tested on 88-92%, while the random
     control sat near 75% on both sides;
  2. false alerts were computed at the flow arrival rate (240,000 per hour) for
     a window-level detector;
  3. nobody checked whether the time-disjoint test sessions held attack
     categories absent from training.

Checking (3) showed why the design cannot work on this corpus. The radio capture
ran nine benign sessions first (0-8), then each attack category in a block
(probe 9-11, brute force 12-14, DoS 15-16, web 17-21, DoS 22, DDoS 23-28), and
one last benign session (29). Splitting on session order holds out whole attack
categories, and the forward test set has exactly one benign session.

Three analyses replace it:

A  Coverage audit of the EXP-051 splits (no model is fitted): for every training
   fraction and direction, and for the random-session control draws with the
   same seeds as EXP-051, which test categories are absent from training.

B  Category-stratified time split. Forward: the LATEST session of every
   category, benign included, is the test set. Reverse: the EARLIEST. Every test
   category is in training by construction. Control: one session of every
   category drawn at random, R draws. The distance from the control is the
   effect of time order with category coverage held fixed.

C  Leave-one-benign-session-out. For each of the ten benign sessions, train on
   all other sessions and score that session alone. If session 29, the only
   benign capture after the attack campaign, draws a far higher false positive
   rate than the nine early sessions, something changed over time. If early
   sessions draw similar rates, the effect is session heterogeneity.

Metrics: balanced accuracy and ROC-AUC are primary because class prevalence
cannot move them. Macro-F1 is kept only for comparison with EXP-051. False
alerts are per benign UE-hour: FPR x 225 windows of 16 s.

Usage:  python experiments/run_drift_v3.py [--reps 50]
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

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.data import load_radio, radio_session_timeline  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import fit_model, predict_scores  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-053"
MODELS = ("logreg", "tree", "rf", "xgboost", "hgb", "mlp", "stratified", "majority")
NONTRIVIAL = MODELS[:6]
TEMPORAL_SEEDS = (11, 12, 13, 14, 15)   # the single temporal split, five model seeds
CONTROL_SEED = 11                       # every control draw, as in EXP-051
TRAIN_FRACS = (0.4, 0.5, 0.6, 0.7)      # EXP-051's fractions, for the audit
WINDOWS_PER_UE_HOUR = 225               # 3600 s / 16 s


def log(msg: str) -> None:
    print(msg, flush=True)


def fit_eval(key: str, seed: int, Xtr, ytr, Xte, yte, cte) -> dict:
    m = fit_model(key, Xtr, ytr, seed)
    s = predict_scores(m, Xte)
    rec = {}
    if len(np.unique(yte)) > 1:
        d = detection_metrics(yte, s, 0.5)
        rec.update(balanced_accuracy=d["balanced_accuracy"], roc_auc=d["roc_auc"],
                   f1_macro=d["f1_macro"], recall=d["recall"], fpr=d["fpr"])
    else:
        pred = (s >= 0.5).astype(int)
        ben = yte == 0
        rec.update(balanced_accuracy=np.nan, roc_auc=np.nan, f1_macro=np.nan,
                   recall=np.nan,
                   fpr=float(pred[ben].mean()) if ben.any() else np.nan)
    rec["false_alerts_per_benign_ue_hour"] = (rec["fpr"] * WINDOWS_PER_UE_HOUR
                                              if np.isfinite(rec["fpr"]) else np.nan)
    pred = (s >= 0.5).astype(int)
    for cat in np.unique(cte):
        mk = cte == cat
        # recall for attack categories, specificity for benign
        rec[f"det_{cat}"] = float(pred[mk].mean() if cat != "benign"
                                  else 1 - pred[mk].mean())
    return rec


def coverage_audit(sessions: np.ndarray, cat_of: dict, reps: int) -> pd.DataFrame:
    """A: categories that EXP-051's session-order splits hold out."""
    order = np.sort(np.unique(sessions))
    n = len(order)
    rows = []
    for frac in TRAIN_FRACS:
        k = int(round(frac * n))
        early, late = order[:k], order[k:]
        splits = [("temporal", "forward", 0, early, late),
                  ("temporal", "reverse", 0, late, early)]
        for rep in range(reps):
            perm = np.random.default_rng(1000 + rep).permutation(order)  # EXP-051 seeds
            splits.append(("random_sessions", "n/a", rep, perm[:k], perm[k:]))
        for proto, direction, rep, tr, te in splits:
            ctr = {cat_of[s] for s in tr}
            cte = {cat_of[s] for s in te}
            unseen = sorted(cte - ctr)
            rows.append(dict(
                protocol=proto, direction=direction, train_frac=frac, rep=rep,
                n_train_sessions=len(tr), n_test_sessions=len(te),
                test_categories=",".join(sorted(cte)),
                unseen_test_categories=",".join(unseen),
                n_unseen_attack_categories=len([c for c in unseen if c != "benign"]),
                benign_test_sessions=",".join(str(s) for s in sorted(te)
                                              if cat_of[s] == "benign"),
                n_benign_train_sessions=sum(cat_of[s] == "benign" for s in tr)))
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=50,
                    help="random category-stratified control draws")
    args = ap.parse_args()
    t0 = time.time()
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    c = load_radio()
    tl = radio_session_timeline()
    sessions = np.asarray(c.groups)
    cat_of = dict(zip(tl.session, tl.category))
    # the timeline and the windows must agree on every session's category
    for s in np.unique(sessions):
        cats = set(c.category[sessions == s])
        if cats != {cat_of[s]}:
            raise AssertionError(f"session {s}: windows {cats} vs timeline {cat_of[s]}")
    n_win = pd.Series(sessions).value_counts().sort_index()
    tl["n_windows"] = tl.session.map(n_win).fillna(0).astype(int)
    tl.to_csv(OUT / "processed/session_timeline.csv", index=False)
    log("radio: %d windows, %d sessions; timeline:" % (len(c.y), len(tl)))
    log(tl[["session", "day", "category", "n_windows", "n_ues"]]
        .to_string(index=False, float_format=lambda v: "%.2f" % v))

    # ---- A ------------------------------------------------------------------
    A = coverage_audit(sessions, cat_of, reps=20)
    A.to_csv(OUT / "raw/coverage_audit.csv", index=False)
    tA = A[A.protocol == "temporal"]
    log("\nA. EXP-051 temporal splits:")
    log(tA[["direction", "train_frac", "unseen_test_categories",
            "benign_test_sessions"]].to_string(index=False))
    cA = A[A.protocol == "random_sessions"]
    log("   random control draws with >= 1 unseen attack category: %d of %d"
        % ((cA.n_unseen_attack_categories > 0).sum(), len(cA)))

    # ---- B ------------------------------------------------------------------
    by_cat: dict[str, list] = {}
    for s in sorted(cat_of):
        by_cat.setdefault(cat_of[s], []).append(s)
    if min(len(v) for v in by_cat.values()) < 2:
        raise AssertionError("every category needs two sessions for B")
    X, y, cat = c.X.to_numpy(), c.y, np.asarray(c.category)

    splits = [("time_stratified", "forward", 0, [v[-1] for v in by_cat.values()]),
              ("time_stratified", "reverse", 0, [v[0] for v in by_cat.values()])]
    for rep in range(args.reps):
        rng = np.random.default_rng(2000 + rep)
        splits.append(("random_stratified", "n/a", rep,
                       [int(rng.choice(v)) for v in by_cat.values()]))
    rows = []
    for proto, direction, rep, test_s in splits:
        te = np.isin(sessions, test_s)
        tr = ~te
        seeds = TEMPORAL_SEEDS if proto == "time_stratified" else (CONTROL_SEED,)
        for key in MODELS:
            for seed in seeds:
                rec = fit_eval(key, seed, X[tr], y[tr], X[te], y[te], cat[te])
                rows.append(dict(protocol=proto, direction=direction, rep=rep,
                                 model=key, model_seed=seed,
                                 test_sessions=",".join(map(str, sorted(test_s))),
                                 n_train=int(tr.sum()), n_test=int(te.sum()),
                                 train_prevalence=float(y[tr].mean()),
                                 test_prevalence=float(y[te].mean()),
                                 n_unseen_test_categories=len(
                                     set(cat[te]) - set(cat[tr])), **rec))
        if proto == "time_stratified" or rep % 10 == 9:
            log("B. %s %s rep %d done (%.0fs)" % (proto, direction, rep,
                                                  time.time() - t0))
    B = pd.DataFrame(rows)
    B.to_csv(OUT / "raw/stratified_time_runs.csv", index=False)

    comp = []
    ctrl = B[B.protocol == "random_stratified"]
    for key in MODELS:
        cg = ctrl[ctrl.model == key]
        for direction in ("forward", "reverse"):
            tg = B[(B.protocol == "time_stratified") & (B.direction == direction)
                   & (B.model == key)]
            rec = dict(model=key, direction=direction, n_control=len(cg),
                       test_sessions=tg.test_sessions.iloc[0],
                       test_prevalence=float(tg.test_prevalence.iloc[0]),
                       control_test_prevalence=float(cg.test_prevalence.mean()))
            for met in ("balanced_accuracy", "roc_auc", "f1_macro", "fpr", "recall",
                        "false_alerts_per_benign_ue_hour"):
                v = float(tg[met].mean())
                cv = cg[met].to_numpy(float)
                rec[f"{met}_temporal"] = v
                rec[f"{met}_temporal_min"] = float(tg[met].min())
                rec[f"{met}_temporal_max"] = float(tg[met].max())
                rec[f"{met}_control_mean"] = float(np.nanmean(cv))
                rec[f"{met}_control_sd"] = float(np.nanstd(cv, ddof=1))
                rec[f"{met}_delta"] = v - float(np.nanmean(cv))
                # descriptive: share of control draws at or below the temporal value
                rec[f"{met}_pct_control_le"] = float(np.mean(cv <= v))
                rec[f"{met}_p_low"] = float((1 + np.sum(cv <= v)) / (1 + len(cv)))
            comp.append(rec)
    Cmp = pd.DataFrame(comp)
    Cmp.to_csv(OUT / "processed/stratified_time_vs_control.csv", index=False)
    log("\nB. time-stratified minus random-stratified control (BA, AUC):")
    log(Cmp[Cmp.model.isin(NONTRIVIAL)][
        ["model", "direction", "balanced_accuracy_temporal",
         "balanced_accuracy_control_mean", "balanced_accuracy_delta",
         "balanced_accuracy_p_low", "roc_auc_delta", "fpr_temporal",
         "fpr_control_mean"]].to_string(index=False, float_format=lambda v: "%.3f" % v))

    # ---- C ------------------------------------------------------------------
    rows = []
    for b in by_cat["benign"]:
        te = sessions == b
        tr = ~te
        for key in NONTRIVIAL:
            rec = fit_eval(key, CONTROL_SEED, X[tr], y[tr], X[te], y[te], cat[te])
            rows.append(dict(held_out_session=int(b),
                             day=float(tl.set_index("session").loc[b, "day"]),
                             n_windows=int(te.sum()), model=key,
                             fpr=rec["fpr"],
                             false_alerts_per_benign_ue_hour=rec[
                                 "false_alerts_per_benign_ue_hour"]))
        log("C. benign session %d held out (%.0fs)" % (b, time.time() - t0))
    Cb = pd.DataFrame(rows)
    Cb.to_csv(OUT / "raw/benign_loso_runs.csv", index=False)
    piv = Cb.pivot(index="held_out_session", columns="model", values="fpr")
    piv["mean"] = piv[list(NONTRIVIAL)].mean(axis=1)
    piv.to_csv(OUT / "processed/benign_loso_fpr.csv")
    log("\nC. FPR on each held-out benign session:")
    log(piv.to_string(float_format=lambda v: "%.3f" % v))

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-053", layer="radio",
        answers=["R1-W2", "R1-W3", "R1-W6", "R2-C4", "R1-minor-5"],
        design=dict(A="coverage audit of EXP-051 session-order splits",
                    B="latest (forward) or earliest (reverse) session of every "
                      "category held out, against a random session of every "
                      "category",
                    C="leave-one-benign-session-out FPR"),
        n_sessions=int(len(tl)), sessions_per_category={k: len(v) for k, v in by_cat.items()},
        control_reps=args.reps, temporal_model_seeds=list(TEMPORAL_SEEDS),
        control_model_seed=CONTROL_SEED, models=list(MODELS),
        false_alert_unit="per benign UE-hour (FPR x 225)",
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2), encoding="utf-8")
    log("\nwrote %s (%.0fs)" % (OUT, time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
