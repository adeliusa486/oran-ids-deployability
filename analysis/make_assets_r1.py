#!/usr/bin/env python3
"""Revision 1: every number, table and data figure of paper/r1/ (EXP-075).

Writes
  paper/r1/numbers_r1.tex   new macros (prefix R) from results/EXP-064 ... 075,
                            plus macros of the first submission whose
                            experiments are unchanged (an explicit whitelist:
                            labels, published pipeline, radio benign sessions,
                            latency, D_C references). No macro of an analysis
                            that involved 5G-NIDD in the shared space is
                            carried over: those were re-measured (D-035).
  paper/r1/tables/*.tex     complete tabular environments
  paper/r1/figs/*.pdf       data figures
  paper/r1/preamble_r1.tex  the preamble of the first submission

Usage:  python analysis/make_assets_r1.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import r1_stats_core as C  # noqa: E402

RES = ROOT / "results"
P = RES / "EXP-075" / "processed"
PAPER = ROOT / "paper" / "r1"
TAB = PAPER / "tables"
FIG = PAPER / "figs"
NONTRIVIAL = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp"]
LABEL = dict(logreg="LR", tree="DT", rf="RF", xgboost="XGB", hgb="HGB", mlp="MLP",
             majority=r"\textit{Maj.}", stratified=r"\textit{Strat.}", dann="DANN")
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten"]
OLD_WHITELIST = re.compile(
    r"^(Ben|Dv|Drift|Lc|Pub|Ric|Lat|Rad|Est|Harm|ThRef|ThCeil|ThConf|ThN|ThPrev|Sess|"
    r"NRadio|NDa|NDb|NSessions|NSrcGroups|NSub|NFullFeat|PrevDa|PrevDb|PrevRadio|"
    r"ZkVersion$|ZkRuleAgreePct$|ZkFlows$|ZkAttackPct$|ZkCopies$)")
MACROS: dict[str, str] = {}


# ---------------------------------------------------------------- helpers
def f(x, d=2):
    """Format a number for prose: minus sign safe inside \\mbox."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    s = f"{x:.{d}f}"
    if s.startswith("-") and float(s) == 0:
        s = s[1:]                                  # no "-0.00"
    return "$-$" + s[1:] if s.startswith("-") else s


def sg(x, d=3):
    """Signed number for table cells, with a true minus sign."""
    s = f"{x:+.{d}f}"
    if float(s) == 0:
        s = "+" + s[1:]
    return "$-$" + s[1:] if s.startswith("-") else s


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def thousands(n) -> str:
    return f"{int(round(n)):,}".replace(",", "{,}")


def M(name: str, value: str, src: str = ""):
    if not re.fullmatch(r"R[A-Za-z]+", name):
        raise ValueError(f"bad macro name {name}")
    MACROS[name] = value + (f"  % {src}" if src else "")


def ci(lo, hi, d=2):
    return f"[{f(lo, d)}, {f(hi, d)}]"


def rng_txt(series, d=2):
    return f(np.nanmin(series), d), f(np.nanmax(series), d)


def read(name):
    p = P / name
    return pd.read_csv(p) if p.exists() else None


