# Finalization audit, 2026-09-25

Manuscript: *What Held-Out Accuracy Predicts About Deploying Intrusion Detection in O-RAN* (A. Ali, A. Ahmad), IEEE Access class. Build after this audit: 19 pages,
0 errors, 0 undefined references, 0 overfull boxes. `pytest` 61/61.
`experiments.final_validation`: 20 PASS, 1 WARN, 2 BLOCKED, 0 FAIL. The WARN and the
two BLOCKED items are the known gaps: latency emulated, no RIC, no CPU/RAM under load.
`reproduce.py paper`: every table, macro and figure regenerated from `results/`. 37 of 37
generated files match the refrozen manifest.

This audit follows the master finalization prompt, with one exception the author asked
for: Figure 1 was rebuilt with the figure-rebuild skill from today's render in
Downloads. The prompt's "do not touch Figure 1" refers to that separate process.

---

## Output 1: final manuscript

`paper/main.pdf`, built from `paper/main.tex`, `paper/fig1_architecture.tex`,
`paper/fig2_pipeline.tex`, `paper/fig_conflict.tex` (new), `paper/latency_section.tex`,
`paper/predicate_section.tex`, `paper/references.bib`, and the generated tables and
figures. No number was typed by hand: every number in the new figures and captions
comes from `results/` or from a macro in `tables/generated/numbers.tex`.

---

## Output 2: change log

| ID | Where | Problem | Action | Reason | Scientific impact |
|---|---|---|---|---|---|
| C01 | Front matter | `\doi{10.1109/ACCESS.2024.0429000}` and "Date of publication xxxx 00, 0000" are IEEE Access template placeholders. That DOI belongs to the template, not to this paper. | Both removed. The class's "Digital Object Identifier" line is patched out. | A reader can take the DOI as real. No DOI was invented. | None on content. Removes a false identifier. |
| C02 | Footer, every page | The class prints "VOLUME 11, 2023", the template default. | Patched out of both page styles. Production restores it. | Template metadata. | None on content. |
| C03 | All captions | The caption math font (Formata) has no upright Greek, so `\Delta` printed as an accent ("´BA") in the captions of Tables 12 and 22. | `\Delta` now comes from Computer Modern in every math version. | A defect that already existed before this audit. | Captions now show ΔBA. |
| C04 | Figure 1 | New render supplied. Six errors found in it (see "Figure 1" below). | Rebuilt in TikZ with the render's own pictograms and palette, and corrected. All text is selectable. | Author's request (figure-rebuild skill). | The figure no longer implies E2 carries flows, radio data in the shared space, or a malicious path that bypasses the radio. |
| C05 | Fig. 1 caption | Described the old figure. | Rewritten for the new lanes, markers 01 to 03 and the xApp-internal panel. | Caption must match the figure. | None. |
| C06 | Figure 2 | Rung 03 omitted the third corpus. Untimed runtime stages were drawn the same as timed ones. The "How to read this figure" box looked like a dashboard. | Rung 03 now names D_C and gives its BA range from a macro. Indication decoding and control encoding are now hatched. The box became a legend. Font set to Helvetica to match Fig. 1. | Consistency (Phases 4, 7, 15). | The figure no longer implies that every latency term was timed. |
| C07 | New Fig. 5 | The label conflict is a main result but had no figure. | Added a one-column schematic of the mechanism: same content, different label, and Seq/Offset separating the copies. Ends with "benchmark separability ≠ deployable signal". Every number is a macro. | Figure A of the prompt. | Makes the D_B finding readable at a glance. |
| C08 | Fig. 6 (transfer) | Grouped bars: no uncertainty, no in-target reference, D_B only. | Redesigned as a three-panel dumbbell: D_B all flows, D_B with consistent labels, D_C. Adds Nadeau–Bengio target intervals, computed per seed with the paper's own `ci()`, and the in-target reference. | Figure D of the prompt. | Shows the whole transfer argument in one figure. No new statistic: the intervals use the same NB procedure. |
| C09 | New Fig. 7 | The per-feature W1 shift was in prose only. | Added a sorted dot plot of W1 per shared column, with the robust subset marked (EXP-045). | Figure E. | Shows why the robust subset does not remove the shift. |
| C10 | New Fig. 4 | Benign-session heterogeneity was in a table only. | Added FPR per held-out benign session (mean and range over six models), in capture order, with the 47-day gap marked and a second axis in false alerts per UE-hour. | Figure F. | Shows the central drift/session finding. |
| C11 | New Fig. 11 | No latency figure. | Added a per-call latency plot: p50, p95 and p99 per architecture and implementation, a B = 10 ms marker, and text naming which terms were timed and which were not. | Figure C (see deviation D1). | Shows that implementation, not architecture, sets latency. |
| C12 | New Fig. 12 | The thresholds of the deployability test looked arbitrary, and the robustness of the verdict was asserted in prose only. | Added (a) a grid of how many architectures meet the alert term over A_max × ρ, with the all-flows boundary, and (b) how many meet the generalization term as δ varies. | Figure B. | The verdict (0/6) holds unless an operator accepts at least ~5,600 false alerts/h at PPV ≤ 0.042 (consistent labels) and δ ≥ 0.32. |
| C13 | All data figures | Off-white background, serif text, default legends, and figures of mixed sizes. | One camera-ready style: white background, closed axes with inward ticks, Arial 7 to 8 pt at print size, Okabe-Ito colours plus marker and line-style redundancy, one column wide (3.5 in), vector PDF plus 600 dpi PNG. | Author's request ("real paper graphs, camera ready, medium size"). | None on content. Readable in greyscale at column width. |
| C14 | Figs. 3, 8, 9, 10 | Captions did not say what to notice. | Rewritten captions (Phase 26). Fig. 3 became a dot plot that includes the 1-NN row. | Self-contained captions. | None. |
| C15 | Sec. VII-B (predicate) | A_max = 200 was justified as "the volume a tier-one team of three analysts can triage after automated filtering". No source supports this. | Replaced with "The bounds are our choice: no O-RAN specification fixes them". Fig. 12 now shows the dependence on the bounds. | Phase 18: unsupported claim. | Removes an uncited empirical claim. |
| C16 | Sec. VII-B | "The test separates an evaluation that predicts deployment from one that does not." This is backwards: the pipeline that passes does so on its least deployment-like evaluation. | Retitled "Is the test attainable?". The text now says the test is only as informative as the evaluation it is applied to. | Phase 32 (logic). | Corrects an overreaching inference. |
| C17 | Sec. III-D | The test read like a requirement. | Added "We propose this test as a reporting device, not as an O-RAN requirement." | Phase 14. | Proportional claim. |
| C18 | Sec. VII-B | "That term matters only once the first two pass" had no clear referent. | Now "The latency term would matter only…". | Clarity. | None. |
| C19 | Abstract, contributions, conclusion | "the models recognize capture sessions" and "inflates the score because models recognize capture sessions" are causal readings of a correlational probe. | Now "consistent with the recognition of capture sessions" and "points to…". | Phase 11: no causal claim from descriptive evidence. | Wording matches the evidence (Sec. VI-A already said "points to"). |
| C20 | Sec. VI-D | "4 of 6 intervals exclude 0.5" is true per model, but only 3 survive Holm correction. | Now adds "(3 after Holm correction)", from the new macro `\TrChanceSigHolm`. | Phase 11. | Complete statistical statement. |
| C21 | Introduction | The benchmark-versus-deployment distinction was implicit. | Added two sentences that separate a benchmark score from deployment behaviour. | Phase 3. | Clearer positioning. No new claim. |
| C22 | Limitations | The declared parameters and the limits of the test itself were not stated as limitations. | New paragraph "Operational parameters and the test". | Phase 24. | Honest scope. |
| C23 | Bibliography | `obiuwevwi2026realtime` was cited as an arXiv preprint but is now published (ICCCN 2026). | Now cites the published paper: DOI 10.1109/ICCCN69946.2026.11662852, pp. 1–9, checked on Crossref. | Phase 17. | Correct citation. |
| C24 | Bibliography | `ilias2024moe5g` has a journal version whose abstract gives different numbers. | Note added: the cited 99.95% is from the arXiv v2 abstract. The Front. AI 2026 version is named. | Phase 17. | The citation now points to the version that contains the number. |
| C25 | Repo | No reference checker. | `scripts/verify_references.py` checks every entry against Crossref (DataCite by hand). Output: `reports/reference_check_2026-09-25.csv`. | Phase 17, reproducible. | None. |
| C26 | Repo | The new figures need generators and pictograms. | `analysis/make_figures_v2.py` rewritten (9 figures). `scripts/extract_figure1_icons.py` added. 20 icons `figures/icons/f1_*.png`. Render copied to `figures/source/fig1_arch_raw_v2.jpg`. | Reproducibility. | None. |
| C28 | Table 2 caption | Said D_B "is used only as a transfer target", but D_B also trains the reverse direction and its in-target references, and D_C its own. | Caption corrected. | Factual error. | Caption now matches Sec. IV-E. |
| C27 | Repo | `numbers.tex` changed (new macro). | `reproducibility/expected_outputs.json` refrozen (37 files). | The manifest must match. | None. |

