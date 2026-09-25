# O-RAN IDS Research Memory

> ## START HERE (new session)
>
> **Read this file top to bottom, then `configs/decisions.md`, then
> `reports/SESSION_REPORT.md`. Then run `python -m experiments.final_validation`
> to see the live state rather than trusting this file.**
>
> ### Where we are, 2026-09-20 (campaign 2)
>
> Repository on `main`, working tree clean. Campaign 2 has run phases 24-31 and
> 36. `pytest` passes 50 tests **from a bare `pytest`**, which it did not before.
>
> ### The four things that changed the paper this campaign
>
> **1. RQ1 is unblocked and running.** `D_B` is verified and the shared feature
> space is built, committed and unit-tested. EXP-026 evaluates transfer in both
> directions. This was the paper's missing headline.
>
> **2. We were about to publish a preprocessing bug as the headline (D-015).**
> The handover note in this very file proposed mapping `src_bytes <-> SrcBytes`.
> Zeek's `src_bytes` is application **payload** (median 0, because both corpora
> are dominated by floods and scans that carry none); Argus's `SrcBytes` is
> header-inclusive (median 84). That mapping would have collapsed every
> architecture on the target, consistently and significantly, and looked exactly
> like the generalisation failure we set out to find. The real counterpart is
> `src_ip_bytes`, at 40 vs 42 bytes per packet. **Caught by twenty minutes of
> label-blind measurement before any transfer metric existed.**
>
> **3. Our own "6x deployment PPV spread" does not survive re-estimation
> (D-018, bug B-E).** PPV is violently non-linear in FPR near zero, and EXP-004
> averaged PPV *across folds*. Any fold with FPR = 0 contributes PPV = 1.000.
> XGBoost drew six such folds out of forty; the MLP drew none; and the published
> ranking is almost exactly that count. Same data, three estimators: pooled
> **1.40x**, median 1.73x, mean **13.18x**. The mean is what was published.
> **Pooled counts are primary from now on.**
>
> **4. Two of our five gaps were closed by other people, in July and August
> 2026 (EXP-036).**
> - **Abraheem & Edhirig (WAUJPAS, 7 Aug 2026)** run bidirectional transfer
>   between **the same two corpora**, with 15 harmonised features to our 15
>   shared concepts. Gap G1 closed. **No "first cross-deployment evaluation"
>   claim is available.**
> - **Obiuwevwi et al. (arXiv:2607.01583, Jul 2026)** measure AI inference in a
>   real OAI+FlexRIC RIC: 1-5 us logreg, 10-25 us MLP. Gap G5 closed.
>
> ### What survives, stated narrowly
>
> - Corpus precision ~0.93; **pooled** deployment PPV 0.0055-0.0077. A **132x**
>   gap at the declared base rate, and the detectors are operationally
>   **indistinguishable** (1.08-1.40x) at every base rate from 1e-4 to 0.5.
> - **FPR is not a stable property of these detectors**: 0.000 to 0.890 across
>   group-disjoint folds. Fold composition explains little of it (max R^2 0.36).
>   Any single-number FPR for this corpus is close to meaningless.
> - Random-split inflation (+0.09 to +0.17) tracking model flexibility, with the
>   trivial floors gaining nothing. Unchanged and still the cleanest result here.
> - Extraction dominates inference **even after a 12x speedup** (EXP-030).
>
> ### THE NEXT TASKS, precisely
>
> **All campaign-2 experiments are COMPLETE.** Validation, 2026-09-21:
> **20 PASS, 1 WARN, 2 BLOCKED, 0 FAIL**. Always re-run
> `python -m experiments.final_validation` rather than trusting this line.
>
> 1. **Manuscript. DONE.** Zero synthetic values remain, the draft banner is
>    replaced by an accurate pre-submission status note, and the ablation
>    section is deleted rather than filled (C5 is WITHDRAWN). Figures 1 and 2
>    are TikZ source with selectable text and are audited against the results
>    (**D-020**). Run `python scripts/check_withdrawn_claims.py` before and
>    after every editing pass.
> 2. **EXP-029 part B** — the only experiment left unrun. Does `src_ip` grouping
>    SCORE like grouping by attack type? Part A predicts it should not, because
>    the alignment is only 20.6% of the oracle. Until it runs, that is a
>    prediction and is labelled as one.
> 3. **Re-run the network leakage audit at n=20.** D-019 promoted the network
>    layer to co-primary but D-013's n=5 constraint still stands, so no
>    network-layer claim may carry a significance mark yet.
> 4. **BLOCKED and staying blocked here:** real RIC runtime and CPU/RAM under
>    load. Both need a Linux host with isolated cores. See EXP-031 — the blocker
>    is one uninstalled Windows feature plus a reboot, so it is cheap to close
>    later and should not be designed around permanently.
>
> ### Do not repeat the mistakes already made
>
> - **Do NOT `git stash -u` while a background job is running.** It removes
>   untracked output directories out from under an open file handle. The job
>   keeps its handle and keeps writing to the now-orphaned file, so **output
>   stops appearing at that path and the job looks dead**. `stash pop` then
>   restores the log frozen at the moment of the stash, which makes it look
>   deader.
>   **CORRECTION, and it matters:** the run was *not* killed. It completed all 20
>   seeds normally. What went wrong next was worse and was entirely mine —
> - **`Get-Process python` is NOT a liveness check on this host.** The Windows
>   Store Python does not run as `python.exe`, so the filter matched nothing and
>   reported "no python processes" while three were running. On that evidence a
>   duplicate transfer run was started, and for eleven minutes **two processes
>   wrote the same output paths** — the exact D-014 collision, self-inflicted.
>   Use this instead, and read the command line:
>   ```powershell
>   Get-CimInstance Win32_Process -Filter "Name LIKE '%python%'" |
>     ForEach-Object { "{0} {1} {2}" -f $_.ProcessId, $_.CreationDate, $_.CommandLine }
>   ```
> - **Never "restart" a job without first confirming the original is dead by its
>   command line**, and never let two runs share an output path or a log path.
>   Two writers with `>` on one log produced an interleaved file that told a
>   coherent-looking but false story about progress.
> - Do NOT average a non-linear functional of a rate across folds. **Pool the
>   counts.** See D-018 -- it cost us a published finding.
> - Do NOT trust a handover table. D-015 was written in this file as settled fact
>   and two of its eight rows were wrong.
> - Do NOT dedup on a column subset and assume alignment with `load_network`.
>   Subset dedup collapses 1,640,182 rows to 888,367.
> - Do NOT use `bootstrap_ci` below n=30 (D-012). Use t-intervals. 20 split seeds.
> - Do NOT `\input` a LaTeX table body inside a `tabular`. Generators emit
>   complete tabular environments.
> - Do NOT let two runs write the same output path (D-014).
> - Do NOT quote any `\syn{}` number from `paper/main.tex`.
> - Do NOT describe any latency figure as a conformance result. **All are
>   EMULATED**; Track C is BLOCKED (EXP-031) and the blocker is one uninstalled
>   Windows feature, not the absence of hardware.
> - Do NOT write "due to deployment shift". Every `Delta_F1` spans an independent
>   deployment **and** an independent exporter (Zeek vs Argus). Abraheem &
>   Edhirig measured a source classifier at **0.993** balanced accuracy on the
>   shared features, which quantifies how separable the two corpora are.

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

**First real measurements exist** (radio layer, group-disjoint, 5 split x 2 model seeds).
Full write-up: `reports/experiments/EXP-002_004_005.md`.

| Finding | Number |
|---|---|
| Leakage: random split inflates macro-F1 | **+0.093 to +0.168** (n=20), significant for **all 6** non-trivial models after Holm, d_z 0.78-1.35 |
| Leakage tracks **model flexibility** | tree +0.168 > xgboost/hgb +0.14 > rf/mlp +0.11 > logreg +0.093 > trivial ~0 |
| Best group-disjoint macro-F1 | **0.853** (rf), 0.849 (mlp), 0.844 (hgb) -- indistinguishable |
| Majority-class floor | **0.434** macro-F1 -- quote this next to every other F1 |
| Corpus precision vs deployment PPV | **0.926-0.933 -> 0.036-0.219** at pi = 0.002 (n=20). Corpus precision is flat within 0.007 across all five detectors; the operational metric separates them 6x |
| Alert volume | **53,000-63,000/hour**, 1.3-1.5M/day, large majority false |
| PPV = 0.5 | **unreachable at any threshold for 4 of 5 detectors** (n=20). Only rf and logreg reach it, at recall 0.418 and 0.189 |
| Latency p99 (EMULATED) | tree 4.76, logreg 6.51, xgboost 7.29, mlp 8.17, hgb 94.6, rf 378 ms |
| Platform floor p99 | 0.103 ms -- two orders below the tightest budget, so not an artefact |
| Conformance at B = 10 ms | **4 of 6** architectures, fastest is a plain decision tree |

**Still true:** every number in `paper/main.tex` is synthetic. None of the above has
been written into the manuscript yet.

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
| Target `D_B` | **5G-NIDD** | **DOWNLOADED AND VERIFIED 2026-09-20.** `Combined.csv`, 1,215,890 flows, 52 Argus columns, **60.71% attack** (8 attack types + benign), 1 duplicate row, **no IP/port columns**. SHA-256 in `data/provenance/d_b_files.json`. Obtained free from the Finnish national repository under CC BY 4.0. Original landing-page notes: DOI `10.21227/xtep-hv36`. Raw pcapng published (BS1 2.2 GB, BS2 1.45 GB) — this is what makes the A3 single-exporter control feasible. No radio KPIs. `group_key: src_ip`. `role: transfer_only` |
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
| D-012 | n raised 5 -> 20; paired t-intervals, not bootstrap below n=30 | decided |
| D-013 | Network-layer audit stays n=5, directional cross-check only (src_ip grouping confound) | decided |
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

