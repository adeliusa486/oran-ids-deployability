# EXP-037 — Manuscript audit: what must change, and why

**Date:** 2026-09-20
**Phase:** 37, step 1 (audit). The rewrite follows once EXP-026 lands.
**Scope:** `paper/main.tex`, 51 `\syn{}` sites plus everything around them.

This is the list of statements in the manuscript that are **not merely
unevidenced but actively contradicted** by what the repository now measures. The
`\syn{}` markers find fabricated *numbers*; they do not find fabricated *methods*,
and the methods are the worse problem.

---

## 1. The Methodology section describes a pipeline that does not exist

`\subsection{Feature Harmonisation}` is wrong in three independent ways, and none
of them is marked synthetic.

### 1.1 The shared feature space is not 24 features

> "Twenty-four of these are packet-level and are computable on both corpora. All
> cross-deployment results therefore use the 24-feature shared space."

`tab:features` breaks the 24 into Volumetric 8, Timing 7, Header 9.

**Measured reality.** `D_A` is Zeek and `D_B` is Argus, and they share **zero
column names**. The space that can actually be built by meaning is **15 shared
concepts / 18 matrix columns** (`configs/features/shared_space.yaml`):

| | Claimed | Actual |
|---|---:|---:|
| Volumetric | 8 | 7 base numeric (duration, src/dst bytes, src/dst pkts, totals) |
| Timing | 7 | **0** — `D_B` publishes no inter-arrival statistics |
| Header | 9 | **1** concept (protocol), 4 one-hot columns |
| Derived | — | 7 |
| **Total** | **24** | **15 concepts / 18 columns** |

The Timing family is the sharpest case: `tab:features` gives it seven members and
a shift of 0.51, and **`D_B` contains no inter-arrival statistics at all.** That
row describes measurements that do not exist.

**Action:** the count, the table and the per-family shift column are all replaced
from the committed mapping. The 24 was never derived from either schema.

### 1.2 The normalisation described violates the study's own A2 rule

> "quantile-normalised per corpus to remove trivially deployment-specific scaling"

Per-corpus normalisation fits a transform **on the target corpus**. A2 forbids
exactly this, and `README.md` lists it as a non-negotiable. The implemented
pipeline fits a `StandardScaler` inside the model pipeline on **source training
data only**, plus a parameter-free `log1p` applied identically to both sides
(D-016), which cannot carry target information because nothing is fitted.

**This is the most serious error in the manuscript.** As written, the Methodology
section describes a leak, and a reviewer who reads only the paper would be right
to reject it.

**Action:** rewritten to describe the source-fitted transform actually used.

### 1.3 The windowing described belongs to a different layer

> "computed over a sliding window of 16 flow records per device"

16-record windows are the **radio** layer's aggregation (`load_radio`). The
network flow pipeline does not window, and the transfer experiment operates on
individual flow records.

**Action:** windowing moved to where it applies and removed from the transfer
description.

---

## 2. The results tables report models we never ran

`tab:cross` lists **1D-CNN** and **LSTM**. Neither is in `models/zoo.py`. The
ladder is: majority, stratified, logreg, tree, rf, xgboost, hgb, mlp.

The same table reports "95% confidence intervals over five seeds". The standing
design is **20 split seeds**, raised from 5 by D-012 on a power calculation made
before the tests, precisely because n=5 intervals were anti-conservative and
produced a wrong significance claim.

**Action:** the table is regenerated from `results/EXP-026/`, with the real
ladder and n=20. Deep sequence models are removed from the paper rather than
invented; if a reviewer asks for them, the answer is that they were not run.

---

## 3. Claims that must change, one by one

| Claim | Manuscript says | Evidence says | Action |
|---|---|---|---|
| **C1** | ">98% in-distribution" | true only under a *random* split, which is the artefact we measure | rescope to the protocol finding |
| **C2** | "every architecture loses 27.9–37.1 F1 points" | numbers synthetic; real values from EXP-026 | **replace**; keep the claim only if the CI supports it |
| **C5** | radio KPIs help in-dist, hurt transfer | pre-registered failure criterion fired | **WITHDRAWN** (D-010), already done |
| **C8** | default threshold unusable | **SUPPORTED and strengthened**: corpus precision ~0.93 vs pooled PPV 0.0055–0.0077, a 132x gap | keep; **delete the "6x spread" clause** (D-018) |
| **C9** | "only XGBoost meets p99" | **CONTRADICTED** by our own measurement, and again by Obiuwevwi et al. | keep as a reported contradiction |
| **C10** | feature extraction dominates | **SUPPORTED and sharpened** by EXP-030: survives a 12x speedup; 3–19x against real-RIC inference | keep, with the new numbers |
| **C13** | existing work under-reports | no evidence was ever collected | **WITHDRAWN**, Table VIII deleted |
| **C15** | energy differs 13x | RAPL cannot attribute to a container | **WITHDRAWN** |

---

## 4. Novelty claims that are no longer available

From `reports/literature_audit_v2.md`:

- **Any "first cross-deployment evaluation" framing is dead.** Abraheem &
  Edhirig (7 August 2026) run bidirectional transfer between **the same two
  corpora**. The paper must cite them as prior art and position itself as
  replication-plus-extension: eight architectures against their one, trivial
  floors on the target, and a group-disjoint source reference.
- **Any near-RT conformance framing is dead.** Obiuwevwi et al. (July 2026)
  measured AI inference inside a real OAI+FlexRIC RIC. Our latency work is
  **emulated** and Track C is **BLOCKED** (EXP-031).

The title — *"Why Accuracy Alone Is Not Enough"* — survives both, because it
promises a critique of evaluation practice rather than a first result. It should
stay.

---

## 5. What the paper gains

Three things that are stronger than what they replace:

1. **A worked estimator error with its magnitude.** Averaging PPV across folds
   instead of pooling counts inflated our own reported spread from 1.40x to
   13.18x. Reporting it as a correction, in a paper about evaluation practice, is
   more persuasive than any result we could have kept.
2. **Implementation, not architecture, sets the latency verdict.** Three orders
   of magnitude between our Python prototype and a deployed embedded model, for
   the same model families. Any architecture recommendation made on prototype
   latency describes its own toolchain.
3. **FPR is not a stable property of these detectors.** 0.000 to 0.890 across
   group-disjoint folds, and fold composition explains almost none of it
   (max R^2 0.36). Every single-number FPR in the NIDS literature, ours included,
   should carry that range.

---

## 6. Structural consequences

| Section | Action |
|---|---|
| Abstract | rewritten last, from the final numbers |
| Related Work | Abraheem & Edhirig and Obiuwevwi et al. added prominently, not in a list |
| Feature Harmonisation | rewritten: 15 concepts / 18 columns, source-fitted normalisation, no windowing |
| `tab:features` | regenerated from `configs/features/shared_space.yaml` |
| Cross-Deployment | regenerated from `results/EXP-026/`; CNN and LSTM removed |
| Calibration | not yet run (Phase 28); section is currently unevidenced |
| Alert Burden | "6x" deleted; collapse factor and the prevalence sweep added |
| Latency | EMULATED throughout; conformance claim removed; §5.2 added |
| Limitations | exporter confound, with Abraheem & Edhirig's 0.993 fingerprint result |
| Reproducibility | 50 tests from a bare `pytest`; the conftest fix |

## 7. The rule that stays

No number reaches the manuscript except by `\input` from `tables/generated/`, and
no `\syn{}` value is ever quoted. A `\syn{}` count of 0 is a necessary condition
for removing the draft banner, not a sufficient one — this audit exists because
the fabricated *methods* carried no marker at all.
