#!/usr/bin/env python3
"""EXP-000 artefact generator: docs/CLAIM_EVIDENCE_MATRIX.csv.

Every claim currently in paper/main.tex, bound to the experiment that could
evidence it, the literature that constrains it, and the wording that is allowed
given today's evidence. At Phase 0 no experiment has run, so every 'result' cell
reads 'none yet' and every classification is 'not_established'. That is the point:
the manuscript's numbers are synthetic, so no claim in it is currently evidenced.

Classification vocabulary (master protocol section 19):
  proved | strong_empirical | moderate_empirical | suggestive |
  not_established | contradicted
"""
import csv
import pathlib

COLS = ["claim_id", "claim_text_in_manuscript", "experiment", "metric", "artefact",
        "result_today", "classification", "confidence", "literature_support",
        "literature_constraint", "falsified_if", "limitation", "allowed_wording_today",
        "action_required"]

R = []


def add(**kw):
    R.append({c: kw.get(c, "") for c in COLS})


NONE = "none yet - no experiment has been executed"

add(claim_id="C1",
    claim_text_in_manuscript="All five architectures exceed 98% F1 in distribution on D_A",
    experiment="EXP-003 / E1a", metric="Acc, P, R, F1, ROC-AUC",
    artefact="tables/generated/indist.tex", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="P03 reports strong in-distribution performance on this corpus; P05 reports F1 94.87% (O-CU) and 99.49% (O-DU)",
    literature_constraint="High in-distribution scores on this corpus are expected and unremarkable. The claim carries no weight on its own; it exists only to set up the transfer contrast",
    falsified_if="any architecture falls below the majority-class baseline",
    limitation="a majority-class floor must be reported alongside it, or the number is uninterpretable (plan I5)",
    allowed_wording_today="none - do not state a number",
    action_required="run EXP-003 with the B0 majority baseline included")

add(claim_id="C2",
    claim_text_in_manuscript="Every model loses 27-37 points of F1 under cross-deployment transfer",
    experiment="EXP-004 / E1b", metric="delta_f1",
    artefact="tables/generated/cross.tex, figures/generated/fig_gen.pdf",
    result_today=NONE, classification="not_established", confidence="none",
    literature_support="P14 (2026) reports cross-domain generalisation failure for lightweight IDS on IIoT corpora; a large NIDS literature reports the same phenomenon",
    literature_constraint="The phenomenon is NOT novel. Only its measurement for an O-RAN detector, jointly with the deployment criteria, is ours. P14 further reports the evaluation protocol can reverse which target appears harder, so the ordering across architectures may be unstable",
    falsified_if="the 95% CI on delta_f1 includes 0 for any architecture",
    limitation="the magnitude is confounded with exporter differences unless D-004 resolves in favour of a single exporter",
    allowed_wording_today="none - do not state a number or a range",
    action_required="resolve D-004; run EXP-004; add the I12 ordering-stability test")

add(claim_id="C3",
    claim_text_in_manuscript="Degradation is not an artefact of one corpus (reverse transfer is comparably poor)",
    experiment="EXP-004 / E1c", metric="delta_f1 reverse", artefact="text",
    result_today=NONE, classification="not_established", confidence="none",
    literature_support="none retrieved - no O-RAN IDS study performs transfer in either direction",
    literature_constraint="",
    falsified_if="reverse transfer is materially better, indicating D_B is simply an easier corpus",
    limitation="D_B has no radio features, so reverse transfer runs on the shared 24-feature space only and is not symmetric with the forward direction",
    allowed_wording_today="none",
    action_required="run EXP-004 B-to-A; state the asymmetry explicitly")

add(claim_id="C4",
    claim_text_in_manuscript="Errors are false-negative dominated under transfer",
    experiment="EXP-004 / E1b", metric="confusion matrix",
    artefact="figures/generated/fig_conf.pdf", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="P03 reports 27-46% DoS-to-Benign confusion on this corpus, which is the same direction of error",
    literature_constraint="P03 attributes their confusion to windowed statistical aggregation, not to model capacity. If we reproduce it we must not attribute it to transfer without ruling out windowing first",
    falsified_if="errors are FP dominated, or the FN dominance disappears when windowing changes",
    limitation="confounded with our A12 windowing policy",
    allowed_wording_today="none",
    action_required="run EXP-004; run a windowing sensitivity check before attributing the asymmetry to transfer")

