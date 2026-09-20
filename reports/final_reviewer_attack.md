# Phase 22 — Reviewer Attack

**Date:** 2026-09-20
**Against:** the repository's actual state, not the draft's aspirations
**Method:** three reviewer personas, each given the real results and the real gaps.
Every criticism gets a problem, the evidence, and an action — never a prose rebuttal
where an experiment is owed.

A note on what this document is for. The draft it attacks is not the manuscript in
`paper/main.tex`, which still contains only synthetic numbers. It attacks the *paper
that could be written from today's results*. That is the more useful target: it tells
us what to run next, and what not to write.

---

## Reviewer A — Machine learning / security

### A1. "Your headline experiment is missing." — **FATAL as things stand**

**Problem.** The paper is titled around cross-deployment deployability, and RQ1 is
cross-deployment generalisation. There is no cross-deployment result. `D_B` was never
obtained (D-011).

**Evidence.** `configs/experiment_registry.yaml`: X2 is the only core experiment with
no result. `docs/CLAIM_EVIDENCE_MATRIX.csv`: C2, C3, C4 all `not_established`.

**Action.** Not arguable. Either obtain a target corpus or **retitle the paper**. A
defensible fallback exists and is arguably a cleaner contribution: *"Evaluation-protocol
effects and operational cost in O-RAN intrusion detection"*, built on the leakage
result, the alert-burden result and the swept-budget latency result, with transfer
named as future work. Decide before writing, not after.

### A2. "Your leakage result is not significant." — **Valid, already self-reported**

**Problem.** Point estimates of +0.08 to +0.13 macro-F1, but at n=5 no non-trivial
model clears α=0.05 under a paired t-test, corrected or not.

**Evidence.** `reports/statistical_audit.md`; D-012.

**Action.** Taken: n raised to 20 on a pre-registered power calculation, and the
anti-conservative bootstrap replaced by a t-interval with a warning guard in the code
so it cannot recur. If n=20 is still null, that is what gets reported.

### A3. "76% attack prevalence is not intrusion detection." — **Valid and important**

**Problem.** The radio layer is 76.5% attack at window level; the network layer 94.6%
after dedup. No real deployment looks remotely like this. Training and evaluating in
that regime learns a task nobody has.

**Evidence.** `results/EXP-002/statistics/provenance.json`.

**Action.** Partly handled — the majority-class floor is reported beside every score,
macro-F1 is primary rather than accuracy, and the alert-burden analysis sweeps π down
to 10⁻⁴ precisely because the corpus prevalence is a capture artefact. What is **not**
yet done and should be: re-run detection under resampled prevalence to check the
ranking is stable. Recorded as the top follow-up.

### A4. "Your group key is an IP address." — **Valid, partially mitigated**

**Problem.** Grouping the network layer by `src_ip` means group-disjoint really means
host-disjoint. Hosts in a testbed map almost one-to-one onto attack roles, so a
host-disjoint split may be closer to attack-disjoint than to deployment-disjoint —
which would make the split *harder* than deployment, not easier.

**Action.** Report the confound explicitly and give the per-group class composition so
a reader can judge. The radio layer does not have this problem: its `session` key is a
capture run and all 30 are label-pure.

### A5. "Where is the adversarial evaluation?" — **Answerable**

Cut deliberately (D-009) and the reasoning is on record: gap G7 was graded *weak*, so
it was never a novelty claim. Listed in Limitations and future work. This is a scope
decision, not an oversight.

---

## Reviewer B — O-RAN / networking systems

### B1. "This was never deployed on a RIC." — **FATAL for Criterion 3 as written**

**Problem.** The latency numbers come from single-process Python timing on a Windows
laptop with no CPU isolation. The paper claims a near-real-time conformance verdict.

**Evidence.** `results/EXP-005/statistics/env_radio.json`, tagged
`measurement_class: emulated` with the limitation written into the artefact.

**Action.** The tagging is necessary but **not sufficient**. Either execute D-005
(Level 2: real Near-RT RIC under synthetic E2 load on a Linux host) or **remove the
conformance claim entirely** and present the swept-budget analysis as what it is — a
relative ordering plus a methodological argument about how budgets are chosen. The
second option is honest and still publishable; the first is better.

