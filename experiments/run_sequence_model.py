#!/usr/bin/env python3
"""EXP-050: sequence models over KPM windows, under the leakage protocols.

Review R4 asked for a sequence model (1D-CNN, LSTM or a small transformer) under
the same protocol as the tabular ladder. Earlier drafts of this paper reported a
1D-CNN and an LSTM that never existed (see scripts/check_withdrawn_claims.py).
These two do exist, in this file, and every number they produce is measured.

  data      the SAME 2,808 windows as load_radio(window=True), as raw
            16-step x 16-feature sequences (load_radio_sequences), asserted
            equal in labels, categories and sessions
  models    GRU      1 layer, hidden 32, last state -> linear
            CNN1D    conv(32,k3)-ReLU-conv(32,k3)-ReLU-global average pool-linear
  training  z-score per feature on TRAIN windows only; BCE with pos_weight =
            n_neg/n_pos, the same balanced policy as the ladder (D-021); Adam
            1e-3, batch 64, <=100 epochs, early stopping (patience 10) on a
            10% validation split drawn from the training windows
  protocols random, group_disjoint, stratified_group; split seeds 101-120 and
            model seeds 11, 22, exactly as EXP-042, so the splits are identical

Environment: CPU PyTorch in an isolated venv, because the global torch install on
this host is broken (two dist-infos, no __init__.py). Recreate with
  python -m venv oranseq
  oranseq/Scripts/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
  oranseq/Scripts/python -m pip install numpy==2.3.5 pandas==2.3.3 scikit-learn==1.8.0 scipy==1.17.1 pyyaml

Usage:  <venv>/python experiments/run_sequence_model.py
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
import torch  # noqa: E402
from torch import nn  # noqa: E402

from oran_ids.data import load_radio, load_radio_sequences  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.splits import (group_disjoint_split, random_split,  # noqa: E402
                             stratified_group_split)

warnings.filterwarnings("ignore")
torch.set_num_threads(4)

OUT = ROOT / "results" / "EXP-050"
SPLIT_SEEDS = list(range(101, 121))
MODEL_SEEDS = [11, 22]
EPOCHS, PATIENCE, BATCH, LR = 100, 10, 64, 1e-3


class GRUNet(nn.Module):
    def __init__(self, f):
        super().__init__()
        self.gru = nn.GRU(f, 32, batch_first=True)
        self.out = nn.Linear(32, 1)

    def forward(self, x):
        _, h = self.gru(x)
        return self.out(h[-1]).squeeze(-1)


class CNNNet(nn.Module):
    def __init__(self, f):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(f, 32, 3, padding=1), nn.ReLU(),
            nn.Conv1d(32, 32, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1))
        self.out = nn.Linear(32, 1)

    def forward(self, x):                     # x: (n, 16, f)
        return self.out(self.net(x.transpose(1, 2)).squeeze(-1)).squeeze(-1)


def fit_predict(Net, Xtr, ytr, Xte, seed):
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)
    mu = Xtr.reshape(-1, Xtr.shape[-1]).mean(0)
    sd = Xtr.reshape(-1, Xtr.shape[-1]).std(0) + 1e-6
    Ztr, Zte = (Xtr - mu) / sd, (Xte - mu) / sd
    idx = rng.permutation(len(ytr))
    n_val = max(1, int(0.1 * len(ytr)))
    va, tr = idx[:n_val], idx[n_val:]
    xt = torch.tensor(Ztr[tr], dtype=torch.float32)
    yt = torch.tensor(ytr[tr], dtype=torch.float32)
    xv = torch.tensor(Ztr[va], dtype=torch.float32)
    yv = torch.tensor(ytr[va], dtype=torch.float32)
    n_pos = float(ytr[tr].sum())
    pos_weight = torch.tensor((len(tr) - n_pos) / max(n_pos, 1.0))
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    model = Net(Xtr.shape[-1])
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    best, best_state, wait = np.inf, None, 0
    for _ in range(EPOCHS):
        model.train()
        perm = torch.from_numpy(rng.permutation(len(tr)))
        for i in range(0, len(tr), BATCH):
            b = perm[i:i + BATCH]
            opt.zero_grad()
            loss_fn(model(xt[b]), yt[b]).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            v = float(loss_fn(model(xv), yv))
        if v < best - 1e-6:
            best, wait = v, 0
            best_state = {k: t.clone() for k, t in model.state_dict().items()}
        else:
            wait += 1
            if wait >= PATIENCE:
                break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(model(torch.tensor(Zte, dtype=torch.float32))).numpy()


def main() -> int:
    t0 = time.time()
    for d in ("raw", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    seq, y, cat, sess, feats = load_radio_sequences()
    ref = load_radio()
    assert np.array_equal(y, ref.y), "sequence labels differ from load_radio"
    assert np.array_equal(cat, ref.category), "sequence categories differ"
    assert np.array_equal(sess, np.asarray(ref.groups)), "sessions differ"
    print(f"sequences {seq.shape}, features {feats}", flush=True)

    rows = []
    for proto in ("random", "group_disjoint", "stratified_group"):
        for seed in SPLIT_SEEDS:
            if proto == "random":
                sp = random_split(y, sess, seed=seed, n_folds=1)[0]
            elif proto == "group_disjoint":
                sp = group_disjoint_split(y, sess, seed=seed, n_folds=1)[0]
            else:
                sp = stratified_group_split(y, sess, cat, seed=seed, n_folds=1)[0]
            tr, te = sp.train_idx, sp.test_idx
            for name, Net in (("gru", GRUNet), ("cnn1d", CNNNet)):
                for ms in MODEL_SEEDS:
                    s = fit_predict(Net, seq[tr], y[tr].astype(np.float32),
                                    seq[te], ms)
                    m = detection_metrics(y[te], s, 0.5)
                    rows.append(dict(protocol=proto, model=name, split_seed=seed,
                                     model_seed=ms, n_train=len(tr),
                                     n_test=len(te), **m))
            last = [r for r in rows[-4:]]
            print(f"  {proto:<17} seed {seed}: "
                  + " ".join(f"{r['model']}/{r['model_seed']} "
                             f"{r['f1_macro']:.3f}" for r in last)
                  + f"  ({time.time() - t0:.0f}s)", flush=True)

    pd.DataFrame(rows).to_csv(OUT / "raw/sequence_runs_radio.csv", index=False)
    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-050", data="load_radio_sequences (16 steps x 16 KPM "
        "features), identical windows to load_radio", n_windows=int(len(y)),
        features=feats, models={"gru": "GRU(hidden 32) -> linear",
                                "cnn1d": "2x Conv1d(32,k3) -> GAP -> linear"},
        training=dict(epochs=EPOCHS, patience=PATIENCE, batch=BATCH, lr=LR,
                      loss="BCEWithLogits, pos_weight = n_neg/n_pos",
                      validation="10% of training windows"),
        split_seeds=SPLIT_SEEDS, model_seeds=MODEL_SEEDS,
        torch=torch.__version__, python=platform.python_version(),
        platform=platform.platform(), runtime_s=round(time.time() - t0, 1)),
        indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
