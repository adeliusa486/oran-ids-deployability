# Response to Reviewers

**Manuscript:** Intrusion Detection for IoT Traffic in O-RAN Edge Data Centers: Why Accuracy Alone Is Not Enough
**Round:** resubmission after the decision of 24 September 2026 (simulated review, `reports/peer_review_ieee_access_2026-09-24.md`)

We thank the reviewers for detailed and specific reports. Several comments found errors that changed our conclusions, and we have treated them as such. Before the point-by-point replies, the changes that matter most:

1. **Every operating-point table is now built from pooled confusion counts.** Two tables and one figure of the previous version averaged precision over folds, the estimator the paper itself criticized, and were arithmetically impossible at the declared base rate (Reviewer 6, comment 2). They are rebuilt from new runs that store counts at every threshold.
2. **Two figures with no data behind them were removed** and replaced by figures generated from the results (Reviewer 6, comment 4).
3. **The literature survey was removed.** Its counts had not come from an executed screening, so the table and its protocol paragraph are deleted (Reviewer 6, comment 10).
4. **The MLP was trained without class weighting**, contrary to the stated protocol (Reviewer 3, comment 5). With the weighting the paper describes, the MLP no longer falls below the trivial baseline on the target corpus, and two headline sentences built on that result are withdrawn.
5. **All intervals are now Nadeau-Bengio corrected** for overlapping resampled splits (Reviewer 6, comment 9). Some effects that were significant under the naive test are not, and the manuscript says so.
6. **Transfer is reported in balanced accuracy first.** The majority baseline loses as much macro-F1 as the detectors, so macro-F1 cannot separate prior shift from other shift. Balanced accuracy falls by [[N:TrBAdropMin]] to [[N:TrBAdropMax]] while both baselines stay at chance (Reviewers 3 and 6).
7. **Ten new or re-run experiments** answer the requests for controls, model families and runtime measurements. None of the new values is projected or estimated: every number in the manuscript is generated from `results/` by a script, and the prose quotes numbers only through generated macros.

Section, table and figure numbers below refer to the revised manuscript.

---

## Reviewer 1

**Comment 1.1.** Markdown asterisks appear in the compiled PDF in Sections VI-B and VI-C.
**Response.** Agreed.
**Action.** The affected paragraphs were rewritten and no Markdown syntax remains. The build was checked for literal asterisks.

**Comment 1.2.** The indicator function in Eq. (7) renders as the wrong symbol.
**Response.** `\mathbb{1}` is not defined for digits in amssymb.
**Action.** The indicator is now `\mathbf{1}` ([[eq:deploy]]).

**Comment 1.3.** Section VII duplicates Section VI, with repeated tables and figures.
**Response.** Agreed. The duplicated section was a second draft that had survived.
**Action.** The results are now one section ([[sec:results]]) with one copy of each table and figure. The duplicated tables and figure are deleted.

**Comment 1.4.** Two figures are never cited.
**Action.** Every figure and table is now cited in the text, which we checked with the LaTeX references list.

**Comment 1.5.** An internal identifier in a caption, and project notes inside two bibliography entries.
**Action.** Removed. Every bibliography entry with a DOI was also checked against Crossref. This corrected an author list (5G-Spector), an author count (SCOPE), a DOI (ColO-RAN) and a page range (5G-NIDD descriptor), and replaced two arXiv entries with their published versions.

**Comment 1.6.** The pre-submission box, the placeholder author block and the conference template.
**Action.** The box is removed. The manuscript now uses the IEEEtran journal layout. The official IEEE Access class and the author biographies will be applied at submission, because the class file is distributed through the IEEE Author Center rather than with the manuscript sources.

**Comment 1.7.** Hardware and thread settings behind the timings.
**Response.** The host is a 13th Gen Intel Core i9-13900H (14 cores, 20 threads) with 47.6 GB of memory, running Windows 11 Pro build 26120. The earlier timings ran the random forest and XGBoost through a thread pool on every single-row call.
**Action.** [[sec:setup]] states the host, library versions and thread settings. The latency experiment was re-run with one thread per library, garbage collection enabled and 20,000 timed calls ([[sec:res:latency]]). The random forest's median single-row time falls from [[N:LatRFthreadsPfifty]] ms with its thread pool to [[N:LatRFarrPfifty]] ms on one thread, so most of the earlier figure was thread start-up.

