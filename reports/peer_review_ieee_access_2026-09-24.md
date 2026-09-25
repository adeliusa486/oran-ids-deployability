# Simulated IEEE Access decision letter

> **Simulated pre-submission review.** Produced with the peer-review skill on 24 September 2026 from `paper/main.tex` and the compiled `paper/main.pdf` at commit 72269b8. No editor or reviewer has seen this paper, and this is not an IEEE document. Section, table, figure, equation and reference numbers follow the compiled PDF. After the letter, Appendix A holds the editor's worksheet, Appendix B a revision plan, and Appendix C notes drawn from the repository that real reviewers would not see.

**Decision letter (Initial Submission)**

**Intrusion Detection for IoT Traffic in O-RAN Edge Data Centres: Why Accuracy Alone Is Not Enough**

| | |
|---|---|
| Subject | IEEE Access - Decision on Manuscript ID Access-2026-XXXXX (simulated) |
| Date sent | 24 September 2026 |
| From | Associate Editor, IEEE Access (simulated) |
| To | Corresponding author |

24-Sep-2026

Dear Mr. Ahmad:

I am writing about manuscript Access-2026-XXXXX, "Intrusion Detection for IoT Traffic in O-RAN Edge Data Centres: Why Accuracy Alone Is Not Enough", which you submitted to IEEE Access.

Seven reviewers read your article with interest, but they do not recommend it for publication in its current form. We encourage you to address their concerns, which appear at the end of this letter, and to resubmit the updated article to IEEE Access.

IEEE Access runs a binary peer review process. To keep quality at IEEE standards, an article that needs changes of any size, including minor edits, is rejected rather than accepted subject to revision.

When you update the manuscript, support each change with references, examples or data. If you disagree with a technical point a reviewer has made, give your counterargument in the response to reviewers and work it into the updated manuscript.

Some reviewers suggest references. Add only those that are relevant and that strengthen your article. You are not obliged to cite suggested work, and the decision will not depend on whether you do.

IEEE Access allows one resubmission. If the updated manuscript does not address all of the reviewers' concerns, or if the Associate Editor still has substantial technical concerns, the article will be rejected with no further opportunity to resubmit.

When you resubmit, you will be asked to upload three files:

1. A response to reviewers that gives, for each comment, (a) the reviewer's concern, (b) your response, and (c) the action you took in the manuscript.
2. The updated manuscript with every change highlighted, including grammatical changes.
3. A clean copy of the final manuscript as LaTeX or Word source and as a PDF.

Please contact me if you have any questions.

Sincerely,

Associate Editor (simulated)
IEEE Access

---

## Reviewers' Comments to Author

### Reviewer: 1

**Comments:**

The manuscript asks a relevant question for O-RAN security: how much of the accuracy reported for intrusion detection xApps survives evaluation protocols that sit closer to deployment. Several design choices deserve credit. The trivial baselines are evaluated on the target corpus as well as the source, the splits are group-disjoint with a guard against overlap, intervals are paired over split seeds with Holm correction, and the target corpus is quarantined behind an access log. The Zeek/Argus byte-count mapping in Section IV-B (src_ip_bytes rather than src_bytes) is a concrete finding that other groups can reuse. The paper is also candid about what it did not measure. The comments below concern presentation errors and internal inconsistencies that should be fixed before the technical content can be judged as final.

1. Markdown syntax appears in the compiled PDF. Section VI-B prints `**all six**` and Section VI-C prints `**Threshold saturation is therefore not a calibration failure but a discriminability limit.**` with the asterisks visible. Please use `\textbf{}` or plain text.

2. The indicator function in Eq. (7) renders as the wrong symbol (it prints as ⊮). The `\mathbb` command from amssymb supports capital letters only, so `\mathbb{1}` does not produce a blackboard-bold one. Please load bbm or dsfont, or write `\mathbf{1}`.

3. Section VII ("Measured Results") duplicates Section VI. Table VIII repeats Table IV value for value, Table XI repeats Table VII, and Fig. 9 is the same image as Fig. 6. The two sections also disagree on substance (see comment 10 and the comments of Reviewer 6). Please merge them into one results section with one copy of each table and figure.

4. Fig. 3 and Fig. 4 are never cited in the text. Please cite each figure where it is discussed.

5. The caption of Table VII contains an internal identifier, "(D-007)". References [16] and [17] contain what look like project notes inside the bibliographic entries ("Closes gap G1", "Closes gap G5", and summaries of each paper's findings). Please remove them.

6. Please remove the "Pre-submission status" box from page 1 and complete the author block, which still reads "First A. Author, Second B. Author, and Third C. Author ... Institution Name". The manuscript is also set in the IEEEtran conference layout. Please move it to the IEEE Access template, which requires author biographies.

7. Please describe the hardware behind every timing result. Section V states only "an Intel Core i-series host running Windows". Give the CPU model, core count, RAM, operating system build, power plan and the thread settings of each library. If the random forest and XGBoost were timed with multithreaded prediction enabled, every single-row call pays thread-pool start-up costs, which may explain part of the 93.41 ms median for the random forest in Table VII.

8. Please state how many trained models were timed. Table VII gives one row per architecture, while the accuracy results average 20 split seeds. If the timings come from one model per architecture, say so.

9. The paper compares its Python timings on a Windows workstation with measurements that [17] took inside a real Near-RT RIC, on different hardware and in a compiled implementation. Please state that the two sets of numbers are not directly comparable, and do not draw a quantitative conclusion such as "three orders of magnitude" (Sections V, VIII-B and X) without a same-host measurement.

10. Section VI-F opens by saying that Table VII reports "the latency decomposition of (5) at an offered load of 1,000 decisions per second, together with sustainable throughput under the p99 constraint of (6) and container resource consumption", and that Fig. 6 "shows how the 99th percentile grows with load". Table VII contains none of these quantities, Fig. 6 shows one p99 value per architecture, and Section V states that no offered-load sweep was run and nothing was containerised. The subsection title, "Latency and Resource Footprint", has the same problem. Please rewrite the paragraph and the title to describe what was measured.

11. Please state the corpus, layer, threshold, number of seeds and estimator behind each operational figure. For logistic regression alone the paper reports 5,620 false alerts per hour on D_B (Section VI-E), 19,551 raw alerts per hour in the prior-correction test (Section VI-C), 35,330 on the source (Section VI-C) and 52,638 on the radio layer (Table IX). Its raw operational precision on D_B is 0.0232 in Section VI-E and 0.0221 in Section VI-C. Some of these values come from different experiments, but the text does not say which.

12. Model names change between text and graphics. The text writes "logistic regression", "random forest" and "histogram gradient boosting", while Tables IV to XI and Figs. 3 and 6 to 8 use code identifiers (logreg, rf, hgb, xgboost, tree, mlp). Please adopt one scheme. Section IV-C also cites LightGBM [40] as the second boosting implementation, but Table III lists scikit-learn's histogram gradient boosting. Please cite the library you ran.

13. Please proofread for consistency before resubmission. IEEE style uses American spelling, and the manuscript uses British forms throughout (centres, generalisation, optimisation, harmonisation). One quantity also appears under four names: "operational precision", "deployment precision", "operational PPV" and "pooled deployment precision".

**Additional Questions:**

Please confirm that you have reviewed all relevant files, including supplementary files and any author response files, which can be found in the "View Author's Response" link above (author responses will only appear for resubmissions): Yes, all files have been reviewed

1) Does the paper contribute to the body of knowledge?: Yes. The paper gives a measured account of how the evaluation protocol changes the reported performance of O-RAN intrusion detectors, and it evaluates trivial floors on the target corpus, which few papers in this area do.

