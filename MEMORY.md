# O-RAN IDS Research Memory

> Permanent research memory. Read this and `configs/experiment_registry.yaml` before
> starting any phase. Never rewrite history here — append corrections instead.
> Last updated: 2026-09-20 (EXP-000)

---

## Current Phase

Phase 0 complete. **Phase 1 (dataset discovery and source corpus verification) is next.**

## Current Experiment

EXP-000 complete. **EXP-001 is next**: download and verify NetsLab-5GORAN-IDD at the
artefact level.

## Overall Status

The repository is a planning artefact with 0 lines of research code and four live,
correctly failing guards. The manuscript is structurally complete with every numeric
value synthetic and machine-detectably marked. The project's declared blocker (gate A1,
unidentified source corpus) is **provisionally resolved**; the binding constraint is now
artefact-level verification, not corpus discovery.

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
| Source `D_A` | **NetsLab-5GORAN-IDD** | **candidate, unverified.** DOI `10.1109/IEEEDATA.2025.3614167`; Zenodo 18923275; Kaggle `10.34740/kaggle/ds/7416931`; CC-BY-4.0. Raw `.pcap` at O-CU + 22 PHY/MAC radio metrics from O-DU over E2 + Zeek logs. 6 classes. OAI testbed at UCD: 1 O-CU, 2 O-DU, 1 O-RU, Dell Precision 7920, 2 physical UEs. **~1.5 TB total**; `Network_Dataset.csv` 227 MB, `Lower_Layer_Data.db` 5.4 MB |
| Target `D_B` | **5G-NIDD** | resolved, not downloaded. DOI `10.21227/xtep-hv36`. Raw pcapng published (BS1 2.2 GB, BS2 1.45 GB) — this is what makes the A3 single-exporter control feasible. No radio KPIs. `group_key: src_ip`. `role: transfer_only` |
| External | **O-RAN E2SM-KPM DoS dataset** | candidate for Phase 13. `10.5281/zenodo.21198102`, MIT, 69.8 MB, University of Regina. Zenodo record has no description; feature overlap unknown |

**Unknown for `D_A`, and all of it blocks split design:** record counts, label column
names, per-record timestamps, device/run identifiers, CU–DU synchronisation tolerance,
class balance, duplicate rate.

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

---

## Important Decisions

Full register: `configs/decisions.md`.

| ID | Decision | Status |
|---|---|---|
| D-001 | Adopt NetsLab-5GORAN-IDD as `D_A` (plan option A1-b) | decided, provisional |
| D-002 | `D_B` = 5G-NIDD, transfer-only, enforced in code | decided |
| D-003 | `source` normalisation primary; report all three modes | decided |
| **D-004** | **`D_A` subsampling policy for the single-exporter control** | **OPEN — blocking for Phase 2** |
| **D-005** | **Track C fallback level** | **OPEN — decide before any runtime work** |
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

---

## Known Limitations

1. **Track C cannot run on this host.** Windows 11; `docs/RUNTIME.md` requires
   `isolcpus`, `nohz_full`, `cpupower`, `pidstat` — all Linux. D-005 is unavoidable.
2. **A3 single-exporter control is in tension with `D_A`'s size.** 1.5 TB versus 3.65 GB.
   D-004 must resolve this before any feature is computed.
3. **Literature depth.** 0 full texts. Absence claims are provisional.
4. **P05 unretrievable** (HTTP 403) — one of only two latency comparators.
5. **Energy (C15) is not measurable** with the planned method (A8), and no retrieved
   source measures it either. Recommend accepting I9 and dropping the column.
6. **Table VIII (C13) has no underlying study.** `reports/literature_audit.md` is **not**
   that study — a keyword search has selection bias by construction.
7. **Two corpora only**, so "cross-deployment" means one pair plus its reverse.

---

## Open Questions

1. Does `D_A` expose a usable per-record device or run identifier? *(blocks A4)*
2. Can CU flow records be joined to DU radio telemetry, and at what time-alignment
   error? *(blocks C5 entirely — if not, C5 is withdrawn, not weakened)*
3. What is `D_A`'s true class balance and duplicate rate?
4. What windowing did P03 use, and does ours reproduce their 27–46% DoS→Benign confusion?
5. Does the `Δ_F1` ordering across architectures survive a change of evaluation protocol?
   *(I12, raised by P14)*
6. At what budget in [10 ms, 1 s] does each architecture cross out of deployability?
   *(I11 — this may be the paper's most useful single figure)*
7. Does the P23 external corpus share enough features with our shared space to be usable?
8. Is our 24-feature shared space actually computable from both corpora with one exporter?

---

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
| *(see below)* | EXP-000: repository and literature reconstruction | *(recorded at commit time)* |

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
- **Do not re-search gate A1 as though it were open.** It is provisionally closed;
  the open item is verification.

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