### The two schematics (Figs. 1-2), D-020

`paper/fig1_architecture.tex` and `paper/fig2_pipeline.tex`, TikZ source, both
`\input{figstyle}` so the palette and the idioms cannot drift apart. Every word
is set in LaTeX and is selectable; the pictograms are crops of the source
renders, regenerated by `scripts/extract_figure_icons.py` from committed
sources in `figures/source/`.

They started as image-model renders and the renders **asserted three things the
work does not support**: three equivalent measurement markers where the third is
emulated with no RIC in the path, telemetry flowing out of the detector into the
feature space rather than into it, and a "measured latency" stage over an
offered-load curve for a sweep that was never run. All three are corrected, and
each correction is written into the figure's header comment. The live-RIC arm is
hatched and labelled NOT EXECUTED rather than removed.

**An image model draws the claim you asked for, whether or not you have the
evidence.** Audit a figure against the results before drawing it.

### The three plots

All generated by `analysis/make_figures.py`, no hand-edited values:
`fig_leakage_radio`, `fig_alert_burden`, `fig_latency_budget` (PDF + 400 dpi PNG).
Palette validated (worst all-pairs CVD dE 9.2); every series carries a marker and
line style as well as a hue, so they survive greyscale printing.

Three defects were caught by **rendering them and looking**, not by assuming:
colliding direct labels, a log axis over half a decade printing false precision, and
clipped reference-line labels. All fixed.

## Tables Completed

Five, all generated by `analysis/make_tables.py` with a provenance header naming the
source file and git commit: `corpora`, `leakage_radio`, `alert_burden`,
`latency_budget`, `ppv_crossings`.

**B-002 is half-closed:** the generator now exists. The remaining half is adding the
`\input{tables/generated/...}` directives to `main.tex` and deleting the synthetic
values they replace.

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

---

# SESSION COMPLETE — 2026-09-20

**Phases executed:** 0, 1, 2, 6, 9, 15, 19, 22, 23 (scope cut to a Q1 paper by D-009)
**Commits:** 22, all pushed to `origin/main`
**Final validation:** 11 PASS, 1 WARN, 4 BLOCKED, **0 FAIL**

## What We Proved

1. **A random split inflates macro-F1 by +0.093 to +0.168** on this corpus.
   Significant for all six non-trivial models after Holm correction, n=20,
   d_z 0.78–1.35.
2. **Leakage tracks model flexibility.** Single tree +0.168 > boosted +0.14 >
   rf/mlp +0.11 > logreg +0.093 > trivial baselines ~0. The trivial baselines
   showing nothing is the control that identifies the mechanism as memorisation.
3. **Corpus precision does not distinguish these detectors; operational
   precision separates them sixfold.** Corpus P flat within 0.007 (0.926–0.933);
   deployment PPV 0.036–0.218 at π=0.002, at 53k–63k alerts/hour.
4. **PPV = 0.5 is unreachable at any threshold for four of five detectors.**
   Score saturation under a group-disjoint split means the operator's only
   runtime control barely works. Not visible in accuracy, F1 or AUC.
5. **The near-RT conformance verdict is an authoring choice.** At 1 ms nothing
   conforms, at 5 ms only a decision tree, at 10 ms four of six, at 1 s all.
   Platform floor p99 is 0.103 ms, so this is not a measurement artefact.
6. **Feature extraction is 7–39× inference** for the architectures that meet a
   10 ms budget. Inverted for rf and hgb, so the claim is architecture-dependent.

## What Failed Technically

- Exporter parsed DLT_LINUX_SLL captures as Ethernet, silently producing 5,851
  fictional flows where 908 real ones existed. Caught by the pilot. Fixed in 1.1.0.
- Dedup policy dropped 35,916 real multi-transaction rows (98% benign). Caught by
  inspecting the data rather than by a test. Fixed.
- `\input` inside a `tabular` does not work in this TeX install. Generator now
  emits complete tabular environments; `.gitattributes` pins LF so the fix
  survives checkout.
- **My own statistics were wrong.** n=5 percentile bootstrap CIs reported four
  significant effects a paired t-test does not support. Withdrawn, cause
  documented (D-012), guard added, re-run at a pre-registered n=20.

## What Failed Scientifically

- **C5 withdrawn** (D-010), the pre-registered outcome. The join works (96.2%)
  but only attack-only archives were fetched, so no benign windows exist.
- **C9 contradicted by our own measurement.** Four of six architectures meet
  10 ms, not one, and the fastest is a plain decision tree, not XGBoost.
- **C13 / Table VIII deleted** (D-009) — never had evidence.
- **C15 energy withdrawn** (I9) — RAPL cannot attribute to a container.

## Critical Warnings For Next Session

1. **RQ1 has no result.** No target corpus (D-011). The paper is currently a
   methods-and-measurement paper wearing a transfer paper's title. Either obtain
   5G-NIDD / the NF-* family, or retitle. This is the single biggest item.
2. **Latency is EMULATED.** Windows, no CPU isolation. Do not let a conformance
   claim reach the paper without Level 2 (D-005) or explicit removal.
3. **51 synthetic values remain in `main.tex`.** The draft banner must stay up.
4. **The network layer groups by `src_ip`**, so its "group-disjoint" is
   host-disjoint and in a testbed that is closer to attack-disjoint. The radio
   layer carries the leakage claim (D-013).
5. **Do not re-claim** radio-beats-flow in-distribution (P03), cross-domain
   collapse (P14) or the base-rate result (Axelsson 2000). All prior work.

## Next Actions, In Priority Order

1. Obtain a target corpus, or retitle the paper away from transfer.
2. Run Track C at Level 2, or delete the conformance claim.
3. Re-run detection under resampled prevalence (Reviewer A3).
4. Report the `src_ip` grouping confound explicitly (Reviewer A4).
5. Align title, abstract and contributions with what was measured (Reviewer C1).

---

## Campaign 2 — experiment records (appended 2026-09-20)

### EXP-024 — Repository / remote reconciliation

- **Phase:** 24 | **Gate:** PASS | **Report:** `reports/repository_remote_reconciliation.md`
- **Question:** the brief reported 24 commits pushed but a GitHub page showing one
  commit and a skeleton. Which is true?
- **Method:** `git ls-remote` (asks the server, cannot be stale), `git fetch`,
  `git diff HEAD origin/main`, `git ls-tree -r origin/main`.
- **Result:** **no discrepancy.** local HEAD == origin/main == `faa2849`, 25
  commits, one branch, clean tree, every required artefact present remotely.
- **Explanation:** the described page matches `6d657fe` exactly — the repository's
  first commit, titled "Repository skeleton". A stale view.
- **Trap for next time:** the git repo is `oran-ids-deployability/` **inside** the
  working folder. `git log` one level up says "not a git repository".

### EXP-025 — Target corpus acquisition and verification

- **Phase:** 25 | **Gate:** PASS | **Report:** `reports/EXP-025_target_corpus.md`
- **Closes:** D-011, gate A1-target. **RQ1 unblocked.**
- **Route:** Etsin/Fairdata, the Finnish national research repository. Open,
  CC BY 4.0, own DOI `10.23729/e80ac9df-d9fb-47e7-8d0d-01384a415361`. **Not** the
  paywalled IEEE DataPort copy; **not** an unattributable mirror.
- **Verified on the artefact:** 1,215,890 rows, 52 cols, Argus, 60.71% attack,
  **no IP or port columns at all**. All four files re-hashed for the report.
- **Coverage:** {benign, dos, probe}. `ddos`, `bruteforce`, `web` exist in `D_A`
  and not in `D_B` — **UNTESTABLE in transfer**, reported, never dropped quietly.
- **`HTTPFlood` maps to `dos`, not `web`.** It is Goldeneye/Torshammer DoS;
  `D_A`'s `web` is SQLi/XSS/directory brute force. Mapping them together would
  invent a correspondence and flatter the result.
- `reports/RQ1_blocked.md` deliberately **not** written — that branch does not apply.

### EXP-026 — Cross-deployment transfer (RQ1)

- **Phase:** 26 | **Runner:** `experiments/run_transfer.py`
- **Space:** `configs/features/shared_space.yaml` — **15 shared concepts / 18
  matrix columns.** The draft claims 24; that number was never derived from
  either schema. `configs/features/shared24.yaml` is superseded.
- **Design:** group-disjoint source split on `src_ip`, 20 split seeds, threshold
  fixed at 0.5, source-fitted scaling only, full 8-model ladder including both
  trivial floors, evaluated on the whole target once.
- **Controls:** source held-out **in the same 18-column space** (so the gap is
  not the projection), and the trivial floor **on the target** (so a collapse
  reads against what guessing scores there).
- **Directions:** `a_to_b` primary, committed first; `b_to_a` a labelled symmetry
  check (D-017). `D_B` has no group key, so its own held-out reference is a
  random split and an **optimistic bound**.
- **Decisions raised:** D-015 (byte semantics), D-016 (log1p), D-017 (direction).
- **Every target read is logged** to `results/EXP-026/logs/target_access.log`.

### EXP-027 — Prevalence sensitivity, and bug B-E

- **Phase:** 27 | **Gate:** PASS (source side) | **Runner:** `experiments/run_prevalence_sensitivity.py`
- **Question asked:** does the operational-precision finding depend on `pi = 0.002`?
- **Answer:** it does not depend on `pi`. It depended on **how PPV was averaged**,
  which is worse. See D-018.
- **Method:** analytic sweep over **pooled** confusion counts from committed
  results. No model refitted, so nothing can drift from what EXP-002/EXP-026 said.