add(claim_id="C5",
    claim_text_in_manuscript="Radio KPIs raise in-distribution F1 and lower cross-deployment F1",
    experiment="EXP-005 / E2", metric="f1_indist, f1_cross",
    artefact="tables/generated/ablation.tex", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="P03 establishes the in-distribution half on this exact corpus: radio features match or exceed network flows",
    literature_constraint="RESCOPE REQUIRED. The first half is prior work. Only the sign-flip under transfer is ours, and it is untested by anyone",
    falsified_if="the two deltas share a sign, meaning no trade-off exists",
    limitation="contingent on D_A actually exposing joinable radio telemetry (EXP-001); if the CU-DU join fails, this claim is withdrawn, not weakened",
    allowed_wording_today="none",
    action_required="rescope the claim text to the transfer half; cite P03 for the in-distribution half; run EXP-005")

add(claim_id="C6",
    claim_text_in_manuscript="Models are miscalibrated under transfer",
    experiment="EXP-007 / E3a", metric="ECE, reliability curve",
    artefact="figures/generated/fig_calib.pdf", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="none retrieved - no O-RAN IDS study reports calibration",
    literature_constraint="",
    falsified_if="cross-deployment ECE is within the bootstrap CI of the in-distribution ECE",
    limitation="ECE is bin-sensitive; bootstrap CIs are mandatory (plan I7)",
    allowed_wording_today="none",
    action_required="run EXP-007 with bootstrap CIs")

add(claim_id="C7",
    claim_text_in_manuscript="Prior correction reduces ECE but not F1",
    experiment="EXP-007 / E3b", metric="ECE pre/post", artefact="text",
    result_today=NONE, classification="not_established", confidence="none",
    literature_support="standard result: neither temperature scaling nor prior correction is order-reversing",
    literature_constraint="the F1-unchanged part is a mathematical property, not an empirical finding, and must be stated as such",
    falsified_if="F1 changes materially, which would indicate an implementation error",
    limitation="requires pi_tr, the training prevalence, which is a property of the capture session rather than of any deployment",
    allowed_wording_today="the F1-invariance may be stated as a property; the ECE reduction may not be quantified",
    action_required="run EXP-007")

add(claim_id="C8",
    claim_text_in_manuscript="The default threshold yields operationally unusable precision",
    experiment="EXP-006 / E4", metric="alerts_per_hour, PPV",
    artefact="figures/generated/fig_alerts.pdf", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="P13 (Axelsson 2000) is the foundational analytical result; P19 restates it; P06 reports 0.6% FPR with no flow rate attached",
    literature_constraint="The base-rate argument is 26 years old. Novelty cannot be the fallacy. Only the O-RAN quantification under measured transfer degradation is ours",
    falsified_if="PPV at tau=0.5 exceeds rho across the whole pi sweep",
    limitation="lambda_b = 240000 flows/hour is a DECLARED parameter, not a measurement; pi is a modelling assumption. Both must be swept and both must be labelled as declared",
    allowed_wording_today="the framing may cite Axelsson; no number may be stated",
    action_required="run EXP-006; report alerts per 10^5 benign flows as well as absolute alerts per hour")

add(claim_id="C9",
    claim_text_in_manuscript="Only the gradient-boosted ensemble meets the p99 budget",
    experiment="EXP-009 / E5a", metric="q99_latency_ms",
    artefact="tables/generated/runtime.tex", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="P04 (ICCCN 2026) measures a real FlexRIC xApp against the same 10 ms budget and reports p95 compliance; P05 measures ~600-850 ms against a 1000 ms budget",
    literature_constraint="CRITICAL RESCOPE. P04 and P05 reach opposite-magnitude results because they pick opposite ends of the 10 ms - 1 s near-RT range. A single-value budget makes this verdict an authoring choice rather than a measurement",
    falsified_if="the floor experiment p99 is already near B, which would make the comparison uninformative",
    limitation="cannot be measured on the current Windows host; requires the D-005 fallback decision. A non-real-RIC result must be labelled 'emulated deployment'",
    allowed_wording_today="none",
    action_required="adopt I11 (sweep B over [10 ms, 1 s] and report each architecture's crossing point); decide D-005; run the floor experiment first")

add(claim_id="C10",
    claim_text_in_manuscript="Feature extraction dominates latency, not inference",
    experiment="EXP-009 / E5b", metric="t_feat / L",
    artefact="tables/generated/runtime.tex", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="P04 measures a C-exported logistic regression at 1-5 microseconds and an MLP at 10-25 microseconds inside a real xApp, which is consistent with inference being negligible",
    literature_constraint="This becomes the LOAD-BEARING latency claim, because P04 has effectively closed the inference-cost question. It must be measured per stage, not inferred",
    falsified_if="inference exceeds feature construction for any architecture at any tested load",
    limitation="stage attribution requires instrumentation that does not itself perturb the tail",
    allowed_wording_today="none",
    action_required="adopt I14 (per-stage breakdown); run EXP-009")