2) Is the paper technically sound?: Yes, with corrections. The design is sound, but several tables, figures and paragraphs disagree with one another (comments 3, 10 and 11).

3) Is the subject matter presented in a comprehensive manner?: Yes. The criteria, pipeline and results are explained in detail. The duplicated Section VII makes the results harder to follow than necessary.

4) Are the references provided applicable and sufficient?: Yes, mostly. Three references are arXiv preprints and two carry internal notes (comment 5).

5) Are there references that are not appropriate for the topic being discussed?: No

5a) If yes, then please indicate which references should be removed.:

---

### Reviewer: 2

**Comments:**

1. The MLP result is stated more strongly than the evidence allows. The Abstract, the contribution list, Section VI-B and Section XI say that the MLP falls "beneath" the trivial floor, is "on the wrong side of chance" and "does worse than guessing". Table V gives a target macro-F1 of 0.422 against 0.424 for the stratified baseline (0.4223 against 0.4240 in the text), a difference of 0.0017, and the text reports a balanced accuracy of 0.4966. No test against the floor or against 0.5 is reported. Table V also gives the MLP a target PR-AUC of 0.663 against a chance level of 0.607, so the MLP ranks target flows better than chance and fails at the fixed threshold τ = 0.5 after a large prior shift. The supportable statement is that, at τ = 0.5, the MLP is statistically indistinguishable from the trivial floor. The paired design allows a direct test of the MLP against the floor, and the manuscript should report it.

2. The phrase "stratified coin flip" is misleading. The stratified baseline samples the training prior of 94.63% attack, so it behaves as a biased coin with p = 0.9463. On a target with 60.71% attack prevalence, a fair coin would score about 0.49 macro-F1, above the stratified baseline's 0.424. The floor's value depends on which prior it samples, so it is not a neutral reference. Please describe it accurately and report prior-independent references beside it, such as balanced accuracy and ROC-AUC, for which chance is 0.5.

3. The rank-correlation claim rests on one model. Section VI-B reports Spearman ρ = 0.143 (p = 0.787) across six architectures and concludes that a practitioner "has close to no information" about transfer from the in-distribution score. With n = 6 the test has little power, so a non-significant result is weak evidence of no association. Table V also shows that the other five models keep the same order on source and target (random forest, histogram gradient boosting, XGBoost, logistic regression, decision tree in both columns). The low ρ comes entirely from the MLP moving from first place to last. Please restate the finding as "the source-best model ranked last on the target" and remove "close to no information". The Abstract says "across the eight" and the contribution list says "across eight architectures", while the body computes the statistic across six.

4. The memorisation mechanism is asserted rather than shown. Sections VI-A and VII-A state that the trivial baselines' null gain "identifies the mechanism" as memorisation rather than a change in task difficulty. A classifier that ignores its inputs is insensitive to every feature-level change, whether memorisation or a harder task, so its null result cannot tell the two apart. Section X adds that radio capture sessions align perfectly with attack category (purity 1.000), so a run-disjoint test fold holds out whole attack scenarios, and the drop may reflect generalisation to scenarios the model has not seen. The stratified baseline also changes significantly between protocols (−0.009*, Table IV), which shows that the two protocols produce test folds with different label composition. Please present memorisation as one explanation consistent with the data, discuss the alternative, and use wording such as "is consistent with" or "suggests".

5. The calibration claim is too absolute. The Abstract states that "every standard calibration method is a monotone transform and therefore cannot change the achievable operating points at all". This holds for strictly increasing maps such as Platt scaling, temperature scaling and the prior correction of Eq. (10). Isotonic regression is non-decreasing and piecewise constant. It merges scores into ties, and on its fitting data the pool-adjacent-violators solution produces the ROC convex hull (Fawcett and Niculescu-Mizil, Machine Learning 68(1), 2007). It can change the ROC. The paper also checks ROC-AUC preservation only for Platt and temperature scaling, and only "for five of six architectures", without saying what happened with the sixth. Please narrow the claim, report the sixth case, and include isotonic regression in the check.

6. Section VIII-B contradicts the paper's own argument about the latency budget. Sections VI-F and VII-C argue that fixing one budget inside the 10 ms to 1 s range "converts an authoring choice into an apparent measurement". Section VIII-B then fixes B = 10 ms and says that it "follows from the specification ... and is not ours to choose". Both positions cannot hold. Please apply the predicate across the swept budgets, or present 10 ms as a stated design choice. The same concern applies to ε = 0.01 in Eq. (6). Table VII shows that at p99.9, logistic regression (13.43 ms), XGBoost (11.39 ms) and the MLP (13.98 ms) all exceed 10 ms, so the verdict also depends on ε.

7. The extraction claim in the Abstract is overstated. The Abstract says feature extraction "remains dominant after an order-of-magnitude optimisation of the extractor". Section VI-F reports speed-ups of 2.3 to 12.1 times, and a best-case extraction cost of 0.058 ms per flow, which is lower than the paper's own inference measurements of 0.18 to 0.96 ms. Extraction stays dominant only when the optimised Python extractor is set against 1 to 5 µs of inference that other authors measured in a compiled implementation inside a real RIC [17], and the paper warns elsewhere against comparing measurement classes. Section VII-C also states that the relation inverts for the random forest and histogram gradient boosting. Please restate the claim for like-for-like implementations and keep the architecture dependence visible in the Abstract.

8. Several terms change meaning across the paper, and several quantities carry more than one name. Please define each of the following once and hold it fixed in the Abstract, Sections III to VIII and the captions.
   - The split. "Run-disjoint" (Tables IV and VIII), "group-disjoint" (Section V, Fig. 2 and the legend of Fig. 7) and "device-level partition" (Section IX) are not the same thing, and Section V states that device-disjoint splitting is not supportable on this corpus.
   - The unit of classification. Radio-layer results count KPM windows ("a median of 136 benign windows", Section VI-E), while Eq. (3), Table IX and Table X express alerts per flow.
   - The alert. Eq. (3) counts false alerts only, while Tables IX and X count all alerts. The majority row of Table IX lists 240,481 alerts per hour, the total flow count including attacks.
   - The precision. "Operational precision", "deployment precision", "operational PPV" and "pooled deployment precision" appear to denote one quantity.

