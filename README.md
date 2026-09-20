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

Two decisions are open and block later phases:

- **D-004** — `D_A` raw captures total ~1.5 TB against `D_B`'s ~3.65 GB, so the
  "one exporter over both corpora" control (A3) needs a pre-registered
  subsampling policy. Blocking for Phase 2.
- **D-005** — Track C needs Linux CPU isolation tooling; the development host is
  Windows. The fallback level must be chosen before any runtime work.

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
