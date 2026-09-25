# Reproducing the results of "Intrusion Detection for O-RAN: What Held-Out Accuracy Predicts About Deployment"

This guide is written for reviewers. It has three levels. Level 1 needs no data
and takes minutes; it regenerates every number, table and figure in the paper
from the per-seed results shipped in `results/` and checks that they equal the
ones in the manuscript. Levels 2 and 3 re-run experiments from the raw corpora.

Everything goes through one script:

```
python scripts/reproduce.py check        # environment and data
python scripts/reproduce.py paper        # Level 1
python scripts/reproduce.py list         # every experiment and its exact command
python scripts/reproduce.py experiment EXP-055    # Level 2, one experiment
python scripts/reproduce.py all          # Level 3, everything
```

## 0. Setup (10 minutes)

Requirements: Python 3.11, a LaTeX distribution with `pdflatex` and `bibtex`
(MiKTeX or TeX Live), about 8 GB of free memory for Level 2/3.

```
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate  on Linux/macOS
pip install -r requirements.lock  # exact versions used for every result
pip install -e .                  # the oran_ids package
python -m pytest -q               # 61 tests
python scripts/reproduce.py check
```

`requirements.lock` pins the versions that produced every number (scikit-learn
1.8.0, XGBoost 3.2.0, NumPy 2.3.5, pandas 2.3.3, ONNX Runtime 1.30.0).
PyTorch is needed only for EXP-050 (`pip install -e .[seq]`).

The paper uses the official IEEE Access LaTeX class (template of 2026-05-13),
shipped with its fonts in `paper/access/`. `scripts/build_paper.py` points
MiKTeX or TeX Live at that folder; nothing has to be installed system-wide.

## 1. Level 1: regenerate the paper from the shipped results (5 to 10 minutes)

```
python scripts/reproduce.py paper
```

This runs, in order:

1. `analysis/revision_stats.py`: every statistic from the raw per-seed CSVs
   in `results/EXP-041` to `results/EXP-057` (Nadeau-Bengio intervals, Holm
   correction, difference-in-differences, pooled operating points, the
   cluster bootstrap with 2,000 replicates and a fixed seed, the deployability
   test). It first asserts that the EXP-056 re-runs reproduce the EXP-046 and
   EXP-041 counts exactly.
2. `analysis/make_numbers.py`: `tables/generated/numbers.tex`, one LaTeX macro
   for every number that appears in the text. No number is typed by hand.
3. `analysis/make_tables_v2.py` and `analysis/make_figures_v2.py`: every table
   and data figure.
4. A comparison of the 36 regenerated files in `tables/generated/` against
   `reproducibility/expected_outputs.json` (comment lines, which carry the
   date and commit, are ignored). Expected result: `36 of 36 generated files
   identical`.
5. `scripts/build_paper.py` (expected: 17 pages, 0 errors, 0 undefined
   references), `scripts/check_withdrawn_claims.py` (no retired claim in the
   text) and `scripts/check_no_placeholders.py`.

To trace any number in the PDF: find its macro in `paper/main.tex`, then its
line in `tables/generated/numbers.tex`, whose comment names the source file.

## 2. Level 2: re-run one experiment from raw data

### Data

| Corpus | Files | Source | Put in |
|---|---|---|---|
| NetsLab-5GORAN-IDD | `Network_Dataset.csv`, `Lower_Layer_Data.db` | https://zenodo.org/records/18923275 (DOI 10.1109/IEEEDATA.2025.3614167) | `data/raw/d_a/` |
| 5G-NIDD | `Combined.csv`, `Encoded.csv` (from `Combined.zip`, `Encoded.zip`) | https://etsin.fairdata.fi/dataset/9d13ef28-2ca7-44b0-9950-225359afac65 | `data/raw/d_b/` |

Both are CC-BY-4.0 and are not redistributed here. `python scripts/reproduce.py
check` verifies each file against the SHA-256 recorded in
`data/provenance/d_a_files.json` and `d_b_files.json`.

### Running

```
python scripts/reproduce.py list
python scripts/reproduce.py experiment EXP-053
python scripts/reproduce.py paper
```

Every runner fixes its split seeds (101-120) and model seed (11), so a re-run
on the same library versions reproduces the shipped CSVs. Runs overwrite
`results/EXP-nnn/`; keep a copy if you want to compare. EXP-043 (latency) must
run alone on a quiet machine; its absolute timings depend on the host.

## 3. Level 3: everything

```
python scripts/reproduce.py all
```

Runs every experiment step behind the manuscript, then Level 1. Expect many
hours: `reproduce.py list` gives the approximate time of each step on the
authors' laptop (Intel i9-13900H, 14 cores, Windows 11). Long
runs can be started detached with `scripts/round2_launch.ps1` (Windows).

## Which experiment feeds which part of the paper

| Experiment | Paper | What it shows |
|---|---|---|
| EXP-042, EXP-050 | Sec. VI-A | Random split raises radio macro-F1 by 0.13 (95% interval -0.01 to 0.27); sequence models gain 0.16 to 0.19 |
| EXP-053 | Sec. VI-B | No drift estimate is possible; held-out benign sessions draw FPR 0.00 to 0.98 |
| EXP-057, EXP-055, EXP-054 | Sec. VI-C | 59% of 5G-NIDD benign flows are copies of flood records; BA ceiling 0.766; the published 99.87-99.96% falls to 76.9% without Seq/Offset |
| EXP-041, EXP-056 | Sec. VI-D | Transfer BA 0.53-0.63 on all flows, 0.61-0.78 without conflicting copies |
| EXP-045, 047, 048, 049 | Sec. VI-E | Robust subset, CORAL and novelty detectors do not transfer |
| EXP-046, EXP-056 | Sec. VI-F | Pooled operating points with cluster-bootstrap intervals |
| EXP-044, diag. | Sec. VI-G | Calibration and prior estimation |
| EXP-043 | Sec. VI-H | Emulated per-stage latency |

Details of every experiment, including the withdrawn ones, are in `EXPERIMENTS.md`.

## Known differences you may see

- Latency (EXP-043) depends on the machine; the conclusions depend on ratios
  between stages and implementations, not on absolute microseconds.
- A different scikit-learn or XGBoost version can change individual fits in
  the last decimal; `reproduce.py paper` will then report which generated
  files differ.
- The paper uses reduced seed counts in three round-2 experiments (EXP-054: 3
  draws; EXP-055: 2 repeats, KNN at the first rung only; EXP-056 flows: 10 of
  20 seeds). The manuscript states this.