**Comment 1.8.** How many trained models were timed.
**Action.** One trained model per architecture and layer, fitted on split seed 101, as now stated in [[sec:res:latency]].

**Comment 1.9.** The Python timings and the real-RIC measurement of [17] are not comparable.
**Response.** Agreed. The previous version drew a quantitative conclusion across hosts and implementations.
**Action.** We now time a compiled runtime (ONNX Runtime) on the same host. The cross-paper comparison is removed from the results and appears only in related work. [[N:LatOnnxOK]] of [[N:LatOnnxN]] exported models matched scikit-learn on at least [[N:LatOnnxAgreeMin]] of decisions and were timed.

**Comment 1.10.** Section VI-F described load, throughput and container measurements that were never made.
**Action.** The latency subsection was rewritten ([[sec:res:latency]]). It reports only the stages measured and states that indication decoding, control encoding and queueing were not measured.

**Comment 1.11.** Four different alert volumes for logistic regression without their context.
**Response.** They came from different layers, splits and experiments. The 19,551 and 5,620 per hour figures differ because the calibration experiment trains on 60% of the source groups, and logistic regression's target false positive rate moves from 0.023 to 0.081 between the two training sets.
**Action.** Every operating point now states its corpus, layer, threshold and estimator ([[tab:pooled]], [[tab:calibration]]). The calibration experiment's split is stated in [[sec:setup]].

**Comment 1.12.** Inconsistent model names and a citation of LightGBM for scikit-learn's histogram gradient boosting.
**Action.** One scheme (LR, DT, RF, XGB, HGB, MLP) is used in text, tables and figures, and defined in [[tab:symbols]]. HGB now cites scikit-learn, and the LightGBM entry is removed.

**Comment 1.13.** Spelling and terminology.
**Action.** The manuscript uses American spelling throughout. "Operational precision" is the single term for Eq. (4).

---

## Reviewer 2

**Comment 2.1.** The claim that the MLP falls beneath the floor is stated too strongly.
**Response.** The reviewer was right, for a reason we had not seen. The MLP was trained without the class weighting every other model received (Reviewer 3, comment 5). With that weighting it scores [[N:TrMLPtgtFone]] macro-F1 on 5G-NIDD, well above the stratified baseline's [[N:TrStratFloor]].
**Action.** The claim is withdrawn from the Abstract, Introduction, Results and Conclusion. [[sec:res:transfer]] reports each architecture against the floor with corrected intervals, and against chance in balanced accuracy.

**Comment 2.2.** "Stratified coin flip" is misleading.
**Action.** The term is gone. [[sec:res:transfer]] reports the stratified baseline ([[N:TrStratFloor]]) and a fair coin ([[N:TrFairCoin]]) on the target, explains why a macro-F1 floor depends on the prior it samples, and moves the headline to balanced accuracy and ROC-AUC, for which chance is 0.5.

**Comment 2.3.** The rank-correlation claim rests on one model.
**Response.** Agreed, and with the corrected MLP the correlation in macro-F1 is [[N:RhoFone]] (p = [[N:RhoFoneP]]), while in balanced accuracy it is [[N:RhoBA]] (p = [[N:RhoBAP]]).
**Action.** The claim is withdrawn. [[sec:res:transfer]] reports both values and states that six architectures cannot settle the question. The Abstract no longer mentions rank correlation.

**Comment 2.4.** The memorization mechanism is asserted rather than shown.
**Response.** We agree that feature-blind baselines cannot distinguish memorization from a harder task. We ran the control the reviewer's argument calls for (EXP-042).
**Action.** A category-stratified run-disjoint protocol holds out whole capture runs while keeping every attack category in training. The random-split gain persists under it ([[N:LeakStratMin]] to [[N:LeakStratMax]]). In none of the 20 run-disjoint splits was a test category absent from training. A model-free probe shows that under a random split [[N:NNSame]]% of test windows have their nearest training window in the same capture session, and a one-nearest-neighbor lookup gains [[N:NNGain]] macro-F1 from the random split ([[sec:res:protocol]], [[tab:leakage]], [[fig:leakage]]). The text now presents memorization as the explanation these controls support, and states the remaining confound between session and scenario in [[sec:limitations]].