# ------------------------------------------------------------- numbers
def numbers():
    nj = json.loads((RES / "EXP-075/numbers.json").read_text()) \
        if (RES / "EXP-075/numbers.json").exists() else {}
    M("RFPRmax", r"$8.3\times10^{-4}$", "A_max / lambda_b")

    # labels and raw captures (EXP-072)
    cl = json.loads((RES / "EXP-072/corrected_labels/README.json").read_text())
    M("RCopies", thousands(cl["rows_corrected"]), "EXP-072 corrected labels")
    M("RCopiesPct", f"{100 * cl['share_of_benign_class']:.0f}", "EXP-072")
    pairs = json.loads((RES / "EXP-072/pairs.json").read_text())
    udp = [p for p in pairs if p["capture"] == "UDPflood"][0]
    others = [p for p in pairs if p["capture"] != "UDPflood"]
    assert udp["shared"] == udp["bs2_keys"] and all(p["shared"] == 0 for p in others)
    M("RPcapBSTwoPkts", thousands(udp["bs2_keys"]), "EXP-072 pairs")
    M("RPcapShareBSOne", f"{100 * udp['share_of_bs1']:.0f}", "EXP-072 pairs")
    d0 = [abs(p["first_bs1"] - p["first_bs2"]) for p in others]
    M("RPcapStartMin", f"{min(d0):.3f}", "EXP-072 pairs, s")
    M("RPcapStartMax", f"{max(d0):.2f}", "EXP-072 pairs, s")
    M("RPcapOtherN", word(len(others)), "EXP-072 pairs")

    # byte accounting (EXP-074 part C)
    ba = json.loads((RES / "EXP-074/byte_accounting.json").read_text())
    M("RArgMinTCP", f"{ba['argus_5gnidd']['tcp']['min']:.0f}")
    M("RArgMinUDP", f"{ba['argus_5gnidd']['udp']['min']:.0f}")
    M("RZkMinTCP", f"{ba['zeek_5gnidd']['tcp']['min']:.0f}")
    M("RZkMinUDP", f"{ba['zeek_5gnidd']['udp']['min']:.0f}")
    shares = [x["share"] for x in ba["pcap"]["files"]]
    M("RPcapEthPct", f"{100 * ba['pcap']['share_header_14']:.1f}", "EXP-074 byte accounting")
    M("RPcapEthPctMin", f"{100 * min(shares):.0f}")
    M("RPcapEthPctMax", f"{100 * max(shares):.1f}")
    M("RPcapEthFiles", word(len(shares)))

    # flow split coverage (EXP-073)
    cov = json.loads((RES / "EXP-073/summary.json").read_text())
    cats = pd.DataFrame(cov["categories"])
    M("RCovAddrNinetyMin", str(int(cats.addresses_for_90pct.min())))
    M("RCovAddrNinetyMax", str(int(cats.addresses_for_90pct.max())))
    M("RCovTestGroupsMin", str(cov["splits"]["test_groups_range"][0]))
    M("RCovTestGroupsMax", str(cov["splits"]["test_groups_range"][1]))
    M("RCovTestFlowsMin", f"{100 * cov['splits']['test_flow_frac_range'][0]:.0f}")
    M("RCovTestFlowsMax", f"{100 * cov['splits']['test_flow_frac_range'][1]:.0f}")
    M("RCovMinTrainShare", f"{100 * min(cov['splits']['min_train_share_by_category'].values()):.0f}")
    M("RCovAttackers", str(cov["hosts"]["attacker_addresses"]))
    M("RCovTopShareMin", f"{100 * cats.top1_share.min():.0f}")
    M("RCovTopShareMax", f"{100 * cats.top1_share.max():.0f}")

    # shift diagnostics (EXP-074)
    for name, tag in (("argus_corrected", "Arg"), ("zeek", "Zk")):
        d = RES / "EXP-074" / name / "processed"
        dc = pd.read_csv(d / "domain_classifier.csv").set_index("feature_set").balanced_accuracy
        fs = pd.read_csv(d / "feature_shift.csv")
        M(f"RDom{tag}Shared", f"{dc['shared (18)']:.3f}")
        M(f"RDom{tag}Robust", f"{dc['robust (9)']:.3f}")
        M(f"RWone{tag}Robust", f"{fs[fs.robust].w1_source_quantile.mean():.2f}")
        M(f"RWone{tag}Nonrobust", f"{fs[~fs.robust].w1_source_quantile.mean():.2f}")
    old = pd.read_csv(RES / "EXP-045/processed/domain_classifier.csv").set_index("feature_set").balanced_accuracy
    M("RDomOldShared", f"{old['shared (18)']:.3f}", "EXP-045 (uncorrected bytes)")
    M("RDomOldRobust", f"{old['robust (9)']:.3f}", "EXP-045 (uncorrected bytes)")

    # radio (EXP-070)
    rad = read("radio_protocols.csv")
    if rad is not None:
        for g, tag in (("sessions", "Sess"), ("runs", "Run")):
            r = rad[(rad.grouping == g) & (rad.comparison == "R-SD")]
            nt = r[r.model.isin(NONTRIVIAL)]
            avg = r[r.model == "average"].iloc[0]
            M(f"RRad{tag}Min", f(nt.gain.min()))
            M(f"RRad{tag}Max", f(nt.gain.max()))
            M(f"RRad{tag}Avg", f(avg.gain))
            M(f"RRad{tag}Lo", f(avg.lo_groups))
            M(f"RRad{tag}Hi", f(avg.hi_groups))
            M(f"RRad{tag}P", f(avg.p_groups))
            M(f"RRad{tag}LoWin", f(avg.lo_windows))
            M(f"RRad{tag}HiWin", f(avg.hi_windows))
            M(f"RRad{tag}SigN", word(int((nt.p_groups_holm < 0.05).sum())))
            M(f"RRad{tag}PosMin", str(int(nt.splits_positive.min())))
        nn = pd.read_csv(RES / "EXP-070/raw/nn_probe.csv")
        s = nn[nn.grouping == "sessions"]
        M("RRadNNSame", f"{100 * s[s.protocol == 'random'].nn_same_group.mean():.0f}")
        M("RRadNNRand", f(s[s.protocol == "random"].nn1_f1_macro.mean(), 3))
        M("RRadNNGd", f(s[s.protocol == "group_disjoint"].nn1_f1_macro.mean(), 3))
        prov = json.loads((RES / "EXP-070/statistics/provenance.json").read_text())
        nb = prov["corpora"]["sessions"]["categories"]["benign"]
        M("RRadBenignWin", thousands(nb), "EXP-070 sessions corpus")
        M("RRadBenignHours", f"{nb * 16 / 3600:.0f}")

    # label-efficient design constants
    M("RLeDraws", word(4))
    M("RLeNtgt", "60{,}000")

    # transfer, references, arms, test: from EXP-075 processed files
    tr = read("transfer__shared.csv")
    if tr is not None:
        b = tr[tr.target == "b"]
        M("RSrcBAmin", rng_txt(b[b.view == "all"].src_ba)[0])
        M("RSrcBAmax", rng_txt(b[b.view == "all"].src_ba)[1])
        for v, tag in (("all", "All"), ("clean", "Clean"), ("relab", "Relab")):
            x = b[b.view == v]
            if x.empty:
                continue
            lo, hi = rng_txt(x.tgt_ba)
            M(f"RTr{tag}BAmin", lo)
            M(f"RTr{tag}BAmax", hi)
            M(f"RTr{tag}AUCmin", rng_txt(x.tgt_auc)[0])
            M(f"RTr{tag}AUCmax", rng_txt(x.tgt_auc)[1])
            M(f"RTr{tag}Dmin", rng_txt(x.d_ba)[0])
            M(f"RTr{tag}Dmax", rng_txt(x.d_ba)[1])
            M(f"RTr{tag}SigN", word(int((x.p_nb_holm < 0.05).sum())))
            M(f"RTr{tag}SigNbN", word(int((x.p_nb_holm < 0.05).sum())))
            M(f"RTr{tag}ChanceN", word(int((x.p_chance_holm < 0.05).sum())))
            M(f"RTr{tag}Splits", str(int(x.splits.min())))
        for t, tag in (("bz", "Zk"), ("c", "C")):
            x = tr[(tr.target == t)]
            for v, vt in (("all", "All"), ("clean", "Clean"), ("relab", "Relab")):
                y = x[x.view == v]
                if len(y):
                    M(f"RTr{tag}{vt}BAmin", rng_txt(y.tgt_ba)[0])
                    M(f"RTr{tag}{vt}BAmax", rng_txt(y.tgt_ba)[1])
                    M(f"RTr{tag}{vt}AUCmin", rng_txt(y.tgt_auc)[0])
                    M(f"RTr{tag}{vt}AUCmax", rng_txt(y.tgt_auc)[1])
                    M(f"RTr{tag}{vt}SigNbN", word(int((y.p_nb_holm < 0.05).sum())))
                    M(f"RTr{tag}{vt}Dmin", rng_txt(y.d_ba)[0])
                    M(f"RTr{tag}{vt}Dmax", rng_txt(y.d_ba)[1])
        M("RNbRatioFlows", f(nj.get("shared_nb_ratio_flows", np.nan)))
    za = read("zeek_vs_argus.csv")
    if za is not None:
        for v, tag in (("all", "All"), ("clean", "Clean"), ("relab", "Relab")):
            x = za[za.view == v]
            M(f"RZkDiff{tag}Min", rng_txt(x["diff"])[0])
            M(f"RZkDiff{tag}Max", rng_txt(x["diff"])[1])
            M(f"RZkDiff{tag}NegN", word(int((x.nb_hi < 0).sum())))
            M(f"RZkDiff{tag}PosN", word(int((x.nb_lo > 0).sum())))
    ref = read("references.csv")
    if ref is not None:
        for d, lab, v, tag in (("random", "clean", "clean", "RandClean"),
                               ("lofo", "clean", "clean", "LofoClean"),
                               ("lofo", "relab", "relab", "LofoRelab"),
                               ("s1_to_s2", "clean", "clean", "SoneClean"),
                               ("s2_to_s1", "clean", "clean", "StwoClean"),
                               ("s1_to_s2", "relab", "relab", "SoneRelab"),
                               ("s2_to_s1", "relab", "relab", "StwoRelab")):
            x = ref[(ref.design == d) & (ref.labels == lab) & (ref.view == v)]
            if len(x):
                M(f"RRef{tag}min", rng_txt(x.ba)[0])
                M(f"RRef{tag}max", rng_txt(x.ba)[1])
    mt = read("reference_vs_transfer.csv")
    if mt is not None:
        for v, tag in (("clean", "Clean"), ("relab", "Relab")):
            x = mt[mt.view == v]
            if len(x):
                M(f"RGap{tag}Min", rng_txt(x.point)[0])
                M(f"RGap{tag}Max", rng_txt(x.point)[1])
                M(f"RGap{tag}SigN", word(int((x.p_holm < 0.05).sum())))
                M(f"RGap{tag}NegN", word(int((x.hi < 0).sum())))
    test = read("test__shared.csv")
    if test is not None:
        b = test[test.target == "b"]
        for v, tag in (("all", "All"), ("clean", "Clean"), ("relab", "Relab")):
            x = b[b.view == v]
            if x.empty:
                continue
            for out in ("pass", "fail", "inconclusive"):
                M(f"RTest{tag}{out.capitalize()}N", word(int((x.verdict == out).sum())))
                M(f"RTest{tag}Gen{out.capitalize()}N", word(int((x.generalization == out).sum())))
                M(f"RTest{tag}Alert{out.capitalize()}N", word(int((x.alert_alert_term == out).sum())))
            M(f"RTest{tag}OracleN", word(int(x.oracle_alert_pass.sum())))
            M(f"RTest{tag}AlertsMin", thousands(x.alert_alerts_per_h.min()))
            M(f"RTest{tag}AlertsMax", thousands(x.alert_alerts_per_h.max()))
            M(f"RTest{tag}PPVmax", f(x.alert_ppv.max(), 3))
            M(f"RTest{tag}OraclePPVmax", f(x.oracle_best_ppv.max(), 3))
            M(f"RTest{tag}OracleAlertsMin", thousands(x.oracle_min_alerts.min()))
            M(f"RTest{tag}GenHiMin", f(x.d_ba_hi.min()))
    ops = read("operating__shared.csv")
    if ops is not None:
        for t, v, tag in (("b", "all", "BAll"), ("b", "clean", "BClean"), ("b", "relab", "BRelab"),
                          ("source_heldout", "all", "Src")):
            x = ops[(ops.target == t) & (ops.view == v)]
            if len(x):
                M(f"ROp{tag}FPRmin", f(x.fpr.min(), 3))
                M(f"ROp{tag}FPRmax", f(x.fpr.max(), 3))
                M(f"ROp{tag}AlertsMin", thousands(x.alerts_per_h.min()))
                M(f"ROp{tag}AlertsMax", thousands(x.alerts_per_h.max()))
                M(f"ROp{tag}PPVmin", f(x.ppv.min(), 4))
                M(f"ROp{tag}PPVmax", f(x.ppv.max(), 4))
                M(f"ROp{tag}BestTen", f(x.oracle_best_ppv_r10.max(), 3))
    for arm, tag in (("robust", "Rob"), ("coral", "Coral"), ("iw", "Iw"), ("dann", "Dann")):
        a = read(f"arm__{arm}.csv")
        if a is None:
            continue
        a = a[~a.model.isin(["majority", "stratified"])]
        M(f"RArm{tag}SrcMin", rng_txt(a.src_ba)[0])
        M(f"RArm{tag}SrcMax", rng_txt(a.src_ba)[1])
        for v, vt in (("all", "All"), ("clean", "Clean"), ("relab", "Relab")):
            c = f"tgt_ba_{v}"
            if c in a:
                M(f"RArm{tag}{vt}Min", rng_txt(a[c])[0])
                M(f"RArm{tag}{vt}Max", rng_txt(a[c])[1])
                M(f"RArm{tag}{vt}AUCmin", rng_txt(a[f"tgt_auc_{v}"])[0])
                M(f"RArm{tag}{vt}AUCmax", rng_txt(a[f"tgt_auc_{v}"])[1])
                M(f"RArm{tag}{vt}FPRmin", rng_txt(a[f"tgt_fpr_{v}"])[0])
                M(f"RArm{tag}{vt}FPRmax", rng_txt(a[f"tgt_fpr_{v}"])[1])
    iwd = read("arm_diag__iw.csv")
    if iwd is not None:
        M("RIwESSmin", f"{100 * iwd.iw_ess_frac.min():.1f}")
        M("RIwESSmax", f"{100 * iwd.iw_ess_frac.max():.1f}")
        M("RIwDomAcc", f(iwd.iw_domain_acc.mean(), 3))
    rv = read("transfer__reverse.csv")
    if rv is not None:
        for t, tag in (("a", "A"), ("c", "C")):
            x = rv[rv.target == t]
            if len(x):
                M(f"RRev{tag}BAmin", rng_txt(x.tgt_ba)[0])
                M(f"RRev{tag}BAmax", rng_txt(x.tgt_ba)[1])
                M(f"RRev{tag}SrcMin", rng_txt(x.src_ba)[0])
                M(f"RRev{tag}SrcMax", rng_txt(x.src_ba)[1])
    le = read("label_efficient.csv")
    if le is not None:
        for k in sorted(le.k.unique()):
            x = le[(le.k == k) & (le.view == "relab") & (le.variant == "source+k")]
            y = le[(le.k == k) & (le.view == "relab") & (le.variant == "target-only")]
            kw = word(int(k)).capitalize()
            if len(x):
                M(f"RLe{kw}BAmin", rng_txt(x.tgt_ba)[0])
                M(f"RLe{kw}BAmax", rng_txt(x.tgt_ba)[1])
                M(f"RLe{kw}AlertsMin", thousands(x.alerts_at_tau_star_min.min()))
                M(f"RLe{kw}MeetN", str(int(x.draws_meeting_alert_bound.sum())))
            if len(y):
                M(f"RLe{kw}TgtBAmin", rng_txt(y.tgt_ba)[0])
                M(f"RLe{kw}TgtBAmax", rng_txt(y.tgt_ba)[1])
    sz = read("sample_size.csv")
    if sz is not None:
        M("RSzMaxChange", f(sz.abs_change_vs_300k.max()))
        M("RSzNlist", r"150{,}000, 600{,}000, and all " + thousands(1640182))
    extra_numbers()

    # old macros of unchanged experiments
    old_lines = []
    for line in (ROOT / "tables/generated/numbers.tex").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\\newcommand\{\\([A-Za-z]+)\}", line)
        if m and OLD_WHITELIST.match(m.group(1)) and m.group(1) not in MACROS:
            old_lines.append(line)
    out = ["% GENERATED by analysis/make_assets_r1.py. DO NOT EDIT.",
           "% New macros (prefix R): revision-1 experiments EXP-064 ... EXP-075.",
           *[f"\\newcommand{{\\{k}}}{{{v.split('  %')[0]}}}" + (f"  %{v.split('  %')[1]}" if "  %" in v else "")
             for k, v in sorted(MACROS.items())],
           "% Unchanged experiments of the first submission (whitelist, see header).",
           *old_lines]
    (PAPER / "numbers_r1.tex").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"numbers_r1.tex: {len(MACROS)} new, {len(old_lines)} carried over")


