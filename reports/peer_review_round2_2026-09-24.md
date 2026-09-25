# Peer review, round 2 (simulated), 2026-09-24

Reviewed: `paper/main.tex` revision of 2026-09-24 as built at about 13:20 on that day
(13 pages, IEEEtran journal class). Mode: full review, standard severity, target venue
IEEE Access. Numbering follows the compiled PDF: Tables I to XVI, Figs. 1 to 7,
Eqs. (1) to (7).

Materials read: `paper/main.tex`, `paper/latency_section.tex`,
`paper/predicate_section.tex`, the sources of Figs. 1 and 2, every generated table,
`tables/generated/numbers.tex`, `paper/references.bib`, `paper/main.pdf`. Spot checks
against `results/EXP-041`, `EXP-046`, `EXP-051` and `analysis/revision_stats.py`.
At review time `rev_latency.tex` and `rev_sequence.tex` did not exist, so Section VI-G
and Table VI rendered as placeholders.

The revision that answers this review is logged in `MEMORY.md` (change log) and
summarised in `reports/response_to_reviewers_round2.md`.

---

## Reviewer 1: Analytical Expert

### Technical summary
Six supervised architectures and two input-blind baselines are trained on
NetsLab-5GORAN-IDD (D_A) and evaluated on a ladder of protocols: random, run-disjoint,
category-stratified run-disjoint and time-disjoint splits on the radio layer, and
cross-corpus transfer to 5G-NIDD (D_B) on an 18-column shared flow space. Balanced-
accuracy gaps carry Nadeau-Bengio corrected intervals with Holm correction. Operational
precision and alert volume are reported at a declared prevalence of 0.002. A
deployability test (Eq. 6) combines the criteria, and no architecture passes.

### Major strengths
1. Every in-text number is a generated macro and every table is generated.
2. Input-blind baselines in every protocol table. The DiD column of Table VIII shows the
   macro-F1 transfer loss (0.10-0.13) equals the majority baseline's loss (0.11).
3. Honest statistics: corrected interval [-0.01, 0.27], p = 0.06, next to the naive
   p = 6e-5. No architecture survives Holm.
4. Table XIV: pooled 1.45, median 1.89, mean 16.0 spread ratio, with the mechanism.
5. The Zeek `src_bytes` vs `src_ip_bytes` mapping and the source-fitted quantile
   transform in Eq. (2).

### Major weaknesses
1. **R1-W1. Transfer gap of Eq. (1) mixes target difficulty with transfer failure.**
   Table IX "Src." shows models trained and tested on a random split of D_B reach only
   0.708-0.752 BA in the shared space. DT, XGB, HGB and MLP sit at 0.751-0.752 with
   identical recall 0.81, specificity 0.69, ROC-AUC 0.865 (raw runs). Against each
   architecture's in-target BA, the transfer loss is 0.08 (LR) to 0.22 (DT), not
   0.21-0.36. Table XII measures the cost of the shared space on D_A only.
2. **R1-W2. Drift reported in macro-F1 across a prevalence shift.** Forward
   time-disjoint splits train on 50.5-67.2% attack prevalence and test on 88.2-91.7%.
   The random-session control is about 75% on both sides. Table VII omits baselines.
   The FPR rise (0.27 to 0.85) survives.
3. **R1-W3. Wrong unit for drift false alerts.** 65,755 and 205,068 per hour are radio
   window FPRs multiplied by 240,000 flows per hour (`experiments/run_drift.py:64`).
4. **R1-W4. Pooled Wilson intervals count samples several times.** Radio pooled benign
   count 2,825 against about 661 distinct benign windows. On D_B each benign flow is
   counted 20 times (DT interval [0.558, 0.559]).
5. **R1-W5. Claims without results in the build.** Table VI placeholder, Section VI-G
   placeholder, B_min "-" in Table XVI, Table XI without robust-subset and CORAL rows.
6. **R1-W6. Time-disjoint splits not checked for category coverage.**

### Minor weaknesses
1. Session recovery "from gaps in the clock" not validated against dataset documentation.
2. The larger category-stratified gap is not specific evidence of memorization.
3. Table XII: all six loss intervals include zero, not stated.
4. Holm family undefined.
5. "20 of 24 configurations outside the control range" is not a test.
6. Table XV raw macro-F1 differs from Table VIII (different split design), not stated.
7. Table XV prints 9e-01, 0e+00, 2e-16.

### Consistency audit
- Abstract NN gain 0.14 vs 0.96 - 0.81 = 0.15 in Section VI-A.
- DiD range "-0.02 to 0.01" vs RF +0.015 in Table VIII.
- Reverse BA change "-0.04 to 0.14" vs DT +0.145 in Table IX.
- Two units for the radio layer (flow-rate alerts in VI-B, per UE-hour in VI-E).
- Section VI-E: "The collapse factor is not an artifact of the declared prevalence:
  sweeping pi ... moves it from 2,627 to 1.18" contradicts its own evidence.
- Table V caption defines an asterisk that no entry carries.
- Table XI caption mentions CORAL, no CORAL row.
- Fig. 2 mixes radio (macro-F1, precision) and flow (BA) rungs on one ladder, and omits
  t_q from the runtime panel.

### Required improvements
Critical: complete or remove placeholders. Recompute drift in BA and ROC-AUC with
baselines, fix the unit. High: D_B in-target ceiling next to Table VIII. Cluster
bootstrap for pooled intervals. Medium: category coverage, session validation, Holm
family. Low: rounding, Table XV format, Fig. 2 labels.

