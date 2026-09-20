# EXP-029 — Is a host-disjoint split really an attack-disjoint split?

**Date:** 2026-09-20
**Phase:** 29
**Verdict:** **The confound is real but partial on the network layer — and
total on the radio layer, which is the opposite of what D-013 assumed.**

---

## 1. The worry, and why it needed measuring

In a testbed each attack scenario is typically launched from a dedicated host. If
that holds here, grouping by `src_ip` produces groups that are nearly pure in
attack category, and a "host-disjoint" split is in substance an
**attack-disjoint** split. Those are different tasks:

| Protocol | What it asks |
|---|---|
| host-disjoint | generalise to a new host running attacks you have seen |
| attack-disjoint | generalise to an attack you have never seen |

The second is much harder, and a leakage magnitude measured under it is not the
quantity the paper claims. D-013 demoted the network layer to a directional
cross-check on the strength of this worry. **The worry was never measured.**

## 2. Method

For each candidate grouping, how much does the grouping already determine the
label? Three quantities, each read against **two** nulls, because an NMI of 0.4
means nothing on its own:

- **shuffle null** — the same groups, labels permuted. Destroys alignment, keeps
  group structure.
- **size-matched null** — a random grouping with the same number and size
  profile. Controls for the fact that many small groups inflate NMI mechanically.

And an **oracle**: grouping directly *by* `attack_type`. If `src_ip` scores like
the oracle, the two protocols are the same protocol wearing different names.

Part A runs on a declared, seeded 300,000-row subsample. Mutual information is a
plug-in estimator and is biased upward at small *n*, so both nulls are computed
on the **same** subsample — they carry the same bias and the comparison against
them survives, even though the absolute NMI is not comparable to a whole-corpus
value.

## 3. Result

| Layer | Grouping | Groups | Largest | NMI(cat) | shuffle null | size-matched null | Purity | Cramér's V |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| network | `src_ip` | 152 | 0.339 | **0.128** | 0.0006 | 0.0006 | **0.435** | 0.350 |
| network | `dst_ip` | 1,083 | 0.837 | 0.176 | 0.0060 | 0.0059 | 0.440 | 0.433 |
| network | `src_ip`×`dst_ip` | 2,768 | 0.295 | 0.176 | 0.0096 | 0.0097 | 0.493 | 0.498 |
| network | `dst_port` | 17,047 | 0.555 | 0.260 | 0.0471 | 0.0469 | 0.523 | 0.573 |
| network | **`attack_type` (ORACLE)** | 15 | 0.309 | **0.620** | 0.0001 | 0.0001 | **0.810** | 0.911 |
| radio | **`session`** | 30 | 0.127 | **0.681** | 0.0106 | 0.0114 | **1.000** | **1.000** |

### 3.1 The network layer: real, but partial

`src_ip` carries genuine label information — NMI 0.128 against nulls of 0.0006,
which is **213x above chance**, and both nulls agree, so it is not a
small-group artefact.

But it is nowhere near the oracle:

```
src_ip NMI is 20.6% of grouping directly by attack type
src_ip purity 0.435   against oracle purity 0.810
src_ip Cramér's V 0.350   against oracle 0.911
```

A `src_ip` group is **not** an attack scenario. Fewer than half its records share
its modal category. Host-disjoint and attack-disjoint are measurably different
protocols on this layer.

The binary story differs from the categorical one and is worth stating:
`purity_binary` is **0.962** for `src_ip`. Hosts are nearly pure in *attack
versus benign* while being impure in *which* attack. That is the expected shape
for a testbed where attack traffic originates from dedicated hosts but each host
runs several scenarios, and it means the binary task carries more host-identity
signal than the multi-class one.

### 3.2 The radio layer: total, and this was not the layer under suspicion

`session` grouping has **purity 1.000 and Cramér's V 1.000**. Every recovered
capture run contains exactly one attack category, by construction of the testbed.
EXP-001 recorded this as "30 runs, 100% label-pure" and treated it as a quality
property. Measured against the oracle it is also a confound, and a stronger one
than the network layer's:

```
radio session   NMI 0.681, purity 1.000, Cramér's V 1.000
network src_ip  NMI 0.128, purity 0.435, Cramér's V 0.350
```

The session grouping carries *more* category information than grouping by attack
type does (0.681 against 0.620), simply because 30 label-pure sessions are a
finer partition than 15 attack types.

## 4. What this does to D-013

D-013 demoted the **network** layer to a directional cross-check because of a
suspected `src_ip`/attack alignment, and kept the **radio** layer as primary.

The measurement says the alignment is **weaker on the layer that was demoted and
complete on the layer that was kept.** D-013's caution was reasonable and its
direction was wrong.

This does not invalidate the radio-layer leakage result, and here is the
distinction that matters. Purity 1.000 means no *group* mixes categories. It does
not mean a group-disjoint split holds out a category: with 30 sessions over 6
categories, each category spans about five runs, so a held-out session usually
shares its category with training sessions. Run-disjoint therefore still asks the
intended question — generalise to a **new capture run of a possibly familiar
attack** — and the random-versus-run-disjoint gap still measures memorisation of
run identity.

What it does mean is that on the radio layer, run identity and attack identity
cannot be separated **at all**, so no result from that layer can distinguish
"memorised the run" from "memorised the attack". On the network layer they can be
separated, and the separation is measurable.

**Recommended amendment to D-013:** both layers are confounded, the radio layer
more completely. The network layer should be **promoted from cross-check to
co-primary** for any claim that needs run identity and attack identity to be
distinguishable, and the radio layer's role restricted for those claims. Neither
layer should carry an unqualified "run-disjoint" label without the purity figure
beside it.

## 5. Part C — what explains the fold-to-fold FPR range?

EXP-027 found FPR ranging 0.000 to 0.890 across group-disjoint folds. Part C
regressed per-fold FPR on test-fold composition:

| Predictor | mean R² | max R² | significant |
|---|---:|---:|---:|
| `n_benign_test` | 0.061 | 0.288 | 1 of 7 |
| `train_prevalence` | 0.061 | 0.362 | 1 of 7 |
| `benign_frac_test` | 0.058 | 0.358 | 1 of 7 |
| `test_prevalence` | 0.058 | 0.358 | 1 of 7 |
| `n_test_groups` | 0.038 | 0.064 | 0 of 7 |

**Composition explains almost none of it.** It is not how many groups land in
test, nor how many benign samples they carry, nor the class balance. It is
*which* groups land in test — their identity, not their shape. Given §3.2, on the
radio layer group identity is attack-scenario identity, so the FPR of a
group-disjoint fold is largely decided by which attack scenarios it happens to
contain.

That is the mechanism behind a result the paper already reports, and it is why a
single-number FPR for this corpus is close to meaningless.

## 6. Status

| Part | Status |
|---|---|
| A — grouping/label alignment against two nulls and an oracle | **complete** |
| B — performance under `src_ip` versus oracle grouping | **not run** |
| C — FPR against fold composition | **complete** |

Part B would close the loop by showing whether the 20.6% alignment translates
into a measurable performance difference. Part A's answer makes the prediction:
it should not be large, because `src_ip` groups are only weakly attack-aligned.
Until it runs, that remains a prediction and is labelled as one.

## 7. Artefacts

```
results/EXP-029/processed/grouping_alignment.csv
results/EXP-029/processed/fpr_vs_fold_composition.csv
results/EXP-029/statistics/provenance.json
```
