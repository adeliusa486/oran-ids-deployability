# EXP-038 — Final reviewer attack (v2)

**Date:** 2026-09-20
**Phase:** 38
**Supersedes:** `reports/final_reviewer_attack.md`, which attacked the previous
campaign and is kept unedited.

Four reviewers, each attacking what the repository now contains. The rule from
the brief is followed: every serious criticism gets an experiment, a fix, a new
baseline, a weakened claim or a withdrawn claim. Defensive prose does not count
as a response, and where the honest response is "you are right and we cannot fix
it", that is written down.

---

## Reviewer A — machine learning and security

### A1. "Your headline is someone else's result."

**Sustained.** Abraheem & Edhirig (WAUJPAS, 7 Aug 2026) run bidirectional
transfer between 5G-NIDD and NetsLab-5GORAN-IDD — the same two corpora, the same
two directions, 15 harmonised features to our 15 concepts — six weeks before this
campaign.

*Response:* the novelty claim is **removed**, not softened. The paper is
repositioned as replication-plus-extension and cites them as prior art at first
mention. What is genuinely additional is stated narrowly: eight architectures
against their one, trivial floors evaluated on the target, and a group-disjoint
source reference so the gap is not inflated by the split artefact we separately
measure. See `reports/literature_audit_v2.md` §3.

### A2. "A macro-F1 of 0.53 on the target could mean anything."

**Sustained, and this drove a design change.** It is why the trivial floors are
evaluated **on the target** rather than only on the source. A coin flip scores
0.4240 on `D_B`. The best architecture clears it by 0.148 and the MLP falls
0.0017 *below* it, with balanced accuracy 0.4966.

*Response:* the floor is in the table, in the figure as a drawn line, and in the
first sentence of the result. It is not a robustness check, it is the unit.

### A3. "Your transfer gap is mostly the exporter difference."

**Partially sustained, and it is the dominant threat.** The A3 single-exporter
control is not applied: `D_A` is Zeek, `D_B` is Argus. We cannot separate
deployment shift from tooling shift.

*Response:* every `Delta_F1` is labelled an **upper bound** spanning both, in the
abstract, the results and the limitations, and the phrase "due to deployment
shift" appears nowhere. We additionally cite Abraheem & Edhirig's
dataset-fingerprint measurement — a source classifier reaching **0.993** balanced
accuracy on the shared features, surviving CORAL and Top-6 filtering — which
quantifies the confound rather than leaving it qualitative. **We cannot remove
it. It would need re-extracting both corpora from raw captures with one exporter,
which D-010 stopped for good reasons.**

### A4. "You tuned nothing. Your models are weak."

**Partially sustained.** No hyperparameter search was run; every architecture
gets the same fixed configuration and the same class-weighting policy.

*Response:* this is deliberate and stated (R7): under-tuning the deep models
would inflate the transfer gap, which is the first thing a reviewer attacks. The
uniform-treatment policy is the defence, and the trivial floors bound how much
tuning could matter. **But the criticism lands on one point and we concede it:**
the MLP's below-chance transfer might partly reflect its configuration rather
than the architecture family, and we say so rather than claiming a general result
about neural detectors.

### A5. "Why is there no deep sequence model?"

**Sustained as a gap, rejected as a flaw.** The draft's `tab:cross` reported a
1D-CNN and an LSTM. Neither was ever run.

*Response:* the fabricated rows are **deleted**. We did not run them, we say we
did not run them, and we do not substitute invented numbers. Adding them is
future work.

---

## Reviewer B — O-RAN systems

### B1. "There is no RIC in this paper."

**Sustained.** Track C was never executed.

*Response:* reported **BLOCKED** with a command-verified cause — the Windows
Virtual Machine Platform feature is absent, so WSL2 cannot start a VM and
Docker's Linux engine cannot run (`reports/EXP-031_real_ric_blocked.md`). Every
latency figure is labelled **EMULATED**. No conformance claim is made anywhere.

### B2. "Your latency numbers are three orders of magnitude off."

**Sustained, and we now report it against ourselves.** Obiuwevwi et al. (2026)
measure 1–5 µs for logistic regression inside a real OAI+FlexRIC RIC. We report
2.45 ms p50 for the same family.

