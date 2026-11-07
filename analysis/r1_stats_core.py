"""Shared statistics for revision 1 (EXP-075): counts, bootstraps, the test.

Everything here works on confusion counts (tp, fp, fn, tn) per cluster and
threshold, as stored by analysis/consolidate_transfer.py and the reference /
label-efficient runners. No model is refitted.

Conventions (declared before any revision-1 result, D-037):
  * clusters: source addresses (D_A source fold), capture files (5G-NIDD; the
    copies '5|c' belong to file 5), capture files (D_C);
  * intervals (final convention, D-037): Nadeau-Bengio corrected t-intervals
    over the 20 splits, with the test/train ratio computed from GROUP counts as
    the ratio of the total held-out to the total training groups (Reviewer 2,
    R2.4, first option). The per-split ratio varies from 0.01 to 25 on the flow
    layer, so the ratio of totals is used. The target is fixed.
  * a cluster bootstrap over target capture files was tried first and is kept
    only as a sensitivity analysis: with 20 heterogeneous, purpose-designed
    capture files and one file holding most benign errors, its distribution of
    ratio statistics (BA, FPR) is strongly shifted (the point estimate fell at
    the 0.1th percentile in one case), and resampling source addresses inside
    a split left 38% of replicates with a single class (diagnosis 2026-11-07);
  * Holm correction within a family (one metric, one comparison, six models);
  * revised deployability test (R1.7, R1.8, R2.5): each term is PASS when its
    whole interval lies on the passing side of the bound, FAIL when its whole
    interval lies on the failing side, INCONCLUSIVE otherwise. Both terms use
    the same bootstrap. The alert threshold of split j is the largest grid
    threshold whose recall on that split's held-out SOURCE fold is at least
    r_min: it is fixed without target labels. A threshold searched on the
    target is reported only as an optimistic bound.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

N_BOOT = 2000
BOOT_SEED = 20261107
PI = 0.002
LAMBDA_B = 240_000.0
DELTA = 0.10
R_MIN = 0.5
RHO = 0.1
A_MAX = 200.0
FPR_MAX = A_MAX / LAMBDA_B           # 8.33e-4: the FPR the alert bound implies
TAU_HALF = 0.5


# ------------------------------------------------------------------ basics
def ba(c: np.ndarray) -> np.ndarray:
    """Balanced accuracy from counts [..., 4] = (tp, fp, fn, tn)."""
    c = np.asarray(c, float)
    tp, fp, fn, tn = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    with np.errstate(invalid="ignore", divide="ignore"):
        return 0.5 * (tp / (tp + fn) + tn / (tn + fp))


def rates(c: np.ndarray, pi: float = PI) -> dict:
    c = np.asarray(c, float)
    tp, fp, fn, tn = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    with np.errstate(invalid="ignore", divide="ignore"):
        rec = tp / (tp + fn)
        fpr = fp / (fp + tn)
        prec = tp / (tp + fp)
        ppv = pi * rec / (pi * rec + (1 - pi) * fpr)
    return dict(recall=rec, fpr=fpr, corpus_precision=prec, ppv=ppv,
                alerts_per_h=LAMBDA_B * fpr, ba=0.5 * (rec + 1 - fpr))


def base_cluster(g: pd.Series) -> pd.Series:
    """'5|c' -> '5': the copies belong to capture file 5."""
    return g.astype(str).str.split("|").str[0]


def holm(p) -> np.ndarray:
    p = np.asarray(p, float)
    out = np.full(len(p), np.nan)
    ok = ~np.isnan(p)
    idx = np.argsort(p[ok])
    m = ok.sum()
    adj = np.minimum(1, np.maximum.accumulate((m - np.arange(m)) * p[ok][idx]))
    tmp = np.empty(m)
    tmp[idx] = adj
    out[ok] = tmp
    return out


def nb_ci(d: np.ndarray, ratio: float) -> dict:
    """Nadeau-Bengio corrected resampled-t interval for the mean of d."""
    d = np.asarray(d, float)
    d = d[~np.isnan(d)]
    J = len(d)
    m = float(d.mean())
    sd = float(d.std(ddof=1)) if J > 1 else np.nan
    if J < 2 or sd == 0:
        return dict(mean=m, nb_lo=m, nb_hi=m, p_nb=np.nan, t_lo=m, t_hi=m, p_t=np.nan, n=J)
    tq = stats.t.ppf(0.975, J - 1)
    se_nb = sd * np.sqrt(1.0 / J + ratio)
    se_t = sd / np.sqrt(J)
    return dict(mean=m, nb_lo=m - tq * se_nb, nb_hi=m + tq * se_nb,
                p_nb=float(2 * stats.t.sf(abs(m / se_nb), J - 1)),
                t_lo=m - tq * se_t, t_hi=m + tq * se_t,
                p_t=float(2 * stats.t.sf(abs(m / se_t), J - 1)), n=J)


def _z0(x: np.ndarray, point: float) -> float:
    B = len(x)
    p0 = (np.sum(x < point) + 0.5 * np.sum(x == point)) / B
    return float(stats.norm.ppf(np.clip(p0, 1 / (B + 1), B / (B + 1))))


def bc_interval(x: np.ndarray, point: float, alpha: float = 0.05):
    """Bias-corrected percentile interval (Efron 1987), no acceleration."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    z0 = _z0(x, point)
    qlo = stats.norm.cdf(2 * z0 + stats.norm.ppf(alpha / 2))
    qhi = stats.norm.cdf(2 * z0 + stats.norm.ppf(1 - alpha / 2))
    lo, hi = np.percentile(x, [100 * qlo, 100 * qhi])
    return float(lo), float(hi), z0


