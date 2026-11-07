#!/usr/bin/env python3
"""EXP-073: attack-category coverage of the D_A flow splits (R1.11, R2.4).

Flow splits hold out whole source addresses (318 groups, 94.63% attack flows).
If an attack category came from one or a few attacker addresses, a split could
remove it from training. This script reports

  * how many of the 318 source addresses send attack flows, per category, and
    how concentrated each category's flows are on its largest attackers;
  * for each of the 20 transfer splits (the same seeded 300,000-flow sample and
    group-disjoint split as EXP-064), the flows and attacker addresses of every
    category on each side, and whether every category is present in training.

Usage:  python analysis/flow_split_coverage.py
Output: results/EXP-073/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.data import load_network_shared  # noqa: E402
from oran_ids.splits import group_disjoint_split  # noqa: E402
from experiments.run_transfer import subsample  # noqa: E402

OUT = ROOT / "results/EXP-073"
SEEDS = list(range(101, 121))
N_SUB = 300_000


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    c = load_network_shared()
    y, g, cat = np.asarray(c.y), np.asarray(c.groups).astype(str), np.asarray(c.category)
    df = pd.DataFrame({"y": y, "g": g, "cat": cat})

    per_addr = df.groupby("g").agg(flows=("y", "size"), attack_share=("y", "mean"))
    hosts = dict(addresses=int(len(per_addr)),
                 attacker_addresses=int((per_addr.attack_share > 0).sum()),
                 attack_only=int((per_addr.attack_share == 1).sum()),
                 mixed=int(((per_addr.attack_share > 0) & (per_addr.attack_share < 1)).sum()),
                 benign_only=int((per_addr.attack_share == 0).sum()),
                 largest_address_flow_share=float(per_addr.flows.max() / len(df)))

    rows = []
    for k, d in df[df.y == 1].groupby("cat"):
        vc = d["g"].value_counts()
        rows.append(dict(category=k, flows=int(len(d)), attacker_addresses=int(len(vc)),
                         top1_share=float(vc.iloc[0] / len(d)),
                         top3_share=float(vc.iloc[:3].sum() / len(d)),
                         addresses_for_90pct=int(np.searchsorted(np.cumsum(vc.to_numpy()) / len(d), 0.9) + 1)))
    per_cat = pd.DataFrame(rows).sort_values("category")
    per_cat.to_csv(OUT / "attackers_per_category.csv", index=False)

    split_rows = []
    for seed in SEEDS:
        X, ys, cs, gs = subsample(c.X, y, cat, g, N_SUB, seed)
        sp = group_disjoint_split(ys, gs, seed=seed, n_folds=1)[0]
        sp.check_disjoint(gs)
        tr, te = sp.train_idx, sp.test_idx
        for k in sorted(set(cs)):
            mtr, mte = cs[tr] == k, cs[te] == k
            split_rows.append(dict(
                split_seed=seed, category=k,
                train_flows=int(mtr.sum()), test_flows=int(mte.sum()),
                train_addresses=int(len(np.unique(gs[tr][mtr]))),
                test_addresses=int(len(np.unique(gs[te][mte]))),
                train_share=float(mtr.sum() / max(mtr.sum() + mte.sum(), 1)),
                n_train_groups=sp.n_train_groups, n_test_groups=sp.n_test_groups,
                test_flow_frac=float(len(te) / (len(tr) + len(te)))))
    splits = pd.DataFrame(split_rows)
    splits.to_csv(OUT / "coverage_per_split.csv", index=False)

    att = splits[splits.category != "benign"]
    summary = dict(
        hosts=hosts,
        categories=per_cat.to_dict(orient="records"),
        splits=dict(
            n_splits=len(SEEDS),
            every_category_in_training_every_split=bool((att.train_flows > 0).all()),
            every_category_in_test_every_split=bool((att.test_flows > 0).all()),
            splits_missing_a_category_in_test=int(att.groupby("split_seed")
                                                  .apply(lambda d: (d.test_flows == 0).any()).sum()),
            min_train_share_by_category=att.groupby("category").train_share.min().round(3).to_dict(),
            min_train_addresses_by_category=att.groupby("category").train_addresses.min().to_dict(),
            test_groups_range=[int(splits.n_test_groups.min()), int(splits.n_test_groups.max())],
            train_groups_range=[int(splits.n_train_groups.min()), int(splits.n_train_groups.max())],
            test_flow_frac_range=[float(splits.test_flow_frac.min()), float(splits.test_flow_frac.max())],
            group_ratio_mean=float((splits.groupby("split_seed").n_test_groups.first()
                                    / splits.groupby("split_seed").n_train_groups.first()).mean()),
        ))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
