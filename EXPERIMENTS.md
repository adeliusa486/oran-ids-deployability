# oran-ids-deployability: project and experiment record

One file that describes the whole project: what it asks, what data it uses, how to
reproduce it, and every experiment that was run, with its command, outputs and
result. Details live in the files this page points to.

| If you want | Read |
|---|---|
| The paper | `paper/main.tex` (build with `python scripts/build_paper.py`) |
| Why a decision was made | `configs/decisions.md` (D-001 to D-033) |
| Which claims stand or were withdrawn | `docs/claims.yaml`, `scripts/check_withdrawn_claims.py` |
| Every change, in order | `MEMORY.md`, section "Change log" |
| The reviews and the answers | `reports/peer_review_*.md`, `reports/response_to_reviewers_*.md` |
| How to reproduce every result | `REPRODUCE.md`, `python scripts/reproduce.py` |
| What is still open | `reports/NEXT_STEPS_round2.md` |

## 1. The question

Intrusion detectors for 5G and O-RAN traffic are usually reported with accuracy
above 99% on a random split of one corpus. The project asks what such a number
predicts about deployment. It evaluates one pipeline (six supervised architectures
and two input-blind baselines) on two public corpora along a ladder of protocols
that move closer to deployment: random split, group-disjoint split, held-out
sessions, a second corpus, and an operational analysis at a declared attack base
rate. It also audits the target corpus's labels and takes a published pipeline
down the same ladder. Authors: Arshad Ali and Adeel Ahmad, Faculty of Computer
and Information Systems, Islamic University of Madinah. Target venue: IEEE Access;
the manuscript uses the official IEEE Access LaTeX class (template of 2026-05-13,
in `paper/access/`).

## 2. Data

Neither corpus is committed (`data/raw/` is ignored). Place them as follows.

