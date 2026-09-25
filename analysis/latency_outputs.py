#!/usr/bin/env python3
"""Latency macros and table for the revised manuscript (EXP-043).

Kept apart from make_numbers.py and make_tables_v2.py so that the timing
outputs, which must come from a run on a quiet machine, are handled in one
place. Both generators call ``numbers()`` and ``table()`` when
results/EXP-043 exists and skip them otherwise.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
L_DIR = ROOT / "results" / "EXP-043"
MODELS = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp"]
NAME = {"logreg": "LR", "tree": "DT", "rf": "RF", "xgboost": "XGB", "hgb": "HGB",
        "mlp": "MLP"}


def available() -> bool:
    return (L_DIR / "raw/latency_stages.csv").exists()


def _stages() -> pd.DataFrame:
    return pd.read_csv(L_DIR / "raw/latency_stages.csv")


def _get(S, layer, model, stage, col):
    r = S[(S.layer == layer) & (S.model == model) & (S.stage == stage)]
    return float(r[col].iloc[0]) if len(r) else float("nan")


def numbers(put, fmt_ms="{:.2f}") -> None:
    S = _stages()
    src = "EXP-043 latency_stages"
    put("LatFloorPnn", _get(S, "platform", "FLOOR", "no_op", "p99"), "{:.3f}", src)
    put("LatAggPnn", _get(S, "radio", "-", "window_aggregation", "p99"), "{:.3f}")
    put("LatMapPfifty", _get(S, "network", "-", "shared_space_mapping", "p50"), "{:.1f}")
    put("LatLRdfPfifty", _get(S, "radio", "logreg", "sk_dataframe", "p50"), fmt_ms)
    put("LatLRarrPfifty", _get(S, "radio", "logreg", "sk_array", "p50"), fmt_ms)
    put("LatRFthreadsPfifty", _get(S, "radio", "rf", "sk_array_all_threads", "p50"), "{:.0f}")
    put("LatRFarrPfifty", _get(S, "radio", "rf", "sk_array", "p50"), "{:.1f}")
    put("LatRFonnxPfifty", _get(S, "radio", "rf", "onnx", "p50"), "{:.3f}")
    onnx = S[(S.layer == "radio") & (S.stage == "onnx")]
    put("LatOnnxPnnMin", onnx.p99.min(), "{:.3f}")
    put("LatOnnxPnnMax", onnx.p99.max(), "{:.3f}")
    arr = S[(S.layer == "radio") & (S.stage == "sk_array")]
    put("LatArrPnnMin", arr.p99.min(), "{:.2f}")
    put("LatArrPnnMax", arr.p99.max(), "{:.1f}")
    e2e = S[(S.layer == "radio") & (S.stage == "e2e_aggregate_plus_onnx")]
    put("LatEtoEPnnHiMax", e2e.p99_hi.max(), "{:.2f}")
    put("LatEtoEPnnnHiMax", e2e.p99_9_hi.max(), "{:.2f}")
    put("LatNOnnx", str(len(e2e)))
    net = S[(S.layer == "network") & (S.stage == "onnx")]
    put("LatNetOnnxPnnMax", net.p99.max(), "{:.3f}")
    ver = pd.read_csv(L_DIR / "processed/onnx_verification.csv")
    put("LatOnnxAgreeMin", float(ver[ver.ok].decision_agreement.min()), "{:.4f}")
    put("LatOnnxOK", str(int(ver.ok.sum())))
    put("LatOnnxN", str(len(ver)))
    ex = L_DIR / "processed/extraction_real_captures.csv"
    if ex.exists():
        E = pd.read_csv(ex)
        put("LatExtrMin", E.ms_per_flow.min(), "{:.2f}", "EXP-043 part B")
        put("LatExtrMax", E.ms_per_flow.max(), "{:.2f}")
        put("LatExtrSpeedMin", E.speedup_vs_ref.min(), "{:.1f}")
        put("LatExtrSpeedMax", E.speedup_vs_ref.max(), "{:.1f}")
        put("LatExtrRefMin", E.ref_ms_per_flow.min(), "{:.2f}")
        put("LatExtrRefMax", E.ref_ms_per_flow.max(), "{:.2f}")
        eq = E.dropna(subset=["eq_n_keys_both"])
        if len(eq):
            # Mismatches on shared keys must be zero for the sentence the paper
            # makes; refuse to emit the macros otherwise.
            if (eq.eq_n_pkt_mismatch.sum() or eq.eq_n_byte_mismatch.sum()
                    or eq.eq_n_keys_fast_only.sum()):
                raise ValueError("fast and reference exporters disagree on shared flows")
            put("LatEqCaptures", str(len(eq)), source="EXP-043 part B equivalence")
            put("LatEqKeys", f"{int(eq.eq_n_keys_both.sum()):,}")
            put("LatRefOnlyMin", str(int(eq.eq_n_keys_ref_only.min())))
            put("LatRefOnlyMax", str(int(eq.eq_n_keys_ref_only.max())))
        line = (r"flow features: {} to {}\,ms per flow (vectorized, real captures)"
                r" against {}\,ms p99 inference (ONNX Runtime)").format(
            f"{E.ms_per_flow.min():.2f}", f"{E.ms_per_flow.max():.2f}",
            f"{net.p99.max():.3f}")
    else:
        line = r"inference {}\,ms p99 (ONNX Runtime)".format(f"{net.p99.max():.2f}")
    put("LatFigLine", line)


def table(write, BS="\\\\") -> None:
    S = _stages()
    rows = []
    for m in MODELS:
        g = lambda st, c, layer="radio": _get(S, layer, m, st, c)
        onnx_p50 = g("onnx", "p50")
        onnx = (f"{g('onnx', 'p50'):.3f} & {g('onnx', 'p99'):.3f}"
                if onnx_p50 == onnx_p50 else "-- & --")
        e2e = g("e2e_aggregate_plus_onnx", "p99_hi")
        e2e_s = f"{e2e:.2f}" if e2e == e2e else "--"
        net = g("onnx", "p99", "network")
        net_s = f"{net:.3f}" if net == net else "--"
        rows.append(f"{NAME[m]} & {g('sk_dataframe', 'p50'):.2f} & "
                    f"{g('sk_dataframe', 'p99'):.2f} & {g('sk_array', 'p50'):.2f} & "
                    f"{g('sk_array', 'p99'):.2f} & {onnx} & {e2e_s} & "
                    f"{g('sk_array', 'p99', 'network'):.2f} & {net_s} {BS}")
    write("rev_latency", rows, "EXP-043 latency_stages", "lccccccccc",
          r"& \multicolumn{2}{c}{sklearn, DataFrame} & \multicolumn{2}{c}{sklearn, array} & "
          r"\multicolumn{2}{c}{ONNX Runtime} & Radio path & \multicolumn{2}{c}{Flow layer, $p_{99}$} "
          + BS + "\n"
          r"Model & $p_{50}$ & $p_{99}$ & $p_{50}$ & $p_{99}$ & $p_{50}$ & $p_{99}$ & "
          r"$\overline{p}_{99}$ & array & ONNX " + BS)