TREES = ["tree", "rf", "xgboost", "hgb"]


def extra_numbers():
    """Macros for the prose of the transfer and alert sections."""
    tr = read("transfer__shared.csv")
    if tr is not None:
        for v, tag in (("clean", "Clean"), ("relab", "Relab"), ("all", "All")):
            b = tr[(tr.target == "b") & (tr.view == v)].set_index("model")
            t = b.loc[[m for m in TREES if m in b.index]]
            M(f"RTrTree{tag}BAmin", rng_txt(t.tgt_ba)[0])
            M(f"RTrTree{tag}BAmax", rng_txt(t.tgt_ba)[1])
            M(f"RTrTree{tag}Dmin", rng_txt(t.d_ba)[0])
            M(f"RTrTree{tag}Dmax", rng_txt(t.d_ba)[1])
            for m in ("logreg", "mlp"):
                if m in b.index:
                    M(f"RTr{LABEL[m]}{tag}BA", f(b.loc[m].tgt_ba))
                    M(f"RTr{LABEL[m]}{tag}D", f(b.loc[m].d_ba))
        c = tr[tr.target == "c"]
        M("RTrCSigNbN", word(int((c.p_nb_holm < 0.05).sum())))
        pc = pd.read_csv(RES / "EXP-064/consolidated__a_to_b_bz_c__shared/per_category_recall.csv")
        pc = pc[pc.domain == "c"].groupby("model").mean(numeric_only=True).loc[NONTRIVIAL]
        for col, tag in (("syn_flood", "Syn"), ("icmp_flood", "Icmp"), ("pfcp_deletion", "Pfcp")):
            M(f"RC{tag}Min", f(pc[col].min()))
            M(f"RC{tag}Max", f(pc[col].max()))
        M("RCBkgMax", f(pc["background"].max()))
        M("RCFPRmin", rng_txt(c.tgt_fpr)[0])
        M("RCFPRmax", rng_txt(c.tgt_fpr)[1])
    test = read("test__shared.csv")
    if test is not None:
        b = test[(test.target == "b")]
        for v, tag in (("clean", "Clean"), ("relab", "Relab")):
            x = b[b.view == v].set_index("model")
            for m in NONTRIVIAL:
                M(f"RJoint{LABEL[m]}{tag}", str(int(x.loc[m].alert_splits_meeting_all)))
                M(f"ROracle{LABEL[m]}{tag}PPV", f(x.loc[m].oracle_best_ppv))
                M(f"ROracle{LABEL[m]}{tag}Alerts", thousands(x.loc[m].oracle_min_alerts))
                M(f"RTest{LABEL[m]}{tag}Alerts", thousands(x.loc[m].alert_alerts_per_h))
                M(f"RTest{LABEL[m]}{tag}PPV", f(x.loc[m].alert_ppv))
                M(f"RTest{LABEL[m]}{tag}Recall", f(x.loc[m].alert_recall))
            M(f"RJointZero{tag}N", word(int((x.alert_splits_meeting_all == 0).sum())))
    # the first submission's clean-label transfer, before the byte correction
    old = (ROOT / "tables/generated/numbers.tex").read_text(encoding="utf-8")
    for name, new in (("TrCleanTgtBAmin", "RPrevCleanBAmin"), ("TrCleanTgtBAmax", "RPrevCleanBAmax"),
                      ("TrCleanOthMin", "RPrevCleanOthMin"), ("TrCleanOthMax", "RPrevCleanOthMax"),
                      ("TrCleanLR", "RPrevCleanLR"), ("TrTgtBAmin", "RPrevAllBAmin"),
                      ("TrTgtBAmax", "RPrevAllBAmax"), ("DomRobust", "RPrevDomRobust")):
        mm = re.search(r"\\newcommand\{\\" + name + r"\}\{([^}]*)\}", old)
        if mm:
            M(new, mm.group(1), f"first submission ({name}), before D-035")
    mt = read("reference_vs_transfer.csv")
    if mt is not None:
        for v, tag in (("clean", "Clean"), ("relab", "Relab")):
            x = mt[(mt.view == v) & mt.model.isin(TREES)]
            if len(x):
                M(f"RGapTree{tag}Min", rng_txt(x.point)[0])
                M(f"RGapTree{tag}Max", rng_txt(x.point)[1])
    za = read("zeek_vs_argus.csv")
    if za is not None:
        z = za[(za.view == "clean")].set_index("model")
        t = z.loc[[m for m in TREES if m in z.index]]
        M("RZkTreeCleanDiffMin", rng_txt(t["diff"])[0])
        M("RZkTreeCleanDiffMax", rng_txt(t["diff"])[1])
        M("RZkTreeCleanBAmin", rng_txt(t.zeek_ba)[0])
        M("RZkTreeCleanBAmax", rng_txt(t.zeek_ba)[1])
    nj = json.loads((RES / "EXP-075/numbers.json").read_text())
    M("RNbRatioGroups", f(nj.get("shared_nb_ratio_groups", np.nan)))
    M("RRadRatioSess", f(nj.get("radio_ratio_groups_sessions", np.nan)))
    M("RRadRatioRun", f(nj.get("radio_ratio_groups_runs", np.nan)))
    # adaptation arms, per model (clean view)
    for arm, tag in (("shared", "Plain"), ("robust", "Rob"), ("iw", "Iw"), ("coral", "Coral"),
                     ("dann", "Dann")):
        a = read(f"arm__{arm}.csv")
        if a is None:
            continue
        a = a.set_index("model")
        for m in [x for x in NONTRIVIAL + ["dann"] if x in a.index]:
            M(f"RArm{tag}{LABEL[m]}Clean", f(a.loc[m].tgt_ba_clean))
            M(f"RArm{tag}{LABEL[m]}Src", f(a.loc[m].src_ba))
            M(f"RArm{tag}{LABEL[m]}CleanFPR", f(a.loc[m].tgt_fpr_clean))
        t = a.loc[[m for m in TREES if m in a.index]] if arm != "dann" else None
        if t is not None and len(t):
            M(f"RArm{tag}TreeCleanMin", rng_txt(t.tgt_ba_clean)[0])
            M(f"RArm{tag}TreeCleanMax", rng_txt(t.tgt_ba_clean)[1])
            M(f"RArm{tag}TreeFPRmin", rng_txt(t.tgt_fpr_clean)[0])
            M(f"RArm{tag}TreeFPRmax", rng_txt(t.tgt_fpr_clean)[1])
    # label-efficient arm
    le = read("label_efficient.csv")
    tr = read("transfer__shared.csv")
    if le is not None:
        nl = [m for m in NONTRIVIAL if m != "logreg"]
        for k in sorted(le.k.unique()):
            kw = word(int(k)).capitalize()
            for variant, vt in (("source+k", "Src"), ("target-only", "Tgt")):
                x = le[(le.k == k) & (le.view == "relab") & (le.variant == variant)].set_index("model")
                if x.empty:
                    continue
                y = x.loc[[m for m in nl if m in x.index]]
                M(f"RLe{vt}{kw}NlMin", rng_txt(y.tgt_ba)[0])
                M(f"RLe{vt}{kw}NlMax", rng_txt(y.tgt_ba)[1])
                if "logreg" in x.index:
                    M(f"RLe{vt}{kw}LR", f(x.loc["logreg"].tgt_ba))
                M(f"RLe{vt}{kw}Meet", str(int(x.draws_meeting_alert_bound.sum())))
                M(f"RLe{vt}{kw}Cells", str(int(x.draws.sum())))
                M(f"RLe{vt}{kw}AlertsMin", thousands(x.alerts_at_tau_star.min()))
                M(f"RLe{vt}{kw}AlertsMax", thousands(x.alerts_at_tau_star.max()))
        if tr is not None:
            z = tr[(tr.target == "b") & (tr.view == "relab")].set_index("model")
            y = z.loc[[m for m in NONTRIVIAL if m != "logreg"]]
            M("RLeZeroNlMin", rng_txt(y.tgt_ba)[0])
            M("RLeZeroNlMax", rng_txt(y.tgt_ba)[1])
            M("RLeZeroMLP", f(z.loc["mlp"].tgt_ba))
        x1 = le[(le.k == 1) & (le.view == "relab") & (le.variant == "source+k")].set_index("model")
        if "mlp" in x1.index:
            M("RLeSrcOneMLP", f(x1.loc["mlp"].tgt_ba))
        x8 = le[(le.k == 8) & (le.view == "relab") & (le.variant == "source+k")].set_index("model")
        for m in NONTRIVIAL:
            if m in x8.index:
                M(f"RLeSrcEight{LABEL[m]}Alerts", thousands(x8.loc[m].alerts_at_tau_star))
                M(f"RLeSrcEight{LABEL[m]}Meet", str(int(x8.loc[m].draws_meeting_alert_bound)))
                M(f"RLeSrcEight{LABEL[m]}Recall", f(x8.loc[m].recall_at_tau_star))
    # reference on the two UDP-flood files when each is held out (R1.5)
    import glob as _glob
    fl = []
    for lab, v in (("clean", "clean"), ("relab", "relab")):
        for q in _glob.glob(str(RES / f"EXP-068/lofo__{lab}*/raw/runs.csv")):
            r = pd.read_csv(q)
            fl.append(r[r.unit.isin(["file5", "file15"]) & (r.view == v)
                        & ~r.model.isin(["majority", "stratified"])])
    if fl:
        fl = pd.concat(fl)
        M("RLofoFloodMin", f(fl.balanced_accuracy.min(), 3))
        M("RLofoFloodMax", f(fl.balanced_accuracy.max(), 3))
    sz = read("sample_size_all.csv")
    if sz is not None:
        ch = sz[sz.view.isin(["clean"]) & (sz.n != 300_000)]
        M("RSzMaxChangeClean", f(ch.abs_change_vs_300k.max()))
        M("RSzSplits", word(int(sz.splits.max())))


