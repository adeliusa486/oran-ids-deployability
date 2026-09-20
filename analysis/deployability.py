#!/usr/bin/env python3
"""EXP-035: multi-dimensional deployability, without a fake single score.

The brief is explicit that no composite "deployability score" may be invented,
and it is right to be. Collapsing latency, alert burden and transfer into one
number requires weights, the weights are unmeasurable, and whoever picks them
picks the winner. This module therefore assembles the dimensions side by side
and identifies the **Pareto-efficient** set, which needs no weights at all.

Dimensions, and their honest status:

  detection quality      EXP-002/EXP-026, macro-F1 on held-out source
  generalisation         EXP-026, macro-F1 on the target, and its distance
                         above the trivial floor there
  operational burden     EXP-027, pooled deployment PPV and false alerts/hour
  calibration            EXP-028, Brier and ECE
  tail latency           EXP-005, p99 -- EMULATED, no real RIC (EXP-031)
  extraction cost        EXP-030
  robustness             EXP-033, worst-case macro-F1 drop across attacks
  drift                  EXP-034, temporal versus control
  CPU / RAM under load   NOT MEASURED -- needs the Linux host. Reported absent.
  integration complexity NOT MEASURED, and arguably not measurable here

A dimension that has not been measured is left as NaN and excluded from the
Pareto computation, with the exclusion printed. It is never imputed, and never
quietly dropped so that the frontier looks cleaner than the evidence.

Usage:  python analysis/deployability.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RES = Path("results")
OUT = Path("results/EXP-035")

# name -> (column, direction) where +1 means larger is better.
AXES = {
    "source_f1": +1,
    "target_f1": +1,
    "target_above_floor": +1,
    "ppv_deploy_target": +1,
    "false_alerts_per_hour": -1,
    "brier_target": -1,
    "p99_latency_ms": -1,
    "worst_case_f1_drop": -1,
    "drift_delta": +1,
}


def _read(p: Path):
    return pd.read_csv(p) if p.exists() else None


def collect() -> pd.DataFrame:
    models = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp"]
    df = pd.DataFrame({"model": models}).set_index("model")

    t = _read(RES / "EXP-026/processed/transfer_summary__a_to_b.csv")
    if t is not None:
        floor = float(t[t.model == "stratified"].target_f1.iloc[0])
        t = t.set_index("model")
        df["source_f1"] = t["source_f1"]
        df["target_f1"] = t["target_f1"]
        df["target_above_floor"] = t["target_f1"] - floor
        df["brier_target"] = t.get("tgt_brier")
        df["delta_f1"] = t["delta_f1"]

    g = _read(RES / "EXP-027/raw/pi_lambda_grid.csv")
    if g is not None:
        s = g[(g.surface == "d_b_target") & (g.pi == 0.002)
              & (g.lambda_b == 240000.0)].set_index("model")
        df["ppv_deploy_target"] = s["ppv"]
        df["false_alerts_per_hour"] = s["false_alerts_per_hour"]

    lat = _read(RES / "EXP-005/raw/latency_radio.csv")
    if lat is not None and "model" in lat.columns:
        col = next((c for c in ("p99", "q99", "latency_ms") if c in lat.columns), None)
        if col == "p99" or col == "q99":
            df["p99_latency_ms"] = lat.groupby("model")[col].mean()
        elif col:
            df["p99_latency_ms"] = lat.groupby("model")[col].quantile(0.99)

    adv = _read(RES / "EXP-033/processed/adversarial_summary.csv")
    if adv is not None:
        w = adv[adv.eps > 0].groupby("model")["f1_drop"].max()
        df["worst_case_f1_drop"] = w

    dr = _read(RES / "EXP-034/processed/temporal_vs_control.csv")
    if dr is not None:
        df["drift_delta"] = dr.groupby("model")["delta"].mean()

    # Not measured. Present as columns so their absence is visible in the table.
    df["cpu_under_load"] = np.nan
    df["ram_under_load"] = np.nan
    df["integration_complexity"] = np.nan
    return df.reset_index()


def pareto(df: pd.DataFrame, axes: dict) -> pd.Series:
    """Non-dominated set over the usable axes.

    ``a`` dominates ``b`` when it is no worse on every axis and strictly better
    on at least one.
    """
    use = [c for c in axes if c in df.columns and df[c].notna().all()]
    if not use:
        return pd.Series(False, index=df.index)
    M = np.column_stack([df[c].to_numpy() * axes[c] for c in use])
    n = len(df)
    eff = np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if np.all(M[j] >= M[i]) and np.any(M[j] > M[i]):
                eff[i] = False
                break
    return pd.Series(eff, index=df.index)


def main() -> int:
    for d in ("processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    df = collect()
    present = [c for c in AXES if c in df.columns and df[c].notna().all()]
    partial = [c for c in AXES if c in df.columns and df[c].notna().any()
               and not df[c].notna().all()]
    absent = [c for c in AXES if c not in df.columns or not df[c].notna().any()]
    not_measured = ["cpu_under_load", "ram_under_load", "integration_complexity"]

    print("dimensions usable for the frontier (%d): %s" % (len(present), present))
    if partial:
        print("dimensions PARTIALLY populated, excluded: %s" % partial)
    if absent:
        print("dimensions absent, excluded: %s" % absent)
    print("dimensions NOT MEASURED at all: %s" % not_measured)

    df["pareto_efficient"] = pareto(df, {k: AXES[k] for k in present}).to_numpy()
    df.to_csv(OUT / "processed/deployability_matrix.csv", index=False)

    # Pairwise frontiers a reader can actually act on.
    pairs = [("target_f1", "false_alerts_per_hour"),
             ("target_above_floor", "ppv_deploy_target"),
             ("source_f1", "target_f1"),
             ("target_f1", "p99_latency_ms"),
             ("target_f1", "worst_case_f1_drop")]
    prs = []
    for a, b in pairs:
        if a not in df.columns or b not in df.columns:
            continue
        sub = df[["model", a, b]].dropna()
        if len(sub) < 2:
            continue
        eff = pareto(sub.reset_index(drop=True), {a: AXES[a], b: AXES[b]})
        for (_, r), e in zip(sub.iterrows(), eff):
            prs.append(dict(axis_x=a, axis_y=b, model=r.model,
                            x=float(r[a]), y=float(r[b]), efficient=bool(e)))
    if prs:
        pd.DataFrame(prs).to_csv(OUT / "processed/pairwise_frontiers.csv",
                                 index=False)

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-035",
        axes_used=present, axes_partial=partial, axes_absent=absent,
        axes_not_measured=not_measured,
        no_composite_score=("deliberate: collapsing these onto one number needs "
                            "weights, the weights are unmeasurable, and whoever "
                            "picks them picks the winner"),
        pareto_efficient=df[df.pareto_efficient].model.tolist(),
        latency_caveat="p99 is EMULATED; no real RIC measurement exists (EXP-031)"),
        indent=2), encoding="utf-8")

    # Which axis does each architecture actually win? With six points and eight
    # axes, "everything is Pareto-efficient" is close to guaranteed and says
    # little on its own. Naming the axis each model wins says what the frontier
    # is made of, and turns a degenerate-looking result into a usable one.
    wins = {m: [] for m in df.model}
    for c in present:
        best = df.loc[(df[c] * AXES[c]).idxmax(), "model"]
        wins[best].append(c)
    df["wins_on"] = df.model.map(lambda m: ";".join(wins[m]) or "-")
    df["n_wins"] = df.model.map(lambda m: len(wins[m]))
    df.to_csv(OUT / "processed/deployability_matrix.csv", index=False)

    cols = ["model"] + present + ["pareto_efficient"]
    print("\n=== deployability matrix ===")
    print(df[cols].to_string(index=False, float_format=lambda v: "%.4f" % v))

    print("\n=== which axis does each architecture win? ===")
    for _, r in df.sort_values("n_wins", ascending=False).iterrows():
        print("  %-8s %d win(s): %s" % (r.model, r.n_wins, r.wins_on))

    n_eff = int(df.pareto_efficient.sum())
    print("\nPareto-efficient over %d axes: %d of %d architectures"
          % (len(present), n_eff, len(df)))
    if n_eff == len(df):
        print("  ALL of them. No architecture dominates another on deployability.")
        print("  With 6 points and 8 axes some of that is dimensionality, but the")
        print("  per-axis winners above show it is not only that: the operational")
        print("  and detection axes genuinely disagree about which model to pick.")
    print("\nNo composite score is computed, by design.")
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