*Response:* rather than bury this, it becomes the finding. The near-RT crossing
point is a property of the **implementation**, not the architecture: a compiled
embedded model against a Python object graph. Any architecture recommendation
made on prototype latency describes its own toolchain. Our own C9 ("only XGBoost
meets p99") is now contradicted twice, by our measurement and by theirs.

### B3. "A flow-level IDS is not an xApp."

**Sustained.** We measure detectors, not a deployed xApp, and the E2 message
path, serialisation and subscription handling are absent from our latency
decomposition entirely.

*Response:* conceded in Limitations. EXP-030 sharpens why it matters: if deployed
inference is microseconds, then extraction and transport are the whole budget and
our decomposition is missing the larger part of it.

### B4. "`src_ip` grouping in a testbed is attack grouping."

**Sustained, and it is under investigation.** In a testbed each attack scenario
is typically launched from a dedicated host, so a host-disjoint split may be an
attack-disjoint split, which is a different and much harder task.

*Response:* EXP-029 measures it instead of caveating it. Part C is complete and
already produced a result we did not expect: test-fold composition explains
almost none of the FPR variance (mean R² 0.04–0.06, max 0.36). Parts A and B —
the alignment measurement against two nulls, and `src_ip` grouping against an
oracle grouping by attack type — were still running at the time of writing and
are reported when they land. **Until then the network layer stays a
cross-check, per D-013, and no per-layer claim rests on it.**

---

## Reviewer C — statistics and methodology

### C1. "Your PPV spread is an averaging artefact."

**Sustained — and we found it ourselves, before this review.** See D-018 / B-E.
PPV is violently non-linear in FPR near zero; EXP-004 averaged PPV across folds;
any fold with FPR = 0 contributed 1.000. XGBoost drew six such folds of forty and
the MLP none, and the published ranking is nearly that count.

*Response:* the "6x" clause is **withdrawn**. Pooled counts are primary
throughout. Mean and median are reported beside the pooled value so the artefact
stays visible instead of being quietly corrected, and the correction has its own
figure. The surviving claim is stronger: corpus precision 0.93 against pooled PPV
0.0055–0.0077, a **132x** gap, with the detectors indistinguishable at every base
rate from 1e-4 to 0.5.

### C2. "n = 20 seeds on 30 sessions is not 20 independent observations."

**Sustained.** Twenty split seeds over thirty capture sessions resample the same
small population. The effective sample size is closer to the number of sessions.

*Response:* conceded in Limitations. It is also why intervals are paired
t-intervals over split means rather than bootstraps (D-012), why the bootstrap
helper warns below n = 30, and why EXP-034's docstring states up front that 30
sessions detects a large effect and nothing subtler. **We cannot fix this with
more seeds — it needs more sessions.**

### C3. "Your source reference is unstable, so the transfer gap is unstable."

**Sustained.** Fold FPR ranges 0.000 to 0.890, and several seeds produce a source
score *below* the target score.

*Response:* stated as threat 4 in the EXP-026 report and visible in the CIs,
which are wide. It is also, in itself, one of our results: a single-number FPR
for this corpus is close to meaningless without that range beside it.

### C4. "Part of your transfer gap is prior shift, not concept shift."

**Sustained, and it now has an experiment.** `D_A` is 94.63% attack and `D_B`
60.71%; a model thresholded at 0.5 under one prior is not calibrated for the
other.

*Response:* EXP-028 tests exactly this, with an **oracle** prior-corrected
variant that consumes the target prior and is labelled non-deployable. Early
results say calibration does **not** rescue the operating point and
source-fitted calibration makes it worse, because the calibrator encodes the
source's 94.6% prior. That is reported as a negative result, not omitted.

### C5. "Three of your figures come from the same twenty seeds."

**Noted, not sustained as an error.** Reusing one set of fits across analyses is
correct — refitting per figure would introduce differences that are not findings.
The dependence matters only for joint claims, and none are made.

---

## Reviewer D — reproducibility

### D1. "Your test suite does not run."

**Sustained. This was real and it was embarrassing.** `pytest` from a clean
checkout failed at collection: the package lives under `src/` and is not
installed, and the suite only ever passed because `final_validation.py` injects
`PYTHONPATH=src` when it shells out.

*Response:* **fixed.** A root `conftest.py` puts `src/` on `sys.path` for every
entry point. A bare `pytest` now passes 50 tests. Recorded rather than quietly
patched, because the failure mode — a guard that works only through one wrapper
— is the interesting part.

### D2. "Your paper's methods section describes a data leak."

**Sustained, and this was the worst finding of the audit.** The manuscript said
features are "quantile-normalised per corpus", which fits a transform on the
target and is precisely what A2 forbids.

*Response:* **fixed.** The section now describes the source-fitted transform the
code actually applies. The `\syn{}` markers never covered this: they mark
fabricated numbers, not fabricated methods, which is why `EXP-037` audits prose
separately.

### D3. "Your feature count is wrong."

**Sustained.** The paper claimed 24 shared features in four families, including a
Timing family of seven with a measured covariate shift — on a target corpus that
publishes no inter-arrival statistics at all.

*Response:* **fixed.** 15 concepts / 18 columns, generated from a committed
specification, with a validation check asserting the code and the spec agree.

### D4. "Can I get your target corpus?"

**Yes.** Open, CC BY 4.0, from the Finnish national research repository with its
own DOI, not the paywalled IEEE DataPort copy and not an unattributable mirror.
All four artefacts hashed and re-verified.

### D5. "How do I know you did not peek at the target?"

**You can check.** Every read of `D_B` appends to
`results/EXP-026/logs/target_access.log` with a timestamp and a stated reason,
and the validation harness fails if the corpus is present without a log. The
shared space was committed and unit-tested before any target metric existed.

*Honest limitation:* the log records that accesses happened, not that no decision
followed from one. D-017 documents the single relaxation made and why the reverse
direction is stored separately so it can be deleted without touching the primary
result.

---

## What changed because of this attack

| Finding | Action |
|---|---|
| A1 | Novelty claim removed; repositioned as replication-plus-extension |
| A3 | Upper-bound language enforced; external fingerprint measurement cited |
| A4 | MLP's below-chance transfer explicitly not generalised to neural detectors |
| A5 | Fabricated CNN/LSTM rows deleted |
| B1, B2 | Track C BLOCKED; Finding 4 rewritten around implementation |
| B4 | EXP-029 run; network layer stays a cross-check until it lands |
| C1 | "6x" withdrawn; pooled estimator primary; artefact given its own figure |
| C2, C3 | Conceded in Limitations; cannot be fixed with more seeds |
| C4 | EXP-028 run, with a labelled oracle |
| D1 | `conftest.py`; bare `pytest` passes 50 tests |
| D2, D3 | Methodology section rewritten; feature count corrected and guarded |

## What we could not answer

Stated plainly, because a reviewer will find these anyway:

1. **The exporter confound cannot be removed** without re-extracting both corpora
   from raw captures with one exporter. This bounds every transfer number.
2. **No real RIC measurement exists**, and this machine cannot produce one.
3. **Thirty capture sessions is a small population**, and no amount of reseeding
   changes that.
4. **`ddos`, `bruteforce` and `web` are untestable in transfer**, because `D_B`
   does not contain them.
5. **CPU and RAM under load are not measured at all.**