9. The manuscript contains conversational and rhetorical expressions that do not suit an IEEE Access research article. Examples include "survive contact with a production network" (Section I), "is the first thing a reviewer should attack" (Section IV-C), "The floors are not decoration" (Section IV-C), "reportable rather than embarrassing" (Section VI-D), "on the wrong side of chance" (Section VI-B), "an alert generator that an operator will switch off within a shift" (Section VI-E), "which upper-bounds nothing on its own" (Section III-B) and "the strongest evidence for it is that the argument applies to us" (Section XI). The paper also narrates its own drafting history: "an earlier version of this protocol specified", "in an earlier version of this work it reported four significant effects", "An earlier version of this work reported the mean", "carried forward through three phases". A journal article should report the final method and results. Earlier versions belong in a response letter, or in a cited erratum if they were published.

10. Two statements cannot be verified. Section XI says that "Two findings we previously published did not survive re-examination", but no earlier publication is cited. Section VI-D says that the ablation claim "was registered in advance with a falsification condition", but no registry, date or identifier is given. Please cite the publication and the pre-registration record, or remove both statements.

11. Please consider the evaluation-methodology literature closest to this work. Pendlebury et al., "TESSERACT: Eliminating experimental bias in malware classification across space and time," USENIX Security 2019, formalises spatial and temporal bias in security machine learning and is close in spirit to the protocol ladder. Kapoor and Narayanan, "Leakage and the reproducibility crisis in machine-learning-based science," Patterns, 2023, catalogues leakage types relevant to Section VI-A. For the prior shift in Section VI-C, Saerens et al. (Neural Computation, 2002) and Lipton et al. (ICML 2018) estimate the target prior from unlabelled target data, so the correction in Eq. (10) does not need an oracle. The statement that a deployment "does not know" the target prior should be revised in light of this work.

**Additional Questions:**

Please confirm that you have reviewed all relevant files, including supplementary files and any author response files, which can be found in the "View Author's Response" link above (author responses will only appear for resubmissions): Yes, all files have been reviewed

1) Does the paper contribute to the body of knowledge?: Yes

2) Is the paper technically sound?: Yes, provided the claims listed above are corrected.

3) Is the subject matter presented in a comprehensive manner?: Yes

4) Are the references provided applicable and sufficient?: Mostly. Standard references on evaluation bias and label-shift estimation are missing (comment 11).

5) Are there references that are not appropriate for the topic being discussed?: No

5a) If yes, then please indicate which references should be removed.:

---

### Reviewer: 3

**Comments:**

1. The transfer experiment changes the exporter as well as the deployment (Zeek for D_A, Argus for D_B), and [16] reports that a classifier identifies the source corpus with 0.993 balanced accuracy on harmonised features. 5G-NIDD publishes packet captures as well as the Argus flow files. Why was D_B not re-extracted with Zeek, matching the version and settings of D_A as closely as its documentation allows? That step removes the exporter confound for the forward direction, and Section X gives only "cost grounds" for not taking it.

2. How much of each ΔF1 in Table V is label-prior shift rather than covariate shift? The majority-class baseline, which reads no features, loses 0.114 macro-F1 between source and target. Logistic regression (0.096), the decision tree (0.101) and histogram gradient boosting (0.111) lose less than that, and XGBoost loses the same amount. Does the conclusion that every non-trivial architecture degrades survive a prevalence-invariant metric such as balanced accuracy or ROC-AUC, or a difference-in-differences test against the floor?

3. How would packet-level flow features reach a Near-RT RIC? E2SM-KPM carries aggregated radio measurements, not packets. Which interface, service model or data path do you assume for the network-layer features that Section III-A describes ("E2SM-KPM indications and packet-level features"), and what does that path add to t_ind in Eq. (5)?

4. The radio layer, which supports Tables IV, VII, IX and X and Figs. 6 to 9, is measured in KPM windows, while λ_b is given in flows per hour. How is a per-window false positive rate turned into alerts per flow-hour in Eq. (3)? What is the window length, and how many benign windows support each alert estimate (Section VI-E mentions a median of 136 per fold)?

5. Scikit-learn's MLPClassifier has no class-weight option. How was the weighted objective of Eq. (9) applied to the MLP, given that Section IV-C and Table III state that every family receives "the same class-imbalance policy"? If the MLP was trained without weighting on a 94.63% attack prior, its false positive rate of 0.885 on D_B may follow from that choice rather than from any property of neural models.

6. Why is the decision tree missing from Table IX and Table X, and why does Fig. 8 show only three models? Section VI-E discusses six detectors, and Section VII-B refers to "all five detectors".

7. How was λ_b = 240,000 benign flows per hour (about 67 flows per second) established as "a modest regional edge site"? Section I describes an edge data centre that aggregates traffic from tens to hundreds of cells. Section V says the rate comes from a benign-only capture segment, while the caption of Table IX calls it a declared parameter that is not measured. Because alert volume scales linearly with λ_b, please also report false alerts per million benign flows, which does not depend on this choice.

8. AI/ML references that may be considered: Ovadia et al., "Can you trust your model's uncertainty? Evaluating predictive uncertainty under dataset shift," NeurIPS 2019, on calibration under shift (Section VI-C), and Rabanser et al., "Failing loudly: An empirical study of methods for detecting dataset shift," NeurIPS 2019. The second bears on the statement in Section VI-B that detectors "fail silently", since shift detection on unlabelled traffic is a standard safeguard.

**Additional Questions:**

Please confirm that you have reviewed all relevant files, including supplementary files and any author response files, which can be found in the "View Author's Response" link above (author responses will only appear for resubmissions): Yes, all files have been reviewed

1) Does the paper contribute to the body of knowledge?: Yes

2) Is the paper technically sound?: Yes

3) Is the subject matter presented in a comprehensive manner?: Yes

4) Are the references provided applicable and sufficient?: Yes

5) Are there references that are not appropriate for the topic being discussed?: No

5a) If yes, then please indicate which references should be removed.:

---

### Reviewer: 4

**Comments:**

The negative transfer result is interesting, but in its current design it cannot be attributed to deployment shift. The paper states that every ΔF1 is an upper bound spanning a change of deployment and a change of exporter, relies on [16] for evidence that the corpora are separable at 0.993 balanced accuracy, and concedes in Section X that two corpora are two points. Please add three things. First, a single-exporter control, at minimum by re-extracting 5G-NIDD from its published captures with Zeek. Second, a third independently collected 5G or O-RAN corpus, so that the gap and ranking claims rest on more than one ordered pair. Third, each model's in-distribution score on the full D_A feature set beside its score in the 18-column shared space, so readers can separate the loss caused by harmonisation from the loss caused by transfer. Table V gives source held-out macro-F1 of only 0.62 to 0.72 in the shared space, so the models are weak before transfer begins. Please report FPR and FNR with confidence intervals for both directions, and add a table for the reverse direction, which Section VI-B discusses without one.

