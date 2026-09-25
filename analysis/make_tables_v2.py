#!/usr/bin/env python3
"""LaTeX tables for the revised manuscript (revision of 2026-09-24).

Same contract as make_tables.py: every table is a complete tabular emitted from
results/, with a provenance header, \\input at table level. One naming scheme
is used everywhere (review R1.12): LR, DT, RF, XGB, HGB, MLP, and the two
floors, Maj. and Strat.

Intervals shown are Nadeau-Bengio corrected (EXP-052); the asterisk marks
significance after Holm correction across the six non-trivial architectures.

Usage:  python analysis/make_tables_v2.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_tables import _esc, _num, _write  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
P = RES / "EXP-052" / "processed"
BS = "\\\\"
NAME = {"logreg": "LR", "tree": "DT", "rf": "RF", "xgboost": "XGB",
        "hgb": "HGB", "mlp": "MLP", "majority": r"\textit{Maj.}",
        "stratified": r"\textit{Strat.}", "iforest": "IF",
        "autoencoder": "AE", "gru": "GRU", "cnn1d": "1D-CNN"}
ORDER = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp", "stratified", "majority"]
NT = ORDER[:6]


def _ord(df, col="model"):
    df = df[df[col].isin(ORDER)].copy()
    df["_o"] = df[col].map({m: i for i, m in enumerate(ORDER)})
    return df.sort_values("_o")


def _star(p):
    return r"$^{\ast}$" if pd.notna(p) and p < 0.05 else ""


def _iv(lo, hi, d=2):
    return f"[{lo:+.{d}f}, {hi:+.{d}f}]"


# ---------------------------------------------------------------------------
def t_corpora():
    pa = json.loads((RES / "EXP-041/a_to_b__shared/statistics/provenance.json").read_text())
    pr = json.loads((RES / "EXP-042/statistics/provenance.json").read_text())["corpus"]
    a, b = pa["source"], pa["target"]
    pc_ = RES / "EXP-058/a_to_c__shared/statistics/provenance.json"
    c = json.loads(pc_.read_text())["target"] if pc_.exists() else None
    col = (lambda v: f" & {v}") if c else (lambda v: "")
    rows = [
        f"Unit & flow & 16\\,s UE window & flow{col('flow')} {BS}",
        f"Source & Zeek & KPM, 1\\,Hz & Argus{col('NFStream')} {BS}",
        f"Samples & {_num(a['n_rows'])} & {_num(pr['n_rows'])} & {_num(b['n_rows'])}"
        f"{col(_num(c['n_rows'])) if c else ''} {BS}",
        f"Features & 18 & {pr['n_features']} & 18{col(18)} {BS}",
        f"Attack prevalence & {a['attack_prevalence_pct']:.2f}\\% & "
        f"{pr['attack_prevalence_pct']:.2f}\\% & {b['attack_prevalence_pct']:.2f}\\%"
        f"{col(format(c['attack_prevalence_pct'], '.2f') + chr(92) + '%') if c else ''} {BS}",
        f"Attack categories & 5 & 5 & 2{col(3)} {BS}",
        f"Groups & {a['n_groups']} hosts & {pr['n_groups']} runs & 20 files{col('3 files')} {BS}",
        f"Role & train, test & train, test & target{col('target')} {BS}",
    ]
    _write("rev_corpora", rows, "EXP-041, EXP-042, EXP-058 provenance", "lcccc" if c else "lccc",
           r"& \DA{} network & \DA{} radio & \DB{}" + (r" & \DC{}" if c else "") + " " + BS)


def t_leakage():
    L = _ord(pd.read_csv(P / "leakage_stats.csv"))
    rows = []
    for _, r in L.iterrows():
        rows.append(
            f"{NAME[r.model]} & {r.random:.3f} & {r.group_disjoint:.3f} & "
            f"{r.stratified_group:.3f} & {r.rg_mean:+.3f}{_star(r.get('rg_p_nb_holm'))} "
            f"{_iv(r.rg_nb_lo, r.rg_nb_hi)} & {r.rs_mean:+.3f}{_star(r.get('rs_p_nb_holm'))} "
            f"{_iv(r.rs_nb_lo, r.rs_nb_hi)} {BS}")
    nn = P / "leakage_nn1.csv"
    if nn.exists():
        r = pd.read_csv(nn).iloc[0]
        rows.append(r"\midrule")
        rows.append(f"1-NN & {r.random:.3f} & {r.group_disjoint:.3f} & "
                    f"{r.stratified_group:.3f} & {r.rg_mean:+.3f} "
                    f"{_iv(r.rg_nb_lo, r.rg_nb_hi)} & {r.rs_mean:+.3f} "
                    f"{_iv(r.rs_nb_lo, r.rs_nb_hi)} {BS}")
    _write("rev_leakage", rows, "EXP-052 leakage_stats, leakage_nn1 (EXP-042)", "lccccc",
           r"Model & Random & Run-disj. & Cat.-strat. & $\Delta_{\mathrm{R-RD}}$ [95\% CI] & "
           r"$\Delta_{\mathrm{R-CS}}$ [95\% CI] " + BS)


def t_drift():
    D = pd.read_csv(P / "drift_per_model.csv")
    rows = []
    for m in NT:
        f = D[(D.model == m) & (D.direction == "forward")].iloc[0]
        r = D[(D.model == m) & (D.direction == "reverse")].iloc[0]
        rows.append(f"{NAME[m]} & {f.mean_delta:+.3f} & {int(f.outside)}/{int(f.n)} & "
                    f"{f.min_z:.1f} & {r.mean_delta:+.3f} & {int(r.outside)}/{int(r.n)} & "
                    f"{r.min_z:.1f} {BS}")
    _write("rev_drift", rows, "EXP-052 drift_per_model (EXP-051)", "lcccccc",
           r"& \multicolumn{3}{c}{Earlier $\rightarrow$ later} & "
           r"\multicolumn{3}{c}{Later $\rightarrow$ earlier} " + BS + "\n"
           r"Model & $\Delta$ & Outside & min $z$ & $\Delta$ & Outside & min $z$ " + BS)


def t_benign_sessions():
    """EXP-053 C: FPR of each benign session when it alone is held out."""
    B = pd.read_csv(P / "drift_v3_benign.csv")
    rows = [f"{int(r.session)} & {r.day:.1f} & {int(r.n_ues)} & {int(r.n_windows)} & "
            f"{r.fpr_mean:.2f} & [{r.fpr_min:.2f}, {r.fpr_max:.2f}] & "
            f"{r.false_alerts_per_benign_ue_hour:.0f} {BS}" for _, r in B.iterrows()]
    _write("rev_benign_sessions", rows, "EXP-052 drift_v3_benign (EXP-053 C)", "rcccccc",
           r"Session & Day & UEs & Windows & FPR & Range & Alerts/UE-h " + BS)


def t_time_split():
    """EXP-053 B: latest / earliest session of every category against a random
    session of every category."""
    C = pd.read_csv(P / "drift_v3_compare.csv")
    rows = []
    for m in NT:
        f = C[(C.model == m) & (C.direction == "forward")].iloc[0]
        r = C[(C.model == m) & (C.direction == "reverse")].iloc[0]
        rows.append(f"{NAME[m]} & {f.balanced_accuracy_control_mean:.3f} & "
                    f"{f.balanced_accuracy_temporal:.3f} & {100 * f.balanced_accuracy_pct_control_le:.0f} & "
                    f"{r.balanced_accuracy_temporal:.3f} & {100 * r.balanced_accuracy_pct_control_le:.0f} {BS}")
    _write("rev_time_split", rows, "EXP-052 drift_v3_compare (EXP-053 B)", "lccccc",
           r"& Control & \multicolumn{2}{c}{Latest held out} & \multicolumn{2}{c}{Earliest held out} " + BS + "\n"
           r"Model & BA & BA & \% ctrl.\ $\le$ & BA & \% ctrl.\ $\le$ " + BS)


def t_transfer(direction, name):
    T = _ord(pd.read_csv(P / "transfer_stats.csv").query("direction == @direction"))
    rows = []
    for _, r in T.iterrows():
        rows.append(
            f"{NAME[r.model]} & {r.src_f1:.3f} & {r.tgt_f1:.3f} & "
            f"{r.src_ba:.3f} & {r.tgt_ba:.3f} & "
            f"{r.dBA_mean:+.3f}{_star(r.get('dBA_p_nb_holm'))} {_iv(r.dBA_nb_lo, r.dBA_nb_hi)} & "
            f"{r.tgt_auc:.3f} & {r.did_mean:+.3f} {BS}")
    _write(name, rows, "EXP-052 transfer_stats (EXP-041)", "lccccccc",
           r"& \multicolumn{2}{c}{Macro-$F_1$} & \multicolumn{3}{c}{Balanced accuracy} & "
           r"Target & $\Delta_{F_1}$ vs. " + BS + "\n"
           r"Model & Src. & Tgt. & Src. & Tgt. & $\Delta_{\mathrm{BA}}$ [95\% CI] & "
           r"ROC-AUC & Maj. " + BS)


def t_percat():
    fa = pd.read_csv(RES / "EXP-041/a_to_b__shared/processed/per_category_recall.csv")
    fb = pd.read_csv(RES / "EXP-041/b_to_a__shared/processed/per_category_recall.csv")
    ga = fa.groupby("model")[["benign", "dos", "probe"]].mean()
    gb = fb.groupby("model")[["benign", "bruteforce", "ddos", "dos", "probe", "web"]].mean()
    rows = []
    for m in NT:
        a, b = ga.loc[m], gb.loc[m]
        rows.append(f"{NAME[m]} & {a.benign:.2f} & {a.dos:.2f} & {a.probe:.2f} & "
                    f"{b.benign:.2f} & {b.dos:.2f} & {b.probe:.2f} & {b.ddos:.2f} & "
                    f"{b.bruteforce:.2f} & {b.web:.2f} {BS}")
    _write("rev_percat", rows, "EXP-041 per_category_recall (both directions)",
           "lccc|cccccc",
           r"& \multicolumn{3}{c|}{\DA{}$\rightarrow$\DB{}} & "
           r"\multicolumn{6}{c}{\DB{}$\rightarrow$\DA{} (absent from \DB{}: DDoS, BF, web)} " + BS + "\n"
           r"Model & Ben. & DoS & Probe & Ben. & DoS & Probe & DDoS & BF & Web " + BS)


def t_arms():
    AR = pd.read_csv(P / "arms_summary.csv")
    tg = AR[AR.domain == "target"]
    sh = AR[AR.domain == "source_heldout"]
    rows = []
    arms = [("supervised (shared, 18)", "Shared space (18)"),
            ("robust subset (9)", "Exporter-robust subset (9)"),
            ("CORAL", "CORAL (reads target features)")]
    for key, label in arms:
        g = tg[tg.arm == key].set_index("model")
        s = sh[sh.arm == key].set_index("model")
        if g.empty:
            continue
        for i, m in enumerate(NT):
            if m not in g.index:
                continue
            lab = label if i == 0 else ""
            rows.append(f"{lab} & {NAME[m]} & {s.loc[m, 'ba']:.3f} & {g.loc[m, 'ba']:.3f} & "
                        f"{g.loc[m, 'auc']:.3f} & {g.loc[m, 'fpr']:.3f} {BS}")
        rows.append("\\midrule")
    g = tg[tg.arm == "unsupervised"].set_index("model")
    s = sh[sh.arm == "unsupervised"].set_index("model")
    for i, m in enumerate(["iforest", "autoencoder"]):
        if m in g.index:
            lab = "Benign-only novelty" if i == 0 else ""
            rows.append(f"{lab} & {NAME[m]} & {s.loc[m, 'ba']:.3f} & {g.loc[m, 'ba']:.3f} & "
                        f"{g.loc[m, 'auc']:.3f} & {g.loc[m, 'fpr']:.3f} {BS}")
    if rows and rows[-1] == "\\midrule":
        rows.pop()
    _write("rev_arms", rows, "EXP-052 arms_summary (EXP-041, 045, 048, 049)", "llcccc",
           r"Arm & Model & Src.\ BA & Tgt.\ BA & Tgt.\ AUC & Tgt.\ FPR " + BS)


def t_harm():
    H = pd.read_csv(P / "harmonisation_loss.csv")
    rows = [f"{NAME[r.model]} & {r.full_balanced_accuracy:.3f} & {r.shared_balanced_accuracy:.3f} & "
            f"{r.loss_balanced_accuracy_mean:+.3f} {_iv(r.loss_balanced_accuracy_nb_lo, r.loss_balanced_accuracy_nb_hi)} & "
            f"{r.full_f1_macro:.3f} & {r.shared_f1_macro:.3f} {BS}"
            for _, r in _ord(H).iterrows()]
    _write("rev_harmonisation", rows, "EXP-052 harmonisation_loss (EXP-047, EXP-041)",
           "lccccc", r"Model & BA full & BA shared & Loss [95\% CI] & $F_1$ full & $F_1$ shared " + BS)


def t_pooled():
    """Pooled operating points; FPR intervals from the cluster bootstrap
    (round-2 R1-W4) where it exists, otherwise Wilson (flagged in the log)."""
    rows = []
    blocks = [("pooled_radio_tau05.csv", r"\DA{} radio", "ue", "pooled_radio_bootstrap.csv"),
              ("pooled_network_source_heldout_tau05.csv", r"\DA{} network", "flow",
               "pooled_network_source_heldout_bootstrap.csv"),
              ("pooled_network_target_tau05.csv", r"\DB{} (transfer)", "flow",
               "pooled_network_target_bootstrap.csv")]
    if (P / "pooled_network_target_clean_tau05.csv").exists():
        blocks.append(("pooled_network_target_clean_tau05.csv",
                       r"\DB{} w/o conflicts", "flow",
                       "pooled_network_target_clean_bootstrap.csv"))
    for fname, label, unit, bfile in blocks:
        A = _ord(pd.read_csv(P / fname))
        reach = pd.read_csv(P / fname.replace("tau05", "reachability")).set_index("model")
        cb = (pd.read_csv(P / bfile).set_index("model") if (P / bfile).exists() else None)
        if cb is None:
            print(f"  t_pooled: no bootstrap for {label}, Wilson interval used")
        A = A[A.model.isin(NT + ["majority"])]
        for i, (_, r) in enumerate(A.iterrows()):
            fa = (r.false_alerts_per_benign_ue_hour if unit == "ue"
                  else r.false_alerts_per_hour_at_240k)
            best = reach.loc[r.model, "ppv_max"] if r.model in reach.index else np.nan
            best_s = "--" if not np.isfinite(best) else f"{best:.4f}"
            lo, hi = r.fpr_lo, r.fpr_hi
            if cb is not None and r.model in cb.index:
                lo, hi = cb.loc[r.model, "fpr_lo"], cb.loc[r.model, "fpr_hi"]
            lab = label if i == 0 else ""
            rows.append(f"{lab} & {NAME[r.model]} & {r.tpr:.3f} & {r.fpr:.3f} [{lo:.3f}, {hi:.3f}] & "
                        f"{r.corpus_precision:.3f} & {r.ppv:.4f} & {_num(fa)} & {best_s} {BS}")
        rows.append("\\midrule")
    rows.pop()
    _write("rev_pooled", rows, "EXP-052 pooled_* and *_bootstrap (EXP-046, EXP-041, EXP-056)",
           "llcccccc",
           r"Corpus & Model & TPR & FPR [95\% CI] & Corpus $P$ & PPV & False alerts$^{\dagger}$ & "
           r"Best PPV$^{\ddagger}$ " + BS)

def t_conflict():
    """EXP-057: flows on records that carry both labels, and the ceiling."""
    C = pd.read_csv(RES / "EXP-057/processed/ceilings.csv").set_index("feature_space")
    lab = {"native_content": "Content fields", "shared18": "Shared space",
           "native_with_seq_offset": r"Content + \texttt{Seq}, \texttt{Offset}"}
    rows = []
    for k in ("native_content", "shared18", "native_with_seq_offset"):
        r = C.loc[k]
        rows.append(f"{lab[k]} & {int(r.n_features)} & {_num(r.n_distinct)} & "
                    f"{100 * r.share_in_conflicting:.1f} & {100 * r.benign_share_in_conflicting:.1f} & "
                    f"{100 * r.attack_share_in_conflicting:.1f} & {r.ba_ceiling:.3f} {BS}")
    _write("rev_conflict", rows, "EXP-057 ceilings", "lcccccc",
           r"Features & Cols & Records & \multicolumn{3}{c}{\% in conflicting records} & BA \\" + "\n"
           r"& & & All & Benign & Attack & ceiling " + BS)


def t_third():
    """EXP-058: transfer to the third corpus D_C, per architecture."""
    f = P / "third_transfer.csv"
    if not f.exists():
        print("  skip third corpus"); return
    T = pd.read_csv(f)
    A = T[T.direction == "a_to_c"].set_index("model")
    B = T[T.direction == "b_to_c"].set_index("model")
    pa = pd.read_csv(P / "third_percat_a_to_c.csv").set_index("model")
    rows = []
    for m in NT + ["majority"]:
        if m not in A.index:
            continue
        a, c = A.loc[m], pa.loc[m]
        b = (f"{B.loc[m, 'tgt_ba']:.3f} & {B.loc[m, 'tgt_auc']:.3f}" if m in B.index else "-- & --")
        rows.append(f"{NAME[m]} & {a.src_ba:.3f} & {a.tgt_ba:.3f} & {a.tgt_auc:.3f} & "
                    f"{c.syn_flood:.2f} & {c.icmp_flood:.2f} & {c.pfcp_deletion:.2f} & "
                    f"{c.background:.2f} & {b} {BS}")
    _write("rev_third", rows, "EXP-052 third_* (EXP-058)", "lccccccccc",
           r"& \multicolumn{7}{c}{Trained on \DA{}} & \multicolumn{2}{c}{Trained on \DB{}} \\" + "\n"
           r"Model & Src.\ BA & Tgt.\ BA & AUC & SYN & ICMP & PFCP & Bkg. & Tgt.\ BA & AUC " + BS)


def t_ladder():
    """EXP-055: balanced accuracy of the 5G-NIDD authors' pipeline per rung."""
    f = P / "published_ladder.csv"
    if not f.exists():
        print("  skip ladder"); return
    L = pd.read_csv(f)
    spec = [("R0", "published_top10", "Random 70/30", "Published 10"),
            ("R1", "no_position_top10", "Random 70/30", r"No \texttt{Seq}/\texttt{Offset}"),
            ("R2", "published_top10", "Capture file", "Published 10"),
            ("R2", "no_position_top10", "Capture file", r"No \texttt{Seq}/\texttt{Offset}"),
            ("R3", "published_top10", "Base station", "Published 10"),
            ("R3", "no_position_top10", "Base station", r"No \texttt{Seq}/\texttt{Offset}")]
    rows = []
    for rung, fs, split, feats in spec:
        g = L[(L.rung == rung) & (L.feature_set == fs)].set_index("model")
        if g.empty:
            continue
        cells = [f"{g.loc[m, 'ba']:.4f}" if m in g.index else "--"
                 for m in ("dt", "rf", "knn", "nb", "mlp")]
        rf = g.loc["rf"] if "rf" in g.index else None
        tail = (f"{rf.ba_clean:.4f} & {rf.fpr:.4f}" if rf is not None else "-- & --")
        rows.append(f"{rung} & {split} & {feats} & " + " & ".join(cells) + f" & {tail} {BS}")
    _write("rev_ladder", rows, "EXP-052 published_ladder (EXP-055)", "lllccccccc",
           r"& & & \multicolumn{5}{c}{Balanced accuracy} & \multicolumn{2}{c}{RF} \\" + "\n"
           r"Rung & Split & Features & DT & RF & KNN & NB & MLP & BA$^{\ast}$ & FPR " + BS)