- **Separability, verified numerically:** PPV is `lambda_b`-invariant (max
  variation 2.2e-16) and alert volume is exactly linear in `lambda_b` (max
  deviation 3.7e-9). So the 2-D grid is really 1-D plus a multiplier.
- **Surviving result:** corpus precision ~0.93, pooled PPV 0.0055-0.0077, a
  **132x** gap at `pi = 0.002`, rising to **2,631x** at `pi = 1e-4` and falling to
  1.19x at `pi = 0.5`. Detectors indistinguishable throughout.
- **Reporting rule:** the *collapse factor* is the finding; the "6x" was not.

### EXP-029 — Grouping confound (parts A and B outstanding)

- **Phase:** 29 | **Status:** part C complete, parts A and B outstanding
- **Part C result:** test-fold composition does **NOT** explain the 0.000-0.890
  FPR range. Mean R^2 across predictors 0.04-0.06, max 0.36, 1 of 7 significant.
  So it is *which* groups land in test, not how many or their class balance.
- **Part A** (label-free): NMI / Cramer's V / purity of each candidate grouping
  against the label, read against **two** nulls — a label shuffle and a
  size-matched random grouping. It reads the whole 227 MB CSV; allow minutes.
- **Part B:** does `src_ip` grouping score like grouping *by attack type*? If yes,
  "host-disjoint" is really "attack-disjoint" and the protocol is misnamed.

### EXP-030 — Native feature extraction

- **Phase:** 30 | **Gate:** PASS | **Runner:** `experiments/run_extraction_benchmark.py`
- **New module:** `src/oran_ids/ingest/fast_exporter.py` — bulk NumPy header
  extraction. **Agrees with the reference exactly** (0 packet mismatches, 0 byte
  mismatches, 100% coverage) on every shape tested. 8 tests.
- **Speedup 2.3x to 12.1x**, tracking packets-per-flow: bulk parsing wins on fat
  flows, groupby overhead eats the win on 2-packet flows. The reference is flat at
  **63-78 us/packet** whatever the shape — that is the per-packet Python cost.
- **The finding survives optimisation.** Best vectorised extraction 0.058 ms/flow;
  against real-RIC inference (1-5 us logreg, 10-25 us MLP) that is still **19x**
  and **3x**. Smaller than the 7-39x against Python inference, same sign, and now
  resting on a measurement rather than a caveat.
- **Captures are SYNTHETIC** — D-010 stopped the pcap download, originals are gone.
  Calibration: the reference exporter runs 0.9-1.1 MB/s here against 1.1-4.3 MB/s
  on the real captures, which is reported whether or not it passes.

### EXP-031 — Real Near-RT RIC runtime

- **Phase:** 31 | **Gate:** **BLOCKED** | **Report:** `reports/EXP-031_real_ric_blocked.md`
- **Blocker, command-verified:** `wsl -d Ubuntu` fails with
  `HCS_E_SERVICE_NOT_AVAILABLE` — the Windows Virtual Machine Platform feature is
  not installed. Docker Desktop's Linux engine runs on WSL2, so it fails too.
  Docker 29.6.2, kubectl 1.36.1 and a registered Ubuntu **are** present.
  Unblocking needs **administrator rights and a reboot**.
- **Why we did not force it:** even with WSL2 there would be no CPU isolation, and
  tail latency is what a noisy scheduler destroys. The outcome would have been a
  third emulated measurement wearing the word "real".
- **The scientific content is a negative result about our own method.** Obiuwevwi
  et al. report 1-5 us for logistic regression on a real RIC; we report 2.45 ms
  p50 for the same family. Three orders of magnitude is not hardware — it is a
  compiled embedded model against a Python object graph. **The near-RT crossing
  point is a property of the implementation, not the architecture.**

### EXP-036 — Fresh literature and novelty audit

- **Phase:** 36 | **Gate:** PASS | **Report:** `reports/literature_audit_v2.md`
- **Two direct pre-emptions in nine queries**, both recorded rather than worked
  around. Gaps **G1 and G5 are CLOSED by other people.**
- **Provenance discipline kept:** 2 entries `FULL_PAGE`, 9 `SNIPPET`. Nothing
  tagged `SNIPPET` may support an absence claim — that rule is what G4 violated.
- **Abraheem & Edhirig's dataset-fingerprint result (0.993 balanced accuracy for a
  source classifier on the shared features, surviving CORAL and Top-6 filtering)
  is the best external support our own exporter confound has ever had.** Cite it
  where we state the caveat.
- **Surviving novelty** is narrow and honest: the B-E estimator error with its
  magnitude; the published Zeek/Argus byte-mapping trap; transfer measured against
  a group-disjoint source reference; an 8-architecture ladder with trivial floors
  on the target; and the combination of protocol, transfer, burden, calibration
  and latency with a decision register of everything withdrawn.
- Also fixed a live integrity problem: the public README described Track C by
  quoting the wording results *would* carry once measured, and an automated
  summary had already repeated it as a result. It now says plainly that no real
  RIC measurement exists.

---

## Campaign 2 — final results (all experiments complete, 2026-09-20)

### EXP-026 reverse — `D_B -> D_A`, the symmetry check

- **Status:** complete, 20 seeds, 4,464 s
- **Result:** all six non-trivial architectures degrade significantly (Holm
  p = 0.0000). **Transfer fails in both directions**, so "D_B is simply harder"
  is ruled out.
- **The reverse is the worse direction.** On `D_A` the majority floor is 0.4862
  and the stratified floor 0.4171. **`tree` (0.3430) and `rf` (0.3365) fall below
  BOTH floors.** `xgboost`, `hgb` and `mlp` beat the majority classifier by
  0.002-0.012. Only `logreg` (0.5631) clears it meaningfully.
- **Caveat that must always travel with the reverse `Delta_F1`:** `D_B` has no
  group key, so its held-out reference is a random split and every reverse
  `Delta_F1` is an over-estimate. **The target-side distance from the floor does
  NOT carry this caveat** — how `D_B` was split does not affect how the floors on
  `D_A` behave.
- **The mechanism, and it is clean:** categories present in the training corpus
  transfer (`ddos` 0.83-0.87, `dos` 0.72-0.77, `probe` 0.87-0.89 for the boosted
  models); categories absent from it do not. `D_B` has no web attacks, and web
  recall on `D_A` is **0.004-0.013** for four of six architectures. `bruteforce`,
  also absent, is 0.33-0.57.
- **Why `logreg` wins both directions:** it is the only architecture with
  non-trivial web recall (0.298) and the best bruteforce recall (0.568), because
  it generalises coarsely instead of fitting source-specific signatures. It pays
  with the worst benign specificity (0.706).

### EXP-028 — calibration

- **Status:** complete, 10 seeds, 6 models, 2,661 s
- **Answer: NO.** Calibration improves every calibration metric and destroys the
  operating point. `logreg` source: Brier 0.1023 -> 0.0486 and ECE 0.1852 ->
  0.0866, while PPV goes 0.0174 -> 0.0025 and alerts/hour 35,330 -> 216,846.
- **Mechanism:** a calibrator fitted on a corpus that is 94.63% attack maps
  scores onto that prior, pushes nearly everything past 0.5, and the detector
  flags everything.
- **The stronger result:** every calibrator here is **monotone**, so none changes
  the achievable operating points. Verified: Platt and temperature preserve
  ROC-AUC to **under 1e-5** for five of six models. **Threshold saturation is a
  discriminability limit, not a calibration failure.** Target ROC-AUC is
  0.537-0.691.
- **A near-miss worth remembering:** temperature scaling appears to rescue two
  architectures in the reachability table. It preserves the ROC exactly, so it
  rescues nothing — it moves where a **fixed threshold grid** lands on the same
  curve. Any comparison of monotone calibrators over a fixed grid can manufacture
  this. Report the ROC beside the grid.
- **Oracle prior correction does not beat raw scores** on precision, even knowing
  the target prior. It cuts the queue (19,551 -> 3,285/h) at half the remaining
  recall. Prior shift is real, helps the queue, and is **not** what limits
  precision.

### EXP-033 — adversarial and degraded telemetry

- **Status:** complete, 5 seeds, 6 models, 6 attacks x 6 magnitudes, 3,558 s
- **NOT first** — O-RAN adversarial ML is prior art. The contribution is the
  operational reading.
- **Detection barely moves; the queue moves 2-4x.** `logreg` loses 0.014 macro-F1
  under missing telemetry and gains 135,000 false alerts/hour.
- **Stale telemetry is nearly harmless** (±0.004 at every magnitude). A delayed
  E2 indication is far less serious than a missing one.
- **Constrained evasion makes attacks MORE detectable** for the tree ensembles
  (`rf` +0.057 at eps=0.50): attack traffic already has higher volumetric
  features, so padding moves further from benign. **Report the constrained
  number; the unconstrained one is an upper bound that points the wrong way.**
- **Missing telemetry is the dominant fault, and it is about WHICH feature.** One
  zeroed feature costs `logreg` 0.240 macro-F1; two cost 0.014. The subset is
  resampled per cell, so variance across identity exceeds the trend in count.
  Reported unsmoothed.
- **Poisoning orders by capacity:** `rf` −0.181 at 25%, `xgboost` −0.148,
  `logreg` −0.054. **The MLP improves** (+0.034) — label noise regularising an
  over-fitted model.

### EXP-035 — deployability, final

Nine axes, all six architectures Pareto-efficient. Per-axis winners:

| Model | Wins |
|---|---|
| `rf` | target F1, distance above floor, Brier |
| `logreg` | deployment PPV, false alerts/hour |
| `mlp` | **source F1** (the metric a paper reports), drift |
| `tree` | p99 latency |
| `hgb` | worst-case robustness |
| `xgboost` | nothing |

