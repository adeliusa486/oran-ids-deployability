#!/usr/bin/env python3
"""EXP-054: in-target references for the transfer gap, on D_B itself.

Round-2 review R1-W1 / R2-C3: Eq. (1) measures the transfer gap against the
source's own held-out score. Models trained and tested on a random split of D_B
reach only 0.71-0.75 balanced accuracy in the 18-column shared space, and four
architectures sit at 0.751-0.752 with identical recall, specificity and ROC-AUC.
Part of the reported 0.21-0.36 gap is therefore the target's own difficulty in
the shared space, not transfer failure.

This experiment measures, on D_B only:

  1. in-target balanced accuracy under three protocols
       random          a 300,000-flow subsample split 80/20 (EXP-041's reverse
                       reference, repeated here with the same code path)
       file_disjoint   four of the 20 capture files held out per seed
       site_disjoint   train on one base station's pass, test on the other's
     The capture files are recovered from resets of Argus's Offset field (see
     run_published_pipeline.py); the site is the pass (files 1-10, 11-20).
  2. the same with D_B's native features (Encoded.csv without the identifiers
     Unnamed: 0, Seq, Offset), so the cost of projecting D_B onto the shared
     space is measured on the target side too (review Table XII asked for it);
  3. the plateau: how many D_B flows share an 18-column vector with a flow of the
     opposite label, and the balanced accuracy of the best possible function of
     the 18 columns (majority label per distinct vector, in sample). This bounds
     every classifier in the shared space from above.

D_B is read here as a SOURCE. Every read is logged to
results/EXP-026/logs/target_access.log.

Usage:  python experiments/run_target_reference.py
"""
from __future__ import annotations

import argparse
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

from oran_ids.data import _log_target_access, load_label_map, _apply_canonical  # noqa: E402
from oran_ids.features import shared as _sh  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-054"
RAW_DB = ROOT / "data" / "raw" / "d_b"
MODEL_SEED = 11
SUBSAMPLE = 300_000
N_TRAIN, N_TEST = 240_000, 60_000
NATIVE_DROP = ("Unnamed: 0", "Seq", "Offset", "Label", "Attack Type", "Attack Tool")


def log(msg: str) -> None:
    print(msg, flush=True)


def capture_files(offset: np.ndarray) -> np.ndarray:
    return np.cumsum(np.r_[True, offset[1:] < offset[:-1]]).astype(int)


def load() -> dict:
    _log_target_access("EXP-054 in-target reference: Combined.csv + Encoded.csv, "
                       "D_B trained on as SOURCE (round-2 R1-W1)")
    comb = pd.read_csv(RAW_DB / "Combined.csv", low_memory=False)
    enc = pd.read_csv(RAW_DB / "Encoded.csv", low_memory=False)
    if len(comb) != len(enc) or not (comb["Label"].to_numpy() == enc["Label"].to_numpy()).all() \
            or not np.array_equal(comb["Offset"].to_numpy(), enc["Offset"].to_numpy()):
        raise AssertionError("Combined.csv and Encoded.csv rows do not align")
    lm = load_label_map()["corpus_d_b"]
    y = _apply_canonical(comb[lm["binary_column"]], lm["binary_map"],
                         "D_B binary").to_numpy(np.int8)
    cat = _apply_canonical(comb[lm["category_column"]], lm["map"],
                           "D_B category").to_numpy()
    files = capture_files(comb["Offset"].to_numpy())
    if files.max() != 20:
        raise AssertionError(f"expected 20 capture files, found {files.max()}")
    site = np.where(files <= 10, 1, 2)
    # EXP-057: benign flows whose record also occurs with an attack label
    content = comb.drop(columns=[c for c in NATIVE_DROP if c in comb.columns])
    h = pd.util.hash_pandas_object(content, index=False).to_numpy()
    att = set(h[y == 1])
    conflict = (y == 0) & np.fromiter((k in att for k in h), bool, len(h))
    Xs = _sh.from_d_b(comb).reset_index(drop=True)
    nat = enc.drop(columns=[c for c in NATIVE_DROP if c in enc.columns])
    nat = nat.apply(pd.to_numeric, errors="coerce")
    nat = nat[[c for c in nat.columns if nat[c].notna().any() and nat[c].nunique() > 1]]
    Xn = nat.fillna(0.0).astype(np.float32).reset_index(drop=True)
    Xn.columns = [f"f{i:02d}_{str(c).strip().replace(' ', '_') or 'blank'}"
                  for i, c in enumerate(Xn.columns)]
    return dict(y=y, cat=cat, files=files, site=site, conflict=conflict,
                X={"shared18": Xs, "native": Xn})