**Comment 2.5.** The calibration claim is too absolute.
**Response.** The reviewer was right, and the data show it directly. Isotonic regression changed ROC-AUC by up to [[N:CalIsoMax]], and Platt scaling inverted the decision tree's ranking in [[N:CalPlattFlipSeeds]] of [[N:CalSeeds]] seeds. Only temperature scaling preserved order everywhere, to within [[N:CalTempMax]].
**Action.** [[sec:res:calibration]] and [[tab:calibration]] report the change in ROC-AUC for each calibrator and model. The Abstract states the narrower claim.

**Comment 2.6.** Fixing B = 10 ms contradicts the argument that the budget is an authoring choice.
**Action.** The phrase "not ours to choose" is gone. The deployability test reports the smallest budget met rather than a verdict at one budget ([[sec:disc:predicate]], [[tab:predicate]]), and the violation rate ε is stated beside B in [[sec:criteria]].

**Comment 2.7.** The extraction claim in the Abstract is overstated.
**Action.** The Abstract no longer makes a latency claim beyond what [[sec:res:latency]] measures. The speed-up of the vectorized exporter is re-measured on the real captures, at [[N:LatExtrSpeedMin]] to [[N:LatExtrSpeedMax]] times, and stated as a range. The earlier figure came from synthetic captures. Re-checking it on real ones exposed a defect: the vectorized exporter did not apply the 120 s active timeout, so long floods came out as fewer, longer records than the reference produces. We fixed it, added a regression test, and re-ran the benchmark. On [[N:LatEqCaptures]] captures compared record by record, the two exporters now agree exactly in packets and bytes on all [[N:LatEqKeys]] shared IPv4 flow keys. The reference also emits a few IPv6 link-local flows, which the vectorized exporter does not parse.

**Comment 2.8.** Terminology for the split, the unit, the alert and precision.
**Action.** [[sec:method]] defines the four protocols and their group keys. [[sec:criteria]] defines the unit of each detector (flow records, or 16 s windows of one UE, 225 per UE-hour), defines an alert as a false alert in Eq. (3), and uses "operational precision" for Eq. (4) throughout.

**Comment 2.9.** Conversational phrasing and drafting history.
**Action.** The manuscript was rewritten in a formal register. Every expression the reviewer listed is gone, and so is every reference to earlier versions of the work.

**Comment 2.10.** "Previously published" findings and a pre-registration without a record.
**Response.** The two findings had appeared in internal project reports, not in a publication. The pre-registration was a claim register kept in the project repository.
**Action.** Both statements are removed, with the section on the withdrawn ablation. The limitation it recorded now appears in [[sec:limitations]] with a citation to the work that performs that fusion from the raw archives.

**Comment 2.11.** Evaluation-bias and label-shift literature.
**Action.** TESSERACT and Kapoor and Narayanan are discussed in [[sec:related]]. We implemented both label-shift estimators the reviewer names (EXP-044). Against a true target prior of [[N:PriorTrue]], their mean estimates per architecture range from [[N:PriorMeanMin]] to [[N:PriorMeanMax]], and [[N:PriorFracExtreme]]% of the individual estimates fall below 0.05 or above 0.95. Both assume that only the class balance changes, which does not hold here ([[sec:res:calibration]]).

---

## Reviewer 3

**Comment 3.1.** Why was 5G-NIDD not re-extracted with Zeek?
**Response.** Our copy of 5G-NIDD contains the published Argus flow records only, and no Zeek installation was available on the measurement host. We could not run this control, and we say so in [[sec:limitations]]. We ran two measurements that bound what the exporter can explain (EXP-045).
**Action.** A domain classifier separates the corpora at [[N:DomShared]] balanced accuracy on the 18 shared columns and at [[N:DomRobust]] on nine columns that are invariant to where a flow is cut. The largest shifts are in protocol mix and direction ratios, which a common exporter would not change. Transfer on the robust subset is reported in [[tab:arms]]. [[sec:res:anatomy]] concludes that the corpora differ in traffic composition as well as in tooling, and that a common exporter would not by itself make them comparable.

