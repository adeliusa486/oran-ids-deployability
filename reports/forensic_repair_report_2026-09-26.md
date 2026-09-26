# Revision report: repair of the manuscript against the forensic writing audit

Audit: `reports/forensic_writing_audit_2026-09-26.md` (151 issues, 16 patterns).
Revised sources: `paper/main.tex`, `paper/latency_section.tex`, `paper/predicate_section.tex`, `paper/fig1_architecture.tex`, `paper/fig_conflict.tex`, `paper/references.bib`.
Analysis code changed where a repair needed a number the paper did not yet compute: `analysis/revision_stats.py`, `analysis/make_numbers.py`, `analysis/make_tables_v2.py`, `analysis/make_figures_v2.py`, new `analysis/nn_chance.py` (writes `results/EXP-042/processed/nn_chance.json`). Every new number is computed from committed results, and no experiment was re-run.

## A. Repair Completed

The manuscript was revised against the forensic audit, issue by issue, followed by a manuscript-wide search for each of the 16 recurring patterns.

| | Count |
|---|---|
| Audit issues identified | 151 (4 Critical, 41 High, 55 Medium, 51 Low) |
| Fixed | 143, of which 4 leave a residual item for the authors (H-12, H-37, M-21, L-48) |
| Merged into another fix | 4 (L-04, L-09, L-22, L-40) |
| Not fixed: requires author input | 3 (L-01, L-16, L-43) |
| Partly fixed: rest needs evidence not in hand | 1 (L-35: a reading of the reliability diagram was not added) |

Completion is not 100%. Section F lists what remains.

Three repairs change what the paper claims, because the audit showed the earlier claim did not follow from the paper's own data:

1. **C-03 (attainability).** With both terms computed on the flows without the benign copies, DT and RF *pass* the test at R1 (random split, no Seq/Offset). RF with the published features passes at R3 (across base stations). Nothing passes at R2 (capture files held out). The old text said the pipeline fails "one rung later ... on the flows without the benign copies alike". That verdict mixed the clean alert term with the all-flows generalization term (`revision_stats.py`, now fixed).
2. **C-04 (generalization on consistent labels).** On the flows without the copies, the generalization upper bounds are 0.29 to 0.41. All six still fail the term, but because the intervals are wide, not because a loss is established. The loss is significant for one architecture of six. The verdict (0 of 6) is unchanged and rests on the alert term.
3. **M-38 (reverse transfer).** The text said DT and RF lose significantly. The data show that three changes are significant after Holm correction: LR's *gain* of 0.037 and the losses of DT and RF.

## B. Audit Resolution Matrix

Locations refer to sections of the revised paper. "Gen." marks a generator change (macro, table, or figure).