def plateau(X: pd.DataFrame, y: np.ndarray, name: str) -> dict:
    """Share of flows whose exact vector occurs with both labels, and the BA of
    the majority label per distinct vector (an in-sample upper bound)."""
    key = pd.util.hash_pandas_object(X.round(9), index=False).to_numpy()
    d = pd.DataFrame(dict(k=key, y=y))
    g = d.groupby("k").y.agg(["mean", "size"])
    mixed = g[(g["mean"] > 0) & (g["mean"] < 1)]
    d = d.join(g["mean"].rename("p"), on="k")
    # balanced-accuracy-optimal rule: attack iff share of attacks > share of benign
    n1 = d.groupby("k").y.sum(); n0 = d.groupby("k").y.size() - n1
    rule = (n1 / max(int(y.sum()), 1) > n0 / max(int((1 - y).sum()), 1)).astype(int)
    pred = d.k.map(rule).to_numpy()
    tpr = pred[y == 1].mean()
    tnr = 1 - pred[y == 0].mean()
    in_mixed = d.k.isin(mixed.index).to_numpy()
    return dict(feature_set=name, n=int(len(y)), n_distinct=int(len(g)),
                share_in_conflicting_vectors=float(in_mixed.mean()),
                share_benign_in_conflicting=float(in_mixed[y == 0].mean()),
                share_attack_in_conflicting=float(in_mixed[y == 1].mean()),
                lookup_ba_upper_bound=float((tpr + tnr) / 2),
                lookup_tpr=float(tpr), lookup_tnr=float(tnr))


