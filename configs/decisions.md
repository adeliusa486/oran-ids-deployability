# Decision Register

Every decision that constrains a later experiment is recorded here **before** the
experiment runs. A decision made after seeing a result is not a decision, it is a
rationalisation, and it belongs in the experiment report as a deviation instead.

Format: `D-nnn` decisions; `I-nn` improvements carried from
`docs/IMPLEMENTATION_PLAN.md` §4 plus new ones raised by later phases.

Status values: `open` | `decided` | `superseded` | `deferred`

---

## D-001 — Adopt NetsLab-5GORAN-IDD as the candidate source corpus `D_A`

- **Phase:** 0 (EXP-000), to be confirmed in Phase 1 (EXP-001)
- **Status:** `decided, provisional`
- **Date:** 2026-09-20

**Context.** Gate A1 blocked the project: the manuscript described `D_A` as "an O-RAN
testbed capture with synchronised packet traces and radio KPIs" while citing platform
papers, not a corpus. The plan gave four options (A1-a collect, A1-b find, A1-c
packet-only, A1-d synthesise).

**Decision.** Pursue **A1-b** with NetsLab-5GORAN-IDD (Abed Zadeh et al., IEEE Data
Descriptions 2025, DOI `10.1109/IEEEDATA.2025.3614167`, CC-BY-4.0).

**Why.** It is the only retrieved public corpus with all three required properties:
raw `.pcap` at the O-CU, 22 PHY/MAC radio metrics per record from the O-DU over E2, and
labelled attack classes, from a physical OpenAirInterface O-RAN testbed. It preserves
the radio-KPI ablation (C5) that options A1-c and A1-d would destroy or falsify.

**What would reverse this.** Artefact-level inspection (EXP-001) finding any of:
no usable per-record device or run identifier; no reliable CU–DU time alignment; label
granularity coarser than the flow/window unit; or a licence restriction on redistribution
of derived features.

**Consequences accepted.** We inherit Fard et al. (IEEE CSR 2026) as prior work on this
corpus, which rescopes claim C5. See `docs/literature/GAP_MATRIX.md` §3.

---

## D-002 — `D_B` remains 5G-NIDD, and remains transfer-only

- **Status:** `decided` (inherited from the plan, re-affirmed)

Already resolved in `configs/corpora/d_b.yaml`. Re-affirmed here because EXP-000
confirmed that raw pcapng is published (BS1.zip 2.2 GB, BS2.zip 1.45 GB), which is what
makes the A3 single-exporter control feasible on the `D_B` side.

The `role: transfer_only` field must be enforced in code (A11), not asserted.

---

## D-003 — Source-fitted normalisation is primary; all three modes are reported

- **Status:** `decided` (inherited from the plan, I2)

`primary_normalisation: source` in `configs/base.yaml`. `target_unsup` is reported as a
transductive *mitigation*, `none` as a scale-sensitivity upper bound. Reporting the
spread pre-empts the A2 criticism rather than hiding from it.

---

## D-004 — `D_A` subsampling policy for the single-exporter control (A3)

- **Phase:** 1 (EXP-001)
- **Status:** `open — BLOCKING for Phase 2`
- **Raised by:** EXP-000

**Problem.** Plan §A3 makes it non-negotiable that one exporter at one pinned version
processes **both** corpora from raw packet captures, because mixing a self-computed
feature set with a published CSV confounds deployment shift with exporter differences.
EXP-000 measured the cost of honouring that: `D_A` raw captures total **~1.5 TB**
(Benign 5.9 GB, DoS 3.5 GB, DDoS 3.1 GB, BruteForce 3.3 GB, Web 594 MB compressed; 1.5 TB
uncompressed total per the Zenodo record), against `D_B`'s ~3.65 GB. Full-scale
single-exporter processing of `D_A` is not feasible on the available hardware.

**Options.**

| Option | Cost | Consequence |
|---|---|---|
| **a** Pre-registered stratified subsample of `D_A` pcaps (by class × run × time block), one exporter over the subsample and over all of `D_B` | moderate | A3 control preserved; introduces a sampling step that must be declared, seeded and reported, including the per-class retention rate |
| **b** Use `D_A`'s published Zeek/CSV features and `D_B`'s published Argus CSV | cheap | **Rejected.** Two different exporters. This is exactly the confound A3 exists to remove |
| **c** Use published features for both and measure the confound instead of removing it (extractor-agreement study, plan T-A3) | cheap | Weaker headline; the confound becomes a reported term rather than a controlled one |
| **d** One exporter over all of `D_B` and over the full `D_A` | infeasible here | Requires ~2 TB of storage and substantial compute |