def boot_summary(x: np.ndarray, point: float) -> dict:
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    lo, hi, z0 = bc_interval(x, point)
    # p-value: the level at which the BC interval just reaches zero
    B = len(x)
    q0 = np.clip((np.sum(x < 0) + 0.5 * np.sum(x == 0)) / B, 1 / (B + 1), B / (B + 1))
    zx = stats.norm.ppf(q0) - 2 * z0
    p = 2 * min(stats.norm.cdf(zx), 1 - stats.norm.cdf(zx))
    return dict(point=float(point), boot_lo=lo, boot_hi=hi, p_boot=float(min(p, 1.0)),
                n_boot=int(B), bias=float(np.mean(x) - point))


# --------------------------------------------------- count array builders
def count_arrays(gc: pd.DataFrame, tau: float, splits=None, clusters=None):
    """{split: (cluster labels, counts[n_cluster, 4])} at one threshold.

    ``gc`` holds one model / domain / view; groups are merged to base clusters.
    With ``clusters`` given, every split gets the same cluster order (missing
    clusters count zero), as needed for paired resampling.
    """
    sub = gc[np.isclose(gc["tau"], tau)].copy()
    sub["cluster"] = base_cluster(sub["group"])
    agg = sub.groupby(["split_seed", "cluster"])[["tp", "fp", "fn", "tn"]].sum()
    out = {}
    for s in (splits if splits is not None else sorted(sub["split_seed"].unique())):
        if s not in agg.index.get_level_values(0):
            continue
        a = agg.loc[s]
        if clusters is not None:
            a = a.reindex(clusters, fill_value=0)
        key = int(s) if str(s).lstrip("-").isdigit() else s   # station units are strings
        out[key] = (a.index.to_numpy(), a.to_numpy(float))
    return out


def counts_by_tau(gc: pd.DataFrame) -> dict:
    """{split: (taus, clusters, counts[n_tau, n_cluster, 4])} for threshold rules."""
    sub = gc.copy()
    sub["cluster"] = base_cluster(sub["group"])
    out = {}
    for s, d in sub.groupby("split_seed"):
        p = d.groupby(["tau", "cluster"])[["tp", "fp", "fn", "tn"]].sum()
        taus = np.sort(p.index.get_level_values(0).unique().to_numpy())
        cl = np.sort(p.index.get_level_values(1).unique().to_numpy())
        full = p.reindex(pd.MultiIndex.from_product([taus, cl]), fill_value=0)
        out[int(s)] = (taus, cl, full.to_numpy(float).reshape(len(taus), len(cl), 4))
    return out


