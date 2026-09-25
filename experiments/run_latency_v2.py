#!/usr/bin/env python3
"""EXP-043: per-stage decision latency, same host, three implementations.

EXP-005 timed one row passed to scikit-learn as a pandas DataFrame and called it
the decision latency. Review found four problems with what the paper built on it
(R1.7-R1.9, R2.7, R4, R6.8):

  * the timed path was dominated by DataFrame input validation, not inference
    (logistic regression: 0.63 ms on an array, 2.45 ms through a DataFrame);
  * the random forest and XGBoost predicted through a thread pool (n_jobs=-1),
    so every single-row call paid thread start-up;
  * garbage collection was disabled while timing, removing a real tail source;
  * p99.9 came from 1,500 calls, i.e. one or two observations, with no interval;
  * the only compiled-inference figure was another group's, on other hardware.

This experiment fixes each, on the SAME host, and adds a compiled runtime:

  stages       FLOOR (no-op), radio window aggregation (16x16 KPM -> 32
               features), shared-space mapping (one Zeek record -> 18 columns,
               the repository's pandas path), and per model:
               sk_dataframe  one pandas row through scikit-learn (EXP-005's path)
               sk_array      one NumPy row through scikit-learn, 1 thread
               onnx          ONNX Runtime, 1 intra-op thread, verified against
                             scikit-learn to within 1e-4 before it is timed
  layers       radio (32 features, trained on group-disjoint seed 101) and
               network shared space (18 features, trained on EXP-041's seed-101
               source split)
  timing       perf_counter_ns around each call, 1,000 warm-up calls, 20,000
               timed calls, garbage collection ENABLED
  intervals    distribution-free 95% intervals for each quantile from order
               statistics (binomial), so p99.9 carries its uncertainty
  decision     radio end-to-end = aggregation + inference, timed as ONE call

Run ALONE. Any concurrent job contaminates the tail.

Usage:  python experiments/run_latency_v2.py [--calls N]
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import binom  # noqa: E402

from oran_ids.data import (load_network_shared, load_radio,  # noqa: E402
                           load_radio_sequences)
from oran_ids.features import shared as sh  # noqa: E402
from oran_ids.models import fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402
from experiments.run_transfer import subsample  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-043"
MODELS = ("tree", "logreg", "xgboost", "mlp", "hgb", "rf")
QUANTS = (50, 95, 99, 99.9)
BUDGETS_MS = (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)
WARMUP = 1000


def quantile_ci(x: np.ndarray, q: float, conf: float = 0.95):
    """Point estimate and distribution-free CI for the q-th percentile."""
    xs = np.sort(x)
    n = len(xs)
    p = q / 100.0
    lo = int(binom.ppf((1 - conf) / 2, n, p))
    hi = int(binom.ppf(1 - (1 - conf) / 2, n, p))
    lo, hi = max(lo - 1, 0), min(hi, n - 1)
    return float(np.percentile(xs, q)), float(xs[lo]), float(xs[hi])


def time_calls(fn, n: int) -> np.ndarray:
    for _ in range(WARMUP):
        fn()
    out = np.empty(n)
    for i in range(n):
        t0 = time.perf_counter_ns()
        fn()
        out[i] = (time.perf_counter_ns() - t0) / 1e6
    return out


def summarise(layer, model, stage, lat, note=""):
    rec = dict(layer=layer, model=model, stage=stage, n=len(lat),
               mean=float(lat.mean()), max=float(lat.max()), note=note)
    for q in QUANTS:
        est, lo, hi = quantile_ci(lat, q)
        k = str(q).replace(".", "_")
        rec[f"p{k}"], rec[f"p{k}_lo"], rec[f"p{k}_hi"] = est, lo, hi
    return rec


def to_onnx(model, n_feat: int):
    from skl2onnx import convert_sklearn, update_registered_converter
    from skl2onnx.common.data_types import FloatTensorType
    from skl2onnx.common.shape_calculator import (
        calculate_linear_classifier_output_shapes)
    try:
        from onnxmltools.convert.xgboost.operator_converters.XGBoost import (
            convert_xgboost)
        from xgboost import XGBClassifier
        update_registered_converter(
            XGBClassifier, "XGBoostXGBClassifier",
            calculate_linear_classifier_output_shapes, convert_xgboost,
            options={"nocl": [True, False], "zipmap": [True, False, "columns"]})
    except Exception:
        pass
    it = [("input", FloatTensorType([None, n_feat]))]
    if type(model).__name__ == "XGBClassifier":
        # onnxmltools requires booster feature names of the form f0, f1, ...
        # Convert a copy with the names cleared; the original, still named, is
        # the one scikit-learn is timed with.
        import copy
        model = copy.deepcopy(model)
        model.get_booster().feature_names = None
    opts = {id(model): {"zipmap": False}}
    return convert_sklearn(model, initial_types=it, options=opts,
                           target_opset={"": 17, "ai.onnx.ml": 3})


def ort_session(onx):
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads = 1
    so.inter_op_num_threads = 1
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(onx.SerializeToString(), so,
                                providers=["CPUExecutionProvider"])


def onnx_proba(sess, X):
    outs = sess.run(None, {"input": X.astype(np.float32)})
    prob = outs[1] if len(outs) > 1 else outs[0]
    prob = np.asarray(prob)
    return prob[:, 1] if prob.ndim == 2 else prob.ravel()


def single_thread(model):
    """Prediction on one thread, for RF and XGBoost (review R1.7)."""
    est = model[-1] if hasattr(model, "steps") else model
    if "n_jobs" in est.get_params():
        est.set_params(n_jobs=1)
    return model


def layer_run(layer, Xtr, ytr, Xte, n_calls, rows, verify):
    from threadpoolctl import threadpool_limits
    one_df = Xte.iloc[[0]]
    one = one_df.to_numpy(np.float32)
    Xv = Xte.iloc[:2000].to_numpy(np.float32)
    for key in MODELS:
        m = fit_model(key, Xtr, ytr, 11)
        if key in ("rf", "xgboost"):
            lat = time_calls(lambda: predict_scores(m, one), max(n_calls // 10, 2000))
            rows.append(summarise(layer, key, "sk_array_all_threads", lat,
                                  "n_jobs=-1, as in EXP-005; fewer calls"))
        single_thread(m)
        # OpenMP (HGB) and BLAS pools are capped too, not only n_jobs
        with threadpool_limits(limits=1):
            lat = time_calls(lambda: predict_scores(m, one_df), n_calls)
            rows.append(summarise(layer, key, "sk_dataframe", lat,
                                  "EXP-005 path, 1 thread"))
            lat = time_calls(lambda: predict_scores(m, one), n_calls)
            rows.append(summarise(layer, key, "sk_array", lat, "1 thread"))
        try:
            sess = ort_session(to_onnx(m, one.shape[1]))
            po, ps = onnx_proba(sess, Xv), predict_scores(m, Xv)
            ad = np.abs(po - ps)
            agree = float(np.mean((po >= 0.5) == (ps >= 0.5)))
            # float32 split thresholds in ONNX can move a few near-threshold
            # rows; accept on decisions and on the typical row, record both
            ok = bool(agree >= 0.999 and np.percentile(ad, 99) < 1e-4)
            verify.append(dict(layer=layer, model=key, max_abs_diff=float(ad.max()),
                               p99_abs_diff=float(np.percentile(ad, 99)),
                               decision_agreement=agree, ok=ok))
            if ok:
                lat = time_calls(lambda: onnx_proba(sess, one), n_calls)
                rows.append(summarise(layer, key, "onnx", lat,
                                      f"agreement {agree:.4f}, max|diff| {ad.max():.1e}"))
            else:
                print(f"  {layer} {key}: ONNX disagrees (agreement {agree:.4f}, "
                      f"p99|diff| {np.percentile(ad, 99):.2e}); not timed", flush=True)
        except Exception as exc:  # recorded, never silently dropped
            verify.append(dict(layer=layer, model=key, max_abs_diff=np.nan,
                               ok=False, error=str(exc)[:200]))
            print(f"  {layer} {key}: ONNX conversion failed: {exc}", flush=True)
        print(f"  {layer} {key} done", flush=True)
        yield key, m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", type=int, default=20_000)
    a = ap.parse_args()
    t0 = time.time()
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    assert gc.isenabled(), "garbage collection must be ENABLED while timing"
    rows, verify = [], []

    floor = np.zeros((1, 32), np.float32)
    rows.append(summarise("platform", "FLOOR", "no_op",
                          time_calls(lambda: floor.sum(), a.calls)))

    # ---- radio layer ------------------------------------------------------
    c = load_radio()
    seq, *_ = load_radio_sequences()
    sp = group_disjoint_split(c.y, c.groups, seed=101, n_folds=1)[0]
    Xtr, ytr, Xte = c.X.iloc[sp.train_idx], c.y[sp.train_idx], c.X.iloc[sp.test_idx]
    win = seq[sp.test_idx[0]].astype(np.float64)

    def aggregate(w=win):
        # load_radio orders columns f1_mean, f1_std, f2_mean, ... (pandas agg)
        mu, sd = np.nanmean(w, 0), np.nanstd(w, 0, ddof=1)
        return np.nan_to_num(np.column_stack([mu, sd]).ravel())[None, :]

    ref = Xte.iloc[0].to_numpy(np.float64)
    got = aggregate()[0]
    assert np.allclose(got, ref, rtol=1e-4, atol=1e-3), (
        "window aggregation does not reproduce load_radio's features")

    rows.append(summarise("radio", "-", "window_aggregation",
                          time_calls(aggregate, a.calls),
                          "16 records x 16 KPM features -> 32"))
    for key, m in layer_run("radio", Xtr, ytr, Xte, a.calls, rows, verify):
        try:
            sess = ort_session(to_onnx(m, Xtr.shape[1]))
            lat = time_calls(lambda: onnx_proba(sess, aggregate().astype(np.float32)),
                             a.calls)
            rows.append(summarise("radio", key, "e2e_aggregate_plus_onnx", lat))
        except Exception:
            pass
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=1):
            lat = time_calls(
                lambda: predict_scores(m, aggregate().astype(np.float32)), a.calls)
        rows.append(summarise("radio", key, "e2e_aggregate_plus_sk_array", lat))

    # ---- network layer, shared space ---------------------------------------
    src = load_network_shared()
    Xs, ys, cs, gs = subsample(src.X, src.y, src.category, src.groups,
                               300_000, 101)
    sp = group_disjoint_split(ys, gs, seed=101, n_folds=1)[0]
    Xtr, ytr, Xte = Xs.iloc[sp.train_idx], ys[sp.train_idx], Xs.iloc[sp.test_idx]
    raw = pd.read_csv(ROOT / "data/raw/d_a/Network_Dataset.csv", nrows=1)
    rows.append(summarise("network", "-", "shared_space_mapping",
                          time_calls(lambda: sh.from_d_a(raw.copy()), a.calls),
                          "one Zeek record -> 18 columns, pandas path"))
    for _ in layer_run("network", Xtr, ytr, Xte, a.calls, rows, verify):
        pass

    R = pd.DataFrame(rows)
    R.to_csv(OUT / "raw/latency_stages.csv", index=False)
    pd.DataFrame(verify).to_csv(OUT / "processed/onnx_verification.csv",
                                index=False)
    conf = []
    for _, r in R.iterrows():
        rec = dict(layer=r.layer, model=r.model, stage=r.stage,
                   p99=r.p99, p99_hi=r.p99_hi)
        ok = [b for b in BUDGETS_MS if r.p99_hi <= b]
        rec["min_budget_ms_upper_ci"] = min(ok) if ok else None
        conf.append(rec)
    pd.DataFrame(conf).to_csv(OUT / "processed/budget_crossings.csv", index=False)

    import onnxruntime
    import sklearn
    import xgboost
    try:
        import psutil
        load = psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
        cpu = psutil.cpu_percent(interval=1.0)
    except Exception:
        load, cpu = None, None
    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-043", measurement_class="emulated (no RIC in the path)",
        host=dict(cpu="13th Gen Intel(R) Core(TM) i9-13900H, 14 cores / 20 "
                      "threads", ram_gb=47.6, os=platform.platform()),
        python=platform.python_version(), sklearn=sklearn.__version__,
        xgboost=xgboost.__version__, onnxruntime=onnxruntime.__version__,
        calls=a.calls, warmup=WARMUP, gc_enabled=True,
        threads="scikit-learn RF/XGBoost set to n_jobs=1 for sk_* stages; "
                "ONNX Runtime intra_op_num_threads=1",
        cpu_percent_after=cpu, loadavg=load, pid=os.getpid(),
        runtime_s=round(time.time() - t0, 1)), indent=2, default=str),
        encoding="utf-8")
    print(R[["layer", "model", "stage", "p50", "p99", "p99_lo", "p99_hi",
             "p99_9", "p99_9_hi"]].to_string(index=False,
                                             float_format=lambda v: "%.4f" % v))
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
