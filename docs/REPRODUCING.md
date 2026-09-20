# Reproducing this work

**Phase 39.** This is the clean-checkout protocol. It is written so that
someone with no context can run it, and so that every step says what it will
produce and roughly how long it takes.

A `BLOCKED` at the end is not a failure. Two things here genuinely cannot be
reproduced on ordinary hardware, and the protocol says so rather than quietly
skipping them.

---

## 0. What you need

| | |
|---|---|
| Python | 3.11 |
| RAM | **16 GB minimum.** Both corpora are held in memory during transfer |
| Disk | ~2 GB for the corpora, ~100 MB for results |
| Time | ~2 hours for everything except the corpora download |
| OS | any. Nothing below needs Linux — the parts that do are BLOCKED anyway |

## 1. Checkout and environment

```bash
git clone https://github.com/adeliusa486/oran-ids-deployability
cd oran-ids-deployability

conda env create -f environment.yml && conda activate oran-ids
pip install -e ".[dev]"
```

`requirements.lock` pins exact versions; `environment.yml` is the looser
specification. Use the lock file if you want byte-identical numbers.

## 2. Check the guards before the science

```bash
pytest -q
```

Expect **50 passed**. This must work from a bare `pytest` with no environment
variables set. If it fails at collection with `ModuleNotFoundError: oran_ids`,
the root `conftest.py` is missing — that exact failure is what campaign 2 found
and fixed, and it had been hidden because the validation harness injected
`PYTHONPATH=src` when it shelled out.

```bash
python -m experiments.final_validation
```

This runs 22 checks and prints a status for each. It is the fastest way to see
what the repository actually supports, and it cannot be talked round.

## 3. Get the corpora

Neither corpus is redistributed here. Both are CC BY 4.0 and both must be
downloaded from their own sources.

### `D_A` — NetsLab-5GORAN-IDD (source)

Place under `data/raw/d_a/`:

```
Network_Dataset.csv     227,184,406 bytes
Lower_Layer_Data.db       5,402,624 bytes
```

### `D_B` — 5G-NIDD (target)

From the Finnish national research repository — **open**, and **not** the
paywalled IEEE DataPort copy:

```
https://etsin.fairdata.fi/dataset/9d13ef28-2ca7-44b0-9950-225359afac65
DOI 10.23729/e80ac9df-d9fb-47e7-8d0d-01384a415361
```

Place `Combined.csv` (275,265,610 bytes) under `data/raw/d_b/`.
`Encoded.csv` is published too and is **deliberately unused**: it is one-hot
expanded and discards the original Argus field names, so it cannot be mapped onto
`D_A`'s Zeek columns by meaning.

### Verify before running anything

```bash
python - <<'PY'
import hashlib, json, pathlib
for corpus in ("d_a", "d_b"):
    rec = pathlib.Path("data/provenance/%s_files.json" % corpus)
    if not rec.exists():
        continue
    for name, meta in json.loads(rec.read_text()).items():
        f = pathlib.Path("data/raw") / corpus / name
        if not f.exists():
            print("%-18s MISSING" % name); continue
        h = hashlib.sha256()
        with f.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 22), b""):
                h.update(chunk)
        ok = h.hexdigest() == meta["sha256"]
        print("%-18s %s" % (name, "OK" if ok else "SHA MISMATCH"))
PY
```

Every line must say `OK`. A mismatch means you have a different artefact from
the one these results were computed on, and nothing below will reproduce.

## 4. Run the experiments

In this order. Timings are from a 20-core Windows laptop with nothing else
running; expect more if you run several at once, which is not recommended.

