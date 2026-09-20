# EXP-026 — Cross-deployment transfer (RQ1)

**Date:** 2026-09-20
**Phase:** 26
**Gate:** **PASS** — the experiment ran as pre-registered and produced a result
**Scientific outcome:** **NEGATIVE, and preserved.** Transfer largely fails.

> **Reading rule, mandatory.** The A3 single-exporter control is **not** applied.
> `D_A` is exported by Zeek, `D_B` by Argus, and the two disagree about where a
> flow ends. Every `Delta_F1` below is an **UPPER BOUND** on deployment shift,
> spanning an independently collected deployment **and** an independent
> feature-extraction pipeline. It must never be described as being "due to
> deployment shift". Abraheem & Edhirig (2026) quantify how separable the two
> corpora are: a classifier predicting *which corpus a flow came from* reaches
> **0.993 balanced accuracy** on the shared features, and stays there after CORAL
> alignment and after feature filtering.

---

## 1. What was run

| | |
|---|---|
| Source | `D_A` = NetsLab-5GORAN-IDD, CU flow records (Zeek), 1,640,182 rows, 94.63% attack |
| Target | `D_B` = 5G-NIDD (Argus), 1,215,889 rows, 60.71% attack, evaluated **whole, once** |
| Space | 18 columns / 15 concepts, `configs/features/shared_space.yaml` |
| Source split | group-disjoint on `src_ip`, 20 split seeds |
| Normalisation | fitted on source training data only; `log1p` is parameter-free (D-016) |
| Threshold | fixed at 0.5, never tuned on the target |
| Models | the full ladder, 8 architectures including both trivial floors |
| Runtime | 1,758 s |
| Untestable categories | `ddos`, `bruteforce`, `web` — present in `D_A`, absent from `D_B` |

Every read of the target is timestamped in `results/EXP-026/logs/target_access.log`.

## 2. Headline result

Macro-F1, mean over 20 split seeds, paired t-intervals, Holm-corrected over the
six non-trivial architectures.

| Model | Source held-out | **Target** | `Delta_F1` | 95% CI | d_z | p (Holm) | Sig. |
|---|---:|---:|---:|---|---:|---:|:--:|
| mlp | 0.7226 | **0.4223** | **+0.3002** | [+0.225, +0.376] | 1.86 | 0.0000 | yes |
| rf | 0.7009 | **0.5716** | +0.1293 | [+0.052, +0.207] | 0.78 | 0.0049 | yes |
| xgboost | 0.6461 | **0.5324** | +0.1136 | [+0.054, +0.173] | 0.90 | 0.0037 | yes |
| hgb | 0.6474 | **0.5366** | +0.1108 | [+0.053, +0.169] | 0.89 | 0.0037 | yes |
| tree | 0.6193 | **0.5182** | +0.1011 | [+0.031, +0.171] | 0.68 | 0.0069 | yes |
| logreg | 0.6259 | **0.5297** | +0.0962 | [+0.043, +0.149] | 0.85 | 0.0037 | yes |
| *stratified* | *0.4943* | *0.4240* | *+0.0703* | — | — | — | floor |
| *majority* | *0.4922* | *0.3778* | *+0.1144* | — | — | — | floor |

**H-transfer is not falsified.** Every non-trivial architecture degrades
significantly. But the size of the drop is the less interesting half.

## 3. The number that matters is the floor, not the gap

A macro-F1 of 0.53 means nothing until you know what guessing scores on the same
corpus. On `D_B`, a stratified coin flip scores **0.4240**.

| Model | Target macro-F1 | **Above the coin flip** | Balanced accuracy |
|---|---:|---:|---:|
| rf | 0.5716 | **+0.1476** | 0.5809 |
| hgb | 0.5366 | +0.1126 | 0.5664 |
| xgboost | 0.5324 | +0.1084 | 0.5618 |
| logreg | 0.5297 | +0.1057 | **0.6270** |
| tree | 0.5182 | +0.0942 | 0.5328 |
| **mlp** | **0.4223** | **−0.0017** | **0.4966** |

