#!/usr/bin/env python3
"""EXP-052: every statistic the revised manuscript reports, from raw per-seed runs.

Review asked for tests the reviewed draft did not run (R2.1-R2.3, R3.2, R4,
R6.5, R6.9). They are all here, computed from committed raw outputs, and written
to results/EXP-052/processed/ for analysis/make_tables.py. Nothing is refitted.

Intervals. Every interval is reported twice:
  t   the paired t-interval over split means the draft used (D-012);
  nb  the Nadeau-Bengio corrected resampled-t interval (Machine Learning 52,
      2003): variance scaled by (1/J + n_test/n_train), because the 20 splits
      resample one population and their training sets overlap. nb is the
      PRIMARY interval in the revised paper; t is kept so the change is visible.

Operating points use POOLED confusion counts only (D-018).

Usage:  python analysis/revision_stats.py
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
OUT = RES / "EXP-052" / "processed"
NONTRIVIAL = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp"]
FLOORS = ["stratified", "majority"]
PI = 0.002
LAMBDA_B = 240_000.0
WINDOWS_PER_UE_HOUR = 225          # 3600 s / 16 s windows
MIN_RECALL = 0.10                  # reachability floor, declared


# ---------------------------------------------------------------------------
def ci(d: np.ndarray, ratio: float | None = None):
    """(mean, t_lo, t_hi, nb_lo, nb_hi, p_t, p_nb, d_z) for paired diffs d."""
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    J = len(d)
    m = float(d.mean())
    sd = float(d.std(ddof=1)) if J > 1 else float("nan")
    if J < 2 or sd == 0:
        return dict(mean=m, t_lo=m, t_hi=m, nb_lo=m, nb_hi=m, p_t=float("nan"),
                    p_nb=float("nan"), d_z=float("nan"), n=J)
    tq = stats.t.ppf(0.975, J - 1)
    se_t = sd / np.sqrt(J)
    se_nb = sd * np.sqrt(1.0 / J + (ratio if ratio is not None else 0.0))
    t_t, t_nb = m / se_t, m / se_nb
    return dict(mean=m, t_lo=m - tq * se_t, t_hi=m + tq * se_t,
                nb_lo=m - tq * se_nb, nb_hi=m + tq * se_nb,
                p_t=float(2 * stats.t.sf(abs(t_t), J - 1)),
                p_nb=float(2 * stats.t.sf(abs(t_nb), J - 1)),
                d_z=m / sd, n=J)


def holm(p: pd.Series) -> pd.Series:
    p = p.astype(float)
    order = np.argsort(p.to_numpy())
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p.iloc[i])
        adj[i] = min(running, 1.0)
    return pd.Series(adj, index=p.index)


def fair_coin_macro_f1(prev: float) -> float:
    f_att = 2 * prev * 0.5 / (prev + 0.5)
    f_ben = 2 * (1 - prev) * 0.5 / ((1 - prev) + 0.5)
    return (f_att + f_ben) / 2


def wilson(k, n, z=1.96):
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - hw) / d), min(1.0, (c + hw) / d))


def ppv(tpr, fpr, pi=PI):
    den = tpr * pi + fpr * (1 - pi)
    return tpr * pi / den if den > 0 else float("nan")


# ---------------------------------------------------------------------------
def transfer(tag: str, label: str) -> pd.DataFrame:
    r = pd.read_csv(RES / tag / "raw/runs.csv")
    src = r[r.domain == "source_heldout"].set_index(["model", "split_seed"])
    tgt = r[r.domain == "target"].set_index(["model", "split_seed"])
    ratio = float((src.n_eval / src.n_train).mean())
    maj_d = (src.f1_macro - tgt.f1_macro).xs("majority", level="model")
    strat_t = tgt.f1_macro.xs("stratified", level="model")
    prev_t = float(tgt.xs("majority", level="model").eval(
        "(tp+fn)/(tp+fn+tn+fp)").mean())
    rows = []
    for m in NONTRIVIAL + FLOORS:
        s, t = src.xs(m, level="model"), tgt.xs(m, level="model")
        d = (s.f1_macro - t.f1_macro).to_numpy()
        rec = dict(direction=label, model=m, n_seeds=len(d),
                   n_ratio_nb=ratio, target_prevalence=prev_t,
                   fair_coin_macro_f1_target=fair_coin_macro_f1(prev_t),
                   src_f1=s.f1_macro.mean(), tgt_f1=t.f1_macro.mean(),
                   src_ba=s.balanced_accuracy.mean(),
                   tgt_ba=t.balanced_accuracy.mean(),
                   src_auc=s.roc_auc.mean(), tgt_auc=t.roc_auc.mean(),
                   tgt_pr_auc=t.pr_auc.mean(),
                   tgt_fpr=t.fpr.mean(), tgt_fnr=t.fnr.mean(),
                   src_fpr=s.fpr.mean(), src_fnr=s.fnr.mean())
        for k, v in ci(d, ratio).items():
            rec[f"dF1_{k}"] = v
        for k, v in ci((s.balanced_accuracy - t.balanced_accuracy).to_numpy(),
                       ratio).items():
            rec[f"dBA_{k}"] = v
        for k, v in ci((s.roc_auc - t.roc_auc).to_numpy(), ratio).items():
            rec[f"dAUC_{k}"] = v
        # difference-in-differences against the feature-blind majority floor
        for k, v in ci(d - maj_d.to_numpy(), ratio).items():
            rec[f"did_{k}"] = v
        # target: model against the stratified floor, and BA against chance
        for k, v in ci((t.f1_macro - strat_t).to_numpy(), ratio).items():
            rec[f"vsfloor_{k}"] = v
        for k, v in ci((t.balanced_accuracy - 0.5).to_numpy(), ratio).items():
            rec[f"ba_vs_chance_{k}"] = v
        for q in ("fpr", "fnr"):
            for k, v in ci(t[q].to_numpy(), ratio).items():
                if k in ("mean", "nb_lo", "nb_hi", "t_lo", "t_hi"):
                    rec[f"tgt_{q}_{k}"] = v
        rows.append(rec)
    df = pd.DataFrame(rows)
    nt = df.model.isin(NONTRIVIAL)
    for col in ("dF1_p_nb", "dBA_p_nb", "did_p_nb", "vsfloor_p_nb",
                "ba_vs_chance_p_nb", "dF1_p_t"):
        df.loc[nt, col + "_holm"] = holm(df.loc[nt, col])
    return df


def rank_corr(df: pd.DataFrame) -> list[dict]:
    out = []
    nt = df[df.model.isin(NONTRIVIAL)]
    for metric in ("f1", "ba", "auc"):
        for subset, g in (("all six", nt), ("without MLP", nt[nt.model != "mlp"])):
            rho, p = stats.spearmanr(g[f"src_{metric}"], g[f"tgt_{metric}"])
            out.append(dict(direction=df.direction.iloc[0], metric=metric,
                            subset=subset, n=len(g), rho=float(rho), p=float(p)))
    return out


# ---------------------------------------------------------------------------
def leakage() -> pd.DataFrame:
    R = pd.read_csv(RES / "EXP-042/raw/leakage_runs_radio.csv")
    per = R.groupby(["protocol", "model", "split_seed"]).f1_macro.mean().unstack(0)
    ratio = float((R.n_test / R.n_train).mean())
    rows = []
    for m in NONTRIVIAL + FLOORS:
        g = per.xs(m, level="model")
        rec = dict(model=m, n_ratio_nb=ratio)
        for proto in ("random", "group_disjoint", "stratified_group"):
            rec[proto] = g[proto].mean()
        for a, b, key in (("random", "group_disjoint", "rg"),
                          ("random", "stratified_group", "rs"),
                          ("stratified_group", "group_disjoint", "sg")):
            for k, v in ci((g[a] - g[b]).to_numpy(), ratio).items():
                rec[f"{key}_{k}"] = v
        rows.append(rec)
    df = pd.DataFrame(rows)
    nt = df.model.isin(NONTRIVIAL)
    for key in ("rg", "rs", "sg"):
        df.loc[nt, f"{key}_p_nb_holm"] = holm(df.loc[nt, f"{key}_p_nb"])
        df.loc[nt, f"{key}_p_t_holm"] = holm(df.loc[nt, f"{key}_p_t"])
    return df


def nn_leakage_row() -> dict:
    """1-NN macro-F1 per protocol with the same paired, corrected gains as the
    models of Table V (round-2 R2: the lookup belongs in the table)."""
    N = pd.read_csv(RES / "EXP-042/raw/nn_probe_radio.csv")
    R = pd.read_csv(RES / "EXP-042/raw/leakage_runs_radio.csv")
    ratio = float((R.n_test / R.n_train).mean())
    per = N.pivot_table(index="split_seed", columns="protocol", values="nn1_f1_macro")
    rec = dict(model="nn1", n_ratio_nb=ratio,
               **{p: float(per[p].mean()) for p in per.columns})
    for a, b, key in (("random", "group_disjoint", "rg"),
                      ("random", "stratified_group", "rs")):
        for k, v in ci((per[a] - per[b]).to_numpy(), ratio).items():
            rec[f"{key}_{k}"] = v
    return rec


def nn_probe() -> pd.DataFrame:
    N = pd.read_csv(RES / "EXP-042/raw/nn_probe_radio.csv")
    return N.groupby("protocol").agg(
        nn_same_session=("nn_same_session", "mean"),
        nn_same_session_min=("nn_same_session", "min"),
        nn_same_session_max=("nn_same_session", "max"),
        nn1_f1=("nn1_f1_macro", "mean"),
        unseen_categories_max=("n_unseen_test_categories", "max"),
        test_prevalence=("test_prevalence", "mean")).reset_index()


def harmonisation() -> pd.DataFrame:
    full = pd.read_csv(RES / "EXP-047/a_to_b__transferable__source_only/raw/runs.csv")
    shr = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/runs.csv")
    shr = shr[shr.domain == "source_heldout"]
    a = full.set_index(["model", "split_seed"])
    b = shr.set_index(["model", "split_seed"])
    ratio = float((b.n_eval / b.n_train).mean())
    rows = []
    for m in NONTRIVIAL:
        rec = dict(model=m, n_features_full=int(json.loads(
            (RES / "EXP-047/a_to_b__transferable__source_only/statistics/"
             "provenance.json").read_text())["n_features"]))
        for met in ("f1_macro", "balanced_accuracy", "roc_auc"):
            fa, fb = a.xs(m, level="model")[met], b.xs(m, level="model")[met]
            rec[f"full_{met}"], rec[f"shared_{met}"] = fa.mean(), fb.mean()
            for k, v in ci((fa - fb).to_numpy(), ratio).items():
                rec[f"loss_{met}_{k}"] = v
        rows.append(rec)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def pooled(counts: pd.DataFrame, unit: str) -> tuple[pd.DataFrame, pd.DataFrame,
                                                      pd.DataFrame]:
    """Pooled operating points at tau=0.5, the pi sweep, and PPV reachability."""
    g = counts.groupby(["model", "tau"])[["tp", "fp", "tn", "fn"]].sum().reset_index()
    g["tpr"] = g.tp / (g.tp + g.fn)
    g["fpr"] = g.fp / (g.fp + g.tn)
    g["corpus_precision"] = g.tp / (g.tp + g.fp).replace(0, np.nan)
    g["ppv"] = [ppv(a, b) for a, b in zip(g.tpr, g.fpr)]
    at = g[np.isclose(g.tau, 0.5)].copy()
    lo_hi = [wilson(fp, fp + tn) for fp, tn in zip(at.fp, at.tn)]
    at["fpr_lo"], at["fpr_hi"] = zip(*lo_hi)
    at["ppv_best_case"] = [ppv(t, f) for t, f in zip(at.tpr, at.fpr_lo)]
    at["ppv_worst_case"] = [ppv(t, f) for t, f in zip(at.tpr, at.fpr_hi)]
    at["collapse"] = at.corpus_precision / at.ppv
    at["n_benign_pooled"] = at.fp + at.tn
    if unit == "window":
        at["false_alerts_per_benign_ue_hour"] = at.fpr * WINDOWS_PER_UE_HOUR
        at["fa_lo"] = at.fpr_lo * WINDOWS_PER_UE_HOUR
        at["fa_hi"] = at.fpr_hi * WINDOWS_PER_UE_HOUR
    else:
        at["false_alerts_per_1e6_benign_flows"] = at.fpr * 1e6
        at["false_alerts_per_hour_at_240k"] = at.fpr * LAMBDA_B
    sweep = []
    for pi in (1e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 5e-2, 0.1, 0.2, 0.5):
        nt = at[at.model.isin(NONTRIVIAL)]
        v = [ppv(t, f, pi) for t, f in zip(nt.tpr, nt.fpr)]
        cp = nt.corpus_precision.to_numpy()
        sweep.append(dict(pi=pi, ppv_min=min(v), ppv_max=max(v),
                          spread=max(v) / min(v),
                          collapse_mean=float(np.mean(cp / np.array(v)))))
    reach = []
    for m, gg in g.groupby("model"):
        gg = gg.sort_values("tau")
        # An operating point detecting under 10% of attacks is not a detector:
        # without this floor a threshold admitting a handful of true positives
        # and zero false positives reports PPV = 1 (declared before use).
        gg = gg[gg.tpr >= MIN_RECALL]
        if gg.empty:
            reach.append(dict(model=m, ppv_max=float("nan")))
            continue
        gg = gg.assign(ppv_worst=[ppv(t, wilson(fp, fp + tn)[1])
                                  for t, fp, tn in zip(gg.tpr, gg.fp, gg.tn)])
        i = gg.ppv.idxmax()
        rec = dict(model=m, ppv_max=gg.loc[i, "ppv"], tau_at_max=gg.loc[i, "tau"],
                   tpr_at_max=gg.loc[i, "tpr"], fpr_at_max=gg.loc[i, "fpr"],
                   fp_at_max=int(gg.loc[i, "fp"]),
                   n_benign=int(gg.loc[i, "fp"] + gg.loc[i, "tn"]),
                   ppv_worst_at_max=float(gg.loc[i, "ppv_worst"]))
        for target in (0.01, 0.05, 0.10):
            ok = gg[gg.ppv >= target]
            rec[f"tau_for_ppv_{target}"] = (float(ok.tau.min()) if len(ok)
                                            else float("nan"))
            rec[f"tpr_for_ppv_{target}"] = (float(ok.sort_values("tau").tpr.iloc[0])
                                            if len(ok) else float("nan"))
        reach.append(rec)
    return at, pd.DataFrame(sweep), pd.DataFrame(reach)


def cluster_bootstrap(by_group: pd.DataFrame, n_boot: int = 2000,
                      seed: int = 7, unit: str = "flow") -> pd.DataFrame:
    """Round-2 R1-W4: percentile intervals for pooled operating points.

    Pooled counts repeat a sample in every split seed that tests it, and the
    samples of one cluster (a radio session, a source address, a D_B capture
    file) are correlated. A Wilson interval on the pooled counts treats every
    count as independent. Here each replicate resamples the clusters AND the
    split seeds with replacement; a cluster drawn k times contributes its counts
    k times in every drawn seed that tested it. Operating points are recomputed
    from the replicate's pooled counts at every threshold.
    """
    rng = np.random.default_rng(seed)
    taus = np.sort(by_group.tau.unique())
    rows = []
    for m, g in by_group.groupby("model"):
        seeds = np.sort(g.split_seed.unique())
        groups = pd.Index(np.sort(g.group.astype(str).unique()))
        C = np.zeros((len(seeds), len(groups), len(taus), 4))
        si = np.searchsorted(seeds, g.split_seed.to_numpy())
        gi = groups.get_indexer(g.group.astype(str))
        ti = np.searchsorted(taus, g.tau.to_numpy())
        C[si, gi, ti] = g[["tp", "fp", "tn", "fn"]].to_numpy(float)
        i05 = int(np.argmin(np.abs(taus - 0.5)))
        stats_ = []
        for _ in range(n_boot):
            ws = np.bincount(rng.integers(0, len(seeds), len(seeds)), minlength=len(seeds))
            wg = np.bincount(rng.integers(0, len(groups), len(groups)), minlength=len(groups))
            T = np.einsum("s,g,sgtc->tc", ws, wg, C)
            tpr = T[:, 0] / np.maximum(T[:, 0] + T[:, 3], 1)
            fpr = T[:, 1] / np.maximum(T[:, 1] + T[:, 2], 1)
            den = tpr * PI + fpr * (1 - PI)
            pv = np.where(den > 0, tpr * PI / np.where(den > 0, den, 1), np.nan)
            ok = tpr >= MIN_RECALL
            best = np.nanmax(pv[ok]) if ok.any() else np.nan
            stats_.append((tpr[i05], fpr[i05], pv[i05], best))
        S = np.array(stats_)
        lo, hi = np.nanpercentile(S, 2.5, axis=0), np.nanpercentile(S, 97.5, axis=0)
        rec = dict(model=m, n_clusters=len(groups), n_seeds=len(seeds), n_boot=n_boot,
                   tpr_lo=lo[0], tpr_hi=hi[0], fpr_lo=lo[1], fpr_hi=hi[1],
                   ppv_lo=lo[2], ppv_hi=hi[2], best_ppv_lo=lo[3], best_ppv_hi=hi[3])
        scale = WINDOWS_PER_UE_HOUR if unit == "window" else LAMBDA_B
        rec["fa_lo"], rec["fa_hi"] = lo[1] * scale, hi[1] * scale
        rows.append(rec)
    return pd.DataFrame(rows)


def estimator_contrast(counts: pd.DataFrame) -> pd.DataFrame:
    """B-E, re-measured: pooled PPV against the mean and median over folds."""
    c = counts[np.isclose(counts.tau, 0.5)].copy()
    c["tpr"] = c.tp / (c.tp + c.fn)
    c["fpr"] = c.fp / (c.fp + c.tn)
    c["ppv_fold"] = [ppv(a, b) for a, b in zip(c.tpr, c.fpr)]
    rows = []
    for m, g in c.groupby("model"):
        tot = g[["tp", "fp", "tn", "fn"]].sum()
        rows.append(dict(model=m, folds=len(g),
                         folds_fpr_zero=int((g.fp == 0).sum()),
                         pooled=ppv(tot.tp / (tot.tp + tot.fn),
                                    tot.fp / (tot.fp + tot.tn)),
                         mean_of_folds=float(g.ppv_fold.mean()),
                         median_of_folds=float(g.ppv_fold.median())))
    df = pd.DataFrame(rows)
    nt = df[df.model.isin(NONTRIVIAL)]
    spread = dict(pooled=nt.pooled.max() / nt.pooled.min(),
                  mean=nt.mean_of_folds.max() / nt.mean_of_folds.min(),
                  median=nt.median_of_folds.max() / nt.median_of_folds.min())
    df.attrs["spread"] = spread
    return df


# ---------------------------------------------------------------------------
def drift() -> pd.DataFrame:
    C = pd.read_csv(RES / "EXP-051/processed/temporal_vs_control.csv")
    R = pd.read_csv(RES / "EXP-051/raw/drift_runs.csv", keep_default_na=False)
    nt = C[C.model.isin(NONTRIVIAL)]
    by_dir = nt.groupby("direction").agg(mean_delta=("delta", "mean"),
                                         mean_z=("z", "mean"),
                                         n_outside=("outside_control_range", "sum"),
                                         n=("delta", "size")).reset_index()
    fa = (R[R.model.isin(NONTRIVIAL)]
          .groupby(["protocol", "direction"]).false_alerts_per_hour.mean())
    by_dir["false_alerts_temporal"] = [fa.get(("temporal", d), np.nan)
                                       for d in by_dir.direction]
    by_dir["false_alerts_control"] = fa.get(("random_sessions", "n/a"), np.nan)
    per_model = nt.groupby(["model", "direction"]).agg(
        mean_delta=("delta", "mean"), min_z=("z", "min"),
        outside=("outside_control_range", "sum"), n=("delta", "size")).reset_index()
    by_dir.attrs["per_model"] = per_model
    return by_dir


def drift_v3() -> dict[str, pd.DataFrame]:
    """EXP-053 (round-2 R1-W2/W3/W6): time order with category coverage fixed,
    and the false positive rate of each benign session when it is held out."""
    base = RES / "EXP-053"
    cmp_ = pd.read_csv(base / "processed/stratified_time_vs_control.csv")
    cmp_ = cmp_[cmp_.model.isin(NONTRIVIAL)]
    tl = pd.read_csv(base / "processed/session_timeline.csv").set_index("session")
    loso = pd.read_csv(base / "raw/benign_loso_runs.csv")
    g = loso.groupby("held_out_session")
    ben = pd.DataFrame(dict(
        day=tl.loc[g.size().index, "day"].to_numpy(),
        n_ues=tl.loc[g.size().index, "n_ues"].to_numpy(),
        n_windows=g.n_windows.first(), fpr_mean=g.fpr.mean(),
        fpr_min=g.fpr.min(), fpr_max=g.fpr.max()))
    ben["false_alerts_per_benign_ue_hour"] = ben.fpr_mean * WINDOWS_PER_UE_HOUR
    ben.index.name = "session"
    audit = pd.read_csv(base / "raw/coverage_audit.csv", keep_default_na=False)
    ta = audit[audit.protocol == "temporal"]
    # EXP-051 re-expressed in balanced accuracy, for the response letter
    R = pd.read_csv(RES / "EXP-051/raw/drift_runs.csv", keep_default_na=False)
    R["balanced_accuracy"] = (R.recall + 1 - R.fpr) / 2
    old = (R[R.model.isin(NONTRIVIAL)]
           .groupby(["protocol", "direction", "train_frac"])
           [["balanced_accuracy", "f1_macro", "fpr", "train_prevalence",
             "test_prevalence"]].mean().reset_index())
    return dict(compare=cmp_, benign=ben.reset_index(), audit=ta, exp051_ba=old)


def published_ladder() -> pd.DataFrame:
    """EXP-055: the 5G-NIDD authors' pipeline down the ladder, per rung, feature
    set and model; pooled counts give operational precision at PI and false
    alerts per hour at LAMBDA_B; the deployability terms of Eq. (6) are read
    against the model's own R0 score (generalisation) and the rung's test set
    (alert term), at the model's default decision rule."""
    R = pd.read_csv(RES / "EXP-055/raw/ladder_runs.csv")
    g = R.groupby(["rung", "feature_set", "model"])
    S = g.agg(n=("accuracy", "size"), accuracy=("accuracy", "mean"),
              ba=("balanced_accuracy", "mean"), fpr=("fpr", "mean"),
              recall=("recall", "mean"), ba_clean=("clean_balanced_accuracy", "mean"),
              fpr_clean=("clean_fpr", "mean"), tp=("tp", "sum"), fp=("fp", "sum"),
              tn=("tn", "sum"), fn=("fn", "sum"), ctp=("clean_tp", "sum"),
              cfp=("clean_fp", "sum"), ctn=("clean_tn", "sum"),
              cfn=("clean_fn", "sum")).reset_index()
    for pre, (tp, fp, tn, fn) in (("", ("tp", "fp", "tn", "fn")),
                                  ("clean_", ("ctp", "cfp", "ctn", "cfn"))):
        tpr = S[tp] / (S[tp] + S[fn])
        fpr = S[fp] / (S[fp] + S[tn])
        S[pre + "pooled_tpr"], S[pre + "pooled_fpr"] = tpr, fpr
        S[pre + "ppv"] = [ppv(a, b) for a, b in zip(tpr, fpr)]
        S[pre + "fa_h"] = fpr * LAMBDA_B
    r0 = S[S.rung == "R0"].set_index("model").ba
    S["ba_drop_from_r0"] = [r0.get(m, np.nan) - b for m, b in zip(S.model, S.ba)]
    for pre in ("", "clean_"):
        S[pre + "alert_pass"] = ((S[pre + "pooled_tpr"] >= R_MIN) & (S[pre + "ppv"] >= RHO)
                                 & (S[pre + "fa_h"] <= A_MAX))
    S["gen_pass"] = S.ba_drop_from_r0 <= DELTA
    S["verdict"] = S.gen_pass & S.alert_pass
    S["verdict_clean"] = S.gen_pass & S.clean_alert_pass
    return S


