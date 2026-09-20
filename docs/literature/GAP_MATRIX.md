# Gap Matrix

**Produced by:** EXP-000 (Phase 0, repository and literature reconstruction)
**Date:** 2026-09-20
**Evidence base:** `docs/literature/LITERATURE_MATRIX.csv`, 25 entries
**Verification caveat:** 11 entries were verified from an abstract or landing page,
4 from search snippets only, and 9 from title and URL only. No full text was read
in this pass. Every gap below is therefore **provisional** and must be re-tested in
Phase 20 against full texts. A gap asserted from an abstract is a hypothesis about
the literature, not a finding about it.

---

## 1. How this matrix was built

The master protocol forbids inventing a research gap. A gap here is recorded only
when a retrieved source is explicitly silent on a criterion, or explicitly states
that the criterion is out of scope. Silence in an *abstract* is weaker evidence than
silence in a *paper*, and the `verification_status` column of the matrix carries
that distinction forward.

Three questions are asked of every study:

1. What did it measure?
2. What did it not measure, and did it say why?
3. Would our measuring it change what a practitioner would do?

Question 3 is the filter that separates a gap from a to-do list. A criterion nobody
measured is only interesting if measuring it can change a deployment decision.

---

## 2. Coverage table: who measured which deployment criterion

`Y` measured, `P` partial, `N` explicitly absent, `?` not established from the
retrieved text.

