#!/usr/bin/env python3
"""EXP-075: every statistic of the revised manuscript (revision 1).

Reads the consolidated transfer experiments, the in-target references, the
label-efficient arm, the radio comparison and the diagnostics, and writes
results/EXP-075/processed/*.csv plus results/EXP-075/numbers.json, from which
analysis/make_assets_r1.py builds the macros, tables and figures.

Conventions: analysis/r1_stats_core.py (D-037). Sections that lack their input
are skipped with a message, so the script can be run while experiments finish.

Usage:  python analysis/revision_stats_r1.py [--boot 2000]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import r1_stats_core as C  # noqa: E402

RES = ROOT / "results"
OUT = RES / "EXP-075"
RATIO_G = float("nan")
NONTRIVIAL = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp"]
LABEL = dict(logreg="LR", tree="DT", rf="RF", xgboost="XGB", hgb="HGB", mlp="MLP",
             majority="Maj.", stratified="Strat.", dann="DANN")
NUM: dict = {}


def note(k, v):
    NUM[k] = v


def load_consolidated(exp: str, tag: str):
    d = RES / exp / f"consolidated__{tag}"
    if not (d / "runs.csv").exists():
        print(f"  [skip] {exp}/{tag}: not consolidated yet")
        return None, None
    return pd.read_csv(d / "runs.csv"), pd.read_parquet(d / "tau_counts_by_group.parquet")


def runner_ratio(exp: str, tag: str) -> float:
    """Mean n_test/n_train of the source fold in flows, from the runners' logs."""
    vals = []
    for p in (RES / exp).glob(tag + "*/raw/runs.csv"):
        r = pd.read_csv(p)
        r = r[(r.domain == "source_heldout") & (r.model == "logreg")]
        vals.append(r.assign(q=r.n_eval / r.n_train)[["split_seed", "q"]])
    if not vals:
        return float("nan")
    return float(pd.concat(vals).drop_duplicates("split_seed").q.mean())


def group_ratio(exp: str, tag: str) -> float:
    """Total held-out over total training groups of the source splits (D-037)."""
    vals = []
    for q in (RES / exp).glob(tag + "*/raw/runs.csv"):
        r = pd.read_csv(q)
        if "n_test_groups" not in r:
            continue
        r = r[(r.domain == "source_heldout")]
        vals.append(r[["split_seed", "n_train_groups", "n_test_groups"]])
    if not vals:
        return float("nan")
    v = pd.concat(vals).drop_duplicates("split_seed")
    return float(v.n_test_groups.sum() / v.n_train_groups.sum())


def clusters_of(gc: pd.DataFrame):
    cl = C.base_cluster(gc["group"]).unique()
    try:
        return sorted(cl, key=int)
    except ValueError:
        return sorted(cl)


