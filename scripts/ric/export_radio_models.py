#!/usr/bin/env python3
"""EXP-061 step 4: export the six radio models for the FlexRIC timing xApp.

Trains exactly the models EXP-043 timed (group-disjoint split seed 101, fit seed
11), converts each with the same converter, checks the export against
scikit-learn with the same acceptance rule, and writes:

  results/EXP-061/models/<key>.onnx      verified exports (git-ignored, regenerable)
  results/EXP-061/models/windows.f32     test windows, N x 16 records x 16 KPM, float32
  results/EXP-061/models/ref_<key>.f32   ONNX Runtime scores on the aggregated
                                         windows, for checking the C xApp
  results/EXP-061/models/meta.json       shapes, verification, feature order

The xApp reproduces the aggregation (per-feature mean and sample standard
deviation, interleaved f1_mean, f1_std, ...) in C and must match ref_<key>.f32.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from experiments.run_latency_v2 import (MODELS, onnx_proba, ort_session,  # noqa: E402
                                        single_thread, to_onnx)
from oran_ids.data import load_radio, load_radio_sequences  # noqa: E402
from oran_ids.models import fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT / "results" / "EXP-061" / "models"


def aggregate(w: np.ndarray) -> np.ndarray:
    mu, sd = np.nanmean(w, 1), np.nanstd(w, 1, ddof=1)
    return np.nan_to_num(np.stack([mu, sd], -1).reshape(len(w), -1))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    c = load_radio()
    seq, *_ = load_radio_sequences()
    sp = group_disjoint_split(c.y, c.groups, seed=101, n_folds=1)[0]
    Xtr, ytr, Xte = c.X.iloc[sp.train_idx], c.y[sp.train_idx], c.X.iloc[sp.test_idx]
    win = seq[sp.test_idx].astype(np.float32)
    agg = aggregate(win.astype(np.float64))
    # One test window (of 589) differs in the two rate features: the sequence
    # array holds 0 where load_radio has a missing first rate, so the mean is
    # over 16 values instead of 15. Timing is unaffected; the count is recorded.
    bad = ~np.isclose(agg, Xte.to_numpy(np.float64), rtol=1e-4, atol=1e-3).all(1)
    assert bad.mean() < 0.01, "aggregation does not reproduce load_radio's features"
    win.tofile(OUT / "windows.f32")
    meta = dict(n_windows=int(win.shape[0]), records=int(win.shape[1]),
                windows_differing_from_load_radio=int(bad.sum()),
                kpm=int(win.shape[2]), n_features=int(agg.shape[1]),
                feature_order=list(Xte.columns), labels_attack=int(c.y[sp.test_idx].sum()),
                models={})
    Xv = agg.astype(np.float32)
    for key in MODELS:
        m = single_thread(fit_model(key, Xtr, ytr, 11))
        onx = to_onnx(m, Xv.shape[1])
        sess = ort_session(onx)
        po, ps = onnx_proba(sess, Xv), predict_scores(m, Xv)
        ad = np.abs(po - ps)
        agree = float(np.mean((po >= 0.5) == (ps >= 0.5)))
        ok = bool(agree >= 0.999 and np.percentile(ad, 99) < 1e-4)
        outs = [o.name for o in sess.get_outputs()]
        meta["models"][key] = dict(ok=ok, decision_agreement=agree,
                                   max_abs_diff=float(ad.max()), outputs=outs,
                                   bytes=len(onx.SerializeToString()))
        if ok:
            (OUT / f"{key}.onnx").write_bytes(onx.SerializeToString())
            po.astype(np.float32).tofile(OUT / f"ref_{key}.f32")
        print(f"{key}: ok={ok} agreement={agree:.4f} max|diff|={ad.max():.1e} "
              f"outputs={outs}", flush=True)
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"windows: {win.shape}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
