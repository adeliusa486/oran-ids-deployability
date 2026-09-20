# O-RAN IDS Research Memory

> Permanent research memory. Read this and `configs/experiment_registry.yaml` before
> starting any phase. Never rewrite history here — append corrections instead.
> Last updated: 2026-09-20 (EXP-000)

---

## Scope (set by D-009, 2026-09-20)

**This is a Q1 journal paper, not a thesis.** Five core experiments plus the
statistical spine. Seven experiments are CUT; the cost of each cut is recorded in
`configs/decisions.md` D-009.

| ID | Experiment | Answers |
|---|---|---|
| X1 | In-distribution baselines on `D_A`, incl. majority-class floor | reference point |
| X2 | Cross-deployment transfer `D_A -> D_B` | **RQ1, the headline** |
| X3 | Radio / network / fusion ablation | the one novel claim we still own |
| X4 | Alert burden over a base-rate sweep | RQ2 |
| X5 | Latency p50/p95/p99 over a **swept** budget | RQ3 |

CUT: adversarial robustness, RIC fault injection, compression, longitudinal drift,
third external corpus, the systematic reporting survey (Table VIII **deleted**),
energy per decision, few-shot adaptation.

**Not negotiable despite the cut:** multiple seeds and CIs, run-disjoint splitting,
the trivial baseline, and reporting negative results. Scope reduction changes how many
questions we ask, never how carefully we answer the ones we keep.

## Current Phase

Phase 1 in progress. EXP-000 and EXP-001 complete. **Phase 2 is blocked** on the
claim-C5 route decision (D-008), which also revisits D-004.

## Current Experiment

EXP-001 complete (`PASS_WITH_LIMITATIONS`). **Next: D-008 must be settled**, then
either EXP-001c (re-extract from the raw archives) or EXP-002 (pipeline) depending on
the route chosen. Unblocked work meanwhile: B-007 dedup policy, B-008 label map,
B-010 split-protocol change, and reading P03/P04/P05 in full.

## Overall Status

The repository is a planning artefact with 0 lines of research *pipeline* code (two
verification scripts now exist) and four live, correctly failing guards. The manuscript
is structurally complete with every numeric value synthetic and machine-detectably
marked.

Gate A1 is **closed**: `D_A` is NetsLab-5GORAN-IDD, downloaded, checksummed and
profiled. The corpus is real and usable for RQ1, RQ2 and RQ3.

The binding constraint is now **claim C5**. The CU flow records and the DU radio
telemetry **cannot be joined at record level** from the published summary artefacts:
the network CSV carries no time column and shares no identifier with the radio layer.
C5's pre-registered failure criterion fired. Three routes exist (EXP-001 §5); the
recommended one reverses D-004 and costs a 16.4 GB download.

---

## Completed Experiments

### EXP-000 — Repository and literature reconstruction

- **Date:** 2026-09-20 | **Phase:** 0 | **Gate:** G0 → `PASS_WITH_LIMITATIONS`
- **Research question:** measured state of the repository; what the literature
  establishes; is gate A1 resolvable?
- **Baseline:** n/a (audit)
- **Method:** command-verified repository measurement; 9 searches, 13 page retrievals,
  provenance-tagged literature matrix
- **Dataset:** none consumed
- **Seeds:** n/a
- **Main result:**
  1. `src/` = 11 files, **0 non-blank lines**; all four guards fail, all correctly
  2. Gate A1 provisionally resolved: **NetsLab-5GORAN-IDD** has pcap + 22 radio KPIs + 6 attack classes, physical OAI O-RAN testbed, CC-BY-4.0
  3. The near-RT budget is a **range** (10 ms–1 s); P04 uses 10 ms and P05 uses 1000 ms, and both conclude feasibility
  4. P03 (IEEE CSR 2026) already published the in-distribution half of claim C5, on our candidate corpus
  5. P14 (2026) already published cross-domain IDS generalisation failure
- **Statistical result:** none computed, none appropriate
- **Unexpected:** the blocker was stale rather than hard — the corpus was published
  after the plan was written