# ---------------------------------------------------------------- transfer
def transfer_section(exp, tag, targets, label, nboot):
    runs, g = load_consolidated(exp, tag)
    if runs is None:
        return None
    ratio_f = runner_ratio(exp, tag)
    ratio = group_ratio(exp, tag)
    note(f"{label}_nb_ratio_flows", ratio_f)
    note(f"{label}_nb_ratio_groups", ratio)
    rows, ops, tests = [], [], []
    for m in NONTRIVIAL:
        gs = g[(g.model == m) & (g.domain == "source_heldout")]
        if gs.empty:
            continue
        src = C.count_arrays(gs, C.TAU_HALF)
        src_bt = C.counts_by_tau(gs)
        tau_star = C.source_thresholds(src_bt)
        src_ba = runs[(runs.model == m) & (runs.domain == "source_heldout")
                      & (runs.view == "all")].set_index("split_seed").balanced_accuracy
        for t in targets:
            views = ["all", "clean", "relab"] if t in ("b", "bz") else ["all"]
            for v in views:
                gt = g[(g.model == m) & (g.domain == t) & (g.view == v)]
                if gt.empty:
                    continue
                cl = clusters_of(gt)
                tgt = C.count_arrays(gt, C.TAU_HALF, clusters=cl)
                r_t = runs[(runs.model == m) & (runs.domain == t) & (runs.view == v)] \
                    .set_index("split_seed")
                d = (src_ba - r_t.balanced_accuracy).dropna()
                nb = C.nb_ci(d.to_numpy(), ratio)
                nbf = C.nb_ci(d.to_numpy(), ratio_f)
                chn = C.nb_ci(r_t.balanced_accuracy.loc[d.index].to_numpy() - 0.5, ratio)
                use_boot = len(cl) >= 10            # sensitivity only (D-037)
                bt = C.delta_ba_boot(src, tgt, nboot) if use_boot else {}
                rows.append(dict(
                    experiment=exp, target=t, view=v, model=m, splits=len(d),
                    src_ba=float(src_ba.loc[d.index].mean()),
                    tgt_ba=float(r_t.balanced_accuracy.loc[d.index].mean()),
                    tgt_auc=float(r_t.roc_auc.loc[d.index].mean()),
                    tgt_fpr=float(r_t.fpr.loc[d.index].mean()) if "fpr" in r_t else np.nan,
                    tgt_recall=float(r_t.recall.loc[d.index].mean()) if "recall" in r_t else np.nan,
                    d_ba=nb["mean"], nb_lo=nb["nb_lo"], nb_hi=nb["nb_hi"], p_nb=nb["p_nb"],
                    nbf_lo=nbf["nb_lo"], nbf_hi=nbf["nb_hi"], p_nbf=nbf["p_nb"],
                    t_lo=nb["t_lo"], t_hi=nb["t_hi"], p_t=nb["p_t"],
                    sens_boot_lo=bt.get("boot_lo", np.nan), sens_boot_hi=bt.get("boot_hi", np.nan),
                    sens_boot_bias=bt.get("bias", np.nan),
                    tgt_ba_lo=chn["nb_lo"] + 0.5, tgt_ba_hi=chn["nb_hi"] + 0.5,
                    p_vs_chance=chn["p_nb"], ratio_groups=ratio, ratio_flows=ratio_f,
                    splits_positive=int((d > 0).sum())))
                if t in ("b", "bz", "a"):
                    op = C.pooled_nb(tgt, ratio)
                    tbt = C.counts_by_tau(gt)
                    orc = C.oracle_alert(tbt)
                    best10 = C.oracle_best_ppv_recall(tbt, 0.10)
                    ops.append(dict(experiment=exp, target=t, view=v, model=m,
                                    **{k: v2 for k, v2 in op.items() if k != "counts"},
                                    oracle_best_ppv_r50=orc["best_ppv"],
                                    oracle_min_alerts_r50=orc["min_alerts"],
                                    oracle_best_ppv_r10=best10))
                    at = C.alert_term_nb(tbt, tau_star, ratio)
                    gen = C.tri(nb["nb_lo"], nb["nb_hi"], C.DELTA, pass_if_below=True)
                    tests.append(dict(
                        experiment=exp, target=t, view=v, model=m,
                        d_ba=nb["mean"], d_ba_lo=nb["nb_lo"], d_ba_hi=nb["nb_hi"],
                        generalization=gen, **{f"alert_{k}": v2 for k, v2 in at.items()
                                               if k != "counts"},
                        verdict=C.combine(gen, at["alert_term"]),
                        oracle_best_ppv=orc["best_ppv"], oracle_min_alerts=orc["min_alerts"],
                        oracle_alert_pass=bool(orc["best_ppv"] >= C.RHO and
                                               orc["min_alerts"] <= C.A_MAX)))
        # source fold operating point
        op = C.pooled_nb(src, ratio)
        ops.append(dict(experiment=exp, target="source_heldout", view="all", model=m,
                        **{k: v2 for k, v2 in op.items() if k != "counts"},
                        oracle_best_ppv_r10=C.oracle_best_ppv_recall(src_bt, 0.10)))
        print(f"  {exp} {m}: done", flush=True)
    T = pd.DataFrame(rows)
    for (t, v), idx in T.groupby(["target", "view"]).groups.items():
        T.loc[idx, "p_nb_holm"] = C.holm(T.loc[idx, "p_nb"])
        T.loc[idx, "p_nbf_holm"] = C.holm(T.loc[idx, "p_nbf"])
        T.loc[idx, "p_chance_holm"] = C.holm(T.loc[idx, "p_vs_chance"])
    T.to_csv(OUT / f"processed/transfer__{label}.csv", index=False)
    pd.DataFrame(ops).to_csv(OUT / f"processed/operating__{label}.csv", index=False)
    pd.DataFrame(tests).to_csv(OUT / f"processed/test__{label}.csv", index=False)
    # trivial baselines (for the tables)
    tr = runs[runs.model.isin(["majority", "stratified"])]
    tr.groupby(["model", "domain"]).balanced_accuracy.mean().reset_index() \
        .to_csv(OUT / f"processed/trivial__{label}.csv", index=False)
    return T