The runtime evidence is emulated, and the latency conclusions lean on another group's measurement [17]. Please provide a proof of concept on an open Near-RT RIC, for example OpenAirInterface with FlexRIC as in [17], or the O-RAN Software Community RIC, driven by live or replayed E2 indications. Measure end-to-end detection latency, xApp CPU and memory, and the effect on E2 message handling as load increases. If a RIC deployment is not possible, time the ONNX exports that Section IX says are released, with ONNX Runtime or a compiled implementation on the same host. That experiment tests the claim in Section VI-F that the latency ranking reflects the toolchain rather than the architecture, without a cross-paper comparison. The conformance table also needs the feature extraction stage. Table VII excludes it, although Section VI-F calls it the dominant cost (a median of 6.90 ms and up to 37.34 ms per flow). Adding the median extraction cost to the p99 values in Table VII puts every architecture above 10 ms.

The detector panel leaves out the model classes most often proposed for O-RAN and IoT intrusion detection. Under the same splits, floors and protocol, please add an unsupervised anomaly detector (isolation forest [41] or an autoencoder), a sequence model over KPM windows (1D-CNN, LSTM or a small transformer), and at least one domain adaptation method such as CORAL, which [16] applied to these two corpora. At present the non-trivial panel consists of five tabular learners and one small MLP. The claim that "the evaluation protocol, not the architecture, dominates" needs a wider range of architectures before it carries weight.

Please add a dedicated discussion subsection on what the findings mean for O-RAN practice. It should cover four points. (a) Which data an xApp can obtain over E2, including E2SM-KPM granularity and reporting periods, compared with the packet-level features the experiments rely on. (b) How detection delay depends on the KPM reporting period and on flow timeouts as well as on compute latency, since a flow-level decision cannot precede the flow record. (c) How alerts would drive E2SM-RC control or Non-RT RIC policy over A1 without harming radio performance, and how false alerts would turn into wrongful mitigation of IoT devices. (d) How the predicate of Eq. (7) would serve for model admission and for ongoing monitoring, including drift detection on unlabelled traffic.

The time-disjoint rung appears in the Abstract (0.269 macro-F1, "nearly triples the alert burden", 52.96 days), in the contribution list and in Fig. 2 (−0.27 F1), but no section, table or figure in the body reports it. Please add the experiment in full, with the split definition, the sizes of the training and test periods, intervals, the control it is compared against and the alert-burden numbers, or remove it from the Abstract, the contributions and Fig. 2.

**Additional Questions:**

Please confirm that you have reviewed all relevant files, including supplementary files and any author response files, which can be found in the "View Author's Response" link above (author responses will only appear for resubmissions): Yes, all files have been reviewed

1) Does the paper contribute to the body of knowledge?: yes

2) Is the paper technically sound?: yes

3) Is the subject matter presented in a comprehensive manner?: yes

4) Are the references provided applicable and sufficient?: yes

5) Are there references that are not appropriate for the topic being discussed?: No

5a) If yes, then please indicate which references should be removed.:

---

### Reviewer: 5

**Comments:**

I1: Does the paper contain a brief introduction/summary at the beginning of each section/subsection, improving the "fluidity" of the text?
No. Please, write a brief introduction summarizing the content of the following subsections before the first subsection of Sections II, III, IV, VI, VII and VIII.

I10: Does the end of the Introduction contain a table summarizing the used symbols, notations, and acronyms?
No. The paper introduces more than fifteen symbols (ΔF1, W̄1, λ_b, π, π_tr, R(τ), τ, τ*, ρ, δ, δ_m, A_max, B, ε, q(1−ε), d_z) and many acronyms (RIC, E2SM-KPM, E2SM-RC, KPM, PPV, FPR, ECE, UE). Please add a table. Note also that ρ in Eq. (8) and δ_m in Algorithm 1 are never given values, and that ρ is reused for Spearman's coefficient in Section VI-B.

I17: Did the authors mention the hardware configuration and/or software, library, programming language, etc., used during the tests?
Partially. Software is listed (Python 3.11.9, scikit-learn 1.4, XGBoost 2.0). The hardware configuration is missing: "an Intel Core i-series host running Windows" identifies neither the CPU nor the memory nor the operating system version.

I20: Are the datasets identified, cited and described?
No. D_A is described as "an O-RAN testbed capture" but is never named or cited, and its licence is not stated. The radio layer behind Tables IV, VII, IX and X (number of windows, window length, KPM features, class balance) does not appear in Table I.

I25: Are the references recent?
More or less. Six of the 42 references date from 2024 or later. None of the O-RAN intrusion detection papers that Section I criticises and Table XII counts is cited individually.

I29: Is there any ArXiV or blog reference?
Please, replace the following arXiv reference(s) with its/their (respective) final published version(s) if possible: 3, 11 and 17.

I33: Are all the inserted figures, tables, and algorithms mentioned in the text?
No. Fig. 3 and Fig. 4 are not mentioned. Tables VIII and XI and Fig. 9 duplicate Tables IV and VII and Fig. 6.

I35: Is the font size of texts in figures (such as titles and names of axes in graphics) big enough to read?
No. Fig. 1 and Fig. 2 are scaled down to the text width, and many labels cannot be read in print, for example "message router · shared data layer · subscriptions" in Fig. 1 and the rung descriptions in Fig. 2. The legend of Fig. 5 overlaps the curves. Increase the font size in the graphics, if possible, please. Figs. 6, 7 and 8 also carry titles inside the image, and IEEE style places titles in the caption only.

I37: Does the abstract respect the journal's format?
No. The abstract has about 460 words in four paragraphs. IEEE Access asks for a single paragraph of 150 to 250 words.

I40: Is the manuscript prepared with the journal template?
No. It uses the IEEEtran conference layout. Please use the IEEE Access template.

**Additional Questions:**

Please confirm that you have reviewed all relevant files, including supplementary files and any author response files, which can be found in the "View Author's Response" link above (author responses will only appear for resubmissions): Yes, all files have been reviewed

1) Does the paper contribute to the body of knowledge?: Yes.

2) Is the paper technically sound?: Yes.

3) Is the subject matter presented in a comprehensive manner?: Yes. The language is clear and objective, although several results are repeated across Sections VI and VII.

4) Are the references provided applicable and sufficient?: Yes.

5) Are there references that are not appropriate for the topic being discussed?: No

5a) If yes, then please indicate which references should be removed.: I29: Is there any ArXiV or blog reference? Please, replace the following arXiv reference(s) with its/their (respective) final published version(s) if possible: 3, 11 and 17.

---

### Reviewer: 6

**Comments:**

1. The central experiment cannot isolate the effect the paper names. The two corpora differ in deployment, in exporter (Zeek against Argus), in flow definition (median flow duration differs by four orders of magnitude, Section X), in label taxonomy (five attack categories against two, Table I) and in class balance (94.63% against 60.71% attack). [16] shows that they are separable at 0.993 balanced accuracy. With one ordered pair of corpora, every transfer number describes this pair and these two tools. Phrases such as "cross-deployment generalisation" and "the accuracy an operator loses by reusing a published model" (Section III-B) are not supported until the exporter is controlled and further corpora are added.