- **Bugs:** B-001…B-006 (see below); B-006 fixed
- **Interpretation:** the contribution is smaller and more defensible than the draft
  implies — the *conjunction* of criteria, plus two open questions (the radio sign-flip
  under transfer, and the budget crossing point)
- **Effect on manuscript:** 8 claims need rescoping or deletion; see
  `docs/CLAIM_EVIDENCE_MATRIX.csv`
- **Files:** see `reports/experiments/EXP-000.md`
- **Git commit:** see Git Commit History below
- **Next step:** EXP-001

### EXP-001 — Artefact-level verification of `D_A`

- **Date:** 2026-09-20 | **Phase:** 1 | **Gate:** G1 -> `PASS_WITH_LIMITATIONS`
- **Research question:** does NetsLab-5GORAN-IDD contain what its descriptor implies,
  at the granularity our split design (A4) and windowing (A12) require?
- **Hypothesis (pre-registered):** H0-data -- the corpus exposes a device or run
  identifier, a usable timestamp, and CU-DU alignment sufficient to join the layers.
  **PARTIALLY FALSIFIED.** First two hold, third does not.
- **Baseline:** n/a (verification)
- **Method:** download from the Zenodo REST API, SHA-256, schema and label profiling,
  group-key feasibility, session recovery from the time axis, a four-level join test.
  Re-runnable: `scripts/exp001_profile_corpus.py`, `scripts/exp001_join_analysis.py`
- **Dataset:** `Lower_Layer_Data.db` (5.4 MB) and `Network_Dataset.csv` (227.2 MB)
- **Seeds:** n/a. Pre-registered parameters: session gap 300 s, window 16 records,
  5 folds, join tolerance 1.0 s
- **Main result:**
  1. **Radio layer:** 45,244 records, 25 cols, 0 exact duplicates, **1.0 Hz sampling**,
     span **52.96 days** (2025-05-09 to 2025-07-01), attack prevalence 76.43%
  2. **Network layer:** 1,723,817 flows, 26 cols, Zeek-derived, attack prevalence
     **90.09%**, **4.85% exact duplicate rows**, **6.94% duplicate Zeek uids**,
     and **no time column at all**
  3. **Run identifier recovered:** segmenting the radio time axis at a 300 s idle gap
     gives **30 sessions, 100% label-pure**. This is the group key
  4. **Device-disjoint splitting is NOT supportable**: `ue_id` has 9 values and one
     holds 60.8%; `cellid` is constant; `rnti` is reassigned. The manuscript's stated
     protocol must change to **run-disjoint**
  5. **CU/DU record-level join is IMPOSSIBLE** from these artefacts (L0 no shared
     identifier, L1 no shared time axis). Only an L2/L3 run- or category-level
     association via a hand-written mapping, with **zero exact string overlap**
     between the 19 radio subcategories and the 15 network attack types
  6. **A12 resolved cleanly:** 2,808 complete 16-record windows, **0.70% drop rate**
  7. **EXP-000's ~1.5 TB size figure was WRONG.** The whole record is **16.85 GB**
- **Statistical result:** none. Class-balance divergence between layers is large
  (dos differs by 26.3 pp, benign by 13.7 pp), so the layers are not aligned samples
  of the same events
- **Unexpected:** (a) a clean 53-day 1 Hz time axis, which upgrades Phase 12 drift
  analysis from speculative to grounded; (b) sessions are 100% label-pure; (c) a 600x
  asymmetry between the modalities (2,808 windows against 1.7 M flows); (d) Probe is
  labelled in both summaries but **no `Probe.zip` is published**
- **Bugs:** B-007 (duplicates and non-unique uids), B-008 (label vocabularies differ
  across layers), B-009 (Probe labelled but no raw capture), B-010 (manuscript's
  device-disjoint protocol is not supportable)
- **Interpretation:** "multi-modal" in this corpus means the layers were captured in
  parallel, not that they correspond record by record. The descriptor never claimed
  correspondence; we assumed it. That assumption was ours and it was wrong, which is
  precisely what the gate was written to catch
- **Effect on manuscript:** C5 held open pending D-008; split protocol changes to
  run-disjoint; window must be described as 16 seconds; the Probe discrepancy and the
  duplicate rates must appear in the data section