def zeek_vs_argus(nboot):
    """Paired: the same trained models scored on Argus and on Zeek 5G-NIDD."""
    runs, g = load_consolidated("EXP-064", "a_to_b_bz_c__shared")
    if runs is None:
        return
    rows = []
    for m in NONTRIVIAL:
        for v in ("all", "clean", "relab"):
            a = runs[(runs.model == m) & (runs.domain == "b") & (runs.view == v)].set_index("split_seed")
            z = runs[(runs.model == m) & (runs.domain == "bz") & (runs.view == v)].set_index("split_seed")
            d = (z.balanced_accuracy - a.balanced_accuracy).dropna()
            ga = g[(g.model == m) & (g.domain == "b") & (g.view == v)]
            gz = g[(g.model == m) & (g.domain == "bz") & (g.view == v)]
            cl = sorted(set(clusters_of(ga)) & set(clusters_of(gz)), key=int)
            A = C.count_arrays(ga, C.TAU_HALF, clusters=cl)
            Z = C.count_arrays(gz, C.TAU_HALF, clusters=cl)
            rng = np.random.default_rng(C.BOOT_SEED)
            sp = sorted(set(A) & set(Z))
            reps = []
            for _ in range(nboot):
                w = rng.multinomial(len(cl), np.full(len(cl), 1 / len(cl)))
                idx = rng.integers(0, len(sp), len(sp))
                reps.append(np.mean([C.ba(w @ Z[sp[i]][1]) - C.ba(w @ A[sp[i]][1]) for i in idx]))
            bs = C.boot_summary(np.array(reps), float(d.mean()))
            nb = C.nb_ci(d.to_numpy(), group_ratio("EXP-064", "a_to_b_bz_c__shared"))
            rows.append(dict(model=m, view=v, argus_ba=float(a.balanced_accuracy.loc[d.index].mean()),
                             zeek_ba=float(z.balanced_accuracy.loc[d.index].mean()),
                             diff=float(d.mean()), nb_lo=nb["nb_lo"], nb_hi=nb["nb_hi"], p_nb=nb["p_nb"],
                             sens_boot_lo=bs["boot_lo"], sens_boot_hi=bs["boot_hi"],
                             zeek_fpr=float(z.fpr.loc[d.index].mean()),
                             argus_fpr=float(a.fpr.loc[d.index].mean())))
    pd.DataFrame(rows).to_csv(OUT / "processed/zeek_vs_argus.csv", index=False)


# -------------------------------------------------------------- references
def load_reference(design: str, labels: str):
    runs, gcs = [], []
    for d in sorted((RES / "EXP-068").glob(f"{design}__{labels}*")):
        if (d / "raw/runs.csv").exists():
            runs.append(pd.read_csv(d / "raw/runs.csv"))
        if (d / "raw/tau_counts_by_group.csv").exists():
            gcs.append(pd.read_csv(d / "raw/tau_counts_by_group.csv"))
    if not runs:
        return None, None
    return (pd.concat(runs).drop_duplicates(["unit", "model", "view"]),
            pd.concat(gcs) if gcs else None)