**Comment 3.2.** How much of the gap is prior shift?
**Response.** In macro-F1, all of it: the majority baseline loses [[N:TrMajDrop]], and the detectors' losses minus that loss are [[N:TrDiDmin]] to [[N:TrDiDmax]].
**Action.** [[tab:transfer]] adds balanced accuracy, ROC-AUC and the difference against the majority baseline. In balanced accuracy the detectors lose [[N:TrBAdropMin]] to [[N:TrBAdropMax]], significant for [[N:TrSigBA]] of six after correction, while both baselines stay at 0.5.

**Comment 3.3.** How would flow features reach a Near-RT RIC?
**Action.** [[sec:criteria]] and [[sec:disc:practice]] now state that E2 does not carry packets. A flow-level detector needs an exporter at the user plane and a transport to the xApp, whose cost adds to t_ind, which we did not measure. Fig. 1 was redrawn to show this path.

**Comment 3.4.** How are per-window rates turned into alerts per flow-hour?
**Response.** They should not have been. The previous version multiplied a per-window rate by a flow rate.
**Action.** Radio-layer rates are now per 16 s window of one UE, and volumes are per benign UE-hour. Flow-layer volumes are per hour at a declared flow rate and per 10^6 benign flows ([[sec:criteria]], [[tab:pooled]]).

**Comment 3.5.** How was the MLP weighted?
**Response.** It was not, and this was a defect. scikit-learn's MLPClassifier has no class-weight option, and the code never passed sample weights.
**Action.** The MLP now receives balanced sample weights, and a unit test fails if the weights are absent. Every experiment that reports the MLP was re-run (EXP-041 to EXP-051). The consequences are reported in our replies to comments 2.1 and 2.3.

**Comment 3.6.** Why were the decision tree and the stratified baseline missing from the alert tables?
**Action.** EXP-046 re-runs the radio alert burden for all eight models, and [[tab:pooled]] includes them.

**Comment 3.7.** How was λ_b chosen?
**Response.** It is a declared parameter, not a measurement.
**Action.** [[sec:criteria]] says so, alert volume is also reported per 10^6 benign flows (independent of λ_b), and precision is shown not to depend on λ_b.

**Comment 3.8.** Calibration under shift and shift detection.
**Action.** Ovadia et al. and Rabanser et al. are discussed in [[sec:related]]. [[sec:disc:practice]] proposes unlabeled shift detection for monitoring after admission, and notes that on these corpora it would fire at once.

---

## Reviewer 4

**Paragraph 1: controls for the transfer result.**
**Response.** We ran three of the four requests. A single-exporter re-extraction was not possible (see our reply to comment 3.1), and no third independently collected O-RAN corpus with paired radio telemetry was available to us. Both are stated as limitations.
**Action.** (a) The harmonization loss is measured (EXP-047): the full 46 Zeek features give between [[N:HarmBAmin]] and [[N:HarmBAmax]] more in-distribution balanced accuracy than the 18 shared columns ([[tab:harm]]). The source detectors are not weak in balanced accuracy ([[N:TrSrcBAmin]] to [[N:TrSrcBAmax]]); their low macro-F1 reflects the 94.6% attack prevalence. (b) The exporter-robust subset is evaluated ([[tab:arms]]). (c) False positive and false negative rates with corrected intervals are in the statistics files and summarized in [[tab:pooled]]. (d) The reverse direction has its own table ([[tab:transfer_rev]]).

**Paragraph 2: runtime.**
**Response.** A RIC deployment remained blocked on the measurement host, which lacks the virtualization support Docker and WSL need. We ran the fallback the reviewer proposed.
**Action.** The models were exported to ONNX and timed with ONNX Runtime on the same host (EXP-043), beside scikit-learn on arrays and on DataFrames. The radio decision path, window aggregation plus ONNX inference, has a 99th-percentile upper bound of at most [[N:LatEtoEPnnHiMax]] ms across the models timed. The vectorized flow exporter costs [[N:LatExtrMin]] to [[N:LatExtrMax]] ms per flow on the real captures. [[tab:latency]] reports every stage.

