#!/usr/bin/env python3
"""EXP-029: is a host-disjoint split really an attack-disjoint split?

The previous campaign flagged this as a caveat and D-013 demoted the network
layer to a directional cross-check because of it. A caveat in prose is not
evidence. This experiment measures it.

The worry, stated precisely. In a testbed, each attack scenario is typically
launched from a dedicated host. If that is true here, then grouping by `src_ip`
produces groups that are almost pure in attack category, and a "host-disjoint"
split is in substance an **attack-disjoint** split. Those are different tasks:

  host-disjoint    generalise to a new host running attacks you have seen
  attack-disjoint  generalise to an attack you have never seen

The second is much harder, and a leakage magnitude measured under it is not the
quantity the paper claims to report. It also inflates the apparent random-split
gap, because the random split has no such structure to destroy.

EXP-027 sharpened the question: FPR under a group-disjoint split ranges from
0.000 to 0.890 across folds for every architecture. Something about which groups
land in the test fold dominates the result. This experiment asks what.

Design:

  Part A (composition, no model fitted)
    For every candidate grouping on both layers, measure how much the grouping
    already determines the label:
      - normalised mutual information NMI(group, category) and NMI(group, binary)
      - Cramer's V
      - per-group label purity, weighted by group size
      - group count and concentration (largest group share, Gini)
    Each is read against TWO nulls, because an NMI of 0.4 means nothing on its
    own: a label-shuffled null, and a size-matched random grouping. Both are
    computed, not assumed.

  Part B (performance)
    Fit the ladder under each grouping and compare. If `src_ip` grouping and
    grouping directly BY attack type give the same scores, the two protocols are
    measuring the same thing and the naming is misleading.

  Part C (fold composition vs FPR)
    Regress per-fold FPR on test-fold composition, to test whether the 0.000 to
    0.890 range is explained by which groups landed in test.

Usage:  python experiments/run_grouping_confound.py [--part a|b|c|all] [--seeds N]
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats as _st  # noqa: E402
from sklearn.metrics import (mutual_info_score,  # noqa: E402
                             normalized_mutual_info_score)

from oran_ids.data import load_network, load_radio  # noqa: E402
from oran_ids.metrics import detection_metrics  # noqa: E402
from oran_ids.models import LADDER, fit_model, predict_scores  # noqa: E402
from oran_ids.splits import group_disjoint_split, random_split  # noqa: E402

warnings.filterwarnings("ignore")

OUT = Path("results/EXP-029")
N_NULL = 50          # label-shuffle replicates
SUBSAMPLE = 300_000  # declared, matches EXP-002


def cramers_v(a: np.ndarray, b: np.ndarray) -> float:
    ct = pd.crosstab(pd.Series(a), pd.Series(b)).to_numpy()
    if ct.size == 0 or ct.shape[0] < 2 or ct.shape[1] < 2:
        return float("nan")
    chi2 = _st.chi2_contingency(ct, correction=False)[0]
    n = ct.sum()
    return float(np.sqrt((chi2 / n) / (min(ct.shape) - 1)))


def weighted_purity(groups: np.ndarray, labels: np.ndarray) -> float:
    """Size-weighted fraction of each group held by its modal label.

    1.0 means every group is label-pure: the grouping IS the label.
    """
    df = pd.DataFrame({"g": groups, "y": labels})
    top = df.groupby("g")["y"].agg(lambda s: s.value_counts().iloc[0])
    size = df.groupby("g")["y"].size()
    return float(top.sum() / size.sum())


def concentration(groups: np.ndarray) -> dict:
    s = pd.Series(groups).value_counts()
    p = (s / s.sum()).to_numpy()
    srt = np.sort(p)
    n = len(srt)
    gini = float((2 * np.arange(1, n + 1) - n - 1).dot(srt) / n) if n > 1 else 0.0
    return dict(n_groups=int(len(s)), largest_group_share=float(p[0]),
                top5_share=float(p[:5].sum()), gini=gini)


def describe_grouping(name: str, groups: np.ndarray, y: np.ndarray,
                      category: np.ndarray, rng: np.random.Generator) -> dict:
    row = dict(grouping=name)
    row.update(concentration(groups))
    row["nmi_category"] = float(normalized_mutual_info_score(groups, category))
    row["nmi_binary"] = float(normalized_mutual_info_score(groups, y))
    row["cramers_v_category"] = cramers_v(groups, category)
    row["purity_category"] = weighted_purity(groups, category)
    row["purity_binary"] = weighted_purity(groups, y)

    # Null 1: shuffle the labels. Fixes group structure, destroys alignment.
    null = [normalized_mutual_info_score(groups, rng.permutation(category))
            for _ in range(N_NULL)]
    row["nmi_category_null_mean"] = float(np.mean(null))
    row["nmi_category_null_p95"] = float(np.percentile(null, 95))
    row["nmi_excess_over_null"] = row["nmi_category"] - row["nmi_category_null_mean"]

    # Null 2: a random grouping with the SAME number and size profile. This is
    # the stricter null -- it controls for the fact that many small groups
    # inflate NMI mechanically.
    sizes = pd.Series(groups).value_counts().to_numpy()
    fake = np.concatenate([np.full(s, i) for i, s in enumerate(sizes)])
    fake = rng.permutation(fake)[:len(groups)]
    row["nmi_category_sizematched_null"] = float(
        normalized_mutual_info_score(fake, category))
    return row


def aligned_metadata(n_expected: int) -> pd.DataFrame:
    """Identifier columns aligned row-for-row with ``load_network``'s output.

    Deduplicating a COLUMN SUBSET is not the same operation as deduplicating
    whole rows, and it is not close: on this corpus the subset collapses
    1,640,182 rows to 888,367. Reading the file whole, applying the identical
    exact-row dedup, and only then projecting is the only way the group arrays
    line up with the feature matrix. The length is asserted rather than trusted,
    because a silent off-by-N here would attach every group label to the wrong
    row and still produce a plausible-looking mutual information.
    """
    df = pd.read_csv(Path("data/raw/d_a/Network_Dataset.csv"), low_memory=False)
    df = df.drop_duplicates()                       # identical policy to data.py
    meta = df[["src_ip", "dst_ip", "src_port", "dst_port", "proto",
               "attack_category", "attack_type", "traffic_type"]].reset_index(drop=True)
    del df
    if len(meta) != n_expected:
        raise SystemExit(
            "metadata/corpus length mismatch: %d vs %d. The dedup policy here "
            "has drifted from data.load_network and every grouping below would "
            "be misaligned." % (len(meta), n_expected))
    return meta


def part_a(rng) -> pd.DataFrame:
    rows = []

    # ---- network layer -------------------------------------------------
    net = load_network(feature_set="full")
    raw = aligned_metadata(len(net.y))
    print("network: %d rows, %d src_ip groups" % (len(net.y), len(set(net.groups))))

    cands = {
        "src_ip": raw["src_ip"].to_numpy(),
        "dst_ip": raw["dst_ip"].to_numpy(),
        "src_ip__dst_ip": (raw["src_ip"].astype(str) + "|"
                           + raw["dst_ip"].astype(str)).to_numpy(),
        # The extreme case: group BY the attack scenario. If src_ip scores like
        # this, the two protocols are the same protocol.
        "attack_type_ORACLE": raw["attack_type"].to_numpy(),
        "dst_port": raw["dst_port"].astype(str).to_numpy(),
    }
    for name, g in cands.items():
        r = describe_grouping(name, g, net.y, net.category, rng)
        r["layer"] = "network"
        rows.append(r)
        print("  %-20s groups=%-6d NMI(cat)=%.3f (null %.3f) purity=%.3f"
              % (name, r["n_groups"], r["nmi_category"],
                 r["nmi_category_null_mean"], r["purity_category"]))

    # ---- radio layer ---------------------------------------------------
    rad = load_radio()
    print("radio: %d windows, %d session groups" % (len(rad.y), len(set(rad.groups))))
    r = describe_grouping("session", rad.groups, rad.y, rad.category, rng)
    r["layer"] = "radio"
    rows.append(r)
    print("  %-20s groups=%-6d NMI(cat)=%.3f (null %.3f) purity=%.3f"
          % ("session", r["n_groups"], r["nmi_category"],
             r["nmi_category_null_mean"], r["purity_category"]))

    return pd.DataFrame(rows)


def part_b(seeds: int, rng) -> pd.DataFrame:
    """Fit under each grouping. The comparison that matters is src_ip vs oracle."""
    net = load_network(feature_set="full")
    raw = aligned_metadata(len(net.y))

    X, y, cat = net.X, net.y, net.category
    groupings = {"src_ip": raw["src_ip"].to_numpy(),
                 "attack_type_ORACLE": raw["attack_type"].to_numpy()}
    # Size-matched random grouping: same group-size profile, no label alignment.
    sizes = pd.Series(groupings["src_ip"]).value_counts().to_numpy()
    fake = np.concatenate([np.full(s, i) for i, s in enumerate(sizes)])
    groupings["random_groups_sizematched"] = rng.permutation(fake)[:len(y)]

    rows = []
    for si in range(seeds):
        seed = 101 + si
        r = np.random.default_rng(seed)
        idx = np.sort(r.choice(len(y), size=min(SUBSAMPLE, len(y)), replace=False))
        Xs, ys, cs = X.iloc[idx].reset_index(drop=True), y[idx], cat[idx]

        for gname, garr in groupings.items():
            gs = garr[idx]
            sp = group_disjoint_split(ys, gs, seed=seed, n_folds=1)[0]
            sp.check_disjoint(gs)
            for proto, s in (("group_disjoint", sp),):
                tr, te = s.train_idx, s.test_idx
                if len(np.unique(ys[tr])) < 2 or len(np.unique(ys[te])) < 2:
                    continue
                for spec in LADDER:
                    if spec.key in ("stratified",):
                        continue
                    mdl = fit_model(spec.key, Xs.iloc[tr], ys[tr], 11)
                    m = detection_metrics(ys[te], predict_scores(mdl, Xs.iloc[te]), 0.5)
                    rows.append(dict(grouping=gname, protocol=proto,
                                     model=spec.key, split_seed=seed,
                                     n_test_groups=s.n_test_groups,
                                     unseen_categories=int(len(
                                         set(cs[te]) - set(cs[tr]))),
                                     **m))
                    print("  seed %d %-26s %-10s f1m=%.3f fpr=%.3f"
                          % (seed, gname, spec.key, m["f1_macro"], m["fpr"]),
                          flush=True)
        # random-split reference, once per seed
        sp = random_split(ys, np.arange(len(ys)), seed=seed, n_folds=1)[0]
        for spec in LADDER:
            if spec.key in ("stratified",):
                continue
            mdl = fit_model(spec.key, Xs.iloc[sp.train_idx], ys[sp.train_idx], 11)
            m = detection_metrics(ys[sp.test_idx],
                                  predict_scores(mdl, Xs.iloc[sp.test_idx]), 0.5)
            rows.append(dict(grouping="none", protocol="random", model=spec.key,
                             split_seed=seed, n_test_groups=0,
                             unseen_categories=0, **m))
    return pd.DataFrame(rows)


def part_c() -> pd.DataFrame:
    """Does test-fold composition explain the 0.000-0.890 FPR range?"""
    p = Path("results/EXP-002/raw/leakage_runs.csv")
    if not p.exists():
        print("EXP-002 raw results absent; skipping part C")
        return pd.DataFrame()
    d = pd.read_csv(p)
    d = d[(d.protocol == "group_disjoint") & (d.threshold == 0.5)].copy()
    d["n_benign_test"] = d.tn + d.fp
    d["benign_frac_test"] = d.n_benign_test / (d.n_benign_test + d.tp + d.fn)

    rows = []
    for (layer, model), g in d.groupby(["layer", "model"]):
        if g.fpr.std() == 0 or len(g) < 5:
            continue
        for col in ("test_prevalence", "benign_frac_test", "n_test_groups",
                    "train_prevalence", "n_benign_test"):
            if col not in g.columns:
                continue
            r, p_ = _st.pearsonr(g[col], g.fpr)
            rows.append(dict(layer=layer, model=model, predictor=col,
                             pearson_r=float(r), p=float(p_),
                             r_squared=float(r * r), n=len(g),
                             fpr_min=float(g.fpr.min()),
                             fpr_max=float(g.fpr.max()),
                             fpr_sd=float(g.fpr.std())))
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="all", choices=["a", "b", "c", "all"])
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260920)

    if args.part in ("a", "all"):
        print("=== Part A: does the grouping already encode the label? ===")
        A = part_a(rng)
        A.to_csv(OUT / "processed/grouping_alignment.csv", index=False)
        print("\n" + A[["layer", "grouping", "n_groups", "largest_group_share",
                        "nmi_category", "nmi_category_null_mean",
                        "nmi_category_sizematched_null", "purity_category",
                        "purity_binary"]].to_string(
                            index=False, float_format=lambda v: "%.4f" % v))

    if args.part in ("c", "all"):
        print("\n=== Part C: what explains the fold-to-fold FPR range? ===")
        C = part_c()
        if len(C):
            C.to_csv(OUT / "processed/fpr_vs_fold_composition.csv", index=False)
            agg = (C.groupby("predictor")
                   .agg(mean_r2=("r_squared", "mean"), max_r2=("r_squared", "max"),
                        n_sig=("p", lambda s: int((s < 0.05).sum())),
                        n=("p", "size")).reset_index()
                   .sort_values("mean_r2", ascending=False))
            print(agg.to_string(index=False, float_format=lambda v: "%.4f" % v))

    if args.part in ("b", "all"):
        print("\n=== Part B: does src_ip grouping score like grouping by attack? ===")
        B = part_b(args.seeds, rng)
        B.to_csv(OUT / "raw/grouping_performance.csv", index=False)
        s = (B.groupby(["grouping", "model"])
             .agg(f1_macro=("f1_macro", "mean"), f1_sd=("f1_macro", "std"),
                  fpr=("fpr", "mean"), recall=("recall", "mean"),
                  unseen_cat=("unseen_categories", "mean"),
                  n=("f1_macro", "size")).reset_index())
        s.to_csv(OUT / "processed/grouping_performance_summary.csv", index=False)
        print(s.to_string(index=False, float_format=lambda v: "%.4f" % v))

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-029", n_null_replicates=N_NULL, subsample=SUBSAMPLE,
        seeds=args.seeds, part=args.part,
        python=platform.python_version(), platform=platform.platform()),
        indent=2), encoding="utf-8")
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