- **Files:** see `reports/experiments/EXP-001.md`
- **Git commit:** see Git Commit History below
- **Next step:** settle D-008

---

## Failed Technical Runs

| Run | Failure | Resolution |
|---|---|---|
| `make smoke` | `ModuleNotFoundError: No module named 'oran_ids'` at step 1/5 | **Expected** — skeleton state. With `PYTHONPATH=src` the import succeeds but `io.smoke_corpus` does not exist, so this is a missing interface, not a missing install. Not a defect |
| `pytest -q` | exit 5, no tests collected | **Expected** — 0 test files |
| `validate_results.py --strict` | exit 1, no results | **Expected** — the gate is doing its job |
| `yaml.safe_load` on the new registry | `ScannerError` at line 255 | **Real bug (B-006)**, fixed: an unquoted `x: 0.0` inside a prose value |

---

## Scientific Negative Results

None yet. No hypothesis has been tested.

Recorded here in advance so the category is not empty by neglect: EXP-000 produced
three results that are *unwelcome* but are not negative results in the experimental
sense — they are literature findings that narrow our claims (P03 pre-empting half of
C5, P14 pre-empting the novelty of RQ1, and P04 pre-empting an inference-latency story).

---

## Current Best Results

None. No experiment has produced a measurement.

**Every number currently in `paper/main.tex` is synthetic.** The draft banner
(`\synthdrafttrue`) is enabled and `check_no_placeholders.py` detects 15 placeholder
sites. Do not quote any of them anywhere, including in conversation.

---

## Current Baselines

Planned ladder (none implemented). The architectures are **subjects, not competitors** —
none is "ours", and all must be tuned equally.

| Level | Models |
|---|---|
| 1 trivial | majority class, random, single decision tree |
| 2 conventional | logistic regression, random forest, XGBoost, SVM |
| 3 deep | MLP, 1D-CNN, LSTM/GRU, autoencoder, transformer |
| 4 deployment | a lightweight model that can realistically meet the latency budget |
| 5 oracle | in-domain upper reference — **never** describable as deployable |

Added by EXP-000: **I13**, a non-learned cross-layer consistency baseline (from P24).

---

## Current Dataset State

| Role | Corpus | Status |
|---|---|---|
| Source `D_A` | **NetsLab-5GORAN-IDD** | **VERIFIED (partial) by EXP-001.** Downloaded, checksummed, profiled. Radio: 45,244 records, 1 Hz, 53-day span, group key `session` (n=30, 100% label-pure), 2,808 windows at 0.70% drop. Network: 1,723,817 Zeek flows, **no time column**, 4.85% duplicate rows, 6.94% duplicate uids, `src_ip` n=318. **CU/DU record-level join impossible.** Whole Zenodo record is **16.85 GB**, not 1.5 TB. Original landing-page notes: DOI `10.1109/IEEEDATA.2025.3614167`; Zenodo 18923275; Kaggle `10.34740/kaggle/ds/7416931`; CC-BY-4.0. Raw `.pcap` at O-CU + 22 PHY/MAC radio metrics from O-DU over E2 + Zeek logs. 6 classes. OAI testbed at UCD: 1 O-CU, 2 O-DU, 1 O-RU, Dell Precision 7920, 2 physical UEs. **~1.5 TB total**; `Network_Dataset.csv` 227 MB, `Lower_Layer_Data.db` 5.4 MB |
| Target `D_B` | **5G-NIDD** | resolved, not downloaded. DOI `10.21227/xtep-hv36`. Raw pcapng published (BS1 2.2 GB, BS2 1.45 GB) — this is what makes the A3 single-exporter control feasible. No radio KPIs. `group_key: src_ip`. `role: transfer_only` |
| External | **O-RAN E2SM-KPM DoS dataset** | candidate for Phase 13. `10.5281/zenodo.21198102`, MIT, 69.8 MB, University of Regina. Zenodo record has no description; feature overlap unknown |

**Resolved by EXP-001:** record counts, label columns, timestamps, run identifiers,
class balance and duplicate rates are all now measured and recorded in
`configs/corpora/d_a.yaml`.