Scores: Novelty 5, Technical Quality 5, Experimental Rigor 6, Clarity 7,
Reproducibility 8, Significance 6, Overall 5. **Major Revision.**

---

## Reviewer 2: Adversarial Critic

### Core concerns
1. **R2-C1.** The ">99% accuracy" premise (abstract, Section I) has no citation.
2. **R2-C2.** No published pipeline is reproduced. Weak, untuned detectors on an
   18-column projection failing is unsurprising.
3. **R2-C3.** D_B is not separable in the shared space even in distribution (0.71-0.75 BA).
4. **R2-C4.** Headline drift number uses the metric the paper rejects.

### Other points
- A 1-NN lookup scores 0.81 macro-F1 run-disjoint, above LR (0.744) and DT (0.782),
  within 0.04 of the best. Add it to Table V.
- Four architectures identical on D_B (BA 0.751-0.752, AUC 0.865). Explain.
- Platt inverted DT once (delta AUC 0.95, so AUC went from >= 0.975 to <= 0.025).
  Degenerate calibration fold. The abstract generalizes from one seed.
- pi = 0.002, lambda_b = 240,000 and A_max = 200 have no source. Per-flow alert counts
  overstate analyst burden. "Best PPV" is an oracle threshold.
- The deployability test never passes. Show one case where it passes.
- Algorithm 1 is not evaluated and drops late true-positive actions.
- Abstract: "no detector reaches 0.05" is false for held-out D_A flows (RF 0.417).
  "1.45 to 16.0" are ratios, not PPV values. Rank correlation p = 0.04 dismissed.

Scores: Novelty 4, Technical Depth 5, Experimental Validity 4, Clarity 6,
Trustworthiness 6, Overall 4. **Reject, resubmission encouraged.**

---

## Reviewer 3: Domain Specialist

- State what Abraheem and Edhirig (2026) found and how this paper differs.
- Radio-window labeling is not described. Benign UEs sharing a cell with attackers
  would degrade KPMs and inflate radio FPR.
- Flow-level base rate is bursty. Report precision per host-hour or per incident.
- D_B group key: capture file or time block may serve.
- Report attacker addresses per split side for D_A.
- Title claims IoT and edge-data-center scope that the corpora do not have.
- Missing literature: D'hooge et al. (JISA 2020), Engelen et al. (WTMC 2021),
  Flood et al. (EuroS&P 2024), Kus et al. (CPSS 2022), published O-RAN/5G IDS results
  that report >99%. RICARCH citation has no version.
- Complete latency, or compare emulated figures with Obiuwevwi et al.'s in-RIC values.
- Domain classifier on robust columns is driven by the protocol one-hot. Report
  within-protocol separability.

Scores: Novelty 5, Impact 6, Technical Depth 5, Relevance 7, Completeness 4,
Overall 5. **Major Revision.**

---

## Meta-review

Decision: Major Revision (at IEEE Access: reject, resubmission encouraged).
Dominant concerns: incomplete build, transfer gap without target reference, drift in a
prevalence-sensitive metric with wrong alert unit, pseudo-replicated pooled intervals,
uncited premise and no reproduced published pipeline. Acceptance estimate: 10% now,
60% after revision, about 75% with a reproduced published pipeline.

## Revision roadmap

| Priority | Issue | Location | Fix |
|---|---|---|---|
| Critical | Placeholders, claims without results | Table VI, VI-G, Table XI, Table XVI, contribution 5 | Integrate EXP-043/045/049/050 or remove claims |
| Critical | Drift in macro-F1 across prevalence shift | VI-B, Table VII, Fig. 2, abstract | BA and ROC-AUC with baselines and DiD, prevalence per fraction, category coverage |
| Critical | Drift false alerts in flow units | VI-B | Per benign UE-hour |
| High | Transfer gap lacks target reference | Eq. (1), VI-C, Table VIII | In-target BA for D_B, group-disjoint if possible, explain the 0.75 plateau |
| High | Shared-space cost on D_B unmeasured | VI-D, Table XII | Native Argus features vs 18 columns on D_B |
| High | Pseudo-replicated pooled intervals | Table XIII, VI-E | Cluster bootstrap |
| High | Uncited premise | Abstract, I | Cite and tabulate published results |
| High | No published pipeline reproduced | VII-C | Reproduce one, or narrow the conclusion |
| High | Abstract overstates body | Abstract | Interval, qualify 0.05 claim, ratios, drop Platt generalization |
| Medium | Collapse-factor sentence | VI-E | Rewrite |
| Medium | Title scope | Title, I | Remove IoT and Edge Data Centers |
| Medium | Radio labeling | IV-A | State rule and cell sharing |
| Medium | Exporter-robust overstated | IV-B, VI-D | Qualify, 2-byte offset, within-protocol separability |
| Medium | 1-NN missing | Table V | Add rows |
| Medium | Deployability test never passes | VII-B, Eq. (6) | Show a pass case, define B, label oracle |
| Medium | Platt inversion | VI-F, Table XV | Diagnose fold, plain decimals |
| Medium | Literature | II | Four papers and Abraheem and Edhirig's findings |
| Low | Rounding | Abstract, VI-A, VI-C | Consistent rounding |
| Low | Holm family, drift count | IV-E, VI-B | Define, descriptive |
| Low | Fig. 2 | Fig. 2 | Per-rung layer and metric, add t_q |
| Low | Algorithm 1 | IV-F | Justify or move |
| Low | Template, front matter | Title block | IEEE Access template, authors, RICARCH version |