Two things follow, and both are stronger than "scores drop".

**The MLP transfers to below chance.** Its target macro-F1 is *beneath* the
stratified floor, and its balanced accuracy is **0.4966** — on the wrong side of
0.5. Trained on one O-RAN deployment and applied to another, it is worse than
guessing. It was also the **best** model on held-out source data.

**Nothing transfers well.** The best architecture clears a coin flip by 0.148
macro-F1 and reaches 0.581 balanced accuracy. This is not degradation, it is
near-collapse, and it is consistent with Abraheem & Edhirig (2026), who report
zero-shot balanced accuracies of 0.505–0.834 between the same two corpora
depending on attack family.

## 4. In-distribution score does not predict transfer

| | Best on source | Best on target |
|---|---|---|
| | **mlp** (0.7226) | **rf** (0.5716) |

The architecture that wins on held-out source data ranks **last of six** on the
target. Across the six:

```
Spearman rho = +0.143   (p = 0.787)
Kendall  tau = +0.333   (p = 0.469)
```

**No significant rank correlation.** A practitioner selecting an architecture by
its published in-distribution score has, on this evidence, close to no
information about how it will transfer. The draft manuscript claimed "the ranking
is broadly preserved". It is not, and the sign of the relationship for the
top-ranked model is inverted.

## 5. Per-category: the failure has a shape

Mean over 20 seeds. `benign` is specificity; the rest are recall. `D_B` holds
477,736 benign, 682,152 `dos`, 56,001 `probe`.

| Model | benign (spec.) | dos (recall) | probe (recall) |
|---|---:|---:|---:|
| logreg | **0.9766** | 0.2472 | **0.6448** |
| tree | 0.4417 | 0.6508 | 0.2946 |
| rf | 0.4590 | 0.7448 | 0.1907 |
| xgboost | 0.5713 | 0.5837 | 0.1684 |
| hgb | 0.5371 | 0.6297 | 0.1830 |
| mlp | 0.1151 | 0.8839 | 0.8073 |
| *majority* | *0.0000* | *1.0000* | *1.0000* |

**No architecture is usable on both classes.** Logistic regression keeps 97.7%
specificity and detects only a quarter of the DoS traffic. The MLP detects 88% of
DoS and 81% of scans while misclassifying 88.5% of benign traffic as attack —
which is why its macro-F1 sits under the floor. The tree ensembles occupy a
middle ground and are the worst at scanning, detecting 17–29% of `probe`.

This is not a smooth degradation. It is each architecture failing differently,
and the failure mode is invisible in a single macro-F1 number.

## 6. Operationally, the target reverses the source-side conclusion

Pooled PPV at `pi = 0.002` (EXP-027, pooled estimator per D-018):

| Surface | PPV spread across detectors | Same, by mean-of-folds |
|---|---:|---:|
| `D_A` radio held-out | 1.40x | 13.18x **(the B-E artefact)** |
| `D_A` network held-out, shared space | 5.74x | 8.29x |
| **`D_B` target** | **11.68x** | 12.05x |

On the target the three estimators agree (11.68 / 12.30 / 12.05), so **this
spread is real and is not B-E.** Logistic regression reaches PPV 0.0232 against
0.0020–0.0026 for everything else, because its target FPR is 0.023 while the
others run at 0.43–0.88.

Two consequences:

1. **The detectors are operationally indistinguishable on the source and an
   order of magnitude apart on the target.** The corpus you evaluate on decides
   whether your architectures look the same or different.
2. **The simplest model is the operationally best one on the unseen
   deployment** — and it is not the best by macro-F1 there either. Whichever
   single metric you choose, it recommends a different model.

A useful diagnostic falls out of the same table: the B-E artefact scales with how
few benign samples a fold holds. The radio folds carry a median of 136 benign
windows and the artefact is 9x; the network shared-space folds carry far more and
it is 1.4x; the target is evaluated whole and it vanishes. **The distortion is a
property of the evaluation design, not of the metric.**

## 7. Threats to validity