def references_section(nboot):
    global RATIO_G
    RATIO_G = group_ratio("EXP-064", "a_to_b_bz_c__shared")
    runs_t, g_t = load_consolidated("EXP-064", "a_to_b_bz_c__shared")
    out, matched = [], []
    # random split references: mean over 20 seeds, NB interval (test/train 0.25)
    r, _ = load_reference("random", "clean")
    if r is not None:
        for m in NONTRIVIAL:
            x = r[(r.model == m)].balanced_accuracy.to_numpy()
            nb = C.nb_ci(x - 0.5, 0.25)
            out.append(dict(design="random", labels="clean", view="clean", model=m,
                            ba=float(x.mean()), lo=nb["nb_lo"] + 0.5, hi=nb["nb_hi"] + 0.5,
                            units=len(x)))
    # leave-one-capture-file-out: pooled over all flows, cluster bootstrap
    for labels, view in (("clean", "clean"), ("relab", "relab")):
        r, gc = load_reference("lofo", labels)
        if r is None or gc is None:
            continue
        units = r.unit.nunique()
        for m in NONTRIVIAL:
            sub = gc[(gc.model == m) & (gc.view == view) & np.isclose(gc.tau, C.TAU_HALF)].copy()
            sub["cluster"] = C.base_cluster(sub.group)
            ref = sub.groupby("cluster")[["tp", "fp", "fn", "tn"]].sum()
            cl = sorted(ref.index, key=int)
            ref = ref.reindex(cl, fill_value=0).to_numpy(float)
            ref_ba = float(C.ba(ref.sum(0)))
            out.append(dict(design="lofo", labels=labels, view=view, model=m,
                            ba=ref_ba, lo=np.nan, hi=np.nan, units=units))
            if g_t is not None and units == 20:
                gt = g_t[(g_t.model == m) & (g_t.domain == "b") & (g_t.view == view)]
                tgt = C.count_arrays(gt, C.TAU_HALF, clusters=cl)
                ba_t = np.array([C.ba(tgt[s][1].sum(0)) for s in sorted(tgt)])
                nb = C.nb_ci(ref_ba - ba_t, RATIO_G)
                pr = C.paired_ref_boot(ref, tgt, nboot)          # sensitivity only
                matched.append(dict(model=m, view=view, point=nb["mean"], lo=nb["nb_lo"],
                                    hi=nb["nb_hi"], p_nb=nb["p_nb"], ref_ba=ref_ba,
                                    transfer_ba=float(ba_t.mean()),
                                    sens_boot_lo=pr["boot_lo"], sens_boot_hi=pr["boot_hi"]))
    # station references: mean over seeds, cluster bootstrap over test files
    for labels in ("clean", "relab"):
        r, gc = load_reference("station", labels)
        if r is None or gc is None:
            continue
        for direction in ("s1_to_s2", "s2_to_s1"):
            for view in (("clean", "relab") if labels == "clean" else ("relab",)):
                for m in NONTRIVIAL:
                    sub = gc[(gc.model == m) & (gc.view == view) & gc.unit.str.startswith(direction)]
                    if sub.empty:
                        continue
                    sub = sub.rename(columns={"unit": "split_seed"})
                    arr = C.count_arrays(sub, C.TAU_HALF)
                    x = np.array([C.ba(arr[k][1].sum(0)) for k in sorted(arr)])
                    nb = C.nb_ci(x - 0.5, 0.0)          # training samples only: t-interval
                    out.append(dict(design=direction, labels=labels, view=view, model=m,
                                    ba=float(x.mean()), lo=nb["nb_lo"] + 0.5,
                                    hi=nb["nb_hi"] + 0.5, units=len(arr)))
    pd.DataFrame(out).to_csv(OUT / "processed/references.csv", index=False)
    mt = pd.DataFrame(matched)
    if len(mt):
        for v, idx in mt.groupby("view").groups.items():
            mt.loc[idx, "p_holm"] = C.holm(mt.loc[idx, "p_nb"])
    mt.to_csv(OUT / "processed/reference_vs_transfer.csv", index=False)


