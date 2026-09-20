# EXP-034 — Temporal drift, measured on real elapsed time

**Date:** 2026-09-20
**Phase:** 34
**Verdict:** Training on one contiguous window of capture time and testing on a
disjoint one costs **0.269 macro-F1**, nearly **triples the alert burden**, and
badly degrades calibration. The effect is **identical in both directions**, so it
is not decay over time — it is that capture periods are heterogeneous.

---

## 1. Real time, not simulated drift

`D_A`'s radio layer spans **52.96 days** (2025-05-09 to 2025-07-01), and EXP-001
recovered **30 label-pure capture sessions** from the clock. Session identifiers
are assigned by a cumulative sum over time-sorted records, so the session index
**is** the temporal order. No drift is injected or simulated.

The network layer has **no time column at all**, so this experiment is radio-only
and says so rather than inventing an ordering.

## 2. Design, and why the control is the whole experiment

| | |
|---|---|
| temporal | train on the earliest *K* sessions, test on the latest. Boundary swept at 40/50/60/70% |
| **control** | the **same session counts**, drawn at **random** rather than by time. 20 repetitions |
| reverse | train on the latest, test on the earliest |

Without the control this experiment is uninterpretable. EXP-027 found that fold
FPR on this corpus ranges 0.000 to 0.890 depending only on which sessions land in
test, so a temporal drop could be entirely ordinary fold variance. The control
draws from exactly that variance, with matched session counts, 20 times.

The reverse direction separates two explanations: if the world drifts, forward
and reverse should differ; if periods are merely heterogeneous, they should match.

**Power, stated up front:** 30 sessions is a small population. This design
detects a large effect and nothing subtler.

## 3. Result

Macro-F1. Control is the mean over 20 random-session repetitions with matched
counts.

| Model | Control | Temporal forward | Δ | z | Temporal reverse | Δ | z |
|---|---:|---:|---:|---:|---:|---:|---:|
| hgb | 0.7779 | 0.4514 | **−0.327** | −3.89 | 0.5182 | −0.260 | −3.09 |
| xgboost | 0.7676 | 0.4654 | **−0.302** | −3.37 | 0.4316 | −0.336 | −3.76 |
| tree | 0.7473 | 0.4907 | −0.257 | −2.90 | 0.3570 | **−0.390** | −4.39 |
| rf | 0.7717 | 0.5193 | −0.252 | −2.79 | 0.3729 | **−0.399** | −4.42 |
| mlp | 0.7478 | 0.5008 | −0.247 | −2.90 | 0.6521 | −0.096 | −1.23 |
| logreg | 0.6840 | 0.4547 | −0.229 | −2.41 | 0.5528 | −0.131 | −1.32 |

**38 of 48** temporal configurations fall **outside the entire range** of their
20-repetition control — not merely below the mean, below the minimum.

### The symmetry is the finding

```
mean delta    forward −0.2690    reverse −0.2686
mean z        forward −3.04      reverse −3.04
```

To three decimal places, training on the past and testing on the future costs
exactly what training on the future and testing on the past costs.

**This is not drift in the sense of decay.** Nothing is degrading as time passes.
Capture periods are simply different from one another, and any split that keeps
time contiguous pays for it while a split that scatters sessions across time does
not. A random split over time is the optimistic case, and it is what most papers
report.

## 4. What it does beyond macro-F1

| | Temporal | Control | Ratio |
|---|---:|---:|---:|
| Brier | 0.2895 | 0.1610 | 1.80x worse |
| ECE | 0.2744 | 0.1699 | 1.62x worse |
| False alerts/hour | **178,839** | 67,065 | **2.67x** |

Calibration degrades by more than detection does, and the operational cost is
larger than either: a detector evaluated the easy way emits 67,000 false alerts an
hour, and the same detector evaluated across a time boundary emits 179,000.

This matters for Phase 28's question. Part of what calibration is asked to fix is
this: a model calibrated on one capture period is not calibrated for another, and
that is visible before any cross-corpus transfer is attempted.

## 5. The protocol ladder

Reading this alongside EXP-002 and EXP-026 gives a ladder of increasingly
realistic protocols, each costing more than the last:

| Protocol | What it holds out | Cost in macro-F1 |
|---|---|---:|
| random split | nothing | — (the optimistic bound) |
| run-disjoint | capture-run identity | −0.09 to −0.17 |
| **time-disjoint** | a contiguous capture period | **−0.27** |
| cross-deployment | the whole deployment and the exporter | −0.10 to −0.30, to near the floor |

Every step is closer to what a deployment experiences, and every step costs. A
published number carries the protocol it was measured under, and the protocol
moves the score more than the architecture does.

## 6. Threats

1. **Heterogeneity, not time, may be the mechanism.** Contiguous session blocks
   are internally more similar than scattered ones for reasons that need not be
   temporal — a configuration change, a different attack tool, a different
   operator. We cannot separate these. What we can say is that *contiguity in
   capture order* is what costs, and deployment is contiguous in exactly that way.
2. **Thirty sessions.** Small. The design detects a large effect only, and the
   effect is large.
3. **The radio layer's sessions are label-pure** (EXP-029 §3.2), so a contiguous
   block is also a particular set of attack scenarios. Part of the temporal gap
   is therefore attack-composition shift, and on this layer the two cannot be
   separated at all.
4. **Radio only.** The network layer has no clock.

## 7. Artefacts

```
results/EXP-034/raw/drift_runs.csv
results/EXP-034/processed/temporal_vs_control.csv
results/EXP-034/processed/drift_summary.csv
results/EXP-034/statistics/provenance.json          20 control reps, 648 s
```
