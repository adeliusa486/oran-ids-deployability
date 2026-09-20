# Execution Plan: *Intrusion Detection for IoT Traffic in O-RAN Edge Data Centres*

**From empty repository to reproducible, reviewer-resistant results.**

---

> **Status of the source paper.** The manuscript is structurally complete and every
> numeric value in it is a synthetic placeholder. This document is the plan for
> replacing those placeholders with measurements. **Nothing in this plan reports a
> result.** Where a number appears, it is either (a) a configuration value you will
> set, (b) a resource estimate, or (c) an explicitly labelled *expected behaviour* —
> a directional prediction that the experiment is designed to be capable of
> falsifying. If an experiment cannot come out the other way, it is not an
> experiment and it is marked as such.

---

# 1. Executive Implementation Strategy

## 1.1 The single most important structural fact

**This is a measurement paper, not a method paper.** The contribution is an
evaluation protocol and the finding that detectors fail it. That inverts several
standard implementation instincts and you must internalise it before writing code:

| Method-paper instinct | Correct instinct here |
|---|---|
| Baselines are things we beat | The five architectures are *subjects*, not competitors. None is "ours". |
| Tune the proposed method hard | Tune **all five equally**. Under-tuning inflates your headline gap and is the first thing a reviewer will attack. |
| A bigger gap is a better result | A bigger gap is a bigger *liability* until you have excluded the artefactual explanations. |
| Optimise for the win | Optimise for the **credibility of the measurement**. |

The paper's claim is that a number ($\Delta_{F_1}$) is large. The reviewer's
counter-claim will be that your number is large *because of how you measured it*.
Essentially all engineering effort should go into closing that gap.

## 1.2 Four decoupled tracks

The paper needs four kinds of evidence with almost nothing in common. Building
them as one pipeline is the most common way projects like this stall — a broken
RIC deployment must not block offline transfer results.

```
TRACK A — Offline transfer            Python only. Cheap. No special hardware.
  └─ E1 transfer, E2 ablation, E3 calibration, E7 adaptation
       ↓ (exports trained model artefacts)
TRACK B — Operational analysis        Pure post-processing of Track A outputs.
  └─ E4 alert burden, E8 base-rate sensitivity
TRACK C — Runtime on a real RIC       Hard. Separate hardware, separate skills.
  └─ E5 latency, E6 scalability
TRACK D — Systematic survey           Human-in-the-loop. Runs in parallel, no code deps.
  └─ E9 reporting-practice review
```

**Track A is on the critical path. Track C is the schedule risk. Track D can start
today and requires no infrastructure.** Start D on day 1 in parallel; it is pure
calendar time and it currently has zero evidence behind it.

Track C has a defined fallback (§7.6) that preserves a publishable latency claim
if RIC deployment proves infeasible. Decide the fallback *before* you sink four
weeks into srsRAN.

## 1.3 Critical-path summary

```
P0 Audit ─→ P1 Spec ─→ [BLOCKING GATE: does D_A exist?] ─→ P3 Env ─→ P4 Repo
                                    │
                                    ├─ P6 Data ─→ P7/P9 Tests ─→ P10 Pilot
                                    │                                 │
                                    │              ┌──────────────────┴──────┐
                                    │              ↓                         ↓
                                    │         Track A/B full            Track C full
                                    │              └──────────┬──────────────┘
                                    │                         ↓
                                    └────────────→ P14 Validate ─→ P15 Stats
                                                                      ↓
                                                          P18 Auto figures/tables
                                                                      ↓
                                                    P20 Consistency ─→ P21 Reviewer audit
```

## 1.4 The mechanism that makes the paper honest

Every number in the manuscript must arrive there by `\input{}` from a generated
file. Not by copy-paste. This is stated once here because it is the whole point:

```
results/raw/*.parquet → analysis/ → tables/generated/*.tex → \input into main.tex
```

Given that the current manuscript is entirely placeholders, a hand-copied number
is indistinguishable from a leftover placeholder. The generation pipeline is what
makes that distinction structural rather than a matter of your memory. Build it
early (Phase 18 machinery in Phase 4), not at the end.

---

# 2. Paper Understanding and Contribution Map

## 2.1 Extraction

**(1) Research problem.** Detection xApps on the near-RT RIC are proposed for IoT
threat detection in O-RAN edge data centres, but published evaluations report only
in-distribution accuracy, which does not establish deployability.

**(2) Research gap.** No published work reports cross-deployment generalisation,
operational alert burden, and near-real-time latency conformance together for the
same artefact.

**(3) Research questions.**
- RQ1: How much detection performance is lost when a detector trained on one
  O-RAN deployment is applied to an independently collected one?
- RQ2: What alert volume and operational precision result at realistic attack
  base rates?
- RQ3: Does a detection xApp meet the near-RT control budget at the tail, under
  load, on a real RIC?
- RQ4 *(implicit, and currently unevidenced)*: How commonly does existing work
  report these three properties?

**(4) Hypotheses.**
- H1: $\Delta_{F_1} > 0$ and is large relative to seed variance.
- H2: At realistic $\pi$, PPV at $\tau=0.5$ is low enough to be operationally
  unusable.
- H3: $q_{0.99}(L)$ exceeds $B=10$ ms for at least some architectures that pass on
  median latency.
- H4 *(added in revision, and the sharpest testable claim)*: the feature families
  that most increase in-distribution $F_1$ **decrease** cross-deployment $F_1$ —
  a sign-flip, not just a weak correlation.

**(5) Contributions.** Three-criterion protocol + deployability predicate Eq. (7);
cross-deployment quantification across five architectures; feature-family ablation
showing the accuracy/transfer tension; runtime measurement on a real RIC;
a reporting checklist.

**(6–9) Methodology / architecture / algorithms / I/O.** Train on $\mathcal{D}_A$,
evaluate on $\mathcal{D}_B$ over a 24-feature shared space; package as an xApp;
measure latency under offered load. Algorithm 1 is the budget-aware inference loop.
Input: E2SM-KPM indications + packet features. Output: binary decision + optional
E2SM-RC control action.

**(10) Data.** $\mathcal{D}_A$ = "an O-RAN testbed capture with synchronised packet
traces and radio KPIs". $\mathcal{D}_B$ = 5G-NIDD.
**$\mathcal{D}_A$ is not a named, obtainable artefact. See A1 — this is the project's
gating risk.**

**(11) Simulation environment.** Not a simulation in the discrete-event sense.
Track A is offline ML. Track C is a *real* softwarised deployment (srsRAN +
FlexRIC/OSC RIC) with a synthetic load generator. Do not build a network simulator;
the paper does not claim one and one would weaken the latency claim.

**(12–15) Variables.**

| Type | Variables |
|---|---|
| Independent | corpus pair & direction; architecture (5); feature-family subset (6); decision threshold $\tau$; offered load (5 levels); base rate $\pi$; target-label budget (adaptation) |
| Dependent | Acc/P/R/$F_1$; ECE; alerts·h⁻¹; PPV; $L$ at p50/p95/p99; $T_{\max}$; vCPU; RSS; mJ·decision⁻¹ |
| Control | feature extractor & version; window size (16); split protocol; class weighting; hardware & kernel isolation; container limits; package versions; $\lambda_b$ |

**(16) Baselines.** RF, XGBoost, MLP, 1D-CNN, LSTM — subjects, not competitors.
§11 argues for three *additions* the current set is missing.

**(17) Metrics.** Above, plus $\bar W_1$ (Eq. 2) and $\Delta_{F_1}$ (Eq. 1).

**(18) Scenarios.** In-distribution; A→B transfer; B→A reverse transfer; ablation;
threshold sweep; base-rate sweep; load sweep; few-shot adaptation.

**(19) Expected results.** See §6.7 — labelled as predictions with falsification
conditions, never as findings.

**(20–21) Figures/tables.** 7 figures, 8 tables. Full plan in §16–17.

**(22) Claims.** Enumerated with evidence status in §20.

**(23) Sustainability claims.** *The paper makes essentially none.* There is one
energy measurement (mJ·decision⁻¹, Table VII) and a derived annual-kWh remark.
That is a resource-efficiency observation, not a sustainability contribution. **Do
not inflate it into one** — an unearned sustainability framing is a reviewer
liability, and the measurement stands perfectly well as a deployment cost. The only
requirement is that RAPL attribution be done correctly (A8).

**(24) Resilience claims.** *None in the system-resilience sense.* The closest is
the budget-aware early-exit in Algorithm 1 (drop rather than act late), which is a
correctness-under-overload property. It **is** testable and currently untested —
see E5c. Do not frame the paper as a resilience paper.

**(25) Smart-city claims.** *None.* IoT device populations are mentioned as a threat
source. Do not add a smart-city framing; it is not supported and reviewers in this
venue will read it as padding.

**(26) Limitations.** Two corpora only; $\pi$ assumed; single hardware config;
binary detection only; no adaptive adversary; $\pi$ unknown for the prior correction.

**(27) Threats to validity.** §21.

**(28) Reproducibility requirements.** §19.

## 2.2 Claim → evidence dependency map