# ------------------------------------------------------------ simple arms
def arm_summary(exp, tag, label, target="b"):
    runs, _ = load_consolidated(exp, tag)
    if runs is None:
        return
    rows = []
    for m in sorted(runs.model.unique()):
        r = runs[runs.model == m]
        row = dict(arm=label, model=m, splits=r.split_seed.nunique(),
                   src_ba=r[(r.domain == "source_heldout")].balanced_accuracy.mean())
        for v in ("all", "clean", "relab"):
            rv = r[(r.domain == target) & (r.view == v)]
            if len(rv):
                row[f"tgt_ba_{v}"] = rv.balanced_accuracy.mean()
                row[f"tgt_auc_{v}"] = rv.roc_auc.mean()
                row[f"tgt_fpr_{v}"] = rv.fpr.mean()
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / f"processed/arm__{label}.csv", index=False)
    diag = RES / exp / tag / "raw/adaptation_diagnostics.csv"
    ds = [pd.read_csv(p) for p in (RES / exp).glob(tag + "*/raw/adaptation_diagnostics.csv")]
    if ds:
        pd.concat(ds).to_csv(OUT / f"processed/arm_diag__{label}.csv", index=False)


# ------------------------------------------------------------------ radio
def radio_section():
    p = RES / "EXP-070/raw/leakage_runs.csv"
    if not p.exists():
        print("  [skip] radio: EXP-070 not finished")
        return
    R = pd.read_csv(p)
    N = pd.read_csv(RES / "EXP-070/raw/nn_probe.csv")
    rows = []
    for gname, Rg in R.groupby("grouping"):
        per = Rg.groupby(["protocol", "model", "split_seed"]).f1_macro.mean().unstack("protocol")
        gd = Rg[Rg.protocol == "group_disjoint"].drop_duplicates("split_seed")
        # ratio of totals, as for the flow splits (D-037)
        r_groups = float(gd.n_test_groups.sum() / gd.n_train_groups.sum())
        r_windows = float(gd.n_test.sum() / gd.n_train.sum())
        note(f"radio_ratio_groups_{gname}", r_groups)
        note(f"radio_ratio_windows_{gname}", r_windows)
        for comp, other in (("R-SD", "group_disjoint"), ("R-CS", "stratified_group")):
            for m in ["majority", "stratified"] + NONTRIVIAL:
                d = (per.loc[m]["random"] - per.loc[m][other]).to_numpy()
                a = C.nb_ci(d, r_groups)
                b = C.nb_ci(d, r_windows)
                rows.append(dict(grouping=gname, comparison=comp, model=m,
                                 random=float(per.loc[m]["random"].mean()),
                                 other=float(per.loc[m][other].mean()),
                                 gain=a["mean"], lo_groups=a["nb_lo"], hi_groups=a["nb_hi"],
                                 p_groups=a["p_nb"], lo_windows=b["nb_lo"], hi_windows=b["nb_hi"],
                                 p_windows=b["p_nb"], p_t=a["p_t"],
                                 splits_positive=int((d > 0).sum()),
                                 ratio_groups=r_groups, ratio_windows=r_windows))
            # across-architecture mean gain
            avg = (per["random"] - per[other]).unstack("model")[NONTRIVIAL].mean(axis=1).to_numpy()
            a = C.nb_ci(avg, r_groups)
            b = C.nb_ci(avg, r_windows)
            rows.append(dict(grouping=gname, comparison=comp, model="average", gain=a["mean"],
                             lo_groups=a["nb_lo"], hi_groups=a["nb_hi"], p_groups=a["p_nb"],
                             lo_windows=b["nb_lo"], hi_windows=b["nb_hi"], p_windows=b["p_nb"],
                             p_t=a["p_t"], ratio_groups=r_groups, ratio_windows=r_windows))
    T = pd.DataFrame(rows)
    for (gname, comp), idx in T[T.model.isin(NONTRIVIAL)].groupby(["grouping", "comparison"]).groups.items():
        T.loc[idx, "p_groups_holm"] = C.holm(T.loc[idx, "p_groups"])
        T.loc[idx, "p_windows_holm"] = C.holm(T.loc[idx, "p_windows"])
    T.to_csv(OUT / "processed/radio_protocols.csv", index=False)
    nn = N.groupby(["grouping", "protocol"])[["nn_same_group", "nn1_f1_macro"]].agg(["mean", "min", "max"])
    nn.to_csv(OUT / "processed/radio_nn.csv")