**Still unknown:** whether an L1 time join is recoverable from the raw per-category
archives (EXP-001c), and the exact Zeek/Argus feature intersection with `D_B`.

---

## Current Literature Findings

`docs/literature/LITERATURE_MATRIX.csv` — 25 entries, 32 fields.
**0 full texts read.** 11 abstracts/landing pages, 4 search-snippet-only, 9 title-only.

The five that matter:

1. **P03** Fard, Komarov, Wunder, IEEE CSR 2026 — seven architectures, run-disjoint,
   ten seeds, on *our candidate corpus*. Radio ≥ flows in distribution. No transfer, no
   latency, no resources, no alert burden, no calibration, no robustness. Reports
   27–46% DoS→Benign confusion from windowed aggregation.
2. **P04** Obiuwevwi et al., IEEE ICCCN 2026 — real FlexRIC xApp, C-exported models,
   1–5 µs inference, < 4 ms end-to-end, **p95 only**, budget `B = 10 ms`.
3. **P05** unverified (HTTP 403) — same corpus, ~600–850 ms, budget `B = 1000 ms`.
4. **P13** Axelsson, ACM TISSEC 2000 — the base-rate result. 26 years old. Our
   Criterion 2 reasoning is his; only the O-RAN quantification is ours.
5. **P14** Hakim, Uddin, Anis, 2026 — cross-domain IDS failure on IIoT. Also reports
   that the evaluation protocol can **reverse** which target looks harder.

**Supported novelty statement** (`GAP_MATRIX.md` §5): the *conjunction* of transfer,
alert burden and swept-budget tail latency for the same artefacts under one protocol.
Nothing stronger.

### Pass 2 (2026-09-20, during EXP-001) — one gap WITHDRAWN, one quantified

- **G4 "no O-RAN IDS study reports p99" is FALSE and is withdrawn.** P05 reports
  **p99 ~140 ms** for its selected LSTM. Never write "no prior work reports tail
  latency".
- **G3 is now quantified by a single number.** That same 140 ms **passes** a 1000 ms
  budget by 7x and **fails** a 10 ms budget by 14x. One measurement, two opposite
  verdicts, decided only by which end of the O-RAN 10 ms - 1 s range an author picks.
  I11 (sweep `B`) is therefore the strongest methodological contribution available.
- **P03 full text supplies the method D-008 route (a) needs.** They align the layers by
  **run-relative timestamps from the RAW per-category archives**, not the summary CSV;
  DoS traces without telemetry timestamps get time from the sample index at 1 Hz;
  sliding windows W in {5,10} s, stride 2 s; 68-72 network and 44 radio features over
  **42 runs**. EXP-001's "join impossible" finding applies to the PUBLISHED SUMMARIES
  ONLY. The join exists in the raw data and has been done.
- **P03 in-distribution reference, to cite rather than re-derive:** radio-only ROC-AUC
  0.925-0.961 against network-only 0.827-0.851, a radio advantage of 8.5-11.7 points.
- **P03 corroborates our small-sample warning.** Stacked fusion is unstable at 42 runs:
  ROC-AUC sd +/-0.171 to 0.182 for TCN and Transformer. **A fusion "gain" smaller than
  ~0.17 ROC-AUC is not a gain.**
- **P03's authors name our RQ1 as their open question:** confirming whether their
  patterns transfer beyond this testbed needs paired captures from independent
  deployments. G2 strengthens to Moderate-Strong.

---

## Important Decisions

Full register: `configs/decisions.md`.

| ID | Decision | Status |
|---|---|---|
| D-001 | Adopt NetsLab-5GORAN-IDD as `D_A` (plan option A1-b) | decided, provisional |
| D-002 | `D_B` = 5G-NIDD, transfer-only, enforced in code | decided |
| D-003 | `source` normalisation primary; report all three modes | decided |
| **D-004** | **Published features on both sides; A3 single-exporter control NOT applied** | **DECIDED 2026-09-20.** Mitigations M1 and M2 are mandatory |
| **D-005** | **Track C at Level 2: real Near-RT RIC + synthetic E2 load, on a Linux host** | **DECIDED 2026-09-20** |
| D-006 | Report p50/p95/p99; never mean alone; per-stage breakdown | decided |
| D-007 | The floor experiment runs before any model is timed | decided |