2. Table X is arithmetically impossible under the paper's own parameters. At π = 0.002 and λ_b = 240,000 benign flows per hour, about 481 attack flows arrive per hour (the majority row of Table IX lists 240,481 alerts, the total flow count). An alert queue of 60,768 per hour can therefore contain at most 481 true positives, which caps precision at 0.0079. Table X reports an operational precision of 0.10 at that volume for the random forest, 0.25 at 53,632 alerts per hour for histogram gradient boosting (cap 0.009), and 0.50 at 8,855 alerts per hour for logistic regression, whose reported recall of 0.189 implies about 91 true positives and a precision near 0.010. Table IX has the same defect. An operational precision of 0.218 for XGBoost at 59,663 alerts per hour requires about 13,000 true positives per hour, 27 times the attack flows available. Eq. (4) applied to Table IX's own FPR and recall columns gives about 0.007 for every model. These tables appear to use the fold-mean estimator that the Abstract and Section VI-E describe as wrong.

3. The paper retracts a result and reports it in the same manuscript. Section XI states that "a reported sixfold spread in deployment precision between architectures was an artefact of averaging", and Section VI-E states that the detectors are "indistinguishable" with a pooled spread of 1.40. Section VII-B, Table IX and Fig. 8 present the sixfold spread (0.036 to 0.218) as a finding and conclude that "the metric an operator lives with separates them sharply". Section VII-B also calls threshold saturation "a calibration failure", which Section VI-C and the Abstract deny. Fig. 8 plots an operational precision near 0.2 for XGBoost at π = 0.0001. Eq. (4) with Table IX's FPR of 0.247 gives about 0.0004 at that prevalence, and Section VI-E reports a collapse factor of 2,631 there.

4. Two figures have no traceable data. Fig. 5 shows XGBoost "in distribution" with 682 alerts per hour and 41.2% operational precision at τ = 0.5, rising to 88.3% at τ = 0.99. The figure does not state its layer. Table IX gives 59,663 alerts per hour for XGBoost at τ = 0.5 on the radio layer, and Table X states that a precision of 0.5 is unreachable for XGBoost at any threshold. The values in Fig. 5 also imply a benign rate of about 141,000 flows per hour, not the declared 240,000. Fig. 4 reports an ECE of 0.021 in distribution and 0.187 under transfer for XGBoost, both outside the ranges in Section VI-C (0.028 to 0.185, and 0.251 to 0.396), and its ten points sit at equal-width bin centres although Section VI-C states that ECE uses fifteen equal-mass bins. The box on page 1 states that every number is measured and generated from a table. Please give the provenance of Figs. 4 and 5 or remove them.

5. The degradation in Table V is confounded with prior shift. The majority-class baseline, which reads no features, loses 0.114 macro-F1 from source to target. Logistic regression (0.096), the decision tree (0.101) and histogram gradient boosting (0.111) lose less, and XGBoost loses the same 0.114. The paired t-tests in Section VI-B compare each model's source and target scores, not each model's drop against the floor's drop. "All six non-trivial architectures degrade significantly" is therefore a statement about label shift and covariate shift together, and for four of the six models the table shows no degradation beyond what the prior shift alone produces.

6. The deployability verdict contradicts Table V. Section VIII-B sets δ = 10 points of F1 and states that the decision tree and logistic regression "fail the generalisation and alert terms". Table V gives logistic regression ΔF1 = 0.096, which satisfies ΔF1 ≤ 0.10. The decision tree misses by 0.001 with a 95% interval of [0.031, 0.171], so its verdict is decided by noise. The alert term A(τ) ≤ A_max in Eq. (7) is met by any detector at τ close to 1, where it raises no alerts, because Eq. (7) contains no minimum-recall condition and ρ in Eq. (8) is never given a value. The random forest is excluded on emulated latency, which the same section says "should be re-evaluated against any deployed system before it is used to exclude a candidate". XGBoost and histogram gradient boosting are not discussed at all. The claim that P(f) = 0 for every architecture is not established.

7. The alert-burden figures extrapolate from a small benign sample, in a different unit. The radio-layer folds contain a median of 136 benign KPM windows (Section VI-E). A false positive rate per window, estimated from about 136 negatives per fold, is multiplied by a flow arrival rate to produce tens of thousands of "alerts per hour". The conversion from windows to flows is not defined, the sample is small for a quantity that is then extrapolated linearly, and λ_b has no measured or cited basis.

8. The latency conclusions rest on a table that omits the stage the paper calls dominant. Section VI-F reports feature extraction at a median of 6.90 ms per flow (up to 37.34 ms), yet the "Min. budget" column of Table VII, the basis for "four of six conform at 10 ms", excludes it. The p99.9 column comes from 1,500 samples, so it rests on one or two observations, and no quantile carries a confidence interval. The statement that "the tail, not the median, decides conformance" is illustrated with histogram gradient boosting and the random forest, whose medians (53.16 ms and 93.41 ms) already exceed 10 ms. At B = 10 ms the median and the p99 give the same verdict for all six models.

9. The statistics overstate certainty. Twenty split seeds resample 30 radio capture sessions or 318 source addresses, so training and test sets overlap across seeds and the paired t-test over split means is anti-conservative. Nadeau and Bengio (Machine Learning 52, 2003) give a corrected resampled t-test for exactly this design. In the transfer experiment the target corpus is fixed and all variance comes from resampling the training split, so the p-values say nothing about other deployments. Holm correction does not repair an anti-conservative base test.

10. The survey in Section VIII-A cannot be checked. Table XII gives counts for 41 papers but identifies none of them, reports no screening flow (records found, screened and excluded, with reasons) and no inter-rater agreement, although two authors screened independently. The search window (January 2021 to December 2025) also excludes [16] and [17], which the paper uses to position its own contribution. Please provide the list of the 41 papers and the per-property coding as supplementary material.

11. The manuscript uses informal and rhetorical phrasing throughout (Reviewer 2 lists examples) and narrates earlier drafts of the study. It needs a thorough rewrite in formal, precise academic English, and professional proofreading would help.

**Additional Questions:**

Please confirm that you have reviewed all relevant files, including supplementary files and any author response files, which can be found in the "View Author's Response" link above (author responses will only appear for resubmissions): Yes, all files have been reviewed

1) Does the paper contribute to the body of knowledge?: The contribution rests on one pair of corpora produced by different exporters, and its operational tables contradict the paper's own equations. This severely limits the practical contribution in the current form.

2) Is the paper technically sound?: No. Tables IX and X and Figs. 4, 5 and 8 conflict with Eq. (4) and with the text.

3) Is the subject matter presented in a comprehensive manner?: No

4) Are the references provided applicable and sufficient?: Yes

5) Are there references that are not appropriate for the topic being discussed?: No

5a) If yes, then please indicate which references should be removed.:

---

### Reviewer: 7