add(claim_id="C11",
    claim_text_in_manuscript="Sustainable throughput T_max differs by an order of magnitude across architectures",
    experiment="EXP-009 / E6", metric="T_max",
    artefact="tables/generated/runtime.tex, figures/generated/fig_latency.pdf",
    result_today=NONE, classification="not_established", confidence="none",
    literature_support="P05 reports a stress test to 80000 instances",
    literature_constraint="",
    falsified_if="T_max is within a factor of two across architectures",
    limitation="plan A7: the draft's 'T_max < 250' is the lowest load tested, which is an unbounded statement dressed as a bound. Requires a downward load sweep plus bisection, and a bracketing interval",
    allowed_wording_today="none - and the '<250' formulation must not be reused in any form",
    action_required="extend the load sweep down to 32 and add bisection; report a bracketing interval")

add(claim_id="C12",
    claim_text_in_manuscript="Few-shot adaptation partially recovers F1",
    experiment="EXP-012 / E7", metric="F1 vs label budget", artefact="text",
    result_today=NONE, classification="not_established", confidence="none",
    literature_support="none retrieved for O-RAN",
    literature_constraint="",
    falsified_if="recovery is within seed variance at every label budget",
    limitation="this experiment deliberately uses target labels, so it must be reported strictly as ADAPTATION and must never be mixed with the generalisation result",
    allowed_wording_today="none",
    action_required="run EXP-012; keep generalisation and adaptation in separate tables")

add(claim_id="C13",
    claim_text_in_manuscript="Existing work under-reports the three deployment criteria",
    experiment="EXP-D01 / E9", metric="reporting counts, inter-coder kappa",
    artefact="tables/generated/survey.tex", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="the EXP-000 coverage table is consistent with it, but is NOT evidence for it",
    literature_constraint="A targeted keyword search over-samples work that mentions the search terms, so it has selection bias by construction. A prevalence claim needs an enumerated candidate pool, pre-registered inclusion and exclusion criteria, and a second coder",
    falsified_if="screening finds the criteria are commonly reported",
    limitation="plan A9: the table currently has placeholder counts with a methods paragraph attached, which is worse than no table because it looks evidenced",
    allowed_wording_today="a qualitative observation naming a handful of concrete studies and what each did and did not report - no counts, no percentages",
    action_required="execute EXP-D01 with a pre-registered protocol, or delete Table VIII")

add(claim_id="C14",
    claim_text_in_manuscript="The deployability predicate evaluates to zero for all five architectures",
    experiment="derived from EXP-003, EXP-006, EXP-009", metric="Eq. (7)",
    artefact="text", result_today=NONE, classification="not_established",
    confidence="none",
    literature_support="none - the predicate is our construction",
    literature_constraint="Master protocol section 18 forbids an arbitrary single deployability score unless the literature supports the weighting. A conjunctive predicate over three thresholds is defensible; a weighted scalar score is not",
    falsified_if="any architecture satisfies all three criteria at the declared thresholds",
    limitation="the predicate inherits the arbitrariness of B, alerts_max and delta_f1_max. With I11, it becomes a function of B rather than a constant",
    allowed_wording_today="none",
    action_required="re-express Eq. (7) as a function of B; report the multidimensional deployment profile alongside the predicate, never instead of it")

add(claim_id="C15",
    claim_text_in_manuscript="Energy per decision differs by about 13x across architectures",
    experiment="EXP-009 / E5d", metric="mJ per decision",
    artefact="tables/generated/runtime.tex", result_today=NONE,
    classification="not_established", confidence="none",
    literature_support="none retrieved - no source in the matrix measures container-attributed energy",
    literature_constraint="",
    falsified_if="the idle-baseline drift exceeds the measured signal",
    limitation="plan A8: RAPL reports package and DRAM energy for the whole socket and cannot attribute it to a container. With co-tenants the figure is mostly idle platform",
    allowed_wording_today="none",
    action_required="RECOMMEND ACCEPTING I9 - drop the energy column. It is one row of one table and is not worth an indefensible claim")

out = pathlib.Path("docs/CLAIM_EVIDENCE_MATRIX.csv")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    w.writerows(R)
print("wrote %s : %d claims" % (out, len(R)))
n_est = sum(1 for r in R if r["classification"] != "not_established")
print("claims currently established by evidence: %d / %d" % (n_est, len(R)))
