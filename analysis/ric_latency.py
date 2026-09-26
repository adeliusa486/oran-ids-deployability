#!/usr/bin/env python3
"""EXP-061: summarise the FlexRIC timing runs (scripts/ric/05_run_exp061.sh).

Input   results/EXP-061/raw/ric_<model>_p<period>.csv, one row per KPM indication,
        header comment with the warm-up count and the drop counter.
Output  results/EXP-061/processed/ric_latency.csv   quantiles with 95% intervals
        results/EXP-061/statistics/summary.json      counts, drops, queue depth

Terms (milliseconds): t_ind (E2 node builds the indication -> xApp callback),
t_q (queueing in the xApp), t_feat/t_inf (first UE; *_all summed over the UEs of
the indication), t_act (RC control -> CONTROL-ACK round trip).
  e2e_one = t_ind + t_q + t_feat1 + t_inf1 + t_act   one UE's decision and action
  e2e_all = t_ind + t_q + t_feat  + t_inf  + t_act   every UE of the indication
Indications that reported no UE carry no decision and are counted, not timed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.run_latency_v2 import QUANTS, quantile_ci  # noqa: E402

EXP = ROOT / "results" / "EXP-061"


def read_run(path: Path):
    head = path.read_text().splitlines()[0]
    meta = {k: float(v) for k, v in re.findall(r"(\w+)=([-\d.e+]+)", head)}
    df = pd.read_csv(path, comment="#")
    return meta, df[df.seq >= meta["warmup"]].reset_index(drop=True)


def main() -> int:
    rows, summ = [], {}
    for f in sorted((EXP / "raw").glob("ric_*_p*.csv")):
        model, period = re.match(r"ric_(\w+?)_p(\d+)\.csv", f.name).groups()
        meta, d = read_run(f)
        dec = d[d.n_ue > 0]
        terms = dict(
            t_ind=dec.t_ind_ms, t_q=dec.t_q_ms, t_feat=dec.t_feat1_ms,
            t_inf=dec.t_inf1_ms, t_act=dec.t_act_ms,
            t_feat_all=dec.t_feat_ms, t_inf_all=dec.t_inf_ms,
            e2e_one=dec.t_ind_ms + dec.t_q_ms + dec.t_feat1_ms + dec.t_inf1_ms + dec.t_act_ms,
            e2e_all=dec.t_ind_ms + dec.t_q_ms + dec.t_feat_ms + dec.t_inf_ms + dec.t_act_ms)
        for term, x in terms.items():
            x = x.to_numpy(float)
            rec = dict(model=model, period_ms=int(period), term=term, n=len(x),
                       mean=float(x.mean()), max=float(x.max()))
            for q in QUANTS:
                est, lo, hi = quantile_ci(x, q)
                k = str(q).replace(".", "_")
                rec[f"p{k}"], rec[f"p{k}_lo"], rec[f"p{k}_hi"] = est, lo, hi
            rows.append(rec)
        summ[f"{model}_p{period}"] = dict(
            indications_recorded=int(len(d)), with_ue=int(len(dec)),
            without_ue=int((d.n_ue == 0).sum()), ues_mean=float(dec.n_ue.mean()),
            ues_max=int(dec.n_ue.max()), queue_max=int(d.qlen.max()),
            seen=int(meta["seen"]), dropped=int(meta["dropped"]),
            wall_s=meta["wall_s"], verify_max_abs=meta["verify_max_abs"],
            decisions=int(dec.n_ue.sum()))
    for d in ("processed", "statistics"):
        (EXP / d).mkdir(parents=True, exist_ok=True)
    R = pd.DataFrame(rows)
    R.to_csv(EXP / "processed/ric_latency.csv", index=False)
    (EXP / "statistics/summary.json").write_text(json.dumps(summ, indent=2))
    show = R[R.term.isin(["t_ind", "t_q", "t_inf", "t_act", "e2e_one", "e2e_all"])]
    print(show.pivot_table(index=["period_ms", "model"], columns="term",
                           values="p99").round(3).to_string())
    print(json.dumps(summ, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