### Final validation state

```
19 PASS   1 WARN   3 BLOCKED   0 FAIL
```

BLOCKED: real RIC runtime, CPU/RAM under load (both need a Linux host with
isolated cores), manuscript (27 synthetic values remain, draft banner up).
WARN: latency is EMULATED.

### A guard added this campaign

`scripts/check_withdrawn_claims.py`, wired into `final_validation`. A claim is
not withdrawn until no sentence in the manuscript asserts it. It found **17**
surviving assertions on its first run, including a 1D-CNN and an LSTM reported
with full hyperparameters, accuracy figures and latency percentiles across three
tables and two figures — **neither model exists in `models/zoo.py`**. Now 0.

---

# REVISION CAMPAIGN — 2026-09-24 (answering the simulated IEEE Access review)

Review: `reports/peer_review_ieee_access_2026-09-24.md` (7 reviewers).
Response: `reports/response_to_reviewers_2026-09-24.md` (generated from
`reports/response_to_reviewers_template.md` by `analysis/fill_response.py`).
Original manuscript preserved in `paper/_original/` for the track-changes diff.

## What changed the paper's claims

1. **D-021: the MLP had no class weighting.** Fixed in `models/zoo.py`, guarded by
   `tests/unit/test_zoo.py`. Weighted MLP scores 0.531 macro-F1 on D_B, above the
   0.424 floor. "MLP beneath the floor" and "rank does not predict transfer" are
   WITHDRAWN (D-028). Five other models reproduce EXP-026 exactly.
2. **D-026: Nadeau-Bengio corrected intervals are primary.** Random-split gain
   averages 0.13, NB 95% [-0.01, 0.27], p = 0.06; no single model significant after
   Holm. Direction consistent (16-20 of 20 splits per model).
3. **D-027: transfer is reported in balanced accuracy.** The majority floor loses as
   much macro-F1 as the detectors; BA falls 0.21-0.36 (5/6 significant) while the
   floors stay at 0.5. Reverse direction keeps BA for LR, XGB, HGB, MLP.
4. **D-025: operating points from pooled counts, in the detector's unit.** Radio:
   FPR 0.22-0.33 per 16 s window = 50-74 false alerts per benign UE-hour; PPV
   0.0055-0.0080 at pi = 0.002; best PPV with recall >= 0.1 is 0.036 even in
   distribution. Flow layer: thresholds reach PPV 0.42 on held-out D_A, 0.026 on D_B.
5. **D-029: calibration claim narrowed.** Isotonic changes ROC-AUC up to 0.21, Platt
   inverted DT in 1 of 10 seeds; only temperature preserves order. EM/BBSE target-
   prior estimates swing 0 to 1 (true 0.607).
6. **D-023: survey table removed** (never run). **D-024: hand-typed Figs 4-5 replaced.**

## New experiments (all real runs, none projected)

EXP-041 transfer v2 | EXP-042 memorisation control (category-stratified split +
nearest-neighbour probe: 68% of random-split test windows have a same-session NN)
| EXP-043 latency v2 + ONNX + real-capture extraction | EXP-044 calibration v2 +
label-free priors | EXP-045 exporter sensitivity (domain classifier 0.999 shared,
0.997 robust; D-022 robust subset) | EXP-046 pooled radio alert burden | EXP-047
harmonisation loss (0.005-0.082 BA) | EXP-048 unsupervised (fail in distribution)
| EXP-049 CORAL | EXP-050 GRU and 1D-CNN (torch in C:/Users/adeel/.venvs/oranseq,
because the global torch install is broken) | EXP-051 drift v2 (-0.26/-0.30,
false alerts x3.1) | EXP-052 statistics layer.

## How numbers reach the paper now

`analysis/revision_stats.py` -> `analysis/make_numbers.py` (every in-text number is
a macro in `tables/generated/numbers.tex`) -> `analysis/make_tables_v2.py` ->
`analysis/make_figures_v2.py`. Latency via `analysis/latency_outputs.py`.

## Still not done, and why

- Single-exporter control: no Zeek on this host, no 5G-NIDD pcaps in our copy.
- Third corpus: none available with paired radio telemetry.
- Real RIC and CPU/RAM under load: EXP-031 blocker unchanged.
- IEEE Access class file: apply at submission (IEEEtran journal layout for now).
- Author block is still a placeholder.

## Traps found this campaign

- psutil suspend scripts match their own command line if they grep for the target
  name. Exclude `os.getpid()`.
- Bash heredocs on this host eat backslashes in LaTeX strings (\t -> tab, \r -> CR).
  Write LaTeX-editing scripts to files instead.
- Windows MAX_PATH breaks pip installs of torch under the session scratchpad path.

---

# Change log

Standing rule (Adeel, 2026-09-24): every change to this repo is recorded here as it
happens. Newest entries at the bottom. Never edit or delete earlier entries.

## 2026-09-24

- `reports/peer_review_ieee_access_2026-09-24.md`: simulated 7-reviewer IEEE Access review written.
- `src/oran_ids/models/zoo.py`: MLP now trained with balanced sample weights (D-021). `tests/unit/test_zoo.py` added (10 tests; suite 60/60 pass).
- `src/oran_ids/data.py`: `load_radio_sequences()` added for the sequence models; asserted equal to `load_radio()` windows.
- `experiments/`: new runners `run_transfer_v2.py`, `run_leakage_v2.py`, `run_alert_burden_v2.py`, `run_unsupervised.py` (fixed a duplicate-keyword crash, re-run), `run_sequence_model.py`, `run_exporter_sensitivity.py`, `run_latency_v2.py`, `run_extraction_real.py`. `run_calibration.py` gained `--out`, `--models`, `--estimate-prior` (EM, BBSE). `run_drift.py` gained `--out`.
- `results/`: EXP-041, 042, 044, 046, 047, 048, 051 complete; EXP-045 part B complete; EXP-045 robust transfer, EXP-049 CORAL and EXP-050 sequence models running (suspended during EXP-043); EXP-043 latency running alone.
- `analysis/`: new `revision_stats.py`, `make_numbers.py`, `make_tables_v2.py`, `make_figures_v2.py`, `latency_outputs.py`, `fill_response.py`.
- `tables/generated/`: `numbers.tex` (in-text macros) and `rev_*.tex` tables. `figures/generated/`: `fig_rev_*` figures.
- `paper/main.tex`: rewritten (IEEEtran journal layout); `paper/latency_section.tex`, `paper/predicate_section.tex` added; `paper/fig1_architecture.tex`, `paper/fig2_pipeline.tex` corrected; originals kept in `paper/_original/`.
- `paper/references.bib`: Crossref-verified; SCOPE, ColO-RAN, 5G-Spector, 5G-NIDD descriptor fixed; Niknam and Layeghy replaced by published versions; LightGBM removed; 14 references added.
- `configs/decisions.md`: D-021 to D-029. `configs/experiment_registry.yaml`: EXP-041 to EXP-052. `docs/claims.yaml`: C13 withdrawn.
- `scripts/check_withdrawn_claims.py`: 8 retired-claim patterns added; LSTM-only sequence rule. Revised manuscript passes, reviewed one fails (13 hits).
- `reports/`: `response_to_reviewers_template.md`, `revision_validation_report_2026-09-24.md` added. `README.md` status table updated.
- Environment: pip installed onnx, onnxruntime, skl2onnx, onnxmltools (core library versions unchanged). CPU torch installed in `C:/Users/adeel/.venvs/oranseq` (global torch install is broken and was left untouched).
- Auto-memory: `feedback-log-every-change` and `project-revision-2026-09-24` saved.
- Build fix (Adeel reported "latex not compiling, pdf is old"): `paper/main.tex` failed because EXP-043 latency and EXP-050 sequence outputs did not exist yet. Added interim guards (`\providecommand{\LatFigLine}`, `\IfFileExists` around the latency section and the sequence table) that switch to real content automatically. Split Eq. (7) onto three lines; shortened `rev_corpora` labels (`analysis/make_tables_v2.py`). New `scripts/build_paper.py` builds the paper and pauses any running timing job during the build (logged in `results/EXP-043/logs/suspensions.log`). Result: `paper/main.pdf` rebuilt, 13 pages, 0 errors, 0 undefined references, 0 overfull boxes over 10 pt.
- EXP-043 complete on a quiet machine (EXP-045/049/050 suspended with psutil during timing, then resumed). All 12 ONNX exports verified (decision agreement 1.0). RF single-row p50: 29 ms thread pool, 5.6 ms one thread, 0.012 ms ONNX. Radio path (aggregation + ONNX) p99 upper bound <= 0.12 ms.
- BUG FIXED `src/oran_ids/ingest/fast_exporter.py`: vectorised exporter ignored the 120 s active timeout (1,199 vs 1,406 records on the real ICMP capture). Added active-timeout splitting identical to the reference; regression test `test_active_timeout_splits_a_long_flow_like_the_reference` (suite 61/61). Re-run `run_extraction_real.py` (now checks equivalence on two captures): exact packet/byte agreement on all 38,032 shared IPv4 keys; reference-only keys are IPv6 link-local (verified, 26 records, 75 packets on ICMP). Speed-up 22.8x-41.6x. Pre-fix output kept as `extraction_real_captures__before_active_timeout_fix.csv`.
- `analysis/latency_outputs.py`: equivalence macros; refuses to emit if shared keys disagree. `paper/latency_section.tex`: equivalence sentence. Response template: exporter defect reported under comment 2.7. Paper rebuilt.
- Track changes: new `scripts/build_diff.py` builds `paper/diff.pdf` (latexdiff from `paper/_original/main_reviewed.tex` to `main.tex`, colour markup, needs `--perl-lib` pointing at Algorithm::Diff). Fixed three failures: old `\measured`/`\syn` macros undefined, inlined bibliography marked up (now `\bibliography{references}` + bibtex), strike-out inside deleted `\subsection`. Result: 17 pages, 0 errors. Remaining undefined references all sit in deleted text and point to labels the revision removed.
- `reports/response_to_reviewers_template.md` I25: "Fifteen" references corrected to "Fourteen" (counted from the bib diff; LightGBM was removed).

