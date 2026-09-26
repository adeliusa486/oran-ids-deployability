#!/usr/bin/env python3
"""EXP-063: does the exporter explain the D_A -> D_B gap?

Compares transfer from D_A (Zeek) to D_B exported by Argus (EXP-056, the
published records) with transfer to D_B re-extracted by Zeek (EXP-063), on the
same 10 split seeds, the same source subsamples and the same models, so each
(model, seed) gives a paired difference whose only change is the exporter of the
target. Balanced accuracy at tau = 0.5 comes from the per-capture counts, on all
target flows and without the flood copies ("|c" groups), exactly as the paper's
other D_B results.

Output  results/EXP-063/processed/exporter_control.csv  per model: both exporters,
        paired difference with a t-interval over seeds (all and clean)
        results/EXP-063/statistics/exporter_control.json

Usage:  python analysis/exporter_control.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
NONTRIVIAL = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp"]


def ba_by_seed(path: Path) -> pd.DataFrame:
    c = pd.read_csv(path)
    c = c[(c.domain == "target") & np.isclose(c.tau, 0.5)]
    c["clean"] = ~c.group.astype(str).str.endswith("|c")
    out = []
    for (m, s), g in c.groupby(["model", "split_seed"]):
        for sub, gg in (("all", g), ("clean", g[g.clean])):
            tp, fp, fn, tn = (gg[k].sum() for k in ("tp", "fp", "fn", "tn"))
            tpr = tp / (tp + fn) if tp + fn else np.nan
            tnr = tn / (tn + fp) if tn + fp else np.nan
            out.append(dict(model=m, split_seed=s, subset=sub, ba=(tpr + tnr) / 2,
                            tpr=tpr, fpr=1 - tnr, n=int(tp + fp + fn + tn)))
    return pd.DataFrame(out)


def main() -> int:
    a = ba_by_seed(RES / "EXP-056/a_to_b__shared/raw/tau_counts_by_group.csv")
    z = ba_by_seed(RES / "EXP-063/a_to_bz__shared/raw/tau_counts_by_group.csv")
    m = a.merge(z, on=["model", "split_seed", "subset"], suffixes=("_argus", "_zeek"))
    m = m[m.model.isin(NONTRIVIAL)]
    rows = []
    for (mod, sub), g in m.groupby(["model", "subset"]):
        d = (g.ba_zeek - g.ba_argus).to_numpy()
        n = len(d)
        h = stats.t.ppf(0.975, n - 1) * d.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
        rows.append(dict(model=mod, subset=sub, seeds=n,
                         ba_argus=g.ba_argus.mean(), ba_zeek=g.ba_zeek.mean(),
                         diff=d.mean(), diff_lo=d.mean() - h, diff_hi=d.mean() + h,
                         fpr_argus=g.fpr_argus.mean(), fpr_zeek=g.fpr_zeek.mean(),
                         tpr_argus=g.tpr_argus.mean(), tpr_zeek=g.tpr_zeek.mean()))
    R = pd.DataFrame(rows)
    (RES / "EXP-063/processed").mkdir(parents=True, exist_ok=True)
    (RES / "EXP-063/statistics").mkdir(parents=True, exist_ok=True)
    R.to_csv(RES / "EXP-063/processed/exporter_control.csv", index=False)
    summ = {sub: dict(ba_argus_min=float(g.ba_argus.min()), ba_argus_max=float(g.ba_argus.max()),
                      ba_zeek_min=float(g.ba_zeek.min()), ba_zeek_max=float(g.ba_zeek.max()),
                      diff_min=float(g["diff"].min()), diff_max=float(g["diff"].max()),
                      n_sig_pos=int((g.diff_lo > 0).sum()), n_sig_neg=int((g.diff_hi < 0).sum()))
            for sub, g in R.groupby("subset")}
    (RES / "EXP-063/statistics/exporter_control.json").write_text(json.dumps(summ, indent=2))
    print(R.round(3).to_string(index=False))
    print(json.dumps(summ, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