def third_corpus() -> dict[str, pd.DataFrame]:
    """EXP-058: transfer from D_A and from D_B to the third corpus D_C.
    D_C has three capture files, too few to resample, so its operating points
    are pooled point estimates without a cluster interval."""
    out = {}
    tr = []
    for tag, lab in (("EXP-058/a_to_c__shared", "a_to_c"), ("EXP-058/b_to_c__shared", "b_to_c")):
        if (RES / tag / "raw/runs.csv").exists():
            tr.append(transfer(tag, lab))
            pc = pd.read_csv(RES / tag / "processed/per_category_recall.csv")
            keep = [c for c in pc.columns if not c.endswith("__n") and c not in ("split_seed",)]
            out[f"third_percat_{lab}"] = pc[keep].groupby("model").mean(numeric_only=True).reset_index()
            cnt = pd.read_csv(RES / tag / "raw/tau_counts.csv")
            cnt = cnt[cnt.domain == "target"]
            a, s, r = pooled(cnt, "flow")
            out[f"third_pooled_{lab}"] = a
            out[f"third_reach_{lab}"] = r
            out[f"third_predicate_{lab}"] = predicate(tr[-1], cnt)
    if tr:
        out["third_transfer"] = pd.concat(tr)
    ref = RES / "EXP-058/reference/processed"
    if ref.exists():
        out["third_reference"] = pd.read_csv(ref / "summary.csv")
        out["third_ceilings"] = pd.read_csv(ref / "ceilings.csv")
    return out