# ---------------------------------------------------------------- tables
def table_static():
    TAB.mkdir(parents=True, exist_ok=True)
    gen = ROOT / "tables/generated"
    # corpora: the first submission's table with the group and role rows updated
    s = (gen / "rev_corpora.tex").read_text(encoding="utf-8")
    s = s.replace(r"Groups & 318 hosts & 30 sessions & 20 files & 3 files \\",
                  r"Groups & 318 hosts & 30 sess.\ (42 runs) & 20 files & 3 files \\")
    s = s.replace(r"Role & train, test & train, test & target & target \\",
                  r"Bytes counted & IP & -- & Eth.$^{\ast}$ & Eth.+GTP-U$^{\ast}$ \\" "\n"
                  r"Role & train, test & train, test & target, ref. & target \\")
    s = s.replace(r"\end{tabular}",
                  r"\end{tabular}" "\n" r"\\[2pt]{\scriptsize $^{\ast}$Ethernet header (and GTP-U) removed per packet (Section~\ref{sec:shared}).}")
    (TAB / "corpora.tex").write_text(s, encoding="utf-8")
    # conflicts and RIC loop: unchanged experiments
    shutil.copy(gen / "rev_conflict.tex", TAB / "conflict.tex")
    shutil.copy(gen / "rev_ric.tex", TAB / "ric.tex")
    # published ladder without the 'Pass' column of the first test
    s = (gen / "rev_ladder.tex").read_text(encoding="utf-8")
    s = s.replace(r"\begin{tabular}{lllcccccccc}", r"\begin{tabular}{lllccccccc}")
    s = s.replace(r"& \multicolumn{2}{c}{RF, w/o copies} & \\", r"& \multicolumn{2}{c}{RF, w/o copies} \\")
    s = re.sub(r" & Pass \\\\", r" \\\\", s)
    s = re.sub(r" & \d / \d \\\\", r" \\\\", s)
    (TAB / "ladder.tex").write_text(s, encoding="utf-8")
    # shared feature space, with the byte correction stated
    rows = [("duration", "duration", "Dur", "base"),
            ("src\\_bytes", "src\\_ip\\_bytes", "SrcBytes $-$ 14\\,SrcPkts", "base"),
            ("dst\\_bytes", "dst\\_ip\\_bytes", "DstBytes $-$ 14\\,DstPkts", "base"),
            ("src\\_pkts", "src\\_pkts", "SrcPkts", "base"),
            ("dst\\_pkts", "dst\\_pkts", "DstPkts", "base"),
            ("tot\\_pkts", "src\\_pkts + dst\\_pkts", "TotPkts", "base"),
            ("tot\\_bytes", "src + dst ip\\_bytes", "src\\_bytes + dst\\_bytes", "base"),
            ("proto", "proto", "Proto", "one-hot (4)")]
    der = [("mean\\_pkt\\_size", "tot\\_bytes / max(tot\\_pkts, 1)"),
           ("src\\_mean\\_pkt\\_size", "src\\_bytes / max(src\\_pkts, 1)"),
           ("dst\\_mean\\_pkt\\_size", "dst\\_bytes / max(dst\\_pkts, 1)"),
           ("bytes\\_per\\_s", "tot\\_bytes / max(duration, 1\\,ms)"),
           ("pkts\\_per\\_s", "tot\\_pkts / max(duration, 1\\,ms)"),
           ("src\\_byte\\_ratio", "src\\_bytes / max(tot\\_bytes, 1)"),
           ("src\\_pkt\\_ratio", "src\\_pkts / max(tot\\_pkts, 1)")]
    out = [r"\begin{tabular}{llll}", r"\toprule", r"Concept & \DA{} (Zeek) & \DB{} (Argus) & Role \\", r"\midrule"]
    out += [f"{a} & {b} & {c} & {d} \\\\" for a, b, c, d in rows]
    out += [f"{a} & \\multicolumn{{2}}{{c}}{{{b}}} & derived \\\\" for a, b in der]
    out += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "features.tex").write_text("\n".join(out) + "\n", encoding="utf-8")


