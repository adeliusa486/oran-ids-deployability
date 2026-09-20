#!/usr/bin/env python3
"""EXP-033: adversarial and degraded-telemetry robustness, read operationally.

The previous campaign cut this phase (D-009). It is run now, with a scope that
the literature permits.

**What this cannot claim.** Adversarial attacks on O-RAN ML components are well
covered: evasion against xApps (arXiv:2309.03844), black-box evasion under
near-RT timing constraints (arXiv:2510.18160), KPI poisoning through the E2 path
(arXiv:2505.05537), and a system-level analysis at WiSec 2024. This experiment is
not first and does not claim to be.

**What it adds.** Those studies report accuracy degradation. An operator does not
experience accuracy; they experience an alert queue and a threshold that either
still works or does not. Every attack here is therefore scored on three axes the
prior work does not report together:

  detection    macro-F1, and recall on attack rows (attack success)
  burden       false alerts per hour at the declared base rate
  control      whether the operating threshold still reaches a usable PPV

Attacks, each with a stated threat model. The distinction that matters is
between what an attacker can actually do to a flow record and what is merely an
arbitrary perturbation of a feature vector.

  gaussian_noise      telemetry corruption, not an attacker: sensor noise at a
                      fraction of each feature's own scale
  missing_telemetry   a fraction of features zeroed -- an E2 subscription gap or
                      a dropped report
  stale_telemetry     features carried over from an earlier record, which is what
                      a delayed E2 indication looks like downstream
  scaling_attack      one feature multiplied by a constant, the classic
                      KPI-manipulation shape
  evasion_unconstrained  bounded perturbation in every direction. Reported as an
                      UPPER BOUND on attack success and explicitly NOT a
                      realisable attack: it lets the attacker reduce byte and
                      packet counts they have already sent
  evasion_constrained an attacker can pad and delay but cannot un-send: only
                      increases to bytes, packets and duration are allowed. This
                      is the realistic number
  label_poisoning     a fraction of TRAINING labels flipped, then refit

Perturbations are applied in the model's input space. Since log1p is monotone,
"increase the byte count" and "increase the log byte count" are the same
constraint, so the constrained threat model is preserved by the representation.

Usage:  python experiments/run_adversarial.py [--seeds N] [--quick]
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

from oran_ids.data import load_network_shared  # noqa: E402
from oran_ids.features.shared import COLUMNS  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402

warnings.filterwarnings("ignore")

OUT = Path("results/EXP-033")
SPLIT_SEEDS = list(range(101, 121))
MODEL_SEED = 11
SUBSAMPLE = 200_000
PI, LAMBDA_B = 0.002, 240_000.0
MODELS = ("logreg", "tree", "rf", "xgboost", "hgb", "mlp")
EPS_GRID = (0.0, 0.01, 0.05, 0.10, 0.25, 0.50)
POISON_GRID = (0.0, 0.01, 0.05, 0.10, 0.25)

# Features an attacker can inflate but not deflate: they can pad packets, send
# more of them and drag a flow out, but cannot retract bytes already sent.
MONOTONE_UP = ("duration", "src_bytes", "src_pkts", "tot_pkts", "tot_bytes",
               "mean_pkt_size", "src_mean_pkt_size", "bytes_per_s", "pkts_per_s")
# The protocol one-hot is structural: perturbing it produces a vector that
# corresponds to no packet. It is never touched.
NEVER_PERTURB = tuple(c for c in COLUMNS if c.startswith("proto_"))


def _scale(X: pd.DataFrame) -> np.ndarray:
    """Per-feature scale, used to make eps mean the same thing for each column."""
    s = X.std(axis=0).to_numpy()
    s[s == 0] = 1.0
    return s


def attack(name: str, X: pd.DataFrame, y: np.ndarray, eps: float,
           rng: np.random.Generator) -> pd.DataFrame:
    """Return a perturbed copy. Attacks apply to ATTACK rows only where an
    attacker is the agent; telemetry faults apply to every row."""
    if eps == 0.0 or name == "clean":
        return X
    Z = X.copy()
    cols = [c for c in COLUMNS if c not in NEVER_PERTURB]
    sc = pd.Series(_scale(X[cols]), index=cols)

    if name == "gaussian_noise":
        for c in cols:
            Z[c] = Z[c] + rng.normal(0, eps * sc[c], len(Z))
    elif name == "missing_telemetry":
        k = max(1, int(round(eps * len(cols))))
        drop = rng.choice(cols, size=k, replace=False)
        Z[list(drop)] = 0.0
    elif name == "stale_telemetry":
        k = max(1, int(round(eps * len(Z))))
        idx = rng.choice(len(Z), size=k, replace=False)
        src = np.maximum(idx - 1, 0)
        Z.iloc[idx, :] = X.iloc[src, :].to_numpy()
    elif name == "scaling_attack":
        c = "tot_bytes"
        m = y == 1
        Z.loc[m, c] = Z.loc[m, c] * (1.0 + eps)
    elif name == "evasion_unconstrained":
        m = y == 1
        for c in cols:
            Z.loc[m, c] = Z.loc[m, c] + rng.uniform(
                -eps * sc[c], eps * sc[c], int(m.sum()))
    elif name == "evasion_constrained":
        m = y == 1
        for c in cols:
            if c in MONOTONE_UP:
                Z.loc[m, c] = Z.loc[m, c] + rng.uniform(
                    0, eps * sc[c], int(m.sum()))
    else:
        raise ValueError(name)
    return Z


def operational(tpr: float, fpr: float) -> dict:
    lam_a = LAMBDA_B * PI / (1 - PI)
    tp_h, fp_h = tpr * lam_a, fpr * LAMBDA_B
    al = tp_h + fp_h
    return dict(alerts_per_hour=al, false_alerts_per_hour=fp_h,
                ppv_deploy=float(tp_h / al) if al > 0 else float("nan"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    seeds = SPLIT_SEEDS[:2] if args.quick else SPLIT_SEEDS[:args.seeds]
    models = ("logreg", "tree") if args.quick else MODELS
    n_sub = 40_000 if args.quick else SUBSAMPLE
    t0 = time.time()

    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    src = load_network_shared()
    print("source %s, attack %.4f" % (src.X.shape, src.y.mean()), flush=True)

    rows, poison_rows = [], []
    attacks = ("gaussian_noise", "missing_telemetry", "stale_telemetry",
               "scaling_attack", "evasion_unconstrained", "evasion_constrained")

    for seed in seeds:
        rng = np.random.default_rng(seed)
        idx = np.sort(rng.choice(len(src.y), size=min(n_sub, len(src.y)),
                                 replace=False))
        X = src.X.iloc[idx].reset_index(drop=True)
        y, g = src.y[idx], src.groups[idx]
        sp = group_disjoint_split(y, g, seed=seed, n_folds=1)[0]
        sp.check_disjoint(g)
        Xtr, ytr = X.iloc[sp.train_idx], y[sp.train_idx]
        Xte, yte = X.iloc[sp.test_idx].reset_index(drop=True), y[sp.test_idx]
        if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
            continue

        for key in models:
            t1 = time.time()
            model = fit_model(key, Xtr, ytr, MODEL_SEED)
            base = detection_metrics(yte, predict_scores(model, Xte), 0.5)

            for name in attacks:
                for eps in EPS_GRID:
                    r = np.random.default_rng(hash((seed, key, name, eps)) % 2**32)
                    Z = attack(name, Xte, yte, eps, r)
                    m = detection_metrics(yte, predict_scores(model, Z), 0.5)
                    rows.append(dict(
                        seed=seed, model=key, attack=name, eps=eps,
                        f1_macro=m["f1_macro"], recall=m["recall"],
                        fpr=m["fpr"], precision=m["precision"],
                        f1_drop=base["f1_macro"] - m["f1_macro"],
                        recall_drop=base["recall"] - m["recall"],
                        fpr_rise=m["fpr"] - base["fpr"],
                        **operational(m["recall"], m["fpr"])))

            # Poisoning needs a refit per rate, so it is kept separate and
            # deliberately small. Labels are flipped in TRAINING only.
            for rate in POISON_GRID:
                r = np.random.default_rng(hash((seed, key, "poison", rate)) % 2**32)
                yp = ytr.copy()
                if rate > 0:
                    k = int(round(rate * len(yp)))
                    fl = r.choice(len(yp), size=k, replace=False)
                    yp[fl] = 1 - yp[fl]
                if len(np.unique(yp)) < 2:
                    continue
                pm = fit_model(key, Xtr, yp, MODEL_SEED)
                m = detection_metrics(yte, predict_scores(pm, Xte), 0.5)
                poison_rows.append(dict(
                    seed=seed, model=key, poison_rate=rate,
                    f1_macro=m["f1_macro"], recall=m["recall"], fpr=m["fpr"],
                    f1_drop=base["f1_macro"] - m["f1_macro"],
                    **operational(m["recall"], m["fpr"])))

            print("  seed %d %-8s %.1fs" % (seed, key, time.time() - t1),
                  flush=True)

    A = pd.DataFrame(rows)
    A.to_csv(OUT / "raw/adversarial_runs.csv", index=False)
    P = pd.DataFrame(poison_rows)
    P.to_csv(OUT / "raw/poisoning_runs.csv", index=False)

    sa = (A.groupby(["attack", "model", "eps"])
          .agg(f1_macro=("f1_macro", "mean"), f1_drop=("f1_drop", "mean"),
               recall=("recall", "mean"), recall_drop=("recall_drop", "mean"),
               fpr=("fpr", "mean"), fpr_rise=("fpr_rise", "mean"),
               false_alerts_per_hour=("false_alerts_per_hour", "mean"),
               ppv_deploy=("ppv_deploy", "mean"), n=("f1_macro", "size"))
          .reset_index())
    sa.to_csv(OUT / "processed/adversarial_summary.csv", index=False)
    if len(P):
        sp_ = (P.groupby(["model", "poison_rate"])
               .agg(f1_macro=("f1_macro", "mean"), f1_drop=("f1_drop", "mean"),
                    recall=("recall", "mean"), fpr=("fpr", "mean"),
                    false_alerts_per_hour=("false_alerts_per_hour", "mean"),
                    ppv_deploy=("ppv_deploy", "mean"), n=("f1_macro", "size"))
               .reset_index())
        sp_.to_csv(OUT / "processed/poisoning_summary.csv", index=False)

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-033", seeds=list(seeds), models=list(models),
        subsample=n_sub, eps_grid=list(EPS_GRID),
        poison_grid=list(POISON_GRID), attacks=list(attacks),
        pi=PI, lambda_b=LAMBDA_B,
        never_perturbed=list(NEVER_PERTURB),
        monotone_up=list(MONOTONE_UP),
        threat_model_note=("evasion_unconstrained is an UPPER BOUND and is not "
                           "realisable: it permits reducing bytes and packets "
                           "already sent. evasion_constrained is the realistic "
                           "number."),
        not_first=("adversarial attacks on O-RAN ML are prior art; this "
                   "experiment reports the operational reading, not primacy"),
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2), encoding="utf-8")

    print("\n=== macro-F1 drop at eps = 0.10 ===")
    v = sa[sa.eps == 0.10].pivot_table(index="model", columns="attack",
                                       values="f1_drop")
    print(v.to_string(float_format=lambda x: "%+.4f" % x))
    print("\n=== false alerts/hour at eps = 0.10 (clean baseline in eps=0) ===")
    w = sa[sa.eps.isin([0.0, 0.10])].pivot_table(
        index="model", columns=["attack", "eps"], values="false_alerts_per_hour")
    print(w.to_string(float_format=lambda x: "%.0f" % x))
    if len(P):
        print("\n=== label poisoning ===")
        print(sp_.pivot_table(index="model", columns="poison_rate",
                              values="f1_macro").to_string(
                                  float_format=lambda x: "%.4f" % x))
    print("\nwrote %s  (%.0fs)" % (OUT, time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