**Deviation D1 (Figure C).** The prompt asks for a latency CDF. EXP-043 kept only
quantiles (p50, p95, p99, p99.9 with confidence intervals), not the 20,000 per-call
samples, so an empirical CDF cannot be drawn without inventing data. Fig. 11 plots the
measured quantiles instead. A true CDF would need EXP-043 re-run with sample retention,
and its numbers would then replace the published ones.

**Deviation D2.** No sentence of the abstract was rewritten except the causal
wording (C19). The abstract is 250 words by PDF text count, at IEEE Access's 250-word limit.
Adding a latency sentence would exceed the limit, and the abstract makes no latency
claim to correct.

---

## Figure 1 (figure-rebuild skill)

Source: `C:\Users\adeel\Downloads\O-RAN_intrusion-detection_system…_2K_20260925161711.jpg`,
the newest image in Downloads (25 Sep 16:17). No other candidate was close in time.
Copied to `figures/source/fig1_arch_raw_v2.jpg`. The five numbered columns, the palette
(sampled: mint DDF0EE, RIC CBDDE1/E4E9ED, xApp C9E1E1, benign 4B7FAF, teal 548F97,
coral E37866) and all 20 pictograms are the render's own. Every word is now LaTeX
text (Helvetica).

Errors found in the render and corrected:

1. "Central Anchor" under "03 NEAR-RT RIC" was prompt text rendered as a heading. Removed.
2. Malicious traffic went from the gateway straight into the O-CU, bypassing the
   radio. All UE traffic enters over Uu at the O-RU, so both streams are now drawn into the O-RU.
3. E2 was drawn straight into the detection xApp. E2 terminates at the E2 termination
   of the RIC platform, and the xApp subscribes through it.
4. The radio lane fed the "harmonised feature space". That space has flow columns only (15
   concepts / 18 columns) and no radio counterpart (review R7, D-022). The layers are
   not fused (Limitations). Radio windows now go to their own detector.
5. The arrows ran from the xApp out to E2SM-KPM and to the flow exporter, and the alert came
   from the feature space. Data now flows into the detector, and the alert is the detector's output.
   Column 04 is labelled as the xApp's own feature construction and inference.
6. Marker 03 (decision latency) was drawn like the measured markers. It is emulated
   off-platform, so it is now hollow and dashed, and the footnote says so.
   Also: "window / feature representation" now states what the window is (16 records × 16 KPM
   fields, mean and s.d.), and "harmonised" became "shared", the paper's own term.

Checks: previewed standalone three times, then checked on the page. Text is selectable:
`O-RU`, `E2 termination`, `NOT EXECUTED`, `shared feature space` and `Decision latency`
are all found by PyMuPDF text search in `main.pdf`.

---

## Output 3: experimental verification

Status key: PASS = result files present, regenerated by `reproduce.py paper`, and the
paper's numbers equal the regenerated macros. WARNING = supported, with a stated
qualification. FAIL = none.

