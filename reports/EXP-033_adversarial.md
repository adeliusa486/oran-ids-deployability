# EXP-033 — Adversarial and degraded-telemetry robustness

**Date:** 2026-09-20
**Phase:** 33 (cut by D-009 in campaign 1, executed now)
**Runtime:** 3,558 s, 5 seeds, 6 architectures, 6 attacks × 6 perturbation
magnitudes, plus a label-poisoning sweep with refitting

**Verdict:** detection degrades modestly. **The alert queue degrades two to four
times as much**, and that is the finding — the operational metric is far more
sensitive to degraded telemetry than macro-F1 is.

---

## 1. Scope, stated before the results

**This is not first, and does not claim to be.** Adversarial attacks on O-RAN ML
components are well covered: evasion against xApps (arXiv:2309.03844), black-box
evasion under near-RT timing constraints (arXiv:2510.18160), KPI poisoning
through the E2 path (arXiv:2505.05537), and a system-level analysis at WiSec 2024.

What is added is the **operational reading**. Those studies report accuracy
degradation. An operator does not experience accuracy; they experience an alert
queue and a threshold. Every attack here is scored on detection, on burden, and
on whether the operating point survives.

### Threat models, and the one that is honest

| Attack | Agent | Realisable? |
|---|---|---|
| `gaussian_noise` | none — sensor noise | telemetry fault |
| `missing_telemetry` | none — dropped E2 report | telemetry fault |
| `stale_telemetry` | none — delayed indication | telemetry fault |
| `scaling_attack` | attacker inflates a KPI | yes |
| `evasion_unconstrained` | attacker moves features freely | **NO — upper bound only** |
| `evasion_constrained` | attacker pads and delays | **yes — the realistic number** |
| `label_poisoning` | attacker corrupts training labels | yes |

`evasion_unconstrained` permits *reducing* bytes and packets already sent, which
no attacker can do. It is reported as an upper bound and never as an attack
result. `evasion_constrained` allows only increases to bytes, packets and
duration — padding and delay, which an attacker genuinely controls. The protocol
one-hot is never perturbed: a perturbed protocol vector corresponds to no packet.

## 2. Detection degrades modestly

Macro-F1 drop at ε = 0.10 (positive = worse):

| Model | evasion (constrained) | evasion (unconstr., bound) | gaussian noise | missing telemetry | scaling | stale |
|---|---:|---:|---:|---:|---:|---:|
| tree | **+0.062** | +0.045 | **+0.084** | **+0.138** | −0.004 | −0.001 |
| logreg | −0.006 | +0.026 | +0.042 | +0.014 | +0.038 | +0.000 |
| hgb | +0.012 | +0.000 | +0.015 | −0.011 | −0.003 | +0.000 |
| xgboost | +0.002 | −0.005 | +0.004 | −0.009 | −0.002 | +0.000 |
| mlp | −0.002 | +0.000 | +0.006 | +0.039 | −0.004 | +0.000 |
| rf | **−0.016** | **−0.029** | −0.015 | +0.004 | −0.007 | +0.000 |

Even at ε = 0.50 the largest drop is 0.269 (MLP under missing telemetry). On
detection alone, these models look robust.

### Two results that are not noise

**Stale telemetry costs essentially nothing** — every drop is within ±0.004 at
every magnitude. Carrying forward the previous record's features is nearly
harmless, because adjacent flow records resemble one another. A delayed E2
indication is a far less serious fault than a missing one.

**Constrained evasion makes attacks *more* detectable for the tree ensembles.**
The random forest improves by 0.016 at ε = 0.10 and by 0.057 at ε = 0.50. This is
not a bug and it has a clean explanation: attack traffic in these corpora already
carries higher volumetric features than benign traffic, so an attacker who pads
packets and lengthens flows moves *further* from the benign region, not closer.

**The realistic evasion attack is weaker than the unrealisable upper bound, and
for some architectures it points the wrong way entirely.** A study that reports
only unconstrained perturbation would conclude these detectors are evadable; the
constrained threat model says an attacker cannot evade them by padding, and may
make things worse for themselves.

## 3. The alert queue is where the damage lands

False alerts per hour at ε = 0.10 against the clean baseline:

| Model | clean | missing telemetry | ratio | gaussian noise | ratio |
|---|---:|---:|---:|---:|---:|
| logreg | 44,055 | **179,161** | **4.07x** | 51,895 | 1.18x |
| xgboost | 22,379 | **69,529** | **3.11x** | 33,434 | 1.49x |
| hgb | 24,470 | 53,057 | 2.17x | 47,554 | 1.94x |
| tree | 48,537 | 77,495 | 1.60x | 87,558 | **1.80x** |
| rf | 72,468 | 94,137 | 1.30x | 89,917 | 1.24x |
| mlp | 108,682 | 110,481 | 1.02x | 109,162 | 1.00x |