| ID | Study | In-dist. detection | Cross-deployment transfer | Alert burden at realistic base rate | Tail latency (p99) | CPU / RAM | Adversarial robustness | Real RIC |
|----|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| P03 | Cross-Layer IDS in 5G O-RAN (CSR'26) | Y | N | P | N | N | N | N |
| P04 | Real-Time AI in Near-RT RIC xApp (ICCCN'26) | Y | N | N | N (p95 only) | N | N | Y |
| P05 | AI-Based IDS xApp performance (2026) | Y | N | ? | ? | ? | ? | Y (claimed) |
| P06 | ARGOS (2025) | Y | N | P | ? | P (unquantified) | N | Y |
| P07 | ZTRAN (2024) | ? | N | N | N | ? | N | Y |
| P08 | 5G-SPECTOR (NDSS'24) | Y | N | ? | ? | ? | N | Y |
| P09 | 6G-XSec / MobiWatch (HotNets'24) | Y | N | ? | ? | ? | N | Y |
| P10 | Multi-Layer Defence (OJCOMS'25) | Y | N | ? | N (aggregate only) | P | P | Y |
| P11 | Black-Box Evasion on O-RAN apps (2025) | n/a | N | N | N | ? | Y | Y |
| P12 | LLM robust anomaly detection (2025) | Y | N | ? | N | ? | Y | ? |
| P14 | Cross-Domain Failure, IIoT (2026) | Y | **Y** | P | N | N | N | n/a |
| P24 | Cross-Layer Wireless Misbehavior (2025) | Y | N | N | N | N | N | N |

**Reading of the table.** Every column has at least one `Y`. **No row has a `Y` in
more than three of the seven columns, and no row has `Y` in the transfer, alert-burden
and tail-latency columns simultaneously.** That conjunction — not any single column —
is the only defensible gap this matrix supports.

---

## 3. Per-study interrogation

### P03 — Cross-Layer IDS in 5G O-RAN (Fard, Komarov, Wunder, IEEE CSR 2026)

This is the nearest prior work and the most consequential entry in the matrix,
because it uses the corpus we intend to adopt as `D_A`.

| Question | Answer |
|---|---|
| Measured | ROC-AUC and run-level detection for 7 architectures across radio-only, flow-only and fused feature sets; run-disjoint splits; 10 seeds |
| Not measured | cross-deployment transfer, latency, resource use, alert volume, base-rate sensitivity, calibration, adversarial robustness |
| Assumed | that in-distribution discrimination on one deployment is the quantity of interest |
| Environment | offline, on the UCD corpus |
| Leakage risk | low — run-disjoint splitting is the correct control and they applied it |
| Split | run-disjoint, 10 seeds |
| Baselines | single-modality variants of each architecture |
| Real-RIC validation | none |

**What this costs us.** The claim "radio KPIs raise in-distribution F1" (our C5, first
half) is now prior work and cannot be presented as our finding. Our H4 must be stated
strictly as the *sign-flip*: the families that most raise in-distribution F1 most
reduce cross-deployment F1. P03 supplies the first half; only the second half is ours.

**What this gives us.** It is independent confirmation that run-disjoint evaluation on
this corpus is achievable and is the community's expectation, and it gives us a
published in-distribution reference point against which our own in-distribution numbers
can be sanity-checked. It also warns us that windowed statistical aggregation on this
corpus produces 27–46% DoS-to-Benign confusion; if our pipeline does not reproduce
something in that neighbourhood, our windowing differs from theirs and we must say how.

---

### P04 and P05 — the two latency studies that disagree

These two must be read together, because their disagreement is the single most useful
thing the literature gave us in this pass.

| | P04 (ICCCN 2026) | P05 (2026) |
|---|---|---|
| Budget assumed | **10 ms** | **1000 ms** |
| Models | logistic regression, shallow MLP, exported to C | LSTM, CNN, Transformer, Autoencoder |
| Latency reported | 1–5 µs (LR), 10–25 µs (MLP) inference; < 4 ms end-to-end | ~600 ms (LSTM/CNN), ~850 ms (Autoencoder) |
| Percentiles | p95 ("> 95% of loop executions") | not established |
| Verdict reached | real-time AI in a Near-RT RIC xApp is feasible | strict latency constraints are satisfiable with structural optimisation |

Both verdicts are positive, and they are five orders of magnitude apart in measured
latency. The reason is that O-RAN specifies the near-real-time control loop as a
**range of 10 ms to 1 s**, and each study picked one end of it.

**Consequence for our paper, and it is a serious one.** Our draft asserts a single
budget `B = 10 ms` and derives a binary deployability predicate from it. Given P04 and
P05, a reviewer can point out that the verdict is determined by an authoring choice
rather than by a measurement. Reporting `q_0.99(L)` against a *swept* budget over
[10 ms, 1 s] converts that weakness into a result: it identifies the budget at which
each architecture crosses from deployable to not, which is the quantity an operator
actually needs.

This is recorded as improvement **I11** in `configs/decisions.md`.

**Second consequence.** P04 measures a C-exported linear model at 1–5 µs. If our
latency finding is about *inference*, P04 has already answered it and answered it
negatively for our story. Our draft already claims (C10) that feature construction
dominates the budget. That claim is now the load-bearing one and must be measured with
a per-stage breakdown, not inferred.

---

### P14 — Cross-Domain Generalization Failure in IIoT (2026)

| Question | Answer |
|---|---|
| Measured | cross-network transfer for four lightweight models over three IIoT corpora, on a shared feature space, under naturally imbalanced class distributions |
| Not measured | latency, resource use, RIC integration, radio modality |
| Finding of note | the evaluation protocol can **reverse** which target network appears harder |

**What this costs us.** "Cross-dataset IDS transfer collapses" is not a novel finding
in 2026, inside or outside O-RAN. Our RQ1 cannot be framed as discovering it.

**What this obliges us to do.** Their protocol-reversal finding is a direct threat to
our own headline: if the apparent ranking of architectures under transfer depends on
the evaluation protocol, then our `Δ_F1` ordering across five architectures may not be
stable. We must test this rather than assume it away — evaluate under at least two
prevalence conventions and report whether the ordering survives. Recorded as **I12**.

---

### P06, P08, P09, P10 — the O-RAN security xApp line

All four build real xApps on real or emulated RICs, and all four evaluate in the
deployment where the detector was trained. None reports transfer. Overhead, where
reported, is either qualitative (P06: "minimal") or a single aggregate (P10: "< 80 ms
at 500 UEs") rather than a distribution.

**Reading.** This community has strong systems practice and weak generalisation
practice. That asymmetry, rather than any individual omission, is the gap our paper
addresses.

---

### P11, P12, P16, P17 — the adversarial line

P11 demonstrates that black-box evasion succeeds against O-RAN ML apps *and* against
prominent adversarial-ML defences, under the RIC's timing constraints. P12 shows the
detector's input path (the Shared Data Layer) is itself manipulable.

**Reading.** Clean-test accuracy does not establish deployability, and this is now
demonstrated rather than argued. Our Phase 8 is therefore justified by literature, not
by completeness instinct. But note: the victims in P11 are a classification xApp and a
power-saving rApp, **not an IDS**. Whether evasion against an IDS interacts with alert
burden (an evader could also be forced to raise the false-positive rate) is untouched.

---

## 4. Candidate gaps, with the evidence for each

Each gap is graded by how much of it survives the verification caveat in the header.

| # | Candidate gap | Evidence | Strength | Verdict |
|---|---|---|---|---|
| G1 | No study reports cross-deployment transfer, operational alert burden and tail latency **for the same artefact** | coverage table §2: no row has all three | **Strong** — this follows from the table's structure, not from any single abstract | **ADOPT as the primary gap** |
| G2 | No study evaluates cross-deployment transfer for an O-RAN IDS at all | P03, P04, P05, P06, P08, P09, P10 all single-deployment; P14 does it but outside O-RAN | Moderate | Adopt, narrowly worded: "for an O-RAN IDS", never "for an IDS" |
| G3 | The near-RT budget is treated as a constant, and the choice determines the verdict | P04 uses 10 ms, P05 uses 1000 ms, spec range is 10 ms–1 s | **Strong** — two sources, directly contradictory in framing | **ADOPT as a secondary contribution** (budget sweep, not budget assertion) |
| G4 | Tail latency (p99) is not reported by any retrieved O-RAN IDS study | P04 reports p95; P10 reports an aggregate; others unestablished | Moderate — 9 entries are title-only, so absence is unproven | Adopt with hedged wording, and re-test in Phase 20 |
| G5 | Alert volume at a realistic attack base rate is not reported for any O-RAN IDS | P06 gives 0.6% FPR with no flow rate; P03 gives a 1% FPR operating point with no volume | Moderate | Adopt; note that Axelsson (P13) means the *reasoning* is 26 years old — only the O-RAN quantification is ours |
| G6 | The radio-modality accuracy/transfer trade-off is unmeasured | P03 establishes the in-distribution half; no source tests the transfer half | Moderate, and **contingent on `D_A` having radio features** | Adopt only if gate A1 resolves with radio KPIs |
| G7 | No adversarial evaluation of an O-RAN **IDS** specifically | P11 attacks non-IDS apps; P16/P17 target DRL/steering xApps | Weak — 3 of 4 adversarial entries are title-only | **Do not claim.** Treat Phase 8 as necessary diligence, not as novelty |
| G8 | Energy per decision is unattributed in container deployments | no retrieved source measures it; our own A8 says RAPL cannot attribute it | Weak, and we cannot fix it either | **Do not claim.** Consistent with improvement I9: drop the energy column |

---

## 5. The novelty statement this matrix supports

Narrow, and deliberately so:

> For a detection xApp on an O-RAN near-RT RIC, we report cross-deployment
> generalisation, operational alert burden at swept attack base rates, and decision
> latency at the tail against a **swept** near-real-time budget, for the same set of
> model artefacts under one feature extractor and one evaluation protocol. We are not
> aware of published work that reports these jointly; each has been reported
> separately.

What this statement does **not** claim, and must never be edited to claim:

- not the first O-RAN IDS (P06, P08, P09 precede us)
- not the first cross-dataset IDS transfer study (P14 and a large NIDS literature precede us)
- not the discovery of the base-rate problem (P13, 2000)
- not the first latency measurement of an xApp (P04, P05)
- not the first adversarial analysis of O-RAN ML (P11)
- not "comprehensive", "state of the art", "unprecedented" or "first ever"

---

## 6. What this matrix changes in the existing plan

| Existing item | Change | Reason |
|---|---|---|
| Gate A1 (`D_A` unidentified) | **Unblocked, provisionally** — NetsLab-5GORAN-IDD (P01) is a real, citable, CC-BY corpus with paired CU flow records and DU radio telemetry | P01 retrieved |
| Claim C5 (radio KPIs help in-distribution) | **Rescope** — first half is P03's result; only the transfer sign-flip is ours | P03 |
| Claim C9 (only XGBoost meets the p99 budget) | **Rescope** — report a budget sweep, not a single-budget verdict | P03/P04/P05 disagreement |
| Claim C10 (feature extraction dominates latency) | **Promote to load-bearing** and measure per stage | P04 shows inference is microseconds |
| Threat model (paper Sec. III) | **Widen or explicitly bound** — message-level and control-logic threats exist | P10, P11, P12 |
| Phase 13 external corpus | **Candidate identified**: O-RAN E2SM-KPM DoS dataset (P23), MIT, 69.8 MB, different site and team | P23 |
| Baseline ladder | **Add** a non-learned cross-layer consistency baseline | P24 |

---

## 7. Open literature questions for the next pass

1. P05 could not be retrieved (HTTP 403). It is one of only two latency comparators. **Must** be obtained before any latency claim is written.
2. Full texts of P03 and P04 are required before the novelty statement in §5 is fixed.
3. Nine entries are title-only. Their `N` cells are currently `?`, and the strength grades of G4, G5 and G7 depend on resolving them.
4. The NetsLab descriptor PDF has not been read; record counts, label columns, run/device identifiers and CU–DU time synchronisation are unknown and are all prerequisites for split design (A4) and windowing (A12).
5. No systematic screening protocol has been executed for Track D / claim C13. Until it is, Table VIII of the manuscript remains unevidenced (see A9).