1. **Exporter confound, not controlled.** See the reading rule at the top. This
   is the dominant threat and it bounds every number here from above.
2. **`D_B` covers three of six canonical categories.** `ddos`, `bruteforce` and
   `web` are untestable in transfer and are reported as untestable, not averaged
   in as though they had been evaluated.
3. **Prior shift.** `D_A` is 94.63% attack, `D_B` 60.71%. A model trained under
   one prior and thresholded at 0.5 is not calibrated for the other. Phase 28
   asks whether calibration recovers anything; until it runs, part of the gap
   here may be prior shift rather than concept shift.
4. **Source folds vary enormously.** The group-disjoint source reference is
   itself unstable — several seeds produce a source score *below* the target
   score. That instability is EXP-029's subject and it widens every CI here.
5. **One threshold.** Everything is at `tau = 0.5`. Threshold-free PR-AUC is in
   the results files and tells the same story.

## 8. What this does to the paper

| Item | Consequence |
|---|---|
| RQ1 | **Answered.** Transfer largely fails; the MLP falls below chance |
| C2 "every architecture loses substantial F1" | **SUPPORTED**, 6/6 significant after Holm |
| "the ranking is broadly preserved" | **CONTRADICTED.** rho = +0.14, p = 0.79; source-best ranks last |
| "24 shared features" | **WRONG.** 15 concepts / 18 columns |
| Novelty | Abraheem & Edhirig got here first. Position as replication-plus-extension: 8 architectures to their 1, trivial floors on the target, group-disjoint source reference |
| Deep models in `tab:cross` | 1D-CNN and LSTM were never run. Removed |

## 9. Reverse direction

`D_B -> D_A` is running as a symmetry check (D-017), to separate "detectors do
not transfer" from "`D_B` is simply harder". It is reported separately and its
own held-out reference is a **random** split, because `D_B` publishes no
identifiers and has no group key — so that reference is an optimistic bound and
its `Delta_F1` is an over-estimate.

## 10. Artefacts

```
results/EXP-026/raw/transfer_runs__a_to_b.csv              320 rows
results/EXP-026/processed/transfer_summary__a_to_b.csv
results/EXP-026/processed/per_category_recall__a_to_b.csv
results/EXP-026/statistics/provenance__a_to_b.json
results/EXP-026/logs/target_access.log
tables/generated/transfer_d_a_to_d_b.tex
```

---

## 11. The reverse direction: `D_B -> D_A` (added after §9 was written)

Run as a symmetry check under D-017, after the primary direction was committed.
Runtime 4,464 s, 20 split seeds, the same shared space and the same threshold.

### 11.1 The caveat, stated before the numbers

`D_B` publishes no identifier columns, so it has **no group key**. Its own
held-out reference is therefore a **random split**, which by this project's own
Finding 1 is the inflated protocol. The `source_f1` column below is an
**optimistic bound** and every `Delta_F1` in this direction is consequently an
**over-estimate**. It is reported because the comparison it enables does not
depend on it — see §11.3.

### 11.2 Result

| Model | Source held-out (optimistic) | **Target (`D_A`)** | `Delta_F1` | d_z | p (Holm) |
|---|---:|---:|---:|---:|---:|
| logreg | 0.7081 | **0.5631** | +0.1450 | 28.3 | 0.0000 |
| xgboost | 0.7526 | 0.4971 | +0.2555 | 12.5 | 0.0000 |
| mlp | 0.7144 | 0.4981 | +0.2163 | 4.5 | 0.0000 |
| hgb | 0.7526 | 0.4883 | +0.2643 | 5.0 | 0.0000 |
| tree | 0.7522 | **0.3430** | +0.4092 | 4.2 | 0.0000 |
| rf | 0.7298 | **0.3365** | +0.3933 | 11.1 | 0.0000 |
| *majority* | *0.3774* | *0.4862* | — | — | — |
| *stratified* | *0.5023* | *0.4171* | — | — | — |

All six non-trivial architectures degrade significantly after Holm correction.