**Comments:**

The novelty beyond the base-rate argument [13], the closed-world critique [14], the pitfalls catalogue [36], transfer between the same two corpora [16] and real-RIC latency measurement [17] is unclear. The contribution list should state what is new relative to each.

D_A is never named or cited. Section IV-A calls it an "OpenRAN Gym style" capture, and Section IX says it "is released under the same terms as the testbed platform", which reads as though the authors collected it.

The radio layer that supports most of Sections VI and VII (number of windows, window length, KPM features, class balance) is not described in Table I or anywhere else.

The time-disjoint rung in the Abstract, the contributions and Fig. 2 has no results in the body.

Fig. 1 draws radio telemetry flowing into the harmonised feature space, but Section IV-B states that radio KPIs have no counterpart and are excluded from it. Fig. 1 also shows mitigation actions (block flow, isolate device, reroute) that were not implemented.

Fig. 2 gives 1 to 25 µs for deployed inference, while Section VI-F cites 1 to 5 µs from the same source. State which models each range covers.

Eq. (2) is defined, and Section III-B promises to report it, but Section VI-B declines to compute it.

Algorithm 1 was never run as an xApp (Section V). As written, it skips RecordLatency for dropped indications (the continue at line 7), so latencies recorded this way would exclude the slowest cases, and a deadline miss detected at line 10 does not increment v.

The reverse direction (D_B to D_A) is discussed without a table. The text says D_A holds "four more" categories than D_B, while Table I lists five against two, and it cites DDoS as a category "present in the training corpus", although the caption of Table VI says D_B contains no DDoS.

Section VI-E: "a factor of 23 in burden for 0.042 of macro-F1" does not match the two models named in the same sentence (5,620 against 212,383 alerts per hour is a factor of 38, and their macro-F1 values differ by 0.108). If the comparison is with the random forest, say so.

Section VI-B states that the spread across architectures on the target (0.149) "is smaller than the distance any of them has fallen". In Table V, five of the six models fell by less than 0.149 (0.096 to 0.129).

No repository URL or DOI is given for the released code, split manifests and models. Section IX also lists an "xApp container image", "the five random seeds" and a "device-level partition", which contradict Section V (nothing containerised, 20 split seeds, device-disjoint splitting "not supportable").

Section VI-D reports a withdrawn analysis with no result, and it cites "Fard et al." without a reference.

**Additional Questions:**

Please confirm that you have reviewed all relevant files, including supplementary files and any author response files, which can be found in the "View Author's Response" link above (author responses will only appear for resubmissions): Yes, all files have been reviewed

1) Does the paper contribute to the body of knowledge?: Yes

2) Is the paper technically sound?: Yes, once the inconsistencies listed above are resolved.

3) Is the subject matter presented in a comprehensive manner?: Yes

4) Are the references provided applicable and sufficient?: Yes

5) Are there references that are not appropriate for the topic being discussed?: No

5a) If yes, then please indicate which references should be removed.:

---

## Appendix A. Editor's worksheet

**Manuscript type and venue.** An empirical evaluation and measurement study in machine learning for network security, submitted to IEEE Access. It proposes no new detector. Its contribution is methodological (an evaluation ladder, trivial floors on the target, an estimator warning, a deployability predicate), so the bar is internal consistency and the strength of the evidence behind each methodological claim.

**Where the reviewers agree and disagree.** All seven credit the question and the design choices around floors, group-disjoint splits and target quarantine. All seven find internal inconsistencies. They split on severity. Reviewers 1, 5 and 7 treat the problems as presentation errors. Reviewers 2 and 3 target claims that go beyond the data. Reviewer 4 requires new experiments: an exporter control, a third corpus, a RIC or compiled-runtime measurement and a wider model panel. Reviewer 6 treats Tables IX and X and Figs. 4, 5 and 8 as disqualifying in the current form. Reviewer 6's arithmetic on Table X can be checked from Table IX alone and it holds, so that review carries the most weight.

**Dominant concerns, in order.**

1. Internal contradictions and impossible numbers. Tables IX and X violate Eq. (4), Figs. 4, 5 and 8 contradict the text, and Section VII reports what Sections VI and XI retract (R1.3, R6.2 to R6.4, R7).
2. The transfer gap mixes exporter change and prior shift with deployment shift. The feature-blind majority floor loses as much as four of the six models (R3.1, R3.2, R4, R6.1, R6.5).
3. Headline claims without support in the body: the time-disjoint rung, "order-of-magnitude", "beneath chance", and the rank correlation (R2.1 to R2.3, R2.7, R4, R7).
4. The predicate verdict contradicts Table V, and the latency conformance table leaves out the stage the paper calls dominant (R2.6, R6.6, R6.8).
5. Verifiability: an unnamed source corpus, an unverifiable survey, and a reproducibility section that contradicts Section V (R5, R6.10, R7).

**Claim strength audit.**

| Claim | Where | Rating | Reason |
|---|---|---|---|
| A random split inflates macro-F1 by 0.09 to 0.17 | Abstract, Table IV | Fully supported | Six paired differences, all significant after Holm |
| The inflation is memorisation | VI-A, VII-A | Weakly supported | Feature-blind floors cannot separate memorisation from task difficulty. Session purity is 1.000 (Section X) |
| A time-disjoint split costs a further 0.269 and nearly triples the alert burden | Abstract, Fig. 2 | Unsupported in the manuscript | No results in the body |
| All six non-trivial architectures degrade significantly under transfer | VI-B, Table V | Partially supported | Significant, but the majority floor loses 0.114, more than three of the six |
| The source-best model falls beneath chance | Abstract, VI-B, XI | Weakly supported | 0.0017 below the floor and untested. PR-AUC 0.663 exceeds chance at 0.607 |
| In-distribution rank does not predict transfer rank | Abstract, VI-B | Weakly supported | n = 6, and five of six keep their order |
| Pooled operational precision of 0.0055 to 0.0077, collapse factor 132 | Abstract, VI-E | Supported for the radio layer | Consistent with Eq. (4). The window-to-flow conversion is undefined |
| Fold averaging inflates the spread from 1.40 to 13.18 | Abstract, VI-E | Partially supported | No table shows the fold data. Section VII and Table IX still use the fold mean |
| Detectors look alike on the source and differ by an order of magnitude on the target | VI-E | Partially supported | Compares a radio-layer source with a network-layer target |
| Calibration cannot change the achievable operating points | Abstract, VI-C | Partially supported | True for strictly monotone maps, not for isotonic regression. Contradicted by VII-B |
| Feature extraction dominates latency even after optimisation | Abstract, VI-F | Weakly supported | Optimised extraction (0.058 ms) costs less than measured inference (0.18 ms). Holds only against [17] |
| P(f) = 0 for every architecture | VIII-B | Contradicted | Logistic regression ΔF1 = 0.096 ≤ δ = 0.10, and the alert term can be met trivially |
| Existing work under-reports the three criteria (0 of 41) | VIII-A, Table XII | Unsupported as presented | No paper identified, no screening record |