def cell(v, d=3):
    return "--" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{d}f}"


def sig(p):
    return r"$^{\ast}$" if p is not None and not np.isnan(p) and p < 0.05 else ""


def table_transfer():
    tr = read("transfer__shared.csv")
    if tr is None:
        return
    mt = read("reference_vs_transfer.csv")
    triv = read("trivial__shared.csv")
    b = tr[tr.target == "b"]
    out = [r"\begin{tabular}{lcccccccc}", r"\toprule",
           r" & Source & All flows & \multicolumn{2}{c}{Clean} & \multicolumn{2}{c}{Relabeled} & \multicolumn{2}{c}{Reference (LOFO), clean} \\",
           r"\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}",
           r"Model & BA & BA & BA & $\Delta_{\mathrm{BA}}$ [95\% CI] & BA & $\Delta_{\mathrm{BA}}$ [95\% CI] & BA & Ref.$-$transfer [95\% CI] \\",
           r"\midrule"]
    for m in NONTRIVIAL:
        a = b[(b.model == m) & (b.view == "all")]
        c = b[(b.model == m) & (b.view == "clean")]
        r = b[(b.model == m) & (b.view == "relab")]
        if a.empty:
            continue
        a, c, r = a.iloc[0], (c.iloc[0] if len(c) else None), (r.iloc[0] if len(r) else None)
        g = mt[(mt.model == m) & (mt.view == "clean")] if mt is not None else pd.DataFrame()
        g = g.iloc[0] if len(g) else None
        row = [LABEL[m], cell(a.src_ba), cell(a.tgt_ba)]
        for x in (c, r):
            if x is None:
                row += ["--", "--"]
            else:
                row += [cell(x.tgt_ba), f"{sg(x.d_ba)}{sig(x.p_nb_holm)} {ci(x.nb_lo, x.nb_hi)}"]
        row += (["--", "--"] if g is None else
                [cell(g.ref_ba), f"{sg(g.point)}{sig(g.p_holm)} {ci(g.lo, g.hi)}"])
        out.append(" & ".join(row) + r" \\")
    if triv is not None:
        for m in ("stratified", "majority"):
            s = triv[(triv.model == m) & (triv.domain == "source_heldout")].balanced_accuracy
            t = triv[(triv.model == m) & (triv.domain == "b")].balanced_accuracy
            if len(s) and len(t):
                out.append(f"{LABEL[m]} & {cell(float(s.iloc[0]))} & {cell(float(t.iloc[0]))} & -- & -- & -- & -- & -- & -- \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "transfer.tex").write_text("\n".join(out) + "\n", encoding="utf-8")


def table_arms():
    rows = []
    for arm, lab in (("shared", "Shared space (18)"), ("robust", "Exporter-robust (9)"),
                     ("iw", "Importance weighting"), ("coral", "CORAL"), ("dann", "DANN")):
        a = read(f"arm__{arm}.csv")
        if a is None:
            continue
        a = a[~a.model.isin(["majority", "stratified"])]
        order = [m for m in NONTRIVIAL + ["dann"] if m in set(a.model)]
        for i, m in enumerate(order):
            x = a[a.model == m].iloc[0]
            rows.append(f"{lab if i == 0 else ''} & {LABEL[m]} & {cell(x.src_ba)} & "
                        f"{cell(x.get('tgt_ba_clean'))} & {cell(x.get('tgt_auc_clean'))} & "
                        f"{cell(x.get('tgt_fpr_clean'))} & {cell(x.get('tgt_ba_relab'))} \\\\")
        rows.append(r"\midrule")
    if not rows:
        return
    rows = rows[:-1]
    out = [r"\begin{tabular}{llccccc}", r"\toprule",
           r"Arm & Model & Src.\ BA & \multicolumn{3}{c}{Target, clean} & Target, relab. \\",
           r"\cmidrule(lr){4-6}", r" & & & BA & AUC & FPR & BA \\", r"\midrule", *rows,
           r"\bottomrule", r"\end{tabular}"]
    (TAB / "arms.tex").write_text("\n".join(out) + "\n", encoding="utf-8")


def table_third():
    tr = read("transfer__shared.csv")
    rv = read("transfer__reverse.csv")
    if tr is None:
        return
    pc = pd.read_csv(RES / "EXP-064/consolidated__a_to_b_bz_c__shared/per_category_recall.csv")
    pc = pc[pc.domain == "c"]
    out = [r"\begin{tabular}{lccccccccc}", r"\toprule",
           r" & \multicolumn{7}{c}{Trained on \DA{}} & \multicolumn{2}{c}{Trained on \DB{}} \\",
           r"\cmidrule(lr){2-8}\cmidrule(lr){9-10}",
           r"Model & Src.\ BA & Tgt.\ BA & AUC & SYN & ICMP & PFCP & Bkg. & Tgt.\ BA & AUC \\",
           r"\midrule"]
    for m in NONTRIVIAL:
        x = tr[(tr.target == "c") & (tr.model == m)]
        if x.empty:
            continue
        x = x.iloc[0]
        p = pc[pc.model == m].mean(numeric_only=True)
        bkg = p.get("background", np.nan)           # per_category_recall gives the flagged share for non-"benign" categories
        y = rv[(rv.target == "c") & (rv.model == m)] if rv is not None else pd.DataFrame()
        yb = cell(y.iloc[0].tgt_ba) if len(y) else "--"
        ya = cell(y.iloc[0].tgt_auc) if len(y) else "--"
        out.append(f"{LABEL[m]} & {cell(x.src_ba)} & {cell(x.tgt_ba)} & {cell(x.tgt_auc)} & "
                   f"{cell(p.get('syn_flood'), 2)} & {cell(p.get('icmp_flood'), 2)} & "
                   f"{cell(p.get('pfcp_deletion'), 2)} & {cell(bkg, 2)} & {yb} & {ya} \\\\")
    out += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "third.tex").write_text("\n".join(out) + "\n", encoding="utf-8")


