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

> ### ⚠ PREMISE CORRECTION — 2026-09-20, EXP-001
>
> **The size figure this decision rested on was wrong.** EXP-000 recorded `D_A` raw
> captures as ~1.5 TB, taken from a page summary rather than from the record. The
> Zenodo REST API gives the **entire record as 16.85 GB**: five pcap zips totalling
> 16.40 GB (Benign 5.94, DoS 3.47, DDOS 3.09, BruteForce 3.32, Web 0.59) plus 0.44 GB
> of summary artefacts.
>
> `D_A` raw is therefore about **4.5x** `D_B` raw, not about **400x**. Option (a) —
> a stratified pcap subsample with one exporter over both corpora — is affordable, and
> so in fact is option (d), running one exporter over *everything*, at roughly 17 GB of
> download and ordinary single-machine compute.
>
> **The infeasibility premise behind this decision does not hold.** The decision stands
> only because it was taken by the owner; it is flagged for revisit and the mitigations
> below remain mandatory while it stands. If it is revisited and reversed, `I1` is
> reinstated, `M1` becomes the full two-corpus T-A3 agreement study, and claim C2 can be
> stated as deployment shift rather than as deployment-shift-plus-exporter.

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
| I1 | One exporter over both corpora, from pcap | plan (A3) | **`REINSTATED`** 2026-09-20 by D-008 route (a). D-004 is reversed for `D_A` |
| M1 | Measure the exporter confound on `D_B` (recompute from pcapng, compare to published Argus) | D-004 | **`mandatory`** — still runs; it is what demonstrates the control worked |
| M2 | Report `Δ_F1` on both the feature intersection and a conservative sub-intersection | D-004 | **`retained`** — now a robustness check rather than a mitigation |
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

---

## D-008 — Route for claim C5 after the CU/DU join failed

- **Phase:** 1 (raised by EXP-001)
- **Status:** `DECIDED 2026-09-20 — route (a), re-extract from the raw archives`
- **Raised by:** EXP-001, 2026-09-20

### What happened

EXP-001's pre-registered failure criterion fired:

> *"CU–DU join impossible → claim C5 is withdrawn, not weakened."*

Measured, from the artefacts (`results/EXP-001/statistics/join_analysis.json`):

| Join level | Result |
|---|---|
| L0, shared record identifier | **impossible.** Radio has `ue_id`, `rnti`, `cellid`; network has `uid`, `src_ip`, `dst_ip`, ports. Intersection empty |
| L1, shared time axis | **impossible.** The radio DB has `timestamp`; `Network_Dataset.csv` has **no time column** — Zeek's `ts` was dropped when the summary was built |
| L2/L3, run or category level | possible, but only through a hand-written mapping: 19 radio subcategories against 15 network attack types, **zero exact string overlap** |

The two layers also differ sharply in composition (dos 10.4% radio against 36.7%
network; attack prevalence 76.4% against 90.1%), so even a category-level join
associates populations that are not the same sample.

### Options

| Route | Cost | Consequence for C5 |
|---|---|---|
| **(a) Re-extract from the raw per-category archives** — `.pcap` and the per-category radio `.txt` both carry timestamps, so an L1 time join is recoverable | 16.4 GB download, one exporter run, build and validate the join (EXP-001c) | **C5 survives intact.** Also reinstates the A3 single-exporter control on the `D_A` side, so it resolves the D-004 premise correction at the same time |
| **(b) Restrict C5 to run-level late fusion** | cheap | A **different, weaker claim**. Run-level fusion cannot show that radio features are deployment-specific *within* a flow. It must be **renamed**, not relabelled |
| **(c) Withdraw C5** | free | The pre-registered outcome. The paper survives on RQ1–RQ3; the gap matrix's G6 is dropped |

### Recommendation

**Route (a).** Three reasons, none of them "we want the claim to survive":

1. The cost premise that ruled it out has already been corrected — 16.4 GB, not 1.5 TB.
2. Prior work on this corpus (Fard et al., IEEE CSR 2026) fuses these modalities, so
   the join demonstrably exists in the raw data. Route (a) is not speculative.