```bash
# Evaluation-protocol sensitivity              ~80 min
python experiments/run_leakage_audit.py

# Cross-deployment transfer, RQ1               ~30 min per direction
python experiments/run_transfer.py --reverse

# Base-rate sweep (analytic, no refitting)     ~10 s
python experiments/run_prevalence_sensitivity.py

# Alert burden                                 ~20 min
python experiments/run_alert_burden.py

# Latency -- EMULATED, see section 6           ~10 min
python experiments/run_latency.py

# Calibration                                  ~40 min
python experiments/run_calibration.py --seeds 10

# Grouping confound                            ~10 min for part A
python experiments/run_grouping_confound.py --part all

# Feature extraction benchmark                 ~5 min
python experiments/run_extraction_benchmark.py

# Adversarial and degraded telemetry           ~30 min
python experiments/run_adversarial.py --seeds 5

# Temporal drift                               ~10 min
python experiments/run_drift.py --reps 20
```

Then the outputs:

```bash
python analysis/make_tables.py
python analysis/make_figures.py
python analysis/deployability.py
python -m experiments.final_validation
```

### Do not run two of these at once into the same directory

Each runner writes fixed output paths. Two concurrent runs of the same
experiment will interleave and the survivor will look complete. This happened
during campaign 2 and is recorded as D-014; a clobber guard now refuses to
replace a result that holds more seeds than the incoming one, but the guard only
fires at write time.

### `--quick` is for smoke-testing only

Every runner accepts `--quick`. It writes **the same filenames** with a fraction
of the seeds and models. The validation harness detects this and reports `WARN`
rather than `PASS`, but do not build on a `--quick` result.

## 5. What you should get

| Check | Expected |
|---|---|
| `pytest` | 50 passed |
| Transfer, `D_A -> D_B` | 6/6 non-trivial architectures significant after Holm |
| | MLP target macro-F1 **below** the stratified floor |
| | Spearman rho between source and target rank ≈ +0.14, not significant |
| Prevalence | pooled PPV 0.0055–0.0077 at π=0.002; collapse factor ≈ 132 |
| Estimator | pooled 1.40x, median 1.73x, mean 13.18x |
| Extraction | vectorised agrees with reference exactly; 2.3x–12.1x speed-up |
| `final_validation` | 0 FAIL |

Exact floating-point agreement is expected only with `requirements.lock`.
Different BLAS builds move the MLP by small amounts. Conclusions must not move.

## 6. What cannot be reproduced, and why

Two items are **BLOCKED** and will stay that way on ordinary hardware. They are
listed here so nobody spends an afternoon discovering it.

### Real Near-RT RIC runtime

`reports/EXP-031_real_ric_blocked.md`. Needs a bare-metal Linux host with root:
`isolcpus`, `nohz_full`, `rcu_nocbs`, the `performance` governor, turbo disabled,
plus FlexRIC and a synthetic E2 load generator with a **recorded** arrival
process.

**Every latency number in this repository is EMULATED** and supports relative
ordering and stage decomposition only. It supports no conformance claim. For a
real measurement see Obiuwevwi et al., arXiv:2607.01583, who report inference
three orders of magnitude faster than our Python prototype.

### CPU and RAM under load

Not measured at all. Same hardware requirement.

## 7. The original pcap captures

`results/EXP-005`'s extraction timings were measured on `D_A`'s raw captures,
which are **no longer on disk** — D-010 stopped the 16.85 GB bulk download.
`experiments/run_extraction_benchmark.py` therefore uses synthetic captures with
flow count, packet count, packets-per-flow and link type controlled exactly, and
calibrates the reference exporter against the recorded real-capture throughput.
That is a fair instrument for comparing implementations and a poor one for an
absolute claim, and the script says so in its own output.

## 8. If a number disagrees

Read `configs/decisions.md` first. Eighteen decisions are recorded there with
what would reverse each one, and several of them exist because an earlier version
of this work got the number wrong:

- **D-012** — bootstrap CIs below n=30 are anti-conservative; use t-intervals
- **D-014** — two runs writing one path
- **D-015** — Zeek `src_bytes` is payload, Argus `SrcBytes` is not
- **D-018** — average PPV across folds and you will get a different answer

Then read `MEMORY.md`, which opens with a START HERE block describing the live
state and the mistakes not to repeat.