def outcome(o):
    return {"pass": r"pass", "fail": r"$\times$", "inconclusive": r"?"}[o]


def table_test():
    t = read("test__shared.csv")
    if t is None:
        return
    t = t[t.target == "b"]
    out = [r"\begin{tabular}{llcccccccc}", r"\toprule",
           r" & & \multicolumn{2}{c}{Generalization} & \multicolumn{5}{c}{Alert burden, threshold fixed on source data} & \\",
           r"\cmidrule(lr){3-4}\cmidrule(lr){5-9}",
           r"View & Model & $\Delta_{\mathrm{BA}}$ [95\% CI] & & Recall [95\% CI] & Alerts/h [95\% CI] & PPV [95\% CI] & Splits & & $\mathcal{P}$ \\",
           r"\midrule"]
    for v, vl in (("all", "All flows"), ("clean", "Clean"), ("relab", "Relabeled")):
        x = t[t.view == v]
        for i, m in enumerate(NONTRIVIAL):
            y = x[x.model == m]
            if y.empty:
                continue
            y = y.iloc[0]
            al = (f"{thousands(y.alert_alerts_per_h)} "
                  f"[{thousands(y.alert_alerts_per_h_lo)}, {thousands(y.alert_alerts_per_h_hi)}]")
            out.append(" & ".join([
                vl if i == 0 else "", LABEL[m],
                f"{sg(y.d_ba, 2)} {ci(y.d_ba_lo, y.d_ba_hi)}", outcome(y.generalization),
                f"{y.alert_recall:.2f} {ci(y.alert_recall_lo, y.alert_recall_hi)}",
                al, f"{y.alert_ppv:.3f} {ci(y.alert_ppv_lo, y.alert_ppv_hi, 3)}",
                f"{int(y.alert_splits_meeting_all)}/{int(y.alert_splits)}",
                outcome(y.alert_alert_term), outcome(y.verdict)]) + r" \\")
        out.append(r"\midrule")
    out = out[:-1] + [r"\bottomrule", r"\end{tabular}"]
    (TAB / "test.tex").write_text("\n".join(out) + "\n", encoding="utf-8")


