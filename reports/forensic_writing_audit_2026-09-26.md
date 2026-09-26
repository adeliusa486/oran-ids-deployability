# Forensic Writing Audit: "What Held-Out Accuracy Predicts About Deploying Intrusion Detection in O-RAN"

Audited version: working copy of 2026-09-26 (commit 30327c2 plus the uncommitted author and page-cut changes, 19 pages).
Sources read: `paper/main.tex` (614 lines), `paper/latency_section.tex` (37 lines), `paper/predicate_section.tex` (25 lines), the rendered `paper/main.pdf` for every number that a macro produces, and the generated tables behind Tables 1, 6, 12 and 14.
Line references: `main.tex:N` unless marked `lat:N` (latency_section.tex) or `pred:N` (predicate_section.tex). Each prose paragraph sits on one source line, so a line number identifies a paragraph.
Earlier versions compared: `9001d8c` (before the two prose rewrites) and `c19230c`, only where this report says so.

This is a diagnosis. Nothing in the manuscript was changed.

---

## 1. Executive Diagnostic

**Clarity.** Sentences are short and grammatical, and most paragraphs are easy to read one sentence at a time. The clarity loss sits between sentences: causal links are left for the reader to supply (why the Seq/Offset fields matter only because of the label conflict, why station 1 recorded station 2's flood, why one fold drops to 1.6% accuracy). Several referents are loose ("this gap", "the same pattern", "the two explanations", "the two counts").

**Natural academic voice.** The prose has been pushed toward short verdict sentences at paragraph ends ("The gap does not close.", "Only latency passes.", "The target corpus is not what limits transfer.", "The benign session matters more than the time of capture."). The repo change log records that the last rewrite targeted sentence-length variation after a detector flagged the text. Those closers read naturally, but many of them state more than the paragraph shows. This is the most common pattern in the paper (P-02).

**Technical precision.** Four statements are false or misleading as written: "PPV depends only on π" (main.tex:197, :569), "precision never exceeds 0.063" (abstract), the claim that false alerts per 10^6 flows are reported (main.tex:197, reported nowhere), and the Fig. 9 caption that calls aggregation plus ONNX "the decision path of the deployability test" (the test now uses the FlexRIC loop). Eq. (2) has three undefined symbols. Algorithm 1 scores every indication, which conflicts with the "225 windows per UE-hour" unit behind every radio alert count.

**Reasoning structure.** The deployability test combines terms measured on different objects. The latency term comes from a radio-window loop, but the generalization and alert terms come from flow-level transfer. The summary "only latency passes" therefore describes detectors that were never timed. The generalization verdict is computed on the all-flows labels that Section VI-C says are wrong. The attainability argument lets the published pipeline pass the generalization term by construction at R0 and, in the underlying code, mixes label sets at R1.

**Evidence and claim alignment.** Claim strength drifts across sections. The session-recognition mechanism is "consistent with" (abstract), "traces" (contribution 1), "exposes the mechanism" (Results) and "fits" (Conclusion). The 9001d8c version said "points to". Non-significant results are summarized as positive facts in the abstract and conclusion: the random-split gain (p = 0.06 for the six-model average), the clean-label transfer loss (significant for 1 of 6) and the third-corpus loss (significant for none).

**AI-rewrite patterns.** Moderate. There is little generic filler of the "this highlights the importance" type. The damage is subtler: evaluative words replaced explicit baselines ("only 0.61 to 0.78" replaced "below the in-target reference"), a concrete definition of what deployment asks was replaced by an abstract sentence, and hedged verbs were strengthened ("demonstrated" became "shown to work", "points to" became "exposes").

**Terminology.** Grouping units drift badly: capture session, run, segment, scenario, and subcategory for the radio layer. Seed, split, fold, and draw for resampling. Station, base station, pass, file, and capture for 5G-NIDD. The paper carefully distinguishes Fard et al.'s 42 runs from its own 30 sessions, then names its protocol "run-disjoint" and labels Table 1 "30 runs". Metric names also drift (PPV, operational precision, precision, corpus precision, TPR, recall).

**Paragraph and section structure.** Methods paragraphs give hyperparameters for five models before those models are introduced. The research question appears in Related Work (main.tex:145), not in the Introduction. Several Results paragraphs do two or three unrelated jobs (main.tex:431, :444, :483). Page-cut leftovers remain: a table caption that explains dashes that no longer occur, internal experiment IDs in captions, and claims whose supporting tables were removed.

---

## 2. Coverage Verification

- First manuscript line reviewed: main.tex:1 (preamble comments and macro definitions inspected for rendered effects only)
- Last manuscript line reviewed: main.tex:614
- Total line range reviewed: main.tex:1-614, latency_section.tex:1-37, predicate_section.tex:1-25
- Sections reviewed: Title, author block, running head, Abstract, Index Terms, I Introduction, II Background and Related Work (A-D), III Deployment Criteria and Threat Model (A-E), IV Methodology (A-F), V Experimental Setup, VI Results (A-I), VII Discussion (A-C), VIII Reproducibility and Ethics, IX Limitations, X Conclusion and Reporting Requirements, biographies
- Equations reviewed: Eq. (1) to Eq. (7), and Algorithm 1 (15 steps)
- Tables reviewed: Tables 1 to 14 (captions in source, contents in the rendered PDF, and generator output for Tables 1, 6, 12, 14)
- Figures and captions reviewed: Figures 1 to 10 (captions in full, and the text embedded in each figure as extracted from the PDF)
- Reference section reviewed: yes, for citation wording and formatting (62 entries). Bibliographic accuracy was not verified, as the audit brief requires.
- Unreviewed regions:
  - The plotted content of Figures 2, 3, 5 to 10 was not inspected as images. Only captions and the text extracted from each figure were read, so the audit cannot confirm that curves match the prose.
  - `paper/fig2_pipeline.tex` and `paper/measured_results.tex` are not input by main.tex and were not audited.
  - main.tex:17-19 is a source comment ("add author biographies") that is stale because biographies now exist. It does not render.

---

## 3. Critical Issues

### Issue C-01

Location: main.tex:103 (abstract), related main.tex:578
Section: Abstract
Severity: Critical
Priority: P1
Category: D. Evidence/claim, scope

Original passage:
"At an attack prevalence of 0.002, precision never exceeds 0.063 while recall stays above 10%, and no detector passes our deployability test."

Problem:
The sentence has no scope. The value 0.063 is the best precision on 5G-NIDD after transfer, on flows without the copies (main.tex:483). The paper reports higher values elsewhere at the same π and recall floor: 0.092 when transferring to the third corpus (main.tex:467), and 0.42 on held-out NetsLab flows (main.tex:483). The conclusion repeats the unscoped form: "At a realistic base rate no threshold gives usable operational precision" (main.tex:578), which is false for held-out source flows (0.42 exceeds the paper's own ρ = 0.1).

Why it matters:
A reviewer who reads Section VI-F will find 0.092 and conclude the abstract misreports the results. The unscoped version also turns a transfer result into a general statement about the detectors.

Underlying pattern:
Summary sentences drop the evaluation set that a number belongs to (P-09).

What to restore/check:
Name the setting (transfer from NetsLab-5GORAN-IDD to 5G-NIDD without the copies) or give the maximum over all transfer targets (0.092). In the conclusion, restrict the claim to transferred detectors.

Related issues: H-04, H-31, M-51

### Issue C-02

Location: main.tex:103, :129, :578, :534, pred:3, pred:5, pred:10 (Table 14 caption), lat:13
Section: Abstract, Contributions, Discussion VII-B, Conclusion
Severity: Critical
Priority: P1
Category: B. Reasoning, epistemic boundary

Original passage:
"Latency is the exception." (abstract) / "Only latency passes." (main.tex:578) / "For latency we take the strictest budget the specification allows, B = 10 ms, and evaluate it on the FlexRIC loop at a 10 ms reporting period." (pred:3)

Problem:
The FlexRIC loop scores radio windows (589 held-out test windows, 16 KPM items per UE, main.tex:313). The generalization and alert terms of the same test are computed on flow-level detectors transferred to 5G-NIDD. Table 14 therefore joins a latency result for one set of models with generalization and alert results for a different set that shares only the architecture names. The paper states this boundary itself: "Our RIC loop measures t_ind for KPM reports only and says nothing about the flow layer" (main.tex:534). The flow path it did time costs 8.5 ms at the median just to map one record into the shared space (lat:13), on top of 0.20 to 0.90 ms per flow for export. That is close to the 10 ms budget before any transport. The abstract and conclusion then present latency as the one criterion these detectors meet. Detection delay (16 s windows, flow timeouts) is also outside the test (main.tex:536, :569), which the abstract's "Latency is the exception" hides.

Why it matters:
The one positive result of the paper is attributed to detectors that were never timed on the path they would need. A reviewer who notices the radio/flow split can dismiss the test's latency column.

Underlying pattern:
Radio-layer and flow-layer evidence merged under one architecture name (P-10).

What to restore/check:
State in the test definition (main.tex:210-227) and in Table 14 that the latency term was measured for the window-level detectors. Either evaluate the flow-level latency term from the measured flow path (lat:13) or mark it as not measured. Qualify "Latency is the exception" and "Only latency passes" to the radio window path, and state the detection-delay caveat once in the abstract or conclusion.

Related issues: H-35, M-04, M-53

### Issue C-03

Location: pred:25, Table 6 (main.tex:399-403)
Section: VII-B Applying the Deployability Test, "Attainability of the test"
Severity: Critical
Priority: P1
Category: D. Evidence/claim, technical meaning

Original passage:
"The same pipeline fails one rung later, once the two position counters are removed, and at every rung after that, on all flows and on the flows without the benign copies alike (Table 6)."

Problem:
The underlying computation (`analysis/revision_stats.py:433-439`, output `results/EXP-052/processed/published_ladder.csv`) forms the clean-flow verdict from the alert term on clean flows and the generalization term on all flows. At R1 without Seq/Offset, DT and RF pass the clean alert term (operational precision 0.88 and 0.88, 63 and 67 false alerts per hour). They fail only because their generalization drop is computed from the all-flows balanced accuracy (0.706), giving 0.29. On clean flows their balanced accuracy is 0.9999, against 0.9996 at R0, so the drop on one consistent label set is about zero and both would pass. The sentence reports a failure that exists only because two label sets are mixed.

Why it matters:
This paragraph is the paper's answer to "maybe the test is too strict". Its conclusion ("the pass vanishes as soon as the evaluation moves one step closer to deployment") does not hold for flows with consistent labels, which the paper defines as the correct evaluation (main.tex:368).

Underlying pattern:
Mixing all-flows and clean-flow results inside one verdict (P-04).

What to restore/check:
Recompute the R1 to R3 clean verdicts with the generalization term on clean balanced accuracy. Report what happens at R1 honestly. If DT and RF pass, the paragraph's argument changes: the test is passable on a random split once the conflict is removed, and it fails only at the capture-file and base-station rungs.

Related issues: H-26, H-39, C-04

### Issue C-04

Location: pred:5, main.tex:103, :412, :578
Section: VII-B, Abstract, VI-D, Conclusion
Severity: Critical
Priority: P1
Category: D. Evidence/claim, negative-result preservation

Original passage:
"All of them fail the generalization term, with upper bounds of 0.32 to 0.50, and all fail the alert term by a wide margin." (pred:5)

Problem:
The upper bounds 0.32 to 0.50 come from the all-flows transfer (Table 7). Section VI-C says the benign copies are mislabeled attack traffic and that the evaluation without them is "the one with correct labels" (main.tex:368). On those flows the source-to-target loss "shrinks to 0.00 to 0.25 and is significant for 1 of the six architectures after correction" (main.tex:412). The clean-flow generalization bounds are never reported. The paragraph on clean flows (pred:5) says only that the alert term rules every architecture out. So the statement that every architecture fails generalization rests on labels the paper itself rejects, and the abstract and conclusion never mention that on consistent labels the loss is mostly not significant.

Why it matters:
Generalization failure is one of the paper's three pillars. As written, the reader believes it was established on correct labels. The overall verdict does not change (the alert term fails either way), but the reason given for it does.

Underlying pattern:
Results on all flows read as if their labels were correct (P-04). Non-significant results summarized as positive facts (P-14).

What to restore/check:
Report the clean-flow upper bound of Δ_BA per architecture next to the all-flows bound in Table 14 or the text. State in the abstract or conclusion that, on consistent labels, the transfer loss is significant for one architecture of six and that the verdict is carried by the alert term.

Related issues: H-04, H-31, C-03

---

## 4. High-Priority Issues

### Issue H-01

Location: main.tex:103, :119, :121 against :132
Section: Abstract, Introduction
Severity: High
Priority: P1
Category: E. Structure, cross-section consistency

Original passage:
"Our study uses two public corpora (NetsLab-5GORAN-IDD and 5G-NIDD)" (abstract) / "For 5G-NIDD, one of our two corpora" (:119) / "For the two corpora used here" (:121) / "The three corpora also come from three different flow exporters" (:132)

Problem:
The abstract and the first two Introduction paragraphs describe a two-corpus study. The third corpus appears in the abstract only as "a third corpus behaves the same way" and in the Introduction first at :126. Line :132 then says "the three corpora".

Why it matters:
The reader builds a wrong picture of the design, then has to revise it. A reviewer reads it as an unfinished edit (the third corpus was added in EXP-058 after the text was written).

Underlying pattern:
Leftovers from an earlier version (P-12).

What to restore/check:
Say "three public corpora" in the abstract with the third named, and remove "two" at :119 and :121 or make clear that two of the three are the main pair.

Related issues: H-31, M-05

### Issue H-02

Location: main.tex:103
Section: Abstract
Severity: High
Priority: P1
Category: C. Technical precision, reader orientation

Original passage:
"On the radio layer, a random split adds 0.13 to macro-F1 (95% interval -0.01 to 0.27, significant only for two sequence models)"

Problem:
Two things are missing or merged. (1) "adds 0.13" has no comparator. The reader cannot tell it is relative to a session-disjoint split. (2) The interval belongs to the six-architecture average, while "significant only for two sequence models" refers to two other models with their own gains (0.16 to 0.19) and a Holm family of two (main.tex:278, :329). The parenthesis reads as if the sequence models were among the six and as if their significance showed a larger effect, when part of it comes from the smaller correction family.

Why it matters:
The abstract's first result is ambiguous about what was compared and which models were tested.

Underlying pattern:
Numbers without baseline in summary positions (P-09). Dense parentheses (P-13).

What to restore/check:
Name the comparison ("than a split that keeps capture sessions apart"). Separate the six-model result from the sequence-model result, and say once that "sequence models" means the GRU and 1D-CNN.

Related issues: M-28, H-38

### Issue H-03

Location: main.tex:103, :124, :327, :578
Section: Abstract, Contributions, VI-A, Conclusion
Severity: High
Priority: P1
Category: D. Claim strength

Original passage:
"consistent with the recognition of capture sessions" (abstract) / "which traces the random-split gain to the recognition of capture sessions" (:124) / "A model-free probe exposes the mechanism." (:327) / "which fits the recognition of capture sessions" (:578)

Problem:
One finding carries four strengths. The evidence is correlational: 68% of test windows have a same-session nearest neighbor, and a 1-NN lookup gains as much as the models. No experiment removes the session signal and shows the gain disappears. In 9001d8c, :327 read "A model-free probe points to the mechanism." The rewrite strengthened it to "exposes".

Why it matters:
A reviewer will ask for the causal test that "traces" and "exposes" imply.

Underlying pattern:
Claim strength drifts between sections (P-01).

What to restore/check:
Pick one verb that matches correlational evidence ("is consistent with", "points to") and use it in all four places.

Related issues: M-26, H-38

### Issue H-04

Location: main.tex:103
Section: Abstract
Severity: High
Priority: P1
Category: D. Evidence/claim, negative-result preservation

Original passage:
"On flows with consistent labels, transferred detectors reach a balanced accuracy of only 0.61 to 0.78."

Problem:
"only" replaces a comparison. In 9001d8c the sentence read "below the in-target reference". The current version gives no reference value (0.84 to 0.92 in-target, 0.81 to 0.91 on held-out source), so "only" is an unsupported evaluation. It also omits the result that weakens the claim: on these flows the loss against held-out source data is significant for 1 of 6 architectures (main.tex:412).

Why it matters:
The reader cannot judge 0.61 to 0.78 without a reference, and the mixed statistical result is hidden.

Underlying pattern:
Evaluative adverbs replace explicit baselines (P-09). Non-significance dropped from summaries (P-14).

What to restore/check:
Restore the comparator with numbers, and mention that the source-to-target loss on consistent labels is significant for one architecture.

Related issues: C-04, H-28

### Issue H-05

Location: main.tex:103
Section: Abstract
Severity: High
Priority: P1
Category: D. Scope

Original passage:
"and no detector passes our deployability test."

Problem:
9001d8c said "no detector passes a deployability test that the published pipeline passes on its own split", which told the reader the test is attainable. The current version drops that context and gives no scope (transfer to 5G-NIDD and to the third corpus). "our deployability test" is also not introduced anywhere in the abstract.

Why it matters:
Without the attainability context, a reader assumes the test is set so that nothing can pass. Without scope, "no detector" reads as a universal claim.

Underlying pattern:
Context removed during rewriting (see Section 10).

What to restore/check:
Define the test in a clause (generalization, alert burden, latency), scope it to the transfer evaluations, and restore the attainability contrast once C-03 and H-39 are resolved.

Related issues: C-03, H-39

### Issue H-06

Location: main.tex:132 against :559
Section: Introduction, Limitations
Severity: High
Priority: P1
Category: D. Claim strength

Original passage:
"For DA and DB we remove this confound by re-extracting DB with the exporter of DA"

Problem:
Limitations says the Zeek version and configuration behind DA are undocumented, so the re-extracted DB "may still differ from it in timeouts or in its handling of single-packet flows". The re-extraction reduces the confound. It does not remove it.

Why it matters:
The Introduction promises a stronger control than the Limitations grant. Readers who stop before Section IX keep the stronger version.

Underlying pattern:
P-01.

What to restore/check:
Replace "remove" with a verb that matches the limitation and point to it.

Related issues: H-29, M-41

### Issue H-07

Location: main.tex:119
Section: Introduction
Severity: High
Priority: P1
Category: A. Clarity, F. AI-rewrite (abstraction replacing content)

Original passage:
"A benchmark score measures how well a detector separates the records of one corpus. Deployment asks a different question, and we treat a benchmark result as evidence about deployment only when an experiment supports that reading."

Problem:
The second sentence never says what the different question is. In 9001d8c it did: "deployment concerns its behavior on traffic it was not trained on, at a realistic base rate, and within a control loop." The rewrite replaced a concrete definition with a personified abstraction ("Deployment asks") and a circular rule ("only when an experiment supports that reading").

Why it matters:
This sentence is where the paper states what it means by deployment. Readers now have to infer it from the three properties above.

Underlying pattern:
Concrete content replaced by abstract scaffolding (P-16).

What to restore/check:
State the deployment question in concrete terms (unseen traffic, base rate, control loop), which also maps onto the three criteria.

Related issues: H-37, M-10

### Issue H-08

Location: main.tex:121
Section: Introduction
Severity: High
Priority: P2
Category: Novelty preservation, referents

Original passage:
"What we add is a single controlled evaluation of one detector family in which these effects are measured together, with input-blind baselines on every corpus, so that their sizes can be compared and the claims that rest on them can be checked."

Problem:
"one detector family" is unclear (six supervised architectures, two sequence models, two novelty detectors, CORAL). "these effects" has no clear antecedent in the previous sentences, which list authors' arguments. "them" can mean the effects or their sizes. The most original findings, the 5G-NIDD label conflict with its address evidence and the Seq/Offset explanation of the published 99.9%, are not named here at all.

Why it matters:
The novelty claim is generic and could belong to any evaluation paper. The distinctive contribution is buried in the second bullet.

Underlying pattern:
Generic contribution language, ambiguous referents (P-08).

What to restore/check:
Name the effects measured together and state the label-audit finding as a contribution in this paragraph.

Related issues: M-08

### Issue H-09

Location: main.tex:126
Section: Contributions
Severity: High
Priority: P1
Category: D. Claim strength, terminology

Original passage:
"A breakdown of the cross-corpus gap into prior shift, label conflicts, and genuine transfer failure, with the target re-extracted by the source's exporter and a third corpus from another site"

Problem:
"Breakdown" implies a quantitative decomposition. Section VI-E gives separate tests (separability, common exporter, model families), not an additive split into three parts. "Genuine transfer failure" is never used or defined again. 9001d8c named the means of separation ("a prevalence-invariant metric, a difference-in-differences test against the majority baseline, references measured within the target corpus, and evaluations with and without the conflicting records"). The rewrite dropped that and added "genuine".

Why it matters:
A reviewer will look for a table that splits the gap into three components and will not find one.

Underlying pattern:
P-01, context removed during rewriting.

What to restore/check:
Describe what the section does (separate tests for prior shift, label conflicts, exporter, and traffic composition) and drop "genuine" unless defined.

Related issues: H-29, H-30

### Issue H-10

Location: main.tex:197, :569
Section: III-C, Limitations
Severity: High
Priority: P1
Category: C. Technical precision, math-prose alignment

Original passage:
"PPV depends only on π, and A grows linearly with λ_b." / "operational precision depends on π alone"

Problem:
By Eq. (4), PPV depends on π, R(τ) and FPR(τ). The intended meaning is that, of the two declared parameters, PPV depends on π and not on λ_b. As written, both sentences are false.

Why it matters:
A mathematically careful reader stops here and questions the rest of the operational analysis.

Underlying pattern:
Qualifier dropped during compression.

What to restore/check:
Say "of the two declared parameters, PPV involves only π" in both places.

Related issues: H-11

### Issue H-11

Location: main.tex:197
Section: III-C
Severity: High
Priority: P1
Category: D. Evidence (claim of reporting)

Original passage:
"For that reason we also report false alerts per 10^6 benign flows, a number that does not depend on λ_b."

Problem:
No table, figure, or sentence reports false alerts per 10^6 flows. A search of main.tex, both section files, and all generated tables finds the phrase only here. Tables 10 and 14 report false alerts per hour at λ_b = 240,000.

Why it matters:
The paper promises a λ_b-free quantity and does not deliver it. A reviewer who checks will count it against the reporting-requirements section.

Underlying pattern:
Leftover from an earlier version or page cut (P-12).

What to restore/check:
Either add the per-10^6 column (it is FPR × 10^6) or delete the sentence.

Related issues: H-12

### Issue H-12

Location: main.tex:197, :315, :569
Section: III-C, V, Limitations
Severity: High
Priority: P1
Category: Methods, evidence

Original passage:
"we declare both and vary them over a range" (:197) / "and vary both over a range" (:315) / "We vary both" (:569)

Problem:
The range for π appears once (10^-4 to 0.5, main.tex:483, for the corpus-to-operational ratio only). No range for λ_b is reported anywhere, and no result shows how alert counts change with λ_b. The choice π = 0.002 has no source or justification.

Why it matters:
Three sentences claim a sensitivity analysis that the reader cannot find. π = 0.002 drives every PPV in the paper.

Underlying pattern:
P-12, unexplained design choice.

What to restore/check:
Report the λ_b range and where its effect is shown, or state that alert counts scale linearly and give the formula instead of claiming a sweep. Give a reason or citation for π = 0.002.

Related issues: H-11, M-51

### Issue H-13

Location: main.tex:178-183, Eq. (2)
Section: III-B
Severity: High
Priority: P1
Category: C. Math-prose alignment

Original passage:
"W̄_1 = (1/|F|) Σ_{j∈F} W_1(Q_j(P_A^(j)), Q_j(P_B^(j)))" with "where Q_j is the quantile transform of feature j"

Problem:
F (the feature set, presumably the 18 shared columns), P_A^(j) and P_B^(j) (the marginal distributions of feature j), and W_1 (first-order Wasserstein distance, named only in the Fig. 6 caption) are not defined. The sentence also sits under "Criterion 1" although W̄_1 is a diagnostic, not part of the test.

Why it matters:
The equation cannot be read without guessing three symbols.

Underlying pattern:
Notation before definition (P-08).

What to restore/check:
Define F, P^(j), and W_1 in the sentence after the equation. Say that W̄_1 is descriptive.

Related issues: M-15, M-16

### Issue H-14

Location: main.tex:187, :234, Algorithm 1 (main.tex:290-303), :536
Section: III-C, IV-A, IV-F, VII-A
Severity: High
Priority: P1
Category: C. Technical precision, methods

Original passage:
"A benign user equipment (UE) produces 225 windows of 16 s per hour." / "we form windows of 16 consecutive records of one UE" / Algorithm 1 scores after every indication.

Problem:
225 windows per hour means non-overlapping windows. The window stride is never stated in IV-A. Algorithm 1 updates the window and scores after every KPM indication, which at 1 Hz means up to 3,600 decisions per UE-hour, not 225. The Detection-delay paragraph (:536) says a window-level decision "has to wait for the end of its window", which also assumes non-overlapping windows. If windows overlap in the corpus, the random-split leakage in VI-A is partly explained by shared records between neighboring windows.

Why it matters:
Every radio alert count (50 to 74 false alerts per benign UE-hour) and the leakage interpretation depend on the stride.

Underlying pattern:
Hidden assumption in methods.

What to restore/check:
State the stride in IV-A. Make Algorithm 1 consistent with it (score once per completed window), or convert the alert unit to decisions per hour.

Related issues: M-26, M-48

### Issue H-15

Location: main.tex:236, :274, :325, Table 1 (rev_corpora), :571
Section: IV-A, IV-D, VI-A, Limitations
Severity: High
Priority: P2
Category: Terminology

Original passage:
"Fard et al. describe the same corpus as 42 experiment runs ... Every one of our sessions is a union of complete segments." / "a run-disjoint split" / Table 1 "Groups: 30 runs" / "30 capture sessions with one scenario each"

Problem:
Line :236 carefully separates runs (42, Fard et al.) and segments from the paper's 30 sessions. The protocol is still named "run-disjoint", Table 1 lists "30 runs", and Limitations says "one scenario each". A reader who took :236 seriously will think "run-disjoint" means disjoint over the 42 runs.

Why it matters:
The group key is the core of the leakage result. Its name contradicts the definition.

Underlying pattern:
Terminology drift for grouping units (P-05).

What to restore/check:
Choose "session" throughout (session-disjoint split, 30 sessions in Table 1) or define "run" as a session once.

Related issues: M-17, M-23, M-33

### Issue H-16

Location: main.tex:238
Section: IV-A
Severity: High
Priority: P1
Category: A. Clarity, "can a reader misunderstand"

Original passage:
"we can recover 20 capture files, two passes over the same ten attack sessions, one per base station."

Problem:
"Two passes over the same ten attack sessions" reads as the same traffic recorded twice. If that were so, identical records under two files would be expected duplication, not mislabeling. The later address evidence (:368) shows two different attackers at two stations with the same attack schedule. "Pass" is also not defined, and Fig. 4 labels files as "pass 1" and "pass 2".

Why it matters:
The label-conflict finding is the paper's most original result. This sentence invites a reader to explain the conflicts away.

Underlying pattern:
Compressed description that changes meaning.

What to restore/check:
Say what a pass is: the same attack schedule run once at each base station with a different attacker host. Use one name for it.

Related issues: M-31, M-33

### Issue H-17

Location: main.tex:268 against :270
Section: IV-C Detectors
Severity: High
Priority: P2
Category: E. Information order, reader orientation

Original passage:
"The GRU has 32 hidden units ... the 1D-CNN two convolutions ... the IF 200 trees, and the AE a 12-6-12 layout ... CORAL uses per-domain z-scores" (:268), followed by "Three more model families answer narrower questions. Two sequence models, a gated recurrent unit (GRU) network ..." (:270)

Problem:
Hyperparameters and abbreviations for GRU, 1D-CNN, IF, AE, and CORAL appear one paragraph before those models are introduced and the abbreviations expanded. The page-cut change log says abbreviations are expanded at first use, but here they are not.

Why it matters:
The reader meets five unexplained abbreviations in a dense list.

Underlying pattern:
P-08, page-cut leftover (P-12).

What to restore/check:
Move the second group of hyperparameters after :270, or swap the two paragraphs.

Related issues: M-20

### Issue H-18

Location: main.tex:278
Section: IV-E Statistical Analysis
Severity: High
Priority: P1
Category: A. Clarity, "can a reader misunderstand"

Original passage:
"The splits resample one population of 30 sessions or 318 source addresses, so their training and test sets overlap"

Problem:
The intended meaning is that training sets of different splits overlap with each other, and so do test sets. As written, "their training and test sets overlap" says train and test overlap within a split, which is leakage and contradicts :274 ("an automated check rejects any split that puts a group on both sides").

Why it matters:
A reviewer can read this as an admission of leakage.

Underlying pattern:
Ambiguous referent (P-08).

What to restore/check:
Say that training sets overlap across splits, as do test sets, which makes the per-split estimates correlated.

Related issues: M-22

### Issue H-19

Location: main.tex:274 against :483, pred:3
Section: IV-D Evaluation Protocols
Severity: High
Priority: P1
Category: D. Methods consistency

Original passage:
"Splits are group-disjoint wherever a group key exists" / "no transform, threshold, or model choice touches DB"

Problem:
(1) The radio random split and the reverse-direction random split of DB both ignore an existing group key by design, so "wherever a group key exists" is false. (2) The best-threshold precision values (0.026, 0.063) are chosen on DB (:483 admits this), and the deployability test searches thresholds on DB (pred:3). Both are threshold choices that touch DB.

Why it matters:
The integrity statement is stronger than the design, and a reviewer can point to the paper's own text to show it.

Underlying pattern:
P-01.

What to restore/check:
List the deliberate exceptions: random splits used as comparison protocols, and threshold searches on the target that are reported as upper bounds.

Related issues: M-21

### Issue H-20

Location: Algorithm 1 (main.tex:284-306), Eq. (5) (main.tex:203), :282
Section: IV-F
Severity: High
Priority: P2
Category: C. Math-prose alignment

Original passage:
"ℓ ← Now() − t_0; if ℓ > B − δ_m then v ← v + 1"

Problem:
ℓ runs from the arrival of the indication at the xApp to the return from SendE2. It excludes t_ind (delivery) and the acknowledgment part of t_act, both of which are in L (Eq. 5) and in the FlexRIC loop that the test uses. The algorithm compares ℓ with the budget B that the paper defines for L. The margin δ_m is never defined or given a value, and its symbol sits next to the generalization bound δ.

Why it matters:
The algorithm's deadline check measures a different quantity from the one the budget constrains.

Underlying pattern:
Mathematical and textual quantities with different scope.

What to restore/check:
Say that ℓ covers the in-xApp terms only and that δ_m reserves room for t_ind and t_act, with a value. Rename δ_m if possible.

Related issues: H-14

### Issue H-21

Location: main.tex:359 (Fig. 3 caption) against :354, :563
Section: VI-B
Severity: High
Priority: P1
Category: D. Cross-section consistency

Original passage:
"The benign session matters more than the time of capture."

Problem:
The text says a change over time "cannot be told apart from this heterogeneity" (:354), and Limitations says "ten benign sessions are too few to decide between the two explanations" (:563). The caption asserts the answer. In 9001d8c the caption said "which indicates that ...". The rewrite turned that into a bare assertion.

Why it matters:
Caption and text disagree on the paper's temporal conclusion.

Underlying pattern:
Paragraph-final verdicts exceed evidence (P-02).

What to restore/check:
Align the caption with :354 (sessions from the same week differ as much as sessions weeks apart).

Related issues: H-22, M-50

### Issue H-22

Location: main.tex:354
Section: VI-B
Severity: High
Priority: P2
Category: D. Evidence wording

Original passage:
"6 of the ten benign sessions give a false positive rate of at most 0.07, while sessions 4, 8 and 29 (days 3, 6 and 53) give between 0.81 and 0.98. The last benign session ... reaches 0.87 ... Two sessions from the first week come close to that."

Problem:
Six plus three is nine. The tenth session is not described. If session 29 is 0.87 and the range is 0.81 to 0.98, one early session reaches 0.98, which is above the late session, not "close to" it. It is also unclear whether 0.81 to 0.98 are means or maxima over architectures (Fig. 3 shows both).

Why it matters:
The finding that an early session is flagged more than the attack-period session is the strongest evidence against the capture-period explanation, and "come close" understates it.

Underlying pattern:
Evidence wording softer or vaguer than the numbers.

What to restore/check:
Report all ten sessions or the missing one, say whether the numbers are means, and state that one early session exceeds the late one.

Related issues: H-21, M-30

### Issue H-23

Location: main.tex:368
Section: VI-C
Severity: High
Priority: P1
Category: D. Claim strength, terminology

Original passage:
"We therefore treat the benign copies as mislabeled attack traffic, which makes the evaluation without them the one with correct labels."

Problem:
Removing the copies removes one known error. It does not make every remaining label correct. If the copies are attack traffic, a second option is to relabel them as attacks. The text does not say why removal was chosen over relabeling. The abstract and conclusion say "consistent labels", which is the accurate term. "Correct" appears only here.

Why it matters:
"Correct" is a claim the audit cannot support and a reviewer can attack.

Underlying pattern:
Terminology drift for the clean set (P-06), P-01.

What to restore/check:
Use "consistent labels" throughout, and add one sentence on why removal rather than relabeling.

Related issues: M-32, M-52

### Issue H-24

Location: main.tex:372, related :412
Section: VI-C
Severity: High
Priority: P2
Category: B. Reasoning, D. causal claim

Original passage:
"The copies cause both drops." / "The target corpus is not what limits transfer."

Problem:
(1) The causal role of the copies is tested only for station 2 to station 1 (removing the copies from the test set lifts balanced accuracy to 0.973 to 0.988). For station 1 to station 2, the clean column in Table 5 is unchanged (0.62 to 0.64), so the mechanism there ("a model misses the floods of station 2") is inferred, not tested. (2) "The target corpus is not what limits transfer" contradicts :412 ("Some of this loss comes from the label conflict") and the ceiling paragraph (:370). The intended claim is narrower: DB's shared features are sufficient to separate its classes. This wording predates the rewrite (9001d8c said "the target corpus itself does not limit transfer").

Why it matters:
Two short closing verdicts claim more than the section shows and contradict a nearby section.

Underlying pattern:
P-02.

What to restore/check:
Say what was tested for each direction. Replace the last sentence with the narrower claim about separability.

Related issues: H-28, M-35

### Issue H-25

Location: main.tex:366, Table 4
Section: VI-C
Severity: High
Priority: P2
Category: D. Evidence clarity

Original passage:
"Of the 1,215,889 flows, 52% (632,378) match a flow with the opposite label ... Each of the 281,529 flows labeled UDP flood in file 15 has an identical copy labeled benign in file 5"

Problem:
281,529 + 281,525 = 563,054. The remaining 69,324 conflicting flows are not explained. The reader has to guess whether they are file 5's own flood matching benign flows in file 15, or something else.

Why it matters:
The central audit finding has an unexplained remainder that a reviewer will ask about.

Underlying pattern:
Causal and quantitative steps left to the reader.

What to restore/check:
Account for the other 69,324 flows in one clause.

Related issues: L-19

### Issue H-26

Location: Table 6 (rev_ladder), caption main.tex:399
Section: VI-C
Severity: High
Priority: P1
Category: Figure/table language

Original passage:
Header "RF: BA* | FPR", caption "*RF on the test flows without the benign copies of Table 4."

Problem:
Under one "RF" header, BA* is on clean flows and FPR is on all flows. Row R1 shows BA 0.9999 with FPR 0.5881, which is impossible for one evaluation set. The asterisk sits on BA only, but the grouping implies both columns share it.

Why it matters:
A careful reader sees an internal contradiction in the table that supports the attainability argument.

Underlying pattern:
P-04.

What to restore/check:
Show clean BA and clean FPR together, or label the FPR column "all flows".

Related issues: C-03

### Issue H-27

Location: main.tex:410
Section: VI-D
Severity: High
Priority: P2
Category: Statistical language

Original passage:
"Source performance, in other words, does not predict target performance in a prevalence-independent metric: the rank correlation in balanced accuracy across the six architectures is -0.26 (p = 0.62). In macro-F1 it is 0.83 (p = 0.04), but macro-F1 rankings move with prevalence, and six architectures give little precision to either estimate."

Problem:
A non-significant correlation over six points shows the data cannot detect a relation. It does not show there is none. The last clause admits this, so the sentence contradicts itself. The dismissal of the macro-F1 correlation is also weak: all six models face the same prevalence on each corpus, so "rankings move with prevalence" needs a mechanism. The title's question ("what held-out accuracy predicts") leans on this sentence.

Why it matters:
This is the paper's most direct test of its title, and the wording overstates it.

Underlying pattern:
Absence of significance read as absence of effect (P-14).

What to restore/check:
Say that with six architectures the correlation is not estimable with useful precision, and keep the qualitative evidence (the MLP is best on source and among the worst on target).

Related issues: H-37

### Issue H-28

Location: main.tex:412, :425 (Fig. 5 caption), :465
Section: VI-D, VI-F
Severity: High
Priority: P2
Category: B. Reasoning, reviewer vulnerability

Original passage:
"Even on these flows, transfer falls 0.06 to 0.25 short of the in-target reference" / "The vertical bar is a reference trained and tested inside the target on a random split."

Problem:
(1) The in-target reference is a random split, the protocol the paper argues inflates scores. Table 5 has three references (random, capture file, station), and :412 does not say which one gives 0.06 to 0.25. (2) For DC, the leave-one-file-out reference (0.660 to 0.826, attack type unseen in training, :465) is the fair comparison for transferred detectors that also never saw ICMP or PFCP attacks. Transfer reaches 0.60 to 0.74, close to that reference. The text and Fig. 5 compare only with the random split (0.987 to 0.990).

Why it matters:
The "falls short" claim depends on choosing the most optimistic reference. A reviewer will point this out from the paper's own numbers.

Underlying pattern:
Inconsistent use of the paper's own protocol argument.

What to restore/check:
Name the reference used for each gap and discuss the DC leave-one-file-out comparison.

Related issues: H-31, H-04

### Issue H-29

Location: main.tex:440, related :559
Section: VI-E
Severity: High
Priority: P2
Category: B. Reasoning by elimination

Original passage:
"What is left is the difference in traffic composition that the domain classifier and the robust columns had already pointed to."

Problem:
The Zeek re-extraction leaves at least two candidate causes: traffic composition, and differences between the Zeek configuration used here and the undocumented one behind DA (:559). On all flows the gap widens under Zeek (balanced accuracy 0.54-0.62 to 0.43-0.56), which a configuration difference explains as well as composition. The sentence assigns the whole remainder to composition. The claim predates the rewrite.

Why it matters:
The paper's explanation of the transfer gap rests on this inference.

Underlying pattern:
P-02.

What to restore/check:
Name both remaining explanations, and say which evidence favors composition.

Related issues: H-06, H-30, M-41

### Issue H-30

Location: main.tex:436
Section: VI-E
Severity: High
Priority: P2
Category: B. Reasoning

Original passage:
"The robust columns shift as much as the segmentation-dependent ones (W̄_1 of 0.28 against 0.27). So the corpora differ both in flow segmentation, which a common exporter would remove, and in traffic composition, which no exporter would."

Problem:
The evidence shows that columns designed to resist segmentation shift as much as the others. That supports a composition difference. It does not show a segmentation difference: the segmentation-dependent columns can shift for compositional reasons too. The first half of the conclusion is asserted.

Why it matters:
"So" presents a claim as a consequence of evidence that does not bear on it.

Underlying pattern:
Decorative causal transition.

What to restore/check:
Separate what the W̄_1 comparison shows (composition) from what is assumed (segmentation, tested next by the Zeek export).

Related issues: H-29

### Issue H-31

Location: main.tex:103, :467, :565
Section: Abstract, VI-F
Severity: High
Priority: P1
Category: Negative-result preservation, cross-section consistency

Original passage:
"and a third corpus behaves the same way" (abstract) / "The loss against held-out source data (0.09 to 0.22) varies so much between split seeds that none of it is significant after correction." (:467)

Problem:
On DC no architecture's transfer loss is significant, and transfer balanced accuracy (0.60 to 0.74) is near the in-target leave-one-file-out reference. "Behaves the same way" hides both. Section VI-F reports the non-significance honestly, but the abstract does not.

Why it matters:
The abstract overstates replication on the third corpus.

Underlying pattern:
P-14, P-09.

What to restore/check:
Say what repeats on DC (the SYN flood is caught, benign signaling is flagged, precision stays low) and that the loss against source is not significant there.

Related issues: H-28, C-04

### Issue H-32

Location: main.tex:483
Section: VI-G
Severity: High
Priority: P1
Category: Figure/text alignment, evidence

Original passage:
"Raising the decision threshold improves precision only on held-out DA flows (Fig. 7)."

Problem:
Fig. 7 shows (a) the radio layer and (b) DB flows after transfer. It does not show held-out DA flows. On the radio layer, raising the threshold does improve precision (0.0055-0.0080 at τ = 0.5, best 0.036). So the sentence cites a figure that cannot support it and is contradicted by the radio numbers two sentences later.

Why it matters:
The claim and its figure reference are both wrong.

Underlying pattern:
Leftover after figure edits (P-12).

What to restore/check:
Restrict the claim to transfer ("on DB, raising the threshold barely changes precision") and cite Fig. 7(b).

Related issues: C-01

### Issue H-33

Location: main.tex:504, :128, Table 11
Section: VI-H, Contributions
Severity: High
Priority: P2
Category: B. Reasoning, metric consistency

Original passage:
"No calibrator lifts the target macro-F1 above that of the raw scores for any architecture." / "its largest change in ROC-AUC ranged from 0.04 to 0.21 across architectures" / contribution: "None of them helps here"

Problem:
(1) Section VI-D declares macro-F1 "the wrong yardstick" under prevalence change, yet calibration is judged by target macro-F1 at a fixed τ = 0.5. (2) The isotonic ROC-AUC change is reported as a magnitude only. The reader cannot tell whether isotonic regression raised or lowered target ROC-AUC, which decides whether "none of them helps" holds for ranking.

Why it matters:
The calibration conclusion uses the metric the paper rejects, and a key sign is missing.

Underlying pattern:
Inconsistent metric argument (P-07).

What to restore/check:
Judge calibration by balanced accuracy or reachable operating points, and give the sign of the isotonic change.

Related issues: M-25

### Issue H-34

Location: lat:13
Section: VI-I
Severity: High
Priority: P2
Category: Reader orientation

Original passage:
"the vectorized exporter produces flow records at 0.20 to 0.90 ms per flow, 22.8 to 41.6 times faster than the per-packet reference implementation"

Problem:
Neither exporter is introduced anywhere. Methods never mention that the authors wrote a flow exporter, which captures it ran on, or why it exists. "The two exporters" in the next sentence can be read as Zeek and Argus.

Why it matters:
A result is reported about a tool the reader has never met.

Underlying pattern:
Mechanism named before explanation (P-08).

What to restore/check:
Introduce both exporters in Section V (what they are, why they were built) before this paragraph.

Related issues: none

### Issue H-35

Location: lat:26 (Fig. 9 caption)
Section: VI-I
Severity: High
Priority: P1
Category: Cross-section consistency, leftover

Original passage:
"(a) The decision path of the deployability test, window aggregation followed by ONNX Runtime, for the six architectures."

Problem:
The deployability test now uses the FlexRIC loop (pred:3, Table 14 caption). The docstring of `predicate()` in `analysis/revision_stats.py` still lists both, which shows the caption dates from before EXP-061.

Why it matters:
Two different definitions of the test's latency term appear in the paper.

Underlying pattern:
P-12.

What to restore/check:
Describe panel (a) as the computation stages without calling it the test's decision path.

Related issues: C-02

### Issue H-36

Location: main.tex:549
Section: VII-C
Severity: High
Priority: P2
Category: D. Evidence, literature claim

Original passage:
"Most published results for O-RAN and 5G intrusion detection are in-distribution scores on corpora other than ours, and under a random split our own in-distribution scores are just as high (Table 3)."

Problem:
(1) "Most" has no citation. (2) The paper itself cites 99.9% results on 5G-NIDD, one of its own corpora (:119, :149), so "corpora other than ours" is not accurate. (3) Table 3 shows random-split macro-F1 of 0.84 to 0.98, not the 99%+ the paper criticizes.

Why it matters:
The comparison claim is false against the paper's own table.

Underlying pattern:
Unsupported literature claim, P-01.

What to restore/check:
Cite the DC random split (0.987 to 0.990) or the published pipeline reproduction (99.87% to 99.96%) instead of Table 3, and drop "most" or support it.

Related issues: H-41

### Issue H-37

Location: title, main.tex:549, :578, pattern across the paper
Section: VII-C, Conclusion, Title
Severity: High
Priority: P2
Category: Scope creep

Original passage:
"What our results can say is which of the commonly reported quantities predict deployment. Held-out macro-F1 under a random split does not." / "says little about how a detection xApp will behave in another deployment"

Problem:
The paper never observes a deployment. It measures transfer to independently collected corpora, which it calls the closest available proxy (pred:25: "Under the evaluations closest to deployment that the available corpora allow"). Elsewhere "deployment" stands in for "another corpus". The claim that random-split macro-F1 "does not predict" also rests on H-27.

Why it matters:
The central claim is stated at a scope the evidence does not reach.

Underlying pattern:
"Deployment" used for "evaluation on another corpus" (P-03).

What to restore/check:
Use "another corpus" or "a new site in our transfer tests" where the evidence is transfer, and keep "deployment" for the motivation.

Related issues: H-27, H-07

### Issue H-38

Location: main.tex:578
Section: Conclusion
Severity: High
Priority: P1
Category: D. Claim strength, scope

Original passage:
"On the corpora we examined, a random split inflates the score, and a model-free lookup gains about as much, which fits the recognition of capture sessions."

Problem:
The protocol comparison ran on the radio layer of DA only, not "the corpora". The six-model average gain has a corrected interval of -0.01 to 0.27 (p = 0.06), and no single architecture is significant after Holm correction (:325). "Inflates" states as fact what Section VI-A calls unresolved in size.

Why it matters:
The conclusion reports a stronger and broader result than Section VI-A.

Underlying pattern:
P-14, P-01.

What to restore/check:
Scope to the radio layer and carry the uncertainty into the sentence.

Related issues: H-02, H-03

### Issue H-39

Location: pred:25
Section: VII-B, "Attainability of the test"
Severity: High
Priority: P1
Category: B. Reasoning, methods

Original passage:
"On its own random split, with the alert term evaluated on that split, 2 of its five classifiers pass"

Problem:
In the code (`revision_stats.py:433-437`), the generalization term for the published pipeline is the drop from the model's own R0 score, which is zero at R0 by construction. So R0 passes generalization automatically. The latency term was never measured for these classifiers (KNN and Naive Bayes do not appear in any latency table). The text mentions only the alert term.

Why it matters:
The attainability argument shows that the alert term is attainable on a random split with position fields. It does not show that the full test is attainable. The reader is not told that two of the three terms are passed by default or not measured.

Underlying pattern:
Hidden assumption.

What to restore/check:
State how the generalization and latency terms were handled for the published pipeline, and narrow the claim to the alert term.

Related issues: C-03

### Issue H-40

Location: main.tex:117
Section: Introduction
Severity: High
Priority: P2
Category: Citation language, claim strength

Original passage:
"detectors that run in or beside the O-RAN control loop have already been shown to work"

Problem:
The paper argues that in-deployment results do not show deployability, and :145 says these same works "build or test a detector inside one deployment". "Shown to work" grants the cited works the very claim the paper disputes. 9001d8c said "have already been demonstrated". The rewrite strengthened it.

Why it matters:
The opening paragraph concedes the point the paper argues against.

Underlying pattern:
P-01, citation overstatement.

What to restore/check:
Say what the cited works did (built and evaluated in one testbed).

Related issues: M-10

### Issue H-41

Location: main.tex:119
Section: Introduction
Severity: High
Priority: P2
Category: Literature claim

Original passage:
"Most of these detectors are tested on a random held-out split of a single dataset, where accuracy or F1 above 99% is common."

Problem:
"These detectors" points back to 5G-Spector and Det-RAN, which are not random-split ML benchmarks. "Most" and "common" rest on two citations (the 5G-NIDD authors and Ilias et al.).

Why it matters:
The motivating claim is broader than its support, and its referent is wrong.

Underlying pattern:
Unsupported generalization about literature.

What to restore/check:
Change the referent to ML intrusion detectors for 5G and O-RAN and either cite more studies or soften to "several studies report".

Related issues: H-36, L-02

---

## 5. Medium-Priority Issues

### Issue M-01
Location: main.tex:103
Section: Abstract
Severity: Medium
Priority: P1
Category: Scope
Original passage: "These copies cap balanced accuracy at 0.766."
Problem: The ceiling applies to any classifier that reads the 90 content fields, computed in sample (:370, Table 4). In the 18 shared columns it is 0.753. The abstract drops both conditions.
Why it matters: Readers take 0.766 as a bound on every detector, including ones with position fields (ceiling 1.000).
Underlying pattern: P-09.
What to restore/check: Add "for any classifier that reads only the record content".
Related issues: M-02

### Issue M-02
Location: main.tex:103
Section: Abstract
Severity: Medium
Priority: P1
Category: Causal-chain compression, referent
Original passage: "The published 99.9% accuracy rests on two fields that encode a record's position in its file, and without them it drops to 76.9%."
Problem: "it" is the published accuracy, but 76.9% is the authors' reproduction without the fields. The abstract never links the two sentences: the position fields matter because they separate the identical copies. Without that link, a reader concludes the published models learned nothing about attacks, while :397 shows RF reaches 0.9999 on the clean flows without the fields. The metric also switches from balanced accuracy to accuracy.
Why it matters: The abstract's causal story is incomplete and invites a stronger reading than the evidence.
Underlying pattern: Causal-chain compression.
What to restore/check: Say that the two fields tell the copies apart, that the reproduced pipeline drops to 76.9% without them, and that on flows without the copies it stays near 100%.
Related issues: M-01, M-36

### Issue M-03
Location: main.tex:103
Section: Abstract
Severity: Medium
Priority: P2
Category: Referent, reader orientation
Original passage: "Re-extracting the target with the source's exporter does not close this gap" / "the flood of a second attacker"
Problem: "this gap" has no antecedent (the previous sentence gives a range, not a gap). "A second attacker" assumes the reader knows 5G-NIDD has two base stations with one attacker each.
Why it matters: Two phrases in the abstract rely on context the abstract does not give.
Underlying pattern: P-08.
What to restore/check: Name the gap (target versus source balanced accuracy) and say "the attacker at the other base station".
Related issues: H-16

### Issue M-04
Location: main.tex:103, :578
Section: Abstract, Conclusion
Severity: Medium
Priority: P1
Category: Technical precision
Original passage: "a decision and its control message take at most 5.01 ms at the 99th percentile"
Problem: 5.01 ms is the upper 95% confidence bound of the 99th percentile. The measured 99th percentiles are 4.45 to 4.95 ms (lat:9). The sentence reads as if 5.01 were the percentile itself.
Why it matters: Small, but it misstates what was measured in both summary positions.
Underlying pattern: Qualifier dropped.
What to restore/check: Say "99th percentile of 4.45 to 4.95 ms (upper bound 5.01 ms)".
Related issues: C-02

### Issue M-05
Location: main.tex:103, title
Section: Abstract
Severity: Medium
Priority: P2
Category: Abstract audit
Original passage: "We asked what such a number says about deployment." / "increasingly strict test protocols" / "We close with reporting requirements."
Problem: The abstract has no gap statement (what earlier work, such as Abraheem and Edhirig, did not do). "Increasingly strict" is vague. The last sentence names a section instead of stating why the findings matter. The question "says about deployment" also differs from the title's "predicts".
Why it matters: The abstract lists results without saying what is new or why the field should change practice.
Underlying pattern: Missing gap and significance.
What to restore/check: Add one sentence on the gap and one on the implication (for example, which reported numbers should not be trusted).
Related issues: H-08

### Issue M-06
Location: main.tex:117
Section: Introduction
Severity: Medium
Priority: P2
Category: Technical precision, unsupported causality
Original passage: "The near-real-time RIC sits close to the cells it controls, so it sees the telemetry of every device those cells serve."
Problem: Proximity does not give visibility. The RIC sees what E2 nodes report under its subscriptions, and :141 and :534 say E2 carries aggregated measurements, not packets. "Every device" overstates.
Why it matters: The motivation contradicts the paper's own data-path discussion.
Underlying pattern: Unsupported "so" causality.
What to restore/check: Tie visibility to E2 subscriptions, and say "per-UE measurements" rather than "the telemetry of every device".
Related issues: L-40

### Issue M-07
Location: main.tex:119, :206, pred:3
Section: Introduction, III-D, VII-B
Severity: Medium
Priority: P2
Category: Terminology, consistency
Original passage: "requires support for control loops between 10 ms and 1 s" / "allows near-real-time latency requirements anywhere from 10 ms to 1 s ... so instead of a verdict for one chosen value we report the smallest budget that is met" / "we take the strictest budget the specification allows, B = 10 ms"
Problem: The specification is described three ways. III-D says the paper reports a smallest budget instead of a verdict for one value, then VII-B gives a verdict at 10 ms. Table 14 does both.
Why it matters: The reader cannot tell whether the test uses a fixed B.
Underlying pattern: Terminology drift.
What to restore/check: Quote the specification once, and say that the test uses B = 10 ms and Table 14 also reports B_min.
Related issues: C-02

### Issue M-08
Location: main.tex:124-129
Section: Contributions
Severity: Medium
Priority: P2
Category: Reader orientation, structure
Original passage: "A ladder of evaluation protocols" / "the addresses of the benign copies identify them" / "Averaging precision over folds instead inflates the apparent difference between architectures by an order of magnitude" / final bullet with "Finally, a deployability test ..."
Problem: "Ladder" is a metaphor used 10 times and never defined. "The benign copies" appears before any mention of copies. The order-of-magnitude claim holds for the mean over folds (16.0 against 1.45) but not the median (1.89). The last bullet carries latency, the test, its sensitivity analysis, and the reporting requirements.
Why it matters: The contribution list uses terms the reader has not met and overloads one item.
Underlying pattern: P-08, P-13.
What to restore/check: Define the ladder in C1, introduce the copies in C2, say "mean over folds" in C4, split the last bullet.
Related issues: H-08

### Issue M-09
Location: main.tex:141
Section: II-A
Severity: Medium
Priority: P3
Category: Rhetorical scaffolding, overclaim
Original passage: "One constraint shapes everything that follows."
Problem: The constraint (E2 carries no packets) shapes only the flow-layer data path. The radio results, label audit, and transfer analysis do not depend on it.
Why it matters: A dramatic setup sentence claims more scope than it has.
Underlying pattern: P-16.
What to restore/check: State the constraint and its one consequence directly.
Related issues: L-40

### Issue M-10
Location: main.tex:145
Section: II-B
Severity: Medium
Priority: P2
Category: Related work synthesis, information order
Original passage: "All of them build or test a detector inside one deployment. Our question is what evidence would show that such a detector still works in another."
Problem: (1) "All of them" is a claim about three papers that the text does not support with details of their evaluations. (2) This is the only explicit research question in the paper, and it sits in Related Work. It also differs from the title's question.
Why it matters: The research question arrives late and in a different form from the title.
Underlying pattern: Information order.
What to restore/check: Move a single research question into the Introduction and use the same wording in the title, abstract, and :145.
Related issues: H-07, H-40

### Issue M-11
Location: main.tex:149 against :119
Section: II-C
Severity: Medium
Priority: P3
Category: Repetition (clearly redundant)
Original passage: "On 5G-NIDD, the dataset authors report binary accuracies of 99.85% to 99.95% for four of five classifiers on a random 70/30 split [11], and later work reaches a weighted F1 of up to 99.95% [12]."
Problem: Near-verbatim repeat of :119. The same numbers appear again at :395.
Why it matters: Three statements of one fact in four pages.
Underlying pattern: P-11.
What to restore/check: Keep it once in the Introduction and once in VI-C.
Related issues: L-04

### Issue M-12
Location: main.tex:153
Section: II-D
Severity: Medium
Priority: P2
Category: Evidence placement, related-work synthesis, paragraph purpose
Original passage: "Our transfer results match theirs in direction and size." / "From the dataset-shift literature we take label-shift estimation ..., calibration ..., shift detection ..., and covariance alignment ..."
Problem: (1) A result claim appears in Related Work before any result, and it compares per-attack-family balanced accuracy (theirs, 0.50 to 0.56) with pooled balanced accuracy (ours, 0.53 to 0.63). (2) The dataset-shift sentence is a citation list with no statement of what those methods assume, although their assumptions fail in Section VI-H. (3) The paragraph does three jobs: pitfalls, closest work, borrowed methods.
Why it matters: A reviewer will ask whether "match in size" survives the metric difference.
Underlying pattern: P-13, citation dumping.
What to restore/check: Move the comparison to VI-D with its metric caveat. Say what assumption the shift methods rely on. Split the paragraph.
Related issues: M-10

### Issue M-13
Location: main.tex:162
Section: III-A
Severity: Medium
Priority: P2
Category: Technical precision
Original passage: "uses them for flooding, scanning, brute-force login, or web attacks, the categories present in our corpora" / "reads either radio telemetry windows delivered through E2SM-KPM"
Problem: DC contains a PFCP session-deletion attack on the core control plane, which is not in the list. Windows are not delivered through E2SM-KPM. KPM reports are delivered and the xApp builds windows (Algorithm 1).
Why it matters: The threat model does not cover one of the tested attacks, and the data flow is misdescribed.
Underlying pattern: Compression.
What to restore/check: Add the control-plane attack, and say KPM reports are delivered and windowed in the xApp.
Related issues: M-14

### Issue M-14
Location: main.tex:167 (Fig. 1 caption and figure text)
Section: III-A
Severity: Medium
Priority: P2
Category: Figure language, terminology
Original passage: "Column 04 expands ..." / "Numbered markers show what this paper measures. Generalization across corpora (01) and alert burden (02) ..." / figure labels "1 Hz radio KPI time series", "KPI monitor" / "The detection xApp receives ... flow records from an exporter at the user plane"
Problem: The figure uses 01 to 05 for columns and 01 to 03 for measurement markers, so "01" means both "Network edge" and "Generalization". The figure says KPI where the text says KPM. The caption says the xApp receives flow records, which implies a working data path that Section VII-A says does not exist. "Mitigation actions ... options E2SM-RC offers" includes "update policy", which is an A1 matter in the figure itself.
Why it matters: The architecture figure contradicts the text in three small ways.
Underlying pattern: Terminology drift.
What to restore/check: Use distinct marker symbols, use KPM, say the flow path is assumed, check the action list.
Related issues: M-06

### Issue M-15
Location: main.tex:187-196, Eq. (3), Eq. (4)
Section: III-C
Severity: Medium
Priority: P2
Category: Notation before definition
Original passage: "A(τ) = λ_b FPR(τ)" / "PPV(τ) = π R(τ) / (π R(τ) + (1 − π) FPR(τ))"
Problem: τ (decision threshold) and R(τ) (recall) are not defined before use. Table 10 then uses TPR for the same quantity.
Why it matters: The reader guesses two symbols in the central operational equation.
Underlying pattern: P-08, P-07.
What to restore/check: Define τ and R(τ) before Eq. (3), and use one name for recall.
Related issues: H-13, M-54

### Issue M-16
Location: main.tex:219-226, Eq. (7)
Section: III-E
Severity: Medium
Priority: P3
Category: Unused concept
Original passage: "As operating threshold we take the most sensitive admissible one, τ* = argmax R(τ) s.t. ..."
Problem: τ* is never reported or used. Results use τ = 0.5 or the best threshold over a search, and Table 14 reports best PPV and minimum alerts separately.
Why it matters: A defined quantity with no result invites the question of what it was.
Underlying pattern: Leftover (P-12).
What to restore/check: Report τ* where a detector passes the alert term, or drop Eq. (7).
Related issues: none

### Issue M-17
Location: main.tex:236, :571
Section: IV-A, Limitations
Severity: Medium
Priority: P2
Category: Terminology
Original passage: "10 of the 30 sessions contain two or three attack subcategories" / "30 capture sessions with one scenario each"
Problem: "Subcategory" is not defined, and "one scenario each" contradicts "two or three attack subcategories" unless scenario means category.
Why it matters: The confound statement in Limitations depends on this term.
Underlying pattern: P-05.
What to restore/check: Define subcategory, and say "one attack category each" in :571.
Related issues: H-15

### Issue M-18
Location: main.tex:253
Section: IV-B
Severity: Medium
Priority: P2
Category: Referent, methods gap
Original passage: "The true counterpart of SrcBytes is Zeek's src_ip_bytes, at 40 and 42 bytes per packet, respectively." / Table 2 has columns for Zeek and Argus only.
Problem: "Respectively" leaves open which exporter counts 40 and which 42. NFStream, the exporter of DC, has no column in Table 2 and no mapping in the text.
Why it matters: The mapping of the third corpus cannot be reconstructed.
Underlying pattern: Methods gap.
What to restore/check: Name the exporter for each byte count, and add the NFStream mapping.
Related issues: L-12

### Issue M-19
Location: main.tex:270 against :274
Section: IV-C
Severity: Medium
Priority: P2
Category: Internal consistency
Original passage: "It is the one case in which a detector sees target data."
Problem: The in-target references are detectors trained on DB and DC. :274 lists three exceptions (references, CORAL, prior estimates).
Why it matters: A flat statement contradicted two sentences later.
Underlying pattern: P-02.
What to restore/check: Say "the one transfer model that sees target data".
Related issues: H-19

### Issue M-20
Location: main.tex:268-274, :327, :436
Section: IV-C, VI-A, VI-E
Severity: Medium
Priority: P2
Category: Methods gap
Original passage: "A model-free probe exposes the mechanism." / "A classifier trained to tell DA flows from DB flows"
Problem: The 1-NN probe and the domain classifier first appear in Results. Methods never specify either (distance metric and features for 1-NN, model type for the domain classifier). :274 refers to "the domain classifier" as if already known.
Why it matters: Two analyses that carry central claims cannot be reproduced from the text.
Underlying pattern: P-08.
What to restore/check: Add both to IV-C.
Related issues: H-17

### Issue M-21
Location: main.tex:274
Section: IV-D
Severity: Medium
Priority: P2
Category: Methods gap
Original passage: "For each of 20 split seeds we draw 300,000 flows from DA, divide them by source address, and evaluate every model on the whole of DB." / "the in-target references either hold out four of the 20 capture files or train on one base station's pass"
Problem: The train/test proportion is not given. The 300,000 sample size has no reason. The random-split in-target reference, which the text uses repeatedly, is left out of the list.
Why it matters: The protocol cannot be reconstructed.
Underlying pattern: Unexplained design choice.
What to restore/check: Add the proportion, a reason for 300,000, and the random reference.
Related issues: H-28

### Issue M-22
Location: main.tex:278
Section: IV-E
Severity: Medium
Priority: P2
Category: Statistical method
Original passage: "the variance is scaled by 1/J + n_test/n_train for J splits"
Problem: Nadeau and Bengio derived the correction for train and test sets drawn from one population. In the transfer experiments the test set is all of DB, fixed across splits. The text does not say whether n counts samples or groups, or how the correction is justified for a fixed external test set. Limitations (:571) notes the fixed target but not this point.
Why it matters: Every transfer interval depends on this choice.
Underlying pattern: Hidden assumption.
What to restore/check: State n_test and n_train for each design and one sentence on applicability to a fixed target.
Related issues: H-18

### Issue M-23
Location: throughout (e.g. :278 "folds", :315 "split seeds", Table 5 "draws", :412 "split seeds", :484 "folds")
Section: IV-E onward
Severity: Medium
Priority: P2
Category: Terminology
Original passage: "Operating points come from confusion counts pooled over folds" / "mean over n draws" / "20 split seeds with two model seeds each"
Problem: Seed, split, split seed, fold, and draw name the same resampling unit in different places.
Why it matters: The reader cannot tell whether "folds" in :484 means something different from "split seeds".
Underlying pattern: P-05.
What to restore/check: Define "split" once and use it.
Related issues: H-15

### Issue M-24
Location: main.tex:315, lat:5
Section: V, VI-I
Severity: Medium
Priority: P2
Category: Paragraph purpose, consistency
Original passage: "with one thread per library" / "RF, asked to predict one row through its default thread pool, takes 29 ms at the median"
Problem: :315 mixes seeds, operational parameters, and latency protocol. It says every latency measurement uses one thread per library, but lat:5 reports a default-thread-pool measurement (29 ms) that is not in Table 12 (RF DataFrame 6.25 ms, array 5.57 ms).
Why it matters: A number in the text has no table source, and the protocol description excludes it.
Underlying pattern: P-13.
What to restore/check: Split :315, and either add the thread-pool row to Table 12 or say where 29 ms comes from.
Related issues: M-46

### Issue M-25
Location: main.tex:325, :408
Section: VI-A, VI-D
Severity: Medium
Priority: P2
Category: Metric consistency
Original passage: "a random split raises macro-F1 by 0.09 to 0.17" / "Macro-F1 is the wrong yardstick here."
Problem: VI-D rejects macro-F1 when prevalence changes. The radio protocol comparison uses macro-F1, and test composition changes between protocols. The input-blind baselines control for this, but the text never says so, and balanced accuracy is not reported for the protocol comparison.
Why it matters: A reviewer can turn the paper's own argument against Section VI-A.
Underlying pattern: P-07.
What to restore/check: Say why macro-F1 is acceptable in VI-A (baselines unchanged), or add balanced accuracy.
Related issues: H-33

### Issue M-26
Location: main.tex:327
Section: VI-A
Severity: Medium
Priority: P2
Category: Evidence interpretation
Original passage: "Under a random split, 68% of the test windows have their nearest training window in the same capture session"
Problem: No chance level is given. Under a random split every session has windows in training, so the expected share by chance depends on session sizes. Without that baseline, 68% cannot be judged.
Why it matters: This number is the main evidence for the mechanism.
Underlying pattern: P-09.
What to restore/check: Report the share expected if the nearest neighbor ignored sessions, or under the run-disjoint split (where it is 0 by construction, which is why a chance baseline is needed).
Related issues: H-03, H-14

### Issue M-27
Location: main.tex:103, :327, Table 3
Section: Abstract, VI-A
Severity: Medium
Priority: P3
Category: Numeric consistency
Original passage: "a nearest-neighbor lookup gains 0.15" / Table 3 "1-NN ... +0.144"
Problem: NNGain (0.15) is the difference of two rounded numbers (0.96 minus 0.81). The table gives +0.144, which rounds to 0.14.
Why it matters: A reader who checks sees two values for one quantity.
Underlying pattern: Rounding before subtraction.
What to restore/check: Compute the macro from unrounded values.
Related issues: none

### Issue M-28
Location: main.tex:329
Section: VI-A
Severity: Medium
Priority: P2
Category: Referent, missing result
Original passage: "Two sequence models ... show the same pattern more sharply."
Problem: "The same pattern" can mean the random-split gain or the point that learned models add little over retrieval. The sequence models score 0.755 to 0.759 under a session-disjoint split, below the 1-NN lookup (0.814), which the text does not say. Their significance comes from a two-model Holm family, not an obviously larger effect.
Why it matters: The reader cannot tell what "more sharply" refers to.
Underlying pattern: P-08.
What to restore/check: Name the pattern and state the comparison with 1-NN.
Related issues: H-02

### Issue M-29
Location: main.tex:352
Section: VI-B
Severity: Medium
Priority: P2
Category: Negative-result preservation, statistical language
Original passage: "Time order, in short, stays within the ordinary variation between sessions."
Problem: 12% to 32% of control draws score as low as the forward split. That means the test cannot distinguish time order from session variation. "Stays within" states it as a finding. The forward split's balanced accuracy of 0.52 to 0.57, close to chance, is not interpreted.
Why it matters: Non-rejection is written as a positive result.
Underlying pattern: P-14, P-02 ("in short").
What to restore/check: Say the design cannot separate the two, and comment on the near-chance forward result.
Related issues: H-21

### Issue M-30
Location: main.tex:354
Section: VI-B
Severity: Medium
Priority: P2
Category: Scope creep
Original passage: "and a detector's false positive rate at a new site cannot be predicted from its rate on the benign sessions it was tested on"
Problem: Observed scope: ten benign sessions of one testbed. Claimed scope: a new site.
Why it matters: The generalization is plausible but not tested here.
Underlying pattern: P-03.
What to restore/check: Scope to unseen sessions of the same testbed, or mark the new-site claim as an implication.
Related issues: H-37

### Issue M-31
Location: main.tex:368
Section: VI-C
Severity: Medium
Priority: P2
Category: Missing mechanism
Original passage: "The capture at the first station evidently recorded the second station's flood too, and only its own attacker got an attack label."
Problem: The text does not say how one station's capture could contain the other station's traffic (for example, both floods targeted 10.41.150.68 and the capture point sat on the path to that host). "Evidently" asks the reader to accept the inference without the mechanism.
Why it matters: This is the explanation of the paper's key audit finding.
Underlying pattern: Causal-chain compression.
What to restore/check: Add the capture location or path argument, or say it is unknown.
Related issues: H-16

### Issue M-32
Location: main.tex:368 against :561
Section: VI-C, Limitations
Severity: Medium
Priority: P2
Category: Scope of a methods claim
Original passage: "every DB result is reported with and without the copies"
Problem: Table 7, Table 8, Table 11, and Fig. 8 report all flows only. :561 says "every operating point on DB", which is narrower.
Why it matters: A reviewer can find counterexamples in the paper.
Underlying pattern: P-01.
What to restore/check: Use the :561 wording or list the exceptions.
Related issues: M-40

### Issue M-33
Location: main.tex:238, :366-372, Fig. 4, :397, :561
Section: IV-A, VI-C
Severity: Medium
Priority: P2
Category: Terminology
Original passage: "capture files", "file 5", "base station", "station 1", "the first station", "pass 1", "pass 2", "the per-station files of the release"
Problem: Four names for overlapping units. The reader has to work out that file 5 belongs to station 1 and pass 1.
Why it matters: The label-conflict story depends on which station recorded what.
Underlying pattern: P-05.
What to restore/check: Pick "station" and "file" and state the file-to-station mapping once.
Related issues: H-16

### Issue M-34
Location: main.tex:385 (Fig. 4 caption and figure text)
Section: VI-C
Severity: Medium
Priority: P2
Category: Figure language
Original passage: "Only the record-position fields Seq and Offset differ between them." / figure: "four published classifiers reach 99.87-99.96% accuracy"
Problem: :366 says the copies also differ in the row index. The figure calls the reproduced classifiers "published".
Why it matters: Small factual slips in the figure that carries the headline finding.
Underlying pattern: Terminology drift.
What to restore/check: Add the row index, and say "reproduced".
Related issues: H-26

### Issue M-35
Location: Table 5 (main.tex:389), :372
Section: VI-C
Severity: Medium
Priority: P2
Category: Statistical language
Original passage: "mean over n draws of a 240,000-flow training sample" (n = 1 to 3)
Problem: The in-target references rest on one to three draws with no intervals. The prose compares them with transfer results that have corrected intervals, without mentioning n.
Why it matters: The references are treated as more certain than the transfer estimates.
Underlying pattern: Missing uncertainty.
What to restore/check: Mention n in the prose where the references are compared.
Related issues: H-28

### Issue M-36
Location: main.tex:397
Section: VI-C
Severity: Medium
Priority: P2
Category: Missing mechanism, terminology
Original passage: "accuracy falls to 1.6% on the fold that trains on one flood capture and tests on the other" / "the two counters"
Problem: 1.6% is far below chance and needs one clause of explanation (the model learns the copies as benign, and the test file is 98% flood). "Counters" is a new name for Seq and Offset, and Offset is a file position, not a counter.
Why it matters: A striking number is left unexplained, and a fourth name appears for the same fields.
Underlying pattern: P-06.
What to restore/check: Explain the 1.6% and use "record-position fields" throughout.
Related issues: M-02

### Issue M-37
Location: main.tex:412, Table 10 caption
Section: VI-D
Severity: Medium
Priority: P2
Category: Methods gap
Original passage: "in a deterministic re-run of 10 of the 20 split seeds"
Problem: The reader is not told why a re-run was needed, why only 10 seeds, or how they were chosen.
Why it matters: A reviewer will ask whether the subset was selected.
Underlying pattern: Unexplained design choice.
What to restore/check: One sentence: why the re-run, and that the 10 are the first 10 or chosen otherwise.
Related issues: M-44

### Issue M-38
Location: main.tex:429
Section: VI-D
Severity: Medium
Priority: P2
Category: Sign convention, statistical language, removed support
Original passage: "the change against the source reference ranges from -0.037 to +0.145" / "while DT and RF lose a significant amount"
Problem: The sign of "change" is not stated (Δ_BA is source minus target, so positive means a loss). "Significant amount" mixes statistical and practical meaning. The reverse-transfer table was cut, so no per-model numbers support these statements.
Why it matters: Claims without visible evidence and an ambiguous sign.
Underlying pattern: P-12.
What to restore/check: Say "loss (source minus target)", say "significant after Holm correction", and point to the repository table if it is not in the paper.
Related issues: M-39

### Issue M-39
Location: main.tex:429
Section: VI-D
Severity: Medium
Priority: P2
Category: Reasoning
Original passage: "One possibility is that the larger and more varied benign traffic of DB teaches a better model of benign behavior."
Problem: 59% of DB's benign class is flood copies (:366). The hypothesis ignores this, and "more varied" has no evidence.
Why it matters: The only offered explanation conflicts with the paper's own audit.
Underlying pattern: Cross-section blind spot.
What to restore/check: Account for the copies in the hypothesis, or drop "more varied".
Related issues: M-40

### Issue M-40
Location: main.tex:431
Section: VI-D
Severity: Medium
Priority: P2
Category: Label-set consistency
Original passage: "The tree models and the MLP catch more attacks and flag 0.43 to 0.56 of the benign traffic along the way."
Problem: These are all-flows numbers. Part of the "benign traffic" flagged is the flood copies that the paper judges to be attacks.
Why it matters: The sentence counts correct detections as false alarms by the paper's own reasoning.
Underlying pattern: P-04.
What to restore/check: Give the clean-flow value or note the copies.
Related issues: C-04

### Issue M-41
Location: main.tex:438
Section: VI-E
Severity: Medium
Priority: P2
Category: Technical precision
Original passage: "We re-extracted them with Zeek 8.0.10, the exporter of DA"
Problem: The apposition implies DA was exported with Zeek 8.0.10. :559 says the version behind DA is undocumented.
Why it matters: Overstates how close the control is.
Underlying pattern: P-01.
What to restore/check: Say "with Zeek (version 8.0.10), the exporter family of DA".
Related issues: H-06

### Issue M-42
Location: main.tex:442
Section: VI-E
Severity: Medium
Priority: P2
Category: Causal claims
Original passage: "The columns that do not depend on flow segmentation carry the compositional shift." / "The novelty detectors ... already fail on held-out source data, because in this feature space floods and scans look like short benign flows."
Problem: Both are explanations stated as findings. No analysis shows which columns carry the shift, or that floods resemble short benign flows. The autoencoder scores 0.455 on held-out source, below chance, which the explanation does not cover.
Why it matters: Hypotheses read as results.
Underlying pattern: P-02.
What to restore/check: Mark both as likely explanations, or add the supporting check.
Related issues: H-30

### Issue M-43
Location: main.tex:479
Section: VI-G
Severity: Medium
Priority: P2
Category: Word choice, table alignment
Original passage: "for three evaluation sets" / "These point estimates are unstable." / "Thirty sessions cannot fix the alert burden of the radio layer."
Problem: Table 10 has four blocks (radio, held-out flows, DB, DB without conflicts). "Unstable" means "imprecise" here. "Fix" reads as "repair" before it reads as "determine". 9001d8c said "cannot pin down". The rewrite introduced the ambiguity.
Why it matters: Word choice changes the meaning on first reading.
Underlying pattern: Rewrite-introduced ambiguity.
What to restore/check: Four sets, "imprecise", "cannot pin down".
Related issues: L-31

### Issue M-44
Location: main.tex:487 (Table 10 caption), lat:26 (Fig. 9 caption)
Section: VI-G, VI-I
Severity: Medium
Priority: P2
Category: Caption language, leftovers
Original passage: "(radio sessions, DA source addresses, DB capture files; for flows from a deterministic re-run on 10 seeds, EXP-056, on which the "w/o conflicts" block is also computed)" / "(EXP-060)"
Problem: Internal experiment IDs mean nothing to a reader. The Table 10 caption says "20 split seeds" and then 10 inside a nested parenthesis.
Why it matters: Captions should stand alone.
Underlying pattern: P-12.
What to restore/check: Remove the IDs, split the caption into short sentences, and state which blocks use 10 seeds.
Related issues: M-37

### Issue M-45
Location: main.tex:506
Section: VI-H
Severity: Medium
Priority: P3
Category: Label-set consistency
Original passage: "For a true target prior of 0.607"
Problem: 0.607 is the published attack share. If the copies are attacks, the true share is higher (about 0.84).
Why it matters: "True" is used for a value the paper considers wrong.
Underlying pattern: P-04.
What to restore/check: Say "the published target prior".
Related issues: M-40

### Issue M-46
Location: lat:5
Section: VI-I
Severity: Medium
Priority: P2
Category: Citation language, causal claim
Original passage: "input validation accounts for the difference" / "Numbers from other hosts or languages [21] tell us nothing about the architectures for the same reason. For context only, Obiuwevwi et al. report ..."
Problem: The input-validation explanation is not measured. The text says [21] tells nothing, then compares with it in the next sentence. 9001d8c said "says nothing about the architectures themselves", so the harsh framing predates the rewrite.
Why it matters: Dismissive wording about a cited paper, followed by reliance on it.
Underlying pattern: P-02.
What to restore/check: Say cross-host numbers cannot rank architectures, and mark the input-validation cause as likely.
Related issues: M-24

### Issue M-47
Location: lat:9, Table 13
Section: VI-I
Severity: Medium
Priority: P2
Category: Unexplained result
Original passage: "Inference in the same loop needs at most 0.229 ms at the 99th percentile."
Problem: Standalone ONNX inference has a 99th percentile of 0.014 to 0.035 ms (lat:5). Inside the loop it is 0.13 to 0.23 ms, five to ten times slower. The text does not comment.
Why it matters: A reader wonders whether the two measurements are comparable.
Underlying pattern: Missing interpretation.
What to restore/check: One clause of explanation (C API in WSL2, per-UE batch, or other).
Related issues: none

### Issue M-48
Location: main.tex:538
Section: VII-A
Severity: Medium
Priority: P2
Category: Overgeneralization, missing implication
Original passage: "automatic mitigation on the radio layer would act against every benign UE 50 to 74 times an hour" / "They should not drive automatic control."
Problem: The pooled rate is an average. Per-session rates range from 0 to 0.98 (Fig. 3), so "every benign UE" is wrong. If alerts should not drive automatic control, the near-real-time budget that the latency term tests loses its purpose for these detectors, and the paper does not draw that link.
Why it matters: An overgeneralization and an unexamined tension with the latency argument.
Underlying pattern: P-02.
What to restore/check: Say "an average benign UE", and add one sentence on what the conclusion implies for the latency criterion.
Related issues: C-02, H-14

### Issue M-49
Location: pred:5
Section: VII-B
Severity: Medium
Priority: P2
Category: Logical connective
Original passage: "It holds for any ρ above 0.0027, any A_max below 95,507 per hour, and any δ below 0.32"
Problem: Each condition alone is enough for the verdict to hold. "And" says all three are needed, which describes a smaller region than the truth.
Why it matters: The robustness claim is misstated.
Underlying pattern: Connective error.
What to restore/check: Use "or" and say that each condition alone suffices.
Related issues: C-04

### Issue M-50
Location: main.tex:563
Section: Limitations
Severity: Medium
Priority: P2
Category: Referent
Original passage: "and ten benign sessions are too few to decide between the two explanations"
Problem: The two explanations (the detector learned capture periods, or benign sessions differ from each other) are not stated as a pair in this paragraph.
Why it matters: The reader has to reconstruct them.
Underlying pattern: P-08.
What to restore/check: Name both.
Related issues: H-21

### Issue M-51
Location: main.tex:578
Section: Conclusion
Severity: Medium
Priority: P2
Category: Epistemic boundary
Original passage: "At a realistic base rate no threshold gives usable operational precision."
Problem: π = 0.002 is declared, not measured (:569), so "realistic" is not established. "Usable" is undefined (ρ = 0.1 is the paper's own choice). The scope issue is C-01.
Why it matters: The conclusion upgrades an assumption to a fact.
Underlying pattern: P-01.
What to restore/check: Say "at the declared prevalence of 0.002" and name the threshold for usable.
Related issues: C-01, H-12

### Issue M-52
Location: main.tex:103, :125, :368, :561, :578
Section: Abstract, Contributions, VI-C, Limitations, Conclusion
Severity: Medium
Priority: P2
Category: Epistemic drift, information order
Original passage: "their addresses mark them" (abstract, :561) / "identify them" (:125, :578) / "evidently" (:368) / "The dataset authors have not confirmed this" (:561)
Problem: The address finding ranges from "evidently" to "identify". In the conclusion the effect (99.9% depends on position fields) comes before its cause (the label conflict), so the causal link is left to the reader.
Why it matters: The strength of the paper's most original claim changes by section.
Underlying pattern: P-01.
What to restore/check: Use one verb that matches unconfirmed evidence, and put the conflict before the 99.9% in the conclusion.
Related issues: H-23, M-31

### Issue M-53
Location: main.tex:585 against :103, :578, lat:9
Section: Conclusion, reporting requirement 6
Severity: Medium
Priority: P2
Category: Cross-section consistency
Original passage: "measured through a RIC and, before any conformance claim, with a real E2 node"
Problem: The paper makes conformance-style statements without a real E2 node: "That meets the smallest specified budget of 10 ms" (lat:9), "Only latency passes" (:578).
Why it matters: The paper does not meet its own reporting rule.
Underlying pattern: P-01.
What to restore/check: Word the latency results as measurements on an emulated loop, not as meeting the budget.
Related issues: C-02

### Issue M-54
Location: :127, :192-197, :479-484, Table 10, Table 14
Section: throughout
Severity: Medium
Priority: P2
Category: Terminology
Original passage: "PPV", "operational precision", "precision", "corpus precision", "Corpus P", "TPR", "recall", "R(τ)", "detects", "catches"
Problem: Each metric has two to four names. "Corpus precision" is never defined in the text.
Why it matters: The distinction between corpus and operational precision is central, and the names blur it.
Underlying pattern: P-07.
What to restore/check: Define "operational precision (PPV at the declared π)" and "corpus precision (precision at the corpus's own prevalence)" once, and use "recall" everywhere.
Related issues: M-15

### Issue M-55
Location: main.tex:444
Section: VI-E
Severity: Medium
Priority: P3
Category: Paragraph purpose, placement
Original passage: "Cost of the shared space. Projecting DA onto the 18 shared columns costs 0.005 to 0.082 ... The low source macro-F1 values in Table 7 reflect the 94.63% attack prevalence of DA"
Problem: Two unrelated points, neither about the composition of the transfer gap. The supporting table was cut.
Why it matters: A detour inside a section about gap composition.
Underlying pattern: P-13.
What to restore/check: Move the shared-space cost to IV-B, and the macro-F1 point to VI-D.
Related issues: none

---

## 6. Low-Priority Issues

Each Low issue keeps the required fields in compact form.

**L-01.** Location: title, :91. Section: Title. Severity: Low. Priority: P3. Category: Terminology. Original: "What Held-Out Accuracy Predicts About Deploying Intrusion Detection in O-RAN". Problem: The paper argues accuracy and macro-F1 are the wrong yardsticks and uses balanced accuracy. The title promises a prediction test that the paper performs only with a six-point rank correlation (H-27). Why it matters: The title frames the answer more strongly than the evidence. Pattern: P-03. Restore/check: Consider "held-out scores" and a title that matches the transfer evidence. Related: H-27, H-37.

**L-02.** Location: :103. Section: Abstract. Severity: Low. Priority: P3. Category: Literature claim. Original: "Papers on intrusion detection for 5G and O-RAN often report more than 99% accuracy". Problem: "Often" rests on two cited papers. Why it matters: Minor overgeneralization in the first sentence. Pattern: unsupported generalization. Restore/check: "Several papers report". Related: H-41.

**L-03.** Location: :117. Section: Introduction. Severity: Low. Priority: P3. Category: Referent, voice. Original: "That makes it an obvious place to look for attacks." / "could catch them close to where they enter the network". Problem: "That" and "them" are loose (them = devices or attacks). "Obvious" is rhetorical. Why it matters: Small referent slips in the opening. Pattern: P-08. Restore/check: Name the referents. Related: M-06.

**L-04.** Location: :121 against :119, :153. Section: Introduction. Severity: Low. Priority: P3. Category: Repetition (potentially redundant). Original: "Axelsson made the base-rate argument [15] and Sommer and Paxson the closed-world critique [16]." Problem: Both works are cited at :119 and again at :153 for the same points. Why it matters: Three citations of the same two arguments. Pattern: P-11. Restore/check: Keep one full statement. Related: M-11.

**L-05.** Location: :141, Fig. 1. Section: II-A. Severity: Low. Priority: P3. Category: Acronyms. Original: "E2SM-KPM delivers periodic key performance measurements (KPM)". Problem: "E2SM" is never expanded. Fig. 1 uses "KPI". Why it matters: Acronym gap. Pattern: P-08. Restore/check: Expand "E2 service model". Related: M-14.

**L-06.** Location: :149. Section: II-C. Severity: Low. Priority: P3. Category: Citation wording, transition. Original: "Standardized NetFlow feature sets made cross-corpus experiments possible" / "The corpora can be wrong, however." Problem: Cross-corpus experiments existed before [39,40], so "made possible" overstates. "However" contrasts with nothing in the previous sentence. "Can be wrong" should say what is wrong (labels, flow construction). Why it matters: Small overstatement and a decorative transition. Pattern: decorative transition. Restore/check: "made easier", and "Their labels can be wrong." Related: M-12.

**L-07.** Location: :173, :178. Section: III-B. Severity: Low. Priority: P3. Category: Word choice, notation. Original: "We describe a model f_θ trained on DA by how far its score on DB falls below" / "the macro-F1 gap Δ_F1". Problem: "Describe ... by" is an odd verb for "measure". Δ_F1 and its difference-in-differences have no equation. Why it matters: Minor. Pattern: P-08. Restore/check: "We measure", and define Δ_F1 in words with its sign. Related: H-13.

**L-08.** Location: :234, Table 1. Section: IV-A. Severity: Low. Priority: P3. Category: Terminology, filler. Original: "We use both." / Table 1 "DA network". Problem: "We use both" adds nothing. The table says "network" where the text says "flow layer". Why it matters: Minor. Pattern: P-05. Restore/check: Drop the sentence, and label the column "DA flows". Related: H-15.

**L-09.** Location: :236, :350, :563. Section: IV-A, VI-B, Limitations. Severity: Low. Priority: P3. Category: Repetition (potentially redundant). Original: "nine benign sessions on days 0 to 6, the attack categories in blocks on days 47 to 53, and one last benign session" (stated three times). Problem: The capture schedule is given in full three times. Why it matters: Repetition without new information. Pattern: P-11. Restore/check: Keep the full statement in VI-B, and refer to it elsewhere. Related: L-40.

**L-10.** Location: :238. Section: IV-A. Severity: Low. Priority: P3. Category: Reader orientation, purpose. Original: "Its combined files have no addresses" / "The row index of Combined.csv also restarts at the second pass." / "A second release of the corpus keeps every Argus field". Problem: "Combined files" is undefined. The row-index sentence has no stated purpose. The second release is later called "the release with all fields preserved" and "the fields-preserved release". Why it matters: Minor drift. Pattern: P-06. Restore/check: Define the combined files, give the row-index sentence a purpose or drop it, use one name for the release. Related: M-33.

**L-11.** Location: :243 (Table 1 caption). Section: IV-A. Severity: Low. Priority: P3. Category: Caption accuracy. Original: "DB and DC are transfer targets; each also trains its own in-target references, and DB trains the reverse direction." Problem: Corpora do not train. DB is also the source for transfer to DC (Table 9), which the caption omits. Table 1 lists "30 runs" (see H-15). Why it matters: Incomplete role description. Pattern: compression. Restore/check: "DB is also a training source for the reverse direction and for DC." Related: H-15.

**L-12.** Location: :253, Table 2. Section: IV-B. Severity: Low. Priority: P3. Category: Technical precision. Original: "seven counts that both exporters report". Problem: Zeek does not report totals (Table 2 computes them), and duration is not a count. The duration floor value (duration_floor_s) is never given. Why it matters: Small inaccuracy and a missing parameter. Pattern: compression. Restore/check: "seven base quantities", and give the floor. Related: M-18.

**L-13.** Location: :255. Section: IV-B. Severity: Low. Priority: P3. Category: Naming. Original: "an exporter-robust subset ... Per-packet means and direction ratios move less, although they are not invariant." Problem: The name claims a property the text immediately qualifies, and Results show these columns shift as much as the rest. Why it matters: The label can mislead readers who skip the qualification. Pattern: P-01. Restore/check: Note once that "robust" is a design intent. Preserve the pre-declaration ("Before computing any result with it"), which is good practice. Related: H-30.

**L-14.** Location: :268. Section: IV-C. Severity: Low. Priority: P3. Category: Repetition, notation, order. Original: "a decision tree (DT) of depth 12" ... "DT depth 12" / "a positive-class weight of n−/n+" / "Tuning on held-out source data would reward ..." Problem: DT depth is given twice. n− and n+ are undefined. The reason for not tuning comes six clauses after "We fixed the hyperparameters and did not tune them." Why it matters: Minor clutter. Pattern: information order. Restore/check: Put the reason next to the decision. Related: H-17.

**L-15.** Location: :282. Section: IV-F. Severity: Low. Priority: P3. Category: Unsupported claim. Original: "because a late mitigation is usually better than none" / "An operator who would rather drop late actions can move the transmission step inside the deadline check." Problem: "Usually better" has no support. In Algorithm 1 the deadline check runs after the send, so moving the send inside it needs a restructure. Why it matters: Minor. Pattern: hidden assumption. Restore/check: Soften, and say the check must precede the send. Related: H-20.

**L-16.** Location: :315. Section: V. Severity: Low. Priority: P3. Category: Citation wording. Original: "the several hundred flows per second that Jin et al. expect at a heavily loaded base station". Problem: "Expect" does not say whether [61] measured or estimated this. Why it matters: Attribution precision. Pattern: citation wording. Restore/check: "report" or "estimate", as [61] does. Related: H-12.

**L-17.** Location: :325. Section: VI-A. Severity: Low. Priority: P3. Category: Sentence purpose. Original: "An uncorrected paired t-test on the same data would have given p = 6 × 10^-5." Problem: The reader must infer why this is here (to show how much the correction matters). Why it matters: Purpose implicit. Pattern: missing interpretation. Restore/check: Add "which shows how much the naive test understates variance". Related: H-18.

**L-18.** Location: :343 (Fig. 2 caption). Section: VI-A. Severity: Low. Priority: P3. Category: Terminology. Original: "does not remove the drop". Problem: The text speaks of a random-split gain. The caption speaks of a drop. Why it matters: Direction flips between text and caption. Pattern: P-07. Restore/check: Use "gain" in both. Related: none.

**L-19.** Location: :366, :370, Table 4. Section: VI-C. Severity: Low. Priority: P3. Category: Referent, precision. Original: "for 33,704 of the 33,708 distinct records the two counts are equal" / "Add Seq and Offset, and every record becomes unique." Problem: "The two counts" means occurrences per file, which the reader must infer. Table 4 shows 1,215,869 distinct records out of 1,215,889 with Seq and Offset, so 20 duplicates remain. Why it matters: Minor imprecision. Pattern: P-08. Restore/check: Name the counts, and say "almost every record". Related: H-25.

**L-20.** Location: :372. Section: VI-C. Severity: Low. Priority: P3. Category: Precision. Original: "A random split gives 0.708 to 0.752 in the shared space, which is the ceiling above". Problem: Only the upper end equals the ceiling. LR (0.708) is below it. Why it matters: Minor. Pattern: compression. Restore/check: "the upper end of which is the ceiling". Related: none.

**L-21.** Location: :395, Table 6. Section: VI-C. Severity: Low. Priority: P3. Category: Precision, missing reason. Original: "on their split we obtain" / "KNN is evaluated at R0 only." Problem: "Their split" suggests the identical partition, when the protocol (random 70/30) is meant. No reason is given for dropping KNN after R0. Why it matters: Minor. Pattern: unexplained design choice. Restore/check: "under their protocol", and a reason for KNN (cost, presumably). Related: H-39.

**L-22.** Location: :397. Section: VI-C. Severity: Low. Priority: P3. Category: Scaffolding, closer. Original: "Put simply, the two counters let the published models tell identical records apart by their position in the file." / "About a deployment, where record positions do not exist, it says nothing." Problem: "Put simply" restates the previous two sentences. The closer is rhetorical but logically sound. Classification: useful reinforcement for the first, acceptable for the second. Pattern: P-16. Restore/check: Keep one of the two restatements. Related: M-36.

**L-23.** Location: :410. Section: VI-D. Severity: Low. Priority: P3. Category: Sentence purpose, inflation. Original: "As floors, the stratified sampler scores a macro-F1 of 0.424 on DB and a fair coin would score 0.494." / "On every prevalence-independent measure LR transfers best". Problem: The floors sentence follows a declaration that macro-F1 is the wrong yardstick, so its purpose is unclear. "Every" means two measures. Why it matters: Minor. Pattern: P-07. Restore/check: Say why the floors matter, and "on both prevalence-independent measures". Related: M-25.

**L-24.** Location: :412. Section: VI-D. Severity: Low. Priority: P3. Category: Order. Original: "flags 0.00 to 0.85 of the benign-labeled copies in file 5. LR finds neither." Problem: The range includes LR's 0.00, and "a detector that learned to recognize a UDP flood" describes the others. Why it matters: Reader has to reconcile the range with the exception. Pattern: compression. Restore/check: Give the range for the five nonlinear models. Related: none.

**L-25.** Location: :431. Section: VI-D. Severity: Low. Priority: P3. Category: Undefined criterion, paragraph purpose. Original: "No architecture handles both classes of DB acceptably." Problem: "Acceptably" is undefined. The paragraph moves from forward transfer to reverse-direction category recall without a break. Why it matters: Minor. Pattern: P-13. Restore/check: Name the criterion, and split the paragraph. Related: M-40.

**L-26.** Location: :438. Section: VI-E. Severity: Low. Priority: P3. Category: Missing interpretation. Original: "we carried those labels over to the 346,882 Zeek flows (76% attacks)". Problem: Zeek produces about a third as many flows as Argus and a higher attack share (76% against 60.7%). The difference is not discussed. Why it matters: A reader wonders how comparable the two exports are. Pattern: missing interpretation. Restore/check: One clause on why the counts differ. Related: H-29.

**L-27.** Location: :440. Section: VI-E. Severity: Low. Priority: P3. Category: Statistical language. Original: "has a 95% interval below zero for 6 of the six architectures". Problem: The interval type (corrected or not) is not stated, and "6 of the six" reads oddly. Why it matters: Minor. Pattern: P-15. Restore/check: State the interval type, and write "all six". Related: L-47.

**L-28.** Location: :458 (Fig. 6 caption). Section: VI-E. Severity: Low. Priority: P3. Category: Referent. Original: "so the gap is not only a matter of how the two exporters segment flows". Problem: "The gap" could be the covariate shift or the transfer gap. Why it matters: Minor. Pattern: P-08. Restore/check: "the shift". Related: H-30.

**L-29.** Location: :465, :586. Section: VI-F, Conclusion. Severity: Low. Priority: P3. Category: Consistency. Original: "unlike DB its labels are consistent. Only 3.2% of its flows sit on records that also occur with the opposite label" / requirement 7: "with no identical records under opposite labels". Problem: 3.2% conflicts is not "consistent", and DC would fail the paper's own requirement 7. Why it matters: Small contradiction. Pattern: P-06. Restore/check: "nearly consistent", or give requirement 7 a tolerance. Related: H-23.

**L-30.** Location: :467. Section: VI-F. Severity: Low. Priority: P3. Category: Missing interpretation, vague reference. Original: "From DB (10 split seeds), balanced accuracy spans 0.42 to 0.85, and ROC-AUC drops as low as 0.38." / "The picture of Section VI-D returns at a third site" / "(0 and 0 of six)". Problem: Below-chance values (0.42, 0.38) mean inverted ranking and are not explained. "The picture of Section VI-D" is vague (VI-D has no SYN flood result). The macro output reads "0 and 0 of six". Why it matters: Minor. Pattern: P-15. Restore/check: Note the inversion, name what repeats, write "none in either direction". Related: H-31.

**L-31.** Location: :481. Section: VI-G. Severity: Low. Priority: P3. Category: Decorative transition. Original: "The flow layer tells a similar story." Problem: The flow layer shows lower FPR on held-out source than the radio layer, so "similar" is vague. Why it matters: Minor. Pattern: P-16. Restore/check: State the shared point (large alert volumes). Related: M-43.

**L-32.** Location: :483. Section: VI-G. Severity: Low. Priority: P3. Category: Referent, density. Original: "but for 4 of the six architectures its bootstrap interval reaches 1.0: a resample that leaves out the benign sessions flagged almost entirely leaves thresholds with no false positive at all" / "changes the ratio between them from 2,627 to 1.18". Problem: "Its" refers to one pooled value but the interval is per architecture. The mechanism is packed into one clause. The ratio's direction (corpus over operational) is not stated. Why it matters: Dense sentence. Pattern: P-13. Restore/check: Split, and state the ratio direction. Related: M-54.

**L-33.** Location: :483-484. Section: VI-G. Severity: Low. Priority: P3. Category: Formatting. Original: "\emph{Estimation of operational precision.}" follows :483 with no blank line. Problem: In LaTeX this run-in heading joins the previous paragraph instead of starting a new one. Why it matters: Visual structure differs from the other run-in headings. Pattern: formatting. Restore/check: Insert a blank line. Related: none.

**L-34.** Location: :504. Section: VI-H. Severity: Low. Priority: P3. Category: Terminology, formatting, density. Original: "achievable operating points" (vs "reachable" at :128) / "at most 2e-05" / the Platt sentence with three numbers and a slope. Problem: Two names for one idea. "2e-05" breaks the paper's "6 × 10^-5" style. The Platt explanation is dense. Why it matters: Minor. Pattern: P-15. Restore/check: One term, one number style, split the Platt sentence. Related: H-33.

**L-35.** Location: :504, :511 (Fig. 8 caption). Section: VI-H. Severity: Low. Priority: P3. Category: Unsupported step, caption. Original: "they pull the scores toward that prior and flag more benign traffic on DB" / "fifteen equal-mass bins pooled over 20 split seeds". Problem: No FPR change is reported to support "flag more". Fig. 8 uses 20 seeds while calibration uses 10, and the caption offers no reading of the diagram. Why it matters: Minor. Pattern: missing evidence. Restore/check: Give the FPR change, and explain the seed difference. Related: H-33.

**L-36.** Location: lat:3, lat:7, lat:16 (Table 12 caption). Section: VI-I. Severity: Low. Priority: P3. Category: Leftovers. Original: "used only where the exported model reproduces the decisions of scikit-learn (12 of 12 exports, decision agreement at least 1.0000)" / "across the architectures with a verified export" / "Dashes: no export that reproduced scikit-learn's decisions." Problem: All 12 exports pass, and Table 12 has no dashes. "At least 1.0000" means exactly 1. Why it matters: Vestigial text. Pattern: P-12. Restore/check: Say all exports matched, and delete the dash note. Related: H-35.

**L-37.** Location: lat:9. Section: VI-I. Severity: Low. Priority: P3. Category: Scope. Original: "Once a RIC is in the path, the choice of model barely matters." Problem: Out of context it reads as a claim about detection quality. Why it matters: Minor misreading risk. Pattern: P-02. Restore/check: Add "for latency". Related: none.

**L-38.** Location: lat:11, and :132, :313, :567, pred:3. Section: VI-I. Severity: Low. Priority: P3. Category: Scaffolding, repetition (useful reinforcement). Original: "Keep in mind that the loop runs on one host, with an emulated node and loopback SCTP." Problem: The one-host, emulated-node caveat appears five times. "Keep in mind" is scaffolding. The power-management explanation is hedged appropriately. Why it matters: Minor. Pattern: P-11, P-16. Restore/check: Keep the caveat in III-D, V, and IX. Related: C-02.

**L-39.** Location: lat:13. Section: VI-I. Severity: Low. Priority: P3. Category: Missing reason, number style. Original: "On the 2 captures compared record by record". Problem: The text does not say why two of the three captures were compared. Why it matters: Minor. Pattern: P-15. Restore/check: Give the reason, write "two". Related: H-34.

**L-40.** Location: :141, :162, :534, Fig. 1. Section: II-A, III-A, VII-A. Severity: Low. Priority: P3. Category: Repetition (useful reinforcement, then redundant). Original: "E2 carries aggregated measurements, not packets" / "since E2 carries no packets" / "It carries no packets." Problem: Stated four times. Why it matters: Minor. Pattern: P-11. Restore/check: Keep II-A and VII-A. Related: L-09.

**L-41.** Location: :540. Section: VII-A. Severity: Low. Priority: P3. Category: Speculation. Original: "unsupervised shift detection [52] can flag the moment incoming traffic departs" / "so a monitor of this kind would fire at once". Problem: A domain classifier trained with both corpora labeled is not an unsupervised monitor, so "would fire at once" is inferred. Why it matters: Minor overstatement. Pattern: P-02. Restore/check: Soften to "would likely detect the shift". Related: none.

**L-42.** Location: pred:7. Section: VII-B. Severity: Low. Priority: P3. Category: Scaffolding, scope. Original: "How far would the bounds have to move? Fig. 10 shows it." / "only if an operator accepts several thousand false alerts per hour". Problem: A rhetorical question with a weak answer. The "several thousand" statement is for clean flows (Fig. 10a) and the sentence does not say so. Why it matters: Minor. Pattern: P-16. Restore/check: State the result directly with the label set. Related: C-04.

**L-43.** Location: :554. Section: VIII. Severity: Low. Priority: P3. Category: Generic statement, reviewer vulnerability. Original: "Showing when detectors fail carries a modest dual-use risk. We judge it smaller than the benefit to operators". Problem: Generic ethics language. The paper reports a labeling error in a public dataset and does not say whether its authors were informed. Limitations says they "have not confirmed this". Why it matters: A reviewer may ask. Pattern: generic voice. Restore/check: State whether the dataset authors were contacted. Related: M-52.

**L-44.** Location: :561. Section: Limitations. Severity: Low. Priority: P3. Category: Precision. Original: "exact copies of records labeled UDP flood" / "(10 of 10)". Problem: The copies match in all fields except row index, Seq, and Offset, so "exact" overstates. "10 of 10" is unclear next to "20 capture files". Why it matters: Minor. Pattern: P-06. Restore/check: "copies identical in content", and say what the 10 are. Related: M-33.

**L-45.** Location: :567. Section: Limitations. Severity: Low. Priority: P3. Category: Clause attachment. Original: "It measures the processing cost of the RIC path, which also depends on the host's power management, not the delay of a deployment." Problem: "Not the delay of a deployment" attaches ambiguously after the relative clause. Why it matters: Minor. Pattern: dense sentence. Restore/check: Split into two sentences. Related: none.

**L-46.** Location: :580-586. Section: Conclusion. Severity: Low. Priority: P3. Category: Precision, overlap. Original: requirement 1 "a reference trained inside that corpus" / requirement 5 "intervals that account for overlap between resampled splits". Problem: Requirement 1 does not specify the reference's protocol, which H-28 shows matters. Requirement 5 overlaps requirement 3. Why it matters: Minor. Pattern: P-11. Restore/check: Specify a group-disjoint reference, merge 5 into 3 or separate their scopes. Related: H-28.

**L-47.** Location: :354, :408, :410, :412, :440, :467, pred:5. Section: Results. Severity: Low. Priority: P3. Category: Number style. Original: "6 of the ten", "5 of the six", "4 of the six architectures (3 after Holm correction)", "6 of the six", "(0 and 0 of six)". Problem: Macros print digits next to spelled-out numbers. Why it matters: Reads as machine output. Pattern: P-15. Restore/check: Have the number macros print words for small counts. Related: L-27, L-30.

**L-48.** Location: :592-610. Section: Biographies. Severity: Low. Priority: P3. Category: Formatting. Original: "Bachelor's degree in information technology" vs "B.S. degree in Information Technology" / "MSc degree ... PhD degree" vs "Ph.D. degree" / Eraj Khan: "lightweight" twice in one sentence. Problem: Degree names and capitalization differ between biographies. Two biographies give no degree years. The repo change log records Ali Akarma's affiliation as taken from his biography and still to be confirmed. Why it matters: Production editors will query it. Pattern: formatting. Restore/check: Use IEEE forms (Ph.D., M.Sc., B.S.) consistently, confirm the affiliation. Related: none.

**L-49.** Location: references [12], [14]. Section: References. Severity: Low. Priority: P3. Category: Formatting. Original: [12] "the weighted F1 cited is from the abstract of v2 (May 2025); a revised version appeared in ..." / [14] "bench- mark -- comparing". Problem: A note inside a reference entry is unusual. [14] prints a literal double hyphen. DOI formatting varies ("doi:10..." against "doi: 10..."). Why it matters: Production polish. Pattern: formatting. Restore/check: Move the [12] note to the text or a footnote, fix the dash. Related: none.

**L-50.** Location: :538. Section: VII-A. Severity: Low. Priority: P3. Category: Acronym. Original: "or a non-real-time policy through A1". Problem: A1 is never defined in the text (it appears only in Fig. 1). Why it matters: Minor. Pattern: P-08. Restore/check: "the A1 interface to the non-real-time RIC". Related: L-05.

**L-51.** Location: :350. Section: VI-B. Severity: Low. Priority: P3. Category: Terminology. Original: "its capture order follows the scenario schedule". Problem: :236 calls it "the capture schedule". Why it matters: Minor drift. Pattern: P-05. Restore/check: One name. Related: M-17.

---

## 7. Recurring Manuscript-Wide Patterns

**P-01. Claim strength drifts between sections.**
Frequency: 14 occurrences. Sections: Abstract, Introduction, Contributions, VI-A, VI-C, VI-E, Conclusion.
Examples: H-03 ("consistent with" / "traces" / "exposes" / "fits"), H-06 ("remove this confound"), H-23 ("correct labels"), H-40 ("shown to work"), M-41, M-52, M-53, H-19, M-32, M-51, L-13.
Likely source: mixed. Some strengthening is traceable to the rewrite (H-03, H-40), some predates it.
Why it matters: A reviewer compares sections and attacks the strongest version.
Repair strategy: For each main finding, write its evidence type (tested, correlational, inferred) and pick one verb per type. Search the paper for every sentence stating that finding.

**P-02. Paragraph-final verdicts exceed the paragraph's evidence.**
Frequency: 13. Sections: VI-B, VI-C, VI-E, VI-G, VI-I, VII, Fig. 3 caption.
Examples: "The benign session matters more than the time of capture." (H-21), "The target corpus is not what limits transfer." (H-24), "What is left is the difference in traffic composition" (H-29), "Time order, in short, stays within the ordinary variation" (M-29), "The columns that do not depend on flow segmentation carry the compositional shift." (M-42), "Only latency passes." (C-02), M-19, M-46, M-48, L-37, L-41.
Likely source: AI rewrite. The change log records that the last pass aimed to raise sentence-length variation after a detector flagged the text, and short closing verdicts are the easiest way to do that.
Why it matters: Readers remember closing sentences. When the closer overstates, the paper's memorable version is its weakest.
Repair strategy: Read the last sentence of every Results and Discussion paragraph and check it against the numbers in that paragraph. Keep short closers only when they restate what was shown.

**P-03. "Deployment" stands in for "another corpus".**
Frequency: 6. Sections: Title, Introduction, VI-B, VII-C, Conclusion.
Examples: H-37, M-30, L-01, :578 "another deployment".
Likely source: framing, predates the rewrite.
Why it matters: The main claim reaches beyond the evidence.
Repair strategy: Use "deployment" for motivation and requirements. Use "an independently collected corpus" or "a new site" for results.

**P-04. All-flows results read as if their labels were correct.**
Frequency: 7. Sections: VI-D, VI-H, VII-B, Table 6.
Examples: C-03, C-04, H-26, M-40, M-45, and the clean-flow verdict code.
Likely source: reasoning compression. The label audit was added after the transfer analysis.
Why it matters: The paper's own audit says those labels are wrong for 23% of flows.
Repair strategy: For every DB statement, label the flow set. Never combine terms from two label sets in one verdict.

**P-05. Terminology drift for grouping units.**
Frequency: 9 locations. Sections: IV, VI, Table 1, Limitations.
Examples: session / run / segment / scenario / subcategory (H-15, M-17, L-51), seed / split / fold / draw (M-23), station / base station / pass / file / capture (M-33, H-16).
Likely source: mixed, partly paraphrase variation.
Why it matters: The group key is the core of the leakage and label-conflict results.
Repair strategy: Build a glossary of the five units and replace every variant.

**P-06. Terminology drift for the conflicting records and fields.**
Frequency: 6. Examples: copies / benign copies / flood copies / conflicts / conflicting records / exact copies (L-44), consistent vs correct labels (H-23), Seq and Offset / record-position fields / position counters / counters / two fields (M-36).
Likely source: paraphrase variation.
Repair strategy: One term each: "benign-labeled copies", "consistent labels", "record-position fields".

**P-07. Metric naming and metric-argument inconsistency.**
Frequency: 6. Examples: M-54 (PPV / operational precision / corpus precision, TPR / recall), M-25 and H-33 (macro-F1 rejected in VI-D, used in VI-A and VI-H), L-18, L-23.
Likely source: structure.
Repair strategy: Define each metric once and justify any use of macro-F1 after VI-D.

**P-08. Notation, concepts, or tools used before definition.**
Frequency: 14. Examples: H-13 (Eq. 2), M-15 (τ, R), H-17 (five abbreviations), H-34 (exporters), M-20 (1-NN, domain classifier), H-18, M-08 (ladder), M-03, M-28, M-50, L-05, L-50, L-03, L-28, L-19.
Likely source: page cut (tables and notation table removed) plus paraphrase.
Repair strategy: A first-use pass: for each symbol, acronym, and named tool, find the first occurrence and check it is defined there.

**P-09. Summary numbers without scope or baseline.**
Frequency: 7. Sections: Abstract, Conclusion, VI-A.
Examples: C-01, H-02, H-04, M-01, M-26, H-31, M-04.
Likely source: AI rewrite (evaluative words replaced comparators, as H-04 shows).
Repair strategy: Every number in the abstract and conclusion gets its evaluation set and its comparator.

**P-10. Radio-layer and flow-layer evidence merged under one architecture name.**
Frequency: 3. Examples: C-02, H-35, M-48.
Likely source: reasoning compression when EXP-061 was added.
Repair strategy: Tag every latency and alert statement with its layer.

**P-11. Repetition across sections.**
Frequency: 7. Examples: M-11, L-04, L-09, L-38, L-40, L-46, the 99.9% explanation (useful reinforcement).
Likely source: structure.
Repair strategy: Keep each fact where it is argued, and point to it elsewhere.

**P-12. Leftovers from earlier versions and the page cut.**
Frequency: 10. Examples: H-01, H-11, H-17, H-32, H-35, M-16, M-38, M-44, M-55, L-36.
Likely source: version churn.
Repair strategy: After each cut, search for references to removed floats and for captions describing content that no longer exists.

**P-13. Paragraphs with several unrelated jobs.**
Frequency: 7. Examples: M-12 (:153), M-24 (:315), M-55 (:444), L-25 (:431), L-32 (:483), M-08 (last bullet), H-02.
Repair strategy: One claim per paragraph in Results.

**P-14. Non-significance written as a positive fact.**
Frequency: 6. Examples: C-04, H-27, H-31, H-38, M-29, H-04.
Likely source: summary compression.
Repair strategy: When an interval includes zero, say what the design cannot tell, and carry that into the abstract and conclusion.

**P-15. Mixed number style from macros.**
Frequency: 8 instances. Examples: L-47, L-27, L-30, L-34, L-39.
Repair strategy: Fix in the macro generator.

**P-16. Rhetorical scaffolding and abstraction replacing content.**
Frequency: 8. Examples: H-07 ("Deployment asks a different question"), M-09 ("One constraint shapes everything that follows."), L-22 ("Put simply"), L-38 ("Keep in mind"), L-42 ("Fig. 10 shows it."), L-31, M-29 ("in short"), L-06.
Likely source: AI rewrite.
Repair strategy: For each flagged sentence, ask what information it adds. Replace or delete.

---

## 8. AI-Rewrite Signature Analysis

| Signature | Level | Evidence |
|---|---|---|
| Generic academic phrasing | Mild | Little stock filler. "None of these concerns is new", "Our contributions are these" are plain. |
| Abstraction inflation | Moderate | H-07: a concrete definition of deployment became "Deployment asks a different question". |
| Nominalization | Mild | Most sentences have actors and verbs. Some remain ("a breakdown of", "An account of which"). |
| Excessive hedging | Absent | The opposite problem dominates. |
| Excessive certainty | Moderate | P-01, P-02: "exposes", "shown to work", "The copies cause both drops". |
| Formulaic transitions | Mild | "in short", "Put simply", "Keep in mind", "The flow layer tells a similar story". |
| Repetitive sentence structures | Mild | "X gives A to B, and Y gives C to D" repeats in VI-C and VI-D, driven by macros. |
| Artificial paragraph scaffolding | Mild | Rhetorical questions open three paragraphs (:368, :465, pred:7). |
| Over-compression | Moderate | M-02, M-31, M-36, H-16: causal steps left out. |
| Loss of causal explanation | Moderate | Mechanisms of the station-1 recording, the 1.6% fold, and the position fields' role in the abstract. |
| Loss of authorial voice | Mild | The voice is direct and skeptical, which should be kept. |
| Terminology drift | Strong | P-05, P-06, P-07. |
| Claim inflation | Moderate | H-03, H-09, H-40, H-36. |
| Scope inflation | Moderate | C-01, H-37, M-30, H-38. |
| Qualification removal | Moderate | H-04 (baseline removed), H-05 (attainability removed), H-10, M-04. |
| Excessive symmetry | Mild | The contribution list and the Limitations paragraphs are uniform in shape. |
| Excessive parallelism | Mild | Three-item lists where the evidence has two or four (Table 10 "three evaluation sets"). |
| Redundant summaries | Mild | L-22, L-38. |
| Unnatural sophistication | Absent | The register is plain. |
| Generic "significance" statements | Mild | L-43 (ethics), M-05 (abstract ending). |
| Loss of concrete actors | Mild | "Deployment asks", "the corpora can be wrong", "Table 8 runs the same splits". |
| Excessive passive voice | Absent | Active voice dominates. |
| Unnecessary meta-language | Mild | "Fig. 10 shows it.", "Keep in mind", "We close with reporting requirements." |

This table identifies writing patterns. It is not a judgment about who or what wrote the text.

---

## 9. Authorial Voice Loss

The paper keeps a clear, skeptical voice. Many sentences do what a careful researcher does: "We do not count its larger gain as extra evidence, though, because it pushes sessions of rare categories into the test set" (:327), "We have not tested why." (:429), "The small group-disjoint calibration fold is to blame, not Platt scaling." (:504), "The largest single value we saw at this period was 11.2 ms." (lat:9). Keep these.

What has weakened:

- **Concrete explanation.** The Introduction no longer says what deployment demands (H-07). The abstract no longer says what "only" is compared with (H-04).
- **Preferred terminology.** The paper made careful distinctions (runs vs sessions, consistent vs correct) and the prose no longer honors them (H-15, H-23).
- **Appropriate skepticism at paragraph ends.** The skeptical sentences above sit in paragraph bodies. The closers often drop the skepticism (P-02).
- **Emphasis on the actual contribution.** The label audit is the most original result. The novelty paragraph (:121) describes the paper as "a single controlled evaluation", which undersells it (H-08).

---

## 10. Scientific Reasoning Loss

The comparisons below use the text of commit 9001d8c, before the two prose rewrites. Where the current wording already existed there, the section says so.

1. **Mechanism of the random-split gain (H-03).** 9001d8c: "A model-free probe points to the mechanism." Now: "exposes the mechanism." A reader of the earlier version understood a correlational pointer. The current reader understands a demonstrated cause.

2. **Status of prior detectors (H-40).** 9001d8c: "have already been demonstrated". Now: "have already been shown to work". The new wording grants the cited works a claim about working in practice, which the paper disputes.

3. **Transfer on consistent labels (H-04).** 9001d8c abstract: "reach a balanced accuracy of 0.61 to 0.78, below the in-target reference". Now: "of only 0.61 to 0.78." The comparator was replaced by an evaluation word.

4. **Attainability of the test (H-05).** 9001d8c abstract: "no detector passes a deployability test that the published pipeline passes on its own split". Now: "no detector passes our deployability test." The earlier version told the reader the test can be passed. Note that C-03 and H-39 show the earlier claim also needs correction.

5. **What deployment asks (H-07).** 9001d8c: "deployment concerns its behavior on traffic it was not trained on, at a realistic base rate, and within a control loop." Now: "Deployment asks a different question, and we treat a benchmark result as evidence about deployment only when an experiment supports that reading." The definition that links the Introduction to the three criteria is gone.

6. **Composition of the gap (H-09).** 9001d8c named the four tools that separate prior shift, label conflict, and transfer failure. Now the contribution says "A breakdown ... into prior shift, label conflicts, and genuine transfer failure" without the tools, which reads as a quantitative decomposition.

7. **Benign sessions (H-21).** 9001d8c caption: "which indicates that the false positive rate depends more on the particular benign session than on the time of capture." Now: "The benign session matters more than the time of capture." Both overstate relative to :563, and the rewrite removed the hedge.

8. **Radio alert burden (M-43).** 9001d8c: "cannot pin down the alert burden". Now: "cannot fix the alert burden", which can be read as "cannot repair".

Present in both versions (not rewrite damage, still reasoning problems): "the target corpus itself does not limit transfer" (H-24), "What remains is the difference in traffic composition" (H-29), "PPV depends only on π" and the per-10^6 claim (H-10, H-11), "precision stays at or below 0.063" without scope (C-01), and the dismissal of [21] (M-46).

Reasoning problems that no version introduced but that clarity problems now hide: the latency term measured on radio windows and applied to flow detectors (C-02), the mixing of label sets in verdicts (C-03, C-04), and the in-target reference chosen from the protocol the paper criticizes (H-28).

---

## 11. Section-by-Section Diagnosis

**Title and Abstract.** Writing: numbers without comparators. Structure: no gap or significance sentence, two corpora then three. AI-rewrite: comparators replaced by "only", attainability context removed. Risk: C-01 and C-02 misstate the evidence. Repair: C-01, C-02, H-01 to H-05, M-01 to M-05.

**I. Introduction.** Writing: "Deployment asks a different question" empties the key definition. Structure: research question missing here (it sits in II-B), novelty undersold. AI-rewrite: "shown to work". Risk: concedes the cited works' claim, overstates the exporter control. Repair: H-06, H-07, H-08, H-40, H-41, M-08.

**II. Background and Related Work.** Writing: repeated 99.9% sentence. Structure: II-D does three jobs, results claim before results. AI-rewrite: "One constraint shapes everything that follows." Risk: "match theirs in direction and size" across different metrics. Repair: M-10, M-11, M-12.

**III. Deployment Criteria and Threat Model.** Writing: undefined symbols in Eq. (2) to (4). Structure: covariate-shift diagnostic under Criterion 1, unused τ*. AI-rewrite: little. Risk: "PPV depends only on π", per-10^6 claim, test defined without saying which layer each term measures. Repair: H-10 to H-13, M-13 to M-16, C-02.

**IV. Methodology.** Writing: sessions vs runs. Structure: hyperparameters before models, 1-NN and domain classifier missing. AI-rewrite: none notable. Risk: stride unstated, integrity statements stronger than the design, Algorithm 1 inconsistent with the alert unit. Repair: H-14 to H-20, M-17 to M-23.

**V. Experimental Setup.** Writing: clear. Structure: :315 mixes three topics. Risk: π and λ_b unjustified and their range missing. Repair: H-12, M-24, H-34.

**VI-A and VI-B.** Writing: "the same pattern", "come close". Structure: sound. AI-rewrite: "exposes", caption verdict. Risk: mechanism overstated, non-rejection stated as a finding, caption contradicts Limitations. Repair: H-03, H-21, H-22, M-25 to M-30.

**VI-C.** Writing: pass/station/file drift, unexplained remainder of conflicts. Structure: good order (conflict, ownership, ceiling, references, published pipeline). Risk: "correct labels", untested causal direction, Table 6 mixes label sets. Repair: H-16, H-23 to H-26, M-31 to M-36.

**VI-D to VI-F.** Writing: sign conventions, unclear references. Structure: :431 and :444 mix topics. AI-rewrite: closers. Risk: in-target reference from random split, gap attributed to composition by elimination, DC non-significance hidden in abstract. Repair: H-27 to H-31, M-37 to M-42.

**VI-G and VI-H.** Writing: "fix", "unstable", "three evaluation sets". Structure: run-in heading merges into a paragraph. Risk: Fig. 7 cited for a claim it does not show, calibration judged by rejected metric. Repair: H-32, H-33, M-43 to M-45.

**VI-I Latency.** Writing: undefined exporters. Structure: clear. Risk: Fig. 9 caption contradicts the test definition, flow-path cost not connected to the budget. Repair: C-02, H-34, H-35, M-46, M-47.

**VII. Discussion.** Writing: "every benign UE", "and" for "or". Structure: attainability argument rests on a default pass. Risk: C-03, H-39, H-36, H-37. Repair: those plus M-48, M-49.

**VIII and IX.** Writing: honest and specific, the best-aligned part of the paper. Risk: Limitations contradict stronger claims elsewhere (H-06, H-21). Repair: bring the other sections into line with IX, not the reverse.

**X. Conclusion.** Writing: effect stated before cause. Risk: "inflates", "Only latency passes", "realistic base rate". Repair: C-01, C-02, H-38, M-51, M-52, M-53.

---

## 12. Highest-Leverage Repair Plan

1. **Fix the evidence behind the verdicts.** Recompute the published-pipeline clean verdicts with one label set (C-03). Report the clean-flow generalization bounds (C-04). State which layer each latency result applies to and whether the flow-level latency term was measured (C-02).
2. **Rescope every summary number.** Abstract and conclusion: add the evaluation set and comparator to each number (C-01, H-02, H-04, H-05, H-31, M-01, M-04).
3. **Correct the technical statements.** PPV dependence (H-10), per-10^6 claim (H-11), λ_b range and π justification (H-12), Eq. (2) symbols (H-13), window stride and Algorithm 1 (H-14, H-20), Fig. 9 caption (H-35), Fig. 7 reference (H-32).
4. **Unify claim strength.** One verb per finding for the session mechanism, the address evidence, the exporter control, and the target-corpus limit (P-01).
5. **Restore scope boundaries.** Radio layer vs corpora, another corpus vs deployment, emulated loop vs budget conformance (P-03, P-10, H-37, H-38, M-53).
6. **Fix terminology.** Glossary for sessions, splits, stations, copies, fields, and metrics, then a global replacement (P-05, P-06, P-07).
7. **Restore reader orientation.** First-use definitions and Methods coverage for 1-NN, the domain classifier, and the two exporters (P-08, H-17, M-20, H-34).
8. **Restore causal steps.** Two passes, station-1 recording, the 1.6% fold, the position fields' role in the abstract (H-16, M-31, M-36, M-02).
9. **Revise paragraph closers.** Check every last sentence in Results and Discussion against its paragraph (P-02).
10. **Split overloaded paragraphs and remove leftovers.** (P-12, P-13).
11. **Final polish.** Number style, run-in heading, biographies, reference formatting (Low issues).

---

## 13. Global Editing Rules for This Manuscript

- Label every 5G-NIDD statement with its flow set (all flows or without the copies). Never combine terms from both in one verdict.
- Label every latency and alert statement with its layer (radio windows or flows).
- Give every number in the abstract and conclusion its evaluation set and its comparator. Do not replace a comparator with "only".
- Use one verb per finding, matched to the evidence type. The session mechanism and the address evidence are correlational or inferred.
- When an interval includes zero, say what the design cannot tell, and say it in the abstract too.
- Use "another corpus" or "a new site" for results, and "deployment" only for motivation.
- Define every symbol, acronym, and tool at first use, in Methods, before any result uses it.
- Keep one name per unit: session, split, station, file, benign-labeled copies, record-position fields, operational precision, recall.
- End a paragraph with what it showed, not with a broader verdict.
- Bring the rest of the paper into line with the Limitations section, which is the most accurate part.

---

## 14. Master Issue Index

| ID | Lines | Section | Category | Severity | Priority | Pattern |
|---|---|---|---|---|---|---|
| C-01 | 103, 578 | Abstract | Scope, evidence | Critical | P1 | P-09 |
| C-02 | 103, 129, 578, pred:3-10, lat:13, 534 | Abstract, VII-B | Epistemic boundary | Critical | P1 | P-10 |
| C-03 | pred:25, Table 6 | VII-B | Evidence, label sets | Critical | P1 | P-04 |
| C-04 | pred:5, 103, 412, 578 | VII-B | Evidence, negative result | Critical | P1 | P-04, P-14 |
| H-01 | 103, 119, 121, 132 | Abstract, Intro | Consistency | High | P1 | P-12 |
| H-02 | 103 | Abstract | Precision | High | P1 | P-09 |
| H-03 | 103, 124, 327, 578 | Several | Claim strength | High | P1 | P-01 |
| H-04 | 103 | Abstract | Negative result | High | P1 | P-09, P-14 |
| H-05 | 103 | Abstract | Scope | High | P1 | P-09 |
| H-06 | 132, 559 | Intro | Claim strength | High | P1 | P-01 |
| H-07 | 119 | Intro | Abstraction | High | P1 | P-16 |
| H-08 | 121 | Intro | Novelty | High | P2 | P-08 |
| H-09 | 126 | Contributions | Claim strength | High | P1 | P-01 |
| H-10 | 197, 569 | III-C, IX | Technical precision | High | P1 | none |
| H-11 | 197 | III-C | Evidence | High | P1 | P-12 |
| H-12 | 197, 315, 569 | III-C, V | Methods | High | P1 | P-12 |
| H-13 | 178-183 | III-B | Math-prose | High | P1 | P-08 |
| H-14 | 187, 234, 290-303, 536 | III-C, IV | Technical precision | High | P1 | none |
| H-15 | 236, 274, 325, Table 1, 571 | IV, VI | Terminology | High | P2 | P-05 |
| H-16 | 238 | IV-A | Clarity | High | P1 | P-05 |
| H-17 | 268, 270 | IV-C | Information order | High | P2 | P-08 |
| H-18 | 278 | IV-E | Clarity | High | P1 | P-08 |
| H-19 | 274, 483, pred:3 | IV-D | Consistency | High | P1 | P-01 |
| H-20 | 284-306, 203 | IV-F | Math-prose | High | P2 | none |
| H-21 | 359, 354, 563 | VI-B | Consistency | High | P1 | P-02 |
| H-22 | 354 | VI-B | Evidence wording | High | P2 | none |
| H-23 | 368 | VI-C | Claim strength | High | P1 | P-06 |
| H-24 | 372, 412 | VI-C | Causal claim | High | P2 | P-02 |
| H-25 | 366, Table 4 | VI-C | Evidence clarity | High | P2 | none |
| H-26 | Table 6, 399 | VI-C | Table language | High | P1 | P-04 |
| H-27 | 410 | VI-D | Statistical language | High | P2 | P-14 |
| H-28 | 412, 425, 465 | VI-D, VI-F | Reasoning | High | P2 | none |
| H-29 | 440, 559 | VI-E | Reasoning | High | P2 | P-02 |
| H-30 | 436 | VI-E | Reasoning | High | P2 | none |
| H-31 | 103, 467, 565 | Abstract, VI-F | Negative result | High | P1 | P-14 |
| H-32 | 483 | VI-G | Figure alignment | High | P1 | P-12 |
| H-33 | 504, 128, Table 11 | VI-H | Metric consistency | High | P2 | P-07 |
| H-34 | lat:13 | VI-I | Orientation | High | P2 | P-08 |
| H-35 | lat:26 | VI-I | Leftover | High | P1 | P-12 |
| H-36 | 549 | VII-C | Evidence | High | P2 | P-01 |
| H-37 | title, 549, 578 | VII-C, X | Scope | High | P2 | P-03 |
| H-38 | 578 | X | Claim strength | High | P1 | P-14 |
| H-39 | pred:25 | VII-B | Reasoning | High | P1 | none |
| H-40 | 117 | Intro | Citation language | High | P2 | P-01 |
| H-41 | 119 | Intro | Literature claim | High | P2 | none |
| M-01 | 103 | Abstract | Scope | Medium | P1 | P-09 |
| M-02 | 103 | Abstract | Causal compression | Medium | P1 | none |
| M-03 | 103 | Abstract | Referent | Medium | P2 | P-08 |
| M-04 | 103, 578 | Abstract, X | Precision | Medium | P1 | P-09 |
| M-05 | 103 | Abstract | Abstract structure | Medium | P2 | none |
| M-06 | 117 | Intro | Precision | Medium | P2 | none |
| M-07 | 119, 206, pred:3 | Intro, III-D | Terminology | Medium | P2 | none |
| M-08 | 124-129 | Contributions | Orientation | Medium | P2 | P-08, P-13 |
| M-09 | 141 | II-A | Scaffolding | Medium | P3 | P-16 |
| M-10 | 145 | II-B | Structure | Medium | P2 | none |
| M-11 | 149 | II-C | Repetition | Medium | P3 | P-11 |
| M-12 | 153 | II-D | Evidence placement | Medium | P2 | P-13 |
| M-13 | 162 | III-A | Precision | Medium | P2 | none |
| M-14 | 167, Fig. 1 | III-A | Figure language | Medium | P2 | P-07 |
| M-15 | 187-196 | III-C | Notation | Medium | P2 | P-08 |
| M-16 | 219-226 | III-E | Unused concept | Medium | P3 | P-12 |
| M-17 | 236, 571 | IV-A, IX | Terminology | Medium | P2 | P-05 |
| M-18 | 253, Table 2 | IV-B | Methods gap | Medium | P2 | none |
| M-19 | 270 | IV-C | Consistency | Medium | P2 | P-02 |
| M-20 | 268-274, 327, 436 | IV-C | Methods gap | Medium | P2 | P-08 |
| M-21 | 274 | IV-D | Methods gap | Medium | P2 | none |
| M-22 | 278 | IV-E | Statistics | Medium | P2 | none |
| M-23 | throughout | IV-E on | Terminology | Medium | P2 | P-05 |
| M-24 | 315, lat:5 | V, VI-I | Paragraph purpose | Medium | P2 | P-13 |
| M-25 | 325, 408 | VI-A, VI-D | Metric consistency | Medium | P2 | P-07 |
| M-26 | 327 | VI-A | Evidence | Medium | P2 | P-09 |
| M-27 | 103, 327, Table 3 | VI-A | Numeric consistency | Medium | P3 | none |
| M-28 | 329 | VI-A | Referent | Medium | P2 | P-08 |
| M-29 | 352 | VI-B | Negative result | Medium | P2 | P-14, P-02 |
| M-30 | 354 | VI-B | Scope | Medium | P2 | P-03 |
| M-31 | 368 | VI-C | Mechanism | Medium | P2 | none |
| M-32 | 368, 561 | VI-C | Scope | Medium | P2 | P-01 |
| M-33 | 238, 366-372, Fig. 4 | VI-C | Terminology | Medium | P2 | P-05 |
| M-34 | 385 | VI-C | Figure language | Medium | P2 | P-06 |
| M-35 | Table 5, 372 | VI-C | Statistics | Medium | P2 | none |
| M-36 | 397 | VI-C | Mechanism | Medium | P2 | P-06 |
| M-37 | 412 | VI-D | Methods gap | Medium | P2 | none |
| M-38 | 429 | VI-D | Sign, support | Medium | P2 | P-12 |
| M-39 | 429 | VI-D | Reasoning | Medium | P2 | none |
| M-40 | 431 | VI-D | Label sets | Medium | P2 | P-04 |
| M-41 | 438 | VI-E | Precision | Medium | P2 | P-01 |
| M-42 | 442 | VI-E | Causal claims | Medium | P2 | P-02 |
| M-43 | 479 | VI-G | Word choice | Medium | P2 | none |
| M-44 | 487, lat:26 | VI-G, VI-I | Captions | Medium | P2 | P-12 |
| M-45 | 506 | VI-H | Label sets | Medium | P3 | P-04 |
| M-46 | lat:5 | VI-I | Citation language | Medium | P2 | P-02 |
| M-47 | lat:9 | VI-I | Interpretation | Medium | P2 | none |
| M-48 | 538 | VII-A | Overgeneralization | Medium | P2 | P-02 |
| M-49 | pred:5 | VII-B | Logic | Medium | P2 | none |
| M-50 | 563 | IX | Referent | Medium | P2 | P-08 |
| M-51 | 578 | X | Epistemic boundary | Medium | P2 | P-01 |
| M-52 | 103, 125, 368, 561, 578 | Several | Epistemic drift | Medium | P2 | P-01 |
| M-53 | 585 | X | Consistency | Medium | P2 | P-01 |
| M-54 | 127, 192-197, 479-484 | Throughout | Terminology | Medium | P2 | P-07 |
| M-55 | 444 | VI-E | Paragraph purpose | Medium | P3 | P-13 |
| L-01 | 91 | Title | Terminology | Low | P3 | P-03 |
| L-02 | 103 | Abstract | Literature claim | Low | P3 | none |
| L-03 | 117 | Intro | Referent | Low | P3 | P-08 |
| L-04 | 121 | Intro | Repetition | Low | P3 | P-11 |
| L-05 | 141 | II-A | Acronyms | Low | P3 | P-08 |
| L-06 | 149 | II-C | Transition | Low | P3 | P-16 |
| L-07 | 173, 178 | III-B | Notation | Low | P3 | P-08 |
| L-08 | 234, Table 1 | IV-A | Terminology | Low | P3 | P-05 |
| L-09 | 236, 350, 563 | IV-A, VI-B | Repetition | Low | P3 | P-11 |
| L-10 | 238 | IV-A | Orientation | Low | P3 | P-06 |
| L-11 | 243 | IV-A | Caption | Low | P3 | none |
| L-12 | 253 | IV-B | Precision | Low | P3 | none |
| L-13 | 255 | IV-B | Naming | Low | P3 | P-01 |
| L-14 | 268 | IV-C | Order | Low | P3 | none |
| L-15 | 282 | IV-F | Unsupported claim | Low | P3 | none |
| L-16 | 315 | V | Citation wording | Low | P3 | none |
| L-17 | 325 | VI-A | Sentence purpose | Low | P3 | none |
| L-18 | 343 | VI-A | Terminology | Low | P3 | P-07 |
| L-19 | 366, 370 | VI-C | Referent | Low | P3 | P-08 |
| L-20 | 372 | VI-C | Precision | Low | P3 | none |
| L-21 | 395 | VI-C | Precision | Low | P3 | none |
| L-22 | 397 | VI-C | Scaffolding | Low | P3 | P-16 |
| L-23 | 410 | VI-D | Sentence purpose | Low | P3 | P-07 |
| L-24 | 412 | VI-D | Order | Low | P3 | none |
| L-25 | 431 | VI-D | Paragraph purpose | Low | P3 | P-13 |
| L-26 | 438 | VI-E | Interpretation | Low | P3 | none |
| L-27 | 440 | VI-E | Statistics | Low | P3 | P-15 |
| L-28 | 458 | VI-E | Referent | Low | P3 | P-08 |
| L-29 | 465, 586 | VI-F, X | Consistency | Low | P3 | P-06 |
| L-30 | 467 | VI-F | Interpretation | Low | P3 | P-15 |
| L-31 | 481 | VI-G | Transition | Low | P3 | P-16 |
| L-32 | 483 | VI-G | Density | Low | P3 | P-13 |
| L-33 | 483-484 | VI-G | Formatting | Low | P3 | none |
| L-34 | 504 | VI-H | Terminology | Low | P3 | P-15 |
| L-35 | 504, 511 | VI-H | Missing evidence | Low | P3 | none |
| L-36 | lat:3, 7, 16 | VI-I | Leftover | Low | P3 | P-12 |
| L-37 | lat:9 | VI-I | Scope | Low | P3 | P-02 |
| L-38 | lat:11 | VI-I | Scaffolding | Low | P3 | P-11, P-16 |
| L-39 | lat:13 | VI-I | Missing reason | Low | P3 | P-15 |
| L-40 | 141, 162, 534 | II-A, VII-A | Repetition | Low | P3 | P-11 |
| L-41 | 540 | VII-A | Speculation | Low | P3 | P-02 |
| L-42 | pred:7 | VII-B | Scaffolding | Low | P3 | P-16 |
| L-43 | 554 | VIII | Generic statement | Low | P3 | none |
| L-44 | 561 | IX | Precision | Low | P3 | P-06 |
| L-45 | 567 | IX | Clause attachment | Low | P3 | none |
| L-46 | 580-586 | X | Precision | Low | P3 | P-11 |
| L-47 | several | VI | Number style | Low | P3 | P-15 |
| L-48 | 592-610 | Biographies | Formatting | Low | P3 | none |
| L-49 | refs [12], [14] | References | Formatting | Low | P3 | none |
| L-50 | 538 | VII-A | Acronym | Low | P3 | P-08 |
| L-51 | 350 | VI-B | Terminology | Low | P3 | P-05 |

Totals: 4 Critical, 41 High, 55 Medium, 51 Low (151 issues), 16 recurring patterns.

---

## 15. Completeness Check

- Every section: yes, Title through biographies (Section 2).
- Every page: yes, all 19 rendered pages were read as extracted text.
- Every line: every prose paragraph (one per source line), every caption, both input section files. Preamble lines were checked for rendered effects only.
- Equations: Eq. (1) to (7) and Algorithm 1.
- Captions: all 14 table captions and 10 figure captions, plus the text inside Figures 1 and 4.
- References: wording and formatting only. Bibliographic details were not verified.
- Recurring patterns searched after first sighting: yes (16 patterns, with locations).
- Local and global problems: both.
- Writing vs scientific problems: separated by category. C-02 to C-04, H-14, H-28, and H-39 are scientific-reasoning problems that the writing hides. They were checked against the analysis code and result files, not only the prose.
- No rewriting: the audit describes what to restore and does not propose replacement sentences.
- No invented information: earlier-version comparisons use commit 9001d8c only. The R1 pass computation comes from `results/EXP-052/processed/published_ladder.csv`.
- Not covered: the plotted content of the figure images, and the two `.tex` files that main.tex does not input (Section 2).