**Recommendation (not yet decided).** Option **a**, with option **c**'s agreement study
run *anyway* as an appendix, because the agreement measurement is what proves the
control worked. Option **a** must fix the subsample seed and the retention policy in
config before any feature is computed.

**Decide by:** end of Phase 1. Blocking for Phase 2.

---

## D-005 — Track C fallback level must be chosen now

- **Phase:** 0, executes in Phase 9/10
- **Status:** `open — decide before any runtime work begins`
- **Raised by:** EXP-000

`docs/RUNTIME.md` defines three fallback levels and the plan (§7.6) says to decide
early. EXP-000 established that the development host is **Windows 11**, while the
runtime methodology requires `isolcpus`, `nohz_full`, `cpupower` and `pidstat` — all
Linux. Track C cannot run here.

**Levels:** (1) real RIC + real gNB + real E2; (2) real RIC + synthetic E2 load;
(3) xApp container only, E2 encode/decode included, no RIC.

Whatever is chosen must be stated in the paper and the README, and a level-3 result
must be labelled **emulated deployment**, never **real deployment** (master protocol
§Phase 9).

---

## D-006 — Report `p99`, and never report mean latency alone

- **Status:** `decided`

Required percentiles: p50, p95, p99; p99.9 and max where the sample size supports them.
Stages reported separately: feature extraction, model inference, serialisation,
transport, xApp processing, end to end.

Justification strengthened by EXP-000: P04 reports p95 only, P10 reports a single
aggregate overhead. The tail is where the open question is.

---

## D-007 — The floor experiment runs before any model is timed

- **Status:** `decided` (inherited from `docs/RUNTIME.md`)

An xApp whose model is `lambda x: 0.0` establishes the platform floor. If the floor p99
is already near the budget, the latency finding is about the platform, not the models,
and the paper must say so.

---

## Improvements register

Carried from `docs/IMPLEMENTATION_PLAN.md` §4, plus those raised by EXP-000.

| ID | Improvement | Origin | Status |
|---|---|---|---|
| I1 | One exporter over both corpora, from pcap | plan (A3) | `open` — contingent on D-004 |
| I2 | `source` normalisation primary, three modes reported | plan (A2) | `decided`, unimplemented |
| I3 | Split-seed × model-seed nesting | plan (A5) | `decided`, unimplemented |
| I4 | π and λ_b swept as surfaces | plan (A6) | `decided`, unimplemented |
| I5 | Add majority-class, single decision tree and isolation forest baselines | plan | `decided`, unimplemented |
| I6 | Test the Algorithm 1 early-exit path (E5c) | plan | `open` |
| I7 | ECE with bootstrap CIs | plan | `decided`, unimplemented |
| I8 | Second hardware class for E5 | plan (A10) | `open` |
| I9 | Drop the energy column unless A8 is resolved | plan | **recommend accept** — EXP-000 found no retrieved source that attributes container energy either |
| I10 | Execute or delete Table VIII | plan (A9) | `open` — see `reports/literature_audit.md` §5 |
| **I11** | **Sweep the near-RT budget `B` over [10 ms, 1 s] instead of asserting `B = 10 ms`** | **EXP-000** | **`decided`** |
| **I12** | **Test whether the per-architecture `Δ_F1` ordering is stable across evaluation protocols / prevalence conventions** | **EXP-000** | **`decided`** |
| **I13** | **Add a non-learned cross-layer consistency baseline to the ladder** | **EXP-000** (P24) | `open` |
| **I14** | **Measure latency per pipeline stage, since P04 shows inference is microseconds** | **EXP-000** (P04) | **`decided`** |
| **I15** | **Widen or explicitly bound the threat model: message-level and control-logic threats exist (P10, P11, P12)** | **EXP-000** | `open` |

### I11 in detail — why the budget sweep matters

P04 (ICCCN 2026) assumes `B = 10 ms` and concludes AI in a Near-RT RIC xApp is feasible.
P05 (2026) assumes `B = 1000 ms` and concludes the same for models that are two orders
of magnitude slower. O-RAN specifies the near-real-time control loop over **10 ms to
1 s**. A single-value budget therefore makes any binary deployability predicate an
authoring choice.

Reporting `q_0.99(L)` against a swept `B` yields the **budget at which each architecture
crosses from deployable to not deployable**. That is a more useful and more defensible
result than a pass/fail table, and it directly answers the question an operator has.

Equation (7) in the manuscript should be re-expressed as a function of `B`, with the
`B = 10 ms` case reported as the strict instance rather than as the definition.