# ---------------------------------------------------------- label-efficient
def label_efficient_section(nboot):
    dirs = sorted((RES / "EXP-069").glob("label_efficient*"))
    runs = [pd.read_csv(d / "raw/runs.csv") for d in dirs if (d / "raw/runs.csv").exists()]
    if not runs:
        print("  [skip] label-efficient: not run yet")
        return
    R = pd.concat(runs).drop_duplicates(["k", "draw", "variant", "model", "domain"])
    S = pd.concat([pd.read_csv(d / "raw/tau_counts.csv") for d in dirs
                   if (d / "raw/tau_counts.csv").exists()])
    rows = []
    for (k, variant, m), rk in R.groupby(["k", "variant", "model"]):
        src = rk[rk.domain == "source_heldout"]
        for dom in ("target_relab", "target_clean"):
            rt = rk[rk.domain == dom]
            if rt.empty:
                continue
            # source-chosen threshold per draw, then target counts at it
            fprs, recs, als = [], [], []
            for dr in rt.draw.unique():
                ss = S[(S.k == k) & (S.variant == variant) & (S.model == m) & (S.draw == dr)]
                s_src = ss[ss.domain == "source_heldout"].sort_values("tau")
                s_tgt = ss[ss.domain == dom].sort_values("tau")
                if variant == "target-only":
                    # no source fold is relevant: threshold 0.5
                    tau = 0.5
                else:
                    rec = s_src.tp / (s_src.tp + s_src.fn)
                    ok = s_src.tau[rec >= C.R_MIN]
                    tau = float(ok.max()) if len(ok) else 0.5
                row = s_tgt.iloc[int(np.argmin(np.abs(s_tgt.tau.to_numpy() - tau)))]
                c = row[["tp", "fp", "fn", "tn"]].to_numpy(float)
                rr = C.rates(c)
                fprs.append(rr["fpr"]); recs.append(rr["recall"]); als.append(rr["alerts_per_h"])
            rows.append(dict(k=k, variant=variant, model=m, view=dom.split("_")[1],
                             draws=rt.draw.nunique(),
                             tgt_ba=rt.balanced_accuracy.mean(), tgt_ba_min=rt.balanced_accuracy.min(),
                             tgt_ba_max=rt.balanced_accuracy.max(),
                             tgt_auc=rt.roc_auc.mean(), tgt_fpr05=rt.fpr.mean(),
                             src_ba=src.balanced_accuracy.mean() if len(src) else np.nan,
                             fpr_at_tau_star=float(np.mean(fprs)), recall_at_tau_star=float(np.mean(recs)),
                             alerts_at_tau_star=float(np.mean(als)),
                             alerts_at_tau_star_min=float(np.min(als)),
                             draws_meeting_alert_bound=int(np.sum((np.array(als) <= C.A_MAX)
                                                                  & (np.array(recs) >= C.R_MIN)))))
    pd.DataFrame(rows).to_csv(OUT / "processed/label_efficient.csv", index=False)