def t_target_ref():
    """EXP-054: models trained and tested on D_B itself."""
    f = P / "target_reference.csv"
    if not f.exists():
        print("  skip target reference"); return
    T = pd.read_csv(f)
    rows = []
    for fs, fl in (("shared18", "Shared (18)"), ("native", "Native")):
        for pr, pl in (("random", "Random"), ("file_disjoint", "Capture file"),
                       ("site1to2", "Station 1 to 2"), ("site2to1", "Station 2 to 1")):
            g = T[(T.feature_set == fs) & (T.protocol == pr)].set_index("model")
            if g.empty:
                continue
            cells = [f"{g.loc[m, 'ba']:.3f}" if m in g.index else "--" for m in NT]
            nt = g.loc[[m for m in NT if m in g.index]]
            rows.append(f"{fl} & {pl} & " + " & ".join(cells)
                        + f" & {nt.ba_clean.min():.2f}--{nt.ba_clean.max():.2f} & {int(nt.n.max())} {BS}")
    _write("rev_target_ref", rows, "EXP-052 target_reference (EXP-054)", "llcccccccc",
           r"Features & Split & LR & DT & RF & XGB & HGB & MLP & BA$^{\ast}$ & $n$ " + BS)


def t_estimator():
    E = _ord(pd.read_csv(P / "estimator_contrast_radio.csv"))
    E = E[E.model.isin(NT)]
    rows = [f"{NAME[r.model]} & {int(r.folds_fpr_zero)} & {r.pooled:.4f} & "
            f"{r.median_of_folds:.4f} & {r.mean_of_folds:.4f} {BS}" for _, r in E.iterrows()]
    _write("rev_estimator", rows, "EXP-052 estimator_contrast_radio (EXP-046)", "lcccc",
           r"Model & Folds with FP $=0$ & Pooled & Median & Mean " + BS)


