#!/usr/bin/env python3
"""EXP-004 (X4): what does this detector cost an operator per hour?

Criterion 2. A detector's FPR is a property of the classifier; the alert volume
it produces is a property of the deployment. The bridge is arithmetic:

    false alerts/hour = FPR x lambda_b
    PPV               = TPR.pi / (TPR.pi + FPR.(1-pi))

Both pi (attack base rate) and lambda_b (benign flows per hour) are **declared
parameters**, not measurements -- neither is observable from these corpora
(plan A6). They are therefore swept, not asserted, and every result is also
reported per 10^5 benign flows so it ports to a deployment with a different
flow rate.

The underlying reasoning is Axelsson's (ACM TISSEC, 2000). Nothing here is a new
statistical insight. What is new is quantifying it for a specific O-RAN detector
under a group-disjoint protocol, alongside the transfer and latency criteria.

Usage:  python experiments/run_alert_burden.py [--layer radio|network]
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.data import load_network, load_radio  # noqa: E402
from oran_ids.metrics import detection_metrics, operational_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402

warnings.filterwarnings("ignore")

OUT = Path("results/EXP-004")
SPLIT_SEEDS = [101, 102, 103, 104, 105]
MODEL_SEED = 11

# Declared deployment parameters (configs/base.yaml). Neither is measured here.
PI_SWEEP = [1e-4, 3e-4, 1e-3, 2e-3, 3e-3, 1e-2, 3e-2, 1e-1]
PI_PRIMARY = 2e-3
LAMBDA_B = 240_000.0        # benign flows per hour
TAU_SWEEP = np.concatenate([np.arange(0.05, 1.0, 0.05), [0.95, 0.99, 0.995]])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", default="radio", choices=["radio", "network"])
    ap.add_argument("--models", nargs="*",
                    default=["logreg", "rf", "xgboost", "hgb", "mlp", "majority"])
    args = ap.parse_args()

    for d in ("raw", "processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    corpus = load_radio() if args.layer == "radio" else load_network()
    X, y, groups = corpus.X, corpus.y, corpus.groups
    print(f"{args.layer}: {len(y):,} rows, {corpus.summary()['n_groups']} groups, "
          f"{corpus.summary()['attack_prevalence_pct']}% attack")
    print(f"NOTE: the corpus prevalence above is a CAPTURE-SESSION artefact. "
          f"pi is swept over {PI_SWEEP[0]:g}..{PI_SWEEP[-1]:g} instead.\n")

    rows, sweep_rows = [], []
    for key in args.models:
        for s_seed in SPLIT_SEEDS:
            sp = group_disjoint_split(y, groups, seed=s_seed, n_folds=1)[0]
            if len(np.unique(y[sp.test_idx])) < 2:
                continue
            model = fit_model(key, X.iloc[sp.train_idx], y[sp.train_idx], MODEL_SEED)
            sc = predict_scores(model, X.iloc[sp.test_idx])
            yte = y[sp.test_idx]

            for tau in TAU_SWEEP:
                m = detection_metrics(yte, sc, float(tau))
                for pi in PI_SWEEP:
                    o = operational_metrics(m["fpr"], m["recall"],
                                            pi=pi, lambda_b=LAMBDA_B)
                    sweep_rows.append({"model": key, "split_seed": s_seed,
                                       "tau": float(tau), **o,
                                       "recall": m["recall"], "fpr": m["fpr"],
                                       "precision_corpus": m["precision"]})
            # the headline operating point: default threshold, primary pi
            m05 = detection_metrics(yte, sc, 0.5)
            o05 = operational_metrics(m05["fpr"], m05["recall"],
                                      pi=PI_PRIMARY, lambda_b=LAMBDA_B)
            rows.append({"model": key, "split_seed": s_seed, "tau": 0.5,
                         **{k: m05[k] for k in
                            ("f1", "f1_macro", "precision", "recall", "fpr",
                             "pr_auc", "pr_auc_benign")},
                         **o05})
        print(f"  {key:10s} done")

    raw = pd.DataFrame(rows)
    sweep = pd.DataFrame(sweep_rows)
    raw.to_csv(OUT / "raw" / f"operating_point_{args.layer}.csv", index=False)
    sweep.to_csv(OUT / "raw" / f"tau_pi_sweep_{args.layer}.csv", index=False)

    agg = (raw.groupby("model")
              .agg(f1_macro=("f1_macro", "mean"),
                   recall=("recall", "mean"), fpr=("fpr", "mean"),
                   corpus_precision=("precision", "mean"),
                   alerts_h=("alerts_per_hour", "mean"),
                   false_alerts_h=("false_alerts_per_hour", "mean"),
                   ppv=("ppv", "mean"),
                   alerts_100k=("alerts_per_100k_benign", "mean"))
              .sort_values("f1_macro", ascending=False))
    agg.to_csv(OUT / "processed" / f"alert_burden_{args.layer}.csv")

    print(f"\n=== ALERT BURDEN at tau=0.5, pi={PI_PRIMARY:g}, "
          f"lambda_b={LAMBDA_B:,.0f} benign flows/h ===")
    print(f"{'model':<10}{'macroF1':>9}{'recall':>8}{'FPR':>9}"
          f"{'corpusP':>9}{'alerts/h':>11}{'falseA/h':>11}{'PPV':>8}")
    for m, r in agg.iterrows():
        print(f"{m:<10}{r.f1_macro:>9.4f}{r.recall:>8.4f}{r.fpr:>9.5f}"
              f"{r.corpus_precision:>9.4f}{r.alerts_h:>11,.0f}"
              f"{r.false_alerts_h:>11,.0f}{r.ppv:>8.4f}")

    print("\nRead this next to the corpus precision column. A detector can show "
          "high precision on a 76-95% attack corpus and near-zero PPV at a "
          "realistic base rate; that gap IS Criterion 2.")

    # where does each model's PPV cross an operator-usable threshold?
    cross = []
    for key in agg.index:
        s = sweep[(sweep.model == key) & (np.isclose(sweep.pi, PI_PRIMARY))]
        s = s.groupby("tau")[["ppv", "recall", "alerts_per_hour"]].mean().reset_index()
        for target in (0.1, 0.25, 0.5):
            ok = s[s.ppv >= target]
            if len(ok):
                r0 = ok.iloc[0]
                cross.append({"model": key, "ppv_target": target,
                              "tau_required": r0.tau, "recall_at_tau": r0.recall,
                              "alerts_per_hour": r0.alerts_per_hour})
            else:
                cross.append({"model": key, "ppv_target": target,
                              "tau_required": None, "recall_at_tau": None,
                              "alerts_per_hour": None})
    cdf = pd.DataFrame(cross)
    cdf.to_csv(OUT / "processed" / f"ppv_crossings_{args.layer}.csv", index=False)
    print(f"\n=== threshold required to reach a usable PPV (pi={PI_PRIMARY:g}) ===")
    print(f"{'model':<10}{'PPV target':>11}{'tau needed':>12}{'recall there':>14}{'alerts/h':>11}")
    for _, r in cdf.iterrows():
        tau = f"{r.tau_required:.2f}" if r.tau_required is not None else "UNREACHABLE"
        rec = f"{r.recall_at_tau:.4f}" if r.recall_at_tau is not None else "-"
        al = f"{r.alerts_per_hour:,.0f}" if r.alerts_per_hour is not None else "-"
        print(f"{r.model:<10}{r.ppv_target:>11.2f}{tau:>12}{rec:>14}{al:>11}")

    (OUT / "statistics" / f"params_{args.layer}.json").write_text(json.dumps({
        "pi_sweep": PI_SWEEP, "pi_primary": PI_PRIMARY, "lambda_b": LAMBDA_B,
        "lambda_b_provenance": "DECLARED deployment parameter, not measured "
                               "(plan A6). Results are also given per 10^5 "
                               "benign flows so they port to other deployments.",
        "split_protocol": "group_disjoint", "split_seeds": SPLIT_SEEDS,
        "corpus": corpus.summary(),
    }, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