def table_radio():
    r = read("radio_protocols.csv")
    if r is None:
        return
    out = [r"\begin{tabular}{lcccccc}", r"\toprule",
           r" & \multicolumn{3}{c}{30 sessions} & \multicolumn{3}{c}{42 runs} \\",
           r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
           r"Model & R & GD & Gain [95\% CI] & R & GD & Gain [95\% CI] \\", r"\midrule"]
    for m in NONTRIVIAL + ["stratified", "majority", "average"]:
        cells = [LABEL.get(m, "Average")]
        for g in ("sessions", "runs"):
            x = r[(r.grouping == g) & (r.comparison == "R-SD") & (r.model == m)].iloc[0]
            if m == "average":
                cells += ["", "", f"{sg(x.gain)} {ci(x.lo_groups, x.hi_groups)}"]
            else:
                cells += [f"{x.random:.3f}", f"{x.other:.3f}",
                          f"{sg(x.gain)}{sig(x.get('p_groups_holm'))} {ci(x.lo_groups, x.hi_groups)}"]
        if m == "average":
            out.append(r"\midrule")
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "radio.tex").write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- figures
COL = 3.45


def style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "mathtext.fontset": "stixsans", "font.size": 8, "axes.labelsize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42})


INK, MUTE, TEAL, COR, BLUE, GRN = "#272B2E", "#8A9095", "#3C7D85", "#E2795E", "#4B7FAF", "#7FA86B"


def fig_transfer():
    tr = read("transfer__shared.csv")
    mt = read("reference_vs_transfer.csv")
    if tr is None:
        return
    b = tr[tr.target == "b"]
    fig, ax = plt.subplots(figsize=(COL, 2.6))
    y0 = np.arange(len(NONTRIVIAL))[::-1]
    off = {"all": 0.22, "clean": 0.0, "relab": -0.22}
    col = {"all": MUTE, "clean": TEAL, "relab": COR}
    for i, m in enumerate(NONTRIVIAL):
        src = b[(b.model == m) & (b.view == "all")]
        if src.empty:
            continue
        ax.plot(src.src_ba.iloc[0], y0[i], marker="o", mfc="white", mec=INK, ms=4.5, ls="none",
                label="held-out source" if i == 0 else None, zorder=4)
        for v in ("all", "clean", "relab"):
            x = b[(b.model == m) & (b.view == v)]
            if x.empty:
                continue
            x = x.iloc[0]
            ax.errorbar(x.tgt_ba, y0[i] + off[v], xerr=[[x.tgt_ba - x.tgt_ba_lo], [x.tgt_ba_hi - x.tgt_ba]],
                        fmt="o", ms=3.6, color=col[v], elinewidth=0.8, capsize=0,
                        label={"all": "5G-NIDD, all flows", "clean": "5G-NIDD, clean",
                               "relab": "5G-NIDD, relabeled"}[v] if i == 0 else None, zorder=3)
        if mt is not None:
            g = mt[(mt.model == m) & (mt.view == "clean")]
            if len(g):
                ax.plot([g.ref_ba.iloc[0]] * 2, [y0[i] - 0.36, y0[i] + 0.36], color=INK, lw=1.2,
                        label="reference (LOFO), clean" if i == 0 else None)
    ax.axvline(0.5, color=MUTE, ls="--", lw=0.6)
    ax.set_yticks(y0)
    ax.set_yticklabels([LABEL[m] for m in NONTRIVIAL])
    ax.set_xlabel("Balanced accuracy")
    ax.set_xlim(0.35, 1.01)
    ax.legend(loc="lower left", frameon=False, ncol=1, bbox_to_anchor=(0.0, 0.0))
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / "fig_transfer.pdf")
    plt.close(fig)


def fig_shift():
    old = pd.read_csv(RES / "EXP-045/processed/feature_shift.csv")
    new = pd.read_csv(RES / "EXP-074/argus_corrected/processed/feature_shift.csv")
    zk = pd.read_csv(RES / "EXP-074/zeek/processed/feature_shift.csv")
    m = old[["feature", "robust", "w1_source_quantile"]].merge(
        new[["feature", "w1_source_quantile"]], on="feature", suffixes=("_old", "_new")).merge(
        zk[["feature", "w1_source_quantile"]].rename(columns={"w1_source_quantile": "w1_zk"}), on="feature")
    m = m.sort_values("w1_source_quantile_new")
    fig, ax = plt.subplots(figsize=(COL, 2.9))
    y = np.arange(len(m))
    ax.scatter(m.w1_source_quantile_old, y, marker="|", s=40, color=MUTE, label="Argus, uncorrected bytes")
    ax.scatter(m.w1_source_quantile_new, y, s=14, color=np.where(m.robust, TEAL, "white"),
               edgecolors=TEAL, linewidths=0.8, label="Argus, Ethernet header removed", zorder=3)
    ax.scatter(m.w1_zk, y, marker="x", s=12, color=COR, linewidths=0.8, label="Zeek re-extraction", zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(m.feature.str.replace("_", r"\_").map(lambda s: s.replace(r"\_", "_")), fontsize=6)
    ax.set_xlabel(r"$W_1$ per column after a source-fitted quantile map")
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / "fig_shift.pdf")
    plt.close(fig)


