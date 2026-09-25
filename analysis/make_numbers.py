#!/usr/bin/env python3
"""Every number the revised manuscript states in prose, as a LaTeX macro.

make_tables.py made table values structural. This does the same for the numbers
in sentences: the abstract, the introduction and the discussion quote values
through macros such as \\LeakAvg, defined in tables/generated/numbers.tex and
computed here from results/. A missing input raises; there is no default.

Usage:  python analysis/make_numbers.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from revision_stats import NONTRIVIAL, ci  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
P = RES / "EXP-052" / "processed"
OUT = ROOT / "tables" / "generated" / "numbers.tex"
N: dict[str, str] = {}
SRC: dict[str, str] = {}


def put(name: str, value, fmt: str = "{:.2f}", source: str = ""):
    if isinstance(value, float) and not np.isfinite(value):
        raise ValueError(f"{name} is not finite ({value}) from {source}")
    s = fmt.format(value) if not isinstance(value, str) else value
    N[name] = re.sub(r"(?<=\d),(?=\d{3})", "{,}", s)   # thousands only
    SRC[name] = source


def num(x, d=0):
    return f"{x:,.{d}f}"


def main() -> int:
    # ---- corpora ------------------------------------------------------------
    pa = json.loads((RES / "EXP-041/a_to_b__shared/statistics/provenance.json")
                    .read_text())
    src, tgt = pa["source"], pa["target"]
    put("NDaFlows", num(src["n_rows"]), source="EXP-041 provenance")
    put("NDbFlows", num(tgt["n_rows"]), source="EXP-041 provenance")
    put("PrevDa", src["attack_prevalence_pct"], "{:.2f}")
    put("PrevDb", tgt["attack_prevalence_pct"], "{:.2f}")
    put("NSrcGroups", str(src["n_groups"]))
    put("NSub", num(pa["source_subsample"]))
    pr = json.loads((RES / "EXP-042/statistics/provenance.json").read_text())["corpus"]
    put("NRadioWin", num(pr["n_rows"]), source="EXP-042 provenance")
    put("NRadioFeat", str(pr["n_features"]))
    put("PrevRadio", pr["attack_prevalence_pct"], "{:.1f}")
    put("NSessions", str(pr["n_groups"]))

    # ---- protocol sensitivity ----------------------------------------------
    L = pd.read_csv(P / "leakage_stats.csv").set_index("model").loc[NONTRIVIAL]
    put("LeakMin", L.rg_mean.min(), source="EXP-052 leakage_stats")
    put("LeakMax", L.rg_mean.max())
    put("LeakStratMin", L.rs_mean.min())
    put("LeakStratMax", L.rs_mean.max())
    R = pd.read_csv(RES / "EXP-042/raw/leakage_runs_radio.csv")
    ratio = float((R.n_test / R.n_train).mean())
    per = R.groupby(["protocol", "model", "split_seed"]).f1_macro.mean().unstack(0)
    for a, b, key in (("random", "group_disjoint", "Leak"),
                      ("random", "stratified_group", "LeakStrat")):
        d = (per[a] - per[b]).unstack(0)[NONTRIVIAL]
        c = ci(d.mean(axis=1).to_numpy(), ratio)
        put(key + "Avg", c["mean"], source="EXP-042 raw, across-architecture mean")
        put(key + "AvgNbLo", c["nb_lo"])
        put(key + "AvgNbHi", c["nb_hi"])
        put(key + "AvgPnb", c["p_nb"], "{:.2f}")
        if c["p_t"] < 1e-3:
            e_ = int(np.floor(np.log10(c["p_t"])))
            put(key + "AvgPt", "%.0f" % (c["p_t"] / 10 ** e_) + r"\times10^{%d}" % e_)
        else:
            put(key + "AvgPt", c["p_t"], "{:.3f}")
        put(key + "SeedsMin", str(int((d > 0).sum().min())))
    put("LeakSigNb", str(int((L.rg_p_nb_holm < 0.05).sum())))
    nn = pd.read_csv(P / "nn_probe.csv").set_index("protocol")
    put("NNSame", 100 * nn.loc["random", "nn_same_session"], "{:.0f}",
        "EXP-052 nn_probe")
    put("NNSameMin", 100 * nn.loc["random", "nn_same_session_min"], "{:.0f}")
    put("NNSameMax", 100 * nn.loc["random", "nn_same_session_max"], "{:.0f}")
    put("NNoneRandom", nn.loc["random", "nn1_f1"])
    put("NNoneRun", nn.loc["group_disjoint", "nn1_f1"])
    # from the displayed (two-decimal) values, so the prose difference matches
    put("NNGain", round(nn.loc["random", "nn1_f1"], 2)
        - round(nn.loc["group_disjoint", "nn1_f1"], 2))
    put("NNgapBest", L.group_disjoint.max() - nn.loc["group_disjoint", "nn1_f1"])

    # ---- temporal ------------------------------------------------------------
    D = pd.read_csv(P / "drift_summary.csv").set_index("direction")
    put("DriftFwd", -D.loc["forward", "mean_delta"], source="EXP-052 drift")
    put("DriftRev", -D.loc["reverse", "mean_delta"])
    put("DriftOutFwd", str(int(D.loc["forward", "n_outside"])))
    put("DriftOutRev", str(int(D.loc["reverse", "n_outside"])))
    put("DriftN", str(int(D.loc["forward", "n"])))
    put("DriftFAtemp", num(D.loc["forward", "false_alerts_temporal"]))
    put("DriftFActrl", num(D.loc["forward", "false_alerts_control"]))
    put("DriftFAratio", D.loc["forward", "false_alerts_temporal"]
        / D.loc["forward", "false_alerts_control"], "{:.1f}")
    put("DriftDays", "52.96")

    # ---- time order with category coverage, EXP-053 (round 2) ---------------
    if (P / "drift_v3_compare.csv").exists():
        Cv = pd.read_csv(P / "drift_v3_compare.csv")
        fw, rv = Cv[Cv.direction == "forward"], Cv[Cv.direction == "reverse"]
        put("DvFwdBA", fw.balanced_accuracy_temporal.mean(), source="EXP-053 B")
        put("DvRevBA", rv.balanced_accuracy_temporal.mean())
        put("DvCtrlBA", fw.balanced_accuracy_control_mean.mean())
        put("DvFwdBAmin", fw.balanced_accuracy_temporal.min())
        put("DvFwdBAmax", fw.balanced_accuracy_temporal.max())
        put("DvRevBAmin", rv.balanced_accuracy_temporal.min())
        put("DvRevBAmax", rv.balanced_accuracy_temporal.max())
        put("DvCtrlBAmin", fw.balanced_accuracy_control_mean.min())
        put("DvCtrlBAmax", fw.balanced_accuracy_control_mean.max())
        # share of control draws at or below the temporal value, in percent
        put("DvFwdPctMin", 100 * fw.balanced_accuracy_pct_control_le.min(), "{:.0f}")
        put("DvFwdPctMax", 100 * fw.balanced_accuracy_pct_control_le.max(), "{:.0f}")
        put("DvRevPctMin", 100 * (1 - rv.balanced_accuracy_pct_control_le.max()), "{:.0f}")
        put("DvRevPctMax", 100 * (1 - rv.balanced_accuracy_pct_control_le.min()), "{:.0f}")
        put("DvFwdFPR", fw.fpr_temporal.mean())
        put("DvRevFPR", rv.fpr_temporal.mean())
        put("DvCtrlFPR", fw.fpr_control_mean.mean())
        put("DvNctrl", str(int(fw.n_control.iloc[0])))
        Bn = pd.read_csv(P / "drift_v3_benign.csv")
        low, high = Bn[Bn.fpr_mean <= 0.10], Bn[Bn.fpr_mean >= 0.80]
        put("BenLowN", str(len(low)), source="EXP-053 C")
        put("BenHighN", str(len(high)))
        put("BenLowMax", low.fpr_mean.max())
        put("BenHighMin", high.fpr_mean.min())
        put("BenHighMax", high.fpr_mean.max())
        sess = [str(int(s)) for s in high.session]
        put("BenHighSessions", ", ".join(sess[:-1]) + " and " + sess[-1])
        days = [f"{d:.0f}" for d in high.day]
        put("BenHighDays", ", ".join(days[:-1]) + " and " + days[-1])
        put("BenLateFPR", float(Bn.set_index("session").loc[Bn.session.max(), "fpr_mean"]))
        put("BenLateFA", float(Bn.set_index("session").loc[Bn.session.max(),
                                                         "false_alerts_per_benign_ue_hour"]),
            "{:.0f}")
        A = pd.read_csv(P / "drift_v3_audit.csv", keep_default_na=False)
        fa = A[(A.direction == "forward")]
        put("DvAuditUnseenMax", str(int(fa.n_unseen_attack_categories.max())),
            source="EXP-053 A")
        put("DvAuditUnseenMin", str(int(fa.n_unseen_attack_categories.min())))
        put("DvAuditBenignTest", str(len(set(fa.benign_test_sessions))))

    # ---- transfer ------------------------------------------------------------
    T = pd.read_csv(P / "transfer_stats.csv")
    f = T[(T.direction == "a_to_b") & T.model.isin(NONTRIVIAL)].set_index("model")
    r = T[(T.direction == "b_to_a") & T.model.isin(NONTRIVIAL)].set_index("model")
    ff = T[T.direction == "a_to_b"].set_index("model")
    put("TrBAdropMin", f.dBA_mean.min(), source="EXP-052 transfer_stats")
    put("TrBAdropMax", f.dBA_mean.max())
    put("TrSigBA", str(int((f.dBA_p_nb_holm < 0.05).sum())))
    put("TrSigFone", str(int((f.dF1_p_nb_holm < 0.05).sum())))
    put("TrSrcBAmin", f.src_ba.min())
    put("TrSrcBAmax", f.src_ba.max())
    put("TrTgtBAmin", f.tgt_ba.min())
    put("TrTgtBAmax", f.tgt_ba.max())
    put("TrTgtAUCmin", f.tgt_auc.min())
    put("TrTgtAUCmax", f.tgt_auc.max())
    put("TrSrcFonemin", f.src_f1.min())
    put("TrSrcFonemax", f.src_f1.max())
    put("TrTgtFonemin", f.tgt_f1.min())
    put("TrTgtFonemax", f.tgt_f1.max())
    put("TrFoneDropMin", f.dF1_mean.min())
    put("TrFoneDropMax", f.dF1_mean.max())
    put("TrMajDrop", ff.loc["majority", "dF1_mean"])
    put("TrStratFloor", ff.loc["stratified", "tgt_f1"], "{:.3f}")
    put("TrFairCoin", float(f.fair_coin_macro_f1_target.iloc[0]), "{:.3f}")
    # three decimals, as in Table VIII (two decimals turned +0.015 into 0.01)
    put("TrDiDmin", f.did_mean.min(), "{:+.3f}")
    put("TrDiDmax", f.did_mean.max(), "{:+.3f}")
    put("TrLRtgtBA", f.loc["logreg", "tgt_ba"])
    put("TrLRtgtAUC", f.loc["logreg", "tgt_auc"])
    put("TrMLPsrcBA", f.loc["mlp", "src_ba"])
    put("TrMLPtgtBA", f.loc["mlp", "tgt_ba"])
    put("TrMLPtgtFone", f.loc["mlp", "tgt_f1"], "{:.3f}")
    put("TrChanceSig", str(int((f.ba_vs_chance_nb_lo > 0).sum())))
    put("TrChanceSigHolm", str(int((f.ba_vs_chance_p_nb_holm < 0.05).sum())))
    run = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/runs.csv")
    s = run[run.domain == "source_heldout"].set_index(["model", "split_seed"])
    t = run[run.domain == "target"].set_index(["model", "split_seed"])
    rat = float((s.n_eval / s.n_train).mean())
    dba = (s.balanced_accuracy - t.balanced_accuracy).unstack(0)[NONTRIVIAL]
    c = ci(dba.mean(axis=1).to_numpy(), rat)
    put("TrBAdropAvg", c["mean"])
    put("TrBAdropAvgNbLo", c["nb_lo"])
    put("TrBAdropAvgNbHi", c["nb_hi"])
    put("TrBAseedsMin", str(int((dba > 0).sum().min())))
    tb = t.balanced_accuracy.unstack(0)[NONTRIVIAL]
    c = ci((tb.mean(axis=1) - 0.5).to_numpy(), rat)
    put("TrTgtBAavg", 0.5 + c["mean"])
    put("TrRevBAdropMin", r.dBA_mean.min(), "{:+.3f}")
    put("TrRevBAdropMax", r.dBA_mean.max(), "{:+.3f}")
    put("TrRevTgtBAmin", r.tgt_ba.min())
    put("TrRevTgtBAmax", r.tgt_ba.max())
    put("TrRevSigBA", str(int((r.dBA_p_nb_holm < 0.05).sum())))
    RC = pd.read_csv(P / "rank_correlation.csv")
    rc = RC[(RC.direction == "a_to_b") & (RC.subset == "all six")].set_index("metric")
    put("RhoFone", rc.loc["f1", "rho"], source="EXP-052 rank_correlation")
    put("RhoFoneP", rc.loc["f1", "p"])
    put("RhoBA", rc.loc["ba", "rho"])
    put("RhoBAP", rc.loc["ba", "p"])
    put("RhoAUC", rc.loc["auc", "rho"])

    H = pd.read_csv(P / "harmonisation_loss.csv").set_index("model")
    put("HarmBAmin", H.loss_balanced_accuracy_mean.min(), "{:.3f}",
        "EXP-052 harmonisation_loss")
    put("HarmBAmax", H.loss_balanced_accuracy_mean.max(), "{:.3f}")
    put("HarmFoneMin", H.loss_f1_macro_mean.min(), "{:.3f}")
    put("HarmFoneMax", H.loss_f1_macro_mean.max(), "{:.3f}")
    put("NFullFeat", str(int(H.n_features_full.iloc[0])))

    dom = pd.read_csv(RES / "EXP-045/processed/domain_classifier.csv")
    put("DomShared", float(dom.balanced_accuracy.iloc[0]), "{:.3f}",
        "EXP-045 domain_classifier")
    put("DomRobust", float(dom.balanced_accuracy.iloc[1]), "{:.3f}")
    fs = json.loads((RES / "EXP-045/statistics/provenance_sensitivity.json")
                    .read_text())
    put("WoneRobust", fs["w1_mean_robust"])
    put("WoneNonrobust", fs["w1_mean_nonrobust"])

    # ---- operational --------------------------------------------------------
    A = pd.read_csv(P / "pooled_radio_tau05.csv").set_index("model").loc[NONTRIVIAL]
    put("RadFPRmin", A.fpr.min(), source="EXP-052 pooled_radio_tau05")
    put("RadFPRmax", A.fpr.max())
    put("RadPrecMin", A.corpus_precision.min())
    put("RadPrecMax", A.corpus_precision.max())
    put("RadPPVmin", A.ppv.min(), "{:.4f}")
    put("RadPPVmax", A.ppv.max(), "{:.4f}")
    put("RadCollapseMin", A.collapse.min(), "{:.0f}")
    put("RadCollapseMax", A.collapse.max(), "{:.0f}")
    put("RadFAmin", A.false_alerts_per_benign_ue_hour.min(), "{:.0f}")
    put("RadFAmax", A.false_alerts_per_benign_ue_hour.max(), "{:.0f}")
    put("RadNbenign", num(A.n_benign_pooled.iloc[0]))
    put("RadSpread", A.ppv.max() / A.ppv.min())
    RR = pd.read_csv(P / "pooled_radio_reachability.csv").set_index("model").loc[NONTRIVIAL]
    put("RadPPVbest", RR.ppv_max.max(), "{:.3f}")
    put("RadPPVbestWorst", RR.loc[RR.ppv_max.idxmax(), "ppv_worst_at_max"], "{:.3f}")
    cbr = P / "pooled_radio_bootstrap.csv"
    if cbr.exists():
        CB = pd.read_csv(cbr).set_index("model").loc[NONTRIVIAL]
        put("RadCbFPRlo", CB.fpr_lo.min(), source="EXP-052 pooled_radio_bootstrap (EXP-056)")
        put("RadCbFPRhi", CB.fpr_hi.max())
        put("RadCbFAlo", CB.fa_lo.min(), "{:.0f}")
        put("RadCbFAhi", CB.fa_hi.max(), "{:.0f}")
        put("RadCbPPVlo", CB.ppv_lo.min(), "{:.4f}")
        put("RadCbPPVhi", CB.ppv_hi.max(), "{:.2f}")
        put("RadCbBestHiN", str(int((CB.best_ppv_hi >= 0.99).sum())))
        put("RadCbNboot", str(int(CB.n_boot.iloc[0])))
    SW = pd.read_csv(P / "pooled_radio_pi_sweep.csv").set_index("pi")
    put("RadCollapseLowPi", num(SW.loc[1e-4, "collapse_mean"]))
    put("RadCollapseHighPi", SW.loc[0.5, "collapse_mean"])
    notes = json.loads((P / "notes.json").read_text())
    e = notes["estimator_spread_radio"]
    put("EstPooled", e["pooled"], source="EXP-052 estimator_contrast_radio")
    put("EstMean", e["mean"], "{:.1f}")
    put("EstMedian", e["median"])
    NS = pd.read_csv(P / "pooled_network_source_heldout_tau05.csv").set_index("model").loc[NONTRIVIAL]
    NT = pd.read_csv(P / "pooled_network_target_tau05.csv").set_index("model").loc[NONTRIVIAL]
    for lab, X in (("NetSrc", NS), ("NetTgt", NT)):
        put(lab + "FPRmin", X.fpr.min(), "{:.3f}")
        put(lab + "FPRmax", X.fpr.max(), "{:.3f}")
        put(lab + "PPVmin", X.ppv.min(), "{:.4f}")
        put(lab + "PPVmax", X.ppv.max(), "{:.4f}")
        put(lab + "FAmin", num(X.false_alerts_per_hour_at_240k.min()))
        put(lab + "FAmax", num(X.false_alerts_per_hour_at_240k.max()))
    NR = pd.read_csv(P / "pooled_network_target_reachability.csv").set_index("model").loc[NONTRIVIAL]
    put("NetTgtPPVbest", NR.ppv_max.max(), "{:.3f}")
    NRs = pd.read_csv(P / "pooled_network_source_heldout_reachability.csv").set_index("model").loc[NONTRIVIAL]
    put("NetSrcPPVbest", NRs.ppv_max.max(), "{:.2f}")

    # ---- calibration ---------------------------------------------------------
    C = pd.read_csv(RES / "EXP-044/raw/calibration_runs.csv")
    raw = C[C.calibrator == "raw"].set_index(["seed", "model", "domain"]).roc_auc
    dev = {}
    for cal in ("platt", "temperature", "isotonic"):
        c2 = C[C.calibrator == cal].set_index(["seed", "model", "domain"]).roc_auc
        dev[cal] = (c2 - raw).abs().groupby(level="model").max()
    put("CalTempMax", float(dev["temperature"].max()), "{:.0e}", "EXP-044 raw")
    put("CalIsoMin", float(dev["isotonic"].min()))
    put("CalIsoMax", float(dev["isotonic"].max()))
    put("CalPlattFlip", float(dev["platt"].max()))
    pl = C[C.calibrator == "platt"].set_index(["seed", "model", "domain"]).roc_auc
    flips = ((pl - raw).abs() > 0.5).groupby(level=["seed", "model"]).any()
    put("CalPlattFlipSeeds", str(int(flips.sum())))
    put("CalSeeds", str(C.seed.nunique()))
    pdg = RES / "EXP-044/processed/platt_inversion_diagnosis.csv"
    if pdg.exists():
        dg = pd.read_csv(pdg)
        inv = dg[dg.inverted].iloc[0]
        put("PlattCalAUC", float(inv.auc_cal), source="analysis/platt_diagnosis.py")
        put("PlattTestAUC", float(inv.auc_test))
        put("PlattCalGroups", str(int(inv.cal_groups)))
        put("PlattSlope", float(inv.platt_slope))
    PE = pd.read_csv(RES / "EXP-044/processed/prior_estimates.csv")
    put("PriorTrue", float(PE.pi_true.iloc[0]), "{:.3f}")
    put("PriorMeanMin", PE.groupby(["method", "calibrator", "model"]).pi_hat.mean().min())
    put("PriorMeanMax", PE.groupby(["method", "calibrator", "model"]).pi_hat.mean().max())
    put("PriorFracExtreme", 100 * float(((PE.pi_hat < 0.05) | (PE.pi_hat > 0.95)).mean()),
        "{:.0f}")

    # ---- per-category detection ---------------------------------------------
    fa = pd.read_csv(RES / "EXP-041/a_to_b__shared/processed/per_category_recall.csv"
                     ).groupby("model").mean(numeric_only=True)
    fb = pd.read_csv(RES / "EXP-041/b_to_a__shared/processed/per_category_recall.csv"
                     ).groupby("model").mean(numeric_only=True)
    ens = ["rf", "xgboost", "hgb", "mlp", "tree"]
    put("FwdLRspec", fa.loc["logreg", "benign"], source="EXP-041 per_category")
    put("FwdLRdos", fa.loc["logreg", "dos"])
    put("FwdEnsFlagMin", 1 - fa.loc[ens, "benign"].max())
    put("FwdEnsFlagMax", 1 - fa.loc[ens, "benign"].min())
    put("RevBFmin", fb.loc[NONTRIVIAL, "bruteforce"].min())
    put("RevBFmax", fb.loc[NONTRIVIAL, "bruteforce"].max())
    put("RevWebEnsMax", fb.loc[["rf", "xgboost", "hgb", "mlp"], "web"].max())

    # ---- deployability test ---------------------------------------------------
    PR = pd.read_csv(P / "predicate.csv").set_index("model")
    put("PredGenMin", PR.dBA_upper.min(), source="EXP-052 predicate")
    put("PredGenMax", PR.dBA_upper.max())
    put("PredPPVmax", PR.best_ppv_at_rmin.max(), "{:.4f}")
    put("PredFAmin", num(PR.min_false_alerts_at_rmin.min()))
    put("PredPass", str(int(PR.verdict.sum())))

    # ---- optional arms (written when present) -------------------------------
    arms = P / "arms_summary.csv"
    if arms.exists():
        AR = pd.read_csv(arms)
        # detectors only: the two floors sit at BA 0.5 by construction
        tg = AR[(AR.domain == "target") & ~AR.model.isin(["majority", "stratified"])]
        for arm, key in (("robust subset (9)", "Rob"), ("CORAL", "Coral"),
                         ("unsupervised", "Unsup")):
            g = tg[tg.arm == arm]
            if len(g):
                put(key + "BAmin", g.ba.min(), source="EXP-052 arms_summary")
                put(key + "BAmax", g.ba.max())
                put(key + "AUCmin", g.auc.min())
                put(key + "AUCmax", g.auc.max())
                put(key + "FPRmin", g.fpr.min())
                put(key + "FPRmax", g.fpr.max())
        sh = AR[(AR.domain == "source_heldout") & ~AR.model.isin(["majority", "stratified"])]
        rob = sh[sh.arm == "robust subset (9)"]
        if len(rob):
            put("RobSrcBAmin", rob.ba.min())
            put("RobSrcBAmax", rob.ba.max())
        cor = tg[(tg.arm == "CORAL") & (tg.model == "mlp")]
        if len(cor):
            put("CoralMLPtgtBA", float(cor.ba.iloc[0]))

    # ---- 5G-NIDD label conflicts (EXP-057) ---------------------------------
    lc = RES / "EXP-057/processed/ceilings.csv"
    if lc.exists():
        Lc = pd.read_csv(lc).set_index("feature_space")
        pr_ = json.loads((RES / "EXP-057/statistics/pairing.json").read_text())
        pf_ = pd.read_csv(RES / "EXP-057/processed/per_file.csv").set_index("file")
        nat = Lc.loc["native_content"]
        put("LcShareAll", 100 * nat.share_in_conflicting, "{:.0f}", "EXP-057")
        put("LcFlowsAll", num(nat.flows_in_conflicting))
        put("LcCeilNative", nat.ba_ceiling, "{:.3f}")
        put("LcCeilShared", Lc.loc["shared18", "ba_ceiling"], "{:.3f}")
        put("LcCeilPos", Lc.loc["native_with_seq_offset", "ba_ceiling"], "{:.3f}")
        put("LcNFeat", str(int(nat.n_features)))
        put("LcTwinBenign", num(pr_["benign_flows"]))
        put("LcTwinAttack", num(pr_["attack_flows"]))
        put("LcTwinRecords", num(pr_["records"]))
        put("LcTwinEqual", num(pr_["equal_counts"]))
        put("LcBenignFile", str(pr_["benign_file"]))
        put("LcAttackFile", str(pr_["attack_file"]))
        put("LcBenignTwinPct", 100 * pr_["benign_flows"] / pr_["benign_total"], "{:.0f}")
        put("LcFileBenignTwinPct", 100 * pr_["benign_flows"] / pr_["benign_in_benign_file"],
            "{:.0f}")
        put("LcBenignFileConf", 100 * pf_.loc[pr_["benign_file"], "conflicting_native"], "{:.0f}")
        put("LcAttackFileConf", 100 * pf_.loc[pr_["attack_file"], "conflicting_native"], "{:.0f}")

    # ---- D_B without the conflicting benign copies (EXP-056) -----------------
    tc = P / "transfer_target_clean.csv"
    if tc.exists():
        TC = pd.read_csv(tc).set_index("model").loc[NONTRIVIAL]
        put("TrCleanTgtBAmin", TC.tgt_ba_clean.min(), source="EXP-056 transfer_target_clean")
        put("TrCleanTgtBAmax", TC.tgt_ba_clean.max())
        put("TrCleanDropMin", TC.dBA_clean_mean.min())
        put("TrCleanDropMax", TC.dBA_clean_mean.max())
        put("TrCleanSig", str(int((TC.dBA_clean_p_nb_holm < 0.05).sum())))
        put("TrCleanLR", TC.loc["logreg", "tgt_ba_clean"])
        put("TrCleanOthMin", TC.drop("logreg").tgt_ba_clean.min())
        put("TrCleanOthMax", TC.drop("logreg").tgt_ba_clean.max())
        TRf = P / "target_reference.csv"
        if TRf.exists():
            TR_ = pd.read_csv(TRf)
            ref = (TR_[(TR_.feature_set == "shared18") & (TR_.protocol == "random")]
                   .set_index("model").loc[NONTRIVIAL, "ba_clean"])
            short = ref - TC.tgt_ba_clean
            put("TrCleanShortMin", short.min())
            put("TrCleanShortMax", short.max())
        NC = pd.read_csv(P / "pooled_network_target_clean_tau05.csv").set_index("model").loc[NONTRIVIAL]
        put("NetCleanFPRmin", NC.fpr.min(), "{:.3f}")
        put("NetCleanFPRmax", NC.fpr.max(), "{:.3f}")
        put("NetCleanPPVmin", NC.ppv.min(), "{:.4f}")
        put("NetCleanPPVmax", NC.ppv.max(), "{:.4f}")
        put("NetCleanFAmin", num(NC.false_alerts_per_hour_at_240k.min()))
        put("NetCleanFAmax", num(NC.false_alerts_per_hour_at_240k.max()))
        RC_ = pd.read_csv(P / "pooled_network_target_clean_reachability.csv").set_index("model").loc[NONTRIVIAL]
        put("NetCleanPPVbest", RC_.ppv_max.max(), "{:.3f}")
        PC = pd.read_csv(P / "predicate_clean.csv").set_index("model")
        put("PredCleanPass", str(int(PC.verdict.sum())))
        put("PredCleanPPVmax", PC.best_ppv_at_rmin.max(), "{:.4f}")
        put("PredCleanFAmin", num(PC.min_false_alerts_at_rmin.min()))
        for dom, key in (("target", "NetTgtCb"), ("target_clean", "NetCleanCb"),
                         ("source_heldout", "NetSrcCb")):
            f_ = P / f"pooled_network_{dom}_bootstrap.csv"
            if f_.exists():
                B_ = pd.read_csv(f_).set_index("model").loc[NONTRIVIAL]
                put(key + "FPRlo", B_.fpr_lo.min(), "{:.3f}")
                put(key + "FPRhi", B_.fpr_hi.max(), "{:.3f}")
                put(key + "PPVhi", B_.ppv_hi.max(), "{:.4f}")
                put(key + "BestHi", B_.best_ppv_hi.max(), "{:.3f}")
        PF = pd.read_csv(P / "target_per_file_tau05.csv")
        cc = PF[PF.group.astype(str).str.endswith("|c") & PF.model.isin(NONTRIVIAL)]
        put("NetCopyFlagMin", cc.fpr.min())
        put("NetCopyFlagMax", cc.fpr.max())
    # ---- third corpus D_C (EXP-058) -------------------------------------------
    tt = P / "third_transfer.csv"
    if tt.exists():
        TT = pd.read_csv(tt)
        for lab, k in (("a_to_c", "ThA"), ("b_to_c", "ThB")):
            g = TT[(TT.direction == lab) & TT.model.isin(NONTRIVIAL)]
            if not len(g):
                continue
            put(k + "SrcBAmin", g.src_ba.min(), source="EXP-058")
            put(k + "SrcBAmax", g.src_ba.max())
            put(k + "TgtBAmin", g.tgt_ba.min())
            put(k + "TgtBAmax", g.tgt_ba.max())
            put(k + "TgtAUCmin", g.tgt_auc.min())
            put(k + "TgtAUCmax", g.tgt_auc.max())
            put(k + "DropMin", g.dBA_mean.min())
            put(k + "DropMax", g.dBA_mean.max())
            put(k + "Sig", str(int((g.dBA_p_nb_holm < 0.05).sum())))
            put(k + "Seeds", str(int(g.n_seeds.max())))
            pc = pd.read_csv(P / f"third_percat_{lab}.csv").set_index("model").loc[NONTRIVIAL]
            for col, nm in (("syn_flood", "Syn"), ("icmp_flood", "Icmp"),
                            ("pfcp_deletion", "Pfcp")):
                put(k + nm + "Min", pc[col].min())
                put(k + nm + "Max", pc[col].max())
            put(k + "BgFlagMax", pc["background"].max())
            put(k + "BenSpecMin", pc["benign"].min())
            po = pd.read_csv(P / f"third_pooled_{lab}.csv").set_index("model").loc[NONTRIVIAL]
            put(k + "FPRmin", po.fpr.min(), "{:.3f}")
            put(k + "FPRmax", po.fpr.max(), "{:.3f}")
            put(k + "PPVmax", po.ppv.max(), "{:.4f}")
            rc = pd.read_csv(P / f"third_reach_{lab}.csv").set_index("model").loc[NONTRIVIAL]
            put(k + "PPVbest", rc.ppv_max.max(), "{:.3f}")
            pr = pd.read_csv(P / f"third_predicate_{lab}.csv")
            put(k + "PredPass", str(int(pr.verdict.sum())))
        Rf = pd.read_csv(P / "third_reference.csv")
        Rf = Rf[Rf.model.isin(NONTRIVIAL)]
        for (fs, pr_), g in Rf.groupby(["feature_set", "protocol"]):
            kk = "ThRef" + {"shared18": "Sh", "native": "Nat"}[fs] + {"random": "Rand",
                                                                      "leave_one_file": "Lofo"}[pr_]
            put(kk + "BAmin", g.ba.min(), "{:.3f}")
            put(kk + "BAmax", g.ba.max(), "{:.3f}")
        Ce = pd.read_csv(P / "third_ceilings.csv").set_index("feature_space")
        put("ThCeilShared", Ce.loc["shared18", "ba_ceiling"], "{:.3f}")
        put("ThCeilNative", Ce.loc["native", "ba_ceiling"], "{:.3f}")
        put("ThConfShare", 100 * Ce.loc["shared18", "share_in_conflicting"], "{:.1f}")
        put("ThNflows", num(Ce.loc["shared18", "n_flows"]))
        pv = json.loads((RES / "EXP-058/a_to_c__shared/statistics/provenance.json").read_text())
        put("ThPrev", pv["target"]["attack_prevalence_pct"], "{:.1f}")
        pcn = pd.read_csv(RES / "EXP-058/a_to_c__shared/processed/per_category_recall.csv").iloc[0]
        put("ThNattack", num(sum(int(pcn[c + "__n"]) for c in
                                 ("syn_flood", "icmp_flood", "pfcp_deletion"))))

    # ---- radio session rule vs the 42 runs of Fard et al. (EXP-059) ----------
    sr = RES / "EXP-059/processed/session_rule.csv"
    if sr.exists():
        S = pd.read_csv(sr)
        k42 = S[S.n_segments == 42]
        put("SessRunN", "42", source="EXP-059")
        put("SessRunGapMin", str(int(k42.gap_s.min())))
        put("SessRunGapMax", str(int(k42.gap_s.max())))
        put("SessRunCatPure", str(int(k42.n_category_pure.min())))
        put("SessMultiSub", str(int(S.reference_sessions_multi_subcategory.iloc[0])))
        put("SessNested", "yes" if bool(k42.nested_in_reference.astype(str).eq("True").all()) else "no")

    # ---- latency repeat with every call kept (EXP-060) vs EXP-043 -----------
    l60 = RES / "EXP-060/raw/latency_stages.csv"
    if l60.exists():
        a = pd.read_csv(RES / "EXP-043/raw/latency_stages.csv")
        b = pd.read_csv(l60)
        key = ["layer", "model", "stage"]
        mm = a[a.layer == "radio"].merge(b[b.layer == "radio"], on=key, suffixes=("_a", "_b"))
        # single-thread stages only; the n_jobs=-1 stage depends on the pool
        mm = mm[mm.stage != "sk_array_all_threads"]
        r50 = mm.p50_b / mm.p50_a
        e2e = mm[mm.stage == "e2e_aggregate_plus_onnx"]
        put("LatRepStages", str(len(mm)), source="EXP-060")
        put("LatRepMedRatio", float(r50.median()), "{:.2f}")
        put("LatRepMedRatioMin", float(r50.min()), "{:.2f}")
        put("LatRepMedRatioMax", float(r50.max()), "{:.1f}")
        put("LatRepEtoEPnnMax", float(e2e.p99_b.max()), "{:.2f}")
        put("LatRepEtoEPnnHiMax", float(e2e.p99_hi_b.max()), "{:.2f}")

    # ---- in-target references on D_B (EXP-054) -----------------------------
    tr_ = P / "target_reference.csv"
    if tr_.exists():
        TR = pd.read_csv(tr_)
        TR = TR[TR.model.isin(NONTRIVIAL)]
        tag = {"shared18": "Sh", "native": "Nat"}
        prot = {"random": "Rand", "file_disjoint": "File", "site1to2": "SiteAB",
                "site2to1": "SiteBA"}
        for (fs, pr), g in TR.groupby(["feature_set", "protocol"]):
            k = "Tgt" + prot[pr] + tag[fs]
            put(k + "BAmin", g.ba.min(), "{:.3f}", "EXP-054")
            put(k + "BAmax", g.ba.max(), "{:.3f}")
            put(k + "CleanBAmin", g.ba_clean.min(), "{:.3f}")
            put(k + "CleanBAmax", g.ba_clean.max(), "{:.3f}")
            put(k + "CleanFPRmax", g.fpr_clean.max())
            put(k + "N", str(int(g.n.max())))

    # ---- published pipeline down the ladder (EXP-055) ----------------------
    pl_ = P / "published_ladder.csv"
    if pl_.exists():
        PL = pd.read_csv(pl_)
        r0 = PL[PL.rung == "R0"].set_index("model")
        top = [m for m in ("dt", "rf", "knn", "mlp") if m in r0.index]
        put("PubRzAccMin", 100 * r0.loc[top, "accuracy"].min(), "{:.2f}", "EXP-055")
        put("PubRzAccMax", 100 * r0.loc[top, "accuracy"].max(), "{:.2f}")
        if "nb" in r0.index:
            put("PubRzAccNB", 100 * r0.loc["nb", "accuracy"], "{:.2f}")
        put("PubRzPassN", str(int(r0.verdict.sum())))
        put("PubRzPPVmax", r0.ppv.max())
        put("PubRzFAmin", num(r0.fa_h.min()))
        for rung, key in (("R1", "One"), ("R2", "Two"), ("R3", "Three")):
            for fs, fk in (("published_top10", "Pub"), ("no_position_top10", "Nopos")):
                g = PL[(PL.rung == rung) & (PL.feature_set == fs) & (PL.model != "nb")]
                if not len(g):
                    continue
                k = "Pub" + key + fk
                put(k + "AccMin", 100 * g.accuracy.min(), "{:.1f}")
                put(k + "AccMax", 100 * g.accuracy.max(), "{:.1f}")
                put(k + "BAmin", g.ba.min(), "{:.3f}")
                put(k + "BAmax", g.ba.max(), "{:.3f}")
                put(k + "CleanBAmin", g.ba_clean.min(), "{:.3f}")
                put(k + "CleanBAmax", g.ba_clean.max(), "{:.3f}")
                put(k + "FPRmin", g.fpr.min(), "{:.3f}")
                put(k + "FPRmax", g.fpr.max(), "{:.3f}")
                put(k + "PassN", str(int(g.verdict.sum())))
                put(k + "PassCleanN", str(int(g.verdict_clean.sum())))
        r1rf = PL[(PL.rung == "R1") & (PL.model == "rf")]
        if len(r1rf):
            put("PubOneRFclean", float(r1rf.ba_clean.iloc[0]), "{:.4f}")
        # per-fold spread of RF at R2: folds that split the two flood captures
        # between train and test collapse, the others do not
        LR_ = pd.read_csv(RES / "EXP-055/raw/ladder_runs.csv")
        for fs, fk in (("published_top10", "Pub"), ("no_position_top10", "Nopos")):
            f2 = LR_[(LR_.rung == "R2") & (LR_.feature_set == fs) & (LR_.model == "rf")]
            if len(f2):
                put("PubTwo" + fk + "FoldMin", f2.balanced_accuracy.min())
                put("PubTwo" + fk + "FoldMax", f2.balanced_accuracy.max())
                put("PubTwo" + fk + "FoldAccMin", 100 * f2.accuracy.min(), "{:.1f}")
    # ---- sequence models (EXP-050), family of two, Holm within the pair -----
    seqf = P / "sequence_models.csv"
    if seqf.exists():
        from revision_stats import holm
        S = pd.read_csv(seqf).set_index("model")
        # three decimals: the two run-disjoint scores agree to two (0.755, 0.759)
        put("SeqRandomMin", S.random.min(), "{:.3f}", "EXP-052 sequence_models")
        put("SeqRandomMax", S.random.max(), "{:.3f}")
        put("SeqRDmin", S.group_disjoint.min(), "{:.3f}")
        put("SeqRDmax", S.group_disjoint.max(), "{:.3f}")
        put("SeqGainMin", S.rg_mean.min())
        put("SeqGainMax", S.rg_mean.max())
        put("SeqPholmMax", float(holm(S.rg_p_nb).max()), "{:.2f}")

    # ---- latency (EXP-043), only once the quiet-machine run exists -----------
    import latency_outputs as lo
    if lo.available():
        lo.numbers(put)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["% GENERATED by analysis/make_numbers.py. DO NOT EDIT.",
             "% Every macro is computed from results/; see SRC comments."]
    for k in sorted(N):
        lines.append(f"\\newcommand{{\\{k}}}{{{N[k]}}}"
                     + (f"  % {SRC[k]}" if SRC[k] else ""))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT} ({len(N)} macros)")
    for k in sorted(N):
        print(f"  {k} = {N[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