# ------------------------------------------------------------- bootstraps
def delta_ba_boot(src: dict, tgt: dict, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """Bootstrap of mean_j [BA(source fold j) - BA(target j)] (R2.4): splits and
    target capture files resampled, BC interval."""
    splits = sorted(set(src) & set(tgt))
    S = [src[s][1] for s in splits]
    T = [tgt[s][1] for s in splits]
    point = float(np.mean([ba(S[i].sum(0)) - ba(T[i].sum(0)) for i in range(len(splits))]))
    rng = np.random.default_rng(seed)
    J = len(splits)
    reps = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, J, J)
        acc = 0.0
        for i in idx:
            wt = rng.multinomial(len(T[i]), np.full(len(T[i]), 1 / len(T[i])))
            acc += ba(S[i].sum(0)) - ba(wt @ T[i])
        reps[b] = acc / J
    return boot_summary(reps, point) | dict(splits=J)


def mean_ba_boot(arrs: dict, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """Cluster bootstrap of mean_j BA(arr j) (splits and clusters resampled)."""
    splits = sorted(arrs)
    A = [arrs[s][1] for s in splits]
    point = float(np.mean([ba(a.sum(0)) for a in A]))
    rng = np.random.default_rng(seed)
    J = len(A)
    reps = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, J, J)
        reps[b] = np.mean([ba(rng.multinomial(len(A[i]), np.full(len(A[i]), 1 / len(A[i])))
                              @ A[i]) for i in idx])
    out = boot_summary(reps - 0.5, point - 0.5)       # p-value against chance
    return dict(point=point, boot_lo=out["boot_lo"] + 0.5, boot_hi=out["boot_hi"] + 0.5,
                p_vs_chance=out["p_boot"], splits=J)  # BC interval via boot_summary


def paired_ref_boot(ref: np.ndarray, tgt: dict, n_boot: int = N_BOOT,
                    seed: int = BOOT_SEED) -> dict:
    """BA(reference) - mean_j BA(transfer j) on the same clusters, files resampled
    jointly (paired) and transfer splits resampled (R2.3).

    ``ref``: counts[n_cluster, 4] in the cluster order of every ``tgt`` entry.
    """
    splits = sorted(tgt)
    T = np.stack([tgt[s][1] for s in splits])            # [J, C, 4]
    C = ref.shape[0]
    point = float(ba(ref.sum(0)) - np.mean([ba(t.sum(0)) for t in T]))
    rng = np.random.default_rng(seed)
    reps = np.empty(n_boot)
    for b in range(n_boot):
        w = rng.multinomial(C, np.full(C, 1 / C))
        idx = rng.integers(0, len(splits), len(splits))
        reps[b] = ba(w @ ref) - np.mean([ba(w @ T[i]) for i in idx])
    return boot_summary(reps, point) | dict(ref_ba=float(ba(ref.sum(0))),
                                           transfer_ba=float(np.mean([ba(t.sum(0)) for t in T])))


def pooled_boot(arrs: dict, n_boot: int = N_BOOT, seed: int = BOOT_SEED, pi: float = PI) -> dict:
    """Pooled operating point over splits and its cluster-bootstrap intervals."""
    splits = sorted(arrs)
    A = [arrs[s][1] for s in splits]
    tot = np.sum([a.sum(0) for a in A], axis=0)
    point = {k: float(v) for k, v in rates(tot, pi).items()}
    rng = np.random.default_rng(seed)
    J = len(A)
    reps = []
    for b in range(n_boot):
        idx = rng.integers(0, J, J)
        c = np.zeros(4)
        for i in idx:
            c += rng.multinomial(len(A[i]), np.full(len(A[i]), 1 / len(A[i]))) @ A[i]
        reps.append(c)
    R = rates(np.array(reps), pi)
    out = dict(point)
    for k in ("recall", "fpr", "ppv", "alerts_per_h", "corpus_precision"):
        lo, hi, _ = bc_interval(R[k], point[k])
        out[k + "_lo"], out[k + "_hi"] = lo, hi
    out["counts"] = tot.tolist()
    return out