## 2026-09-24 (round 2: answering the second simulated review)

Adeel asked (17:20) to fix every problem in the round-2 review phase by phase, log every change here, and consolidate all experiments and project information into one file ready for GitHub.

- `reports/peer_review_round2_2026-09-24.md`: round-2 review saved (3 reviewers + area chair, standard severity). Its roadmap drives phases 0-7 below.
- State check: EXP-043 (13:29), EXP-050 (14:07), EXP-049 (14:20) and EXP-045 robust (15:13) all finished with EXIT 0 after the last paper build. No Python process is running. Their results are not yet in the tables or the text.
- Phase 0 (review R1-W5, placeholders). `analysis/revision_stats.py`: sequence-model NB ratio computed from the runs (0.280) instead of the hard-coded 0.25. `analysis/make_numbers.py`: arm min/max exclude the two floors (they sat at 0.5 by construction and set RobBAmin); new macros RobSrcBA*, Rob/Coral/Unsup FPR*, CoralMLPtgtBA, Seq* (three decimals). Re-ran revision_stats, make_numbers (206 macros), make_tables_v2: `rev_sequence.tex` (GRU +0.165, 1D-CNN +0.189, Holm-adjusted p <= 0.02 within the pair), `rev_arms.tex` (robust: source BA 0.80-0.94, target 0.48-0.53; CORAL: target 0.47-0.60, only MLP gains, target FPR 0.55-0.99), `rev_predicate.tex` (B_min = 1 ms for every architecture), `rev_latency.tex`.
- Phase 0 `paper/main.tex`: Section VI-A sequence sentence now quotes Table VI; Section VI-D arms paragraph rewritten with the robust-subset and CORAL numbers; interim `\InputIfReady`/`\IfFileExists` guards and the `\LatFigLine` fallback removed (results exist, a missing file should now fail the build). Built: 13 pages, 0 errors, 0 undefined references.
- Phase 1 finding (R1-W6, checked before any model was fitted): the radio capture is ordered by scenario. Sessions 0-8 are benign (days 0-6, one UE each), 9-11 probe, 12-14 brute force, 15-16 DoS, 17-21 web, 22 DoS, 23-28 DDoS (days 47-53, 1-4 UEs), 29 benign (day 52.95, 3 UEs). Radio labels are session-level: every window of an attack session is labelled attack. So every EXP-051 forward "time-disjoint" split holds out whole attack categories (at 0.4: brute force, DDoS, DoS, web) and has one benign test session (29). EXP-051's drift numbers measure unseen categories plus one late benign session, not drift. Benign and attack captures are also six weeks apart, a capture-period confound for the whole radio layer.
- `src/oran_ids/data.py`: new `radio_session_timeline()` (session start/end/day, UEs, category; same session rule as `load_radio`), exported in `__all__`.
- `experiments/run_drift_v3.py` (EXP-053, new): A coverage audit of EXP-051 splits; B category-stratified time split (latest/earliest session of every category held out) against 50 random-session-per-category controls, BA and ROC-AUC primary, false alerts per benign UE-hour; C leave-one-benign-session-out FPR. Running.
- Phase 2/5 findings: 5G-NIDD `Combined.csv`/`Encoded.csv` keep Argus `Seq` and `Offset`. `Offset` resets recover 20 capture files: two passes of the same ten captures, one per base station (the dataset description names two base stations, each with an attacker node; pass-to-station assignment is inferred). Every attack file mixes benign and one attack type. This gives D_B a group key.
- Published pipeline found: Samarakoon et al., arXiv:2212.01298 (5G-NIDD). Encoded.csv, ANOVA top-10 features (Seq and Offset rank 1 and 2, sTtl 3), z-score, random 70/30 x10, DT/RF/KNN/NB/MLP(10,20,10). Table X binary accuracy: DT 0.998956, RF 0.999467, KNN 0.998675, NB 0.963472, MLP 0.998520. Our ANOVA F on this copy reproduces their ranking in the same order, each value about 1/0.7 of theirs (they ranked on the 70% training split).
- `experiments/run_published_pipeline.py` (EXP-055, new): R0 published split/features, R1 without Seq/Offset, R2 capture-file-disjoint (5 group folds), R3 base-station-disjoint. First R0 runs reproduce the paper: DT 0.99958, RF 0.99959. Running.
- `experiments/run_target_reference.py` (EXP-054, new): D_B in-target BA (random, file-disjoint, site-disjoint) in the shared 18 columns and in native Encoded features without identifiers; plateau analysis (flows sharing an 18-column vector with the opposite label; majority-per-vector BA bound). Running.
- EXP-053 complete (631 s, EXIT 0). A: every EXP-051 forward split holds out 1-4 attack categories and tests one benign session (29). B: latest session of every category held out gives BA 0.52-0.57 against control means 0.75-0.83, but 12-32% of the 50 control draws score as low; earliest held out gives 0.95-0.99 (FPR 0.00), matched or beaten by 4-34% of draws. Time order stays inside session-to-session variation. C: leave-one-benign-session-out FPR is 0.00-0.07 for six sessions, 0.14 for session 5, and 0.81-0.98 for sessions 4, 8 and 29 (days 3, 6, 53). Session 29 draws 196 false alerts per benign UE-hour. Conclusion: benign-session heterogeneity, not drift; EXP-051's "-0.26 macro-F1, false alerts x3.1" is withdrawn.
- `analysis/revision_stats.py`: `drift_v3()` (EXP-053 summaries, EXP-051 re-expressed in BA for the response letter). `analysis/make_numbers.py`: Dv* and Ben* macros. `analysis/make_tables_v2.py`: `rev_time_split.tex`, `rev_benign_sessions.tex`.
- `paper/main.tex` Section VI-B replaced: "Time Order and Benign Sessions" (capture schedule, coverage audit, category-stratified time split, held-out benign sessions); Table VII (rev_drift) replaced by Tables tab:timesplit and tab:benign.
- Phase 3 (R1-W4): `experiments/run_alert_burden_v2.py` gained `--out`, `--by-session`; `experiments/run_transfer_v2.py` gained `--group-counts` (counts per source address and per D_B capture file); `src/oran_ids/data.py` gained `d_b_capture_files()` and `load_target_d_b(groups="capture_file")` (computed before dedup; not a feature). Tests 61/61 pass.
- EXP-056 radio re-run (279 s): counts identical to EXP-046 at every (model, seed, tau); per-session sums equal the totals. EXP-056 forward transfer with per-cluster counts: running.
- `analysis/revision_stats.py`: `cluster_bootstrap()` resamples clusters and split seeds (2,000 replicates), recomputes pooled TPR, FPR, PPV at tau 0.5 and best PPV at recall >= 0.1; asserts EXP-056 totals equal EXP-046/EXP-041 first. Radio result: pooled FPR interval for LR [0.02, 0.55] (Wilson gave [0.21, 0.24]); PPV at tau 0.5 [0.003, 0.13]; best-threshold PPV interval reaches 1.0 for LR, RF, XGB, MLP. The radio "no threshold reaches 0.05" claim is NOT supported; radio alert burden cannot be pinned down with 10 benign sessions.
- Phase 4 `paper/references.bib`: RICARCH now "O-RAN.WG3.RICARCH-R003-v04.00, Mar. 2023"; added samarakoon2022niddarxiv (arXiv:2212.01298, Table X accuracies), ilias2024moe5g (arXiv:2412.03483, weighted F1 up to 99.95% on 5G-NIDD), dhooge2020interdataset, engelen2021troubleshooting, flood2024smells, kus2022falsesense (all four Crossref-verified with DOI and pages). 62 entries.
- EXP-055 attempt 1 (default MLP, stopped for compute): R0 rep0 reproduces the published numbers (DT 0.99958, RF 0.99959, KNN 0.99900, NB 0.92738, MLP 0.99863 against published 0.99896/0.99947/0.99868/0.96347/0.99852). R1 (Seq and Offset removed, next two ranked features in): DT and RF accuracy 0.769, BA 0.706, FPR 0.587. Kept as `results/EXP-055/raw/ladder_runs_attempt1_default_mlp.csv` and `logs/run_attempt1_default_mlp.log`.
- FINDING, EXP-057 (`analysis/label_conflict_audit.py`, new): 5G-NIDD labels are not a function of the flow record for half the corpus. 52.0% of flows (632,378) sit on records (all Encoded fields except row index, Seq, Offset, labels) that occur with both labels; all of them are in the two UDP-flood captures (75% of file 5, 98.4% of file 15). Every one of file 15's 281,529 UDPFlood flows has an identical twin in file 5 labelled Benign, with equal counts for 33,704 of 33,708 distinct records; file 5's benign class is 96.4% such twins. So 281,525-281,529 of D_B's 477,737 benign flows (59%) are copies of flood traffic labelled UDPFlood elsewhere. Combined.csv also restarts its row index at row 728,316 (start of file 11), confirming two per-station files. Balanced-accuracy ceilings (in-sample, BA-optimal lookup): native content 0.766, shared 18 columns 0.753 (= the 0.751-0.752 plateau of DT/XGB/HGB/MLP, R1-W1 explained), with Seq and Offset 1.000.
- `src/oran_ids/data.py`: `load_target_d_b(groups="capture_file")` now suffixes "|c" on benign flows whose record also occurs with an attack label (281,529 flagged; group suffix only, never a feature); dedup restricted to the published columns so row count stays 1,215,889 as in EXP-041.
- EXP-056 forward transfer restarted with the conflict-aware groups (first attempt stopped at seed 3). `analysis/revision_stats.py`: target bootstrap clusters on capture files, plus a "clean" variant without the flagged flows (pooled, reachability, predicate, per-seed BA gap, per-file FPR).
- EXP-054 and EXP-055 stopped and relaunched lighter (three jobs made each fit 5-10x slower): EXP-054 `--seeds 5 --native-seeds 2`, with clean-subset metrics, resume support and the BA-optimal plateau rule; EXP-055 `--repeats 2`, MLP with early stopping (documented deviation), clean-subset metrics, resume support. Partial first attempts kept as `runs_attempt1.csv` / `run_attempt1.log`.
- `analysis/label_conflict_audit.py` extended with the file-to-file pairing (`processed/pairing_between_files.csv`, `statistics/pairing.json`) and re-run: file 5 benign vs file 15 attack, 33,708 records, 281,525 vs 281,529 flows, 33,704 equal counts.
- `analysis/platt_diagnosis.py` (new) -> `results/EXP-044/processed/platt_inversion_diagnosis.csv`: seed 110 tree has ROC-AUC 0.484 on its calibration fold (96 source addresses) and 0.973 on test (reproduces EXP-044's logged value exactly); Platt slope -0.55. Explains the inversion.
- 1-NN row added to Table V (`nn_leakage_row()` in revision_stats, `leakage_nn1.csv`): random 0.958, run-disjoint 0.814, cat.-strat. 0.794.
- `analysis/make_tables_v2.py`: calibration table prints `<10^-6` and `a x 10^e` instead of 9e-01 / 2e-16 (a heredoc had turned `\times` into a tab; fixed with the Edit tool; all patched .py files scanned, no other tabs).
- `analysis/make_numbers.py`: NNGain from the displayed two-decimal values (0.15, matches 0.96 - 0.81), NNgapBest, TrDiD and TrRevBAdrop at three decimals (match the tables), Platt* macros, Lc* macros (EXP-057). 256 macros.
- `paper/main.tex` (round-2 text, part 1): new title "Intrusion Detection for O-RAN: What Held-Out Accuracy Predicts About Deployment"; keyword "IoT security" -> "label quality"; intro paragraphs 1-2 (no edge-data-center or signalling-storm claims; >99% premise cited to samarakoon2022niddarxiv and ilias2024moe5g); Section II (5G-NIDD published accuracies, Engelen, Flood, Kus, D'hooge, Abraheem and Edhirig's numbers and what this paper adds); IV-A (session-level radio labels, capture schedule, 5G-NIDD capture files from Offset resets); IV-B (robust subset not invariant, 40 vs 42 bytes); IV-D (protocols updated, in-target references); IV-E (Holm family defined, cluster bootstrap described); Algorithm 1 (late action sent and counted, policy stated); VI-A (category-stratified argument toned down, 1-NN comparison, Table V caption); VI-C rank-correlation sentence; VI-F Platt diagnosis; Limitations (target labels, radio capture schedule, radio interval).
- `configs/decisions.md`: D-030 (drift withdrawn), D-031 (cluster bootstrap), D-032 (5G-NIDD label conflicts), D-033 (published pipeline).
- `scripts/check_withdrawn_claims.py`: round-2 patterns (drift/triples, radio 0.05 claim, collapse-factor sentence, old title). It currently flags the abstract and Section VI-E, to be rewritten when EXP-054/055/056 finish.

## 2026-09-25

- The session of 2026-09-24 ended with EXP-054/055/056 still running; their processes died with it. Partial logs kept as `*_attempt2_killed.log`. New `scripts/round2_launch.ps1` starts all three as detached Windows processes (survive the session); EXP-054 and EXP-055 resumed from their raw CSV, EXP-056 restarted. Launched 09:47.
- `reports/NEXT_STEPS_round2.md` (new): handover prompt and checklist for finishing round 2 if this session ends (Adeel is away for 7 hours and asked for one).
- `paper/fig2_pipeline.tex`: callout "ONE PIPELINE, TWO LAYERS"; rungs 01/02 name layer and metric; rung 02 replaced by held-out benign sessions (FPR 0.00 to BenHighMax); t_q added to the runtime formula.
- `EXPERIMENTS.md` (new, repo root): the consolidated project and experiment record Adeel asked for (question, data, layout, reproduction, EXP-000..EXP-057, withdrawn claims, limitations). EXP-054/055/056 rows say running; update when they finish.
- 10:45 EXP-054/055/056 stopped and relaunched lighter (CPU shared with another project's jobs made EXP-056 take ~25 min per seed): EXP-056 --seeds 10 (revision_stats now asserts equality on the seeds run); EXP-055 KNN only at R0 (its prediction dominated later rungs); EXP-054 --seeds 3 --native-seeds 2. Partial logs kept as *_attempt3_stopped.log.
- README links EXPERIMENTS.md. `analysis/make_numbers.py`: RadCb* macros (radio cluster bootstrap). `analysis/make_tables_v2.py`: t_pooled uses bootstrap intervals when present and adds a 'D_B w/o conflicts' block; new t_conflict -> rev_conflict.tex. `paper/main.tex`: Section VI-E radio text rewritten (point estimates not stable, bootstrap FPR 0.01-0.65, PPV 0.0028-0.13, best-threshold PPV = oracle, interval reaches 1.0 for 4 of 6; collapse factor stated as arithmetic in pi); Table XIII caption now cluster bootstrap; new subsection 'The Target Corpus: Labels and a Published Result' (sec:res:target) with the EXP-057 label-conflict paragraphs and Table tab:conflict. Build: 15 pages, 0 errors, 0 undefined refs. Checker flags only the abstract (to rewrite last).
- Analysis for EXP-054/055 written and tested on partial data: revision_stats `published_ladder()` (per rung/features/model, pooled PPV and alerts/h, Eq. (6) terms against the model's own R0) and `target_reference()`; make_numbers Tgt*/Pub* macros; make_tables_v2 `rev_ladder.tex`, `rev_target_ref.tex`. Partial results: published R0 DT/RF pass the alert term (PPV 0.79, 129 false alerts/h) = the pass case; in-target random BA 0.71-0.75 all flows, 0.84-0.92 without conflicting copies; file-disjoint 0.97-0.99 (2 seeds).
- `reports/response_to_reviewers_round2.md` drafted (point by point; PENDING markers for EXP-054/055/056 numbers).
- `paper/predicate_section.tex`: B stated (10 ms, the radio path meets 1 ms); new paragraph 'Does the test discriminate?' (published pipeline passes on its own split, fails one rung later). `paper/main.tex`: ladder paragraph and Table tab:ladder (EXP-055) in sec:res:target. `paper/latency_section.tex`: context sentence on Obiuwevwi et al.'s in-RIC microsecond inference. New `scripts/refresh_round2.py` (ladder + references -> numbers + tables without the full bootstrap). Build 15 pages, 0 errors.
- `configs/experiment_registry.yaml`: EXP-053..057 added; EXP-043/045/049/050/052 complete; EXP-051 withdrawn (D-030). `docs/claims.yaml`: C19, C20 withdrawn (drift, radio 0.05), C21 (5G-NIDD label conflicts), C22 (published accuracy rests on Seq/Offset).
- EXP-054 complete (3466 s). Base-station directions now kept apart in analysis (flood copies are benign in station 1's labels). In-target BA, shared: random 0.71-0.75 (clean 0.84-0.92), held-out files 0.93-0.98 (no draw held out files 5/15), station 1->2 0.62-0.64, station 2->1 0.64-0.65 (clean 0.97-0.99); native: files 0.99-1.00. `paper/main.tex`: paragraph 'References inside the target' and Table tab:target_ref in sec:res:target.
- EXP-056 flows complete (5215 s, 10 seeds). revision_stats ran clean: EXP-056 target and source counts equal EXP-041 on the 10 seeds. Results: D_B without the benign copies: transfer BA 0.61-0.78 (nonlinear 0.74-0.78, LR 0.61), loss from source 0.00-0.25 (1 of 6 significant), short of the in-target clean reference by 0.06-0.25; detectors flag 0.00-0.85 of the copies (LR none, RF/MLP most); clean FPR 0.026-0.183, 6,158-44,003 false alerts/h, PPV 0.0072-0.0398, best 0.063; deployability test clean: 0 of 6 pass (best PPV at recall>=0.5 0.042, >= 5,603 alerts/h). Flow bootstrap: D_B FPR interval 0.009-0.796 across models, D_A held-out 0.027-0.611. `paper/main.tex`: transfer paragraph 'The target's labels' (conflicts reverse which detector looks transferable); VI-E flows with clean numbers; Table XIII caption; predicate_section clean verdict. New macros TrClean*, NetClean*, NetCb*, PredClean*.
- `paper/main.tex`: abstract rewritten (237 words, all numbers macros; no drift claim, leakage interval, label conflicts, published pipeline, clean-target transfer, radio burden not bounded, ratio wording); contribution list rewritten (6 items incl. target audit and discriminating test); conclusion rewritten with requirement (vii) on label consistency and no position/identifier features, (i)-(iii) extended; header comment and III-A wording updated. check_withdrawn_claims: OK (23 patterns). Build 16 pages, 0 errors.
- Fig. 2 rungs 03/04 (D_B flows with consistent labels: BA TrCleanTgtBA, in-target reference; PPV <= NetCleanPPVbest) and caption (two layers) updated; rendered and checked (page 6). Algorithm comment shortened; results roadmap sentence updated; LeakAvgPt printed as 6x10^-5 (a heredoc again produced a tab; repaired via PowerShell; all .py re-scanned, clean).
- `scripts/perl5/Algorithm/Diff.pm` vendored (Algorithm-Diff 1.201, pure Perl, redistributable) so `python scripts/build_diff.py --perl-lib scripts/perl5` works from a checkout. `paper/diff.pdf` rebuilt: 22 pages, 0 errors (diff against the originally reviewed manuscript; the round-1 revised text as reviewed in round 2 was never saved separately, so no round-2-only diff).
- EXPERIMENTS.md rows EXP-054/056 and the response letter filled with final EXP-054/056 numbers (two PENDING left, both EXP-055). pytest 61/61; check_no_placeholders OK on main/latency/predicate sections.
- EXP-055 complete (10923 s). R0 BA 0.9986-0.9996 (NB 0.931); R1 (no Seq/Offset) accuracy 76.8-76.9%, BA 0.70-0.71, FPR 0.59, but RF BA 0.9999 on test flows without the benign copies: the counters resolve the label conflict, they carry no attack signal; R2 capture-file: published features BA 0.86-0.92 (RF folds 0.82-1.00), no counters 0.80 (RF folds 0.50-1.00, accuracy down to 1.6%); R3 base station: published 0.76-0.89, no counters 0.66-0.69. Deployability test: R0 DT/RF pass; every later rung fails, all flows and clean. `paper/main.tex`: ladder paragraph extended (R1 interpretation, R2 fold range, R3); abstract sentence; predicate_section 'every later rung'. New macro PubOneRFclean, R2 per-fold macros. Full chain rerun: 409 macros, 17 pages, 0 errors, 0 undefined refs; check_withdrawn_claims OK (23 patterns); placeholders OK. `scripts/build_diff.py`: blank lines inside captions removed and `--exclude-textcmd=caption` (latexdiff inline markup broke a caption); diff.pdf 22 pages, 0 errors.
- `paper/latency_section.tex`: 'same order' -> 'within an order of magnitude' (Obiuwevwi LR 1-5 us vs our ONNX 10 us). README status row (round 2, EXPERIMENTS.md, correct response-letter path) and latency remark corrected. .gitignore: latexdiff scratch and preview PNGs.
- Round 2 closed 13:55: ladder/in-target macros at three decimals (ranges no longer print as '0.80 to 0.80'); diff.pdf rebuilt (22 pages); pytest 61/61; `reports/NEXT_STEPS_round2.md` rewritten as status + open items; auto-memory project note updated. Local commit follows (Adeel asked to update the local repo for GitHub; not pushed).
- 2026-09-25 afternoon (Adeel: authors, remaining steps, zip, README, push; commit as Adeel only, never Claude). Claude Co-Authored-By trailer removed from the unpushed commit (message amended); rule saved to auto-memory `feedback-commit-as-user`.
- Authors set: Arshad Ali and Adeel Ahmad, Faculty of Computer and Information Systems, Islamic University of Madinah, Madinah, Saudi Arabia (no e-mails or corresponding author given; biographies are one line with the affiliation only).
- Paper moved to the official IEEE Access class from Adeel's Downloads (ACCESS_latex_template_20260513-1-1.zip, unpacked to `paper/access/`). Three compatibility fixes in the preamble, each commented: (1) the class redefines the primitive \year, which broke pgf/TikZ at load (found by bisecting the class: line 512) -> save and restore the primitive; (2) the class's \textbf#1 = {\bf #1} fails on math -> kernel \textbf/\textit restored; (3) the Pantone spot colour is lost when TikZ rewrites page resources -> accessblue as the same CMYK. \url package kept. Front matter in Access form (\history, \doi placeholders, \address, \markboth, keywords alphabetical, \titlepgskip, biographies, \EOD). `scripts/build_paper.py` finds the class via -include-directory (MiKTeX) or kpathsea variables (TeX Live); overfulls "while \output is active" (class header, also in the sample) are not counted. `scripts/build_diff.py` uses the same setup and repairs \titlepgskip. Build 17 pages, 0 errors; diff 24 pages.
- `scripts/reproduce.py` (new): check / paper / list / experiment / all / freeze. `reproducibility/expected_outputs.json`: 36 generated files (content hashes without comment lines). `reproduce.py paper` regenerated everything from results/ and matched 36 of 36; data checksums OK. `REPRODUCE.md` (new, reviewer guide, 3 levels). README rewritten (findings table with macro-checked numbers, layout, reproduction, data, citation). `requirements.lock` + ONNX stack and PyMuPDF; `pyproject.toml` adds skl2onnx, onnxmltools, dpkt, torch moved to extra [seq]. Paper Section VIII mentions the script. EXPERIMENTS.md, NEXT_STEPS, response letter updated. No LICENSE file exists (Adeel to choose).
- Pushed to https://github.com/adeliusa486/oran-ids-deployability (main, commits a5e2ab8 and a8399cb, authored by adeliusa486 only; GitHub lists one contributor). Reproducibility zip built with git archive from the pushed commit: E:/Work/New ORAN paper/oran-ids-deployability_reproducibility_package.zip. Verified from a clean extraction: reproduce.py paper -> 36 of 36 generated files identical, paper 17 pages 0 errors, PDF text hash equal to the repo copy, pytest 61/61. The zip is rebuilt after this log entry so repo, GitHub and zip stay identical.
- 2026-09-25 15:10 (Adeel asked to run the third dataset and for the time it takes; estimate given: ~4 h). EXP-058, third corpus D_C = DLTeamTUC 5G datasets (Nugraha et al., IEEE CSR 2025), github.com/DLTeamTUC/5GDatasets at commit e71267c: NFStream flow records from an Open5GS 5G core in Docker. Only the three flow-level files are usable (003a-pfcp, 004-syn-flood, 005-icmp-flood: 39,425 flows, 839 attacks: 580 SYN flood, 156 ICMP flood, 103 PFCP session deletion; labels malicious/benign/background); the other CSVs are per-interval NAS counts, not flows. No licence stated upstream; not redistributed. Files in data/raw/d_c/ (ignored), checksums in data/provenance/d_c_files.json.
- Trap caught before any result: NFStream counts link-layer bytes (TCP 54, ICMP 42 for bare packets) and flows inside the GTP-U tunnel carry 44 more bytes per packet (98, 86); every SYN/ICMP attack flow is tunnelled. `src/oran_ids/features/shared.py` new `from_d_c()` removes 14 bytes per packet, plus 44 when tunnel_id != 0; verified: attack inner sizes come out at 40 (SYN) and 28 (ICMP echo). `src/oran_ids/data.py` new `load_target_d_c()` (logged like D_B; groups = capture file; categories syn_flood/icmp_flood/pfcp_deletion/benign/background).
- `experiments/run_transfer_v2.py`: directions a_to_c (D_A source, identical training to EXP-041) and b_to_c (D_B source, random split). `scripts/exp058_launch.ps1` runs both detached (a_to_c 20 seeds, b_to_c 10 seeds; b_to_c first launched with 20 and restarted at 10 for time).
- `experiments/run_third_corpus_reference.py` (EXP-058 reference, 131 s): D_C label ceiling 0.992 (shared 18) and 0.9997 (native 48 fields); only 3.2% of flows on conflicting records. In-target random split BA 0.987-0.990 (shared), 0.991-0.998 (native); leave-one-capture-file-out (attack type unseen in training) 0.66-0.83 shared, PFCP deletion never detected.
- EXP-058 analysis code: revision_stats `third_corpus()` (transfer stats both directions, per-attack recall, pooled points, reachability, predicate; no cluster bootstrap: 3 capture files), make_numbers ThA*/ThB*/ThRef*/ThCeil* macros, make_tables_v2 `rev_third.tex` and a D_C column in `rev_corpora.tex` (D_B groups row now '20 files'). `paper/main.tex`: \DC macro and notation row. `paper/references.bib`: nugraha2025fivegdatasets (Crossref-verified, IEEE CSR 2025, pp. 326-333, DOI 10.1109/CSR64739.2025.11130023). 63 entries.
- EXP-058 b_to_c attempt 2 stalled after the last seed: with D_B as source (random split, group = row) --group-counts built ~10^7 per-row tables (12.6 GB, and the cause of its ~10 min per seed). Stopped; `run_transfer_v2.py` now counts source clusters only when the source has a group key. a_to_c unaffected (source groups = 318 addresses). b_to_c relaunched (10 seeds); stalled log kept as b_to_c_attempt2_stalled.log.
- EXP-058 complete (a_to_c 20 seeds 2032 s; b_to_c 10 seeds 828 s after the fix). Results: D_A->D_C BA 0.60-0.74, AUC 0.70-0.93, SYN recall 1.00, ICMP 0.10-1.00, PFCP 0.00-0.99, FPR 0.225-0.807, background flagged up to 0.81, drop 0.09-0.22 (0 of 6 significant), best PPV 0.092, test 0/6; D_B->D_C BA 0.42-0.85, AUC 0.38-0.81, SYN 0.71-1.00, drop -0.10..0.33 (3 of 6 significant), best PPV 0.031, test 0/6.
- `paper/main.tex`: new Section VI-F "A Third Corpus" + Table tab:third; D_C in IV-A, notation table, Table of datasets (D_C column; D_B groups now "20 files"), contributions, results roadmap, conclusion, Limitations ("Three corpora"); abstract +1 sentence ("A third corpus shows the same pattern."), 247 words. Wording checked against data: SYN flood recall 1.00 only from D_A (0.71-1.00 from D_B); "floods they were trained on" replaced by "the SYN flood". Build 18 pages, 0 errors; diff 25 pages; 469 macros; 37 generated files frozen.
- Records: configs/decisions.md D-034; registry EXP-058 (and EXP-054/055/056 marked complete); docs/claims.yaml C23; EXPERIMENTS.md row and data notes; README findings row and data table column; REPRODUCE.md data row, section map, counts (37 of 37, 18 pages); scripts/reproduce.py EXP-058 step and d_c checksum check; response letter section on the third corpus; NEXT_STEPS updated.
- 2026-09-25 evening (Adeel: rebuild Figure 1 from Downloads with the figure-rebuild skill, camera-ready medium-size graphs, full finalization audit per the master prompt). Report: `reports/finalization_audit_2026-09-25.md` (change log C01-C28, experiment, reference, figure and table audits, reviewer risks, ratings, GO with three author items).
- Figure 1 rebuilt from Downloads render O-RAN_intrusion-detection_system..._20260925161711.jpg (copied to figures/source/fig1_arch_raw_v2.jpg). 20 pictograms cut out with transparent background by new scripts/extract_figure1_icons.py (figures/icons/f1_*.png); palette sampled into figstyle.tex (fMint..fBadge). Six render errors corrected (prompt heading "Central Anchor"; malicious traffic bypassing the O-RU; E2 into the xApp instead of E2 termination; radio lane into the flow-only shared space; arrows out of the xApp and alert from the feature space; emulated latency marker drawn as measured). Helvetica text, selectable. Caption rewritten. Macro \act clashed with the class: renamed \fOneAct.
- Figure 2: rung 03 names D_C (BA from macros), untimed runtime stages hatched (chevoff), "how to read" box -> legend, Helvetica.
- New paper/fig_conflict.tex (label-conflict schematic, numbers are macros; \fcRecord). analysis/make_figures_v2.py rewritten: one camera-ready style (white, closed axes, inward ticks, Arial 7-8 pt, Okabe-Ito, 3.5 in wide, PDF + 600 dpi PNG). New figures fig_rev_benign, fig_rev_shift, fig_rev_sensitivity, fig_rev_latency; fig_rev_transfer is now a three-panel dumbbell (D_B all, D_B clean, D_C) with NB target intervals and in-target references; leakage is a dot plot with 1-NN. Latency is a quantile plot, not a CDF: EXP-043 kept quantiles only (no per-call samples).
- paper/main.tex: template DOI 10.1109/ACCESS.2024.0429000, "Date of publication xxxx", and footer "VOLUME 11, 2023" removed (etoolbox \patchcmd on the class; \history{} \doi{}). \Delta taken from cmr in all math versions (caption font printed it as an accent). Captions of Figs 1, 3, 6, 8, 9 rewritten; new figure environments for benign, conflict, shift; sensitivity figure in predicate_section.tex, latency figure in latency_section.tex. Abstract/contributions/conclusion: causal "models recognize capture sessions" -> "consistent with"/"points to". "(3 after Holm correction)" added via new macro \TrChanceSigHolm (make_numbers.py). Intro: benchmark vs deployment sentences. Sec. III-D: test proposed as a reporting device, not an O-RAN requirement. predicate_section.tex: unsupported "tier-one team of three analysts" justification removed; "Does the test discriminate?" -> "Is the test attainable?" with corrected logic. Limitations: new paragraph on declared parameters and the test. Table 2 caption corrected (D_B also trains reverse direction and references).
- references.bib: obiuwevwi2026realtime now the ICCCN 2026 paper (DOI 10.1109/ICCCN69946.2026.11662852, Crossref-checked); ilias2024moe5g note names the Front. AI 2026 version (the cited 99.95% is from arXiv v2). Abraheem journal DOI 10.63318/waujpasv4i2_24 returns 404 -> not added. New scripts/verify_references.py -> reports/reference_check_2026-09-25.csv: 50 verified, 10 partial (no DOI), 2 unverified (O-RAN specs). Risk found: Fard et al. describe NetsLab-5GORAN-IDD as 42 runs vs our 30 recovered radio sessions -> needs a reconciling sentence.
- Checks: build 19 pages, 0 errors, 0 undefined, 0 overfull; pytest 61/61; withdrawn-claims OK; placeholders OK; final_validation 20 PASS 1 WARN 2 BLOCKED 0 FAIL; reproduce.py paper 37 of 37 identical after refreezing expected_outputs.json (numbers.tex gained one macro). REPRODUCE.md page count 18 -> 19. Not committed.
- 2026-09-25 night (Adeel: fix the remaining items except authors/affiliations, rebuild Figure 2 from Downloads, title in one sentence without a colon, humanize-latex and writing-style skills, then the forensic reference prompt, IEEE guideline check, no AI-use statement, and verify code/zip/repo/paper are in sync). Report sections: finalization_audit_2026-09-25.md "Second pass" (S01-S11, open issues) and reports/reference_forensics_2026-09-25.md (Reports A-K).
- Title: "What Held-Out Accuracy Predicts About Deploying Intrusion Detection in O-RAN" (main.tex, README, REPRODUCE, response letter, audit report). Running head "Held-Out Accuracy and Deployment of O-RAN Intrusion Detection" (the IEEE "Authors: short title" form keeps its colon).
- Figure 2 rebuilt (figure-rebuild skill) from Downloads Academic_research_figure_layout..._20260925175932.jpg (the second-newest of two, the less machine-made one); both candidates copied to figures/source/fig2_candidate_{a,b}.jpg. scripts/extract_figure2_icons.py -> figures/icons/f2_*.png (14). Palette gPanel..gPink in figstyle.tex. Seven render errors corrected (own caption drawn in; radio routed into the flow-only shared space; floors drawn twice; "booster" and "tracking progression toward realism" prompt text; measured brace covered untimed terms; no D_C; how-to-read box). Runtime shown as a vertical list, timed stages solid, untimed dashed. decorations.pathreplacing added to main.tex.
- O-RAN specs now public ETSI editions, both PDFs read: etsi_e2gap = ETSI TS 104 038 V4.1.0 (O-RAN.WG3.E2GAP-R003-v04.01; "10 milliseconds up to 1 second") and etsi_wg11_threat = ETSI TR 104 106 V3.0.0 (WG11 threat model; clauses on Near-RT RIC and xApp threats). Budget sentences say "the O-RAN E2 specification".
- EXP-059 (experiments/run_session_rule.py): gap rules 90-105 s give exactly 42 category-pure segments (Fard et al.'s 42 runs), nested in our 30 five-minute sessions; 10 sessions hold 2-3 subcategories. Sentence + SessRun* macros in Sec. IV-A.
- lambda_b anchored with jin2013softcell (CoNEXT 2013, Crossref-checked; quote read in arXiv 1305.3568). Hyperparameter-rationale sentence in IV-C.
- EXP-060 (run_latency_v2.py gained --exp, --radio-only, --keep-samples; defaults unchanged): attempt 1 ran while I was building the paper, stages timed then were ~5x slower; moved to results/EXP-060/attempt1_concurrent_load/ with WHY_NOT_USED.txt. Clean re-run alone (1029 s): medians 1.02-2.1x EXP-043 (median 1.46), aggregation+ONNX p99 upper bound <= 0.36 ms. Fig. 11 is now an empirical CDF (logit axis) from EXP-060; Table XXI and all latency numbers stay EXP-043. LatRep* macros; one sentence in latency_section on host-state dependence.
- humanize-latex pass: abstract, intro, discussion, conclusion, limitations; "therefore" 18 -> 5; conclusion semicolon chain split; stale "separates predictive evaluation" bullet and "two exporters" fixed; three corpora in reproducibility section; "licence" -> "license". writing-style applied to the reports (no semicolons, no em dashes).
- IEEE style: 44 serial commas added (hand-checked list); "et al." no longer italic (8); tables renumbered in order of first citation (conflict table and figure moved before the target-reference table, benign table before time-split, two early citations redirected). No AI-use statement anywhere (checked), none added.
- Forensic reference audit (scripts/audit_references_forensic.py, audit_pdf_links.py, write_reference_report.py): 62 references, 47 DOIs all resolve, Crossref author lists match position by position, no-DOI entries checked on USENIX/PMLR/JMLR/NeurIPS/arXiv/ETSI pages. Fixes: hyperref (hidelinks) added (PDF had no links); new paper/IEEEtran_doi.bst prints linked "doi: ..." (IEEEtran ignored doi); ICCCN names set to the DOI record (Nannou, Ur Rahman; arXiv spelling in a comment); my first version put % comments inside that BibTeX entry and emptied reference [21] -> fixed and build_paper.py now fails on BibTeX warnings/errors; Shi et al. dropped from the RIC-placement sentence; xApp sentence split by what its sources show; Apruzzese "surveyed" -> "examined"; pages for Niknam (215-220) and Scalingi (41-50). WAUJPAS DOI 10.63318/waujpasv4i2_24 returns 404 and is not used.
- Checks: build 19 pages, 0 errors, 0 undefined, 0 bibtex warnings; reproduce.py paper 37 of 37 identical (manifest refrozen); pytest 61/61; final_validation 20 PASS 1 WARN 2 BLOCKED 0 FAIL; diff.pdf 27 pages 0 errors. EXPERIMENTS.md, REPRODUCE.md, registry and reproduce.py list EXP-059/060.
- 2026-09-26 01:40: push of 8ebee74 rejected by GitHub (GH001): results/EXP-060/attempt1_concurrent_load/latency.err.log was 5.2 GB (26 million scikit-learn warning lines written during timed calls, which also explains part of that attempt's slowness). Replaced by latency.err.excerpt.log (first 40 and last 20 lines, sizes recorded), WHY_NOT_USED.txt updated, unpushed commit amended so the large blob is not in history, zip rebuilt.