### 11.3 The comparison that does not depend on the caveat

The **target-side scores are protocol-independent.** How `D_B` was split affects
what the model learned, not how the trivial floors on `D_A` behave. So the
distance from the floor is directly readable even though `Delta_F1` is inflated.

On `D_A`, the majority floor is **0.4862** and the stratified floor is **0.4171**.

| Model | Target macro-F1 | vs majority | vs stratified |
|---|---:|---:|---:|
| logreg | 0.5631 | **+0.077** | +0.146 |
| mlp | 0.4981 | +0.012 | +0.081 |
| xgboost | 0.4971 | +0.011 | +0.080 |
| hgb | 0.4883 | +0.002 | +0.071 |
| **tree** | **0.3430** | **−0.143** | **−0.074** |
| **rf** | **0.3365** | **−0.150** | **−0.081** |

**Two architectures fall below both trivial floors**, and three more beat the
majority classifier by between 0.002 and 0.012 of macro-F1. Only logistic
regression clears it by a margin worth the name.

The forward direction put one architecture below the floor. The reverse puts two
below and three within a rounding error of it. **Transfer fails in both
directions**, which is what the symmetry check existed to establish: the finding
is about transfer, not about `D_B` being an intrinsically harder corpus.

### 11.4 Where the failure lands: unseen categories are invisible

Per-category on `D_A`, mean over 20 seeds. `benign` is specificity, the rest
recall. This direction has **no untestable categories** — `D_A` contains
everything `D_B` does and more — which is what makes the table informative.

| Model | benign | ddos | dos | probe | bruteforce | **web** |
|---|---:|---:|---:|---:|---:|---:|
| logreg | 0.706 | 0.963 | 0.854 | 0.923 | 0.568 | **0.298** |
| xgboost | 0.887 | 0.852 | 0.729 | 0.885 | 0.354 | **0.011** |
| hgb | 0.875 | 0.826 | 0.719 | 0.866 | 0.335 | **0.013** |
| mlp | 0.855 | 0.865 | 0.768 | 0.781 | 0.417 | **0.004** |
| tree | 0.818 | 0.481 | 0.437 | 0.474 | 0.431 | **0.129** |
| rf | 0.890 | 0.490 | 0.405 | 0.550 | 0.341 | **0.005** |

The structure is clean and it explains the aggregate.

**Categories present in the training corpus transfer.** `D_B` contains floods and
scans, and on `D_A` the boosted models detect `ddos` at 0.83–0.87, `dos` at
0.72–0.77 and `probe` at 0.87–0.89. That is real transfer of a real capability.

**Categories absent from the training corpus do not.** `D_B` contains no web
attacks, and on `D_A` web recall is **0.004 to 0.013** for four of six
architectures — the random forest detects half of one percent of SQL injection,
XSS and directory brute force. `bruteforce`, also absent from `D_B`, sits at
0.33–0.57.

This is not a subtle distributional effect. A detector does not recognise an
attack class it has never been shown, it fails silently rather than noisily, and
the aggregate macro-F1 conceals the difference between an architecture that
transfers its competence and one that does not.

It also explains why the **linear model transfers best in both directions**.
Logistic regression is the only architecture with non-trivial web recall (0.298)
and the best bruteforce recall (0.568), because it generalises coarsely instead
of fitting the source corpus's particular attack signatures. Its cost is the
worst benign specificity in the table (0.706). That trade — worse on the class
you have, better on the class you have never seen — is the whole of the
generalisation argument in one row.

### 11.5 Consequence for the paper

| Item | Consequence |
|---|---|
| "`D_B` is simply a harder corpus" | **Ruled out.** Failure is symmetric |
| Severity | The reverse direction is **worse**: 2 architectures below both floors |
| The mechanism | Unseen attack categories are essentially undetected (web: 0.004–0.013) |
| Why logreg wins | Coarse generalisation, paid for in benign specificity |
| Reporting rule | The reverse `Delta_F1` must always carry its optimistic-bound caveat; the **target-side distance from the floor must not**, because it does not depend on the source split |
