# Deployability Evaluation of Intrusion Detection xApps in O-RAN Edge Data Centres

Reproduction repository. See `IMPLEMENTATION_PLAN.md` for the full roadmap.

## Status

Skeleton. `src/oran_ids/` contains 11 empty `__init__.py` files and **0 lines of
research code**. All four guards (`smoke`, `test`, placeholder check, validation
gate) are live and correctly fail on an empty project.

**Every number in `paper/main.tex` is a synthetic placeholder.** The draft banner
is enabled and `scripts/check_no_placeholders.py` detects all 15 sites. Do not
quote any of them.

**Gate A1 is provisionally resolved.** EXP-000 (2026-09-20) identified
NetsLab-5GORAN-IDD — raw pcap at the O-CU plus 22 DU radio KPIs over E2, six
labelled attack classes, physical OpenAirInterface testbed, CC-BY-4.0 — as the
source corpus. It is a *candidate*: nothing has been downloaded or checked.
The blocking item is now **artefact-level verification (EXP-001)**, not corpus
discovery. See `configs/corpora/d_a.yaml` and `configs/decisions.md` D-001.

Two structural decisions were taken on 2026-09-20 (`configs/decisions.md`):

- **D-004** — published features are used on **both** sides (`D_A` Zeek/CSV,
  `D_B` Argus CSV). The A3 single-exporter control is **not** applied, because
  `D_A`'s raw captures were believed to total ~1.5 TB. **That figure was wrong**
  (actual: 16.85 GB — see `reports/experiments/EXP-001.md`), so the premise of
  this decision no longer holds and it is flagged for revisit. Consequence while
  it stands: `Δ_F1` conflates deployment
  shift with exporter differences and is an **upper bound**, not an estimate.
  Mitigations M1 (measure the exporter-only `Δ_F1` on `D_B`, where deployment
  shift is zero by construction — EXP-001b) and M2 (feature-intersection
  sensitivity) are mandatory, and M1 must run before any `Δ_F1` is quoted.
- **D-005** — Track C runs at **Level 2**: a real Near-RT RIC under a
  **synthetic** E2 load generator, no gNB, on a separate Linux host. Results are
  described as "measured on a real Near-RT RIC under synthetic E2 load", never as
  a real deployment.

Start here: `MEMORY.md`, then `configs/experiment_registry.yaml`.

## Quick start

```bash
conda env create -f environment.yml && conda activate oran-ids
pip install -e ".[dev]"
make smoke
```

## Pipeline

```bash
make data-fetch data-extract data-features data-splits data-verify
make test
make experiments-track-a
make validate aggregate figures tables
make paper
```

Track C (runtime measurement on a real RIC) requires dedicated hardware with
isolated CPU cores. See `docs/RUNTIME.md`.

## Non-negotiables

- One flow exporter, one version, both corpora (plan section A3).
- Normalisation fitted on the source corpus only (A2).
- The target corpus is loaded once, at final evaluation, and access is logged (A11).
- No number reaches the paper except by `\input` from `tables/generated/` (section 18.3).