3. It fixes two problems with one action: C5 becomes evaluable, and the A3 control is
   restored on the `D_A` side, which upgrades `Δ_F1` from an upper bound to an estimate.

If route (a) is chosen, EXP-001c runs next and D-004 is formally reversed for `D_A`.
If route (b) or (c) is chosen, C5's text changes in the manuscript before any
experiment is run, not after.

### Guard against the wrong kind of reasoning

Route (a) must be judged on whether the join *exists*, not on whether it rescues the
claim. EXP-001c has its own pre-registered failure criterion: if the joined fraction is
too low to support an ablation, **C5 is withdrawn**, and route (a) having been attempted
is not a reason to weaken that.

---

### DECISION — 2026-09-20, project owner: **route (a)**

**Re-extract from the raw per-category archives.** EXP-001c is authorised and becomes
the next experiment.

Basis on which it was taken (all three established before the decision, not after):

1. The cost premise that originally ruled route (a) out was wrong. The whole Zenodo
   record is **16.85 GB**, of which 16.40 GB is pcap archives — not the ~1.5 TB
   EXP-000 recorded.
2. The join demonstrably exists in the raw data. P03 (Fard et al., IEEE CSR 2026)
   performs it on this corpus, aligning the layers by **run-relative timestamps** taken
   from the raw per-category archives, and assigning time from the sample index at 1 Hz
   for DoS traces whose telemetry lacks timestamps.
3. The alternative routes were worse for reasons independent of the claim's survival:
   route (b) joins populations that differ in composition by up to 26 percentage points
   and cannot address the within-flow question C5 asks; route (c) discards the only part
   of the paper that uses the radio modality.

**Consequential changes:**

- **D-004 is REVERSED for `D_A`.** The A3 single-exporter control is reinstated on the
  `D_A` side. `use_artefact` returns to `pcap`.
- **I1 is reinstated** and supersedes M1/M2 for `D_A`. M1 (the `D_B` exporter-agreement
  study, EXP-001b) **still runs**, because `D_B`'s published Argus CSV remains the point
  of comparison and the agreement measurement is what demonstrates the control worked.
- `Δ_F1` is upgraded from an *upper bound* to an *estimate*, conditional on EXP-001b
  showing acceptable agreement.

**The failure criterion is unchanged and is not softened by this decision.** EXP-001c
pre-registers: if the joined fraction is too low to support an ablation, **C5 is
withdrawn, not weakened**. Having spent the download is not a reason to keep the claim.

**Pilot first.** `Web.zip` (594 MB, the smallest category) is downloaded and the join is
validated end to end on it before the remaining 15.8 GB is fetched. If the method does
not work on one category it will not work on five, and the pilot costs 4% of the data.

**Storage.** Raw archives live at `C:/Users/adeel/oran-ids-data/`, deliberately outside
the OneDrive-synced project tree, so that 16 GB of packet captures is not uploaded to
the owner's cloud storage. The path is recorded in provenance; nothing in the repository
depends on its value.

---

## D-009 — Cut the experimental programme to a Q1 paper, not a thesis

