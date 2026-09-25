# Deployability Evaluation of Intrusion Detection xApps in O-RAN Edge Data Centres

Reproduction repository for a study of what happens to O-RAN intrusion detectors
between a benchmark table and a deployment: across evaluation protocols, across
deployments, under a realistic attack base rate, and against the near-real-time
budget.

**One-file overview of the whole project and every experiment:** `EXPERIMENTS.md`.

**Start here:** `MEMORY.md`, then `configs/decisions.md`, then
`reports/SESSION_REPORT.md`. Then run the validation harness, which reports the
live state rather than the state this file claims:

```bash
python -m experiments.final_validation
```

---

## Status

**Work in progress. Not submitted. Do not cite any number from this repository
without checking it against `results/`.**

What exists: a tested pipeline, an independently obtained target corpus, measured
results for evaluation-protocol sensitivity, cross-deployment transfer, alert
burden under a swept base rate, and emulated latency. A decision register
recording every claim that has been withdrawn, and why.

What does not exist, and is reported as not existing:

| Area | Status |
|---|---|
| Real Near-RT RIC runtime measurement | **NOT EXECUTED.** See below |
| Resource scaling under load | **NOT MEASURED** |
| Manuscript | revised twice against simulated IEEE Access reviews (2026-09-24, and round 2 on 2026-09-24/25); every table, figure and in-text number is generated from `results/`. See `reports/response_to_reviewers_round2.md` and the one-file project record `EXPERIMENTS.md` |
| Single-exporter control, third corpus | **NOT DONE**: no Zeek on this host, no 5G-NIDD captures in our copy, no third paired corpus |

### A correction to an earlier version of this file

A previous README described Track C by quoting the wording that results *would*
carry once measured: *"measured on a real Near-RT RIC under synthetic E2 load"*.
That sentence was a statement of intended labelling, not of a result, but it
reads as a result and at least one automated summary of this repository has
repeated it as one.

**To be unambiguous: no measurement on a real Near-RT RIC has been performed in
this project.** All latency figures here are **emulated** — a Windows host, no
CPU isolation, single-process Python — and support relative ordering and stage
decomposition only. They do not support a conformance claim. For what a real
measurement looks like, see Obiuwevwi et al., arXiv:2607.01583, who report
microsecond-scale inference on an OpenAirInterface + FlexRIC testbed, within an
order of magnitude of our ONNX Runtime figures and far below our scikit-learn ones.

---

## What the results currently say

Each of these is backed by files under `results/` and by a report under
`reports/`. Claims that did not survive measurement are listed after them,
because that list is the more informative one.

- **The split protocol moves the score more than the architecture does.** A
  random split inflates macro-F1 by +0.09 to +0.17 against a run-disjoint split,
  and the inflation tracks model flexibility. The two trivial baselines gain
  nothing, which identifies the mechanism as memorisation.
- **Corpus precision and deployment precision differ by two orders of
  magnitude.** At a declared base rate of 0.002, corpus precision is ~0.93 and
  pooled deployment PPV is 0.0055–0.0077, for every detector.
- **The detectors are operationally indistinguishable**, at every base rate from
  1e-4 to 0.5.
- **FPR is not a stable property of these detectors.** Across group-disjoint
  folds it ranges from 0.000 to 0.890.

### Claims withdrawn or contradicted by our own measurements

| Claim | Outcome |
|---|---|
| "Deployment PPV differs ~6x across detectors" | **WITHDRAWN** — an estimator artefact. Pooled, the spread is 1.40x (D-018) |
| "Only XGBoost meets the p99 budget" | **CONTRADICTED** — four of six conform at 10 ms; the fastest is a decision tree |
| "Radio KPIs help in-distribution and hurt transfer" | **WITHDRAWN** under a pre-registered failure criterion (D-010) |
| "Existing work under-reports latency" | **WITHDRAWN** — no evidence was ever collected |
| "Energy differs 13x" | **WITHDRAWN** — RAPL cannot attribute to a container |

### Prior art that pre-empts parts of this work

Found in the Phase 36 re-audit and recorded rather than worked around:

- **Abraheem & Edhirig (2026)** run bidirectional transfer between the same two
  corpora. Any "first cross-deployment evaluation" claim is unavailable.
- **Obiuwevwi et al. (2026)** measure AI inference inside a real Near-RT RIC.

See `reports/literature_audit_v2.md`.

---

## Corpora

| | `D_A` source | `D_B` target |
|---|---|---|
| Name | NetsLab-5GORAN-IDD | 5G-NIDD |
| Exporter | Zeek | Argus |
| Licence | CC BY 4.0 | CC BY 4.0 |
| Obtained from | published artefacts | Etsin/Fairdata, the Finnish national research repository |
| Role | trained on | **transfer-only** |

Neither corpus is redistributed here. `data/provenance/` holds SHA-256 hashes for
every file, and `configs/corpora/` holds the acquisition routes.

The two share **no column names**. The shared feature space is defined by meaning
in `configs/features/shared_space.yaml` — **15 shared concepts, 18 matrix
columns**, not the 24 an earlier draft claimed.

---

## Quick start

```bash
conda env create -f environment.yml && conda activate oran-ids
pip install -e ".[dev]"
pytest -q                              # 42 tests
python -m experiments.final_validation
```

## Pipeline

```bash
python experiments/run_leakage_audit.py            # protocol sensitivity
python experiments/run_transfer.py --reverse       # cross-deployment, both directions
python experiments/run_prevalence_sensitivity.py   # base-rate sweep
python experiments/run_alert_burden.py             # operational burden
python experiments/run_latency.py                  # EMULATED latency
python experiments/run_grouping_confound.py        # grouping confound
make figures tables paper
```

## Non-negotiables

- Normalisation fitted on the source corpus only (A2).
- The target corpus is evaluated once and **every access is logged** to
  `results/EXP-026/logs/target_access.log` (A11).
- No number reaches the paper except by `\input` from `tables/generated/`.
- Results are committed as soon as they exist, not once they are final — that is
  what made D-014 recoverable.
- A negative scientific result is preserved and reported. It is never re-run
  until it improves.

### One non-negotiable that is NOT met, and the consequence

> One flow exporter, one version, both corpora (plan A3).

**Not applied.** `D_A` is Zeek and `D_B` is Argus. Every `Delta_F1` here is
therefore an **upper bound** spanning an independently collected deployment *and*
an independent feature-extraction pipeline, and must never be described as being
"due to deployment shift". Abraheem & Edhirig's dataset-fingerprint audit — a
source classifier reaching 0.993 balanced accuracy on the shared features —
quantifies how separable the two corpora are.

---

## Repository layout

```
configs/      decisions.md, experiment_registry.yaml, corpora, feature spaces
src/oran_ids/ data loaders, shared feature space, models, splits, metrics
experiments/  one runner per experiment; final_validation.py is the health check
results/      raw and processed outputs, one directory per experiment
reports/      one report per experiment, plus audits
paper/        manuscript; every number arrives by \input
tests/        42 tests, incl. regression guards on bugs that reached results
```
