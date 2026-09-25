#!/usr/bin/env python3
"""EXP-055: a published 5G-NIDD pipeline, reproduced, then run down the ladder.

Round-2 review R2-C2: the paper argues that held-out accuracy does not predict
deployment, but never reproduces a published result. This experiment takes the
pipeline the 5G-NIDD authors published with the dataset and changes one thing per
rung.

Published pipeline (Samarakoon et al., arXiv:2212.01298, Sections V-C, V-D, VI):
  data       Encoded.csv: Argus flow records, categorical fields one-hot encoded
  ranking    ANOVA F-score against the binary label; the top 10 features give the
             reported results (Table V: Seq, Offset, sTtl, e, tcp, AckDat, RST,
             INT, TcpRtt, icmp)
  scaling    z-score
  split      random 70/30, repeated 10 times (we repeat 5)
  models     DT, RF, KNN, Naive Bayes, MLP with hidden layers (10, 20, 10).
             Hyperparameters were grid-searched, but the grid is not reported, so
             scikit-learn defaults are used here.
  reported   binary accuracy 0.998956 (DT), 0.999467 (RF), 0.998675 (KNN),
             0.963472 (NB), 0.998520 (MLP)  (Table X)

Seq and Offset are Argus's record counter and byte offset inside one capture
file. They rank first and second in Table V. They reset at every file boundary,
which is how this experiment recovers the 20 capture files: two passes over the
same ten captures (eight attacks with Slowrate DoS in two files, and one
benign-only file), one pass per base station.

Ladder, one change per rung:
  R0  published: random 70/30 split, published top-10 features
  R1  R0 without the two position counters (next two features of Table V's
      ranking take their place: sMeanPktSz, FIN)
  R2  capture-file-disjoint: five group folds over the 20 files, each file
      tested once; both feature sets
  R3  base-station-disjoint: train on one pass, test on the other, both
      directions; both feature sets
Operational precision at pi = 0.002 is computed later from the pooled counts of
R2 and R3, where every flow is tested once per direction.

Every read of D_B is logged to results/EXP-026/logs/target_access.log.

Usage:  python experiments/run_published_pipeline.py [--repeats 5]
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
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.feature_selection import f_classif  # noqa: E402
from sklearn.metrics import (balanced_accuracy_score, confusion_matrix,  # noqa: E402
                             f1_score, roc_auc_score)
from sklearn.model_selection import GroupKFold, train_test_split  # noqa: E402
from sklearn.naive_bayes import GaussianNB  # noqa: E402
from sklearn.neighbors import KNeighborsClassifier  # noqa: E402
from sklearn.neural_network import MLPClassifier  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

from oran_ids.data import _log_target_access  # noqa: E402

warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "EXP-055"
ENCODED = ROOT / "data" / "raw" / "d_b" / "Encoded.csv"
LABELS = ("Label", "Attack Type", "Attack Tool")
NOT_FEATURES = ("Unnamed: 0",) + LABELS
# Table V of the paper: the ANOVA F-scores it reports for the top binary features.
TABLE_V = {"Seq": 329589.08, "Offset": 223791.80, "sTtl": 189934.06, "e": 159060.91,
           "tcp": 142813.28, "AckDat": 80707.00, "RST": 35379.19, "INT": 33941.29,
           "TcpRtt": 32500.88, "icmp": 29713.08, "sMeanPktSz": 26963.61,
           "FIN": 24472.87, "sHops": 24055.76, "Mean": 23238.27}
PUBLISHED_TOP10 = ["Seq", "Offset", "sTtl", "e", "tcp", "AckDat", "RST", "INT",
                   "TcpRtt", "icmp"]
NO_POSITION_TOP10 = ["sTtl", "e", "tcp", "AckDat", "RST", "INT", "TcpRtt", "icmp",
                     "sMeanPktSz", "FIN"]
REPORTED_ACC = {"dt": 0.998955772, "rf": 0.999467331, "knn": 0.998675045,
                "nb": 0.963472299, "mlp": 0.998520425}


def models(seed: int) -> dict:
    return {"dt": DecisionTreeClassifier(random_state=seed),
            "rf": RandomForestClassifier(random_state=seed, n_jobs=-1),
            "knn": KNeighborsClassifier(n_jobs=-1),
            "nb": GaussianNB(),
            # early stopping: the default (200 epochs on ~850k rows) took 17 min
            # per fit under load; attempt 1 with the default reproduced 0.99863
            "mlp": MLPClassifier(hidden_layer_sizes=(10, 20, 10), early_stopping=True,
                                 random_state=seed)}


def log(msg: str) -> None:
    print(msg, flush=True)


def capture_files(offset: np.ndarray) -> np.ndarray:
    """1-based capture-file id: a new file starts wherever Offset falls."""
    return np.cumsum(np.r_[True, offset[1:] < offset[:-1]]).astype(int)


def _clean_metrics(yte, pred, keep) -> dict:
    """Metrics on the test flows that are not conflicting benign records."""
    yk, pk = yte[keep], pred[keep]
    tn, fp, fn, tp = confusion_matrix(yk, pk, labels=[0, 1]).ravel()
    tpr = tp / (tp + fn) if tp + fn else np.nan
    tnr = tn / (tn + fp) if tn + fp else np.nan
    return dict(clean_n=int(keep.sum()), clean_accuracy=float((tp + tn) / max(len(yk), 1)),
                clean_balanced_accuracy=float((tpr + tnr) / 2), clean_recall=float(tpr),
                clean_fpr=float(fp / (fp + tn)) if fp + tn else np.nan,
                clean_tp=int(tp), clean_fp=int(fp), clean_tn=int(tn), clean_fn=int(fn))


def evaluate(key, model, Xtr, ytr, Xte, yte, keep=None) -> dict:
    t0 = time.time()
    model.fit(Xtr, ytr)
    t_fit = time.time() - t0
    t0 = time.time()
    pred = model.predict(Xte)
    t_pred = time.time() - t0
    try:
        score = model.predict_proba(Xte)[:, 1]
        auc = float(roc_auc_score(yte, score)) if len(np.unique(yte)) > 1 else np.nan
    except Exception:  # noqa: BLE001
        auc = np.nan
    tn, fp, fn, tp = confusion_matrix(yte, pred, labels=[0, 1]).ravel()
    extra = _clean_metrics(yte, pred, keep) if keep is not None else {}
    return dict(**extra, accuracy=float((tp + tn) / len(yte)),
                balanced_accuracy=float(balanced_accuracy_score(yte, pred)),
                f1_macro=float(f1_score(yte, pred, average="macro")),
                recall=float(tp / (tp + fn)) if tp + fn else np.nan,
                fpr=float(fp / (fp + tn)) if fp + tn else np.nan,
                roc_auc=auc, tp=int(tp), fp=int(fp), tn=int(tn), fn=int(fn),
                fit_s=round(t_fit, 2), predict_s=round(t_pred, 2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()
    t_all = time.time()
    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    _log_target_access("EXP-055 published-pipeline reproduction (Encoded.csv, trains on D_B)")
    df = pd.read_csv(ENCODED, low_memory=False)
    log("Encoded.csv: %d rows, %d columns" % df.shape)
    y = (df["Label"] != "Benign").to_numpy(np.int8)
    files = capture_files(df["Offset"].to_numpy())
    n_files = int(files.max())
    site = np.where(files <= n_files // 2, 1, 2)
    fsum = (pd.DataFrame(dict(file=files, y=y, attack=df["Attack Type"]))
            .groupby("file").agg(n=("y", "size"), attack_share=("y", "mean"),
                                 attack_type=("attack", lambda s: s[s != "Benign"].mode().iat[0]
                                              if (s != "Benign").any() else "none")))
    fsum["site"] = np.where(fsum.index <= n_files // 2, 1, 2)
    fsum.to_csv(OUT / "processed/capture_files.csv")
    # EXP-057: benign flows whose record (all fields but the row index, Seq,
    # Offset and the labels) also occurs with an attack label
    content = df.drop(columns=[c for c in ("Unnamed: 0", "Seq", "Offset") + LABELS
                               if c in df.columns])
    h = pd.util.hash_pandas_object(content, index=False).to_numpy()
    att = set(h[y == 1])
    conflict = (y == 0) & np.fromiter((k in att for k in h), bool, len(h))
    log("benign flows with an attack-labelled twin record: %d" % conflict.sum())
    log(fsum.to_string())
    if n_files != 20:
        raise AssertionError(f"expected 20 capture files, found {n_files}")

    # ---- verify the published ranking on this copy of the data ----------------
    feats = df.drop(columns=[c for c in NOT_FEATURES if c in df.columns])
    feats = feats.apply(pd.to_numeric, errors="coerce")
    keep = [c for c in feats.columns
            if feats[c].notna().any() and feats[c].nunique(dropna=True) > 1]
    feats = feats[keep].fillna(0.0).astype(np.float64)
    F, _ = f_classif(feats.to_numpy(), y)
    rank = (pd.DataFrame(dict(feature=feats.columns, F=F))
            .sort_values("F", ascending=False).reset_index(drop=True))
    rank.to_csv(OUT / "processed/anova_ranking.csv", index=False)
    # map each published name to this copy's column; "e" is a one-hot flag column
    colmap = {}
    for name, f_pub in TABLE_V.items():
        cands = [c for c in feats.columns if c.strip() == name]
        if not cands:
            continue
        best = min(cands, key=lambda c: abs(rank.set_index("feature").loc[c, "F"] - f_pub))
        colmap[name] = best
    check = pd.DataFrame([dict(published=n, column=repr(colmap.get(n)),
                               F_published=TABLE_V[n],
                               F_here=float(rank.set_index("feature").loc[colmap[n], "F"])
                               if n in colmap else np.nan) for n in TABLE_V])
    check["rel_diff"] = (check.F_here - check.F_published) / check.F_published
    check.to_csv(OUT / "processed/table_v_check.csv", index=False)
    log("\nTable V check (published ANOVA F against this copy):")
    log(check.to_string(index=False, float_format=lambda v: "%.4f" % v))
    missing = [n for n in PUBLISHED_TOP10 + NO_POSITION_TOP10 if n not in colmap]
    if missing:
        raise AssertionError(f"published features not found: {missing}")

    sets = {"published_top10": [colmap[n] for n in PUBLISHED_TOP10],
            "no_position_top10": [colmap[n] for n in NO_POSITION_TOP10]}
    Xall = {k: feats[v].to_numpy(np.float64) for k, v in sets.items()}

    raw_path = OUT / "raw/ladder_runs.csv"
    rows = pd.read_csv(raw_path).to_dict("records") if raw_path.exists() else []
    done = {(r["rung"], r["feature_set"], r["split"], r["model"]) for r in rows}

    def run(rung, fset, split_id, tr, te, seed):
        # KNN is kept at R0, where it reproduces the published number; on later
        # rungs its prediction on ~1M rows dominated the runtime (round 2)
        todo = [k for k in models(seed) if (rung, fset, split_id, k) not in done
                and (k != "knn" or rung == "R0")]
        if not todo:
            return
        sc = StandardScaler().fit(Xall[fset][tr])
        Xtr, Xte = sc.transform(Xall[fset][tr]), sc.transform(Xall[fset][te])
        keep = ~conflict[te]
        for key, m in models(seed).items():
            if key not in todo:
                continue
            rec = evaluate(key, m, Xtr, y[tr], Xte, y[te], keep)
            rows.append(dict(rung=rung, feature_set=fset, split=split_id,
                             seed=seed, model=key, n_train=int(tr.sum()),
                             n_test=int(te.sum()),
                             test_prevalence=float(y[te].mean()), **rec))
            log("  %-3s %-18s %-10s %-4s acc %.5f  BA %.4f  FPR %.4f  (%.0fs)"
                % (rung, fset, split_id, key, rec["accuracy"],
                   rec["balanced_accuracy"], rec["fpr"], time.time() - t_all))
        pd.DataFrame(rows).to_csv(raw_path, index=False)

    idx = np.arange(len(y))
    # R0, R1: the published random 70/30 split, repeated
    for rep in range(args.repeats):
        tr_i, te_i = train_test_split(idx, test_size=0.30, random_state=100 + rep)
        tr = np.zeros(len(y), bool); tr[tr_i] = True
        run("R0", "published_top10", f"rep{rep}", tr, ~tr, 11 + rep)
        run("R1", "no_position_top10", f"rep{rep}", tr, ~tr, 11 + rep)
    # R2: capture-file-disjoint, five group folds, each file tested once
    for k, (tr_i, te_i) in enumerate(GroupKFold(n_splits=5).split(idx, y, files)):
        tr = np.zeros(len(y), bool); tr[tr_i] = True
        for fset in sets:
            run("R2", fset, f"fold{k}", tr, ~tr, 11)
    # R3: base-station-disjoint, both directions
    for a, b in ((1, 2), (2, 1)):
        tr = site == a
        for fset in sets:
            run("R3", fset, f"site{a}to{b}", tr, site == b, 11)

    R = pd.DataFrame(rows)
    R.to_csv(OUT / "raw/ladder_runs.csv", index=False)
    summ = (R.groupby(["rung", "feature_set", "model"])
            .agg(accuracy=("accuracy", "mean"), balanced_accuracy=("balanced_accuracy", "mean"),
                 f1_macro=("f1_macro", "mean"), recall=("recall", "mean"),
                 fpr=("fpr", "mean"), roc_auc=("roc_auc", "mean"),
                 tp=("tp", "sum"), fp=("fp", "sum"), tn=("tn", "sum"), fn=("fn", "sum"),
                 clean_balanced_accuracy=("clean_balanced_accuracy", "mean"),
                 clean_fpr=("clean_fpr", "mean"), clean_recall=("clean_recall", "mean"),
                 clean_tp=("clean_tp", "sum"), clean_fp=("clean_fp", "sum"),
                 clean_tn=("clean_tn", "sum"), clean_fn=("clean_fn", "sum"),
                 n=("accuracy", "size")).reset_index())
    summ["reported_accuracy"] = summ.model.map(REPORTED_ACC)
    summ.to_csv(OUT / "processed/ladder_summary.csv", index=False)
    log("\n" + summ.to_string(index=False, float_format=lambda v: "%.4f" % v))

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-055", answers=["R2-C1", "R2-C2", "R1-W1"],
        source="Samarakoon et al., 5G-NIDD, arXiv:2212.01298, Tables V and X",
        data=str(ENCODED.relative_to(ROOT)), n_rows=int(len(y)),
        attack_prevalence=float(y.mean()), n_capture_files=n_files,
        capture_file_rule="new file wherever Offset decreases",
        site_rule="files 1-10 and 11-20 are the two passes, one per base station "
                  "(the dataset description names two base stations; the "
                  "assignment of passes to stations is inferred from the "
                  "repeated capture schedule)",
        feature_sets=sets, feature_columns_repr={k: [repr(c) for c in v] for k, v in sets.items()},
        n_conflicting_benign=int(conflict.sum()),
        deviations=[f"{args.repeats} random repeats instead of 10",
                    "scikit-learn default hyperparameters (grid not reported), "
                    "except MLP early_stopping=True (attempt 1 with the default "
                    "MLP reproduced accuracy 0.99863, see raw/ladder_runs_attempt1_default_mlp.csv)",
                    "StandardScaler fitted on the training part of each split"],
        repeats=args.repeats, python=platform.python_version(),
        platform=platform.platform(), runtime_s=round(time.time() - t_all, 1)),
        indent=2), encoding="utf-8")
    log("\nwrote %s (%.0fs)" % (OUT, time.time() - t_all))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
