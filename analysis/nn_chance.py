#!/usr/bin/env python3
"""Chance levels for the nearest-neighbour session probe (forensic writing audit M-26).

Under a random split, 68% of radio test windows have their nearest training
window in the same capture session. That share needs a reference. Two are
written here, both from the session sizes of the windowed radio layer alone:

  any       the nearest training window drawn at random from the whole training
            set: sum over sessions of (n_s / N)^2
  category  drawn at random among training windows of the same attack category
            (a lookup that knows the category but nothing else):
            sum over sessions of (n_s / N) * (n_s / N_c(s))

Both assume the training set keeps the session proportions of the corpus, which
a random split does in expectation.

Usage:  python analysis/nn_chance.py   -> results/EXP-042/processed/nn_chance.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from oran_ids.data import load_radio  # noqa: E402

OUT = ROOT / "results" / "EXP-042" / "processed" / "nn_chance.json"


def main() -> int:
    c = load_radio()
    d = pd.DataFrame(dict(session=list(c.groups), category=list(c.category)))
    n = d.groupby("session").size()
    N = int(n.sum())
    cat = d.groupby("session").category.first()
    nc = d.groupby("category").size()
    any_ = float(((n / N) ** 2).sum())
    same_cat = float(sum((n[s] / N) * (n[s] / nc[cat[s]]) for s in n.index))
    rec = dict(sessions=int(len(n)), windows=N, chance_any=any_,
               chance_same_category=same_cat,
               note="expected share of test windows whose nearest training window "
                    "shares their session if that neighbour were random")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(json.dumps(rec, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
