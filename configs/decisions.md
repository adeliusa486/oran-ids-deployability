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
- **Status:** `DECIDED 2026-09-20 — option (b), published features on both sides`
- **Raised by:** EXP-000
- **Decided by:** project owner, after the trade-off below was presented

### Decision

**Option (b): use `D_A`'s published Zeek/CSV features and `D_B`'s published Argus CSV.**
The A3 single-exporter control is **not** applied.

### Consequences, stated plainly

This is the option the plan called non-negotiable-against. The owner was shown the
trade-off and chose it. Recording what it costs, so that no later phase can pretend
otherwise:

1. `Δ_F1` now conflates **deployment distribution shift** (what we claim to measure)
   with **flow-exporter differences** — timeout semantics, direction inference, field
   definitions, rounding — between Zeek and Argus. These are not separable post hoc.
2. The measured degradation is therefore an **upper bound** on true deployment shift,
   not an estimate of it. Every statement of `Δ_F1` must carry that qualifier.
3. Claim C2 cannot be stated as "models lose X points to deployment shift". It must be
   stated as "models lose X points across an independently collected deployment
   *and* an independent feature-extraction pipeline", which is the honest description
   of what was measured — and is arguably the more realistic deployment condition,
   since a real operator inheriting a model also inherits someone else's exporter.
4. The shared feature space shrinks to fields that are **semantically** comparable
   between Zeek `conn.log` and Argus, which may be fewer than the planned 24. The
   actual intersection must be enumerated in EXP-001 and the count reported.

### Mitigation M1 — measure the confound rather than ignore it (MANDATORY)

Option (b) removes the control. It does not remove our ability to **bound** the term.
`D_B` publishes both raw pcapng (3.65 GB, tractable) and the Argus CSV derived from it.
Therefore:

> Recompute `D_B`'s features from its own pcapng with a single pinned exporter, compare
> against `D_B`'s published Argus CSV on the same flows, and report per-feature
> agreement (correlation, and distributional distance for the features we use).

This is the plan's T-A3 verification, run on one corpus instead of two. It yields a
*measured* estimate of how much of `Δ_F1` a change of exporter can produce, on data
where deployment shift is held at zero by construction. That number goes in an
appendix and is cited wherever `Δ_F1` is stated.

Low per-feature agreement is **not a result to hide**. It is direct evidence of how
large the confound can be, and reporting it is what makes the headline number
interpretable under option (b).

### Mitigation M2 — sensitivity to the feature intersection

Report `Δ_F1` on the semantically-comparable intersection **and** on a conservative
sub-intersection that drops every feature whose Zeek/Argus definitions differ in any
respect flagged by M1. If the two agree, the confound is small in practice. If they
diverge, that divergence is the headline caveat.

### What would reverse this

M1 showing severe disagreement (say, median per-feature correlation below ~0.9 on the
features we use). At that point option (b)'s `Δ_F1` is not interpretable and the
project must either fall back to option (a) or reframe the contribution away from a
`Δ_F1` magnitude and toward the qualitative collapse plus the operational criteria.

---

### Context that preceded the decision (retained, not rewritten)

**Problem.** Plan §A3 makes it non-negotiable that one exporter at one pinned version
processes **both** corpora from raw packet captures, because mixing a self-computed
feature set with a published CSV confounds deployment shift with exporter differences.
EXP-000 measured the cost of honouring that: `D_A` raw captures total **~1.5 TB**
(Benign 5.9 GB, DoS 3.5 GB, DDoS 3.1 GB, BruteForce 3.3 GB, Web 594 MB compressed; 1.5 TB
uncompressed total per the Zenodo record), against `D_B`'s ~3.65 GB. Full-scale
single-exporter processing of `D_A` is not feasible on the available hardware.

**Options as presented.**

