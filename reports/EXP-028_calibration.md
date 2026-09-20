# EXP-028 — Can calibration rescue operational precision?

**Date:** 2026-09-20
**Phase:** 28
**Verdict:** **No, and it makes things substantially worse.** Calibration improves
every calibration metric and destroys the operating point. Even an oracle prior
correction that consumes the target prior does not beat leaving the scores alone.

---

## 1. Why this was the right question

Two results made it so.

**Threshold saturation.** EXP-004 found four of five detectors could not reach
PPV = 0.50 at any threshold. A threshold is the only runtime control an operator
has, and it did not work. That looks like miscalibration.

**Prior shift.** `D_A` is **94.63%** attack and `D_B` is **60.71%**. A model
fitted under one prior and thresholded at 0.5 is not calibrated for the other, so
part of the EXP-026 transfer gap might be prior shift rather than concept shift.
Those have very different implications: prior shift is correctable with unlabelled
target data, concept shift is not.

## 2. Design

| | |
|---|---|
| Split | group-disjoint **three-way** on `src_ip`: train / calibration / test, with overlap asserted absent |
| Calibrators | raw, Platt (sigmoid), isotonic, temperature scaling |
| Fitted on | the source **calibration** fold only. Never on the test fold, never on the target |
| Evaluated on | source test **and** the whole of `D_B` |
| Seeds | 10 | 
| ECE | 15 **equal-mass** bins — equal-width bins are misleading when scores pile up near 1.0 |
| Oracle | a prior-corrected variant consuming the **target** prior, labelled non-deployable, reported as an upper bound only |
| Runtime | 2,661 s |

## 3. Result: the calibration metrics and the operator disagree

Logistic regression is the clearest case. Source test, mean over 10 seeds:

| Calibrator | Brier ↓ | ECE ↓ | **PPV in deployment** ↑ | **Alerts/hour** ↓ | Recall |
|---|---:|---:|---:|---:|---:|
| **raw** | 0.1023 | 0.1852 | **0.0174** | **35,330** | 0.838 |
| Platt | 0.0520 | 0.0861 | 0.0025 | 216,846 | 0.995 |
| isotonic | **0.0486** | **0.0866** | 0.0025 | 211,350 | 0.999 |

**Calibration halves the Brier score and halves the ECE, while making deployment
precision seven times worse and the alert queue six times larger.** The two
families of metric point in opposite directions.

The same pattern holds on the target:

| Model | Calibrator | Brier ↓ | **PPV** ↑ | **Alerts/hour** ↓ | Recall |
|---|---|---:|---:|---:|---:|
| logreg | **raw** | 0.3764 | **0.0221** | **19,551** | 0.328 |
| logreg | isotonic | **0.2538** | 0.0020 | 237,475 | 1.000 |
| xgboost | **raw** | 0.3148 | **0.0057** | **118,143** | 0.645 |
| xgboost | temperature | **0.2670** | 0.0057 | 118,143 | 0.645 |

### Why

A calibrator fitted on source data learns to map scores onto the **source
prior**, which is 94.63% attack. Applied anywhere, it pushes almost every score
above 0.5, so the detector flags nearly everything — recall goes to 1.000 and
precision collapses. It is behaving exactly as asked, on a prior that is wrong
for the deployment.

## 4. The deeper result: calibration cannot change what is reachable

All four transforms are monotone, so none of them can change the model's ranking
of examples, and therefore none can change the set of achievable (TPR, FPR)
operating points. This is verifiable and we verified it:

| Calibrator | ROC-AUC difference from raw |
|---|---|
| Platt | **< 1e-5** for 5 of 6 models |
| temperature | **< 1e-5** for 5 of 6 models |
| isotonic | up to 0.016 — isotonic is *non-decreasing*, not strictly increasing, so it merges distinct scores into ties |

The exception is the decision tree, where both Platt and isotonic move the AUC
materially (raw 0.822, isotonic 0.806, Platt 0.728). A depth-12 tree emits few
distinct score values, and a calibrator fitted on so coarse a distribution
degenerates. That is a property of the base model's score granularity, not of the
calibration method, and it is worth stating because it is the case where
calibration does real damage to discrimination.

**The consequence matters for how the reachability table below is read.**

| Reaches PPV ≥ 0.25 at any τ? | raw | Platt | isotonic | temperature |
|---|:--:|:--:|:--:|:--:|
| source, logreg | ✘ | ✘ | ✘ | **✔** |
| source, hgb / mlp / rf / xgboost | ✔ | ✘ | ✔ | ✔ |
| source, tree | ✘ | ✘ | ✘ | ✘ |
| **target, all six** | hgb only | ✘ | ✘ | hgb, mlp |

