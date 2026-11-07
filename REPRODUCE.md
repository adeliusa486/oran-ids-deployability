# Reproducing the results of "Cross-Corpus Evaluation of 5G Flow Intrusion Detectors: Label Faults, Transfer, and Alert Burden"

(Revision 1 of IEEE Access manuscript Access-2026-49092; first submitted as "What Held-Out
Scores Predict About Deploying Intrusion Detection in O-RAN". Section R below covers the
revision; sections 0 to 3 describe the first submission's pipeline, which revision 1 reuses.)

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
4. A comparison of the 38 regenerated files in `tables/generated/` against
   `reproducibility/expected_outputs.json` (comment lines, which carry the
   date and commit, are ignored). Expected result: `38 of 38 generated files
   identical`.
5. `scripts/build_paper.py` (expected: 19 pages, 0 errors, 0 undefined
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
| 5G core datasets (Nugraha et al., IEEE CSR 2025) | `csv/003a-pfcp.csv`, `csv/004-syn-flood.csv`, `csv/005-icmp-flood.csv` | https://github.com/DLTeamTUC/5GDatasets at commit e71267ca84f6f38ab39f830a2c515555bb5f5898 | `data/raw/d_c/` |

The first two are CC-BY-4.0; the third states no licence. None is redistributed here. `python scripts/reproduce.py
check` verifies each file against the SHA-256 recorded in
`data/provenance/d_a_files.json`, `d_b_files.json` and `d_c_files.json`.

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
| EXP-058 | Sec. VI-F | A third corpus (5G core, NFStream): floods are found, most normal traffic is flagged |
| EXP-046, EXP-056 | Sec. VI-G | Pooled operating points with cluster-bootstrap intervals |
| EXP-044, diag. | Sec. VI-H | Calibration and prior estimation |
| EXP-043 | Sec. VI-I | Emulated per-stage latency |
| EXP-060 | Sec. VI-I | Latency CDF from a repeat that kept every call |
| EXP-059 | Sec. IV-A | Session rule against the 42 runs of Fard et al. |
| EXP-061 | Sec. VI-I, VII-B | Decision loop through FlexRIC with an emulated E2 node (WSL2; `scripts/ric/run_exp061.py`) |
| EXP-062 | Sec. VI-C, Limitations | Addresses of the conflicting 5G-NIDD records (fields-preserved release) |
| EXP-063 | Sec. VI-E | 5G-NIDD re-extracted with Zeek from its captures; transfer paired with EXP-056 |

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


## R. Revision 1 (resubmission of 2026-11)

Revision 1 corrected the 5G-NIDD byte accounting (decision D-035) and added the
experiments the reviewers asked for (EXP-064 to EXP-075; see `EXPERIMENTS.md`).

**Level 1, from the shipped results (minutes).**

```
python analysis/revision_stats_r1.py        # EXP-075: every statistic
python analysis/make_assets_r1.py           # paper/r1/numbers_r1.tex, tables/, figs/
cd paper/r1 && pdflatex main && pdflatex main && pdflatex main
python scripts/flatten_r1.py OUTDIR         # the flat source uploaded to IEEE Access
```

The consolidated per-split outputs are committed (`results/EXP-0xx/consolidated__*`);
the per-flow score arrays they were built from (`scores/`, about 0.9 GB) are not. To
rebuild them, re-run the experiments (Level 2) and then
`python analysis/consolidate_transfer.py EXP tag` for each transfer experiment.

**Level 2, re-running the experiments (hours; about 20 single-process hours).**

```
python experiments/run_transfer_r1.py --exp EXP-064 --source a --targets b bz c --sweeps --reliability --scores
python experiments/run_transfer_r1.py --exp EXP-065 --source a --targets b bz c --features robust --sweeps --scores
python experiments/run_transfer_r1.py --exp EXP-066 --source a --targets b --adapt coral --sweeps --scores
python experiments/run_transfer_r1.py --exp EXP-067 --source b --targets a c --sweeps --scores
python experiments/run_transfer_r1.py --exp EXP-069 --source a --targets b --adapt iw --sweeps --scores
python experiments/run_transfer_r1.py --exp EXP-069 --source a --targets b --adapt dann --sweeps --scores
python experiments/run_target_reference_r1.py --design random  --labels clean --seeds 20
python experiments/run_target_reference_r1.py --design lofo    --labels clean --scores
python experiments/run_target_reference_r1.py --design lofo    --labels relab --scores
python experiments/run_target_reference_r1.py --design station --labels clean --seeds 10 --scores
python experiments/run_target_reference_r1.py --design station --labels relab --seeds 5 --scores
python experiments/run_label_efficient.py --draws 4
python experiments/run_leakage_r1.py
python experiments/run_transfer_r1.py --exp EXP-071 --source a --targets b --n-sub 150000 --seeds 5 --models logreg tree rf xgboost hgb --scores
python analysis/flow_split_coverage.py
python experiments/run_exporter_sensitivity.py --out results/EXP-074/argus_corrected --target b
python experiments/run_exporter_sensitivity.py --out results/EXP-074/zeek --target bz
python analysis/byte_accounting.py
python analysis/label_conflict_pcap.py          # reads the raw 5G-NIDD captures
python analysis/label_conflict_pcap_pairs.py
python analysis/make_corrected_labels.py
```

Every transfer runner accepts `--seed-list` and `--shard i/n` to split work over
processes; each process writes its own folder, and consolidation merges them.
`ORAN_IDS_N_JOBS` limits the threads of the forest and XGBoost per process.

**Corrected 5G-NIDD labels.** `results/EXP-072/corrected_labels/` holds the 281,529
rows of Combined.csv whose label we correct (row position, Seq, Offset, addresses,
published and corrected labels) with SHA-256 checksums and a one-line recipe. No
published file is changed.
