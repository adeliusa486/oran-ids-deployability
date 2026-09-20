# Repository Audit

**Experiment:** EXP-000 (Phase 0, step 1)
**Date:** 2026-09-20
**Commit audited:** `6d657fe` — "Repository skeleton" (the only commit on `main`)
**Remote:** `https://github.com/adeliusa486/oran-ids-deployability.git`
**Auditor stance:** treat every claim the repository makes about itself as unverified
until a command confirms it.

---

## 1. Summary

The repository is a **planning artefact, not a software artefact**. It contains
approximately 138 KB of specification (an implementation plan, a manuscript, a claims
file, four config files) and **zero lines of executable research code**. Everything the
README says about its own status is accurate; nothing is overstated. That is unusual
and worth recording, because the audit's usual job — finding the gap between claimed
and actual state — found no gap here.

The one substantive correction the audit produces is to the README's blocking
statement, which EXP-000's literature pass has now superseded (see §6).

---

## 2. What exists, measured

| Measurement | Command | Result |
|---|---|---|
| Git history | `git log --oneline` | 1 commit (`6d657fe`), working tree clean, tracking `origin/main` |
| Python modules under `src/` | `find src -name '*.py' \| wc -l` | 11 files |
| Non-blank lines of code under `src/` | `cat $(find src -name '*.py') \| grep -cv '^\s*$'` | **0** |
| Test files | `find tests -name 'test_*.py' \| wc -l` | **0** |
| Config files | — | 6 (`base.yaml`, 2 corpora, exporter, 2 feature sets) |
| Manuscript | `paper/main.tex` | 795 lines, 12 sections, compiles to a 331 KB PDF |
| Plan | `docs/IMPLEMENTATION_PLAN.md` | 73 KB, 25 sections, 12 identified weaknesses (A1–A12) |

The 11 Python files under `src/oran_ids/` are all empty `__init__.py` files. There are
no stubs raising `NotImplementedError` in the package itself, contrary to the README's
phrasing "every stub raises `NotImplementedError` by design" — that is true of
`analysis/validate_results.py` only. **Minor README inaccuracy, logged as B-001.**

---

## 3. Gate behaviour, as actually executed

All four guards were run. Raw output is preserved in `results/EXP-000/logs/`.

| Gate | Command | Exit | Behaviour |
|---|---|---|---|
| Smoke | `bash scripts/smoke_test.sh` | 1 | `ModuleNotFoundError: No module named 'oran_ids'` at step 1/5 |
| Tests | `python -m pytest -q` | 5 | "no tests ran" |
| Placeholder guard | `python scripts/check_no_placeholders.py paper/main.tex` | 1 | correctly flags **15** placeholder sites |
| Validation gate | `python analysis/validate_results.py --strict` | 1 | correctly refuses: "no result files under results/raw" |

**Every gate failed, and every gate failed correctly.** This is the desired state for a
skeleton: the guards are live and they refuse to pass an empty project. A skeleton
whose guards passed would be the alarming outcome.

Two clarifications the raw exit codes do not convey:

- The smoke failure is **not** solely an installation problem. With `PYTHONPATH=src`,
  `import oran_ids` succeeds but `oran_ids.io.smoke_corpus` does not exist
  (`hasattr` → `False`). Installing the package would move the failure from step 1 to
  step 2, not fix it. The smoke script is a specification of an interface that has not
  been written.
- `pytest` exit code 5 means "no tests collected", not "tests failed". The
  `--cov-fail-under=80` in the Makefile would be vacuous today.

---

## 4. The plan's own weakness register, re-assessed

`docs/IMPLEMENTATION_PLAN.md` §3 lists 12 weaknesses. This audit re-grades each against
what EXP-000 established.