New improvements from EXP-000: **I11** sweep `B` over [10 ms, 1 s]; **I12** test
ordering stability across evaluation protocols; **I13** add a non-learned cross-layer
baseline; **I14** per-stage latency breakdown; **I15** widen or bound the threat model.

---

## Known Bugs

| ID | Severity | Description | Owner phase |
|---|---|---|---|
| B-001 | cosmetic | README says stubs raise `NotImplementedError`; `src/` is empty `__init__.py` files | 5 |
| B-002 | structural | the `\input`-only number contract has no mechanism | 18 machinery, build early |
| B-003 | blocking-later | `Makefile` references non-existent `scripts/check_imports.py` | 5 |
| B-004 | environment | xgboost, onnx, onnxruntime, scapy, hypothesis not installed | 3 |
| B-005 | environment | no conda on PATH; `environment.yml` assumes it | 3 |
| B-006 | fixed | registry YAML parse error (unquoted `x: 0.0`) | closed 2026-09-20 |
| B-007 | data | `Network_Dataset.csv`: 83,635 exact duplicate rows (4.85%) and 119,551 duplicate Zeek `uid`s (6.94%). Dedup and uid-namespacing policy must be declared **before** splits are drawn, or one connection can land in both train and test | 2 |
| B-008 | data | Label vocabularies differ across layers (`dos`/`DoS`, `web`/`Web Attacks`). Commit a canonical mapping table | 2 |
| B-009 | provenance | Probe is labelled in both summaries (8,445 radio, 183,293 network) but no `Probe.zip` is published. Probe features cannot be re-extracted from raw packets | report in the paper |
| B-010 | methodology | The manuscript states device-disjoint splitting for `D_A`; the corpus cannot support it at 5 folds. Change to run-disjoint | 2 |

---

## Known Limitations

1. **Track C runs at Level 2** (D-005): a real Near-RT RIC with a **synthetic** E2
   load generator, no gNB, on a separate Linux host. Real-RAN arrival process and
   over-the-air effects are out of scope and belong in Limitations. Permitted phrasing:
   "measured on a real Near-RT RIC under synthetic E2 load". Never "real deployment".
2. **The A3 single-exporter control is NOT applied** (D-004, decided 2026-09-20).
   `Δ_F1` therefore conflates deployment shift with Zeek-vs-Argus exporter differences
   and is an **upper bound** on true deployment shift, not an estimate of it. Every
   statement of `Δ_F1` must carry that qualifier. Mitigations M1 (measure the confound
   on `D_B`) and M2 (intersection sensitivity) are mandatory, not optional.
3. **Literature depth.** 0 full texts. Absence claims are provisional.
4. **P05 unretrievable** (HTTP 403) — one of only two latency comparators.
5. **Energy (C15) is not measurable** with the planned method (A8), and no retrieved
   source measures it either. Recommend accepting I9 and dropping the column.
6. **Table VIII (C13) has no underlying study.** `reports/literature_audit.md` is **not**
   that study — a keyword search has selection bias by construction.
7. **Two corpora only**, so "cross-deployment" means one pair plus its reverse.

---

## Open Questions

1. ~~Does `D_A` expose a usable per-record device or run identifier?~~ **ANSWERED
   (EXP-001):** not a device one, but `session` (n=30, 100% label-pure) works.
2. ~~Can CU flow records be joined to DU radio telemetry?~~ **ANSWERED (EXP-001): NO**,
   not from the published summary artefacts. Open follow-up: can an L1 time join be
   recovered from the raw per-category archives? *(EXP-001c, blocks C5)*
3. ~~What is `D_A`'s class balance and duplicate rate?~~ **ANSWERED (EXP-001):** radio
   76.43% attack with 0 duplicates; network 90.09% attack with 4.85% duplicate rows.
4. What windowing did P03 use, and does ours reproduce their 27–46% DoS→Benign confusion?
5. Does the `Δ_F1` ordering across architectures survive a change of evaluation protocol?
   *(I12, raised by P14)*
