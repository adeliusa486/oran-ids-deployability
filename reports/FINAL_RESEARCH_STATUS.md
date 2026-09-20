# Final research status — campaign 2

**Date:** 2026-09-20
**Repository:** https://github.com/adeliusa486/oran-ids-deployability
**Preceded by:** `reports/SESSION_REPORT.md` (campaign 1), kept unedited

---

## 1. What this campaign was asked to do, and what happened

Campaign 1 ended with a sound methods-and-measurement paper and a missing
headline: RQ1, cross-deployment transfer, had no result because no target corpus
could be obtained. This campaign was asked to resolve the blockers and rebuild
the paper from evidence.

**RQ1 is now answered.** The answer is negative and it is preserved.

Along the way, three defects were found in work that already existed and had
already been reported as sound — two of them in campaign 1's own published
findings, one in a handover note written to prevent exactly this kind of error.

## 2. The headline result

**Cross-deployment transfer largely fails.**

Trained on `D_A` (NetsLab-5GORAN-IDD, Zeek) and evaluated once on the whole of
`D_B` (5G-NIDD, Argus), 20 group-disjoint split seeds, threshold fixed at 0.5:

| | |
|---|---|
| Significant degradation | **6 of 6** non-trivial architectures, after Holm |
| `Delta_F1` | +0.096 to +0.300 |
| **Trivial floor on `D_B`** | **0.4240** (stratified) |
| Best architecture above the floor | **+0.148** (rf, 0.5716) |
| **MLP** | **0.4223 — below the floor**, balanced accuracy **0.4966** |

The MLP was the **best** model on held-out source data and transfers to below
chance. Across the six architectures there is **no significant rank correlation**
between in-distribution and transfer performance (Spearman ρ = +0.143,
p = 0.787), and the source-best model ranks **last of six** on the target.

The failure has a shape that macro-F1 hides. Logistic regression holds 97.7%
specificity and detects a quarter of the DoS traffic; the MLP detects 88% of DoS
and 81% of scans while calling 88.5% of benign traffic an attack. **No
architecture is usable on both classes.**

### The constraint that bounds all of it

The A3 single-exporter control is **not applied**. `D_A` is Zeek and `D_B` is
Argus. Every `Delta_F1` is an **upper bound** spanning an independently collected
deployment *and* an independent feature-extraction pipeline. Abraheem and
Edhirig (2026) quantify the separability: a classifier predicting which corpus a
flow came from reaches **0.993** balanced accuracy on the shared features.

## 3. Three defects found in existing work

### B-E — a published finding that was an estimator artefact (D-018)

Campaign 1 reported that deployment PPV spans **6x** across detectors whose
corpus precision is flat. PPV is violently non-linear in FPR near zero, and the
analysis averaged PPV **across evaluation folds**, so any fold with FPR = 0
contributed PPV = 1.000 exactly. XGBoost drew six such folds of forty, the MLP
drew none, and the published ranking is almost exactly that count.

```
pooled (micro)     1.40x      <- what a deployment experiences
median of folds    1.73x
mean of folds     13.18x      <- the estimator that was published
```

The claim is **withdrawn**. What survives is stronger: corpus precision ~0.93
against pooled deployment PPV 0.0055–0.0077, a **132x** collapse, with the
detectors **operationally indistinguishable at every base rate** from 1e-4 to 0.5.

The distortion scales with how few negatives a fold holds — 9x on radio folds
holding 136 benign windows, 1.4x on the larger network folds, none on the target
evaluated whole. **It is a property of the evaluation design, not of the metric.**

### D-015 — a feature mapping that would have manufactured the headline

`MEMORY.md` carried a handover table proposing `src_bytes <-> SrcBytes`. Zeek's
`src_bytes` is application **payload** and has median **0**, because both corpora
are dominated by floods and scans that carry none. Argus's `SrcBytes` is
header-inclusive with median **84**.

That mapping would have trained models on a feature that is zero almost
everywhere and scored them where it is 84 and up, collapsing every architecture
on the target — consistently, significantly, and looking exactly like the
generalisation failure the paper set out to find. Five of eighteen columns derive
from it.

Caught by twenty minutes of label-blind measurement before any transfer metric
existed. The real counterpart is `src_ip_bytes`, at 40 against 42 bytes per
packet.

### D-019 — a caveat that had been treated as a measurement

D-013 demoted the network layer to a cross-check because `src_ip` grouping might
really be attack grouping. Measured for the first time:

| Grouping | NMI(category) | Purity | % of oracle |
|---|---:|---:|---:|
| network `src_ip` | 0.128 | 0.435 | **20.6%** |
| `attack_type` (oracle) | 0.620 | 0.810 | 100% |
| **radio `session`** | **0.681** | **1.000** | **110%** |

The network confound is real but partial. **The radio confound is total** —
every capture run holds exactly one attack category. D-013 demoted the weaker
confound and kept the complete one.

## 4. Other measured results