**Reviewer scores (out of 10).**

| Reviewer | Novelty | Technical quality | Experimental rigor | Clarity | Reproducibility | Significance | Overall | Recommendation |
|---|---|---|---|---|---|---|---|---|
| 1 | 6 | 6 | 6 | 5 | 6 | 6 | 6 | Minor revision |
| 2 | 5 | 5 | 5 | 4 | 5 | 6 | 5 | Major revision |
| 3 | 5 | 5 | 4 | 5 | 5 | 6 | 5 | Major revision |
| 4 | 5 | 5 | 4 | 6 | 5 | 6 | 5 | Major revision |
| 5 | 6 | 6 | 5 | 5 | 5 | 6 | 6 | Minor revision |
| 6 | 4 | 3 | 3 | 3 | 4 | 4 | 3 | Reject |
| 7 | 4 | 5 | 5 | 4 | 4 | 5 | 4 | Major revision |

Under IEEE Access's binary process, any recommendation short of acceptance returns the paper. The decision is reject with resubmission encouraged.

**Publication risk matrix.**

| Risk area | Severity | Effect on publication |
|---|---|---|
| Novelty | Medium | [16] covers transfer between the same two corpora and [17] covers real-RIC latency. What remains is the protocol ladder, the floors on the target and the estimator warning |
| Experimental validity | High | Exporter change and prior shift confound the headline, and Tables IX and X violate Eq. (4) |
| Reproducibility | Medium | Generated tables with provenance are a strength. The unnamed corpus, missing URL and contradictory Section IX weaken it |
| Statistical rigor | Medium | Anti-conservative resampled t-tests, a rank test on six points, and an untested "beneath the floor" claim |
| Writing quality | High | Duplicated section, conversational register, drafting history in the text, visible formatting errors |
| Overall acceptance risk | High | Returned in the current form. Recoverable in one revision cycle with two added experiments |

**Acceptance estimate and likely outcome.** In its current form the paper has below a 5% chance of acceptance, and the most likely outcome is reject after review with resubmission encouraged. After a revision that regenerates Tables IX and X and Fig. 8 with pooled counts, removes or rebuilds Figs. 4 and 5, adds the time-disjoint results, merges Section VII into Section VI and restates the claims in the audit above, the estimate rises to about 45%. Adding the single-exporter control and a same-host compiled-runtime latency measurement lifts it to about 65%. The idea behind the paper holds up under review. The problems sit in its execution, and all of them are fixable without abandoning the study.

---

## Appendix B. Revision plan

Each row names the reviewer comments it answers (R6.2 means Reviewer 6, comment 2). Effort assumes the existing pipeline and results.

| Priority | Issue | Where | Fix | Effort | Answers |
|---|---|---|---|---|---|
| Critical | Tables IX and X and Fig. 8 use the fold-mean estimator and violate Eq. (4) | VII-B, Tables IX and X, Fig. 8 | Regenerate from pooled confusion counts, recompute the threshold for each precision target (most targets will become unreachable), rewrite VII-B | 1 day | R6.2, R6.3, R2.8 |
| Critical | Figs. 4 and 5 have no data source and contradict the text | VI-C, VI-E | Rebuild both from the calibration and threshold-sweep results, or delete them | Half a day | R6.4, R1.4 |
| Critical | The survey behind Table XII cannot be verified | VIII-A, Table XII | Run the screening and publish the paper list with per-property coding, or delete the table and the paragraph (see Appendix C, note 1) | 3 to 5 days to run, 1 hour to delete | R6.10, R5 (I25) |
| Critical | The time-disjoint rung is missing from the body | Abstract, VI, Fig. 2 | Add a subsection and a table with split definition, period sizes, control, intervals and alert burden | Half a day | R4, R7 |
| Critical | Section VII duplicates and contradicts Section VI | VI, VII | Merge the sections, delete Tables VIII and XI and Fig. 9, remove the sixfold-spread and "calibration failure" statements | 1 day | R1.3, R6.3 |
| Critical | The predicate verdict contradicts Table V | VIII-B, Eqs. (7) and (8) | Add a minimum-recall condition, set ρ, judge each term on its confidence bound, re-evaluate logistic regression, discuss XGBoost and histogram gradient boosting, and resolve the "not ours to choose" contradiction | 1 day | R2.6, R6.6 |
| High | Prior shift is mixed with covariate shift | VI-B, Table V | Add balanced accuracy and ROC-AUC columns and a difference-in-differences test against the majority floor | 1 day | R3.2, R6.5 |
| High | "Beneath chance" is untested | Abstract, VI-B, XI | Test the MLP against the floor, cite its PR-AUC, and rephrase | 2 hours | R2.1, R2.2 |
| High | Exporter confound | IV-B, VI-B, X | Re-extract 5G-NIDD from its captures with Zeek and rerun the transfer experiment | 3 to 5 days | R3.1, R4, R6.1 |
| High | Latency conformance omits extraction and quantile uncertainty | V, VI-F, Table VII | Add a stage table, include extraction in conformance, give confidence intervals for quantiles, collect at least 100,000 samples for p99.9, report thread settings, and time the ONNX models on the same host | 2 days | R1.7 to R1.9, R4, R6.8 |
| High | The MLP may lack class weighting | IV-C, Table III | Weight the MLP (sample weights or resampling) and rerun, or state the exception | 1 day | R3.5 |
| High | Source corpus unnamed and radio layer undescribed | IV-A, Table I | Name and cite D_A, give its DOI and licence, add a radio-layer column to Table I | 2 hours | R5 (I20), R7 |
| High | Window-to-flow conversion and the basis for λ_b | III-C, V, VI-E | Define the conversion, measure or cite λ_b, report false alerts per million benign flows | Half a day | R3.4, R3.7, R6.7 |
| High | Anti-conservative significance tests | V, VI | Recompute intervals with the Nadeau and Bengio correction | Half a day | R6.9 |
| High | Rank-correlation claim | Abstract, VI-B | Report ρ with and without the MLP, fix "eight" against "six", restate | 1 hour | R2.3 |
| High | Calibration claim | Abstract, VI-C | Restrict to strictly monotone maps, add the isotonic check, explain the sixth architecture | Half a day | R2.5 |
| High | Memorisation wording | VI-A, VII-A | Rephrase and discuss the scenario hold-out explanation | 1 hour | R2.4 |
| Medium | Reproducibility section contradicts Section V | IX | Add the repository URL, correct the seed count and split description, remove the container image | 1 hour | R7, R1.6 |
| Medium | Section VI-F describes load, throughput and resource results that do not exist | VI-F | Rewrite the paragraph and the subsection title | 1 hour | R1.10 |
| Medium | Terminology | Throughout | Define the split, the unit, the alert and the precision terms once | Half a day | R2.8, R1.13 |
| Medium | Wrong numbers in the text | VI-B, VI-E, VII-C | Correct "factor of 23", the 0.149 claim, "four more", the DDoS statement for the reverse direction and "four different conclusions" | 1 hour | R7 |
| Medium | Missing discussion of O-RAN practice | New subsection | Write the subsection that Reviewer 4 outlines | 1 day | R4, R3.3 |
| Medium | Narrow model panel | IV-C, VI | Add isolation forest or an autoencoder, a sequence model and CORAL | 3 to 5 days | R4 |
| Medium | Two corpora only | IV-A, VI | Add a third 5G or O-RAN corpus | 1 to 2 weeks | R4, R6.1 |
| Medium | No real RIC measurement | VI-F | OpenAirInterface with FlexRIC on a Linux host with isolated cores | 1 to 2 weeks, blocked on this Windows host (EXP-031) | R4 |
| Low | Formatting | Various | Fix the Markdown asterisks, the Eq. (7) glyph, the "(D-007)" caption, the notes in [16] and [17], the page-1 box, the author block, the template and the abstract length | Half a day | R1.1, R1.2, R1.5, R1.6, R5 (I37, I40) |
| Low | Figures | Figs. 1, 2, 6 to 8 | Enlarge fonts, remove embedded titles, fix the Fig. 7 legend, remove the radio-to-shared-space arrow in Fig. 1, state the model behind each microsecond range in Fig. 2 | 1 day | R5 (I35), R7 |
| Low | Front and back matter | Various | Add a symbols table and section introductions, adopt American spelling and one set of model names, cite the library you ran, remove Eq. (2) or report it, fix Algorithm 1 | 1 day | R5 (I1, I10), R1.12, R7 |
| Low | Register and drafting history | Throughout | Formal rewrite, remove the drafting narrative, cite or remove "previously published" and the pre-registration | 2 days | R2.9, R2.10, R6.11 |
| Low | References | Bibliography | Replace arXiv entries [3], [11] and [17] where published versions exist, and add TESSERACT, Kapoor and Narayanan, Saerens et al., Lipton et al., Nadeau and Bengio, Fawcett and Niculescu-Mizil, Ovadia et al. and Rabanser et al. | 2 hours | R2.11, R3.8, R5 (I29) |

