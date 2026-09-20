#!/usr/bin/env python3
"""EXP-005 (X5): per-decision latency, at the tail, against a SWEPT budget.

Criterion 3. Three things this does that the draft did not:

1. **Sweeps the budget.** O-RAN specifies the near-real-time control loop over
   10 ms to 1 s. Prior work picks one end and reaches opposite verdicts: one
   study assumes 10 ms and passes, another assumes 1000 ms and passes with a
   p99 of ~140 ms -- a measurement that fails the first budget by 14x. A single
   asserted budget makes the verdict an authoring choice. We report, per
   architecture, the budget at which it crosses from conforming to not.

2. **Runs the floor first.** A no-op model gives the platform's own latency
   distribution. If the floor p99 is already near the budget, the finding is
   about the platform, not the models, and must be reported that way.

3. **Decomposes by stage.** Prior work measures a C-exported linear model at
   1-5 microseconds inside a real xApp, so an inference-cost story is already
   answered. The open question is whether feature construction dominates.

MEASUREMENT HONESTY. This host is Windows with no CPU isolation, so these are
**emulated-deployment** numbers: single-process Python timing of the inference
path, not a Near-RT RIC under load. They support the per-stage decomposition
and the relative ordering of architectures. They do NOT support a claim that a
given architecture meets a budget on real hardware. Every artefact this writes
is tagged ``measurement_class: emulated``.

Usage:  python experiments/run_latency.py [--layer radio] [--repeats 2000]
"""
from __future__ import annotations

import argparse
import gc
import json
import platform
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.data import load_network, load_radio  # noqa: E402
from oran_ids.models import fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402

warnings.filterwarnings("ignore")

OUT = Path("results/EXP-005")
# The O-RAN near-real-time control loop, end to end.
BUDGET_SWEEP_MS = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
PERCENTILES = [50, 90, 95, 99, 99.9]
WARMUP = 200


class _NoOpModel:
    """The floor. Its latency is the platform's, not a model's."""

    def predict_proba(self, X):
        n = len(X)
        return np.column_stack([np.zeros(n), np.zeros(n)])


def time_calls(fn, n: int, warmup: int = WARMUP) -> np.ndarray:
    for _ in range(warmup):
        fn()
    gc.collect()
    gc.disable()
    try:
        out = np.empty(n, dtype=np.float64)
        for i in range(n):
            t0 = time.perf_counter_ns()
            fn()
            out[i] = (time.perf_counter_ns() - t0) / 1e6   # ms
    finally:
        gc.enable()
    return out