| ID | Status | Location | What changed |
|---|---|---|---|
| C-01 | FIXED | Abstract, X | Abstract gives the maximum over all transfer targets (0.092, Gen. `ThAPPVbest`) for "any transferred detector"; conclusion restricted to transferred detectors at the declared prevalence |
| C-02 | FIXED | Abstract, III-D, III-E, VI-I, VII-B, Table 14, Fig. 1, Fig. 9, IX, X | Latency term stated as measured for window-level detectors only; flow-level term marked not measured (export + mapping ≈ 10 ms, no transport path); Table 14 B_min footnoted; detection-delay caveat in conclusion; "Only latency passes" removed |
| C-03 | FIXED | VII-B, Table 6, `revision_stats.py` | Clean verdict recomputed on one label set; Table 6 gains "Pass (all / w/o copies)"; attainability paragraph rewritten to the new result (see A) |
| C-04 | FIXED | Abstract, VII-B, Fig. 10b, X, `revision_stats.py` | Clean predicate uses the clean Δ_BA bound (Gen. `PredCleanGen*`); significance 1 of 6 in abstract and conclusion; Fig. 10b shows both label sets |
| H-01 | FIXED | Abstract, I | Three corpora named in abstract; "one of our three corpora", "two of our corpora" |
| H-02 | FIXED | Abstract, VI-A | Comparator "over a session-disjoint split"; sequence-model clause moved out of abstract; VI-A notes the smaller Holm family |
| H-03 | FIXED | Abstract, I, VI-A, X | One verb class ("consistent with", "points to"); VI-A adds that the probe does not show the models rely on sessions |
| H-04 | FIXED | Abstract | Comparator restored (in-target references 0.842 to 0.982) and significance for 1 of 6 |
| H-05 | FIXED | Abstract | Test introduced with its three terms; scope "transferred detector"; the attainability contrast is in VII-B, not in the abstract (word limit) |
| H-06 | FIXED | I | "remove" → "reduce", with the undocumented Zeek configuration |
| H-07 | FIXED | I | Deployment question stated concretely (unseen site, base rate, control loop), plus explicit research question |
| H-08 | FIXED | I | Effects named; labeling fault stated as a finding in the novelty paragraph |
| H-09 | FIXED | I (contributions) | "Breakdown ... genuine transfer failure" → "separate tests" of prior shift, labels, exporter, traffic |
| H-10 | FIXED | III-C, IX | "Of the two declared parameters, only π enters the PPV" |
| H-11 | FIXED | III-C | Per-10^6 claim removed; alert counts at other λ_b follow from the reported FPR |
| H-12 | FIXED (residual) | III-C, V, IX | "vary over a range" removed; linear scaling in λ_b stated; π declared with "no measured source", break-even π in VII-B. Source for π needs author input (F) |
| H-13 | FIXED | III-B | F, P^(j), W_1 defined; W̄_1 labeled descriptive, not part of the test |
| H-14 | FIXED | III-C, IV-A, IV-F, Algorithm 1 | Non-overlapping windows stated; Algorithm 1 scores once per completed window; timing xApp deviation stated |
| H-15 | FIXED | IV, VI-A, Tables 1 and 3, Fig. 2, IX | "Session-disjoint" throughout; Table 1 "30 sessions" (Gen.); Fig. 2 legend (Gen.) |
| H-16 | FIXED | IV-A | Ten files per station, same sequence of attack types, file-to-station mapping |
| H-17 | FIXED | IV-C | Hyperparameters placed with the models they describe |
| H-18 | FIXED | IV-E | "Training sets of different splits overlap, as do their test sets" |
| H-19 | FIXED | IV-D | Exceptions listed: comparison random splits, best-threshold searches on D_B |
| H-20 | FIXED | IV-F, Algorithm 1 | δ_m replaced by in-xApp budget B_x = B minus reserved t_ind and acknowledgment; ℓ scope stated; timing xApp records full loop |
| H-21 | FIXED | Fig. 3 caption | Verdict removed; caption states the early session flagged more than the late one |
| H-22 | FIXED | VI-B | All ten sessions accounted for (6 low, session 5 at 0.14, sessions 4 and 8, session 29); means over architectures; early exceeds late (Gen. `BenEarly*`, `BenMid*`) |
| H-23 | FIXED | VI-C | "Correct labels" removed; reason for setting aside rather than relabeling |
| H-24 | FIXED | VI-C | Tested direction (2→1) separated from inferred direction (1→2); closer narrowed to the shared features |
| H-25 | FIXED | VI-C | Remaining 69,324 flows explained (station 1's own flood with copy content; Gen. `LcOwnConf`, with a consistency guard) |
| H-26 | FIXED | Table 6 | RF BA and FPR both on the flows without copies; header says so (Gen.) |
| H-27 | FIXED | VI-D | Correlation called too imprecise to decide; MLP example kept; macro-F1 mechanism stated |
| H-28 | FIXED | VI-D, VI-F, Fig. 5 | Reference named (random split, most optimistic); capture-file reference given; D_C compared with the leave-one-file-out reference |
| H-29 | FIXED | VI-E | Both remaining explanations named; which evidence favors composition |
| H-30 | FIXED | VI-E | Composition shown; segmentation left to the Zeek test |
| H-31 | FIXED | Abstract, VI-F, X | "Behaves the same way" removed; non-significance on D_C stated in VI-F and conclusion; repeated findings named |
| H-32 | FIXED | VI-G | Claim restricted to D_B, Fig. 7b; radio improvement stated with Fig. 7a |
| H-33 | FIXED | VI-H, Table 11 | Calibration judged by target balanced accuracy (Gen.); isotonic sign given (−0.21 / +0.05) |
| H-34 | FIXED | V, VI-I | Both exporters introduced in V |
| H-35 | FIXED | Fig. 9 caption, `revision_stats.py` docstring | Panel (a) described as computation stages |
| H-36 | FIXED | VII-C | "Most" removed; comparison uses the reproduced pipeline and D_C random split |
| H-37 | FIXED (residual) | I, VII-C, X, IX | "Another site"/"another corpus in our transfer tests" for results; title unchanged (L-01) |
| H-38 | FIXED | X | Scoped to the radio layer of NetsLab-5GORAN-IDD, interval included |
| H-39 | FIXED | VII-B | Generalization-by-construction and unmeasured latency stated for the published pipeline |
| H-40 | FIXED | I | "Built and evaluated, each in its own testbed" |
| H-41 | FIXED | I, Abstract | "Several studies of machine-learning intrusion detection for 5G"; no new citations invented |
| M-01 | FIXED | Abstract | "any content-only classifier" |
| M-02 | FIXED | Abstract | Causal link (fields tell copies apart) and clean-flow result stated |
| M-03 | FIXED | Abstract | "transfer gap"; "attacker at the other base station" |
| M-04 | FIXED | Abstract, VI-I, X | 99th percentile 4.45 to 4.95 ms; 5.01 ms given as upper bound |
| M-05 | FIXED | Abstract | Gap sentence and implication sentence |
| M-06 | FIXED | I | Visibility tied to E2 subscriptions and per-device measurements |
| M-07 | FIXED | I, III-D, VII-B | Specification quoted once; test uses B = 10 ms, B_min also reported |
| M-08 | FIXED | I | Ladder defined in first bullet; copies introduced before bullets; "mean of per-split precision"; last bullet split |
| M-09 | FIXED | II-A | Scaffolding sentence removed |
| M-10 | FIXED | I, II-B | Research question moved to Introduction; II-B points to it |
| M-11 | FIXED | II-C | Repeated 99.9% sentence removed |
| M-12 | FIXED | II-D, VI-D | Comparison moved to VI-D with metric caveat; assumptions of borrowed methods stated; paragraph split |
| M-13 | FIXED | III-A | Control-plane attack added; KPM reports delivered, windows built in the xApp |
| M-14 | FIXED | Fig. 1 and caption | Column numbers removed (markers 01–03 unique); KPI → KPM; "update policy" → "remap QoS flow"; flow path marked as assumed |
| M-15 | FIXED | III-C, Table 10 | τ, R(τ) defined before use; "Recall" in Table 10 (Gen.) |
| M-16 | FIXED | III-E | Eq. (7) replaced by its definition in prose (never reached by a transferred detector) |
| M-17 | FIXED | IV-A, IX | Subcategory defined; Limitations "one attack category" |
| M-18 | FIXED | IV-B | Byte counts attributed per exporter; NFStream mapping in text |
| M-19 | FIXED | IV-C | "The one transfer model that sees target data" |
| M-20 | FIXED | IV-C | 1-NN and domain classifier specified |
| M-21 | FIXED (residual) | IV-D | 80/20 proportions; random-split in-target reference; 300,000 "fixed before the first run" (rationale needs author input) |
| M-22 | FIXED | IV-E | n counts; fixed-target limitation of the correction |
| M-23 | FIXED | throughout | "Split" defined once; folds/draws/seeds replaced; "control draws" kept as a distinct design |
| M-24 | FIXED | V, VI-I | Paragraph split; 29 ms identified as a configuration not in Table 12 |
| M-25 | FIXED | VI-A | Why macro-F1 is valid for the protocol comparison |
| M-26 | FIXED | VI-A, `nn_chance.py` | Chance levels 27% (same category) and 5% (any window) |
| M-27 | FIXED | Abstract, VI-A | NNGain from unrounded values (0.14); 1-NN scores at three decimals (Gen.) |
| M-28 | FIXED | VI-A | Referent named; sequence models below 1-NN |
| M-29 | FIXED | VI-B | "Design cannot separate"; near-chance forward result stated |
| M-30 | FIXED | VI-B | Scoped to unseen sessions of this testbed |
| M-31 | FIXED | VI-C | Mechanism stated as undocumented; "evidently" removed |
| M-32 | FIXED | VI-C | Lists which results appear with and without copies and which use all flows |
| M-33 | FIXED | IV-A, VI-C, Fig. 4 | "Pass" removed; station/file mapping stated once; Fig. 4 labels |
| M-34 | FIXED | Fig. 4 | Row index added; "reproduced" |
| M-35 | FIXED | VI-C, VI-D | One to three samples, no intervals, stated where references are compared |
| M-36 | FIXED | VI-C | 1.6% explained; "record-position fields" throughout |
| M-37 | FIXED | V, VI-D | Re-run is the first 10 splits, kept per-cluster counts, runtime-limited |
| M-38 | FIXED | VI-D | Sign convention; Holm; corrected to three significant changes; pointer to repository table (Gen. `TrRev*`) |
| M-39 | FIXED | VI-D | Hypothesis accounts for the copies; "more varied" removed |
| M-40 | FIXED | VI-D | Clean FPR of the five models given (Gen. `FwdEnsCleanFPR*`) |
| M-41 | FIXED | VI-E | "Zeek (version 8.0.10), the exporter family of D_A" |
| M-42 | FIXED | VI-E | Both explanations marked as likely/untested; AE below chance noted |
| M-43 | FIXED | VI-G | Four sets; "imprecise"; "pin down" |
| M-44 | FIXED | Table 10, Fig. 9 captions | Internal IDs removed; seed counts per block stated |
| M-45 | FIXED | VI-H, Table 11 | "Published target prior" |
| M-46 | FIXED | VI-I | Input validation marked as unmeasured attribution; cross-host sentence reworded |
| M-47 | FIXED | VI-I | Differences (C API/WSL2 vs Python/Windows) named; cause not isolated |
| M-48 | FIXED | VII-A | "Average benign UE"; implication for the latency criterion |
| M-49 | FIXED | VII-B | "Any one of ... suffices on its own" |
| M-50 | FIXED | IX | Both explanations named |
| M-51 | FIXED | X | "Declared prevalence"; ρ = 0.1 named |
| M-52 | FIXED | Abstract, I, VI-C, IX, X | "Point to" throughout; conflict before 99.9% in conclusion |
| M-53 | FIXED | VI-I, VII-B, X | Latency worded as a measurement on an emulated loop, not conformance |
| M-54 | FIXED | III-C, Table 10 | Operational and corpus precision defined; "Recall", "Corpus prec." (Gen.) |
| M-55 | FIXED | IV-B, VI-D | Shared-space cost moved to IV-B, macro-F1 point to VI-D |
| L-01 | NOT FIXED — REQUIRES AUTHOR INPUT | Title | Title change is the authors' decision (F) |
| L-02 | FIXED | Abstract | "Several" |
| L-03 | FIXED | I | Referents named; "obvious" removed |
| L-04 | MERGED | I | Merged into M-11/II-D repair: Axelsson/Sommer–Paxson/Arp/Pendlebury stated once in II-D |
| L-05 | FIXED | II-A | E2SM expanded |
| L-06 | FIXED | II-C | "Easier"; "labels and flow records ... can be wrong" |
| L-07 | FIXED | III-B | "Measure"; Δ_F1 sign defined |
| L-08 | FIXED | IV-A, Table 1 | "We use both" removed; "D_A flows" (Gen.) |
| L-09 | MERGED | IV-A, IX | Merged into H-15/M-17 edits: schedule stated in VI-B only, referenced elsewhere |
| L-10 | FIXED | IV-A | Combined file defined; row-index sentence removed; "full-field release" everywhere |
| L-11 | FIXED | Table 1 caption | Roles corrected, D_B as source for reverse and D_C |
| L-12 | FIXED | IV-B | "Base quantities"; 1 ms floor |
| L-13 | FIXED | IV-B | "Robust" stated as design intent |
| L-14 | FIXED | IV-C | DT depth once; n−/n+ in words; reason next to decision |
| L-15 | FIXED | IV-F | Softened; check must precede the send |
| L-16 | NOT FIXED — REQUIRES AUTHOR INPUT | V | "Expect" kept: whether [61] measured or estimated could not be checked (F) |
| L-17 | FIXED | VI-A | Purpose of the uncorrected p stated |
| L-18 | FIXED | Fig. 2 caption | "Gain" |
| L-19 | FIXED | VI-C | Counts named; "almost every record" |
| L-20 | FIXED | VI-C | "The upper end of which is the ceiling" |
| L-21 | FIXED | VI-C, Table 6 | "Under their protocol"; KNN reason (runtime) |
| L-22 | MERGED | VI-C | Merged into M-36: "Put simply" restatement removed, one closer kept |
| L-23 | FIXED | VI-D | "Both prevalence-independent measures"; purpose of the floors |
| L-24 | FIXED | VI-D | Range for the five nonlinear models (0.70–0.85), LR none (Gen.) |
| L-25 | FIXED | VI-D | Criterion stated; paragraph split from the reverse direction |
| L-26 | FIXED | VI-E | Flow-count difference noted, not analyzed |
| L-27 | FIXED | VI-E | Interval type (uncorrected paired t) and "all six" |
| L-28 | FIXED | Fig. 6 caption | "The shift" |
| L-29 | FIXED | VI-F, X | "Nearly consistent"; requirement 6 asks for the share |
| L-30 | FIXED | VI-F | Inversion explained; "(0 and 0 of six)" removed; repeated findings named |
| L-31 | FIXED | VI-G | Shared point stated |
| L-32 | FIXED | VI-G | Split; ratio direction stated |
| L-33 | FIXED | VI-G | Run-in heading starts a new paragraph |
| L-34 | FIXED | VI-H | "Reachable"; 2×10^−5 (Gen.); Platt sentence reordered |
| L-35 | PARTLY FIXED | VI-H, Fig. 8 | FPR change given; seed difference explained; a reading of the diagram not added (needs inspection of the plotted curves) |
| L-36 | FIXED | VI-I, Table 12 | "All 12 exports reproduce ... exactly"; dash note removed |
| L-37 | FIXED | VI-I | "For latency" |
| L-38 | FIXED | VI-I | Caveat kept in III-D, V, IX; "Keep in mind" removed |
| L-39 | FIXED | VI-I | Why two captures (reference too slow on the largest); "two" |
| L-40 | MERGED | III-A | Merged into M-13: III-A statement removed, kept in II-A and VII-A |
| L-41 | FIXED | VII-A | "Would likely detect ... we did not test one" |
| L-42 | FIXED | VII-B | Rhetorical question removed; label set stated |
| L-43 | NOT FIXED — REQUIRES AUTHOR INPUT | VIII | Whether the 5G-NIDD authors were contacted (draft exists, unsent) (F) |
| L-44 | FIXED | IX | "Content copies"; "all 10 files of station 1" |
| L-45 | FIXED | IX | Clause attachment fixed |
| L-46 | FIXED | X | Requirement 1 asks for a group-disjoint reference; old requirement 5 merged into 2 |
| L-47 | FIXED | Gen. `make_numbers.py` | Counts 0–9 printed as words |
| L-48 | FIXED (residual) | Biographies | Degree forms (B.S., M.Sc., Ph.D.), repeated "lightweight"; missing years and one affiliation need author input |
| L-49 | FIXED | references.bib | [12] note moved to a BibTeX comment, arXiv v2 cited; [14] title dash → colon |
| L-50 | FIXED | VII-A | "A1 interface of the non-real-time RIC" |
| L-51 | FIXED | VI-B | "Captured in blocks by category" |

## C. Global Patterns Repaired

- **P-01 claim-strength drift:** one verb class per finding (session mechanism "consistent with / points to"; address evidence "point to"; exporter control "reduce"; target corpus limit narrowed to the shared features).
- **P-02 paragraph-final verdicts:** every Results and Discussion closer re-read against its paragraph ("The benign session matters more...", "The target corpus is not what limits transfer", "What is left is...", "Time order, in short...", "Only latency passes", "Once a RIC is in the path..." rewritten).
- **P-03 "deployment" for "another corpus":** results say "another site" or "another corpus in our transfer tests"; "Criterion 1: Generalization Across Corpora".
- **P-04 mixed label sets:** every D_B statement labeled (all flows / without the copies); verdicts and Table 6 now use one label set; `revision_stats.py` fixed at source.
- **P-05, P-06 terminology:** session (not run or scenario), split (not fold, draw, or seed), station/file (not pass), benign-labeled copies, record-position fields, full-field release, consistent (not correct) labels.
- **P-07 metrics:** operational vs corpus precision defined; "recall" replaces TPR; macro-F1 use justified where kept; calibration judged by balanced accuracy.
- **P-08 definitions before use:** τ, R(τ), F, P^(j), W_1, E2SM, A1, 1-NN, domain classifier, exporters, subcategory, combined file.
- **P-09, P-14 summary numbers and non-significance:** abstract and conclusion numbers carry their evaluation set and comparator; non-significant results stated as such.
- **P-10 radio/flow merging:** every latency statement tagged window-level or flow-level.
- **P-11 repetition:** 99.9% sentence, capture schedule, "E2 carries no packets", base-rate citations stated once.
- **P-12 leftovers:** per-10^6 claim, "Dashes" note, EXP IDs in captions, Fig. 9 "decision path", unused τ*.
- **P-13 overloaded paragraphs:** II-D, V, VI-D, VI-G split or restructured.
- **P-15 number style:** word counts, 2×10^−5, "all six", non-breaking negative numbers (`\mbox`).
- **P-16 scaffolding:** "One constraint shapes everything", "Put simply", "Keep in mind", "How far would...? Fig. 10 shows it", section roadmaps.

## D. Scientific Meaning Preservation

Checked explicitly: equations (1)–(6), Algorithm 1, assumptions (declared π and λ_b, fixed target, host-only latency), every numerical result (all numbers are macros from `tables/generated/numbers.tex`; a scripted comparison against the pre-revision sources shows no citation lost, and every removed number macro is replaced by a more specific one), statistical claims (intervals, Holm, non-significance), experimental conditions, limitations, negative results, and contribution claims.

- Eq. (7) (τ*) was removed as an equation and kept as a prose definition, because no transferred detector reaches it (M-16).
- Algorithm 1 changed as the audit required: one decision per completed window, and the budget check against B_x (H-14, H-20).
- Findings that changed are listed in Section A (C-03, C-04, M-38). They follow the recomputation, and each rests on data already in `results/`.
- Needs author confirmation: the new attainability reading (C-03), and the definition of B_x as "operator-reserved" time (H-20), which describes a design and not a measurement.

## E. Page-Limit Verification

- Target format: official IEEE Access LaTeX class (`paper/access/ieeeaccess.cls`), two-column; class formatting untouched.
- Applicable limit: IEEE Access sets no fixed page limit in the supplied template. The limit applied is the author's earlier instruction to stay under 20 pages, which equals the pre-revision length of 19 pages.
- Final page count: **19 pages** (`scripts/build_paper.py`: 0 errors, 0 undefined references, 0 overfull boxes, 0 BibTeX warnings). The count includes references and biographies; there is no appendix.
- Compression was required. The repairs added about 2,200 words (21 pages), and these were recovered by removing repetition, scaffolding, duplicated caveats, and verbose captions. Rendered words: 17,876 before, about 17,700 after. No font, margin, spacing, or figure-size changes.
- Abstract: 248 rendered words (IEEE Access limit 250).
- Reproducibility: `scripts/reproduce.py paper` regenerates every statistic, macro, table, and figure from `results/` and reports 38 of 38 generated files identical (manifest refrozen after the intended changes); the full statistics run reproduces the targeted C-03/C-04 refresh exactly; pytest 61/61; withdrawn-claims and placeholder guards OK.

## F. Remaining Issues

1. **L-01 / H-37 title.** "What Held-Out Accuracy Predicts About Deploying..." promises more than the six-point correlation shows. Needs: author decision on a title such as "...Held-Out Scores..." or one naming transfer.
2. **L-16 Jin et al. [61].** Needs a check of SoftCell for whether "several hundred flows per second" was measured ("report") or projected ("expect", kept).
3. **L-43 ethics.** Needs a decision on whether and when the 5G-NIDD authors are told about the label conflict (`reports/5gnidd_label_query_draft.md` is unsent), and a sentence saying so.
4. **H-12 π = 0.002.** Now stated as a declared value with no measured source. Needs a citation if the authors have one; the break-even analysis keeps the conclusion independent of it.
5. **M-21 300,000-flow sample.** The code records it as declared before the first run, with no rationale. Needs the reason (probably compute cost) if the authors want to state one.
6. **L-48 biographies.** Degree years for Eraj Khan and Gahangir Hossain, and confirmation of Ali Akarma's affiliation.
7. **L-35 Fig. 8.** A one-line reading of the reliability diagram needs someone to inspect the plotted curves.
8. **C-03 new finding.** The attainability paragraph now says the test is passable within one corpus once the label conflict is removed. The authors should confirm they accept this reading.