6. At what budget in [10 ms, 1 s] does each architecture cross out of deployability?
   *(I11 — this may be the paper's most useful single figure)*
7. Does the P23 external corpus share enough features with our shared space to be usable?
8. Is our 24-feature shared space actually computable from both corpora with one exporter?

---

## Standing Tasks

| Task | Raised | Status |
|---|---|---|
| **Re-mine `plan.zip` / `IMPLEMENTATION_PLAN.md` for paper-strengthening items once the experimental phases are done.** Owner's instruction, 2026-09-20. First check (2026-09-20): `plan.zip` holds only `IMPLEMENTATION_PLAN.md` (md5 identical to `docs/IMPLEMENTATION_PLAN.md`, already mined in EXP-000) and `bootstrap_repo.sh`, which creates the skeleton already present. **No unmined content.** The plan's sections 16-17 (figure and table plans), 21 (reviewer-risk audit) and 22 (final improvement priorities) are the parts not yet exploited and are the natural source of strengthening material in Phases 17-22 | owner | open |
| Retrieve the P05 PDF (HTTP 403 so far). Its numbers are used in reasoning and must not be cited until the PDF is in hand | EXP-000 | open |
| Execute or delete Table VIII / claim C13 (plan A9) | EXP-000 | open |

## Manuscript Changes Required

Tracked in `docs/CLAIM_EVIDENCE_MATRIX.csv`. **0 of 15 claims are currently established.**

Priority order:

1. Replace the `D_A` platform-paper citation with the real corpus (after EXP-001)
2. Rescope C5 to the transfer half; cite P03 for the in-distribution half
3. Re-express C9 and Eq. (7) against a swept `B`
4. Promote C10 to load-bearing; require a per-stage breakdown
5. Delete the `T_max < 250` formulation (C11, plan A7)
6. Execute or delete Table VIII (C13)
7. Drop the energy column (C15, plan I9)
8. Widen or explicitly bound the threat model (I15)
9. Add P03, P04, P05, P06, P10, P11, P14 to related work
10. Cite the IoT-signalling-overload claim in the Introduction, or remove it

---

## Figures Completed

None. 15 planned; none generated; no generator exists.

## Tables Completed

None. 12 planned; none generated; no generator exists. **B-002:** no
`\input{tables/generated/*}` directive exists in `main.tex`, so the "no number reaches
the paper except through a generated table" contract currently has no mechanism.

---

## Git Commit History

| Commit | Description | Pushed |
|---|---|---|
| `6d657fe` | Repository skeleton (pre-existing) | yes |
| `8c600de` | EXP-000: repository and literature reconstruction | **yes** — `6d657fe..8c600de main -> main`, confirmed by Git; `origin/main` at `8c600de` |

---

## Next Experiment

**EXP-001 — Resolve and verify the source corpus at artefact level.**

Steps, in order:

1. Download the smallest sufficient `D_A` subset (`Network_Dataset.csv` 227 MB,
   `Lower_Layer_Data.db` 5.4 MB) and record SHA-256 for every file in `data/provenance/`
2. Enumerate columns, dtypes, null rates, label values, class counts
3. Identify candidate group keys; test cardinality and disjointness for 5 splits
4. Test the CU–DU join and quantify the time-alignment error
5. Measure duplicate rate and exact-duplicate-across-class rate
6. **Settle D-004 before computing any feature**
7. Read the descriptor PDF in full
8. Retrieve P05 and read P03/P04 in full

**Failure criteria, pre-registered:** no usable group key → D-001 reverses and we fall
back to plan option A1-c (packet-only, C5 dropped). CU–DU join impossible → C5 is
withdrawn, not weakened.

---

## Do Not Repeat

- **Do not quote any number from `paper/main.tex`.** All 15 are synthetic.
- **Do not cite a platform paper as the provenance of a dataset.** That is the exact
  error gate A1 identifies.
- **Do not use `reports/literature_audit.md` as evidence for C13.** It is a targeted
  keyword search with selection bias by construction, not a systematic review.
- **Do not claim** "first", "first comprehensive", "state of the art", "unique" or
  "unprecedented". P06, P08 and P09 precede us on O-RAN IDS; P14 and the NIDS literature
  precede us on cross-dataset transfer; P13 (2000) precedes us on base rates; P04 and
  P05 precede us on xApp latency; P11 precedes us on O-RAN adversarial ML.
- **Do not present cross-domain IDS failure as a discovery.**
- **Do not assert a single near-RT budget.** It is a 10 ms – 1 s range and the choice
  decides the verdict.
- **Do not build an inference-cost latency story.** P04 measured 1–5 µs in a real xApp.
- **Do not describe an emulated measurement as a real deployment.**
- **Do not select a baseline, threshold, seed or split after seeing target results.**
- **Do not re-search gate A1 as though it were open.** It is **closed** — `D_A` is
  verified at artefact level.
- **Do not describe `D_A` as record-level multi-modal.** The layers were captured in
  parallel; they do not correspond row by row, and from the published summaries they
  cannot be joined at all.
- **Do not state device-disjoint splitting for `D_A`.** It is not supportable (B-010).
  The protocol is run-disjoint, on the recovered `session` key.
- **Do not quote the ~1.5 TB corpus size.** It was wrong. The record is 16.85 GB.
- **Do not draw a split on the network layer before the dedup and uid-namespacing
  policy is declared** (B-007) — 6.94% of Zeek `uid`s are duplicated.
- **Do not claim that no prior work reports p99.** P05 reports ~140 ms. Gap G4 is
  withdrawn as false.
- **Do not call a fusion improvement a gain unless it exceeds ~0.17 ROC-AUC.** P03
  measured that much seed-to-seed variance on this corpus at this sample size.
- **Do not say the modalities cannot be joined, full stop.** They cannot be joined from
  the published summaries. Prior work joined them from the raw archives.

---

## Critical Warnings

1. **`D_B` must be consumed exactly once, at final evaluation.** This is currently a
   process claim. Until `TargetCorpusGuard` exists and logs every access (A11), the
   claim is unauditable and must not appear in the paper as though it were enforced.
2. **Normalisation fitted on `D_A` only.** Fitting on `D_B` is transductive and
   contradicts the protocol the paper describes (A2).
3. **One exporter, one version, both corpora** — or the headline `Δ_F1` conflates
   deployment shift with exporter differences and the result is gone in one reviewer
   sentence (A3). D-004 is unresolved and this is the reason it is blocking.
4. **A negative result is preserved, diagnosed and reported.** Never change a seed,
   split, baseline, threshold, metric or exclusion rule to make a result favourable.
5. **The five architectures are subjects, not competitors.** Under-tuning any of them
   inflates the headline gap and is the first thing a reviewer will attack.

---

# PHASE 0 COMPLETE

**Date:** 2026-09-20
**Phase:** 0 — Repository and literature reconstruction
**Experiments:** EXP-000

## What We Proved

- The repository contains **0 non-blank lines of research code** and four guards that
  all fail, all correctly. Established by command output, not by reading the README.
- `paper/main.tex` contains exactly **15** machine-detectable synthetic placeholder
  sites. The honesty mechanism works.
- **NetsLab-5GORAN-IDD exists and is citable** (IEEE Data Descriptions 2025,
  CC-BY-4.0): raw pcap at the O-CU, 22 DU radio KPIs over E2, six labelled attack
  classes, physical OpenAirInterface O-RAN testbed. Gate A1 has a route.
- The O-RAN near-real-time control loop is specified over **10 ms to 1 s**, and two
  prior studies reach positive deployability verdicts five orders of magnitude apart by
  picking opposite ends of it.

## What We Observed

- The blocker was **stale, not hard**. The corpus was published after the plan was
  written. A blocker that has not been re-searched recently may simply be out of date.
- Adopting the corpus means **inheriting prior work on it** (Fard et al., IEEE CSR 2026)
  and giving up half of claim C5. The plan's decision table did not anticipate this cost
  of the cheap option.
- The A3 single-exporter control was believed to collide with reality: `D_A` raw at
  ~1.5 TB against `D_B`'s ~3.65 GB. **CORRECTION 2026-09-20 (EXP-001): the ~1.5 TB figure recorded by EXP-000 was WRONG. It came from a page summary, not from the record. The Zenodo API gives the whole record as 16.85 GB: five pcap zips totalling 16.40 GB (Benign 5.94, DoS 3.47, DDOS 3.09, BruteForce 3.32, Web 0.59) plus 0.44 GB of summary artefacts.** `D_A` raw is ~4.5x `D_B`, not
  ~400x. Appended rather than rewritten, per this file's own rule.

## What Failed Technically

Nothing in the experiment. One artefact defect found and fixed: **B-006**, an unquoted
`x: 0.0` in a prose value broke `configs/experiment_registry.yaml` parsing. Fixed and
re-validated with `yaml.safe_load`.

The four failing repository guards are **not** technical failures — they are guards
correctly refusing an empty project.

## What Failed Scientifically

Nothing was tested, so nothing failed. But three literature findings **narrow the
paper**, and they are recorded as findings rather than as inconveniences:

1. The in-distribution half of C5 is prior work (P03), on our own candidate corpus.
2. Cross-domain IDS transfer failure is published for IIoT in 2026 (P14), so RQ1 cannot
   be framed as a discovery.
3. Inference cost is not where the latency is (P04: 1–5 µs in a real xApp), so C10
   becomes the load-bearing latency claim.

## Strongest Baseline

None established. The ladder is specified and unimplemented.

## Strongest Proposed Result

None. No measurement exists.

## Unexpected Finding

**The two latency comparators contradict each other, and the contradiction is a
contribution opportunity.** P04 assumes `B = 10 ms`, P05 assumes `B = 1000 ms`, both
conclude feasibility. Sweeping `B` over the specified range and reporting each
architecture's crossing point converts an arbitrary threshold into the quantity an
operator actually needs. This may become the paper's most useful single figure.

## Literature Findings

25 entries, 32 fields, every cell provenance-tagged. **0 full texts read**; 11 abstracts
or landing pages, 4 search-snippet-only, 9 title-only. One retrieval blocked (HTTP 403)
and it is one of only two latency comparators.

## New Literature Gap

Primary, and the only one graded strong: **no retrieved study reports cross-deployment
transfer, operational alert burden and tail latency for the same artefact.** This rests
on a coverage *pattern* across twelve studies, not on any single source, which is why it
survives the shallow-reading caveat.

Secondary: the near-RT budget is treated as a constant when it is a range, and the
choice decides the verdict.

## New Limitation

Track C cannot run on this host (Windows; the methodology needs Linux CPU isolation).
D-005 is now unavoidable rather than deferrable.

## Manuscript Claims Changed

C5 rescoped, C9 rescoped, C10 promoted to load-bearing, C11's `< 250` formulation
marked for deletion, C15 recommended for withdrawal, C13 unevidenced and explicitly
barred from citing this phase's literature audit as support. `docs/claims.yaml` updated;
C10, C11 and C15 added to it so the Phase 20 audit covers the whole manuscript.

## New Figures

None.

## New Tables

None.

## Git Commits

`8c600de` — EXP-000: repository and literature reconstruction (27 files).

## GitHub Status

Pushed. `6d657fe..8c600de main -> main`, confirmed by Git. `origin/main` is at
`8c600de`.

## Next Phase

**Phase 1 / EXP-001** — artefact-level verification of `D_A`. Gate G1 cannot pass on a
landing page. **D-004 must be settled inside EXP-001, before any feature is computed.**

## Critical Warnings

1. **The gate is provisionally, not actually, resolved.** Nothing has been downloaded.
   Record counts, label columns, group keys, timestamps and CU–DU alignment are all
   unknown, and every one of them blocks the split design.
2. **If the CU–DU join cannot be demonstrated, C5 is withdrawn, not weakened.** Written
   down now, before the data is seen, so the decision cannot be made after the fact.
3. **Do not treat `reports/literature_audit.md` as a systematic review.** It is a
   targeted keyword search and over-samples work that mentions the search terms.
4. **Do not let the contribution quietly re-inflate.** Three of the four things the
   draft treats as findings are separately known. What is ours is the conjunction, plus
   two open questions.
