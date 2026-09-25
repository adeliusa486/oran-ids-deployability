#!/usr/bin/env python3
"""EXP-058 (reference part): the third corpus D_C on its own.

D_C is the flow-level part of the DLTeamTUC 5G datasets (Nugraha et al., IEEE
CSR 2025): NFStream records from an Open5GS core in Docker, three capture
files, each with one attack (SYN flood, ICMP flood, PFCP session deletion).

This script gives the references that the transfer runs are read against:

  1. label audit, as EXP-057 did for 5G-NIDD: share of flows whose record also
     occurs with the opposite label, and the in-sample balanced-accuracy ceiling
     of the best lookup on distinct records, in the shared 18 columns and in the
     native NFStream fields (identifiers, addresses, ports, timestamps removed);
  2. in-target balanced accuracy of the eight models of the paper:
       random         stratified 70/30 split, 5 seeds
       leave-one-file each capture file held out in turn; its attack type is
                      then absent from training (an unseen-attack test)

Every read of D_C is logged like D_B.

Usage:  python experiments/run_third_corpus_reference.py
"""
from __future__ import annotations

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
from sklearn.model_selection import train_test_split  # noqa: E402

from oran_ids.data import D_C_FILES, RAW_DC, _log_target_access, load_target_d_c  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT / "results" / "EXP-058" / "reference"
MODEL_SEED = 11
NATIVE_DROP_PREFIX = ("src_ip", "dst_ip", "src_mac", "dst_mac", "src_oui", "dst_oui",
                      "src_port", "dst_port", "vlan_id", "tunnel_id", "id",
                      "expiration_id", "label")


def log(msg):
    print(msg, flush=True)


def native_frame() -> pd.DataFrame:
    _log_target_access("EXP-058 reference: native NFStream fields of D_C")
    frames = [pd.read_csv(ROOT / RAW_DC / n, low_memory=False) for n in D_C_FILES]
    df = pd.concat(frames, ignore_index=True)
    keep = [c for c in df.columns
            if c not in NATIVE_DROP_PREFIX and not c.endswith(("_first_seen_ms", "_last_seen_ms"))
            and pd.api.types.is_numeric_dtype(df[c])]
    X = df[keep].astype(np.float64).fillna(0.0)
    return X[[c for c in X.columns if X[c].nunique() > 1]]


def ceiling(X: pd.DataFrame, y: np.ndarray, name: str) -> dict:
    k = pd.util.hash_pandas_object(X.round(9), index=False).to_numpy()
    d = pd.DataFrame(dict(k=k, y=y))
    g = d.groupby("k").y.agg(n1="sum", n="size")
    g["n0"] = g.n - g.n1
    n1, n0 = int(y.sum()), int((1 - y).sum())
    pred = (g.n1 / n1 > g.n0 / n0).astype(int)
    tpr = float((pred * g.n1).sum() / n1)
    tnr = float(((1 - pred) * g.n0).sum() / n0)
    mixed = g[(g.n1 > 0) & (g.n0 > 0)]
    inm = d.k.isin(mixed.index).to_numpy()
    return dict(feature_space=name, n_features=int(X.shape[1]), n_flows=int(len(y)),
                n_distinct=int(len(g)), share_in_conflicting=float(inm.mean()),
                attack_share_in_conflicting=float(inm[y == 1].mean()),
                ba_ceiling=(tpr + tnr) / 2)


def evaluate(fset, proto, split, X, y, tr, te, cat):
    rows = []
    for m in LADDER:
        model = fit_model(m.key, X.iloc[tr], y[tr], MODEL_SEED)
        s = predict_scores(model, X.iloc[te])
        met = detection_metrics(y[te], s, 0.5)
        pred = (s >= 0.5).astype(int)
        cte = cat[te]
        det = {f"det_{c}": float(pred[cte == c].mean() if c not in ("benign", "background")
                                 else 1 - pred[cte == c].mean()) for c in np.unique(cte)}
        rows.append(dict(feature_set=fset, protocol=proto, split=split, model=m.key,
                         n_train=int(len(tr)), n_test=int(len(te)),
                         test_prevalence=float(y[te].mean()), **met, **det))
    return rows


def main() -> int:
    t0 = time.time()
    for d in ("raw", "processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    c = load_target_d_c(reason="EXP-058 reference (D_C trained on as SOURCE)")
    y, cat, files = c.y, np.asarray(c.category), np.asarray(c.groups)
    Xs = c.X.reset_index(drop=True)
    Xn = native_frame().reset_index(drop=True)
    if len(Xn) != len(Xs):
        raise AssertionError("native and shared frames do not align")
    Xn.columns = [f"n_{i:02d}" for i in range(Xn.shape[1])]
    C = pd.DataFrame([ceiling(Xs, y, "shared18"), ceiling(Xn, y, "native")])
    C.to_csv(OUT / "processed/ceilings.csv", index=False)
    log(C.to_string(index=False, float_format=lambda v: "%.4f" % v))

    rows = []
    idx = np.arange(len(y))
    for fset, X in (("shared18", Xs), ("native", Xn)):
        for s in range(5):
            tr, te = train_test_split(idx, test_size=0.30, stratify=y, random_state=101 + s)
            rows += evaluate(fset, "random", f"seed{101 + s}", X, y, tr, te, cat)
        for f in np.unique(files):
            te = idx[files == f]
            tr = idx[files != f]
            rows += evaluate(fset, "leave_one_file", f, X, y, tr, te, cat)
        log(f"  {fset} done ({time.time() - t0:.0f}s)")
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "raw/runs.csv", index=False)
    S = (R.groupby(["feature_set", "protocol", "model"])
         .agg(ba=("balanced_accuracy", "mean"), auc=("roc_auc", "mean"),
              fpr=("fpr", "mean"), recall=("recall", "mean"), n=("balanced_accuracy", "size"))
         .reset_index())
    S.to_csv(OUT / "processed/summary.csv", index=False)
    log(S.to_string(index=False, float_format=lambda v: "%.3f" % v))
    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-058 reference", corpus=c.summary(),
        native_features=int(Xn.shape[1]), native_dropped=list(NATIVE_DROP_PREFIX)
        + ["*_first_seen_ms", "*_last_seen_ms"], model_seed=MODEL_SEED,
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2, default=str), encoding="utf-8")
    log(f"wrote {OUT} ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