| Experiment | Dataset | Split | Metric | Seeds | Statistics | Table / figure | Status |
|---|---|---|---|---|---|---|---|
| Protocol sensitivity (EXP-041/052) | D_A radio | random vs run-disjoint vs category-stratified | macro-F1 | 20 split × 2 model | NB-corrected CI, Holm | Tab. 5, Fig. 3 | PASS. Average gain not significant. The text says so. |
| NN probe (EXP-042) | D_A radio | same splits | macro-F1, same-session NN share | 20 | NB CI | Tab. 5, Sec. VI-A | PASS |
| Sequence models (EXP-050) | D_A radio | same | macro-F1 | 20 | NB, Holm within pair | Tab. 6 | PASS |
| Time split with coverage fixed (EXP-053) | D_A radio | latest/earliest session per category vs random draws | BA | control draws | percentile of control | Tab. 7 | PASS |
| Benign sessions held out (EXP-053) | D_A radio | leave-one-benign-session-out | FPR, alerts/UE-h | 1 per session | range over 6 models | Tab. 8, Fig. 4 | WARNING: n = 10 sessions, as the paper states. |
| Label-conflict audit (EXP-057) | D_B | n/a | conflict share, BA ceiling | deterministic | exact | Tab. 10, Fig. 5 | PASS |
| In-target references (EXP-054) | D_B | random / file-disjoint / station | BA | 1–2 draws | range | Tab. 9 | WARNING: few draws per protocol (n = 1 to 2). |
| Published pipeline ladder (EXP-055) | D_B | R0–R3 | acc., BA, FPR | per rung | range | Tab. 11 | PASS. R0 reproduces 99.87–99.96%. |
| Transfer A→B (EXP-041) | D_A→D_B | src-address-disjoint | BA, macro-F1, AUC | 20 | NB, Holm, DiD vs majority | Tab. 12, Fig. 6a | PASS |
| Transfer A→B, consistent labels (EXP-056) | D_A→D_B | same | BA | 10 | NB, Holm | Fig. 6b, Sec. VI-D | PASS |
| Reverse B→A (EXP-041) | D_B→D_A | random (no group key) | BA | 20 | NB, Holm | Tab. 13 | WARNING: source reference is optimistic (stated). |
| Per-category (EXP-041) | both | same | recall/specificity | 20 | means | Tab. 14 | PASS |
| Arms: robust subset, CORAL, novelty (EXP-045/048/049) | D_A→D_B | same | BA | 20 | means | Tab. 15, Fig. 7 | PASS |
| Harmonisation cost (EXP-047) | D_A | same | BA | 20 | NB | Tab. 16 | PASS |
| Third corpus (EXP-058) | D_A→D_C, D_B→D_C | as above | BA, AUC, recall, PPV | 20 / 10 | NB, Holm. No cluster bootstrap (3 files) | Tab. 17, Fig. 6c | WARNING: 3 capture files, no cluster intervals. The drop is not significant from D_A. All stated. |
| Pooled operating points (EXP-046/052/056) | D_A radio, D_A flows, D_B | pooled | FPR, PPV, alerts/h | 20 (10 for bootstrap) | cluster bootstrap, 2,000 reps | Tab. 18, Figs. 8, 9 | PASS |
| Estimator contrast (EXP-052) | D_A radio | same | PPV pooled/median/mean | 20 | n/a | Tab. 19 | PASS |
| Calibration and prior (EXP-044) | D_A→D_B | three-way group split | ΔAUC, macro-F1 | 10 | range | Tab. 20, Fig. 10 | PASS |
| Latency (EXP-043) | radio + flow | n/a | p50/p95/p99/p99.9 ms | 20,000 calls | distribution-free CI | Tab. 21, Fig. 11 | WARNING: off-platform, one Windows host, no CPU isolation. Indication, action and queueing terms not timed. |
| Deployability test (EXP-052) | D_B (and clean) | n/a | Eq. (6) | from above | upper NB bound | Tab. 22, Fig. 12 | PASS |
| Live RIC, CPU/RAM (EXP-031) | none | n/a | n/a | n/a | n/a | none | NOT RUN, stated as not run (not a FAIL: nothing claims it). |

---

## Output 4: reference verification

Method: `scripts/verify_references.py` resolved every DOI at Crossref (DataCite for the IEEE DataPort DOI by hand) and compared title, first author, author count and year. Entries without a DOI were checked against the publisher page or arXiv where marked. "DOI resolved to same work" = the DOI record has the same title (Crossref stores some titles without the subtitle), first author and year. "Citation context" = whether the source supports the sentence that cites it. For the canonical works this rests on their well-known central result. The full texts were not re-read in this session. 62 references are printed. `gorbil2016signalling` is in the .bib but not cited, so BibTeX omits it.

Summary after the second pass: **53 VERIFIED, 10 PARTIAL** (no DOI exists, metadata matches the known proceedings record), **0 UNVERIFIED**, **0 PROBLEM**. The two O-RAN specifications now point to their public ETSI editions, which were opened and read. Fixed in this audit: C23, C24. One journal-printed DOI (Abraheem & Edhirig, 10.63318/waujpasv4i2_24) does not resolve at doi.org and was deliberately not added.