---

## Appendix C. Notes for the authors only

These points come from the repository, not from the paper. Reviewers would not see them, but several of them decide how you should answer the letter above.

1. **Table XII must not go out as it stands.** `paper/main.tex` line 607 marks it "[SYNTHETIC] --- counts are placeholders", and claim C13 in `docs/claims.yaml` has status "planned" with the note "No evidence exists yet". Section VIII-A still describes the screening in the past tense ("Two authors screened titles and abstracts independently"). Run the screening before submission, or delete the table and the protocol paragraph. Reviewer 6, comment 10, asks for the list of the 41 papers, and there is no list to send.

2. **Figs. 4 and 5 are hand-typed.** Their coordinates sit in `paper/main.tex` (lines 469 to 496 and 521 to 558) with no source under `results/`. `results/EXP-028/processed/calibration_summary.csv` gives XGBoost a raw source ECE of 0.076 and a raw target ECE of 0.319, not 0.021 and 0.187. While these figures remain, the page-1 claim that every number is measured is false.

3. **The MLP is trained without class weighting.** In `src/oran_ids/models/zoo.py`, `_mlp` sets no weighting and `fit_model` adjusts only XGBoost. The paper's "identical class-imbalance policy" is false for the MLP, and the below-floor headline may change once the MLP is weighted.

4. **Library versions in Section V are wrong.** The paper says scikit-learn 1.4 and XGBoost 2.0. `data/provenance/pip-freeze-full.txt` and `requirements.lock` pin scikit-learn 1.8.0 and XGBoost 3.2.0.

5. **The time-disjoint result already exists.** `reports/EXP-034_drift.md` has it: −0.269 macro-F1 against a matched random-session control, z = −3.04 in both directions, and false alerts rising from 67,065 to 178,839 per hour. Adding it answers Reviewer 4 and Reviewer 7 directly.

6. **The source-against-target precision contrast compares layers.** On the network layer, which the transfer experiment uses, pooled operational precision at π = 0.002 spans 0.0046 to 0.0262, a spread of 5.74 (`tables/generated/prevalence_d_a_network_heldout_shared.tex`). Section VI-E sets the radio-layer source spread (1.40) against the network-layer target spread (11.68). Like for like, the contrast is 5.74 against 11.68, a factor of two.

7. **The reverse-direction table cuts against the text.** `tables/generated/per_category_d_a.tex`, which is not in the paper, shows brute force (absent from D_B) detected at 0.335 to 0.568 by every model, and web detected at 0.298 by logistic regression. That contradicts "a detector does not recognise an attack class it has never been shown". The DDoS range of 0.83 to 0.87 attributed to "the boosted ensembles" includes the MLP (0.865). XGBoost and histogram gradient boosting give 0.852 and 0.826.

8. **Tables IX and X and Fig. 8 predate the estimator fix.** They come from EXP-004 (`alert_burden_radio.csv`, `ppv_crossings_radio.csv`, `fig_alert_burden.pdf`), which was produced before decision D-018. Regenerate all three with pooled counts.

9. **The timing script has undisclosed settings.** `experiments/run_latency.py` times one model per architecture (split seed 101, one fold), disables garbage collection during timing, and inherits `n_jobs=-1` for the random forest and XGBoost. Disabling garbage collection removes a real source of tail latency for a Python xApp, and `n_jobs=-1` adds thread start-up cost to every single-row random forest call. State these settings in Section V or change them.

10. **D_A is NetsLab-5GORAN-IDD.** `configs/corpora/d_a.yaml` records a UCD testbed with OpenAirInterface, one O-CU, two O-DUs, one O-RU and two physical UEs, released under CC-BY-4.0 with descriptor DOI 10.1109/IEEEDATA.2025.3614167. Name and cite it. "OpenRAN Gym style" does not describe it, and a two-UE testbed sits awkwardly beside the Abstract's "very large numbers of IoT devices".

11. **The LaTeX source still carries draft markers.** The header comment of `paper/main.tex` (lines 9 to 23) says every number is a synthetic placeholder, and [SYNTHETIC] markers remain at the setup paragraph and at Tables I, III, VII and XII. IEEE Access receives the source files, so clean these before upload. The page-1 box also claims every number "reaches the text by \input from a generated table", while most in-text numbers are typed inside `\measured{}`.

12. **"Previously published" may be inaccurate.** `reports/FINAL_RESEARCH_STATUS.md` describes the two corrected findings as campaign-1 results. If they never appeared in a peer-reviewed venue, drop the word "published".

13. **Unused results can pre-empt a common request.** `reports/EXP-033_adversarial.md` holds evasion results that the paper does not mention. Reviewers of intrusion detection papers ask about adversarial robustness often enough that a short subsection is worth adding.

14. **The repository link is missing.** Section IX promises released artefacts but gives no URL. IEEE Access review is single-blind, so add https://github.com/adeliusa486/oran-ids-deployability.