def _small(v: float) -> str:
    """Round-2 R1 minor 7: plain decimals, and a bound instead of 2e-16."""
    if v < 1e-6:
        return r"$<10^{-6}$"
    if v < 1e-3:
        e = int(np.floor(np.log10(v)))
        return rf"${v / 10 ** e:.0f}\times10^{{{e}}}$"
    return f"{v:.3f}"


def t_calibration():
    C = pd.read_csv(RES / "EXP-044/raw/calibration_runs.csv")
    raw = C[C.calibrator == "raw"].set_index(["seed", "model", "domain"]).roc_auc
    dev = {}
    for cal in ("temperature", "platt", "isotonic"):
        c2 = C[C.calibrator == cal].set_index(["seed", "model", "domain"]).roc_auc
        dev[cal] = (c2 - raw).abs().groupby(level="model").max()
    tg = C[C.domain == "target"].groupby(["model", "calibrator"]).f1_macro.mean().unstack()
    rows = []
    for m in NT:
        rows.append(f"{NAME[m]} & {_small(dev['temperature'][m])} & {_small(dev['platt'][m])} & "
                    f"{_small(dev['isotonic'][m])} & {tg.loc[m, 'raw']:.3f} & "
                    f"{tg.loc[m, 'platt']:.3f} & {tg.loc[m, 'isotonic']:.3f} & "
                    f"{tg.loc[m, 'platt+prior_EM']:.3f} & {tg.loc[m, 'platt+prior_ORACLE']:.3f} {BS}")
    _write("rev_calibration", rows, "EXP-044 calibration_runs", "lcccccccc",
           r"& \multicolumn{3}{c}{max $|\Delta$ROC-AUC$|$} & \multicolumn{5}{c}{Target macro-$F_1$ at $\tau=0.5$} " + BS + "\n"
           r"Model & Temp. & Platt & Iso. & Raw & Platt & Iso. & +EM & +Oracle " + BS)