| # | Key | Title (truncated) | First author (n) | Year | DOI | DOI resolved to same work? | Citation context | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | `polese2023understanding` | Understanding O-RAN: Architecture, Interfaces, Algorithms, Security, and Research Challe | Polese (5) | 2023 | 10.1109/COMST.2023.3239220 | yes | O-RAN architecture survey. Cited for disaggregation, RIC, E2SM-KPM/RC. Matches. | **VERIFIED** |
| 2 | `abdalla2022toward` | Toward Next Generation Open Radio Access Networks: What O-RAN Can and Cannot Do! | Abdalla (4) | 2022 | 10.1109/MNET.108.2100659 | yes | O-RAN overview. Background only. | **VERIFIED** |
| 3 | `niknam2022intelligent` | Intelligent O-RAN for Beyond 5G and 6G Wireless Networks | Niknam (8) | 2022 | 10.1109/GCWkshps56602.2022.10008676 | yes | Intelligent O-RAN. Background only. | **VERIFIED** |
| 4 | `shi2016edge` | Edge Computing: Vision and Challenges | Shi (5) | 2016 | 10.1109/JIOT.2016.2579198 | yes | Edge computing vision. Cited for 'RIC runs close to the cells'. Loose but acceptable (general edge argument). | **VERIFIED** |
| 5 | `bonati2021intelligence` | Intelligence and Learning in O-RAN for Data-Driven NextG Cellular Networks | Bonati (5) | 2021 | 10.1109/MCOM.101.2001120 | yes | O-RAN intelligence/learning. Background. | **VERIFIED** |
| 6 | `antonakakis2017mirai` | Understanding the Mirai Botnet | Antonakakis (19) | 2017 | none | n/a (no DOI) | USENIX Sec 2017 pp. 1093-1110. No DOI exists. Metadata matches the USENIX record as known. Page not reopened this session. Context (IoT botnets as volumetric source) matches. | **PARTIAL** |
| 7 | `kolias2017ddos` | DDoS in the IoT: Mirai and Other Botnets | Kolias (4) | 2017 | 10.1109/MC.2017.201 | yes | Mirai/IoT DDoS. Matches. | **VERIFIED** |
| 8 | `polese2023coloran` | ColO-RAN: Developing Machine Learning-Based xApps for Open RAN Closed-Loop Control o | Polese (5) | 2023 | 10.1109/TMC.2022.3188013 | yes | xApp development platform. Matches. | **VERIFIED** |
| 9 | `schmidt2021flexric` | FlexRIC: An SDK for Next-Generation SD-RANs | Schmidt (3) | 2021 | 10.1145/3485983.3494870 | yes (short title in Crossref) | Crossref stores short title 'FlexRIC'. Subtitle, authors, year match. SDK for SD-RAN. Matches. | **VERIFIED** |
| 10 | `wen2024spector` | 5G-Spector: An O-RAN Compliant Layer-3 Cellular Attack Detection Service | Wen (5) | 2024 | 10.14722/ndss.2024.24527 | yes | O-RAN compliant L3 attack detection. Matches. | **VERIFIED** |
| 11 | `scalingi2024detran` | Det-RAN: Data-Driven Cross-Layer Real-Time Attack Detection in 5G Open RANs | Scalingi (5) | 2024 | 10.1109/INFOCOM52122.2024.10621223 | yes | Cross-layer real-time attack detection in O-RAN. Matches. | **VERIFIED** |
| 12 | `samarakoon2022niddarxiv` | 5G-NIDD: A Comprehensive Network Intrusion Detection Dataset Generated over 5G Wireles | Samarakoon (8) | 2022 | none | n/a (no DOI) | arXiv 2212.01298 checked (title, 8 authors in order, 2 Dec 2022). The 99.85-99.95% figures come from its Table X and were reproduced in EXP-055. | **VERIFIED** |
| 13 | `ilias2024moe5g` | Convolutional Neural Networks and Mixture of Experts for Intrusion Detection in 5G Netwo | Ilias (5) | 2024 | none | n/a (no DOI) | arXiv v2 abstract states 'weighted F1-score up to 99.95%' on 5G-NIDD (checked). Journal version (Front. AI 8:1708953, 2026) now noted in the entry. Its abstract reports accuracy up to 99.96%. | **VERIFIED** |
| 14 | `layeghy2022generalisability` | Explainable Cross-Domain Evaluation of ML-Based Network Intrusion Detection Systems | Layeghy (2) | 2023 | 10.1016/j.compeleceng.2023.108692 | yes | Key name says 2022, entry is the 2023 Comput. Electr. Eng. paper. Metadata consistent. Cross-domain NIDS generalization is poor. Matches. | **VERIFIED** |
| 15 | `layeghy2023benchmarking` | Benchmarking the Benchmark --- Comparing Synthetic and Real-World Network IDS Datasets | Layeghy (3) | 2024 | 10.1016/j.jisa.2023.103689 | yes | J. Inf. Secur. Appl. 2024. Synthetic vs real NIDS datasets. Matches. | **VERIFIED** |
| 16 | `axelsson2000baserate` | The Base-Rate Fallacy and the Difficulty of Intrusion Detection | Axelsson (1) | 2000 | 10.1145/357830.357849 | yes | Base-rate fallacy. Canonical source for the claim. | **VERIFIED** |
| 17 | `sommer2010outside` | Outside the Closed World: On With Machine Learning for Network Intrusion Detection | Sommer (2) | 2010 | 10.1109/SP.2010.25 | yes | Closed-world critique. Canonical source. | **VERIFIED** |
| 18 | `etsi_e2gap` (was `oran_wg3_ricarch`) | E2 Interface: General Aspects and Principles (O-RAN.WG3.E2GAP-R003-v04.01) | ETSI (PAS) | 2024 | none (ETSI TS 104 038 V4.1.0, public URL) | n/a, PDF opened | Replaces the unopenable RICARCH document. The PDF states "E2 interface shall support latency requirements for near-real-time optimization, i.e. from 10 milliseconds up to 1 second", which is exactly what the paper cites it for. | **VERIFIED** |
| 19 | `arp2022dosdonts` | Dos and Don'ts of Machine Learning in Computer Security | Arp (8) | 2022 | none | n/a (no DOI) | USENIX Sec 2022 pp. 3971-3988. No DOI. Metadata matches the known record. Context (pitfalls: sampling bias, data snooping) matches. | **PARTIAL** |
| 20 | `pendlebury2019tesseract` | TESSERACT: Eliminating Experimental Bias in Malware Classification across Space and Time | Pendlebury (5) | 2019 | none | n/a (no DOI) | USENIX Sec 2019 pp. 729-746. No DOI. Temporal/spatial bias. Matches. | **PARTIAL** |
| 21 | `abraheem2026bidirectional` | Bidirectional Cross-Dataset Generalization and Label-Efficient Adaptation for 5G Network | Abraheem (2) | 2026 | none | n/a (no DOI) | Journal page checked: title, 2 authors, WAUJPAS 4(2), 7 Aug 2026, XGBoost, 15 harmonized features. Zero-shot BA per task 0.505/0.500/0.558 NetsLab->5G-NIDD and 0.518/0.807/0.834 reverse, i.e. 0.50-0.56 and 0.52-0.83 as the paper states. The DOI printed on the journal page (10.63318/waujpasv4i2_24) returns 404 at doi.org, so it is NOT added. | **PARTIAL** |
| 22 | `obiuwevwi2026realtime` | Enabling Real-Time AI in O-RAN: Deploying and Measuring AI Inside a Near-RT RIC  | Obiuwevwi (10) | 2026 | 10.1109/ICCCN69946.2026.11662852 | yes | Now cited as the published ICCCN 2026 paper, DOI 10.1109/ICCCN69946.2026.11662852 (Crossref: title, 10 authors, pp. 1-9). arXiv v2 abstract: LR 1-5 us, MLP 10-25 us in OAI+FlexRIC. Crossref spells two names 'Nannou' and 'Ur Rahman'. The entry keeps the authors' own arXiv spelling. Check against IEEE Xplore. | **VERIFIED** |
| 23 | `nugraha2025fivegdatasets` | A Comprehensive 5G Dataset for Control and Data Plane Security and Resource Management | Nugraha (10) | 2025 | 10.1109/CSR64739.2025.11130023 | yes | IEEE CSR 2025 pp. 326-333. D_C source. Matches (checked when added, and again now). | **VERIFIED** |
| 24 | `bonati2023openrangym` | OpenRAN Gym: AI/ML Development, Data Collection, and Testing for O-RAN on PAWR Pla | Bonati (5) | 2023 | 10.1016/j.comnet.2022.109502 | yes | Platform. Matches. | **VERIFIED** |
| 25 | `bonati2021scope` | SCOPE: An Open and Softwarized Prototyping Platform for NextG Systems | Bonati (4) | 2021 | 10.1145/3458864.3466863 | yes (short title in Crossref) | Crossref short title 'SCOPE'. Rest matches. | **VERIFIED** |
| 26 | `nikaein2014oai` | OpenAirInterface: A Flexible Platform for 5G Research | Nikaein (6) | 2014 | 10.1145/2677046.2677053 | yes (short title in Crossref) | Crossref short title. Rest matches. | **VERIFIED** |
| 27 | `gomez2016srslte` | srsLTE: An Open-Source Platform for LTE Evolution and Experimentation | Gomez-Miguelez (6) | 2016 | 10.1145/2980159.2980163 | yes (short title in Crossref) | Crossref short title. Rest matches. | **VERIFIED** |
| 28 | `etsi_wg11_threat` (was `oran_wg11_security`) | O-RAN Security Threat Modeling and Risk Assessment (O-RAN.WG11.Threat-Modeling.O-R003-v03.00) | ETSI (PAS) | 2025 | none (ETSI TR 104 106 V3.0.0, public URL) | n/a, PDF opened | The public ETSI edition of the WG11 threat model. Title page read, and it has clauses on threats against the Near-RT RIC (7.4.1.4) and against xApps (7.4.1.6), which is what the paper cites it for. | **VERIFIED** |
| 29 | `liyanage2023openran` | Open RAN Security: Challenges and Opportunities | Liyanage (4) | 2023 | 10.1016/j.jnca.2023.103621 | yes | Open RAN security challenges. Matches. | **VERIFIED** |
| 30 | `mimran2022security` | Security of Open Radio Access Networks | Mimran (8) | 2022 | 10.1016/j.cose.2022.102890 | yes | Security of Open RAN. Matches. | **VERIFIED** |
| 31 | `groen2025implementing` | Implementing and Evaluating Security in O-RAN: Interfaces, Intelligence, and Platforms | Groen (7) | 2025 | 10.1109/MNET.2024.3434419 | yes | Security mechanisms across O-RAN interfaces implemented and measured. Matches. | **VERIFIED** |
| 32 | `fard2026crosslayer` | Cross-Layer Intrusion Detection in 5G O-RAN: Gains and Limits of Fusing Radio Telemetr | Fard (3) | 2026 | none | n/a (no DOI) | arXiv 2606.22450 checked: title, 3 authors, 21 Jun 2026. Uses NetsLab-5GORAN-IDD and fuses radio telemetry with flow records, as the paper says. Note: it reports 42 experiment runs, where our clock-gap recovery finds 30 radio sessions (see risk report). | **VERIFIED** |
| 33 | `koroniotis2019botiot` | Towards the Development of Realistic Botnet Dataset in the Internet of Things for Networ | Koroniotis (4) | 2019 | 10.1016/j.future.2019.05.041 | yes | IoT corpus list. Matches. | **VERIFIED** |
| 34 | `moustafa2021toniot` | A New Distributed Architecture for Evaluating AI-Based Security Systems at the Edge: Net | Moustafa (1) | 2021 | 10.1016/j.scs.2021.102994 | yes | IoT corpus list. Matches. | **VERIFIED** |
| 35 | `ferrag2022edgeiiot` | Edge-IIoTset: A New Comprehensive Realistic Cyber Security Dataset of IoT and IIoT A | Ferrag (5) | 2022 | 10.1109/ACCESS.2022.3165809 | yes | IoT corpus list. Matches. | **VERIFIED** |
| 36 | `neto2023ciciot` | CICIoT2023: A Real-Time Dataset and Benchmark for Large-Scale Attacks in IoT Environme | Neto (6) | 2023 | 10.3390/s23135941 | yes | IoT corpus list. Matches. | **VERIFIED** |
| 37 | `sharafaldin2018cicids` | Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization | Sharafaldin (3) | 2018 | 10.5220/0006639801080116 | yes | CIC-IDS2017. Matches. | **VERIFIED** |
| 38 | `samarakoon2022nidd` | 5G-NIDD: A Comprehensive Network Intrusion Detection Dataset Generated over 5G Wireles | Samarakoon (8) | 2022 | 10.21227/xtep-hv36 | yes (DataCite) | IEEE DataPort DOI 10.21227/xtep-hv36 is a DataCite DOI (not in Crossref). DataCite record checked: title, first 3 authors, 2022, IEEE DataPort. | **VERIFIED** |
| 39 | `siriwardhana2025descriptor` | Descriptor: 5G Wireless Network Intrusion Detection Dataset (5G-NIDD) | Siriwardhana (8) | 2025 | 10.1109/IEEEDATA.2025.3592888 | yes | 5G-NIDD descriptor. Matches. | **VERIFIED** |
| 40 | `abedzadeh2025netslab` | Descriptor: 5G Open Radio Access Network Multi-Modal Intrusion Detection Dataset (NetsL | Zadeh (5) | 2025 | 10.1109/IEEEDATA.2025.3614167 | yes | NetsLab-5GORAN-IDD descriptor. Matches (Fard et al. cite the same record). | **VERIFIED** |
| 41 | `sarhan2021netflow` | NetFlow Datasets for Machine Learning-Based Network Intrusion Detection Systems | Sarhan (4) | 2021 | 10.1007/978-3-030-72802-1_9 | yes | NetFlow datasets. Matches. | **VERIFIED** |
| 42 | `sarhan2022standard` | Towards a Standard Feature Set for Network Intrusion Detection System Datasets | Sarhan (3) | 2022 | 10.1007/s11036-021-01843-0 | yes | Standard NetFlow feature set. Matches. | **VERIFIED** |
| 43 | `engelen2021troubleshooting` | Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study | Engelen (3) | 2021 | 10.1109/SPW53761.2021.00009 | yes | CIC-IDS2017 labeling/flow faults. Matches. | **VERIFIED** |
| 44 | `flood2024smells` | Bad Design Smells in Benchmark NIDS Datasets | Flood (4) | 2024 | 10.1109/EuroSP60621.2024.00042 | yes | Design smells in NIDS benchmarks. Matches. | **VERIFIED** |
| 45 | `kapoor2023leakage` | Leakage and the Reproducibility Crisis in Machine-Learning-Based Science | Kapoor (2) | 2023 | 10.1016/j.patter.2023.100804 | yes | Leakage taxonomy. Matches. | **VERIFIED** |
| 46 | `apruzzese2023role` | The Role of Machine Learning in Cybersecurity | Apruzzese (7) | 2023 | 10.1145/3545574 | yes | Survey of ML in cybersecurity practice. 'gap between reported and operational effectiveness is surveyed' is a fair summary. | **VERIFIED** |
| 47 | `kus2022falsesense` | A False Sense of Security? Revisiting the State of Machine Learning-Based Industrial Int | Kus (8) | 2022 | 10.1145/3494107.3522773 | yes (short title in Crossref) | Crossref short title. Industrial IDS re-evaluation. Matches. | **VERIFIED** |
| 48 | `dhooge2020interdataset` | Inter-Dataset Generalization Strength of Supervised Machine Learning Methods for Intrusion | Dhooge (4) | 2020 | 10.1016/j.jisa.2020.102564 | yes | Inter-dataset generalization. Matches. | **VERIFIED** |
| 49 | `saerens2002adjusting` | Adjusting the Outputs of a Classifier to New a Priori Probabilities: A Simple Procedure | Saerens (3) | 2002 | 10.1162/089976602753284446 | yes | EM prior adjustment. Canonical. | **VERIFIED** |
| 50 | `lipton2018bbse` | Detecting and Correcting for Label Shift with Black Box Predictors | Lipton (3) | 2018 | none | n/a (no DOI) | ICML 2018, PMLR 80:3122-3130. No DOI. BBSE. Matches. | **PARTIAL** |
| 51 | `guo2017calibration` | On Calibration of Modern Neural Networks | Guo (4) | 2017 | none | n/a (no DOI) | ICML 2017, PMLR 70:1321-1330. No DOI. Temperature scaling. Matches. | **PARTIAL** |
| 52 | `ovadia2019trust` | Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty under Dataset  | Ovadia (9) | 2019 | none | n/a (no DOI) | NeurIPS 2019. No DOI, no pages in entry. Calibration under shift. Matches. | **PARTIAL** |
| 53 | `fawcett2007pav` | PAV and the ROC Convex Hull | Fawcett (2) | 2007 | 10.1007/s10994-007-5011-0 | yes | Isotonic = ROC convex hull on fitting data. Matches the paper's use exactly. | **VERIFIED** |
| 54 | `rabanser2019failing` | Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift | Rabanser (3) | 2019 | none | n/a (no DOI) | NeurIPS 2019. No DOI. Shift detection. Matches. | **PARTIAL** |
| 55 | `sun2016coral` | Return of Frustratingly Easy Domain Adaptation | Sun (3) | 2016 | 10.1609/aaai.v30i1.10306 | yes | CORAL. Matches. | **VERIFIED** |
| 56 | `nadeau2003inference` | Inference for the Generalization Error | Nadeau (2) | 2003 | 10.1023/A:1024068626366 | yes | Corrected resampled t-test. Canonical. Variance factor 1/J + n_test/n_train is theirs. | **VERIFIED** |
| 57 | `breiman2001random` | Random Forests | Breiman (1) | 2001 | 10.1023/A:1010933404324 | yes | Random forests. | **VERIFIED** |
| 58 | `chen2016xgboost` | XGBoost: A Scalable Tree Boosting System | Chen (2) | 2016 | 10.1145/2939672.2939785 | yes (short title in Crossref) | Crossref short title 'XGBoost'. Rest matches. | **VERIFIED** |
| 59 | `pedregosa2011scikit` | Scikit-learn: Machine Learning in Python | Pedregosa (16) | 2011 | none | n/a (no DOI) | JMLR 12:2825-2830. JMLR issues no DOI. Matches the known record. | **PARTIAL** |
| 60 | `cho2014gru` | Learning Phrase Representations with RNN Encoder--Decoder for Statistical Machine Trans | Cho (7) | 2014 | 10.3115/v1/D14-1179 | yes | GRU. Matches. | **VERIFIED** |
| 61 | `liu2008isolation` | Isolation Forest | Liu (3) | 2008 | 10.1109/ICDM.2008.17 | yes | Isolation forest. Matches. | **VERIFIED** |
| 62 | `lundberg2017shap` | A Unified Approach to Interpreting Model Predictions | Lundberg (2) | 2017 | none | n/a (no DOI) | NeurIPS 2017 pp. 4765-4774. No DOI. SHAP, cited only as future work. | **PARTIAL** |
| new | `jin2013softcell` | SoftCell: Scalable and Flexible Cellular Core Network Architecture | Jin (4) | 2013 | 10.1145/2535372.2535377 | yes (Crossref, pp. 163-174) | Added to anchor the declared benign flow rate. The arXiv version (1305.3568) says "we expect the actual flow arrival rate to be around several hundred flows per second" at a heavily loaded LTE base station. The paper uses it only to say its 67 flows per second is low. | **VERIFIED** |

---

## Output 5: figure audit

| Figure | Purpose | Scientific correctness | Data source | Visual clarity | Caption | Changes made | Status |
|---|---|---|---|---|---|---|---|
| 1 Architecture | Deployment context. What is measured | Rebuilt by the figure-rebuild skill (the prompt excludes Fig. 1 from this audit). Six render errors corrected | n/a | Good at page width. Smallest text ≈6.6 pt | Rewritten | See "Figure 1" | PASS (skill) |
| 2 Pipeline | The evaluation ladder | Now names D_C. Untimed stages hatched | macros | Dense. Smallest text ≈4.8 pt (`\tiny` after scaling) | OK | C06 | REVISE (optional): enlarge the `\tiny` detail lines |
| 3 Protocol sensitivity | Random-split inflation | Matches Tab. 5 | EXP-052 leakage_stats, leakage_nn1 | Dot plot, 3 markers | Rewritten | C13, C14 | PASS |
| 4 Benign sessions (new) | FPR set by the session | Matches Tab. 8 | EXP-052 drift_v3_benign | Clear. 2nd axis is the same quantity ×225 | New | C10 | PASS |
| 5 Label conflict (new) | Mechanism of the D_B conflict | Numbers are macros. Tiles marked schematic in caption | EXP-055, EXP-057 | One column, 7 pt | New | C07 | PASS |
| 6 Transfer (redesigned) | Source vs target BA, three targets | Means equal Tab. 12/17 and Sec. VI-D. CIs from the same NB procedure | EXP-041, EXP-056, EXP-058 runs | Three narrow panels. Readable at 3.5 in | Rewritten | C08 | PASS |
| 7 Feature shift (new) | W1 per column, robust subset | Matches W̄1 macros (0.28 / 0.27) | EXP-045 feature_shift | Clear | New | C09 | PASS |
| 8 PPV vs threshold | No threshold rescues precision | Matches reachability macros | EXP-046, EXP-041 | Restyled. ρ line added | Rewritten | C13, C14 | PASS |
| 9 PPV vs prevalence | Base-rate arithmetic | Matches π-sweep | EXP-052 pooled_radio_tau05 | Six lines overlap (intended: they are nearly identical) | Rewritten | C13, C14 | PASS. Candidate for the supplement if space is tight |
| 10 Reliability | Miscalibration under transfer | Unchanged data | EXP-041 reliability_bins | Restyled | OK | C13 | PASS |
| 11 Latency (new) | Implementation vs architecture | Quantiles from EXP-043. Untimed terms named | EXP-043 latency_stages | Log axis, 3 implementations | New | C11, D1 | PASS (quantile plot, not CDF) |
| 12 Sensitivity (new) | Robustness of the 0/6 verdict | Recomputed from pooled counts with the paper's rule. Endpoints equal PredClean*/PredGen* macros | EXP-041, EXP-056, predicate.csv | Grid plus step plot | New | C12 | PASS |

---

## Output 6: table audit

All 22 tables are generated (`analysis/make_tables_v2.py`, provenance header,
`reproduce.py` checks). Every prose number is a macro from the same
statistics files, so tables and text cannot disagree unless a generator is edited.

| Table | Numerical consistency | Formatting | Caption | Units | Statistical notation | Cross-ref | Status |
|---|---|---|---|---|---|---|---|
| 1 Notation | n/a | OK | OK | n/a | ok | cited in Sec. I | PASS |
| 2 Datasets | regenerated | OK | Fixed: said D_B is "used only as a transfer target", but D_B also trains the reverse direction and its in-target references | counts | n/a | ok | PASS (fixed, C28) |
| 3 Shared space | generated from YAML | OK | OK | n/a | n/a | ok | PASS |
| 4 Hyperparameters | hand-written, matches `configs` | OK | OK | n/a | n/a | ok | PASS |
| 5 Protocol sensitivity | = macros | OK | OK | macro-F1 | NB 95% CI, Holm | ok | PASS |
| 6 Sequence models | = macros | OK | OK | macro-F1 | NB CI | ok | PASS |
| 7 Time split | = macros | OK | OK | BA | control percentile | ok | PASS |
| 8 Benign sessions | = Fig. 4 | OK | OK | FPR, alerts/UE-h | range | ok | PASS |
| 9 In-target refs | = macros | wide (table*) | OK | BA | n draws stated | ok | PASS |
| 10 Conflicts | = macros | OK | OK | %, BA | exact | ok | PASS |
| 11 Published ladder | = macros | table* | OK | BA | n/a | ok | PASS |
| 12 Transfer A→B | = macros | table* | Δ fixed (C03) | BA, F1 | NB, Holm, * | ok | PASS |
| 13 Reverse | = macros | narrow tabcolsep 2.2pt | OK | BA | NB | ok | PASS |
| 14 Per-category | = macros | table* | OK | recall | n/a | ok | PASS |
| 15 Arms | = macros | OK | OK | BA | means | ok | PASS |
| 16 Harmonisation | = macros | OK | OK | BA | NB | ok | PASS |
| 17 Third corpus | = macros | table* | OK | BA, AUC, recall | means only (3 files) | ok | PASS |
| 18 Pooled points | = macros | table*, dense | long but complete | FPR, PPV, alerts/h, alerts/UE-h | cluster bootstrap | ok | PASS |
| 19 Estimator | = macros | OK | OK | PPV | n/a | ok | PASS |
| 20 Calibration | = macros | table* | OK | ΔAUC, F1 | n/a | ok | PASS |
| 21 Latency | = macros | table* | OK | ms | distribution-free CI | ok | PASS |
| 22 Deployability | = macros | OK | Δ fixed (C03) | BA, PPV, alerts/h, ms | upper NB bound | ok | PASS |

Global: 22 tables and 12 figures in 19 pages is heavy for a journal article. Tables
4, 6, 13, 16, 19 and Fig. 9 are candidates for supplementary material if an editor asks
for a shorter paper. None of them carries a result that is not also stated in the text.

---

## Output 7: reviewer risk report

| # | Issue | Severity | Evidence | Current response in the manuscript | Recommended fix |
|---|---|---|---|---|---|
| 1 | No live near-RT RIC. Latency timed off-platform on one Windows host | HIGH | EXP-031 blocked | Stated in abstract scope, Sec. I, III-C, V, VI-J, VII, IX, Figs. 1, 2, 11 | Run EXP-031 on a Linux host with isolated cores (OAI + FlexRIC), or keep the current framing. It is consistent throughout |
| 2 | Cross-corpus gap confounded by exporter (Zeek vs Argus vs NFStream) | HIGH | Tab. 2, Sec. VI-E | Robust subset, domain classifier, base-station split inside D_B, D_C with a third exporter, Limitations | Re-extract one corpus with the other's exporter. Needs 5G-NIDD pcaps, which are not in our copy |
| 3 | 30 radio sessions (10 benign) limit every radio conclusion | MEDIUM-HIGH | Tabs. 5, 7, 8, 18 | NB intervals, cluster bootstrap, explicit "cannot determine" wording | Nothing more is possible without new radio captures |
| 4 | Session count: Fard et al. describe NetsLab-5GORAN-IDD as 42 experiment runs. We recover 30 radio sessions from clock gaps | MEDIUM | arXiv 2606.22450 text vs Sec. IV-A | Not addressed | Check whether the 42 runs include flow-only runs or split sessions, and add one reconciling sentence in Sec. IV-A. Not done here: it needs the raw archives |
| 5 | Deployability bounds look arbitrary | MEDIUM | Sec. VII-B | Fixed in this audit: bounds declared as ours. Fig. 12 shows how the verdict depends on them. Unsupported analyst-capacity claim removed | None further |
| 6 | Novelty: transfer between these corpora (Abraheem & Edhirig) and in-RIC inference (Obiuwevwi et al.) already published | MEDIUM | Sec. I, II-D | Credited at first mention. Contribution stated as joint measurement + label audit + published-pipeline ladder + operational/latency criteria | Keep. Do not add "first" claims |
| 7 | D_B label assignment: which copy is correct is unknown, and the base-station mapping is inferred | MEDIUM | Sec. VI-C, Limitations | Every D_B result given with and without the copies. Neutral wording ("label conflict"). No label changed | Contact the 5G-NIDD authors for the capture log, and cite the reply if one arrives |
| 8 | D_C is a 5G-core testbed, not O-RAN. 3 files. No cluster CIs. Drop from D_A not significant | MEDIUM | Tab. 17 | All stated in Sec. VI-F and Limitations | None. Do not strengthen the D_C sentence in the abstract |
| 9 | π = 0.002 and λ_b = 240,000 flows/h have no cited source | MEDIUM | Sec. V | Declared and swept. PPV depends on π only. New Limitations paragraph | Optionally cite an operator or measurement study for flow rates. Otherwise keep "declared" |
| 10 | Fixed hyperparameters, no tuning | LOW-MEDIUM | Tab. 4 | Stated. Identical across protocols by design | One sentence on why: tuning on the source would favour source-specific structure. Optional |
| 11 | O-RAN specifications not opened. Version of the WG11 document missing | LOW | refs 18, 24 | n/a | Confirm versions on the O-RAN portal before submission |
| 12 | Length: 19 pages, 22 tables, 12 figures | LOW-MEDIUM | PDF | n/a | Move the tables listed in Output 6 to a supplement if asked |

---

## Output 8: readiness ratings

| Dimension | Score | Why |
|---|---|---|
| Scientific quality | 8/10 | Coherent question, negative results kept, every claim traced to a generated number |
| Novelty | 6/10 | The individual critiques are known and credited. The contribution is measuring them together, plus the D_B label audit and the published-pipeline ladder. Real, but incremental |
| Methodology | 8/10 | Group-disjoint splits, input-blind baselines, in-target references, pre-declared robust subset |
| Experimental rigor | 8/10 | Many controls. Limited by 30 radio sessions and no RIC |
| Statistical rigor | 8.5/10 | NB correction, Holm, pooled counts, cluster bootstrap. Causal wording now removed |
| O-RAN relevance | 6/10 | Only D_A comes from an O-RAN testbed. No xApp was deployed |
| Deployment relevance | 7/10 | Operational precision, alert units and latency decomposition are deployment quantities, but emulated or declared |
| Writing | 7.5/10 | Precise and plain. Dense in Sections VI-C and VI-G |
| Figures | 8/10 | One visual system, camera-ready. Fig. 2 still has small detail text |
| Tables | 7/10 | Correct and generated, but many and dense |
| References | 8/10 | 50 of 62 fully verified. 10 partial (no DOI exists. Metadata matches). 2 O-RAN specs unopened |
| Reproducibility | 9/10 | One-command regeneration, checksums, frozen manifest, public repository |
| Submission readiness | 7.5/10 | Clean build and honest scope. Needs the author items below |

---

## Output 9: GO / NO-GO

**GO.** The second pass (below) closed two of the three author items. The third, the
corresponding author, is left to you because you asked me not to touch the author block.

---

## Second pass, 2026-09-25 evening

You asked me to fix the open items except the authors and affiliations, to rebuild
Figure 2 from Downloads, and to change the title to one sentence with no colon.

| ID | Item | What I did | Evidence |
|---|---|---|---|
| S01 | Title had a colon | New title: "What Held-Out Accuracy Predicts About Deploying Intrusion Detection in O-RAN". Also changed in README, REPRODUCE.md, the response letter and this report. The running head keeps IEEE's "A. Ali and A. Ahmad: short title" form, which the class requires. | page 1 of `paper/main.pdf` |
| S02 | Figure 2 | Two candidates in Downloads (17:59 and 18:02). I used the 17:59 one, the second-last, because it looks less machine-made: grey panels, no title baked in, no "[DATA]" style headers. Rebuilt with the figure-rebuild skill. 14 icons cut out by `scripts/extract_figure2_icons.py`, palette sampled into `figstyle.tex` (gPanel to gPink). | `figures/source/fig2_candidate_a.jpg`, page 7 |
| S03 | Errors in that render | Seven fixed. Its own caption was drawn into the image. It fed the radio layer into the flow-only shared space. It drew "baseline floors" twice. "booster" and "tracking progression toward realism" were prompt text. Its "measured off-platform" brace covered untimed terms. Rung 03 left out D_C. The "how to read" box looked like a dashboard. All listed in the header of `paper/fig2_pipeline.tex`. | figure header comment |
| S04 | O-RAN specification versions | Both citations now point to public ETSI editions that I opened and read. ETSI TS 104 038 V4.1.0 (O-RAN.WG3.E2GAP-R003-v04.01) says the E2 interface "shall support latency requirements for near-real-time optimization, i.e. from 10 milliseconds up to 1 second". ETSI TR 104 106 V3.0.0 (O-RAN.WG11.Threat-Modeling.O-R003-v03.00) has clauses on threats to the Near-RT RIC and to xApps. The two sentences citing the budget now say "the O-RAN E2 specification". | `paper/references.bib` comments |
| S05 | 42 runs vs 30 sessions | New EXP-059 (`experiments/run_session_rule.py`). A gap rule of 90 to 105 s gives exactly 42 segments, all with one attack category, and each of the 30 five-minute sessions is a union of whole segments. So Fard et al.'s 42 runs are our sessions split finer, and 10 of our sessions hold two or three back-to-back runs. Merging them is the stricter choice for a group-disjoint split. One sentence added to Sec. IV-A, with macros. | `results/EXP-059/processed/session_rule.csv` |
| S06 | lambda_b had no source | Added Jin et al., CoNEXT 2013 (SoftCell, Crossref-checked). They expect several hundred flows per second at a heavily loaded LTE base station. Our 240,000 per hour is 67 per second, so our alert volumes are low, not high. The prevalence pi = 0.002 still has no source and stays "declared and swept". | Sec. V |
| S07 | Fixed hyperparameters | One sentence says why: tuning on the source rewards source-specific structure, and tuning on the target leaks it. | Sec. IV-C |
| S08 | Latency CDF | New EXP-060: the radio part of EXP-043 run again with `--keep-samples`, which saves all 20,000 per-call times per stage. My first attempt ran while I was building the paper on the same machine, and stages timed during that work came out about 5 times slower at the median. I discarded it (kept only as a record in `results/EXP-060/attempt1_concurrent_load/`) and re-ran it alone. The clean run gives medians 1.02 to 2.1 times EXP-043's (median 1.46). That is the same laptop in a different state, which the paper now says in one sentence. Fig. 11 is a real empirical CDF from the clean run. Table XXI and every latency number in the text still come from EXP-043, and the aggregation + ONNX p99 upper bound stays at most 0.36 ms, so no conclusion changes. | `results/EXP-060/raw/latency_samples.npz` |
| S09 | Figure 2 detail text too small | The rebuilt figure has no `\tiny` text. Its smallest text is about 6.2 pt at print size. | page 7 |
| S10 | Prose (humanize-latex) | Abstract, introduction, discussion, conclusion and limitations reworked. "therefore" cut from 18 to 5. The conclusion's three-semicolon sentence became six short ones. Two stale statements fixed: the contribution list still said the test "separates a predictive evaluation from a non-predictive one", and the introduction still spoke of two exporters. The reproducibility section now covers all three corpora. The British "licence" became "license". No citation, label or number changed except the new citations and macros listed here. | `git diff paper/` |
| S11 | Report style | Semicolons removed from this report (61), and a few banned words replaced. | this file |

### Issues still open

These are the issues left after both passes, most serious first.

1. **No live Near-RT RIC.** Latency is timed off-platform on one Windows host. The fix needs
   a Linux host with isolated cores (EXP-031). This is the most likely reviewer objection, and the paper already states it
   everywhere it matters.
2. **Exporter confound.** Zeek, Argus and NFStream segment flows differently. A common
   exporter would need the 5G-NIDD pcaps, which our copy does not have.
3. **Which 5G-NIDD label is right.** Only the dataset authors can say. Every D_B result is
   reported with and without the copies, so no conclusion depends on the answer.
4. **Radio sample size.** 30 sessions, 10 of them benign. Nothing short of new captures fixes this.
5. **Corresponding author e-mail.** IEEE Access expects `\corresp{}`. Left for you, as asked.
6. **Attack prevalence pi = 0.002** has no published source. It is declared and swept, and
   PPV is reported across 1e-4 to 0.5.
7. **Length.** 19 pages, 22 tables, 12 figures. Tables 4, 6, 13, 16 and 19 and Fig. 9 can move to
   a supplement if the editor asks.
8. **Two author names in the ICCCN record.** Crossref spells them "Nannou" and "Ur Rahman",
   the arXiv version "Nanou" and "Rahman, Muhammad Enayetur". Check IEEE Xplore before submission.
9. **Ten references without DOIs** (USENIX, ICML, NeurIPS, JMLR). None exists. Their metadata
   matches the proceedings records.