def summarise(lat_ms: np.ndarray) -> dict:
    d = {f"p{p}".replace(".0", ""): float(np.percentile(lat_ms, p)) for p in PERCENTILES}
    d.update(mean=float(lat_ms.mean()), std=float(lat_ms.std()),
             min=float(lat_ms.min()), max=float(lat_ms.max()), n=int(len(lat_ms)))
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", default="radio", choices=["radio", "network"])
    ap.add_argument("--repeats", type=int, default=2000)
    ap.add_argument("--models", nargs="*",
                    default=["logreg", "tree", "rf", "xgboost", "hgb", "mlp"])
    args = ap.parse_args()

    for d in ("raw", "processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    corpus = load_radio() if args.layer == "radio" else load_network()
    X, y, groups = corpus.X, corpus.y, corpus.groups
    sp = group_disjoint_split(y, groups, seed=101, n_folds=1)[0]
    Xtr, ytr = X.iloc[sp.train_idx], y[sp.train_idx]
    Xte = X.iloc[sp.test_idx].reset_index(drop=True)

    env = {
        "measurement_class": "emulated",
        "warning": "Single-process Python timing on a non-isolated Windows host. "
                   "Supports per-stage decomposition and relative ordering. Does "
                   "NOT support a conformance claim on real RIC hardware.",
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "n_features": int(X.shape[1]),
        "layer": args.layer,
        "repeats": args.repeats,
        "warmup": WARMUP,
    }
    print(json.dumps(env, indent=2), "\n")

    one = Xte.iloc[[0]]
    rows = []

    # ---- 1. the floor, first ------------------------------------------------
    floor = _NoOpModel()
    lat = time_calls(lambda: predict_scores(floor, one), args.repeats)
    fs = summarise(lat)
    rows.append({"model": "FLOOR (no-op)", "stage": "end_to_end", **fs})
    print(f"FLOOR p50={fs['p50']:.4f} p99={fs['p99']:.4f} ms  <- platform, not a model")
    if fs["p99"] > 1.0:
        print("  WARNING: the floor p99 already exceeds 1 ms. Any sub-millisecond "
              "budget result below is about this platform, not the models.")

    # ---- 2. per model: feature access, inference, end to end ----------------
    for key in args.models:
        model = fit_model(key, Xtr, ytr, 11)
        # feature "construction" here is the DataFrame->array marshalling that
        # any deployed wrapper must also do. It is not packet parsing; real
        # feature extraction from packets is measured separately in the
        # exporter throughput and is far larger.
        lat_feat = time_calls(lambda: one.to_numpy(dtype=np.float32), args.repeats)
        arr = one.to_numpy(dtype=np.float32)
        lat_inf = time_calls(lambda: predict_scores(model, arr), args.repeats)
        lat_e2e = time_calls(lambda: predict_scores(model, one), args.repeats)

        for stage, lt in (("feature_marshal", lat_feat),
                          ("inference", lat_inf),
                          ("end_to_end", lat_e2e)):
            rows.append({"model": key, "stage": stage, **summarise(lt)})
        e = summarise(lat_e2e)
        i = summarise(lat_inf)
        f = summarise(lat_feat)
        share = 100 * f["p50"] / e["p50"] if e["p50"] > 0 else float("nan")
        print(f"{key:<9} e2e p50={e['p50']:8.3f} p95={e['p95']:8.3f} "
              f"p99={e['p99']:8.3f} p99.9={e['p99.9']:8.3f} ms | "
              f"inf p50={i['p50']:7.3f} | marshal {share:4.1f}% of p50")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "raw" / f"latency_{args.layer}.csv", index=False)

    # ---- 3. the budget sweep: where does each architecture cross? -----------
    e2e = df[df.stage == "end_to_end"].set_index("model")
    cross = []
    for m, r in e2e.iterrows():
        rec = {"model": m, "p50": r.p50, "p95": r.p95, "p99": r.p99, "p99.9": r["p99.9"]}
        for b in BUDGET_SWEEP_MS:
            rec[f"conforms_p99_at_{b}ms"] = bool(r.p99 <= b)
        passing = [b for b in BUDGET_SWEEP_MS if r.p99 <= b]
        rec["min_conforming_budget_ms"] = min(passing) if passing else None
        cross.append(rec)
    cdf = pd.DataFrame(cross)
    cdf.to_csv(OUT / "processed" / f"budget_sweep_{args.layer}.csv", index=False)

    print(f"\n=== p99 CONFORMANCE vs SWEPT BUDGET ({args.layer}, emulated) ===")
    hdr = "".join(f"{b:>7}" for b in BUDGET_SWEEP_MS)
    print(f"{'model':<14}{'p99 ms':>9}  {hdr}")
    for _, r in cdf.iterrows():
        marks = "".join(f"{'  ok  ' if r[f'conforms_p99_at_{b}ms'] else '  --  '}"
                        for b in BUDGET_SWEEP_MS)
        print(f"{r.model:<14}{r.p99:>9.3f}  {marks}")
    print("\nbudget (ms):   " + "".join(f"{b:>7}" for b in BUDGET_SWEEP_MS))
    print("\nThe verdict column an author picks decides the paper's conclusion. "
          "That is why it is swept rather than asserted.")

    (OUT / "statistics" / f"env_{args.layer}.json").write_text(
        json.dumps({**env, "budget_sweep_ms": BUDGET_SWEEP_MS,
                    "floor": fs}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