| Option | Cost | Consequence | Outcome |
|---|---|---|---|
| **a** Pre-registered stratified subsample of `D_A` pcaps (class × run × time block), one exporter over the subsample and over all of `D_B` | moderate | A3 control preserved; sampling step must be declared, seeded and its per-class retention reported | recommended, **not chosen** |
| **b** `D_A` published Zeek/CSV + `D_B` published Argus CSV | cheap | Two different exporters; the confound A3 exists to remove is present | **CHOSEN** |
| **c** Published features both sides, plus an extractor-agreement study to measure the confound | cheap | Weaker headline; confound reported rather than controlled | partially adopted as **M1** |
| **d** One exporter over the full `D_A` and `D_B` | infeasible here | needs ~2 TB storage and substantial compute | not viable |

**Analyst recommendation at the time** was option **a**. The project owner chose **b**.
The recommendation is retained here unedited so the record shows what was traded away;
mitigations M1 and M2 above are the conditions under which **b** remains publishable.

---

## D-005 — Track C fallback level

- **Phase:** 0, executes in Phase 9/10
- **Status:** `DECIDED 2026-09-20 — Level 2`
- **Raised by:** EXP-000
- **Decided by:** project owner

`docs/RUNTIME.md` defines three fallback levels and the plan (§7.6) says to decide
early. EXP-000 established that the development host is **Windows 11**, while the
runtime methodology requires `isolcpus`, `nohz_full`, `cpupower` and `pidstat` — all
Linux. Track C cannot run on the development host.

### Decision

**Level 2 — a real Near-RT RIC with a synthetic E2 load generator, no gNB**, on a
Linux machine with root access. Level 1 (real RIC + real gNB + real E2) is not
available; Level 3 (container only) is not necessary.

### What Level 2 supports, and what it does not

| Claim | Supported at Level 2? |
|---|---|
| C9 — p99 against the near-RT budget | **Yes, qualified.** The RIC and the xApp are real and the E2 path is exercised; the load is synthetic, so the arrival process is ours rather than a real RAN's |
| C10 — feature construction dominates latency | **Yes.** This is the strongest Level-2 claim |
| C11 — sustainable throughput `T_max` | **Yes** — a synthetic generator is in fact the right instrument for a load sweep |
| CPU / RAM under load | **Yes** |
| Behaviour under a real RAN's arrival process and jitter | **No.** Must appear in Limitations |
| End-to-end latency including over-the-air effects | **No** |

### Required labelling

The paper and README must both state the level. Permitted phrasing: *"measured on a
real Near-RT RIC under synthetic E2 load"*. **Forbidden:** any phrasing implying a
live RAN, and the bare words *real deployment*.

### Prerequisites now on the critical path for Phase 9

1. A Linux host with root, isolated cores (`isolcpus`, `nohz_full`, `rcu_nocbs`),
   governor set to `performance`, turbo disabled, `OMP_NUM_THREADS=1`.
2. A Near-RT RIC: FlexRIC or the O-RAN SC RIC. FlexRIC is the lighter target and is
   what P04 and P06 both used, which also makes our numbers comparable to theirs.
3. A synthetic E2 load generator with a controllable and *recorded* arrival process.
   The arrival distribution is a reported parameter, not an implementation detail —
   a Poisson process and a periodic one produce different tails.
4. The floor experiment (D-007) runs before any model is timed.

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
| I1 | One exporter over both corpora, from pcap | plan (A3) | **`withdrawn`** — D-004 decided against it. Replaced by M1 + M2 |
| M1 | Measure the exporter confound on `D_B` (recompute from pcapng, compare to published Argus) | D-004 | **`mandatory`** |
| M2 | Report `Δ_F1` on both the feature intersection and a conservative sub-intersection | D-004 | **`mandatory`** |
| I2 | `source` normalisation primary, three modes reported | plan (A2) | `decided`, unimplemented |
| I3 | Split-seed × model-seed nesting | plan (A5) | `decided`, unimplemented |
| I4 | π and λ_b swept as surfaces | plan (A6) | `decided`, unimplemented |
| I5 | Add majority-class, single decision tree and isolation forest baselines | plan | `decided`, unimplemented |
| I6 | Test the Algorithm 1 early-exit path (E5c) | plan | `open` |
| I7 | ECE with bootstrap CIs | plan | `decided`, unimplemented |
| I8 | Second hardware class for E5 | plan (A10) | `open` — now feasible: the Windows dev host is a natural second class alongside the Linux measurement host, though only for coarse comparison |
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