def target_reference() -> pd.DataFrame:
    """EXP-054: balanced accuracy of models trained and tested on D_B itself."""
    R = pd.read_csv(RES / "EXP-054/raw/runs.csv")
    # the two base-station directions differ (the flood copies are benign in
    # station 1's training labels), so they are kept apart
    R["protocol"] = np.where(R.protocol == "site_disjoint", R.split, R.protocol)
    return (R.groupby(["feature_set", "protocol", "model"])
            .agg(n=("balanced_accuracy", "size"), ba=("balanced_accuracy", "mean"),
                 ba_min=("balanced_accuracy", "min"), ba_max=("balanced_accuracy", "max"),
                 ba_clean=("clean_balanced_accuracy", "mean"),
                 fpr=("fpr", "mean"), fpr_clean=("clean_fpr", "mean"),
                 auc=("roc_auc", "mean")).reset_index())


def summarise_simple(path: Path, label: str, group="model") -> pd.DataFrame:
    r = pd.read_csv(path)
    rows = []
    for (m, dom), g in r.groupby([group, "domain"]):
        rows.append(dict(arm=label, model=m, domain=dom, n=len(g),
                         f1=g.f1_macro.mean(), ba=g.balanced_accuracy.mean(),
                         auc=g.roc_auc.mean(), pr_auc=g.pr_auc.mean(),
                         fpr=g.fpr.mean(), recall=g.recall.mean()))
    return pd.DataFrame(rows)