# ------------------------------------------------------------ the test
def tri(lo: float, hi: float, bound: float, pass_if_below: bool) -> str:
    """Three-valued outcome of one condition from a 95% interval."""
    if pass_if_below:
        return "pass" if hi <= bound else ("fail" if lo > bound else "inconclusive")
    return "pass" if lo >= bound else ("fail" if hi < bound else "inconclusive")


def combine(*outcomes: str) -> str:
    if any(o == "fail" for o in outcomes):
        return "fail"
    if all(o == "pass" for o in outcomes):
        return "pass"
    return "inconclusive"


def source_thresholds(src_by_tau: dict, r_min: float = R_MIN) -> dict:
    """tau*_j: the largest grid threshold with recall >= r_min on source fold j."""
    out = {}
    for s, (taus, _cl, C) in src_by_tau.items():
        rec = rates(C.sum(1))["recall"]
        ok = np.flatnonzero(rec >= r_min)
        out[s] = float(taus[ok.max()]) if len(ok) else float(taus.min())
    return out


def alert_term(tgt_by_tau: dict, tau_star: dict, n_boot: int = N_BOOT,
               seed: int = BOOT_SEED, pi: float = PI) -> dict:
    """Pooled target operating point, each split at its own source threshold."""
    splits = sorted(set(tgt_by_tau) & set(tau_star))
    A = []
    for s in splits:
        taus, _cl, C = tgt_by_tau[s]
        k = int(np.argmin(np.abs(taus - tau_star[s])))
        A.append(C[k])                                     # [n_cluster, 4]
    res = pooled_boot({s: (None, a) for s, a in zip(splits, A)}, n_boot, seed, pi)
    res["tau_star_min"] = float(min(tau_star[s] for s in splits))
    res["tau_star_max"] = float(max(tau_star[s] for s in splits))
    rec_o = tri(res["recall_lo"], res["recall_hi"], R_MIN, pass_if_below=False)
    fpr_o = tri(res["alerts_per_h_lo"], res["alerts_per_h_hi"], A_MAX, pass_if_below=True)
    ppv_o = tri(res["ppv_lo"], res["ppv_hi"], RHO, pass_if_below=False)
    res.update(recall_outcome=rec_o, alerts_outcome=fpr_o, ppv_outcome=ppv_o,
               alert_term=combine(rec_o, fpr_o, ppv_o))
    return res


def oracle_alert(tgt_by_tau: dict, r_min: float = R_MIN, pi: float = PI) -> dict:
    """Optimistic bound: one threshold for all splits, searched on the target."""
    splits = sorted(tgt_by_tau)
    taus = tgt_by_tau[splits[0]][0]
    tot = np.sum([tgt_by_tau[s][2].sum(1) for s in splits], axis=0)   # [n_tau, 4]
    R = rates(tot, pi)
    ok = R["recall"] >= r_min
    if not ok.any():
        return dict(best_ppv=np.nan, min_alerts=np.nan, tau_best_ppv=np.nan)
    i_ppv = np.flatnonzero(ok)[np.nanargmax(R["ppv"][ok])]
    i_al = np.flatnonzero(ok)[np.nanargmin(R["alerts_per_h"][ok])]
    return dict(best_ppv=float(R["ppv"][i_ppv]), tau_best_ppv=float(taus[i_ppv]),
                min_alerts=float(R["alerts_per_h"][i_al]), tau_min_alerts=float(taus[i_al]),
                recall_at_min_alerts=float(R["recall"][i_al]))


def oracle_best_ppv_recall(tgt_by_tau: dict, r_floor: float = 0.10, pi: float = PI) -> float:
    splits = sorted(tgt_by_tau)
    tot = np.sum([tgt_by_tau[s][2].sum(1) for s in splits], axis=0)
    R = rates(tot, pi)
    ok = R["recall"] >= r_floor
    return float(np.nanmax(R["ppv"][ok])) if ok.any() else float("nan")


# ------------------------------------------------- NB versions (primary)
def nb_rate(x: np.ndarray, ratio: float) -> tuple[float, float, float]:
    """Mean of per-split rates and its NB-corrected 95% interval, clipped to [0, 1]."""
    r = nb_ci(np.asarray(x, float), ratio)
    return r["mean"], max(0.0, r["nb_lo"]), min(1.0, r["nb_hi"])


