# Deployability Evaluation of Intrusion Detection xApps in O-RAN Edge Data Centres

Reproduction repository. See `IMPLEMENTATION_PLAN.md` for the full roadmap.

## Status

Skeleton only. Phases 5-8 (research modules) are unimplemented; every stub
raises `NotImplementedError` by design.

**Blocked on gate A1:** the source corpus is not yet identified. Do not begin
feature implementation until `configs/corpora/d_a.yaml` is resolved.

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