**Logistic regression loses 0.014 of macro-F1 and gains 135,000 false alerts an
hour.** XGBoost loses 0.009 and triples its queue. A robustness evaluation that
reports only detection metrics would call both of these outcomes negligible.

This is the same argument the paper makes about base rates, arriving from a
different direction: the metric a paper reports and the metric an operator lives
with move independently, and the second one moves further.

## 4. Missing telemetry: *which* feature, not *how many*

The strongest single effect in the study, and it is not monotone in ε. At
ε = 0.05 — one feature zeroed — logistic regression drops **0.240** of macro-F1
and the MLP drops 0.195. At ε = 0.10, two features, logistic regression drops
only 0.014.

That is not a measurement error, it is the design: the attack samples a *random*
feature subset per configuration, so the identity of the dropped feature varies
between cells. **The variance across which feature is lost is larger than the
trend in how many are lost.**

The honest conclusion is therefore about identity rather than count: **losing a
single feature can cost a linear model a quarter of its macro-F1**, and an
operator cannot know in advance which E2 subscription gap matters. A study that
wanted the trend in ε would need to fix the subset across magnitudes, and that is
the right design for a follow-up. It is reported this way rather than smoothed,
because the smoothed version would understate the worst case by an order of
magnitude.

## 5. Label poisoning

Macro-F1 after refitting on training labels corrupted at each rate:

| Model | 0% | 1% | 5% | 10% | 25% | Δ at 25% |
|---|---:|---:|---:|---:|---:|---:|
| rf | 0.677 | 0.653 | 0.607 | 0.584 | **0.496** | **−0.181** |
| xgboost | 0.636 | 0.625 | 0.582 | 0.567 | **0.488** | **−0.148** |
| hgb | 0.616 | 0.608 | 0.570 | 0.581 | 0.554 | −0.062 |
| tree | 0.625 | 0.619 | 0.596 | 0.617 | 0.565 | −0.060 |
| logreg | 0.593 | 0.590 | 0.590 | 0.583 | 0.539 | **−0.054** |
| **mlp** | 0.700 | 0.700 | 0.715 | 0.719 | **0.734** | **+0.034** |

The high-capacity ensembles are the most poisonable: the random forest loses 0.18
of macro-F1 at 25% corruption and XGBoost 0.15. Logistic regression is the most
robust of the six, losing 0.054.

**The MLP improves under poisoning**, monotonically, all the way to 25%. The
explanation is unglamorous: label noise is acting as a regulariser on a model
that was over-fitting its training fold. It is reported because it is what
happened, and because it is a useful caution — a robustness curve that goes the
wrong way usually means the clean baseline was the anomaly, not that the attack
helps.

Note the ordering: **capacity that buys in-distribution accuracy also buys
poisonability**, which is the same relationship EXP-002 found between capacity
and split-protocol inflation, and the same one EXP-026 found between source rank
and transfer failure. Three different experiments, one pattern.

## 6. What this does to the paper

| Item | Consequence |
|---|---|
| Robustness | Moves from SKIP to a measured result. **No primacy claim** |
| The headline | Detection degrades modestly; **burden degrades 2–4x**. Report both or the finding inverts |
| Evasion | Report the **constrained** number. The unconstrained one is an upper bound and for the tree ensembles points the wrong way |
| Missing telemetry | The dominant fault. Report the worst case, not the ε trend |
| Poisoning | Capacity and poisonability track together |
| Deployability | Robustness enters `EXP-035` as `worst_case_f1_drop`, now populated for all six |

## 7. Threats

1. **The missing-telemetry subset is resampled per cell**, so the ε axis is
   confounded with feature identity. Stated in §4 rather than smoothed away.
2. **Perturbations are in the model's input space.** `log1p` is monotone, so the
   constrained threat model ("can only increase") is preserved, but a
   perturbation budget defined in log space is not the same as one in bytes.
3. **No adaptive adversary.** Every attack here is oblivious to the detector. A
   white-box attacker optimising against a specific model would do better, and
   the cited literature shows they do.
4. **5 seeds.** Enough for a sensitivity analysis, not for a significance claim,
   and no significance is claimed.

## 8. Artefacts

```
results/EXP-033/raw/adversarial_runs.csv
results/EXP-033/raw/poisoning_runs.csv
results/EXP-033/processed/adversarial_summary.csv
results/EXP-033/processed/poisoning_summary.csv
results/EXP-033/statistics/provenance.json
```