**Paragraph 3: wider model panel.**
**Action.** Three families were added. Sequence models (a GRU and a 1D-CNN over raw KPM sequences, EXP-050) show the same random-split inflation ([[tab:sequence]]). Two benign-only novelty detectors (isolation forest, autoencoder, EXP-048) fail already in distribution, with source balanced accuracy near 0.5, because floods and scans resemble short benign flows in this feature space. CORAL adaptation (EXP-049), which reads unlabeled target features, is reported in [[tab:arms]].

**Paragraph 4: discussion of O-RAN practice.**
**Action.** The new [[sec:disc:practice]] covers the data path, detection delay (window length and flow timeouts), acting on alerts through E2SM-RC or A1, and admission and monitoring with the deployability test.

**Paragraph 5: the time-disjoint results were missing.**
**Action.** They are now [[sec:res:drift]] and [[tab:drift]], re-run with the corrected MLP (EXP-051). The time-disjoint split costs [[N:DriftFwd]] against a matched random-session control. [[N:DriftOutFwd]] of [[N:DriftN]] configurations fall outside the control's range, and false alerts rise by a factor of [[N:DriftFAratio]].

---

## Reviewer 5

**I1 (section introductions).** Each section now opens with a short paragraph describing its subsections.
**I10 (symbols table).** Added as [[tab:symbols]]. ρ in Eq. (8) and δ_m in Algorithm 1 are defined, and ρ is no longer reused for rank correlation.
**I17 (hardware).** Stated in [[sec:setup]] (see comment 1.7).
**I20 (datasets).** D_A is named and cited (NetsLab-5GORAN-IDD), and the radio layer has its own column in [[tab:corpora]].
**I25 (recent references).** Fourteen references were added, among them recent O-RAN detection work (Det-RAN, the cross-layer study on the same corpus) and the evaluation, calibration and shift literature used in the analysis.
**I29 (arXiv references).** Two were replaced by their published versions (Niknam et al., Globecom Workshops 2022, and Layeghy and Portmann, Computers and Electrical Engineering 2023). Obiuwevwi et al. has no published version yet and is cited as a preprint.
**I33 (uncited floats).** Every float is cited, and the duplicates are removed.
**I35 (font size).** The data figures are regenerated at print size with 7.5 to 8 pt text and no embedded titles. The small labels in the two schematics were enlarged where space allows.
**I37 (abstract).** One paragraph of [[N:AbstractWords]] words.
**I40 (template).** See comment 1.6.

---

## Reviewer 6

**Comment 6.1.** The central experiment cannot isolate deployment shift.
**Response.** Agreed. We no longer describe the gap as deployment shift.
**Action.** [[sec:res:anatomy]] measures what the gap is made of. Prior shift explains the macro-F1 gap but not the balanced-accuracy gap. The corpora are separable at [[N:DomShared]], and at [[N:DomRobust]] on exporter-robust features, so traffic composition differs as well as tooling. [[sec:limitations]] states that a common exporter was not applied and that two corpora cannot describe the space of deployments.

**Comment 6.2.** The alert tables are arithmetically impossible.
**Response.** The reviewer's arithmetic is correct. Both tables averaged precision over folds.
**Action.** Rebuilt from pooled counts (EXP-046, EXP-041) as [[tab:pooled]]. With recall held above 10%, no detector reaches an operational precision of 0.05 on the radio layer (best [[N:RadPPVbest]]) or on 5G-NIDD (best [[N:NetTgtPPVbest]]).

**Comment 6.3.** A retracted result is reported in the same manuscript.
**Action.** The fold-averaged spread, the "calibration failure" sentence and the figure built on fold averages are removed. [[tab:estimator]] now shows the three estimators side by side: [[N:EstPooled]]× pooled, [[N:EstMedian]]× as a median and [[N:EstMean]]× as a mean over folds.

