# EXP-036 — Fresh literature and novelty audit

**Date:** 2026-09-20
**Phase:** 36
**Supersedes:** `reports/literature_audit.md` (Phase 0), which is kept unedited
**Verdict:** **two of the paper's remaining novelty claims are pre-empted by work
published in July and August 2026.** Both are recorded here and both claims are
rewritten rather than defended.

---

## 1. Why this pass was run now, not at the end

The Phase 0 literature matrix was built before any experiment existed. It has
already been wrong once in a way that mattered: gap G4 ("no O-RAN IDS study
reports p99") was withdrawn as false when P05 turned out to report ~140 ms.

The brief requires a fresh search before the manuscript is reconstructed,
specifically because a claim written against a stale matrix is a claim a reviewer
finds in ten minutes. That is what happened here, twice.

## 2. Provenance discipline

The Phase 0 matrix carries a per-entry verification tag and that convention is
kept. In this pass:

| Tag | Meaning | Count |
|---|---|---|
| `FULL_PAGE` | landing page or abstract page retrieved and read | 2 |
| `SNIPPET` | title plus search-result summary only — **not** a read | 9 |

Nothing tagged `SNIPPET` may support a claim of absence. That rule is what G4
violated last time.

---

## 3. Finding 1 — RQ1 is directly pre-empted

**Abraheem, A. and Edhirig, A. (2026).** "Bidirectional Cross-Dataset
Generalization and Label-Efficient Adaptation for 5G Network Intrusion
Detection." *Wadi Alshatti University Journal of Pure and Applied Sciences*,
4(2). Published **7 August 2026**. `FULL_PAGE`

This study uses **the same two corpora, in the same two directions, for the same
purpose as our EXP-026.**

| | Abraheem & Edhirig 2026 | This work (EXP-026) |
|---|---|---|
| Source / target | 5G-NIDD ↔ NetsLab-5GORAN-IDD | NetsLab-5GORAN-IDD ↔ 5G-NIDD |
| Direction | bidirectional | bidirectional (primary + symmetry check) |
| Feature space | "conservative semantic matching", **15 harmonised numerical features** | semantic mapping, **15 shared concepts / 18 columns** |
| Transfer | five-seed zero-shot | 20-seed zero-shot |
| Models | XGBoost | 8-architecture ladder incl. two trivial floors |
| Source split | not stated | group-disjoint on `src_ip` |
| Adaptation | CORAL + few-shot (1/5/10% target labels) | none — zero-shot only |
| Extra | dataset-fingerprint audit | operational, calibration and latency criteria |

Their headline zero-shot balanced accuracies:

| Attack family | 5G-NIDD → NetsLab | NetsLab → 5G-NIDD |
|---|---:|---:|
| Application-layer DoS | 0.518 | 0.505 |
| Network/transport flooding | 0.807 | 0.500 |
| Scanning | 0.834 | 0.558 |

Several of those are at or barely above the 0.5 chance floor.

### What this costs us

**Any claim of the form "the first cross-deployment evaluation between these
corpora" is dead.** It was published six weeks before this campaign ran. The
claim must be removed, not softened.

### What it does not cost us

Their design differs from ours in ways that are not cosmetic:

1. **One architecture versus eight.** They transfer XGBoost. Our result is about
   what happens to a ladder *including the trivial floors*, which is what makes a
   collapse readable — a macro-F1 of 0.55 means nothing until the reader knows
   that guessing scores 0.42 on that corpus.
2. **No source-side split protocol is stated.** Our source reference is
   group-disjoint, which is the whole subject of our Finding 1. A transfer gap
   measured against an inflated random-split source reference is larger than the
   real one, and we can quantify that because we measured both.
3. **They stop at detection metrics.** The operational half of our paper — alert
   burden, base-rate sensitivity, calibration, latency — is not in their scope.

### What it gives us for free, and we should say so

Their **dataset-fingerprint audit is the strongest independent support our own
limitation has.** A classifier trained to predict *which corpus a flow came from*
reaches **0.993 balanced accuracy on the 15 shared features**, and stays at 0.993
after CORAL alignment and after Top-6 source-predictiveness filtering.

That is an external, quantitative confirmation of exactly what D-004, D-010 and
D-015 force us to write: the two corpora are trivially separable in the shared
space, so a transfer gap between them spans deployment **and** exporter, and
cannot be attributed to deployment shift. We have been stating that as a caution.
They measured it. It should be cited at the point where we state the caveat.

### Action

- Novelty claim on RQ1: **rewritten**, see §7.
- Their fingerprint result: **cited in support of our own stated confound**.
- Their result: **cited as prior art**, and our numbers reported beside theirs.
- One note of caution for the comparison: they report "15 harmonised numerical
  features" without publishing the mapping. If their harmonisation mapped Zeek's
  payload-byte columns onto Argus's header-inclusive columns, it would carry the
  D-015 trap. We cannot tell from the abstract page, so we say nothing about it
  in the paper beyond publishing our own mapping in full.

---

## 4. Finding 2 — the real-RIC latency track is pre-empted

**Obiuwevwi, L., Rechowicz, K. J., Jayarathna, S., Bouk, S. H., Afrin, F.,
Barati, C. N., Moghim, N., Nanou, V., Rahman, M. E. and Shetty, S. (2026).**
"Enabling Real-Time AI in O-RAN: Deploying and Measuring AI Inside a Near-RT RIC
xApp." arXiv:2607.01583, submitted 2 July 2026. `FULL_PAGE`

An AI xApp on a real **OpenAirInterface + FlexRIC** testbed on commodity
hardware. Measured:

| Quantity | Reported |
|---|---|
| Logistic regression inference | **1–5 µs** |
| Shallow MLP inference | **10–25 µs** |
| End-to-end service latency | **< 4 ms** |
| 10 ms Near-RT budget | met for **> 95%** of projected loop executions |
| Model accuracy | 0.88–0.90 across six models |

Their own scope statement is careful: the results "validate embedding and
execution feasibility rather than production-level generalization", and the data
is synthetic emulation.

### What this costs us

Our latency campaign is **emulated** — Windows host, no CPU isolation,
single-process Python — and D-005's Track C Level 2 was never executed. A real
FlexRIC measurement now exists and ours does not. Any framing of our latency
work as establishing near-RT conformance is gone.

### What it does to our numbers

This is the uncomfortable part and it belongs in the paper. Their inference
latencies are **three orders of magnitude** below ours:

| Model | Ours (emulated, Python/sklearn) | Theirs (embedded, real RIC) |
|---|---:|---:|
| logistic regression | p50 2.45 ms | 1–5 **µs** |
| MLP | p50 2.25 ms | 10–25 **µs** |

A 1000x gap is not a hardware difference. It is an **implementation** difference:
a compiled, embedded model against a Python object graph. Which means our
Finding 4 — that the conformance verdict depends on where you draw the budget —
survives but with its conclusion sharpened and partly inverted:

> The budget crossing point is not a property of the architecture. It is a
> property of the implementation. Our own measurement puts four of six
> architectures inside a 10 ms budget and two outside; theirs puts the same two
> model families three orders of magnitude inside it. Architecture ranking
> derived from a Python prototype does not transfer to a deployed xApp, and a
> paper that recommends an architecture on the strength of prototype latency is
> recommending its own build system.

That is a more useful finding than the one we had, and it is a **negative result
about our own method**, which is the kind this project has agreed to keep.

### Action

- Track C: reported **BLOCKED**, not attempted, with this paper cited as what a
  real measurement looks like.
- All latency language constrained to "emulated"; no conformance claim.
- Finding 4 rewritten around implementation rather than architecture.
- C9 remains **CONTRADICTED** and is now contradicted twice.

---

## 5. Other work retrieved this pass

`SNIPPET` unless marked. None of these supports an absence claim.

| Ref | Work | Relevance |
|---|---|---|
| N01 | *Experimental Study of Adversarial Attacks on ML-based xApps in O-RAN*, arXiv:2309.03844 | Phase 33 baseline: small perturbations materially degrade near-RT RIC ML |
| N02 | *System-level Analysis of Adversarial Attacks and Defenses on Intelligence in O-RAN*, ACM WiSec 2024 | System-level adversarial framing |
| N03 | *KPI Poisoning: An Attack in Open RAN Near Real-Time Control Loop*, arXiv:2505.05537 | Poisoning via the E2 KPI path — the exact input our radio-layer detector consumes |
| N04 | *Black-Box Evasion Attacks on Data-Driven Open RAN Apps*, arXiv:2510.18160 | Evasion under near-RT timing constraints; UAPs and model cloning |
| N05 | *Adversarial ML Threat Analysis and Remediation in O-RAN*, arXiv:2201.06093 | Threat taxonomy |
| N06 | *Enhancing O-RAN Security: Evasion Attacks and Robust Defenses for Graph RL Connection Management*, arXiv:2405.03891 | Defence side; distillation reported to beat adversarial training under near-RT latency |
| N07 | *CALIBURN: Operationally Calibrated Streaming Intrusion Detection with Regime-Dependent Conformal Risk Control*, arXiv:2605.24696 | **Directly relevant to Phase 28.** Operational calibration with conformal risk control, 2026 |
| N08 | *On the Cross-Dataset Generalization of ML for Network Intrusion Detection*, arXiv:2402.10974 | General cross-dataset collapse, non-5G |
| N09 | *Cross-Domain Generalization Failure in Lightweight IDS for IIoT*, arXiv:2607.00553 | Same phenomenon, IIoT |
| N10 | *Assessing Generalisation Capability of ML Models for Intrusion Detection*, arXiv:2605.04407 | Methodology for generalisation assessment |
| N11 | *Base-Rate Fallacy Redux and a Deep Dive Review in Cybersecurity*, arXiv:2203.08801 | Confirms Axelsson (2000) remains the reference framing |

**Phase 33 consequence.** The adversarial literature (N01–N06) is substantial and
predates us. Our adversarial phase can contribute a *deployability* reading —
what an attack does to alert burden and to the operating threshold — but it
cannot claim to be the first adversarial evaluation of an O-RAN ML component.

**Phase 28 consequence.** N07 already does operationally-calibrated streaming IDS
with conformal risk control. Our calibration phase must be positioned as an audit
of whether calibration rescues PPV for *these* detectors, not as a new method.

---

## 6. Gaps from Phase 0 — status after this pass

| Gap | Phase 0 status | Now |
|---|---|---|
| G1 — no cross-deployment O-RAN IDS evaluation | open | **CLOSED by Abraheem & Edhirig 2026** |
| G3 — quantified | open, quantified | unchanged |
| G4 — "no O-RAN IDS reports p99" | already withdrawn (false) | stays withdrawn |
| G5 — no real-RIC AI latency measurement | open | **CLOSED by Obiuwevwi et al. 2026** |
| G7 — absence-based | provisional | **remains provisional**; `SNIPPET` evidence cannot close it |

Two of the five gaps this paper was built on are now closed by other people.
That is the single most important output of this pass.

---

## 7. What novelty actually survives

Stated as narrowly as the evidence allows. Each line is something we can point at
a result for.

1. **An estimator error in operational IDS metrics, with its magnitude.**
   Averaging PPV across evaluation folds rather than pooling confusion counts
   inflated our own reported spread between detectors from 1.40x to 13.18x
   (D-018 / B-E). We have not found this documented elsewhere, but note that this
   is an *absence* observation and by our own rule it is stated as "we are not
   aware of", never as "no prior work".

2. **A published feature-mapping trap between Zeek and Argus corpora.** Zeek
   `src_bytes` is payload (median 0); Argus `SrcBytes` is header-inclusive
   (median 84). The natural name-based mapping manufactures a large artefactual
   transfer gap. We publish the full mapping table; the pre-empting study
   publishes a feature count but not a mapping.

3. **Transfer measured against a group-disjoint source reference**, so the gap is
   not inflated by the split-protocol artefact that our Finding 1 quantifies.

4. **Transfer across an eight-architecture ladder with trivial floors on the
   target**, which converts "macro-F1 0.55" into a statement about whether
   anything transferred at all.

5. **The combination**: the same detectors evaluated on protocol sensitivity,
   transfer, alert burden under a swept base rate, calibration and latency, with
   a decision register recording every claim withdrawn along the way.

Point 5 is the honest centre of the paper. Points 1 and 2 are methodological
contributions that arrived by accident, from catching our own errors, and they
are the most defensible things here precisely because they are small and exactly
demonstrated.

## 8. What this pass forces to change in the manuscript

| Item | Action |
|---|---|
| Title | must not promise first/novel cross-deployment evaluation |
| RQ1 novelty claim | **removed**; reframed as replication-plus-extension |
| C2/C3/C4 | rewritten against Abraheem & Edhirig as prior art |
| C9 | remains CONTRADICTED, now by an external real-RIC measurement too |
| Latency section | "emulated" throughout; Track C reported BLOCKED |
| Finding 4 | rewritten: implementation, not architecture, sets the crossing point |
| Related work | must add Abraheem & Edhirig 2026 and Obiuwevwi et al. 2026 prominently, not in a list |
| Adversarial section | positioned against N01–N06, no primacy claim |
| Calibration section | positioned against N07 |

## 9. Honest note on the search itself

This pass ran nine queries and read two pages in full. It is a targeted keyword
search, not a systematic review, and it has selection bias by construction — the
same limitation recorded against the Phase 0 pass, and the reason Track D's
survey was deleted rather than written up.

Two direct pre-emptions surfaced in nine queries. That rate is itself evidence
that the surviving absence-based claims in §7 should be read with suspicion, and
they are worded accordingly.

---

## Sources read in full

- [Bidirectional Cross-Dataset Generalization and Label-Efficient Adaptation for 5G Network Intrusion Detection](https://waujpas.com/index.php/journal/article/view/509)
- [Enabling Real-Time AI in O-RAN: Deploying and Measuring AI Inside a Near-RT RIC xApp](https://arxiv.org/abs/2607.01583)