Temperature scaling **preserves the ROC exactly**, yet it appears to "rescue"
logistic regression on the source and the MLP on the target. It does no such
thing. It rescales the score distribution so that the *fixed grid of thresholds
we sweep* lands on a different part of the same ROC curve. **Those cells are
threshold-grid artefacts, not calibration benefits** — a distinction that is easy
to miss and would have produced a positive-sounding finding from nothing.

Platt scaling cannot reach PPV ≥ 0.25 anywhere, on either domain, for any model.

## 5. Threshold saturation is a discriminability limit, not a calibration failure

This is the finding that replaces the one we went looking for.

If every calibrator is monotone, and PPV at a fixed base rate is a function of
the operating point, then whether a usable PPV exists at all is decided by the
**ROC curve**, which calibration does not meaningfully change. The detector
either separates the classes well enough at that base rate or it does not.

On the target it does not. Target ROC-AUC is 0.537 to 0.691 across the six
architectures. There is no threshold, under any calibration, that extracts a
usable operating point from a curve that close to the diagonal.

And where a bar *is* reachable, the price is the whole detector:

| Domain | Model | Calibrator | τ | Recall there | Alerts/hour |
|---|---|---|---:|---:|---:|
| target | hgb | raw | 0.995 | **0.064** | 14,183 |
| target | hgb | temperature | 0.990 | **0.039** | 7,090 |
| target | mlp | temperature | 0.999 | 0.282 | 63,722 |

Reaching PPV ≥ 0.25 on the target costs **93.6% of the attacks**.

## 6. The oracle, and what it says about prior shift

The prior-corrected variants consume the **target prior**. They are not
deployable and carry no claim. They exist to answer one question: how much of
the gap is prior shift?

| Model | Calibrator | PPV | Alerts/hour | Recall |
|---|---|---:|---:|---:|
| logreg | **raw** (no oracle) | **0.0221** | 19,551 | 0.328 |
| logreg | isotonic + prior ORACLE | 0.0197 | **3,285** | 0.162 |
| logreg | Platt + prior ORACLE | 0.0208 | 5,090 | 0.220 |
| xgboost | isotonic + prior ORACLE | 0.0654 | 90,272 | 0.497 |

**Even with the target prior known exactly, prior correction does not beat raw
scores on precision for logistic regression.** It does cut the alert queue
sharply — 19,551 to 3,285 per hour — by moving to a much more conservative
operating point, at the cost of more than half the remaining recall.

So prior shift is real and correcting it helps the *queue*, but it is not what is
limiting *precision*. The limit is discriminability, and the target ROC is where
that is visible.

## 7. What this does to the paper

| Item | Consequence |
|---|---|
| C8 threshold saturation | **Stands, and is re-attributed.** Not a calibration failure — a discriminability limit that calibration cannot address |
| "tune the threshold" | Must not be offered as a remedy. It is the control that does not work, and calibration does not restore it |
| Calibration section | Reports a **negative** result: source-fitted calibration worsens the operating point because it encodes the source prior |
| Brier / ECE | Reported, with the explicit warning that they improve while the operational metrics degrade |
| Prior shift | Real, corrigible in principle, and **not the binding constraint** |
| Methods note | Any threshold sweep on a fixed grid can produce apparent differences between monotone calibrators. Report the ROC, not just the grid |

## 8. Threats

1. **The threshold grid is finite** (24 points to τ=0.999). Section 4 shows this
   is not a detail: two apparent rescues are grid artefacts. A continuous sweep
   would remove them and is the better instrument.
2. **The calibration fold shares the source corpus**, so a calibrator fitted
   there inherits its prior by construction. That is the realistic setting — an
   operator has source labels and not target ones — but it means this result is
   about *source-fitted* calibration specifically.
3. **10 seeds over 152 `src_ip` groups.** Same limitation as everywhere else.
4. **The tree's degenerate calibration** is a score-granularity effect and should
   not be generalised to other low-capacity models without checking.

## 9. Artefacts

```
results/EXP-028/raw/calibration_runs.csv
results/EXP-028/raw/calibration_tau_sweep.csv
results/EXP-028/processed/calibration_summary.csv
results/EXP-028/processed/ppv_reachability.csv
results/EXP-028/statistics/provenance.json      10 seeds, 6 models, 2,661 s
```