| ID | Weakness | Plan's grade | Status after EXP-000 |
|---|---|---|---|
| A1 | `D_A` is not a citable artefact | 🔴 BLOCKER | **Provisionally resolved** via option A1-b — see §6 |
| A2 | Per-corpus normalisation leaks target information | 🔴 | Unresolved; mitigation is designed (`normalisation_modes` in `configs/base.yaml`) but unimplemented |
| A3 | Extractor confound | 🔴 | Unresolved. *(Size figure in §6 corrected by EXP-001: 16.85 GB, not 1.5 TB.)* |
| A4 | Grouping key undefined for `D_B` | 🟠 | Partially addressed in config (`group_key: src_ip`); `D_A` key still `null` |
| A5 | Five seeds measure the wrong variance | 🟠 | Addressed in config (5 split × 3 model seeds); unimplemented |
| A6 | π and λ_b unsourced | 🟠 | Addressed in config (declared parameter + sweep); unimplemented |
| A7 | `T_max < 250` is not a measurement | 🟠 | Unresolved |
| A8 | RAPL cannot attribute energy to a container | 🟠 | Unresolved. Recommend accepting I9 (drop the column) — no retrieved source measures it either |
| A9 | Table VIII has no underlying study | 🟠 | Unresolved. No screening protocol has been executed |
| A10 | Single hardware configuration | 🟡 | Unresolved |
| A11 | `D_B`-is-consumed-once needs enforcement | 🟡 | Design exists (`TargetCorpusGuard`); no code |
| A12 | 16-record window under-defined | 🟡 | Addressed in config (`min_records: 16`, `short_flow_policy: drop`); unimplemented, and now **contested** by P03's 27–46% DoS/Benign confusion finding |

The plan's self-assessment is honest and, with one exception, still accurate. The
exception is A1.

---

## 5. Manuscript state

`paper/main.tex` is structurally complete: 12 sections, a threat model, a deployability
predicate, 7 planned figures and 8 planned tables. **Every numerical value in it is
synthetic and is marked as such.** The preamble sets `\synthdrafttrue`, which prints a
page-1 draft banner reading "NOT FOR SUBMISSION", and headline figures are wrapped in a
`\syn{}` macro that the placeholder guard detects.

This is a well-built honesty mechanism and should not be weakened. The guard found 15
sites; those 15 are the complete list of what must be replaced by generated values.