**Comment 6.4.** Two figures have no traceable data.
**Response.** Correct. Both were typed by hand.
**Action.** Both are replaced: the reliability diagram by [[fig:reliability]] (pooled equal-mass bins from EXP-041) and the threshold sweep by [[fig:threshold]] (pooled counts).

**Comment 6.5.** The degradation is confounded with prior shift.
**Action.** See our reply to comment 3.2. The difference-in-differences column of [[tab:transfer]] shows the confound in macro-F1, and balanced accuracy removes it.

**Comment 6.6.** The deployability verdict contradicts the table.
**Response.** Correct. Logistic regression passed the generalization bound in the previous version's own table, and the alert term could be satisfied by never alerting.
**Action.** Eq. (7) now requires a minimum recall, evaluates the alert term on the target, and applies the generalization bound to the upper confidence bound. [[tab:predicate]] evaluates all six architectures. None passes, each fails both the generalization and the alert terms, and the verdict holds for any bound less strict than the data by margins stated in [[sec:disc:predicate]].

**Comment 6.7.** Small benign sample and wrong unit.
**Action.** Units are corrected (see comment 3.4). The radio operating points pool [[N:RadNbenign]] benign windows and carry Wilson intervals, and Table [[tab:pooled]] marks the recall floor used for reachability.

**Comment 6.8.** The latency table omits the dominant stage and has no quantile uncertainty.
**Action.** [[tab:latency]] reports feature construction and inference separately for three implementations, the radio path end to end, and the flow exporter per flow. Every quantile carries a distribution-free 95% interval from 20,000 calls. The claim that the median misleads is removed.

**Comment 6.9.** The paired t-test is anti-conservative.
**Response.** Agreed.
**Action.** Nadeau-Bengio corrected intervals are primary throughout ([[sec:method]]). The consequences are reported, not hidden. Averaged over architectures, the random-split gain is [[N:LeakAvg]] with a corrected interval of [[N:LeakAvgNbLo]] to [[N:LeakAvgNbHi]], so no single architecture's gain is significant after Holm correction. The transfer loss in balanced accuracy remains significant ([[N:TrBAdropAvg]], [[N:TrBAdropAvgNbLo]] to [[N:TrBAdropAvgNbHi]]).

**Comment 6.10.** The survey cannot be checked.
**Response.** The survey had not been carried out, and the counts should not have been in the manuscript.
**Action.** The table and its protocol paragraph are deleted. [[sec:discussion]] no longer makes a claim about reporting practice in the literature.

**Comment 6.11.** Informal phrasing and drafting history.
**Action.** See comment 2.9.

---

## Reviewer 7

- **Novelty.** The Introduction now states what is not new (the base-rate argument, the closed-world critique, transfer between these corpora, real-RIC inference) and what is: a controlled evaluation in which these effects are measured together with baselines on every corpus.
- **D_A unnamed.** Named and cited, with the testbed correctly described.
- **Radio layer undescribed.** [[tab:corpora]] and [[sec:method]].
- **Time-disjoint rung without results.** [[sec:res:drift]].
- **Fig. 1 arrows and actions.** Radio telemetry no longer enters the harmonized flow space, flow features come from a user-plane exporter, and the actions are marked as options not evaluated.
- **Fig. 2 microsecond ranges.** Fig. 2 no longer quotes the external measurement. Its annotations come from this study's generated results.
- **Eq. (2) promised and not computed.** Corrected (source-fitted quantile transform, since per-corpus normalization makes every term zero) and reported in [[sec:res:anatomy]].
- **Algorithm 1.** Every indication's latency is recorded, both deadline checks count a violation, and the text states that the algorithm was not deployed.
- **Reverse direction and category counts.** [[tab:transfer_rev]] and [[tab:percat]]. The text no longer claims "four more" categories or that DDoS is present in D_B.
- **"Factor of 23" and the 0.149 claim.** Both sentences are removed.
- **Repository and Section IX.** The repository URL is given, and the section lists only artifacts that exist.
- **Withdrawn ablation and "Fard et al."** The section is removed, and Fard et al. is cited where the limitation is stated.