- **Phase:** 1
- **Status:** `DECIDED 2026-09-20`
- **Decided by:** project owner ("we don't need so big experiments, do those which are
  easily acceptable in a normal Q1 research paper")

### Problem

The registry held 27 experiments across 23 phases. That is a multi-year programme. A Q1
journal paper needs a defensible core, not exhaustive coverage, and an over-scoped plan
mostly produces half-finished experiments that a reviewer reads as padding.

### What we keep — the core five

Each is kept because a reviewer would ask for it, not because it is available.

| Keep | Why a reviewer requires it |
|---|---|
| **X1 In-distribution baselines** on `D_A` | Without it no other number has a reference. Includes the trivial majority-class floor, which is what shows the task is non-trivial |
| **X2 Cross-deployment transfer** `D_A -> D_B` | The headline. RQ1. This is the paper |
| **X3 Radio / network / fusion ablation** | The only genuinely novel claim we still own (the transfer half of the sign-flip). Requires the raw-archive join, which is already validated |
| **X4 Alert burden over a base-rate sweep** | Pure post-processing of X2. Near-zero cost, and it is the criterion that turns an accuracy result into a deployability result |
| **X5 Latency with p50/p95/p99 over a swept budget** | RQ3, and the swept budget is our strongest methodological contribution (a single 140 ms measurement passes a 1 s budget and fails a 10 ms one) |

Plus the statistical spine that makes them citable: multiple seeds, run-disjoint splits,
confidence intervals, and generated tables.

### What we cut, and what each cut costs

| Cut | Was | Cost of cutting |
|---|---|---|
| Adversarial robustness (Phase 8) | EXP-008 | None to this paper. Gap G7 was graded **weak** anyway, so it was never a novelty claim. Becomes future work |
| RIC fault-injection tests (Phase 10) | EXP-010 | Low. X5 still measures latency on a real Near-RT RIC; we simply do not also test restart and recovery |
| Model compression / quantisation (Phase 11) | EXP-011 | Low. Interesting, but a separate paper |
| Longitudinal drift (Phase 12) | EXP-012 | Moderate, and genuinely a shame: the corpus has a 53-day span that would support it. Recorded as the single best follow-up |
| Third external corpus (Phase 13) | EXP-013 | Moderate. Two corpora is the honest limitation and is already in the Limitations section |
| Systematic reporting survey (Track D) | EXP-D01 | None. It had no evidence behind it. **Table VIII is deleted** and claim C13 becomes a qualitative observation with a few named examples, which is what plan A9 recommended anyway |
| Energy per decision | E5d | None. Already recommended for withdrawal under I9: RAPL cannot attribute energy to a container |
| Few-shot adaptation | EXP-012/E7 | Low. Mentioned as future work |

### What does NOT get cut, however tempting

- Multiple seeds and confidence intervals. A single-seed result is not publishable.
- Run-disjoint splitting. A random split would inflate every number.
- The trivial majority-class baseline. Without it the transfer result cannot be
  interpreted.
- Reporting negative results.

Scope reduction is about **how many questions we ask**, never about how carefully we
answer the ones we keep.

---

## D-010 — Bulk pcap download stopped; C5 withdrawn; multi-pair transfer adopted instead

- **Phase:** 1
- **Status:** `DECIDED 2026-09-20`
- **Decided by:** project owner ("yes don't need to download")

### What was stopped

The 16.4 GB raw-archive download, at 3.7 GB. Kept on disk: `Web.zip` (0.59 GB) and
`DDOS.zip` (3.09 GB), both complete. Deleted: partial `DoS.zip` and `BruteForce.zip`.
Never started: `Benign.zip`.

### Direct consequence: claim C5 is WITHDRAWN

This is the pre-registered outcome from EXP-001, recorded before the data was seen:

> *"CU–DU join impossible → claim C5 is withdrawn, not weakened."*

The join itself is not the problem — EXP-001c proved it works at a 96.2% median rate.
The problem is coverage. The two complete archives are **Web and DDoS, both attack-only**.
`Benign.zip` was never fetched, so there are **no benign joined windows**, and a detector
cannot be trained or evaluated without them.

**C5 is withdrawn, not weakened, and the manuscript's Section VI-C is deleted rather than
softened.** What must NOT happen is a rescue attempt: reporting a fusion result on
attack-only data, or quietly redefining C5 as something the available data can support.

### What survives as an observation, clearly labelled as one

One structural point remains and costs nothing: **`D_B` exports no radio telemetry at
all.** The modality that helps most in-distribution (P03: radio beats flow by 8.5–11.7
ROC-AUC points, on this same corpus) is the one least likely to exist in another
deployment. That is a real deployability argument and prior work does not make it.

It must be written as a **structural observation with prior work cited for the
in-distribution half**, never as our measured ablation. No number of ours attaches to it.

### The replacement, and it is a better experiment

`docs/IMPLEMENTATION_PLAN.md` §21, risk **R4**, anticipated exactly this situation:

> *"Two corpora cannot establish a general claim. [...] Add corpus pairs if A1-c is
> chosen — with packet-only corpora, three or four pairs is cheap and materially
> strengthens the claim."*

Adopted. **X3 is replaced by X3′: cross-deployment transfer over multiple corpus
pairs** rather than one. Rationale:

| | X3 (fusion ablation) | X3′ (multi-pair transfer) |
|---|---|---|
| Data cost | 16.4 GB of pcap | tens of MB of published CSV per corpus |
| Strengthens | one secondary claim | **the paper's headline claim, RQ1** |
| Reviewer risk addressed | none | **R4, a listed major threat** |
| Generality | one deployment pair | three or four pairs |

A single A→B pair supports "transfer failed between these two". Three or four pairs
support "transfer failure is the normal case, and here is how much it varies", which is
a materially stronger and more defensible claim for the same effort.

### Cost this incurs: A3 returns

Without `D_A`'s pcaps we cannot run our own exporter on `D_A`, so the single-exporter
control (A3, plan priority "Must fix") is **not** satisfied. `Δ_F1` reverts to an
**upper bound** on deployment shift, conflated with exporter differences.

This is the one genuinely uncomfortable consequence and it must be stated in the paper,
not buried. Mitigations, in order of preference:

1. **M1 still runs** where a corpus publishes both raw captures and its own derived CSV.
   Recomputing one corpus's features with our exporter and comparing against its
   published CSV bounds the exporter term on data where deployment shift is zero by
   construction. This needs only that corpus's captures, not `D_A`'s 16 GB.
2. **M2 retained**: report `Δ_F1` on the full shared feature space and on a conservative
   sub-intersection restricted to features whose definitions are unambiguous across
   exporters (packet and byte counts, duration) and which are therefore least
   exporter-sensitive.
3. Wording discipline: every `Δ_F1` is described as spanning *an independently collected
   deployment **and** an independent feature-extraction pipeline*. That is the honest
   description, and it is arguably the more realistic deployment condition anyway — an
   operator inheriting a model also inherits somebody else's exporter.

### Small downloads are not affected

"No downloads" is read as "no multi-gigabyte packet captures". Published feature CSVs of
tens of megabytes remain in scope: without at least one target corpus there is no RQ1
and therefore no paper.

---

## D-011 — Target corpus for RQ1 is unresolved; Phase 2 proceeds on `D_A` regardless

- **Phase:** 1/2
- **Status:** `OPEN — blocks X2 only`
- **Raised:** 2026-09-20

### Problem

RQ1 (cross-deployment transfer) needs a second, independently collected corpus.
`D_B` = 5G-NIDD is published on IEEE DataPort behind a login, and no anonymous direct
CSV route was found. The obvious alternative, the University of Queensland NF-* NetFlow
family, sits behind a JavaScript portal whose file API did not resolve to a public
endpoint.

### Why the NF-* family is worth pursuing anyway

It would solve two problems at once, and it is what plan §21 risk **R4** recommends:

> *"Add corpus pairs if A1-c is chosen — with packet-only corpora, three or four pairs
> is cheap and materially strengthens the claim."*

NF-UNSW-NB15, NF-ToN-IoT, NF-BoT-IoT and NF-CSE-CIC-IDS2018 (v1, 12 features) were all
regenerated **with one tool, nProbe, onto one identical schema**. That means:

1. **Four corpora, twelve ordered pairs** instead of a single A→B claim.
2. **The A3 exporter control comes for free**, because the exporter is held constant
   across every pair by construction. Better still, it gives an *empirical bound* on the
   exporter confound: if `Δ_F1` is large with the exporter fixed, the exporter cannot be
   the explanation for a large `Δ_F1` in our O-RAN pair. That is a stronger answer to
   reviewer risk R1 than any agreement study.

### Options, in preference order

| # | Route | Cost | Note |
|---|---|---|---|
| 1 | Owner downloads 5G-NIDD from IEEE DataPort with institutional access | minutes | Smallest artefacts are `Encoded.zip` (29 MB) and the combined CSV. Keeps the 5G framing |
| 2 | Owner downloads the NF-* v1 CSVs from the UQ portal in a browser | minutes | Unlocks the multi-pair design and the exporter control |
| 3 | Find a provenance-clean mirror | uncertain | Third-party HuggingFace/Kaggle re-uploads exist but are **unverified**. Using one would reintroduce exactly the provenance problem this project exists to avoid |

### Decision for now

**Do not block on it.** X1 (in-distribution baselines), the leakage audit, X4 (alert
burden) and X5 (latency) all run on `D_A` alone and are the majority of the work. X2 is
the only experiment that waits.

`D_A` supports a full Phase 2 immediately: 1,723,817 network flows with an `src_ip`
group key (318 groups) and 45,244 radio records with a recovered `session` group key
(30 label-pure runs).

**Do not substitute an unverified mirror to unblock X2.** An unattributable corpus is
worse than a missing experiment: the missing experiment is a stated limitation, the
unattributable one is a reproducibility failure.

---

## D-012 — The n=5 bootstrap CIs were anti-conservative; raise n to 20 and re-run

- **Phase:** 15 (statistical audit)
- **Status:** `DECIDED 2026-09-20`
- **Raised by:** the Phase 15 audit contradicting the Phase 2 result

### What happened

EXP-002 reported that the leakage effect was significant for 4 of 6 non-trivial
models, on the basis that a **percentile bootstrap CI over 5 split means excluded
zero**. The statistical audit then ran the correct paired test on the same data:

| Model | Diff | Bootstrap CI (as reported) | **Paired t 95% CI** | p | p (Holm) |
|---|---:|---|---|---:|---:|
| tree | +0.134 | [+0.048, +0.226] | **[−0.007, +0.274]** | 0.057 | 0.401 |
| xgboost | +0.117 | [+0.029, +0.221] | **[−0.033, +0.266]** | 0.096 | 0.554 |
| hgb | +0.113 | [+0.027, +0.209] | **[−0.029, +0.256]** | 0.092 | 0.554 |
| rf | +0.099 | [+0.009, +0.204] | **[−0.054, +0.252]** | 0.148 | 0.590 |

**The earlier significance claim was wrong.** A percentile bootstrap resampling
5 points with replacement is well known to be anti-conservative: it can only ever
produce intervals spanning the observed values, so at n=5 it systematically
understates uncertainty. The paired t-interval is the correct instrument at this
sample size, and under it **no non-trivial model reaches significance**, corrected
or uncorrected.

The point estimates did not change. The effect is still large (d_z 0.66–1.18) and
uniformly positive. What changed is that **n=5 cannot establish it.** The audit's own
pre-stated power calculation said as much before the tests ran: the minimum effect
detectable at n=5 with 80% power is d_z ≈ 1.32, larger than anything observed.

### Decision

**Raise the split-seed count to 20 and re-run the leakage audit.** Pre-registered
before the re-run:

- **n = 20**, chosen from the power calculation, not from the data: 80% power at
  alpha = 0.05 requires n ≈ 20 to detect d_z = 0.63, which sits below the smallest
  non-trivial effect observed (mlp, d_z = 0.66).
- **Run exactly 20 and report whatever results.** Not "add seeds until it becomes
  significant" — that is the p-hacking this project exists to avoid. If the effect
  is still not significant at n=20, that is the reported outcome.
- **The primary interval becomes the paired t-interval.** Bootstrap intervals are
  retained only where n ≥ 30.
- **The Holm family stays as it is**, including the trivial baselines. Dropping
  them now would make the correction less conservative *after* seeing that the
  correction bites, which is the wrong direction to move.

### Why raising n is legitimate here and not p-hacking

The distinction is whether the stopping rule depends on the result. It does not:
n = 20 is fixed in advance from a power calculation that was written into the audit
script *before* the tests ran, the analysis is unchanged, and the outcome will be
reported either way. What would be illegitimate is re-running at n = 25, 30, 35
until a p-value crossed 0.05.

### Correction to the record

`reports/experiments/EXP-002_004_005.md` §1 and the EXP-002 commit message both
state "significant for 4 of 6 non-trivial models". **That is withdrawn.** The
corrected statement, pending the n=20 re-run, is:

> The leakage effect is large and uniformly positive in point estimate (+0.03 to
> +0.13 macro-F1, ordered by model capacity), but n = 5 split seeds is underpowered
> to establish it: no non-trivial model reaches significance under a paired t-test,
> before or after Holm correction.