def draw(rng, idx: np.ndarray, n: int) -> np.ndarray:
    return idx if len(idx) <= n else rng.choice(idx, n, replace=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--native-seeds", type=int, default=5)
    args = ap.parse_args()
    t0 = time.time()
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    D = load()
    y, files, site = D["y"], D["files"], D["site"]
    log("D_B: %d flows, attack %.4f, %d capture files; shared %s, native %s (%.0fs)"
        % (len(y), y.mean(), files.max(), D["X"]["shared18"].shape,
           D["X"]["native"].shape, time.time() - t0))

    P = pd.DataFrame([plateau(D["X"]["shared18"], y, "shared18"),
                      plateau(D["X"]["native"], y, "native")])
    P.to_csv(OUT / "processed/plateau.csv", index=False)
    log("\nplateau:\n" + P.to_string(index=False, float_format=lambda v: "%.4f" % v))

    all_idx = np.arange(len(y))
    splits = []
    for s in range(args.seeds):
        seed = 101 + s
        rng = np.random.default_rng(seed)
        sub = rng.choice(all_idx, SUBSAMPLE, replace=False)
        perm = rng.permutation(sub)
        splits.append(("random", seed, perm[:N_TRAIN], perm[N_TRAIN:]))
        test_files = rng.choice(np.arange(1, 21), 4, replace=False)
        te_pool = all_idx[np.isin(files, test_files)]
        tr_pool = all_idx[~np.isin(files, test_files)]
        splits.append(("file_disjoint", seed, draw(rng, tr_pool, N_TRAIN),
                       draw(rng, te_pool, N_TEST)))
    for s in range(args.seeds // 2):
        for a, b in ((1, 2), (2, 1)):
            seed = 201 + s
            rng = np.random.default_rng(seed * 10 + a)
            splits.append((f"site{a}to{b}", seed,
                           draw(rng, all_idx[site == a], N_TRAIN),
                           all_idx[site == b]))

    conflict = D["conflict"]
    log("benign flows with an attack-labelled twin record: %d" % conflict.sum())
    raw_path = OUT / "raw/runs.csv"
    rows = pd.read_csv(raw_path).to_dict("records") if raw_path.exists() else []
    done = {(r["feature_set"], r["split"], int(r["split_seed"])) for r in rows}
    for fset in ("shared18", "native"):
        X = D["X"][fset]
        n_seen = {}
        for proto, seed, tr, te in splits:
            fam = "site_disjoint" if proto.startswith("site") else proto
            n_seen[fam] = n_seen.get(fam, 0) + 1
            limit = args.seeds if fset == "shared18" else args.native_seeds
            if n_seen[fam] > limit or (fset, proto, seed) in done:
                continue
            Xtr, Xte = X.iloc[tr], X.iloc[te]
            keep = ~conflict[te]
            for m in LADDER:
                model = fit_model(m.key, Xtr, y[tr], MODEL_SEED)
                s = predict_scores(model, Xte)
                met = detection_metrics(y[te], s, 0.5)
                mc = detection_metrics(y[te][keep], s[keep], 0.5)
                met.update({f"clean_{k}": mc[k] for k in
                            ("balanced_accuracy", "roc_auc", "fpr", "recall", "f1_macro")})
                met["clean_n"] = int(keep.sum())
                rows.append(dict(feature_set=fset, protocol=fam, split=proto,
                                 split_seed=seed, model=m.key,
                                 n_train=int(len(tr)), n_test=int(len(te)),
                                 train_prevalence=float(y[tr].mean()),
                                 test_prevalence=float(y[te].mean()),
                                 test_files=",".join(map(str, sorted(np.unique(files[te])))),
                                 **met))
            last = [r for r in rows[-len(LADDER):] if r["model"] in ("xgboost", "mlp")]
            log("  %-8s %-14s %-9s seed %d  BA xgb %.3f mlp %.3f  (%.0fs)"
                % (fset, fam, proto, seed, last[0]["balanced_accuracy"],
                   last[1]["balanced_accuracy"], time.time() - t0))
            pd.DataFrame(rows).to_csv(raw_path, index=False)

    R = pd.DataFrame(rows)
    R.to_csv(OUT / "raw/runs.csv", index=False)
    S = (R.groupby(["feature_set", "protocol", "model"])
         .agg(ba=("balanced_accuracy", "mean"), ba_sd=("balanced_accuracy", "std"),
              ba_clean=("clean_balanced_accuracy", "mean"),
              auc_clean=("clean_roc_auc", "mean"), fpr_clean=("clean_fpr", "mean"),
              auc=("roc_auc", "mean"), f1=("f1_macro", "mean"),
              fpr=("fpr", "mean"), recall=("recall", "mean"),
              n=("balanced_accuracy", "size")).reset_index())
    S.to_csv(OUT / "processed/summary.csv", index=False)
    log("\n" + S.to_string(index=False, float_format=lambda v: "%.3f" % v))

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-054", answers=["R1-W1", "R2-C3", "R3 (D_B group key)"],
        capture_file_rule="new file wherever Argus Offset decreases (20 files)",
        site_rule="files 1-10 and 11-20, one pass per base station (inferred)",
        protocols=dict(random="300k subsample, 240k/60k",
                       file_disjoint="4 of 20 files held out, 240k/60k drawn",
                       site_disjoint="240k from one site, all of the other"),
        native_features=list(D["X"]["native"].columns),
        native_dropped=list(NATIVE_DROP), seeds=args.seeds,
        n_conflicting_benign=int(conflict.sum()),
        clean_rule="test flows minus benign flows whose record also occurs with an attack label",
        native_seeds=args.native_seeds, model_seed=MODEL_SEED,
        models=[m.key for m in LADDER],
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t0, 1)), indent=2), encoding="utf-8")
    log("\nwrote %s (%.0fs)" % (OUT, time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