# ------------------------------------------------------------ sample size
def sample_size_section():
    """EXP-071: target BA against the size of the source sample (R2.8)."""
    rows = []
    for n in (150_000, 300_000, 600_000, 1_640_182):
        runs, _ = load_consolidated("EXP-071", f"a_to_b__shared__n{n}")
        if runs is None:
            continue
        r = runs[(runs.domain == "b")]
        for (m, v), x in r.groupby(["model", "view"]):
            rows.append(dict(n=n, model=m, view=v, splits=x.split_seed.nunique(),
                             tgt_ba=float(x.balanced_accuracy.mean())))
        s = runs[runs.domain == "source_heldout"].groupby("model").balanced_accuracy.mean()
        for m, val in s.items():
            rows.append(dict(n=n, model=m, view="source", splits=5, tgt_ba=float(val)))
    if not rows:
        print("  [skip] sample size: not run yet")
        return
    S = pd.DataFrame(rows)
    ref = S[S.n == 300_000].set_index(["model", "view"]).tgt_ba
    S["abs_change_vs_300k"] = [abs(t - ref.get((m, v), np.nan)) for t, m, v in
                               zip(S.tgt_ba, S.model, S.view)]
    S.to_csv(OUT / "processed/sample_size_all.csv", index=False)
    # the paper's statement concerns the target, clean and all flows
    S[S.view.isin(["clean", "all"]) & (S.n != 300_000)].to_csv(
        OUT / "processed/sample_size.csv", index=False)


# ----------------------------------------------------------- diagnostics
def diagnostics_section():
    for name in ("argus_corrected", "zeek"):
        d = RES / "EXP-074" / name / "processed"
        if (d / "domain_classifier.csv").exists():
            dc = pd.read_csv(d / "domain_classifier.csv")
            fs = pd.read_csv(d / "feature_shift.csv")
            note(f"dom_{name}", dc.set_index("feature_set").balanced_accuracy.to_dict())
            note(f"w1_{name}", dict(robust=float(fs[fs.robust].w1_source_quantile.mean()),
                                    nonrobust=float(fs[~fs.robust].w1_source_quantile.mean()),
                                    all=float(fs.w1_source_quantile.mean())))
    for f in ("EXP-072/summary.json", "EXP-072/pairs.json", "EXP-072/corrected_labels/README.json",
              "EXP-073/summary.json"):
        p = RES / f
        if p.exists():
            note(f.replace("/", "__").replace(".json", ""), json.loads(p.read_text()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=C.N_BOOT)
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    (OUT / "processed").mkdir(parents=True, exist_ok=True)
    want = lambda s: a.only is None or s in a.only  # noqa: E731
    if want("transfer"):
        transfer_section("EXP-064", "a_to_b_bz_c__shared", ["b", "bz", "c"], "shared", a.boot)
        zeek_vs_argus(a.boot)
    if want("robust"):
        transfer_section("EXP-065", "a_to_b_bz_c__robust", ["b", "bz", "c"], "robust", a.boot)
    if want("reverse"):
        transfer_section("EXP-067", "b_to_a_c__shared", ["a", "c"], "reverse", a.boot)
    if want("arms"):
        arm_summary("EXP-064", "a_to_b_bz_c__shared", "shared")
        arm_summary("EXP-065", "a_to_b_bz_c__robust", "robust")
        arm_summary("EXP-066", "a_to_b__shared__coral", "coral")
        arm_summary("EXP-069", "a_to_b__shared__iw", "iw")
        arm_summary("EXP-069", "a_to_b__shared__dann", "dann")
    if want("references"):
        references_section(a.boot)
    if want("radio"):
        radio_section()
    if want("label_efficient"):
        label_efficient_section(a.boot)
    if want("sample_size"):
        sample_size_section()
    diagnostics_section()
    prev = json.loads((OUT / "numbers.json").read_text()) if (OUT / "numbers.json").exists() else {}
    prev.update(NUM)
    (OUT / "numbers.json").write_text(json.dumps(prev, indent=2, default=float), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