def t_sequence():
    f = P / "sequence_models.csv"
    if not f.exists():
        print("  skip sequence table"); return
    S = pd.read_csv(f)
    L = pd.read_csv(P / "leakage_stats.csv").set_index("model")
    rows = []
    for _, r in S.iterrows():
        rows.append(f"{NAME[r.model]} & {r.random:.3f} & {r.group_disjoint:.3f} & "
                    f"{r.stratified_group:.3f} & {r.rg_mean:+.3f} {_iv(r.rg_nb_lo, r.rg_nb_hi)} {BS}")
    _write("rev_sequence", rows, "EXP-052 sequence_models (EXP-050)", "lcccc",
           r"Model & Random & Run-disj. & Cat.-strat. & $\Delta_{\mathrm{R-RD}}$ [95\% CI] " + BS)


def t_predicate():
    PR = pd.read_csv(P / "predicate.csv")
    has_lat = "radio_min_budget_ms" in PR.columns
    rows = []
    for _, r in _ord(PR).iterrows():
        mk = lambda b: r"\checkmark" if b else r"$\times$"
        lat = (f"{r.radio_min_budget_ms:.0f}" if has_lat and pd.notna(r.radio_min_budget_ms)
               else "--")
        rows.append(f"{NAME[r.model]} & {r.dBA_upper:.2f} & {mk(r.gen_pass)} & "
                    f"{r.best_ppv_at_rmin:.4f} & {_num(r.min_false_alerts_at_rmin)} & "
                    f"{mk(r.alert_pass)} & {lat} & {int(r.verdict)} {BS}")
    _write("rev_predicate", rows, "EXP-052 predicate (EXP-041, EXP-043)", "lccccccc",
           r"Model & $\overline{\Delta}_{\mathrm{BA}}$ & Gen. & Best PPV & Min.\ alerts/h & Alert & "
           r"$B_{\min}$ (ms) & $\mathcal{P}$ " + BS)


def t_latency():
    import latency_outputs as lo
    if lo.available():
        lo.table(_write)
    else:
        print('  skip latency table (EXP-043 not run)')


def main() -> int:
    for fn in (t_corpora, t_leakage, t_drift, t_benign_sessions, t_time_split,
               lambda: t_transfer("a_to_b", "rev_transfer_fwd"),
               lambda: t_transfer("b_to_a", "rev_transfer_rev"), t_percat, t_harm,
               t_pooled, t_estimator, t_conflict, t_ladder, t_target_ref, t_third, t_calibration, t_sequence, t_arms, t_predicate, t_latency):
        try:
            fn()
        except FileNotFoundError as exc:
            print(f"  skip ({exc})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
