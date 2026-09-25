#!/usr/bin/env python3
"""EXP-041 / EXP-045 / EXP-047 / EXP-049: the transfer experiment, extended.

EXP-026 answered RQ1. Review (reports/peer_review_ieee_access_2026-09-24.md)
asked for things its outputs cannot answer. This runner keeps EXP-026's design
exactly and adds what the reviewers need:

  * per-threshold confusion COUNTS on the source held-out fold and on the
    target, so every operating-point table is built from pooled counts (D-018)
    rather than from per-fold averages of a non-linear functional;
  * equal-mass reliability bins (15), so the reliability diagram is drawn from
    data instead of typed by hand;
  * a declared exporter-robust feature subset (``--features robust``), fixed in
    D-022 BEFORE any target result under it existed;
  * a CORAL arm (``--adapt coral``, Sun et al., AAAI 2016) that re-colours the
    source to the target covariance. It READS UNLABELLED TARGET FEATURES, so it
    is a declared, transductive exception to the D_B quarantine and is never
    the primary result;
  * a source-only mode (``--source-only``) for the harmonisation-loss question:
    how much in-distribution skill does projecting onto the shared space cost?

Unchanged from EXP-026, and not to be changed after seeing any result:
  split seeds 101-120, model seed 11, source subsample 300,000 (seeded), split
  group-disjoint on src_ip, threshold 0.5, the full ladder including both
  trivial floors, target evaluated whole.

Usage:
  python experiments/run_transfer_v2.py --exp EXP-041 --direction a_to_b \
      --sweeps --reliability
  python experiments/run_transfer_v2.py --exp EXP-041 --direction b_to_a
  python experiments/run_transfer_v2.py --exp EXP-045 --features robust --sweeps
  python experiments/run_transfer_v2.py --exp EXP-049 --adapt coral
  python experiments/run_transfer_v2.py --exp EXP-047 --features transferable \
      --source-only
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
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.data import (load_network, load_network_shared,  # noqa: E402
                           load_target_d_b, load_target_d_c)
from oran_ids.features.shared import (COLUMNS, PROTO_COLS,  # noqa: E402
                                      assert_compatible)
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split, random_split  # noqa: E402
from experiments.run_transfer import (per_category_recall,  # noqa: E402
                                      subsample)

warnings.filterwarnings("ignore")

SPLIT_SEEDS = list(range(101, 121))
MODEL_SEED = 11
SOURCE_SUBSAMPLE = 300_000
THRESHOLD = 0.5
TAU_GRID = np.round(np.concatenate(
    [np.arange(0.05, 1.0, 0.05), [0.975, 0.99, 0.995, 0.999]]), 4)
N_BINS = 15

# D-022, fixed before any target result under it was seen. Duration, the two
# rates divided by it, and the seven packet and byte totals all depend on where
# an exporter decides a flow ends, and Zeek and Argus disagree about that by four
# orders of magnitude in median duration. Per-packet means and direction ratios
# are invariant to splitting a flow into pieces, and the protocol is a header
# field. This subset is the part of the shared space that a change of exporter
# should move least.
ROBUST_COLUMNS = PROTO_COLS + ("mean_pkt_size", "src_mean_pkt_size",
                               "dst_mean_pkt_size", "src_byte_ratio",
                               "src_pkt_ratio")


# ---------------------------------------------------------------------------
def counts_at(y: np.ndarray, s: np.ndarray, taus: np.ndarray) -> pd.DataFrame:
    """tp, fp, tn, fn at each threshold, by sorting once (score >= tau)."""
    y = np.asarray(y).astype(bool)
    pos = np.sort(s[y])
    neg = np.sort(s[~y])
    n_pos, n_neg = len(pos), len(neg)
    tp = n_pos - np.searchsorted(pos, taus, side="left")
    fp = n_neg - np.searchsorted(neg, taus, side="left")
    return pd.DataFrame({"tau": taus, "tp": tp, "fp": fp,
                         "fn": n_pos - tp, "tn": n_neg - fp})


def reliability_bins(y: np.ndarray, s: np.ndarray, n_bins: int = N_BINS):
    """Equal-mass bins: (bin, mean score, attack frequency, n)."""
    order = np.argsort(s, kind="mergesort")
    out = []
    for b, idx in enumerate(np.array_split(order, min(n_bins, len(order)))):
        if len(idx):
            out.append((b, float(s[idx].mean()), float(y[idx].mean()),
                        int(len(idx))))
    return out


def _sym_power(C: np.ndarray, p: float) -> np.ndarray:
    w, V = np.linalg.eigh(C)
    w = np.clip(w, 1e-12, None)
    return (V * w ** p) @ V.T


class Coral:
    """CORAL (Sun, Feng and Saenko, AAAI 2016), with per-domain z-scoring.

    Source rows are z-scored with source-train statistics, whitened by the
    source covariance and re-coloured with the target covariance. Target rows
    are z-scored with TARGET statistics. Both covariances carry the identity
    regulariser of the original paper. Fitting it reads unlabelled target
    features: a declared exception to the D_B quarantine.
    """

    def fit(self, Xs: np.ndarray, Xt: np.ndarray) -> "Coral":
        self.mu_s, self.sd_s = Xs.mean(0), Xs.std(0) + 1e-9
        self.mu_t, self.sd_t = Xt.mean(0), Xt.std(0) + 1e-9
        Zs = (Xs - self.mu_s) / self.sd_s
        Zt = (Xt - self.mu_t) / self.sd_t
        eye = np.eye(Xs.shape[1])
        Cs = np.cov(Zs, rowvar=False) + eye
        Ct = np.cov(Zt, rowvar=False) + eye
        self.A = _sym_power(Cs, -0.5) @ _sym_power(Ct, 0.5)
        return self

    def source(self, X: np.ndarray) -> np.ndarray:
        return ((X - self.mu_s) / self.sd_s) @ self.A

    def target(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mu_t) / self.sd_t


# ---------------------------------------------------------------------------
def load_pair(direction: str, features: str, source_only: bool):
    reason = f"{EXP} {direction} features={features}"
    if direction == "a_to_b":
        if features == "transferable":
            src = load_network(feature_set="transferable")
        else:
            src = load_network_shared()
        tgt = None if source_only else load_target_d_b(
            reason=reason, groups="capture_file" if GROUP_COUNTS else "none")
        return src, tgt, src.groups, True
    if direction in ("a_to_c", "b_to_c"):
        # EXP-058: a third corpus (NFStream, Open5GS core) as target
        tgt = None if source_only else load_target_d_c(reason=reason)
        if direction == "a_to_c":
            src = load_network_shared()
            return src, tgt, src.groups, True
        src = load_target_d_b(reason=reason + " (as SOURCE for D_C)")
        return src, tgt, np.arange(len(src.y)), False
    src = load_target_d_b(reason=reason + " (as SOURCE, reverse check)")
    tgt = None if source_only else load_network_shared()
    return src, tgt, np.arange(len(src.y)), False


def select(X: pd.DataFrame, features: str) -> pd.DataFrame:
    if features == "robust":
        return X[list(ROBUST_COLUMNS)]
    return X


def run(args) -> None:
    t_start = time.time()
    out = ROOT / "results" / EXP / args.tag
    for sub in ("raw", "processed", "statistics", "logs"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    models = args.models or [m.key for m in LADDER]
    seeds = SPLIT_SEEDS[: args.seeds]
    src, tgt, groups, grouped = load_pair(args.direction, args.features,
                                          args.source_only)
    Xsrc_all = select(src.X, args.features)
    Xtgt_all = None if tgt is None else select(tgt.X, args.features)
    if Xtgt_all is not None and args.features != "transferable":
        if args.features == "shared":
            assert_compatible(Xsrc_all, Xtgt_all)
        else:
            assert tuple(Xsrc_all.columns) == tuple(Xtgt_all.columns)
    print(f"[{args.tag}] source {src.name} {Xsrc_all.shape} "
          f"attack {src.y.mean():.4f}", flush=True)
    if tgt is not None:
        print(f"[{args.tag}] target {tgt.name} {Xtgt_all.shape} "
              f"attack {tgt.y.mean():.4f}", flush=True)

    rows, cats, sweeps, rel, gcounts = [], [], [], [], []
    for si, seed in enumerate(seeds):
        Xs, ys, cs, gs = subsample(Xsrc_all, src.y, src.category, groups,
                                   SOURCE_SUBSAMPLE, seed)
        if grouped:
            sp = group_disjoint_split(ys, gs, seed=seed, n_folds=1)[0]
            sp.check_disjoint(gs)
        else:
            sp = random_split(ys, gs, seed=seed, n_folds=1)[0]
        Xtr, ytr = Xs.iloc[sp.train_idx], ys[sp.train_idx]
        Xte, yte = Xs.iloc[sp.test_idx], ys[sp.test_idx]

        Xt_eval = Xtgt_all
        if args.adapt == "coral":
            cor = Coral().fit(Xtr.to_numpy(np.float64),
                              Xtgt_all.to_numpy(np.float64))
            cols = list(Xtr.columns)
            Xtr = pd.DataFrame(cor.source(Xtr.to_numpy(np.float64)),
                               columns=cols).astype(np.float32)
            Xte = pd.DataFrame(cor.source(Xte.to_numpy(np.float64)),
                               columns=cols).astype(np.float32)
            Xt_eval = pd.DataFrame(cor.target(Xtgt_all.to_numpy(np.float64)),
                                   columns=cols).astype(np.float32)

        for key in models:
            t0 = time.time()
            model = fit_model(key, Xtr, ytr, MODEL_SEED)
            s_src = predict_scores(model, Xte)
            domains = [("source_heldout", yte, s_src, None)]
            if Xt_eval is not None:
                s_tgt = predict_scores(model, Xt_eval)
                domains.append(("target", tgt.y, s_tgt, tgt.category))
            if args.group_counts:
                # round-2 R1-W4: counts per cluster, for a cluster bootstrap.
                # source clusters are source addresses, target clusters are
                # capture files.
                # a source without a group key (random split, one "group" per
                # row) has no clusters; counting per row built ~10^7 tables
                glist = ([("source_heldout", yte, s_src, np.asarray(gs)[sp.test_idx])]
                         if grouped else [])
                if Xt_eval is not None:
                    glist.append(("target", tgt.y, s_tgt, np.asarray(tgt.groups)))
                for dom, yy, ss, gg in glist:
                    for g in np.unique(gg):
                        mk = gg == g
                        c = counts_at(yy[mk], ss[mk], TAU_GRID)
                        c.insert(0, "group", g)
                        c.insert(0, "domain", dom)
                        c.insert(0, "split_seed", seed)
                        c.insert(0, "model", key)
                        gcounts.append(c)
            for dom, yy, ss, cc in domains:
                m = detection_metrics(yy, ss, THRESHOLD)
                rows.append(dict(model=key, split_seed=seed, domain=dom,
                                 n_train=len(ytr), n_eval=len(yy),
                                 train_prevalence=float(ytr.mean()), **m))
                if args.sweeps:
                    c = counts_at(yy, ss, TAU_GRID)
                    c.insert(0, "domain", dom)
                    c.insert(0, "split_seed", seed)
                    c.insert(0, "model", key)
                    sweeps.append(c)
                if args.reliability:
                    for b, ms, fr, n in reliability_bins(yy, ss):
                        rel.append(dict(model=key, split_seed=seed, domain=dom,
                                        bin=b, mean_score=ms, attack_freq=fr,
                                        n=n))
                if cc is not None:
                    pred = (ss >= THRESHOLD).astype(int)
                    cats.append(dict(model=key, split_seed=seed,
                                     **per_category_recall(yy, cc, pred)))
            last = rows[-1]
            print(f"  seed {seed} [{si + 1}/{len(seeds)}] {key:<10} "
                  f"src {rows[-len(domains)]['f1_macro']:.3f}"
                  + (f" -> tgt {last['f1_macro']:.3f}" if Xt_eval is not None
                     else "") + f"  {time.time() - t0:.1f}s", flush=True)

    pd.DataFrame(rows).to_csv(out / "raw/runs.csv", index=False)
    if cats:
        pd.DataFrame(cats).to_csv(out / "processed/per_category_recall.csv",
                                  index=False)
    if sweeps:
        pd.concat(sweeps).to_csv(out / "raw/tau_counts.csv", index=False)
    if rel:
        pd.DataFrame(rel).to_csv(out / "raw/reliability_bins.csv", index=False)
    if gcounts:
        pd.concat(gcounts).to_csv(out / "raw/tau_counts_by_group.csv", index=False)

    prov = dict(
        experiment=EXP, tag=args.tag, direction=args.direction,
        features=args.features,
        columns=list(Xsrc_all.columns), n_features=int(Xsrc_all.shape[1]),
        adapt=args.adapt, source_only=args.source_only, models=models,
        split_seeds=seeds, model_seed=MODEL_SEED, threshold=THRESHOLD,
        source_subsample=SOURCE_SUBSAMPLE,
        source_split=("group_disjoint(src_ip)" if grouped
                      else "random (D_B has no group key; optimistic bound)"),
        tau_grid=TAU_GRID.tolist() if args.sweeps else None,
        reliability_bins=N_BINS if args.reliability else None,
        mlp_class_weighting="balanced sample_weight (D-021)",
        target_reads_unlabelled_features=(args.adapt == "coral"),
        source=src.summary(), target=None if tgt is None else tgt.summary(),
        exporter_confound=("source and target produced by different exporters; "
                           "every transfer gap is an upper bound on deployment "
                           "shift"),
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t_start, 1))
    (out / "statistics/provenance.json").write_text(
        json.dumps(prov, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {out}  ({time.time() - t_start:.0f}s)")


def main() -> None:
    global EXP, GROUP_COUNTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", required=True)
    ap.add_argument("--direction", default="a_to_b", choices=["a_to_b", "b_to_a", "a_to_c", "b_to_c"])
    ap.add_argument("--features", default="shared",
                    choices=["shared", "robust", "transferable"])
    ap.add_argument("--adapt", default="none", choices=["none", "coral"])
    ap.add_argument("--source-only", action="store_true")
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--sweeps", action="store_true")
    ap.add_argument("--group-counts", action="store_true",
                    help="store tau counts per source address and per D_B "
                         "capture file (cluster bootstrap, round-2 R1-W4)")
    ap.add_argument("--reliability", action="store_true")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    EXP = a.exp
    GROUP_COUNTS = a.group_counts
    if a.features == "transferable" and not a.source_only:
        raise SystemExit("--features transferable has no target counterpart; "
                         "use --source-only")
    a.tag = a.tag or "__".join(
        [a.direction, a.features] + ([a.adapt] if a.adapt != "none" else [])
        + (["source_only"] if a.source_only else []))
    run(a)


EXP = "EXP-041"
GROUP_COUNTS = False

if __name__ == "__main__":
    main()
