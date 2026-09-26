# What Held-Out Scores Predict About Deploying Intrusion Detection in O-RAN

Code, results and manuscript for the paper by **Adeel Ahmad, Arshad Ali, Eraj
Khan, Gahangir Hossain, and Ali Akarma** (Islamic University of Madinah, Higher
Colleges of Technology, and University of North Texas). Prepared for *IEEE
Access* (not yet submitted).

Intrusion detectors for 5G and O-RAN traffic are often reported above 99%
accuracy on a random split of one dataset. This project measures what such a
number predicts about deployment. It evaluates one pipeline (six supervised
architectures and two input-blind baselines) on two public corpora,
NetsLab-5GORAN-IDD and 5G-NIDD, along a ladder of protocols that move closer to
deployment, audits the target corpus's labels, and takes a published 5G-NIDD
pipeline down the same ladder.

**Every number in the paper is generated from `results/`.** No value is typed
into the manuscript, and one command regenerates all of them and checks them
against the paper (see [Reproducing](#reproducing)).

---

## Main findings

| Question | Result | Paper |
|---|---|---|
| Does a random split inflate scores? | Radio-layer macro-F1 rises by 0.13 over a run-disjoint split (95% corrected interval -0.01 to 0.27); for two sequence models the gain is 0.16 to 0.19 and significant. A nearest-neighbor lookup shows the models recognize capture sessions. | VI-A |
| Do detectors drift over time? | The radio capture is ordered by scenario, so a time split hides attack categories. With categories covered, time order is inside session-to-session variation. A held-out benign session draws a false positive rate between 0.00 and 0.98. | VI-B |
| Are 5G-NIDD's labels consistent? | No. 59% of its benign flows are exact copies of UDP-flood records labeled as attacks in the other base station's capture. No classifier reading the record can exceed balanced accuracy 0.766 (0.753 in the shared feature space). | VI-C |
| Does a published 99.9% survive? | The dataset authors' pipeline reproduces (99.87% to 99.96% accuracy) but rests on two record-position fields; without them it scores 76.9%, lower again on held-out capture files and base stations. | VI-C |
| Does a detector transfer between corpora? | Balanced accuracy on 5G-NIDD is 0.53 to 0.63 on all flows and 0.61 to 0.78 on flows with consistent labels, below what the target itself allows. | VI-D |
| Is it usable at a realistic base rate? | At attack prevalence 0.002, operational precision on 5G-NIDD reaches at most 0.063 at any threshold keeping recall above 10%, even on flows with consistent labels. No architecture passes the deployability test; the published pipeline passes it only on its own random split. | VI-G, VII-B |
| Does it hold on a third corpus? | Yes. On a 5G core testbed with consistent labels (NFStream flows), detectors find the SYN flood (recall 1.00 from NetsLab, 0.71 to 1.00 from 5G-NIDD) but flag 16% to 81% of normal flows; balanced accuracy 0.60 to 0.74 from NetsLab, 0.42 to 0.85 from 5G-NIDD, against 0.99 in-target. | VI-F |
| Is the exporter the cause? | No. Re-extracting 5G-NIDD from its captures with Zeek, the exporter of NetsLab, leaves transfer no better: balanced accuracy 0.43 to 0.56 on all flows (lower for all six models) and 0.41 to 0.79 without the copies. | VI-E |
| Does it meet the latency budget in a RIC? | Yes. As a C xApp in FlexRIC with an emulated E2 node, a decision and its control message take at most 5.0 ms at the 99th percentile (10 ms reports); the RIC path, not inference, takes most of that time. | VI-I |
| How should precision be estimated? | Averaging precision over folds inflates the best-to-worst ratio between architectures from 1.45 (pooled counts) to 16.0. | VI-G |

Latency is measured on one host, off-platform and through FlexRIC with an
emulated E2 node (no radio, no real E2 node). All claims that earlier
versions made and later measurements retired are listed in
[EXPERIMENTS.md](EXPERIMENTS.md#6-claims-withdrawn).

---

## Repository layout

```
paper/                 manuscript (IEEE Access class in paper/access/), TikZ figures,
                       references.bib, main.pdf, diff.pdf (tracked changes)
src/oran_ids/          library: data loaders, shared feature space, models, splits, metrics
experiments/           one runner per experiment (run_*.py)
analysis/              statistics, number macros, tables, figures, audits
results/EXP-nnn/       raw per-seed outputs, processed tables, provenance, logs
tables/generated/      every LaTeX table and numbers.tex (all in-text numbers)
figures/generated/     every data figure
scripts/               reproduce.py, build_paper.py, build_diff.py, guards
configs/               decisions.md (D-001..D-033), experiment registry, feature spec
reports/               reviews, responses to reviewers, experiment reports, audits
reproducibility/       expected generated outputs for verification
tests/                 61 unit tests
```

## Reproducing

Full instructions for reviewers: **[REPRODUCE.md](REPRODUCE.md)**.

```bash
pip install -r requirements.lock && pip install -e .
python -m pytest -q                      # 61 tests
python scripts/reproduce.py paper        # regenerate every number, table and figure
                                         # from results/, verify 38 of 38 identical,
                                         # rebuild paper/main.pdf (minutes, no data)
python scripts/reproduce.py list         # every experiment with its exact command
python scripts/reproduce.py experiment EXP-055   # re-run one from raw data
```

Requirements: Python 3.11, `pdflatex` and `bibtex` (MiKTeX or TeX Live).
Versions that produced every result are pinned in `requirements.lock`.

## Data

The corpora are public and are not redistributed here (the first two are CC-BY-4.0; the third states no licence).

| | NetsLab-5GORAN-IDD | 5G-NIDD | 5G core datasets (third) |
|---|---|---|---|
| Role | source (training) | target (transfer), audited | second target |
| Flow exporter | Zeek | Argus | NFStream |
| Download | https://zenodo.org/records/18923275 | https://etsin.fairdata.fi/dataset/9d13ef28-2ca7-44b0-9950-225359afac65 | https://github.com/DLTeamTUC/5GDatasets (commit e71267c) |
| Place in | `data/raw/d_a/` | `data/raw/d_b/` | `data/raw/d_c/` |
| Checksums | `data/provenance/d_a_files.json` | `data/provenance/d_b_files.json` | `data/provenance/d_c_files.json` |

`python scripts/reproduce.py check` verifies the files. Every read of 5G-NIDD is
logged to `results/EXP-026/logs/target_access.log`.

## Experiments

[EXPERIMENTS.md](EXPERIMENTS.md) is the single record of the project: every
experiment from EXP-000 to EXP-057 with its question, command, outputs, status,
result and place in the paper, plus the withdrawn claims and limitations. The
decisions behind each change are in `configs/decisions.md`; the full change log
is at the end of `MEMORY.md`.

## Rules the project keeps

- Normalization and every model choice are fitted on source data only; reads of
  the target corpus are logged.
- Splits are group-disjoint wherever a group key exists (capture session,
  source address, capture file), with a guard that fails on overlap.
- Operating points come from pooled confusion counts, with cluster-bootstrap
  intervals; per-fold averages of precision are not used.
- A negative result is kept and reported. A claim that measurement contradicts
  is withdrawn, recorded in `configs/decisions.md`, and blocked from the text by
  `scripts/check_withdrawn_claims.py`.

## Limitations

The RIC loop uses FlexRIC's emulated E2 node on one host, not a radio deployment. Three
corpora, the third a 5G core testbed rather than O-RAN. The radio layer has 30 capture
sessions, 10 of them benign. 5G-NIDD's conflicting benign records are, by their
addresses, the flood of a second attacker; the dataset authors have not confirmed
this, so results are reported with and without them.

## Citation

If you use this code, please cite the paper (details will be updated on
publication):

```bibtex
@misc{ahmad2026oranids,
  author = {Ahmad, Adeel and Ali, Arshad and Khan, Eraj and Hossain, Gahangir and Akarma, Ali},
  title  = {What Held-Out Scores Predict About Deploying Intrusion Detection in {O-RAN}},
  year   = {2026},
  note   = {Manuscript in preparation for IEEE Access},
  url    = {https://github.com/adeliusa486/oran-ids-deployability}
}
```