| Finding | Status |
|---|---|
| Random splits inflate macro-F1 by +0.09 to +0.17, tracking model flexibility, with trivial baselines gaining nothing | unchanged from campaign 1 |
| **Time-disjoint evaluation costs 0.269 macro-F1** against a matched random-session control, **identically in both directions** (z = −3.04 both) | new |
| Time-disjoint nearly **triples** the alert burden: 67,065 to 178,839 false alerts/hour | new |
| **Extraction still dominates after a 12x speed-up**: 0.058 ms/flow against 1–25 µs of deployed inference | new |
| **No architecture dominates on deployability.** logreg wins the operational axes, rf the detection axes, tree latency, and mlp wins only source macro-F1 | new |
| FPR is **not a stable property** of these detectors: 0.000 to 0.890 across folds, and composition explains almost none of it (max R² 0.36) | new |

### The protocol ladder

Each step is closer to what a deployment experiences, and each costs more than
the choice of architecture does:

| Protocol | Holds out | Cost in macro-F1 |
|---|---|---:|
| random split | nothing | the optimistic bound |
| run-disjoint | capture-run identity | −0.09 to −0.17 |
| time-disjoint | a contiguous capture period | **−0.27** |
| cross-deployment | the deployment and the exporter | to the trivial floor |

## 5. Novelty, after a fresh literature pass

**Two of the five gaps this paper was built on were closed by other people, in
July and August 2026.**

- **Abraheem & Edhirig (7 Aug 2026)** ran bidirectional transfer between **the
  same two corpora**, with 15 harmonised features to our 15 concepts. **G1
  closed.** No "first cross-deployment evaluation" claim is available, and the
  claim was removed rather than softened.
- **Obiuwevwi et al. (Jul 2026)** measured AI inference inside a real
  OpenAirInterface + FlexRIC RIC. **G5 closed.**

What survives, stated as narrowly as the evidence allows:

1. A worked estimator error in operational IDS metrics, with its magnitude.
2. A published Zeek/Argus feature-mapping trap, with the full mapping table.
3. Transfer measured against a **group-disjoint** source reference.
4. An **eight-architecture ladder with trivial floors on the target**.
5. The combination of protocol, transfer, burden, calibration, drift and latency,
   with a decision register recording every claim withdrawn along the way.

## 6. What is BLOCKED, and why

| Item | Status | Blocker |
|---|---|---|
| Real Near-RT RIC runtime | **BLOCKED** | Windows Virtual Machine Platform feature absent — `wsl` fails with `HCS_E_SERVICE_NOT_AVAILABLE`, so Docker's Linux engine cannot start either. Needs admin rights and a reboot, then a bare-metal Linux host with isolated cores |
| CPU / RAM under load | **NOT MEASURED** | same |
| Manuscript | **34 synthetic values remain** | draft banner correctly up |

**Every latency figure in this repository is EMULATED.** No conformance claim is
made. Obiuwevwi et al. report inference three orders of magnitude faster than our
Python prototype for the same model families, which is not a hardware difference
— it is a compiled embedded model against a Python object graph. **The near-RT
crossing point is a property of the implementation, not the architecture.**

## 7. What changed in the repository

| | Campaign 1 end | Now |
|---|---|---|
| Commits | 25 | 50+ |
| Tests | 29, **only through one wrapper** | **50, from a bare `pytest`** |
| Decisions recorded | 14 | 19 |
| Validation | 11 PASS, 1 WARN, 4 BLOCKED | 16+ PASS, 3 BLOCKED, **0 FAIL** |
| Target corpus | none | obtained, open, checksummed, access-logged |
| RQ1 | no result | **answered** |

A reproducibility defect worth naming: `pytest` from a clean checkout had **never
worked**. The suite passed only because the validation harness injected
`PYTHONPATH=src` when it shelled out — a guard that works through one wrapper is
not a guard. Fixed with a root `conftest.py`.

## 8. Honest limitations

1. The **exporter confound cannot be removed** without re-extracting both corpora
   with one exporter. It bounds every transfer number here.
2. **No real RIC measurement exists**, and this machine cannot produce one.
3. **Thirty capture sessions** is a small population. Twenty split seeds resample
   it; they do not enlarge it.
4. **`ddos`, `bruteforce` and `web` are untestable in transfer** — `D_B` does not
   contain them. Reported as untestable, never averaged in.
5. **CPU and RAM under load are not measured at all.**
6. The target access log records that accesses happened, **not that no decision
   followed from one**.

## 9. What the paper should now claim

Not a first cross-deployment evaluation. Not near-RT conformance. What the
evidence supports is a paper about **evaluation practice in O-RAN intrusion
detection**, whose title already promises exactly that:

> *Why Accuracy Alone Is Not Enough*

- The protocol moves the score more than the architecture does, and there is a
  ladder of protocols each costing more than the last.
- The metric a paper reports cannot separate these detectors, and the metric an
  operator lives with says all of them are unusable — a 132x gap.
- In-distribution rank does not predict transfer rank.
- The model that wins on the reported metric wins on nothing else.
- Two of our own published numbers did not survive re-estimation, and the
  corrections are in the paper.

That last point is not an embarrassment to be minimised. In a paper arguing that
evaluation practice produces misleading numbers, demonstrating it on our own
results is the strongest evidence available.