DELTA, R_MIN, RHO, A_MAX = 0.10, 0.50, 0.10, 200.0   # Eq. (7), declared


def predicate(fwd: pd.DataFrame, counts: pd.DataFrame) -> pd.DataFrame:
    """Eq. (7) per architecture. Every alert term is evaluated on the target.

    generalisation  upper NB bound of Delta_BA <= DELTA
    alert           some tau with R >= R_MIN, PPV >= RHO and false alerts per
                    hour at lambda_b <= A_MAX (pooled counts on D_B)
    latency         smallest budget whose p99 upper bound the radio decision
                    path (window aggregation + ONNX Runtime) meets, EXP-043
    """
    g = counts.groupby(["model", "tau"])[["tp", "fp", "tn", "fn"]].sum().reset_index()
    g["tpr"] = g.tp / (g.tp + g.fn)
    g["fpr"] = g.fp / (g.fp + g.tn)
    g["ppv"] = [ppv(a, b) for a, b in zip(g.tpr, g.fpr)]
    g["fa_h"] = g.fpr * LAMBDA_B
    lat = RES / "EXP-043/processed/budget_crossings.csv"
    L = pd.read_csv(lat) if lat.exists() else None
    rows = []
    for m in NONTRIVIAL:
        f = fwd.set_index("model").loc[m]
        gm = g[(g.model == m) & (g.tpr >= R_MIN)]
        ok = gm[(gm.ppv >= RHO) & (gm.fa_h <= A_MAX)]
        rec = dict(model=m, dBA_upper=f.dBA_nb_hi, gen_pass=bool(f.dBA_nb_hi <= DELTA),
                   best_ppv_at_rmin=float(gm.ppv.max()) if len(gm) else float("nan"),
                   min_false_alerts_at_rmin=float(gm.fa_h.min()) if len(gm) else float("nan"),
                   alert_pass=bool(len(ok)))
        if L is not None:
            r = L[(L.layer == "radio") & (L.model == m)
                  & (L.stage == "e2e_aggregate_plus_onnx")]
            rec["radio_min_budget_ms"] = (float(r.min_budget_ms_upper_ci.iloc[0])
                                          if len(r) and pd.notna(r.min_budget_ms_upper_ci.iloc[0])
                                          else float("nan"))
        rec["verdict"] = int(rec["gen_pass"] and rec["alert_pass"])
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    notes = {}

    fwd = transfer("EXP-041/a_to_b__shared", "a_to_b")
    rev = transfer("EXP-041/b_to_a__shared", "b_to_a")
    pd.concat([fwd, rev]).to_csv(OUT / "transfer_stats.csv", index=False)
    rc = rank_corr(fwd) + rank_corr(rev)
    pd.DataFrame(rc).to_csv(OUT / "rank_correlation.csv", index=False)

    leakage().to_csv(OUT / "leakage_stats.csv", index=False)
    pd.DataFrame([nn_leakage_row()]).to_csv(OUT / "leakage_nn1.csv", index=False)
    nn_probe().to_csv(OUT / "nn_probe.csv", index=False)
    harmonisation().to_csv(OUT / "harmonisation_loss.csv", index=False)

    radio = pd.read_csv(RES / "EXP-046/raw/tau_counts_radio.csv")
    at, sw, rch = pooled(radio, "window")
    at.to_csv(OUT / "pooled_radio_tau05.csv", index=False)
    sw.to_csv(OUT / "pooled_radio_pi_sweep.csv", index=False)
    rch.to_csv(OUT / "pooled_radio_reachability.csv", index=False)
    est = estimator_contrast(radio)
    est.to_csv(OUT / "estimator_contrast_radio.csv", index=False)
    notes["estimator_spread_radio"] = est.attrs["spread"]

    net = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/tau_counts.csv")
    for dom in ("source_heldout", "target"):
        a2, s2, r2 = pooled(net[net.domain == dom], "flow")
        a2.to_csv(OUT / f"pooled_network_{dom}_tau05.csv", index=False)
        s2.to_csv(OUT / f"pooled_network_{dom}_pi_sweep.csv", index=False)
        r2.to_csv(OUT / f"pooled_network_{dom}_reachability.csv", index=False)
        e2 = estimator_contrast(net[net.domain == dom])
        e2.to_csv(OUT / f"estimator_contrast_network_{dom}.csv", index=False)
        notes[f"estimator_spread_network_{dom}"] = e2.attrs["spread"]

    predicate(fwd, net[net.domain == "target"]).to_csv(OUT / "predicate.csv",
                                                        index=False)

    # ---- cluster bootstrap for pooled operating points (round-2 R1-W4) ------
    # EXP-056 re-ran EXP-046 and EXP-041 (forward) with the same seeds and kept
    # counts per cluster; its totals are checked against the originals here.
    rb = RES / "EXP-056/raw/tau_counts_radio_by_session.csv"
    if rb.exists():
        bs = pd.read_csv(rb).rename(columns={"session": "group"})
        chk = bs.groupby(["model", "split_seed", "tau"])[["tp", "fp", "tn", "fn"]].sum()
        ref = radio.set_index(["model", "split_seed", "tau"])[["tp", "fp", "tn", "fn"]]
        if not chk.sort_index().equals(ref.sort_index().astype(chk.dtypes.iloc[0])):
            raise AssertionError("EXP-056 radio counts differ from EXP-046")
        cluster_bootstrap(bs, unit="window").to_csv(OUT / "pooled_radio_bootstrap.csv",
                                                    index=False)
    nb = RES / "EXP-056/a_to_b__shared/raw/tau_counts_by_group.csv"
    if nb.exists():
        bg = pd.read_csv(nb, low_memory=False, dtype={"group": str})
        cols = ["tp", "fp", "tn", "fn"]
        for dom in ("source_heldout", "target"):
            sub = bg[bg.domain == dom]
            chk = sub.groupby(["model", "split_seed", "tau"])[cols].sum()
            ref = net[(net.domain == dom) & net.split_seed.isin(sub.split_seed.unique())]
            ref = ref.set_index(["model", "split_seed", "tau"])[cols]
            common = chk.index.intersection(ref.index)
            if len(common) != len(ref) or not (chk.loc[common].to_numpy()
                                               == ref.loc[common].to_numpy()).all():
                raise AssertionError(f"EXP-056 {dom} counts differ from EXP-041")
            if dom == "source_heldout":
                cluster_bootstrap(sub, unit="flow").to_csv(
                    OUT / "pooled_network_source_heldout_bootstrap.csv", index=False)
                continue
            # target clusters are capture files; "|c" marks the benign flows whose
            # record also occurs with an attack label (EXP-057)
            files = sub.assign(group=sub.group.str.replace("|c", "", regex=False))
            files = files.groupby(["model", "split_seed", "tau", "group"])[cols].sum().reset_index()
            cluster_bootstrap(files, unit="flow").to_csv(
                OUT / "pooled_network_target_bootstrap.csv", index=False)
            clean = sub[~sub.group.str.endswith("|c")]
            cluster_bootstrap(clean, unit="flow").to_csv(
                OUT / "pooled_network_target_clean_bootstrap.csv", index=False)
            cs = clean.groupby(["model", "split_seed", "tau"])[cols].sum().reset_index()
            a3, s3, r3 = pooled(cs, "flow")
            a3.to_csv(OUT / "pooled_network_target_clean_tau05.csv", index=False)
            s3.to_csv(OUT / "pooled_network_target_clean_pi_sweep.csv", index=False)
            r3.to_csv(OUT / "pooled_network_target_clean_reachability.csv", index=False)
            predicate(fwd, cs).to_csv(OUT / "predicate_clean.csv", index=False)
            # per-seed balanced accuracy on the clean target, and its gap
            c5 = cs[np.isclose(cs.tau, 0.5)].copy()
            c5["ba_clean"] = (c5.tp / (c5.tp + c5.fn) + c5.tn / (c5.tn + c5.fp)) / 2
            runs = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/runs.csv")
            srcr = runs[runs.domain == "source_heldout"].set_index(["model", "split_seed"])
            ratio = float((srcr.n_eval / srcr.n_train).mean())
            rows = []
            for m in NONTRIVIAL + FLOORS:
                cm = c5[c5.model == m].set_index("split_seed").ba_clean
                sm = srcr.xs(m, level="model").balanced_accuracy.loc[cm.index]
                rec = dict(model=m, tgt_ba_clean=float(cm.mean()))
                for k, v in ci((sm - cm).to_numpy(), ratio).items():
                    rec[f"dBA_clean_{k}"] = v
                rows.append(rec)
            dfc = pd.DataFrame(rows)
            ntm = dfc.model.isin(NONTRIVIAL)
            dfc.loc[ntm, "dBA_clean_p_nb_holm"] = holm(dfc.loc[ntm, "dBA_clean_p_nb"])
            dfc.to_csv(OUT / "transfer_target_clean.csv", index=False)
            # per-file false positive rate at tau 0.5, pooled over seeds
            pf = sub[np.isclose(sub.tau, 0.5)].groupby(["model", "group"])[cols].sum().reset_index()
            pf["fpr"] = pf.fp / (pf.fp + pf.tn).replace(0, np.nan)
            pf["tpr"] = pf.tp / (pf.tp + pf.fn).replace(0, np.nan)
            pf.to_csv(OUT / "target_per_file_tau05.csv", index=False)

    d = drift()
    d.to_csv(OUT / "drift_summary.csv", index=False)
    d.attrs["per_model"].to_csv(OUT / "drift_per_model.csv", index=False)
    if (RES / "EXP-053/raw/benign_loso_runs.csv").exists():
        for k, v in drift_v3().items():
            v.to_csv(OUT / f"drift_v3_{k}.csv", index=False)

    parts = [summarise_simple(RES / "EXP-041/a_to_b__shared/raw/runs.csv",
                              "supervised (shared, 18)")]
    for path, label in (
            (RES / "EXP-045/a_to_b__robust/raw/runs.csv", "robust subset (9)"),
            (RES / "EXP-049/a_to_b__shared__coral/raw/runs.csv", "CORAL"),
            (RES / "EXP-048/raw/runs.csv", "unsupervised")):
        if path.exists():
            parts.append(summarise_simple(path, label))
        else:
            print(f"  (not yet available: {path})")
    pd.concat(parts).to_csv(OUT / "arms_summary.csv", index=False)

    seq = RES / "EXP-050/raw/sequence_runs_radio.csv"
    if seq.exists():
        S = pd.read_csv(seq)
        per = S.groupby(["protocol", "model", "split_seed"]).f1_macro.mean().unstack(0)
        # same n_test/n_train convention as leakage(): mean over every run
        s_ratio = float((S.n_test / S.n_train).mean())
        rows = []
        for m in per.index.get_level_values(0).unique():
            g = per.xs(m, level="model")
            rec = dict(model=m, n_ratio_nb=s_ratio, **{p: g[p].mean() for p in g.columns})
            for k, v in ci((g["random"] - g["group_disjoint"]).to_numpy(),
                           s_ratio).items():
                rec[f"rg_{k}"] = v
            rows.append(rec)
        pd.DataFrame(rows).to_csv(OUT / "sequence_models.csv", index=False)

    if (RES / "EXP-055/raw/ladder_runs.csv").exists():
        published_ladder().to_csv(OUT / "published_ladder.csv", index=False)
    if (RES / "EXP-054/raw/runs.csv").exists():
        target_reference().to_csv(OUT / "target_reference.csv", index=False)
    for k, v in third_corpus().items():
        v.to_csv(OUT / f"{k}.csv", index=False)

    (OUT / "notes.json").write_text(json.dumps(notes, indent=2, default=float),
                                    encoding="utf-8")
    print("wrote", OUT)
    print(json.dumps(notes, indent=2, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