No `\input{tables/generated/...}` directive exists in the manuscript yet. The
"no number reaches the paper except through a generated table" contract (README
non-negotiable #4, plan §18.3) is currently a statement of intent with no mechanism
behind it. **Logged as B-002.**

---

## 6. The finding that changes the project's state

The README says:

> **Blocked on gate A1:** the source corpus is not yet identified. Do not begin feature
> implementation until `configs/corpora/d_a.yaml` is resolved.

EXP-000's literature pass identified a corpus that satisfies the three properties A1
requires — packet-level traces, synchronised radio KPIs, and labelled attack traffic —
from a physical O-RAN testbed:

**NetsLab-5GORAN-IDD** (Abed Zadeh et al., IEEE Data Descriptions 2025;
DOI `10.1109/IEEEDATA.2025.3614167`; Zenodo record 18923275; CC-BY-4.0). Raw `.pcap`
captured at the O-CU, 22 PHY/MAC radio metrics per record exported from the O-DU over
E2, six attack classes, OpenAirInterface testbed with 1 O-CU, 2 O-DU, 1 O-RU and two
physical UEs.

This is option **A1-b** in the plan's own decision table — the cheapest good outcome —
and it means the radio-KPI ablation (C5) does not have to be abandoned.

**Three caveats, all material:**

1. **It is not yet verified at the artefact level.** Only landing pages were retrieved.
   Record counts, label column names, per-record timestamps, device/run identifiers and
   the CU–DU synchronisation tolerance are all unknown. Every one of those is a
   prerequisite for A4 (grouping key) and A12 (windowing). The gate is *provisionally*
   resolved, not resolved.

2. **It creates a new problem for A3.** The plan's non-negotiable is one exporter over
   both corpora from raw packet captures. `D_A`'s raw captures were recorded here as
   ~1.5 TB. **CORRECTION 2026-09-20 (EXP-001): the ~1.5 TB figure recorded by EXP-000 was WRONG. It came from a page summary, not from the record. The Zenodo API gives the whole record as 16.85 GB: five pcap zips totalling 16.40 GB (Benign 5.94, DoS 3.47, DDOS 3.09, BruteForce 3.32, Web 0.59) plus 0.44 GB of summary artefacts.** The sentence below is retained as written, with this
   correction attached, because the record is appended to rather than rewritten.
   `D_A`'s raw captures total ~1.5 TB; `D_B`'s
   are ~3.65 GB. Running one exporter over both at full scale is not feasible on the
   hardware available. A documented, pre-registered subsampling policy for `D_A` is now
   required, or the A3 control must be explicitly weakened and the confound measured
   rather than eliminated. **This is a decision, not a task** — recorded as D-004 in
   `configs/decisions.md`.

3. **There is prior work on this corpus.** Fard, Komarov and Wunder (IEEE CSR 2026)
   already publish a seven-architecture, run-disjoint, ten-seed cross-layer study on it.
   Adopting the corpus means inheriting their result as the in-distribution reference
   and narrowing our C5 claim to the transfer half only. See `docs/literature/GAP_MATRIX.md` §3.

---

## 7. Known bugs and defects opened by this audit

| ID | Severity | Description | Action |
|---|---|---|---|
| B-001 | cosmetic | README says "every stub raises `NotImplementedError`"; the `src/` modules are empty `__init__.py` files with no stubs | correct the README when Phase 5 starts |
| B-002 | structural | the "every number arrives by `\input`" contract has no mechanism: no `\input{tables/generated/*}` exists in `main.tex`, and no generator exists | build the Phase 18 machinery early, as the plan's §1.4 instructs |
| B-003 | blocking-later | `Makefile` references `scripts/check_imports.py`, which does not exist | create it in Phase 5, or drop the `check-imports` target |
| B-004 | environment | `xgboost`, `onnx`, `onnxruntime`, `scapy` and `hypothesis` are declared in `pyproject.toml`/plan but are not installed in the active interpreter | resolve in Phase 3 (environment setup) |
| B-005 | environment | no conda on PATH; `environment.yml` assumes it | document a venv path as an equal-status alternative |

---

## 8. Environment, as measured

| Component | State |
|---|---|
| Python | 3.11.9 (`WindowsApps` interpreter) |
| Available | numpy 2.3.5, pandas 2.3.3, scikit-learn 1.8.0, scipy 1.17.1, statsmodels 0.14.6, matplotlib 3.10.9, pyarrow 23.0.1, torch (present), psutil 7.2.2, pyyaml 6.0.3, pytest 8.4.2 |
| Missing | xgboost, onnx, onnxruntime, scapy, hypothesis |
| LaTeX | `latexmk` present (MiKTeX) |
| conda | **absent** |
| Platform | Windows 11, `win32` |

**Implication for Track C.** `docs/RUNTIME.md` requires `isolcpus`, `nohz_full`,
`cpupower frequency-set` and `pidstat` — all Linux. Track C cannot be executed on this
host. The fallback level (plan §7.6) must be decided now rather than after four weeks of
srsRAN work, and the decision must be recorded in both the paper and the README, as
`docs/RUNTIME.md` itself requires.

---

## 9. Audit verdict

| Dimension | Verdict |
|---|---|
| Repository state matches its own claims | **PASS** (one cosmetic inaccuracy, B-001) |
| Guards are live and fail correctly | **PASS** |
| Research code exists | **FAIL by design** — 0 LOC, and correctly gated |
| Gate A1 | **PROVISIONALLY RESOLVED** — corpus identified, artefact unverified |
| Manuscript honesty mechanism | **PASS** — synthetic values marked and machine-detectable |
| Number-provenance mechanism | **ABSENT** (B-002) |
| Track C feasibility on this host | **BLOCKED** — Linux-only tooling |

**Phase 0 is not blocked by this audit.** The next gate is artefact-level verification
of `D_A`, which is Phase 1 (EXP-001).