def ppv_of(rec, fpr, pi: float = PI):
    with np.errstate(invalid="ignore", divide="ignore"):
        return pi * rec / (pi * rec + (1 - pi) * fpr)


def alert_term_nb(tgt_by_tau: dict, tau_star: dict, ratio: float, pi: float = PI) -> dict:
    """Alert term at each split's source threshold, NB intervals over splits.

    Recall and FPR are averaged over splits (every split is evaluated on the
    same target flows, so this equals the pooled counts); operational precision
    and false alerts follow from the mean rates, never from averaging PPV, and
    their interval ends from the interval ends of recall and FPR (PPV rises
    with recall and falls with FPR).
    """
    splits = sorted(set(tgt_by_tau) & set(tau_star))
    rec, fpr, joint = [], [], 0
    for s in splits:
        taus, _cl, Cc = tgt_by_tau[s]
        k = int(np.argmin(np.abs(taus - tau_star[s])))
        r = rates(Cc[k].sum(0), pi)
        rec.append(r["recall"])
        fpr.append(r["fpr"])
        joint += int(r["recall"] >= R_MIN and r["alerts_per_h"] <= A_MAX and r["ppv"] >= RHO)
    rm, rlo, rhi = nb_rate(rec, ratio)
    fm, flo, fhi = nb_rate(fpr, ratio)
    out = dict(recall=rm, recall_lo=rlo, recall_hi=rhi, fpr=fm, fpr_lo=flo, fpr_hi=fhi,
               alerts_per_h=LAMBDA_B * fm, alerts_per_h_lo=LAMBDA_B * flo,
               alerts_per_h_hi=LAMBDA_B * fhi,
               ppv=float(ppv_of(rm, fm, pi)), ppv_lo=float(ppv_of(rlo, fhi, pi)),
               ppv_hi=float(ppv_of(rhi, flo, pi)) if fhi > 0 or flo > 0 else 1.0,
               tau_star_min=float(min(tau_star[s] for s in splits)),
               tau_star_max=float(max(tau_star[s] for s in splits)), splits=len(splits),
               splits_meeting_all=joint)
    if flo == 0 and rhi > 0:
        out["ppv_hi"] = 1.0
    rec_o = tri(out["recall_lo"], out["recall_hi"], R_MIN, pass_if_below=False)
    al_o = tri(out["alerts_per_h_lo"], out["alerts_per_h_hi"], A_MAX, pass_if_below=True)
    pp_o = tri(out["ppv_lo"], out["ppv_hi"], RHO, pass_if_below=False)
    out.update(recall_outcome=rec_o, alerts_outcome=al_o, ppv_outcome=pp_o,
               alert_term=combine(rec_o, al_o, pp_o))
    return out


def pooled_nb(arrs: dict, ratio: float, pi: float = PI) -> dict:
    """Operating point at one threshold: rates per split, NB intervals."""
    splits = sorted(arrs)
    R = [rates(arrs[s][1].sum(0), pi) for s in splits]
    rm, rlo, rhi = nb_rate([r["recall"] for r in R], ratio)
    fm, flo, fhi = nb_rate([r["fpr"] for r in R], ratio)
    tot = np.sum([arrs[s][1].sum(0) for s in splits], axis=0)
    pooled = rates(tot, pi)
    return dict(recall=rm, recall_lo=rlo, recall_hi=rhi, fpr=fm, fpr_lo=flo, fpr_hi=fhi,
                alerts_per_h=LAMBDA_B * fm, alerts_per_h_lo=LAMBDA_B * flo,
                alerts_per_h_hi=LAMBDA_B * fhi,
                ppv=float(ppv_of(rm, fm, pi)), ppv_lo=float(ppv_of(rlo, fhi, pi)),
                ppv_hi=float(ppv_of(rhi, flo, pi)) if flo > 0 else 1.0,
                corpus_precision=float(pooled["corpus_precision"]),
                pooled_fpr=float(pooled["fpr"]), pooled_recall=float(pooled["recall"]))