| Symbol | Corpus | Files used | Where from | Licence |
|---|---|---|---|---|
| D_A | NetsLab-5GORAN-IDD (Zadeh et al., IEEE Data Descriptions 2025) | `data/raw/d_a/Network_Dataset.csv` (Zeek flows), `data/raw/d_a/Lower_Layer_Data.db` (1 Hz radio KPMs) | the dataset's IEEE DataPort record (`reports/experiments/EXP-001.md`) | CC-BY-4.0 |
| D_B | 5G-NIDD (Samarakoon et al. 2022; Siriwardhana et al., IEEE Data Descriptions 2025) | `data/raw/d_b/Combined.csv` (Argus flows, 1,215,890 rows), `data/raw/d_b/Encoded.csv` (authors' one-hot encoding) | https://etsin.fairdata.fi/dataset/9d13ef28-2ca7-44b0-9950-225359afac65 | CC-BY-4.0 |

Facts about the data the analysis depends on:

- D_A radio: 30 capture sessions recovered from clock gaps over 300 s; every
  session carries one category label throughout, so radio labels are session
  labels. Nine benign sessions on days 0-6, attack categories in blocks on days
  47-53, one benign session last (EXP-001, EXP-053).
- D_A flows: 318 source addresses (the group key), 94.63% attack.
- D_B: no addresses, ports or timestamps, but Argus `Seq` and `Offset` survive.
  `Offset` resets recover 20 capture files: two passes of ten captures, one per
  base station. 281,525 of 477,737 benign flows are exact copies of UDPFlood
  records of another file (EXP-057).
- D_C: DLTeamTUC 5G datasets (Nugraha et al., IEEE CSR 2025), https://github.com/DLTeamTUC/5GDatasets at commit e71267c, files `csv/003a-pfcp.csv`, `csv/004-syn-flood.csv`, `csv/005-icmp-flood.csv` into `data/raw/d_c/` (no licence stated upstream; not redistributed). NFStream bytes are converted to inner IP bytes (EXP-058).
- Every read of D_B and D_C is logged to `results/EXP-026/logs/target_access.log`.

## 3. Repository layout

```
src/oran_ids/        loaders (data.py), shared feature space (features/shared.py),
                     model zoo (models/zoo.py), metrics, splits, exporter (ingest/)
experiments/         one runner per experiment (run_*.py)
analysis/            statistics, number macros, tables, figures, audits
scripts/             build, diff, guards (withdrawn claims, placeholders), launcher
configs/             decisions.md, experiment_registry.yaml, label map, feature spec
results/EXP-nnn/     raw/ processed/ statistics/ logs/ per experiment
tables/generated/    every LaTeX table and numbers.tex (all in-text numbers)
figures/generated/   every data figure
paper/               main.tex and inputs, TikZ figures, references.bib
reports/             experiment reports, reviews, responses, audits
tests/               pytest suite (61 tests)
```

## 4. Reproducing

Python 3.11, scikit-learn 1.8.0, XGBoost 3.2.0, NumPy 2.3.5, ONNX Runtime 1.30.0
(`requirements.lock`, `environment.yml`). EXP-050 uses CPU PyTorch in a separate
environment. Split seeds 101-120, model seed 11 unless a runner says otherwise.

```
python -m pytest -q
python scripts/reproduce.py paper           # all numbers, tables, figures, the PDF
python experiments/<runner>.py ...          # see the tables below
python analysis/revision_stats.py           # statistics layer
python analysis/make_numbers.py             # tables/generated/numbers.tex
python analysis/make_tables_v2.py           # tables/generated/rev_*.tex
python analysis/make_figures_v2.py          # figures/generated/fig_rev_*
python scripts/build_paper.py               # paper/main.pdf
python scripts/check_withdrawn_claims.py    # no retired claim in the text
python scripts/build_diff.py                # track-changes PDF
```

Long runs can be started detached with `scripts/round2_launch.ps1`.

## 5. Experiments

### Campaign 1 (2026-09-20): reconstruction and first measurements

| ID | Question | Runner | Status | Result |
|---|---|---|---|---|
| EXP-000 | What do the repository and literature contain? | audit | complete | Four guards work; four draft claims rescoped (`reports/experiments/EXP-000.md`) |
| EXP-001 | Is D_A what its description says? | verification | complete | Time axis present; 30 label-pure sessions; device split not supportable |
| EXP-001c | Can radio and flow records be joined? | re-extraction | partial | Not from the published summary files; needs raw archives |
| EXP-002 | Random-split inflation | `run_leakage_audit.py` | superseded by EXP-042 | +0.09 to +0.17 macro-F1 (radio) |
| EXP-004 | Alert burden | `run_alert_burden.py` | superseded by EXP-046 | Averaged PPV over folds (bug found in EXP-027) |
| EXP-005 | Latency | `run_latency.py` | superseded by EXP-043 | First timings |

### Campaign 2 (2026-09-20): transfer and operational criteria

| ID | Question | Runner | Status | Result |
|---|---|---|---|---|
| EXP-024 | Is the remote repo intact? | git | complete | No discrepancy |
| EXP-025 | Acquire and verify D_B | acquisition | complete | 5G-NIDD verified |
| EXP-026 | D_A to D_B transfer | `run_transfer.py` | superseded by EXP-041 | Transfer largely fails both ways |
| EXP-027 | PPV and pi; the estimator | `run_prevalence_sensitivity.py` | complete | Pooled 1.40x vs mean 13.18x spread; pooled counts primary (D-018) |
| EXP-028 | Calibration | `run_calibration.py` | superseded by EXP-044 | float32 isotonic bug found |
| EXP-029 | Fold composition and FPR | `run_grouping_confound.py` | partial | Composition explains little (max R^2 0.36) |
| EXP-030 | Extraction cost | `run_extraction_benchmark.py` | superseded by EXP-043 | Vectorised exporter 2.3x-12.1x faster, exact |
| EXP-031 | Real near-RT RIC | none | blocked | WSL2/Docker cannot start on host |
| EXP-033 | Adversarial robustness | `run_adversarial.py` | complete, not in paper | Scored on alert burden |
| EXP-034 | Temporal drift | `run_drift.py` | withdrawn (D-030) | See EXP-053 |
| EXP-035 | Multi-axis deployability | `analysis/deployability.py` | complete, not in paper | All six Pareto-efficient |
| EXP-036 | Literature audit | search | complete | Transfer and in-RIC latency already published by others |
| EXP-037 | Manuscript from evidence only | audit | complete | Removed synthetic numbers and a described leak |
| EXP-038 | Reviewer attack | review | complete | `reports/final_reviewer_attack_v2.md` |
| EXP-039 | Figures rebuilt in TikZ | `scripts/extract_figure_icons.py` | complete | Three unsupported figure claims removed |

### Revision 1 (2026-09-24)

| ID | Question | Runner | Status | Result |
|---|---|---|---|---|
| EXP-041 | Transfer, corrected MLP, counts | `run_transfer_v2.py --exp EXP-041 --direction a_to_b --sweeps --reliability` (and `b_to_a`) | complete | Target BA 0.53-0.63; macro-F1 loss equals the majority baseline's |
| EXP-042 | Is the random-split gain memorisation? | `run_leakage_v2.py` | complete | Gain 0.13, NB 95% [-0.01, 0.27]; 1-NN 0.96 vs 0.81 |
| EXP-043 | Per-stage latency, ONNX | `run_latency_v2.py`, `run_extraction_real.py` | complete | Radio path p99 upper bound <= 0.12 ms; exporter bug fixed |
| EXP-044 | Calibration, prior estimation | `run_calibration.py --estimate-prior --out results/EXP-044` | complete | No calibrator helps; EM/BBSE priors 0.16-0.86 vs 0.607 |
| EXP-045 | Exporter sensitivity, robust subset | `run_exporter_sensitivity.py`; `run_transfer_v2.py --exp EXP-045 --features robust --sweeps` | complete | Robust subset: source BA 0.80-0.94, target 0.48-0.53 |
| EXP-046 | Radio alert burden, pooled | `run_alert_burden_v2.py` | complete | FPR 0.22-0.33, 50-74 false alerts per benign UE-hour (intervals: EXP-056) |
| EXP-047 | Cost of the shared space on D_A | `run_transfer_v2.py --exp EXP-047 --features transferable --source-only` | complete | 0.005-0.082 BA, none significant |
| EXP-048 | Benign-only novelty detectors | `run_unsupervised.py` | complete | Fail in distribution |
| EXP-049 | CORAL | `run_transfer_v2.py --exp EXP-049 --adapt coral` | complete | Target BA 0.47-0.60 |
| EXP-050 | Sequence models | `run_sequence_model.py` | complete | GRU +0.165, 1D-CNN +0.189, Holm p <= 0.02 |
| EXP-051 | Drift re-run | `run_drift.py --out results/EXP-051` | withdrawn (D-030) | Held out whole categories |
| EXP-052 | Statistics layer | `analysis/revision_stats.py` etc. | complete | NB intervals, DiD, deployability test |

### Revision 2 (2026-09-24/25)

Review: `reports/peer_review_round2_2026-09-24.md`; decisions D-030 to D-033.

| ID | Question | Runner | Status | Result |
|---|---|---|---|---|
| EXP-053 | Time order with category coverage fixed | `run_drift_v3.py --reps 50` | complete | Latest-session split inside the random-draw range; held-out benign FPR 0.00-0.07 (six sessions), 0.81-0.98 (sessions 4, 8, 29) |
| EXP-054 | D_B in-target references | `run_target_reference.py --seeds 3 --native-seeds 2` | complete | Shared space: random 0.71-0.75 (0.84-0.92 without conflicting copies), held-out capture files 0.93-0.98, station 1 to 2 0.62-0.64, station 2 to 1 0.64-0.65 (0.97-0.99 without copies); native features on held-out files 0.99-1.00 |
| EXP-055 | Published pipeline down the ladder | `run_published_pipeline.py --repeats 2` | complete | Reproduces 99.87-99.96% accuracy; without Seq/Offset 76.9% (BA 0.71), though RF still scores 0.9999 on flows without the conflicting copies; held-out capture files BA 0.80 without the counters (folds 0.50-1.00); across base stations 0.66-0.69; passes the deployability test only at R0 |
| EXP-056 | Cluster-bootstrap intervals | `run_alert_burden_v2.py --out results/EXP-056 --by-session`; `run_transfer_v2.py --exp EXP-056 --direction a_to_b --sweeps --group-counts` | complete (flows on 10 seeds) | Counts equal EXP-046/EXP-041. Radio FPR for LR [0.02, 0.55] (Wilson [0.21, 0.24]); best-threshold PPV interval reaches 1.0. D_B without conflicting copies: transfer BA 0.61-0.78 (LR 0.61, others 0.74-0.78), 0.06-0.25 below the in-target reference; FPR 0.026-0.183; deployability test 0 of 6 |
| EXP-057 | Are D_B labels a function of the record? | `analysis/label_conflict_audit.py` | complete | 52% of flows on records with both labels; file 5 benign = copies of file 15 UDPFlood (33,704 of 33,708 equal counts); BA ceiling 0.766 native, 0.753 shared, 1.000 with Seq/Offset |
| EXP-058 | Does the transfer result hold on a third corpus? | `run_transfer_v2.py --exp EXP-058 --direction a_to_c` (20 seeds) and `b_to_c` (10 seeds); `run_third_corpus_reference.py` | complete | Third corpus = DLTeamTUC 5G core datasets (NFStream, 39,425 flows, 839 attacks). Labels consistent (ceiling 0.992), in-target BA 0.99. Transfer BA 0.60-0.74 from NetsLab, 0.42-0.85 from 5G-NIDD; SYN flood recall 1.00 from NetsLab and 0.71-1.00 from 5G-NIDD; FPR 0.16-0.81; deployability test 0 of 6 |
| EXP-059 | Why do we find 30 radio sessions where Fard et al. report 42 runs? | `run_session_rule.py` | complete | A 90-105 s gap rule gives exactly 42 category-pure segments, and each five-minute session is a union of whole segments. The paper's rule merges back-to-back runs (10 sessions hold two or three subcategories), which is the stricter split |
| EXP-060 | Latency CDF: the EXP-043 radio measurement repeated with every call kept | `run_latency_v2.py --exp EXP-060 --radio-only --keep-samples` | complete | 20,000 per-call times per stage feed the CDF figure. Medians 1.02-2.1 times EXP-043's (median 1.46) on the same host. Aggregation + ONNX p99 upper bound at most 0.36 ms. Attempt 1 ran while other jobs used the host and is kept only as a record (`results/EXP-060/attempt1_concurrent_load/`) |
| EXP-061 | Does the decision loop meet the budget with a RIC in the path? | `scripts/ric/run_exp061.py` (WSL2: FlexRIC v2.0.0, C xApp, emulated gNB) | complete | 6 models at 10 ms reports (5,000 each), LR and RF at 1 ms (20,016 each), no report dropped, C scores equal Python within 3.6e-7. Loop p99, indication to control ACK, 4.45-4.95 ms at 10 ms (upper bound <= 5.01) and 1.42-1.69 ms at 1 ms. Delivery and control are >= 86% of the loop, inference <= 0.23 ms. Emulated E2 node, one host |
| EXP-062 | Which label of the conflicting 5G-NIDD records is right? | `analysis/label_conflict_addresses.py` | complete | The fields-preserved release aligns row for row. All 281,525 benign copies are 10.155.15.7 -> 10.41.150.68 UDP in the window of the UDPFlood of file 15, while file 5's own attacker is 10.155.15.4: they are the second attacker's flood. All 10 BS1 files match capture files 1-10, so the station assignment is confirmed |
| EXP-063 | How much of the D_A -> D_B gap is the exporter? | `scripts/zeek/*.sh`, `build_d_b_zeek.py`, `run_transfer_v2.py --exp EXP-063 --direction a_to_bz --sweeps --group-counts --seeds 10`, `analysis/exporter_control.py` | see registry | 5G-NIDD pcaps re-extracted with Zeek 8.0.10; labels by host pair reproduce all published labels. 346,882 flows. Paired with EXP-056 on the same 10 seeds |
| diag. | Platt inversion | `analysis/platt_diagnosis.py` | complete | Calibration fold AUC 0.48 vs test 0.97; slope -0.55 |

## 6. Claims withdrawn

| Claim | Retired by | Why |
|---|---|---|
| "6x deployment PPV spread" | D-018 | PPV averaged over folds |
| "MLP transfers worse than guessing" | D-028 | Missing class weights |
| "Rank does not predict transfer" | D-028 | Six points cannot settle it |
| "Every calibration method is monotone" | D-029 | Isotonic changes AUC up to 0.21 |
| "Later sessions cost 0.26, false alerts triple" | D-030 | Split held out whole categories |
| "No radio threshold reaches PPV 0.05" | D-031 | Bootstrap intervals reach 1.0 |
| Title scope "IoT traffic in O-RAN edge data centers" | round 2 | Not supported by the corpora |

## 7. Known limitations

- No real near-RT RIC; latency emulated on one Windows host.
- Three corpora, three exporters; the third is a 5G core testbed, not O-RAN, with three capture files.
- Radio layer: 30 sessions (10 benign) in scenario blocks six weeks apart.
- 5G-NIDD labels conflict for 59% of benign flows; results given with and without.
- Author biographies and photographs are still to be added before submission.