| # | Claim (paper) | Experiment | Metric | Data | Figure/Table | Status |
|---|---|---|---|---|---|---|
| C1 | All architectures score >98 % in-distribution | E1a | Acc/P/R/$F_1$ | $\mathcal{D}_A$ test | T-IV | Planned |
| C2 | Every model loses 27–37 pts $F_1$ under transfer | E1b | $\Delta_{F_1}$ | $\mathcal{D}_A$→$\mathcal{D}_B$ | T-V, F-3 | Planned |
| C3 | Degradation is not an artefact of one corpus | E1c | $\Delta_{F_1}$ reverse | $\mathcal{D}_B$→$\mathcal{D}_A$ | text | Planned |
| C4 | Errors are FN-dominated under transfer | E1b | confusion matrix | $\mathcal{D}_B$ | F-4 | Planned |
| C5 | Radio KPIs help in-distribution, hurt transfer | E2 | $F_1$ both settings | both | T-VI, F-5 | Planned |
| C6 | Models are miscalibrated under transfer | E3 | ECE, reliability | both | F-6 | Planned |
| C7 | Prior correction reduces ECE, not $F_1$ | E3b | ECE pre/post | both | text | Planned |
| C8 | Default threshold yields unusable PPV | E4 | alerts·h⁻¹, PPV | benign trace | F-7 | Planned |
| C9 | Only XGBoost meets the p99 budget | E5 | $q_{0.99}(L)$ | live RIC | T-VII, F-8 | Planned |
| C10 | Feature extraction dominates latency | E5b | $t_{\text{feat}}/L$ | live RIC | T-VII | Planned |
| C11 | $T_{\max}$ differs by an order of magnitude | E6 | $T_{\max}$ | live RIC | T-VII, F-8 | **Under-specified — see A7** |
| C12 | Few-shot adaptation partially recovers $F_1$ | E7 | $F_1$ vs budget | $\mathcal{D}_B$ | text | Planned |
| C13 | Existing work under-reports these criteria | E9 | counts | literature | T-VIII | **No evidence exists** |
| C14 | $\mathcal{P}(f_\theta)=0$ for all five | derived | Eq. (7) | E1+E4+E5 | text | Derived |
| C15 | Energy differs ~13× across architectures | E5d | mJ·dec⁻¹ | live RIC | T-VII | **Measurement method unsound — A8** |

**Three claims (C11, C13, C15) currently have no valid path to evidence.** Fix
before they reach a reviewer.

---

# 3. Current Weaknesses and Ambiguities

Ordered by severity. **A1–A3 are project-threatening.**

---

### A1 — $\mathcal{D}_A$ does not exist as a citable artefact 🔴 BLOCKER

**What the paper says.** "An O-RAN testbed capture containing packet traces
synchronised with per-user radio KPIs exported over E2SM-KPM, collected on an
OpenRAN Gym style softwarised deployment."

**Problem.** That describes a dataset; it does not identify one. The citations
point at *platform* papers (OpenRAN Gym, SCOPE), not at a labelled intrusion-
detection corpus with attack ground truth. No public corpus known to me combines
(i) packet-level traces, (ii) synchronised E2SM-KPM radio KPIs, and (iii) labelled
IoT attack traffic. The entire radio-KPI ablation (C5, the paper's most interesting
finding) depends on this.

**This is a gate, not a task.** Do not write feature code before resolving it.

**Options, in preference order:**

| Option | Cost | Consequence |
|---|---|---|
| **A1-a** Collect it on Colosseum / OpenRAN Gym / X5G | 4–10 weeks + testbed access | Best paper. Enables C5 fully. Dataset is itself a contribution. |
| **A1-b** Find an existing corpus with radio KPIs | 1 week search | If one exists, cheapest good outcome. Search first regardless. |
| **A1-c** Use two packet-only corpora (e.g. 5G-NIDD ↔ CICIoT2023 / TON_IoT) | 1 week | **Kills C5.** Paper loses its sharpest finding but RQ1–RQ3 survive. |
| **A1-d** Synthesise radio KPIs | — | **Do not.** Fabricates the exact quantity the ablation measures. |

**Recommendation.** Attempt A1-b for one week (bounded). If it fails, decide A1-a
vs A1-c on testbed access. If A1-c, **rewrite Section VI-C and drop C5** rather
than weakening it — a packet-only version of this paper is still publishable.

---

### A2 — Per-corpus quantile normalisation leaks target information 🔴

**What the paper says.** Features are "quantile-normalised per corpus to remove
trivially deployment-specific scaling."