### B2. "Your p99 measures Python, not the model." — **Partly answered**

The floor experiment was run first and gives a platform p99 of 0.103 ms, two orders
below the tightest budget, so the *ordering* is not a platform artefact. But
interpreter overhead is inside every number: logistic regression at 6.51 ms p99 is
plainly framework cost, given prior work measures a C-exported logistic regression at
1–5 µs inside a real xApp. **The absolute values must not be compared against a budget
without a native implementation.**

### B3. "Feature extraction at 6.9 ms/flow is your exporter being slow." — **Valid**

**Problem.** The C10 evidence comes from a pure-Python exporter running at 1.1–4.3
MB/s. A production C or eBPF exporter is perhaps 10× faster, which would change the
ratio substantially.

**Evidence and action.** Already recorded in the artefact's own
`caveat_that_must_appear_in_the_paper`. The claim must be the bounded one: extraction
is the same order as or larger than inference **for every architecture that meets a
10 ms budget**, so optimising the model alone addresses the smaller half. Anything
stronger needs a native exporter.

### B4. "One cell, two UEs, one testbed." — **Valid and inherent**

`cellid` has a single value; `ue_id` has nine. Belongs in Limitations, stated plainly
rather than buried.

---

## Reviewer C — IEEE Transactions methodological reviewer

### C1. "What is the contribution, in one sentence?" — **The hardest question**

With X2 missing, the honest answer is: *a measurement of how much evaluation-protocol
choices and deployment-parameter choices change the apparent deployability of an O-RAN
IDS.* That is a real contribution — the leakage-scales-with-capacity result and the
budget-flip result are both novel and both actionable — but it is **not** the
contribution the title promises.

**Action.** Align title, abstract and contribution list with what was measured. Do not
let the abstract keep promising transfer results that the results section does not
contain.

### C2. "Three of your findings restate known results." — **Valid, already handled**

Radio-beats-flow in-distribution (P03, on this same corpus), cross-domain collapse
(P14), base-rate precision collapse (Axelsson, 2000). `GAP_MATRIX.md` §5 already
states the novelty narrowly and the "Do Not Repeat" list in `MEMORY.md` forbids
re-claiming them. Keep it that way under revision pressure.

### C3. "Your negative and contradicted results — did you report them?" — **Yes**

- C9 contradicted by our own measurement: four of six architectures conform at 10 ms,
  not one, and the fastest is a decision tree.
- C5 withdrawn per a pre-registered criterion rather than rescued.
- The n=5 significance claim withdrawn and the cause documented.
- Table VIII deleted for lack of evidence.

This is the strongest part of the submission and should be visible in the paper, not
only in the repository.

### C4. "Can I reproduce it?" — **Mostly**

Every figure and table is generated by a committed script with a provenance header.
Data provenance is SHA-256 recorded. Splits are seeded. **Gaps:** no environment lock
file, no `make` target exercised end to end, and the raw corpora need manual download.

### C5. "Two model seeds, not three." — **Minor**

Deviation recorded in the audit. Model seeds are nested inside split seeds and
averaged before testing, so they affect precision of the within-split mean, not the
number of independent observations.

---

## Consolidated actions, in priority order

| # | Action | Blocks | Status |
|---|---|---|---|
| 1 | Obtain a target corpus, or retitle the paper away from transfer | the headline | **open (D-011)** |
| 2 | Run Track C at Level 2, or delete the conformance claim | Criterion 3 | open (D-005) |
| 3 | Finish the n=20 leakage re-run and report whatever it gives | the protocol result | running |
| 4 | Re-run detection under resampled prevalence | Reviewer A3 | open |
| 5 | Report the `src_ip` grouping confound explicitly | Reviewer A4 | open |
| 6 | Align title, abstract and contributions with measured results | framing | open |
| 7 | Environment lock file and an end-to-end `make` run | reproducibility | open |
| 8 | Native-exporter measurement before strengthening C10 | Reviewer B3 | future work |

---

## The one-line verdict

**Today this is a sound methods-and-measurement paper wearing the title of a transfer
paper.** Two of the three deployment criteria are measured and carry findings that are
genuinely new; the third is emulated and the transfer criterion is absent. The
strongest available move is not to write the transfer claims more carefully — it is to
either get the target corpus or change what the paper claims to be.