def fig_test():
    t = read("test__shared.csv")
    if t is None:
        return
    fig, axes = plt.subplots(1, 2, figsize=(COL * 2.05, 2.4), sharey=True)
    for ax, v, title in zip(axes, ("clean", "relab"), ("(a) 5G-NIDD, clean", "(b) 5G-NIDD, relabeled")):
        x = t[(t.target == "b") & (t.view == v)]
        ax.axvspan(1e0, C.A_MAX, ymin=0, ymax=1, color=GRN, alpha=0.08, lw=0)
        ax.axvline(C.A_MAX, color=INK, ls=":", lw=0.8)
        ax.axhline(C.RHO, color=INK, ls=":", lw=0.8)
        for _, y in x.iterrows():
            lab = LABEL[y.model]
            xv = max(y.alert_alerts_per_h, 1.0)
            ax.errorbar(xv, y.alert_ppv,
                        xerr=[[xv - max(y.alert_alerts_per_h_lo, 1.0)], [max(y.alert_alerts_per_h_hi, 1.0) - xv]],
                        yerr=[[y.alert_ppv - y.alert_ppv_lo], [y.alert_ppv_hi - y.alert_ppv]],
                        fmt="o", ms=3.5, color=TEAL, elinewidth=0.6, capsize=0)
            ax.annotate(lab, (xv, y.alert_ppv), fontsize=6, xytext=(3, 2), textcoords="offset points")
            if not np.isnan(y.oracle_min_alerts):
                ox, oy = max(y.oracle_min_alerts, 1.0), y.oracle_best_ppv
                ax.plot([xv, ox], [y.alert_ppv, oy], color=COR, lw=0.5, ls=(0, (2, 1.5)), zorder=1)
                ax.plot(ox, oy, marker="o", mfc="white", mec=COR, ms=3.5, ls="none", zorder=4)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(1, 3e5)
        ax.set_ylim(1e-3, 1.2)
        ax.set_title(title, fontsize=7.5, loc="left")
        ax.set_xlabel(r"False alerts per hour at $\lambda_b$ = 240,000 flows/h")
    axes[0].set_ylabel(r"Operational precision at $\pi$ = 0.002")
    axes[1].plot([], [], "o", color=TEAL, ms=3.5, label="threshold fixed on source (95% CI)")
    axes[1].plot([], [], "o", mfc="white", mec=COR, ms=3.5, label="threshold searched on target (bound)")
    axes[1].legend(loc="lower right", frameon=False)
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / "fig_test.pdf")
    plt.close(fig)


def fig_label_efficient():
    le = read("label_efficient.csv")
    tr = read("transfer__shared.csv")
    if le is None:
        return
    fig, axes = plt.subplots(1, 2, figsize=(COL * 2.05, 2.2))
    ks = sorted(le.k.unique())
    for m, c in zip(NONTRIVIAL, [BLUE, MUTE, GRN, TEAL, COR, INK]):
        x = le[(le.model == m) & (le.view == "relab") & (le.variant == "source+k")].sort_values("k")
        x0 = tr[(tr.target == "b") & (tr.view == "relab") & (tr.model == m)] if tr is not None else None
        kk = list(x.k)
        ba = list(x.tgt_ba)
        al = list(x.alerts_at_tau_star)
        if x0 is not None and len(x0):
            kk, ba = [0] + kk, [x0.tgt_ba.iloc[0]] + ba
        axes[0].plot(kk, ba, marker="o", ms=3, lw=0.9, color=c, label=LABEL[m])
        axes[1].plot(list(x.k), np.maximum(al, 1), marker="o", ms=3, lw=0.9, color=c)
    axes[0].set_xticks([0] + ks)
    axes[1].set_xticks(ks)
    axes[0].set_xlabel("Labeled 5G-NIDD capture files in training, $k$")
    axes[1].set_xlabel("Labeled 5G-NIDD capture files in training, $k$")
    axes[0].set_ylabel("BA on held-out files (relabeled)")
    axes[1].set_ylabel("False alerts/h, source-fixed threshold")
    axes[1].set_yscale("log")
    axes[1].axhline(C.A_MAX, color=INK, ls=":", lw=0.8)
    axes[1].text(ks[-1], C.A_MAX * 1.15, r"$A_{\max}$", ha="right", fontsize=6.5)
    axes[0].legend(loc="lower right", frameon=False, ncol=2)
    axes[0].set_title("(a)", fontsize=7.5, loc="left")
    axes[1].set_title("(b)", fontsize=7.5, loc="left")
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / "fig_label_efficient.pdf")
    plt.close(fig)


def fig_benign():
    """FPR on each benign radio session held out alone (EXP-053, unchanged data).

    Revision 1 (R1.3): no axis in false alerts per UE-hour; the radio layer
    supports no operating figure."""
    B = pd.read_csv(RES / "EXP-052/processed/drift_v3_benign.csv").sort_values("day").reset_index(drop=True)
    x = np.arange(len(B)).astype(float)
    x[-1] += 0.8
    fig, ax = plt.subplots(figsize=(COL, 2.0))
    ax.vlines(x, B.fpr_min, B.fpr_max, color=INK, lw=1.0, zorder=2)
    ax.plot(x, B.fpr_min, ls="none", marker="_", ms=5, color=INK, zorder=2)
    ax.plot(x, B.fpr_max, ls="none", marker="_", ms=5, color=INK, zorder=2)
    late = (B.day > 30).to_numpy()
    ax.plot(x[~late], B.fpr_mean[~late], ls="none", marker="o", ms=4.6, mfc=BLUE, mec=BLUE,
            label="first week (days 0 to 6)", zorder=3)
    ax.plot(x[late], B.fpr_mean[late], ls="none", marker="D", ms=4.2, mfc=COR, mec=COR,
            label="attack period (day 53)", zorder=3)
    ax.axvline((x[-2] + x[-1]) / 2, color=MUTE, lw=0.6, ls=(0, (3, 2)))
    ax.text((x[-2] + x[-1]) / 2, 0.5, "47-day gap", rotation=90, ha="right", va="center",
            fontsize=6.5, color=INK)
    ax.set_xticks(x, [f"{int(v)}" for v in B.session])
    ax.set_xlabel("Held-out benign session (ordered by capture day)")
    ax.set_ylabel("False positive rate")
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlim(x[0] - 0.6, x[-1] + 0.6)
    ax.yaxis.grid(True, lw=0.3, color="#D6D9DC", zorder=0)
    ax.legend(loc="upper left", fontsize=6.5, handletextpad=0.2, frameon=False)
    fig.tight_layout(pad=0.3)
    fig.savefig(FIG / "fig_benign.pdf")
    plt.close(fig)


def main() -> int:
    PAPER.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    shutil.copy(PAPER / "_preamble_from_submission.tex", PAPER / "preamble_r1.tex")
    style()
    numbers()
    table_static()
    for fn in (table_transfer, table_arms, table_third, table_test, table_radio,
               fig_transfer, fig_shift, fig_test, fig_label_efficient, fig_benign):
        try:
            fn()
        except Exception as e:                     # partial results: report, go on
            print(f"  [skip] {fn.__name__}: {type(e).__name__}: {e}")
    print(f"wrote {PAPER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