**Problem.** Normalising $\mathcal{D}_B$ using $\mathcal{D}_B$'s own quantiles uses
the target distribution at test time. That is **transductive**, and it is exactly
the setting the paper claims *not* to be in ("$\mathcal{D}_B$ is consumed only once,
at final evaluation"). Two contradictory things are stated. A reviewer who notices
will question the whole protocol.

It also cuts against the finding: per-corpus normalisation should *reduce* the
measured gap, so the reported degradation is if anything a lower bound — but you
cannot make that argument without having measured both.

**Resolution.** Implement three normalisation modes as a first-class config axis
and report all three:

| Mode | Fit on | Interpretation |
|---|---|---|
| `source` | $\mathcal{D}_A$ train only | **Primary.** Honest zero-knowledge deployment. |
| `target_unsup` | $\mathcal{D}_B$ unlabelled | Transductive; what the paper currently describes. Report as a *mitigation*. |
| `none` | raw | Upper bound on scale sensitivity. |

Make `source` the headline. Reporting the spread across all three is a strength,
not a hedge — it pre-empts the criticism.

---

### A3 — The extractor confound will be the reviewer's first attack 🔴

**Problem.** If $\mathcal{D}_A$ features come from your exporter and
$\mathcal{D}_B$ features come from 5G-NIDD's published Argus CSVs, then
$\Delta_{F_1}$ conflates:

1. genuine deployment distribution shift (what you claim to measure), with
2. differences in flow timeout, direction inference, field semantics, and
   rounding between two flow exporters (an artefact).

These are not separable post hoc. A hostile reviewer states this in one sentence
and the headline result is gone.

**Resolution — non-negotiable.** Recompute features for **both** corpora from raw
packet captures using **one** exporter at **one** pinned version, with identical
timeout and direction-inference settings. 5G-NIDD publishes `pcapng`, so this is
feasible. Never mix a published CSV with a self-computed one.

**Verification (T-A3).** Recompute 5G-NIDD features with your pipeline, compare
against the published CSVs on the same flows, and report per-feature correlation.
Low correlation on a feature is not a bug to hide — it is direct evidence that the
confound is real and that you controlled for it. Put this in an appendix.

---

### A4 — Device-disjoint splitting is not defined for $\mathcal{D}_B$ 🟠

Paper says $\mathcal{D}_A$ splits are "disjoint by device identifier". 5G-NIDD does
not expose a stable device ID in the same form. Since $\mathcal{D}_B$ is never
trained on, this does not invalidate anything — but the grouping key must be
defined per corpus and recorded in the split manifest, or the protocol is not
reproducible. **Fix:** declare the grouping key in each corpus config
(`group_key: ue_imsi` / `group_key: src_ip`), assert it exists at load.

---

### A5 — Five seeds measure the wrong variance 🟠

Paper reports "five random seeds" and the revision derives CIs from them. But for
XGBoost and RF on a *fixed* split, the seed perturbs only subsampling — variance is
tiny and the CI is correspondingly narrow. It does not capture the dominant
uncertainty, which is **which devices landed in which split**.

**Consequence.** Your CIs will be too tight, and a statistician reviewer will say
so. This matters because the revision now leans on CIs to argue the architectures
are indistinguishable.

**Fix.** Two-level design: 5 outer split repetitions (`split_seed`) × 3 inner model
seeds (`model_seed`) = 15 runs per cell. Report the CI over *split* means. Cost is
3× on the cheapest track; accept it.

---

### A6 — $\pi = 0.002$ and $\lambda_b = 240{,}000$ h⁻¹ are unsourced 🟠

Neither is measurable from these corpora. $\pi$ is a modelling assumption; $\lambda_b$
is a deployment parameter.
**Fix.** Never report a single PPV. Report PPV as a surface over
$\pi \in [10^{-4}, 10^{-1}]$ (E8), state $\lambda_b$ as a declared parameter with
its derivation, and give alerts·h⁻¹ *per 10⁵ benign flows* so the number is
portable to any deployment. This converts two weaknesses into a sensitivity result.

---

### A7 — $T_{\max} < 250$ is not a measurement 🟠

Table VII reports "$<250$" for CNN and LSTM because 250 dec·s⁻¹ was the lowest load
tested. That is an unbounded statement dressed as a bound.
**Fix.** Extend the load sweep down (32, 64, 125) and add a bisection search for the
crossing point. Report $T_{\max}$ with a bracketing interval, or state "below the
lowest tested load of 32 dec·s⁻¹".

---

### A8 — RAPL cannot attribute energy to a container 🟠

RAPL reports package/DRAM energy for the whole socket. With co-tenants and
background load, subtracting nothing gives an energy figure that is mostly
*idle platform*, not the xApp.
**Fix.** (i) Measure idle baseline over ≥300 s immediately before and after each
run; (ii) report $\Delta$energy above baseline attributed over decisions;
(iii) pin the xApp to isolated cores so the delta is attributable; (iv) report the
baseline and its drift alongside the result. If drift exceeds the signal, **drop the
energy column** — it is one row of one table, not worth an indefensible claim.

---

### A9 — Table VIII has no underlying study 🟠

The revision added a protocol; nobody has executed it. Until then the table is
placeholder counts with a methods paragraph attached, which is *worse* than no
table because it looks evidenced.
**Fix.** Run Track D (§6.9) or delete the table and soften the claim to a
qualitative observation with a handful of concrete cited examples.

---

### A10 — Single hardware configuration 🟡

Acknowledged in Limitations. Cheap partial fix: repeat E5 on one second machine
class. Two points do not characterise a space but they distinguish "our numbers" from
"a property of this CPU". Worth one day.

---

### A11 — "$\mathcal{D}_A$ never influences $\mathcal{D}_B$" needs enforcement, not assertion 🟡

The claim that $\mathcal{D}_B$ is consumed once is a *process* claim. Enforce it in
code: a `TargetCorpusGuard` that refuses to load $\mathcal{D}_B$ labels outside a
run tagged `final_eval`, and logs every access. Then the claim is auditable.

---

### A12 — Window of 16 flow records is under-defined 🟡

What happens with fewer than 16 records per device? Left-pad, drop, or partial-window
statistics? Each changes the short-flow population, which is where scanning traffic
lives. **Fix:** declare `min_records: 16, short_flow_policy: drop` in config, report
the fraction dropped per corpus (this is itself a distribution-shift signal).

---

# 4. Recommended Improvements

Only changes justified by the paper's own claims. The core idea is untouched.

| ID | Improvement | Why | Changes core idea? |
|---|---|---|---|
| I1 | One exporter, both corpora, from pcap (A3) | Without it the headline number is confounded | No — makes the existing claim valid |
| I2 | `source` normalisation as primary, 3 modes reported (A2) | Removes a self-contradiction | No |
| I3 | Split × model seed nesting (A5) | CIs currently measure the wrong thing | No |
| I4 | $\pi$ and $\lambda_b$ as swept surfaces (A6) | Converts assumptions into results | No — strengthens |
| I5 | Add 3 baselines: majority-class, single decision tree, isolation forest | Establishes the floor. Currently nothing shows the task is non-trivial or that supervision is needed | No — additive |
| I6 | Test the Algorithm 1 early-exit path (E5c) | Currently specified but unmeasured | No |
| I7 | Report ECE with bootstrap CIs | ECE is bin-sensitive and unstable | No |
| I8 | Second hardware class for E5 (A10) | Distinguishes finding from artefact | No |
| I9 | Drop energy column unless A8 resolved | Indefensible claim for marginal value | Minor deletion |
| I10 | Execute or delete Table VIII (A9) | Fabricated-looking evidence | Deletion is acceptable |

**I5 deserves emphasis.** The paper currently shows five sophisticated models all
failing. A reviewer will ask: *what does a majority-class classifier get?* On
$\mathcal{D}_B$ (60.7 % attack prevalence) the majority baseline achieves ~60.7 %
accuracy by construction. If your transferred models land near that, the honest
framing is "transfer performance approaches trivial-baseline performance", which is
a **stronger and more defensible statement** than the current one. You cannot make
it without the baseline. Add it.


---

# 5. Complete Phase-by-Phase Roadmap

Every phase carries hard exit criteria. **Do not proceed past a red gate.**

---

## PHASE 0 — Paper Audit

**Objective.** Establish what must be built, what is ambiguous, and what is
unresolvable, before any code exists.
**Inputs.** `main.tex`, `references.bib`.
**Tasks.** Complete the audit table below; resolve A1 by decision, not by hope.

### Audit table

| Paper component | What paper says | Implementation requirement | Problem / ambiguity | Recommended resolution |
|---|---|---|---|---|
| $\mathcal{D}_A$ | O-RAN testbed capture, packets + radio KPIs | Labelled corpus with attack ground truth and synchronised KPM | **Does not exist as citable artefact** | A1 decision gate; prefer collect, else drop C5 |
| $\mathcal{D}_B$ | 5G-NIDD | Public, obtainable | None — verified DOI | Use published pcapng, not published CSV (A3) |
| Feature space | 32 features, 4 families, 24 shared | Single extractor, both corpora | Extractor confound | I1: one exporter from pcap |
| Normalisation | "quantile-normalised per corpus" | Fit-on-source transform | Target leakage (A2) | I2: three modes, `source` primary |
| Windowing | 16 flow records per device | Sliding window builder | Short-flow policy undefined (A12) | Declare + report drop rate |
| Splits | 70/10/20, device-disjoint | Grouped stratified split | Grouping key undefined for $\mathcal{D}_B$ (A4) | Per-corpus `group_key` |
| Seeds | "five random seeds" | Repetition harness | Measures wrong variance (A5) | I3: 5 split × 3 model |
| Models | RF, XGB, MLP, CNN, LSTM | Uniform train/eval interface | No trivial baseline (I5) | Add majority / tree / iForest |
| Eq. (1) $\Delta_{F_1}$ | gap definition | Straightforward | None | — |
| Eq. (2) $\bar W_1$ | mean Wasserstein over features | Per-feature $W_1$ after normalisation | Depends on normalisation mode | Report per mode |
| Eq. (3) alerts | $\lambda_b\,\mathrm{FPR}(\tau)$ | Post-processing | $\lambda_b$ unsourced (A6) | Declare + normalise per 10⁵ flows |
| Eq. (4) PPV | base-rate formula | Post-processing | $\pi$ assumed (A6) | I4: sweep |
| Eq. (5) $L$ | latency decomposition | In-process instrumentation | $t_q$ hard to separate | Instrument each stage; derive $t_q$ by residual |
| Eq. (6) budget | $q_{0.99}\le B$ | Percentile over full sample | Needs ≥10⁶ samples for stable p99 | Enforce in harness |
| Eq. (7) predicate | conjunctive deployability | Derived | None | — |
| Eq. (8) $\tau^\star$ | constrained argmax | Grid search over $\tau$ | None | — |
| Eq. (9) prior corr. | Saerens-style rescaling | Post-processing | Requires known $\pi$ (stated in Limitations) | Sweep |
| Alg. 1 | budget-aware early exit | xApp inference loop | Drop path untested (I6) | E5c |
| Table VII energy | mJ per decision | RAPL | Attribution invalid (A8) | Fix or drop |
| Table VIII | 41-paper survey | Systematic review | Not executed (A9) | Track D or delete |
| §VIII repro | artefact list | Actual artefacts | Currently aspirational | Phase 19 |

**Exit criteria (RED GATE).**
- [ ] A1 resolved by written decision, with the consequence for C5 recorded.
- [ ] A2, A3 resolutions accepted.
- [ ] Every row above has an owner and a resolution.

**Failure conditions.** Proceeding without an A1 decision. Deciding A1-d.

---

## PHASE 1 — Research Specification

**Objective.** Turn the paper into a machine-checkable spec.
**Files.** `docs/SPEC.md`, `docs/claims.yaml`.

`docs/claims.yaml` is the backbone of Phases 18/20 — it binds each claim to the
artefact that will evidence it:

```yaml
claims:
  C2:
    text: "Every architecture loses 27-37 points of F1 under transfer"
    hypothesis: H1
    experiment: E1b
    metric: delta_f1
    artefact: tables/generated/cross_deployment.tex
    figure: figures/generated/fig_gen.pdf
    falsified_if: "CI on delta_f1 includes 0 for any architecture"
    status: planned
  C5:
    text: "Radio KPIs raise in-distribution F1 and lower cross-deployment F1"
    hypothesis: H4
    experiment: E2
    metric: [f1_indist, f1_cross]
    artefact: tables/generated/ablation.tex
    falsified_if: "sign of the two deltas is the same"
    status: blocked_on: A1
```

**Verification.** `python -m oran_ids.audit.claims --check-schema` passes; every
claim has a `falsified_if`.
**Exit criteria.** No claim lacks an experiment. No experiment lacks a claim.

---

## PHASE 2 — Experimental Design Improvement

**Objective.** Fix the design before it costs compute. Detailed in §6.
**Exit criteria.** Runs-per-cell, seed scheme, load levels, and sweep ranges frozen
in `configs/`. Power justification recorded (§15.1).

---

## PHASE 3 — Environment Setup

**Objective.** Two reproducible environments — offline and runtime — because Track A
and Track C share almost no dependencies.

**Files.** `pyproject.toml`, `environment.yml`, `Dockerfile.offline`,
`Dockerfile.xapp`, `scripts/smoke_test.sh`.

**Offline (Track A/B).** Python 3.11; numpy, pandas, pyarrow, scikit-learn,
xgboost, torch (CPU wheel is sufficient — see §14), scipy, statsmodels, pyyaml,
matplotlib, pytest, hypothesis. Pin **exact** versions; `pip freeze > requirements.lock`.

**Runtime (Track C).** Ubuntu 22.04; srsRAN Project; FlexRIC or OSC RIC (H release);
Docker ≥24; ONNX Runtime; `psutil`; `perf`/RAPL access. Kernel boot parameters
`isolcpus=`, `nohz_full=`, `rcu_nocbs=` on the measurement cores — **without CPU
isolation your p99 measures the scheduler, not the model** (see §7.4).

**Commands.**
```bash
conda env create -f environment.yml && conda activate oran-ids
pip install -e ".[dev]"
bash scripts/smoke_test.sh
```

**Smoke test must, in <60 s:** import all modules; build a 500-row synthetic
corpus; extract features; train a depth-2 tree; compute every metric; write and
re-read a parquet; assert bit-identical output across two runs at the same seed.

**Exit criteria.** Smoke test green on a clean clone. `requirements.lock` committed.
Determinism assertion passes.

---

## PHASE 4 — Repository Architecture

Detailed in §9. **Build the `tables/generated/` and `figures/generated/` plumbing
now**, even empty, so no one is ever tempted to paste a number.

**Exit criteria.** Tree exists; `make help` lists targets; pre-commit hooks active;
`.gitignore` excludes `data/raw/`, `results/raw/`, `*.pcapng`.

---

## PHASE 5 — Implementation Architecture

Detailed in §8.
**Exit criteria.** Every module in §8.2 has a signature and a docstring stating
inputs/outputs; import graph is acyclic (`make check-imports`).

---

## PHASE 6 — Data and Scenario Generation

Detailed in §10.
**Exit criteria (RED GATE).**
- [ ] Both corpora processed through the **same** extractor version.
- [ ] T-A3 extractor-agreement report produced.
- [ ] Split manifests written with content hashes.
- [ ] `data/MANIFEST.json` reproduces byte-identically from config+seed.
- [ ] Short-flow drop rate reported per corpus.

---

## PHASE 7 — Runtime Implementation (Track C)

Detailed in §7. **Not a discrete-event simulation.**
**Exit criteria.** xApp registers over E2, receives indications, emits decisions;
no-op control experiment establishes the latency floor.

---

## PHASE 8 — Baselines

Detailed in §11.
**Exit criteria.** All eight subjects share one interface; equal tuning budget
recorded; majority-class baseline present.

---

## PHASE 9 — Tests

Detailed in §12.
**Exit criteria.** `pytest` green; coverage ≥80 % on `src/oran_ids/`; the metric
module has property-based tests against sklearn.

---

## PHASE 10 — Pilot

**Objective.** Exercise the whole pipeline at 1 % scale.

```bash
python -m experiments.run --config configs/experiments/pilot.yaml
```

**Sanity checks (all must pass):**

| Check | Failure meaning |
|---|---|
| No NaN/Inf in any metric | Division by zero in P/R/$F_1$ at degenerate thresholds |
| $0 \le$ all rates $\le 1$ | Metric bug |
| Confusion matrix sums to n | Row/label misalignment |
| Different `split_seed` ⇒ different split hash | Seeds not wired through |
| Same seed ⇒ bit-identical metrics | Uncontrolled nondeterminism (thread count, hash seed) |
| Majority baseline accuracy ≈ class prior | Label mapping inverted |
| In-dist $F_1$ > cross $F_1$ | Corpora swapped |
| $\bar W_1 > 0$ | Normalisation collapsed the distributions |
| Feature count == 24 in transfer runs | Radio features leaked into transfer |

**Exit criteria (RED GATE).** All checks pass twice consecutively. Re-run
reproduces bit-identically.

---

## PHASE 11–13 — Matrix, Budget, Execution

§13, §14. Staged: smoke → pilot → 1 arch × 1 seed → full Track A → Track C.

**Every run records:** config hash, git commit (dirty flag), seeds, timestamps,
package versions, hostname, CPU model, runtime, exit status, output path. Written
as `results/raw/<exp_id>/<run_id>/meta.json` **before** the run starts, updated on
completion — so crashed runs are visible rather than silently absent.

---

## PHASE 14 — Results Validation

Detailed in §18.1. **Fails loudly.**
**Exit criteria.** `make validate` green; run count matches matrix exactly.

---

## PHASE 15–18 — Statistics, Figures, Tables, Automation

§15–18. **Exit criteria.** `make paper` regenerates every figure and table from
`results/` and the PDF builds with zero placeholders (checked by
`scripts/check_no_placeholders.py`, which greps for `\syn{`).

---

## PHASE 19–24 — Reproducibility, Audits, Package

§19–24.

---

# 6. Detailed Experimental Design

## 6.1 Seeds and repetition (resolves A5)

```
split_seed ∈ {101,102,103,104,105}     — regenerates the grouped split
model_seed ∈ {11,22,33}                 — model init / subsampling
```
15 runs per (architecture × configuration) cell. **CIs are computed over the five
split means**, not over all 15 runs — the runs within a split are not independent
samples of the quantity of interest.

## 6.2 Normalisation modes (resolves A2)

`{source, target_unsup, none}` × everything in E1. Primary results use `source`.

## 6.3 Load levels (resolves A7)

`{32, 64, 125, 250, 500, 1000, 2000, 4000}` dec·s⁻¹, plus bisection between the
last passing and first failing level to locate $T_{\max}$ within ±10 %.

## 6.4 Duration, warm-up, sampling

| Parameter | Value | Justification |
|---|---|---|
| Warm-up | 60 s discarded | JIT, page cache, ONNX arena allocation stabilise |
| Measurement | until 10⁶ decisions | p99 with ~10⁴ tail samples; relative SE <2 % |
| Repetitions | 5 runs per load | Captures between-run platform variance |
| Sampling | every decision (no reservoir) | Reservoir sampling biases tails low |

**Not longer.** A 24-hour run does not improve a p99 estimate that has already
converged; it only invites thermal drift. Measure convergence directly: plot p99 vs
sample count and stop when it is flat over the last decade.

## 6.5 Sweeps

- $\tau \in \{0.05, 0.1, \dots, 0.95, 0.99, 0.995\}$
- $\pi \in \{10^{-4}, 3\!\times\!10^{-4}, 10^{-3}, 3\!\times\!10^{-3}, 10^{-2}, 3\!\times\!10^{-2}, 10^{-1}\}$
- adaptation budget $\in \{0, 0.5, 1, 2, 5, 10, 25\}$ % of $\mathcal{D}_B$ labels

## 6.6 What we deliberately do *not* do

- **No 24-hour simulations.** Nothing in the design benefits.
- **No hyperparameter search on $\mathcal{D}_B$.** Would destroy the claim.
- **No GPU inference in Track C.** The paper explicitly assumes tenant xApps get CPU
  only; using a GPU would answer a different question.
- **No architecture search.** Five families is the point; a sixth adds nothing.

## 6.7 Expected behaviour — *predictions, not results*

Each is stated with the observation that would falsify it. If you cannot state the
falsifier, the experiment is decorative.

| Prediction | Falsified if |
|---|---|
| P1: $\Delta_{F_1} > 0$ for all architectures | Any CI on $\Delta_{F_1}$ includes 0 |
| P2: Transfer $F_1$ exceeds majority-class $F_1$ | Transfer ≤ trivial baseline (⇒ reframe as "transfer is no better than trivial") |
| P3: Radio-KPI removal has opposite sign in the two settings (H4) | Both deltas share a sign ⇒ **C5 is withdrawn** |
| P4: ECE rises under transfer | ECE flat or falls ⇒ §VI-C withdrawn |
| P5: $q_{0.99}$ exceeds $q_{0.50}$ by >2× under load | Tail is flat ⇒ the "median is misleading" argument fails |
| P6: $t_{\text{feat}}$ is the largest p50 component for tree models | Inference dominates ⇒ C10 withdrawn |

**P3 is the one to watch.** It is the paper's most interesting and least safe claim.
Treat a same-sign outcome as a finding to report, not a failure to hide.


---

# 7. Runtime Architecture (Track C)

**The paper does not describe a simulation and must not gain one.** Its latency
claim derives its force from being measured on a real RIC. A discrete-event model
would be strictly weaker evidence. What follows is a *measurement harness* around a
real deployment.

## 7.1 Entities

| Entity | Realisation |
|---|---|
| E2 node | srsRAN gNB with FlexRIC E2 agent (or `nr-softmodem`) |
| Near-RT RIC | FlexRIC or OSC RIC (H release) via Helm |
| Detection xApp | Container: E2 client → window store → feature builder → ONNX session → decision → optional E2SM-RC |
| Load generator | Replay harness emitting E2SM-KPM indications at Poisson arrivals |
| Clock | `CLOCK_MONOTONIC_RAW` inside the xApp process |

## 7.2 State and lifecycle

```
Initialize    load config, ONNX session, warm the arena with 1k dummy inferences
Configure     subscribe over E2, pin threads to isolated cores, set container limits
Warm-up       60 s at target load, discarded
Run           until 1e6 decisions; per-decision timestamps at each stage boundary
Inject        (E5c) burst to 3x target for 30 s to force the early-exit path
Collect       append-only binary log, flushed off the critical path
Terminate     drain, close session, write parquet + meta.json
```

**Stage boundaries instrumented** (maps to Eq. 5): `t_recv → t_decoded → t_features
→ t_inferred → t_encoded → t_sent`. $t_q$ is derived as the residual between arrival
timestamp and `t_recv`. Logging must **never** happen on the critical path — write to
a preallocated ring buffer, drain on a separate pinned thread.

## 7.3 Metric extraction

```python
L        = t_sent - t_recv
t_ind    = t_decoded  - t_recv
t_feat   = t_features - t_decoded
t_inf    = t_inferred - t_features
t_act    = t_sent     - t_inferred
```
Percentiles over the full retained sample. Report p50/p95/p99/p999 and max.

## 7.4 Measurement validity — the part that is easy to get wrong

Without these, p99 measures Linux, not the model:

1. **Core isolation.** `isolcpus=`, `nohz_full=`, `rcu_nocbs=` on measurement cores.
2. **Frequency pinning.** `performance` governor; disable turbo; record
   `/proc/cpuinfo` MHz throughout — thermal drift over a long run is a real p99 confound.
3. **Thread pinning.** `taskset` the xApp; set `OMP_NUM_THREADS=1` (ONNX and BLAS
   will otherwise oversubscribe and add tail latency).
4. **No co-tenants** during measurement; verify with `pidstat`.
5. **Floor experiment (mandatory).** Run an xApp whose model is `lambda x: 0.0`.
   Its latency distribution is the platform floor. **Report it.** Every model's
   latency must be interpreted against it, and if the floor's p99 is already near
   10 ms, the entire latency finding is about the platform, not the models.

The floor experiment is the single highest-value item in Track C. Do it first.

## 7.5 Early-exit validation (E5c, resolves I6)

Algorithm 1 drops rather than acting late. Test it: drive 3× target load and assert
(i) drop count > 0, (ii) **no** emitted control action has $L > B - \delta_m$,
(iii) drops are counted and reported. An unexercised branch in a published algorithm
is a reviewer finding.

## 7.6 Track C fallback (decide early)

If RIC deployment is infeasible, degrade in this order — each step is honest but
weaker, and the paper must say which was used:

1. **Full**: real RIC, real E2, real gNB. *(claim: "measured on a real RIC")*
2. **RIC-only**: real RIC + synthetic E2 traffic, no gNB. *(claim: "measured on a
   real near-RT RIC with synthetic E2 load")*
3. **Container-only**: xApp container, E2 encode/decode included, no RIC.
   *(claim: "measured for the xApp inference path, excluding RIC platform overhead")*

**Do not use option 3 while claiming option 1.** Option 3 still supports C10
(feature extraction dominates) and most of C9. It does not support the p99-against-
budget claim as strongly, and §VI-E must be reworded.

---

# 8. Software Architecture

## 8.1 Dependency graph

```
configs/*.yaml
     ↓
config.py ──────────────────────────────┐
     ↓                                  │
ingest/  (pcap → flows, ONE exporter)   │
     ↓                                  │
features/ (families, window, normalise) │
     ↓                                  │
splits/  (grouped, manifested)          │
     ↓                                  │
models/  (8 subjects, one interface) ───┤
     ↓                                  │
calibration/ (ECE, temperature, prior)  │
     ↓                                  │
metrics/  (classification + shift)      │
     ↓                                  │
results/raw/*.parquet ←─────────────────┘
     ↓
operational/ (alerts, PPV, tau*, predicate)      runtime/ (Track C harness)
     ↓                                                    ↓
analysis/ (aggregate, bootstrap, tests) ←─────────────────┘
     ↓
figures/generated/*.pdf   tables/generated/*.tex
     ↓
paper/main.tex  (\input only)
```

## 8.2 Module specifications

### `src/oran_ids/config.py`
Frozen dataclasses mirroring the YAML schema; `load_config(path) -> Config`;
`config_hash(cfg) -> str` (SHA-256 of canonical JSON). Every result is keyed by this
hash. **No module reads YAML directly.**

### `src/oran_ids/ingest/exporter.py`
`extract_flows(pcap: Path, cfg: ExporterConfig) -> pd.DataFrame`.
Single flow exporter for **both** corpora (resolves A3). Config exposes
`active_timeout`, `idle_timeout`, `direction_policy`, `bidirectional`.
Emits `exporter_version` into every output. Unit-tested against a hand-built pcap
with known flow boundaries.

### `src/oran_ids/features/families.py`
```python
FAMILIES = {"volumetric": [...], "timing": [...], "header": [...], "radio": [...]}
def build(flows, families, window, cfg) -> tuple[np.ndarray, list[str]]
```
Asserts the produced column set equals the declared family union — this is what
prevents radio features silently leaking into a transfer run.

### `src/oran_ids/features/normalise.py`
`QuantileNormaliser(mode)` with `fit(source)`/`transform(target)`. Mode `source`
forbids `fit` on the target corpus (raises). Resolves A2 by construction.

### `src/oran_ids/splits/grouped.py`
`make_split(df, group_key, ratios, split_seed, stratify_on) -> SplitManifest`.
Writes `{train,val,test}` index arrays + SHA-256 of each, plus the group key used.
Asserts group disjointness across partitions.

### `src/oran_ids/models/base.py`
```python
class Detector(Protocol):
    def fit(self, X, y, *, model_seed: int) -> None: ...
    def predict_proba(self, X) -> np.ndarray: ...   # shape (n,), P(attack)
    def to_onnx(self, path: Path) -> None: ...
```
All eight subjects implement it. `to_onnx` is required so Track C consumes exactly
the Track A artefact — not a reimplementation.

### `src/oran_ids/calibration/`
`ece(y, p, n_bins=10, weighting="mass") -> float`; `TemperatureScaler`;
`prior_correct(p, pi_train, pi_target)` implementing Eq. (9). ECE gets a bootstrap
CI (I7).

### `src/oran_ids/metrics/shift.py`
`wasserstein_per_feature(A, B) -> dict`, `mean_w1(...)` for Eq. (2). Reported per
normalisation mode.

### `src/oran_ids/operational/burden.py`
Eq. (3), (4), (8). `alerts_per_hour(fpr, lambda_b)`,
`ppv(recall, fpr, pi)`, `tau_star(sweep, a_max, rho)`,
`deployability(delta, alerts, q99, thresholds) -> bool`.
Pure functions, exhaustively unit-tested — these are the paper's equations and a
bug here is a retraction.

### `src/oran_ids/audit/`
`claims.py` (validate `claims.yaml`), `guard.py` (`TargetCorpusGuard`, resolves A11),
`provenance.py` (git hash, dirty flag, package versions).

---

# 9. Repository Architecture

```
oran-ids-deployability/
├── README.md                    # 10-minute path from clone to a figure
├── LICENSE                      # code licence
├── LICENSE-DATA                 # corpus terms differ; keep separate
├── CITATION.cff
├── Makefile                     # the only interface anyone needs
├── pyproject.toml
├── requirements.lock            # exact pins, generated
├── environment.yml
├── Dockerfile.offline           # Track A/B
├── Dockerfile.xapp              # Track C, deployable image
├── .gitignore  .pre-commit-config.yaml
│
├── configs/
│   ├── base.yaml
│   ├── corpora/{d_a.yaml,d_b.yaml}          # paths, group_key, label map
│   ├── exporter/default.yaml                # timeouts — the A3 control
│   ├── features/{full32.yaml,shared24.yaml,ablation_*.yaml}
│   ├── models/{rf,xgb,mlp,cnn,lstm,majority,tree,iforest}.yaml
│   ├── experiments/{pilot,e1..e9}.yaml
│   └── runtime/{load_sweep.yaml,floor.yaml}
│
├── src/oran_ids/
│   ├── config.py
│   ├── ingest/       features/    splits/
│   ├── models/       calibration/ metrics/
│   ├── operational/  runtime/     audit/  io/
│
├── xapp/                        # what actually ships to the RIC
│   ├── main.py                  # Algorithm 1
│   ├── e2_client.py             # subscription, decode, encode
│   ├── ring_logger.py           # off-critical-path timing log
│   └── xapp-descriptor.json
│
├── experiments/
│   ├── run.py                   # single entry point, config-driven
│   ├── matrix.py                # expands a config into run specs
│   └── runtime_harness.py       # Poisson load generator
│
├── analysis/
│   ├── aggregate.py  stats.py  bootstrap.py
│   ├── make_figures.py  make_tables.py
│   └── validate_results.py      # Phase 14, fails loudly
│
├── survey/                      # Track D
│   ├── protocol.md  screening.csv  extraction.csv  make_survey_table.py
│
├── tests/
│   ├── unit/  integration/  property/
│   └── fixtures/tiny.pcapng     # 200 packets, known ground truth
│
├── scripts/
│   ├── smoke_test.sh  setup_isolation.sh  check_no_placeholders.py
│
├── data/            # gitignored; MANIFEST.json + checksums ARE committed
│   ├── raw/  interim/  processed/  splits/  MANIFEST.json
├── results/         # raw gitignored; aggregated committed
│   ├── raw/  aggregated/  runtime/
├── figures/generated/           # committed (paper depends on them)
├── tables/generated/            # committed
├── logs/                        # gitignored
└── paper/
    ├── main.tex  references.bib
    └── generated → symlink to ../tables/generated
```

**What does *not* belong where.** No notebooks in `src/`. No hardcoded paths
anywhere (all via `config`). No model code in `xapp/` — it loads ONNX only. No raw
captures in git. **No numbers in `main.tex` that are not `\input`.**

---

# 10. Dataset and Scenario Pipeline

## 10.1 Provenance chain

```
config + seed → exporter(version) → flows.parquet → features(family set, norm mode)
              → window(16) → split manifest → run → results
```
Every artefact records the hash of its inputs. `data/MANIFEST.json`:

```json
{
  "corpus": "d_b_5gnidd",
  "source_doi": "10.21227/xtep-hv36",
  "source_sha256": "…",
  "exporter": {"name": "oran_ids.ingest.exporter", "version": "1.2.0",
               "active_timeout_s": 120, "idle_timeout_s": 30,
               "direction_policy": "first_packet"},
  "n_flows": null,
  "n_flows_dropped_short": null,
  "feature_set": "shared24",
  "produced_at": "…", "git_commit": "…",
  "output_sha256": "…"
}
```
`null` fields are filled at generation time. They are not placeholders in the paper
sense; they are schema.

## 10.2 Steps

```bash
make data-fetch      # download D_B pcapng, verify SHA against MANIFEST
make data-extract    # ONE exporter over BOTH corpora  (A3)
make data-features   # families, windowing, short-flow policy  (A12)
make data-splits     # grouped stratified, per split_seed  (A4)
make data-verify     # T-A3 agreement report + manifest reproducibility
```

## 10.3 T-A3 extractor agreement report

`results/aggregated/extractor_agreement.csv`: for 5G-NIDD flows matchable to the
published CSVs, per-feature Spearman correlation and median relative error.
**This is an appendix table in the final paper**, and it is the artefact that
answers the confound objection.

## 10.4 What is *not* generated

No synthetic attack traffic. No synthetic radio KPIs (A1-d). If $\mathcal{D}_A$
cannot be obtained, the answer is to change the paper's scope, not to manufacture
the data.

---

# 11. Baseline Implementation

Eight subjects, one interface, equal budget.

| ID | Subject | Why it is present | Tuning budget |
|---|---|---|---|
| B0 | Majority class | **Floor.** Establishes what 60.7 % prevalence gives for free (I5) | none |
| B1 | Single decision tree (depth ≤6) | Is the task trivially separable in-distribution? | 10 trials |
| B2 | Isolation forest (unsupervised) | Does supervision help, or is this outlier detection? | 10 trials |
| M1 | Random forest | Paper subject | 40 trials |
| M2 | XGBoost | Paper subject | 40 trials |
| M3 | MLP | Paper subject | 40 trials |
| M4 | 1D-CNN | Paper subject | 40 trials |
| M5 | LSTM | Paper subject | 40 trials |

**Fairness constraints.** Identical features, splits, seeds, class weighting, and
threshold sweep. Identical tuning budget across M1–M5 (40 trials of the *same*
search algorithm), recorded in `results/aggregated/tuning_log.csv`. Selection on
$\mathcal{D}_A$ validation only, never on $\mathcal{D}_B$.

**Expected behaviour.** B0 accuracy → class prior by construction; use it as a
pipeline correctness assertion. If M1–M5 transfer performance approaches B0, report
that plainly — it strengthens the paper (see I5).

---

# 12. Testing and Verification Strategy

## 12.1 Unit

| Target | Test | Pass condition |
|---|---|---|
| `config` | round-trip, hash stability | Same YAML ⇒ same hash across processes |
| `exporter` | `tests/fixtures/tiny.pcapng` | Flow count/boundaries match hand annotation |
| `features` | column-set assertion | Declared families == produced columns |
| `normalise` | `source` mode refuses target fit | Raises `LeakageError` |
| `splits` | group disjointness | No group key in two partitions |
| `metrics` | property-based vs sklearn | Agreement to 1e-9 on 1000 random inputs |
| `operational` | Eq. (3),(4),(8) closed forms | Match hand-computed values |
| `calibration` | ECE of perfectly calibrated input | ≈0 |
| `models` | ONNX round-trip | `predict_proba` == ONNX output to 1e-6 |

## 12.2 Integration

- Full pipeline on `tiny.pcapng`, 2 architectures, 1 seed, <90 s.
- Determinism: same seed twice ⇒ identical parquet checksums.
- Seed sensitivity: different `split_seed` ⇒ different split hash.
- Guard: loading $\mathcal{D}_B$ labels outside `final_eval` raises.

## 12.3 Property-based (hypothesis)

`ppv(recall, fpr, pi)` is monotone increasing in recall, decreasing in fpr,
increasing in pi, and ∈[0,1] for all valid inputs. `alerts_per_hour` is linear in
both arguments. These are the paper's equations; test them as mathematics.

---

# 13. Full Experiment Matrix

| ID | RQ | Scenario | Subjects | Parameters | Seeds | Runs | Metrics | Output |
|---|---|---|---|---|---|---|---|---|
| **E1a** | 1 | In-distribution | 8 | full32, norm×3 | 5×3 | 360 | Acc,P,R,F1,AUC | `raw/e1a/` |
| **E1b** | 1 | A→B transfer | 8 | shared24, norm×3 | 5×3 | 360 | + conf. matrix | `raw/e1b/` |
| **E1c** | 1 | B→A reverse | 5 | shared24, norm=source | 5×3 | 75 | Δ$F_1$ | `raw/e1c/` |
| **E2** | 1 | Family ablation | 1 (XGB) | 6 subsets × 2 settings | 5×3 | 180 | F1 both | `raw/e2/` |
| **E3a** | 1 | Calibration | 5 | both settings | 5×3 | 150 | ECE+bootstrap CI | `raw/e3a/` |
| **E3b** | 1 | Temp + prior corr. | 5 | π sweep (7) | 5×3 | 525 | ECE post | `raw/e3b/` |
| **E4** | 2 | Threshold sweep | 5 | τ (21) | 5×3 | — (post-hoc) | alerts·h⁻¹, PPV | `aggregated/e4` |
| **E5a** | 3 | Latency @1k | 5 + floor | pinned cores | 5 runs | 30 | L p50/95/99/999 | `runtime/e5a/` |
| **E5b** | 3 | Stage decomposition | 5 | — | (from E5a) | — | t_feat/t_inf share | `runtime/e5a/` |
| **E5c** | 3 | Early-exit under burst | 1 | 3× overload | 5 | 5 | drops, late-action count | `runtime/e5c/` |
| **E5d** | 3 | Energy | 5 | + idle baseline | 5 | 30 | ΔmJ·dec⁻¹ | `runtime/e5d/` |
| **E6** | 3 | Load sweep + bisection | 5 | 8 loads + bisect | 5 | ~240 | $T_{\max}$ ±10 % | `runtime/e6/` |
| **E7** | 1 | Few-shot adaptation | 2 | 7 budgets | 5×3 | 210 | F1 vs budget | `raw/e7/` |
| **E8** | 2 | Base-rate sensitivity | 5 | π (7) × τ (21) | — | — (post-hoc) | PPV surface | `aggregated/e8` |
| **E9** | 4 | Systematic survey | — | protocol §6.9 | — | — | counts, κ | `survey/` |
| **E10** | 3 | Second hardware class | 5 | (I8) | 3 | 15 | L p99 | `runtime/e10/` |

Total offline runs ≈ 1 860. Track C runs ≈ 320. Both are modest — see §14.

**Every experiment maps to a claim in `claims.yaml`.** Anything that does not map is
deleted, not run.


---

# 14. Computational Budget

## 14.1 Estimates

Assumes a 16-core workstation, 64 GB RAM. Per-run times are engineering estimates
for planning; measure and update after the pilot.

| Experiment | Runs | Est. min/run | Serial CPU-h | Parallel (12 workers) | RAM/worker | Storage |
|---|---|---|---|---|---|---|
| E1a | 360 | 3 | 18 | 1.5 h | 6 GB | 2 GB |
| E1b | 360 | 1 (inference only) | 6 | 0.5 h | 6 GB | 3 GB |
| E1c | 75 | 3 | 4 | 0.4 h | 6 GB | 0.5 GB |
| E2 | 180 | 3 | 9 | 0.8 h | 6 GB | 1 GB |
| E3a/b | 675 | 0.5 | 6 | 0.5 h | 4 GB | 1 GB |
| E7 | 210 | 4 | 14 | 1.2 h | 6 GB | 1 GB |
| **Track A total** | ~1 860 | — | **~57 CPU-h** | **~5 h wall** | — | ~9 GB |
| Data extraction | — | — | ~8 CPU-h | 1 h | 16 GB | 40 GB interim |
| **Track C** | ~320 | 20 (10⁶ decisions + warm-up) | **~107 h** | **not parallelisable** | — | ~25 GB |

**Track C dominates and cannot be parallelised** — the whole point is exclusive use
of isolated cores. ~107 hours ≈ 5 days of continuous machine time. Plan for it.

## 14.2 Cost reductions that preserve validity

- **Deep models: CPU training is fine.** These are ≤1 M parameter models on tabular
  windows. A GPU saves wall-clock but adds a nondeterminism source (cuDNN kernel
  selection). Prefer CPU with `torch.use_deterministic_algorithms(True)`.
- **E1b is inference-only.** Do not retrain for transfer; load the E1a artefact.
  This is also a correctness property — the *same* model must be evaluated in both
  settings, or C2 is meaningless.
- **E4 and E8 are pure post-processing** of stored per-sample scores. Store scores,
  not just metrics; then the entire threshold and base-rate analysis costs seconds
  and can be rerun without touching a model.
- **Track C: reduce repetitions, not sample count.** p99 stability comes from
  samples within a run. 3 runs × 10⁶ is better than 10 runs × 10⁵.

## 14.3 Staged execution

```
smoke (60 s) → pilot 1 % (10 min) → 1 arch × 1 seed full (20 min)
  → Track A full (5 h) → [GATE: Phase 14 validation] → Track C floor (30 min)
  → Track C full (5 days) → E10 (2 h)
```
**Never launch Track C before Track A validation passes** — Track C consumes ONNX
artefacts produced by Track A, and a model bug found on day 4 of a 5-day run is
expensive.

---

# 15. Statistical Analysis Plan

## 15.1 Design rationale

The unit of analysis is the **split repetition** (n=5), not the run (n=15). Within a
split, model seeds are not independent samples of the population quantity.

With n=5 the achievable precision is modest — a paired *t* on 5 observations detects
effects of roughly 1.5σ at 80 % power. This is adequate *only because* the predicted
effect (Δ ≈ 30 points against a split-level σ of a few points) is enormous. **Say
this explicitly in the paper**: the design is powered for a large effect and is not
powered to resolve small differences between architectures. That is an honest
framing and it is also exactly what the revised Section VI-A now argues.

## 15.2 Methods

| Question | Method | Why |
|---|---|---|
| Central tendency | Mean over split means + 95 % CI (t, df=4) | Small n; report the CI, not just σ |
| $\Delta_{F_1} \ne 0$ | Paired *t* on split-level differences | Same splits both settings ⇒ paired |
| Non-normality check | Shapiro–Wilk + Wilcoxon signed-rank as confirmatory | n=5 cannot establish normality; report both |
| Architecture comparison | Friedman + Nemenyi post-hoc | Multiple related subjects across splits |
| Multiplicity | Holm–Bonferroni within each family of tests | Less conservative than Bonferroni, still FWER |
| Effect size | Cohen's $d_z$ for paired; report alongside every *p* | A *p* without an effect size is uninformative |
| ECE uncertainty | BCa bootstrap, 10 000 resamples | ECE has no closed-form SE and is bin-sensitive |
| $T_{\max}$ | Bracketing interval from bisection | Not a point estimate |
| Latency | Percentiles + Maritz–Jarrett SE for p99 | Standard SE formulas are invalid for extreme quantiles |

**Maritz–Jarrett is not decoration** — it gives a defensible interval on p99, which
is the quantity Eq. (6) tests. A p99 without an interval cannot support a
conformance claim.

## 15.3 What we do not do

No test where the prediction is deterministic (e.g. B0 accuracy = class prior). No
significance testing on a single run. No post-hoc test selection after seeing the
data — the tests above are pre-registered in `docs/SPEC.md`.

---

# 16. Figure Plan

| ID | Purpose | Claim | X | Y | Grouping | Source | Stats | Error bars | Script | File |
|---|---|---|---|---|---|---|---|---|---|---|
| F-1 | Reference deployment | context | — | — | — | hand TikZ | — | — | in `main.tex` | — |
| F-2 | Experimental pipeline | method | — | — | — | hand TikZ | — | — | in `main.tex` | — |
| F-3 | In-dist vs transfer $F_1$ | C2 | architecture | $F_1$ % | setting | E1a/E1b | split means | 95 % CI | `make_figures.py::fig_gen` | `fig_gen.pdf` |
| F-4 | Transfer confusion matrix | C4 | pred | actual | — | E1b (XGB) | summed over splits | — | `::fig_conf` | `fig_conf.pdf` |
| F-5 | Family ablation | C5 | $F_1$ % | config | setting | E2 | split means | 95 % CI | `::fig_ablation` | `fig_ablation.pdf` |
| F-6 | Reliability diagram | C6 | mean score | empirical freq | setting | E3a | mass-weighted bins | bootstrap band | `::fig_calib` | `fig_calib.pdf` |
| F-7 | Alert burden vs τ | C8 | τ | alerts·h⁻¹ (log) / PPV | metric | E4 | — | — | `::fig_alerts` | `fig_alerts.pdf` |
| F-8 | p99 vs offered load | C9,C11 | load (log) | p99 ms (log) | architecture | E5a/E6 | median of 5 runs | Maritz–Jarrett | `::fig_latency` | `fig_latency.pdf` |
| **F-9 (new)** | PPV surface over π | C8, A6 | π (log) | PPV | τ | E8 | — | — | `::fig_ppv_surface` | `fig_ppv.pdf` |
| **F-10 (appendix)** | Extractor agreement | A3 | feature | Spearman ρ | — | T-A3 | — | — | `::fig_extractor` | `fig_extractor.pdf` |

F-9 and F-10 are additions. F-9 converts assumption A6 into a result. F-10 is the
appendix figure that answers the confound objection before it is raised.

**F-1 and F-2 stay as hand-written TikZ** — they are conceptual diagrams, not data.
Everything else is generated.

---

# 17. Table Plan

| ID | Purpose | Variables | Source | Statistics | Script |
|---|---|---|---|---|---|
| T-I | Corpora summary | flows, prevalence, KPIs, duration, drop rate | `MANIFEST.json` | counts | `make_tables.py::corpora` |
| T-II | Feature families + $\bar W_1$ | family, members, n, $W_1$ | E1 + shift | per norm mode | `::features` |
| T-III | Hyperparameters | per architecture | tuning log | selected config | `::hyper` |
| T-IV | In-distribution results | Acc,P,R,$F_1$±CI | E1a | split means, t-CI | `::indist` |
| T-V | Cross-deployment + Δ | Acc,P,R,$F_1$±CI, Δ±CI | E1a+E1b | paired, Holm | `::cross` |
| T-VI | Ablation | config, n, both $F_1$ | E2 | split means | `::ablation` |
| T-VII | Runtime | components, p50/95/99, $T_{\max}$, vCPU, RSS, (mJ) | E5,E6 | percentiles + MJ SE | `::runtime` |
| T-VIII | Survey counts | 8 properties, n | Track D | counts + κ | `survey/make_survey_table.py` |
| **T-IX (appendix)** | Extractor agreement | per-feature ρ, rel. error | T-A3 | — | `::extractor` |
| **T-X (appendix)** | Full statistical results | test, statistic, p, $d_z$, adj-p | E1–E7 | Holm | `::stats_appendix` |

T-X matters: putting the full test battery in an appendix lets the body stay
readable while giving a statistician reviewer everything at once.

**Add the energy column to T-VII only if A8 is resolved.**

---

# 18. Automated Results Pipeline

## 18.1 Validation gate (Phase 14)

`analysis/validate_results.py` — **exits non-zero and refuses to produce figures** on:

```
missing runs          expected cell count != observed
duplicate runs        same (config_hash, split_seed, model_seed) twice
NaN/Inf               in any metric column
out-of-range          any rate outside [0,1]; any latency <= 0
inconsistent n        confusion matrix does not sum to test-set size
crashed runs          meta.json without a completion record
stale artefacts       result git_commit not an ancestor of HEAD
placeholder leakage   any metric exactly equal to a value in the old synthetic set
```

That last check is worth building. It is a cheap, direct guard against a synthetic
number surviving into the final paper — which, given this paper's history, is the
specific failure mode to engineer against.

## 18.2 One command

```make
paper: validate aggregate figures tables
	cd paper && latexmk -pdf main.tex
	python scripts/check_no_placeholders.py paper/main.tex

validate:  ; python analysis/validate_results.py --strict
aggregate: ; python analysis/aggregate.py --in results/raw --out results/aggregated
figures:   ; python analysis/make_figures.py --config configs/base.yaml
tables:    ; python analysis/make_tables.py --config configs/base.yaml
```

`check_no_placeholders.py` greps for `\syn{`, `[SYNTHETIC]`, `TBD`, `XXX` and exits
non-zero. Wire it into CI so a placeholder cannot be merged.

## 18.3 Table generation contract

`make_tables.py` writes `tables/generated/cross_deployment.tex` containing **only**
the tabular body. `main.tex` does:

```latex
\begin{table}[t]
\caption{Cross-deployment performance…}\label{tab:cross}
\centering\scriptsize
\input{generated/cross_deployment}
\end{table}
```
Caption and label stay in the paper; numbers come from the pipeline. Neither can
drift from the other.

---

# 19. Reproducibility Plan

## 19.1 The path

```bash
git clone https://github.com/<org>/oran-ids-deployability && cd $_
conda env create -f environment.yml && conda activate oran-ids
pip install -e ".[dev]"
bash scripts/smoke_test.sh          # 60 s
make data-fetch data-extract data-features data-splits data-verify
pytest                              # ~3 min
make experiments-track-a            # ~5 h on 12 cores
make validate aggregate figures tables
make paper                          # regenerates the PDF
```

Track C requires hardware and is documented separately in `docs/RUNTIME.md` with the
kernel parameters, isolation setup, and the floor experiment.

## 19.2 Committed vs excluded

| Committed | Excluded (`.gitignore`) |
|---|---|
| all code, configs, tests | `data/raw/`, `*.pcapng` |
| `data/MANIFEST.json`, checksums | `data/interim/`, `data/processed/` |
| split manifests (indices + hashes) | `results/raw/` |
| `results/aggregated/*.csv` | `logs/` |
| `figures/generated/`, `tables/generated/` | `*.onnx` >50 MB (release asset instead) |
| `requirements.lock` | env dirs |

Split manifests are committed because they are small and they are what makes the
partition exactly reproducible.

## 19.3 README must contain

Hardware requirements; runtime estimates per target; expected outputs with
checksums for the aggregated CSVs; troubleshooting (ONNX version mismatch, thread
oversubscription, missing RAPL permissions); the corpus licence position; and an
explicit statement of which Track C fallback level (§7.6) was used.

---

# 20. Paper-to-Code Consistency Audit

Run after implementation; fill `status` from evidence, not memory.

| Paper statement | Code implementation | Experiment | Evidence | Status |
|---|---|---|---|---|
| "32 features in four families" | `features/families.py` | E1a | column-set assertion in test | ☐ |
| "24 shared, used for transfer" | `configs/features/shared24.yaml` | E1b | assert n_features==24 | ☐ |
| "quantile-normalised per corpus" | `normalise.py` mode | E1 all modes | **Reword to state the mode used (A2)** | ☐ |
| "window of 16 flow records" | `features/window.py` | all | config + drop-rate report | ☐ |
| "disjoint by device identifier" | `splits/grouped.py` | all | group-disjointness test | ☐ |
| "five random seeds" | `matrix.py` | all | **Reword to 5 split × 3 model (A5)** | ☐ |
| "$\mathcal{D}_B$ consumed once" | `audit/guard.py` | all | guard access log | ☐ |
| "$\lambda_b$ = 240 000 flows/h" | `operational/burden.py` | E4 | **State as declared parameter (A6)** | ☐ |
| "$\pi$ = 0.002" | config | E4, E8 | **Present as sweep (A6)** | ☐ |
| "B = 10 ms from spec" | `configs/runtime` | E5 | cite O-RAN WG3 | ☐ |
| "$10^6$ decisions per point" | `runtime_harness.py` | E5 | sample count in meta | ☐ |
| "60 s warm-up discarded" | harness | E5 | discarded count logged | ☐ |
| "CLOCK_MONOTONIC_RAW" | `ring_logger.py` | E5 | code + docs | ☐ |
| "drops rather than acting late" | `xapp/main.py` | E5c | drop count > 0, no late actions | ☐ |
| "RAPL energy per decision" | `runtime/energy.py` | E5d | **baseline-subtracted or dropped (A8)** | ☐ |
| "ECE over ten mass-weighted bins" | `calibration/ece.py` | E3a | unit test | ☐ |
| "temperature scaling on held-out benign" | `calibration/` | E3b | fit-set provenance | ☐ |
| "41 papers surveyed" | `survey/` | E9 | screening.csv | ☐ |
| "we release … container image by digest" | `Dockerfile.xapp` + release | — | digest in README | ☐ |

**Six statements already require rewording** regardless of results (marked bold).
Do that edit before the audit, not after.

---

# 21. Reviewer-Risk Audit

## Major threats

**R1 — "Your gap measures your feature pipeline, not deployment shift." (A3)**
Real, and fatal if unaddressed. *Evidence needed:* T-IX extractor agreement, single
exporter for both corpora, and the `none`/`source`/`target_unsup` spread.
*Fixable without changing the contribution:* yes.

**R2 — "You normalised using the target corpus, so your protocol is transductive." (A2)**
Real. *Evidence:* report all three modes with `source` primary. *Fixable:* yes.

**R3 — "$\mathcal{D}_A$ is not identified; the result is unreproducible." (A1)**
Real and possibly fatal. *Fixable:* only by resolving A1. This is why A1 is a gate.

**R4 — "Two corpora cannot establish a general claim."**
Real but inherent. *Response:* soften phrasing from "detectors do not transfer" to
"transfer fails between these two independently collected deployments, and the
mechanism we identify (deployment-specific radio features) predicts it will recur".
Add corpus pairs if A1-c is chosen — with packet-only corpora, three or four pairs
is cheap and materially strengthens the claim.

**R5 — "Your p99 measures the platform, not the model."**
Real. *Evidence:* the floor experiment (§7.4) plus documented core isolation. Cheap
to fix, devastating if missing.

**R6 — "Table VIII is unsubstantiated." (A9)**
Real. *Fix:* execute Track D or delete.

## Moderate threats

**R7 — "You under-tuned the deep models."** *Fix:* equal-budget tuning log,
published. **R8 — "No trivial baseline."** *Fix:* I5. **R9 — "π is invented."**
*Fix:* I4 sweep + F-9. **R10 — "n=5 cannot support these CIs."** *Fix:* §15.1
explicit power framing; do not overclaim architecture differences. **R11 — "Energy
attribution is invalid."** *Fix:* A8 or drop.

## Minor threats

**R12** single hardware (→ I8). **R13** binary only (already in Limitations).
**R14** no adaptive adversary (already in Limitations). **R15** the early-exit path
is unexercised (→ E5c).

## Not worth engineering for

Do **not** add federated learning, a smart-city framing, a sustainability section,
or a novel detector to pre-empt "where is the contribution?". The contribution is
the measurement. Adding a weak method would dilute it and invite a stronger
objection.

---

# 22. Final Improvement Priorities

| Priority | Problem | Impact | Required change | Effort | Phase | Verification |
|---|---|---|---|---|---|---|
| **Must fix** | A1 $\mathcal{D}_A$ unidentified | Blocks C5, reproducibility | Obtain corpus or drop C5 | 1–10 wk | P0 | Corpus with DOI, or paper rescoped |
| **Must fix** | A3 extractor confound | Invalidates headline | One exporter, both corpora | 1 wk | P6 | T-IX report |
| **Must fix** | A2 normalisation leak | Self-contradiction | 3 modes, `source` primary | 2 d | P6 | `LeakageError` test |
| **Must fix** | A9 unsubstantiated survey | Looks fabricated | Execute or delete | 3 wk / 0 | Track D | screening.csv + κ |
| **Must fix** | No floor experiment | p99 uninterpretable | No-op xApp run | 1 d | P7 | floor distribution reported |
| **Strongly rec.** | A5 wrong variance | CIs too tight | 5 split × 3 model | 1 d (+3× compute) | P2 | CI over split means |
| **Strongly rec.** | I5 no trivial baseline | Cannot judge magnitude | Add B0,B1,B2 | 2 d | P8 | B0 accuracy == prior |
| **Strongly rec.** | A6 π unsourced | Assumption presented as result | Sweep + F-9 | 1 d | P11 | PPV surface |
| **Strongly rec.** | A7 $T_{\max}$ unbounded | Unsupported claim | Extend sweep + bisect | 1 d | P11 | bracketing interval |
| **Strongly rec.** | I6 early exit untested | Unexercised published algorithm | E5c | 1 d | P7 | drops>0, no late actions |
| Optional | A8 energy | One table column | Baseline-subtract or drop | 2 d | P7 | drift < signal |
| Optional | I8 second hardware | Generality | Repeat E5 | 1 d | P13 | two-machine comparison |
| Optional | I7 ECE CIs | Rigour | Bootstrap | 2 h | P15 | BCa interval |
| **Unnecessary** | Discrete-event simulator | — | — | — | — | Weakens the latency claim |
| **Unnecessary** | Novel detector | — | — | — | — | Dilutes the contribution |
| **Unnecessary** | Sustainability/smart-city framing | — | — | — | — | Unsupported by any claim |

---

# 23. Final Repository Tree

As §9, with the state after execution:

```
oran-ids-deployability/
├── data/MANIFEST.json               ← corpora provenance, committed
├── data/splits/split_{101..105}/    ← index arrays + hashes, committed
├── results/aggregated/
│   ├── e1_indist.csv  e1_cross.csv  e2_ablation.csv
│   ├── e3_calibration.csv  e4_burden.csv  e5_runtime.csv
│   ├── e6_scalability.csv  e7_adaptation.csv  e8_ppv_surface.csv
│   ├── extractor_agreement.csv      ← T-IX / F-10
│   ├── tuning_log.csv               ← answers R7
│   └── statistical_tests.csv        ← T-X
├── figures/generated/fig_{gen,conf,ablation,calib,alerts,latency,ppv,extractor}.pdf
├── tables/generated/{corpora,features,hyper,indist,cross,ablation,runtime,survey,extractor,stats}.tex
├── survey/{protocol.md,screening.csv,extraction.csv}
└── paper/{main.tex,references.bib,generated→../tables/generated}
```

---

# 24. End-to-End Execution Checklist

```
[ ] P0  A1 decided in writing; consequence for C5 recorded
[ ] P0  Audit table complete, every row owned
[ ] P1  claims.yaml validates; every claim has falsified_if
[ ] P2  Seed scheme, loads, sweeps frozen in configs
[ ] P3  smoke_test.sh green on clean clone; requirements.lock committed
[ ] P4  Tree built; make help works; pre-commit active
[ ] P5  Import graph acyclic; all modules documented
[ ] P6  ONE exporter over BOTH corpora           ← RED GATE
[ ] P6  T-IX extractor agreement produced
[ ] P6  Manifests reproduce byte-identically
[ ] P7  xApp registers over E2; FLOOR experiment run   ← RED GATE
[ ] P8  Eight subjects, one interface, equal budget logged
[ ] P9  pytest green; ≥80 % coverage; property tests pass
[ ] P10 Pilot sanity checks pass twice; bit-identical rerun  ← RED GATE
[ ] P11 Matrix expanded; every cell maps to a claim
[ ] P12 Budget estimated; staged plan agreed
[ ] P13 Track A executed with full provenance
[ ] P14 make validate green; run count exact       ← RED GATE
[ ] P13 Track C executed (fallback level recorded)
[ ] P15 Pre-registered tests only; effect sizes reported
[ ] P16 All data figures generated, none hand-drawn
[ ] P17 All tables \input, none typed
[ ] P18 make paper regenerates end to end
[ ] P18 check_no_placeholders.py exits 0           ← RED GATE
[ ] P19 Clean-clone reproduction by a second person
[ ] P20 Consistency audit; six rewordings applied
[ ] P21 Reviewer audit; R1–R6 each have evidence
[ ] P22 Must-fix list empty
```

---

# 25. Definition of Done

The project is done when **all** of the following hold:

1. A second person, on a clean machine, reproduces every Track A number from
   `git clone` using only the README, and the aggregated CSVs match committed
   checksums.
2. `make paper` regenerates the PDF from `results/` with zero manual steps, and
   `check_no_placeholders.py` exits 0.
3. Every claim in `claims.yaml` has status `supported`, `withdrawn`, or `rescoped` —
   **none remain `planned`**, and any `withdrawn` claim has been removed from the
   manuscript rather than softened into vagueness.
4. `\synthdraftfalse` is set, the draft banner is gone, and no `\syn{}` macro
   remains in `main.tex`.
5. The bibliography has been verified entry by entry (35 entries still unchecked as
   of the last revision; 3 of the 5 checked contained errors).
6. R1–R6 each have a named artefact answering them.
7. The Track C fallback level actually used is stated in both the paper and the
   README, and §VI-E's wording matches it.
8. Every figure and table in the paper traces to a generating script recorded in
   §16/§17.

**The project is not done when the results look good.** It is done when the path
from raw capture to printed number is mechanical, auditable, and survives a hostile
reading.
