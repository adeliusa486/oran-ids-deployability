# O-RAN IDS Deployability — Full Session Report

**Date:** 2026-09-20
**Repository:** https://github.com/adeliusa486/oran-ids-deployability
**Commits this session:** 23 (`6d657fe` → `26c95ca`), all pushed to `main`
**Final validation:** 11 PASS · 1 WARN · 4 BLOCKED · **0 FAIL**

---

## 1. TL;DR

The repository went from **0 lines of research code and a fully synthetic manuscript**
to **1,208 lines of tested code, 29 passing tests, three measured findings, generated
figures and tables, and a manuscript that compiles with real numbers**.

Three findings are new and defensible. One of the draft's claims is **contradicted by
our own measurement**. Two claims were **withdrawn** under pre-registered failure
criteria. Four bugs were caught — including one of my own statistical errors — and all
are documented rather than quietly fixed.

**The one thing still missing is the headline.** RQ1 (cross-deployment transfer) has no
result, because no target corpus could be obtained. The paper currently measures
something real and valuable, but not the thing its title promises.

---

## 2. Where the project started

| | State at `6d657fe` |
|---|---|
| Research code | **0 non-blank lines** (11 empty `__init__.py`) |
| Tests | 0 |
| Figures / tables | 0, no generators |
| Manuscript | 795 lines, **every number synthetic**, draft banner up |
| Source corpus `D_A` | **Not identified** — described but never named (gate A1) |
| Target corpus `D_B` | 5G-NIDD, named but never downloaded |
| Guards | 4 present, all correctly failing |

The four guards (smoke, tests, placeholder check, validation gate) all failed, which was
the *correct* state for a skeleton. A skeleton whose guards passed would have been the
alarming outcome.

---

## 3. Phases executed

| Phase | What was done | Gate |
|---|---|---|
| 0 | Repository audit + literature reconstruction (25 papers) | PASS_WITH_LIMITATIONS |
| 1 | Corpus identified, downloaded, verified at artefact level | PASS_WITH_LIMITATIONS |
| 1c | Cross-layer join validated on a pilot archive | complete, then superseded |
| 2 | Data layer, split protocols, leakage audit | PASS |
| 3 | Baseline ladder (8 architectures incl. trivial floor) | PASS |
| 6 | Alert burden over swept base rate | PASS |
| 9 | Latency, tail percentiles, swept budget | PASS (emulated) |
| 15 | Statistical audit (paired tests, Holm, power) | PASS |
| 19 | Claim audit | PASS |
| 22 | Reviewer attack (3 personas) | complete |
| 23 | Final validation harness | 0 FAIL |

Phases 8, 10, 11, 12, 13 and Track D were **deliberately cut** — see D-009.

---

## 4. RESULTS

All results below are on `D_A` = NetsLab-5GORAN-IDD, radio-telemetry layer,
2,808 windows of 16 seconds, 30 label-pure capture runs, group-disjoint splits,
20 split seeds × 2 model seeds.

### 4.1 Finding 1 — A random split inflates scores, and the inflation is not uniform

| Model | Random split | Run-disjoint | Δ | 95% CI | d_z | p (Holm) | Sig. |
|---|---:|---:|---:|---|---:|---:|:---:|
| tree | 0.950 | 0.782 | **+0.168** | [+0.110, +0.226] | 1.35 | 0.0001 | ✔ |
| xgboost | 0.977 | 0.837 | **+0.140** | [+0.084, +0.195] | 1.17 | 0.0003 | ✔ |
| hgb | 0.982 | 0.844 | **+0.138** | [+0.082, +0.194] | 1.16 | 0.0003 | ✔ |
| rf | 0.970 | 0.853 | **+0.117** | [+0.057, +0.177] | 0.92 | 0.0018 | ✔ |
| mlp | 0.959 | 0.849 | **+0.110** | [+0.056, +0.164] | 0.96 | 0.0016 | ✔ |
| logreg | 0.836 | 0.744 | **+0.093** | [+0.037, +0.149] | 0.78 | 0.0051 | ✔ |
| stratified | 0.498 | 0.507 | −0.009 | [−0.011, −0.007] | −2.33 | 0.0000 | (negligible) |
| majority | 0.431 | 0.434 | −0.002 | [−0.008, +0.003] | −0.19 | 0.4006 | ✘ |

**All six non-trivial models significant after Holm correction.**

**The novel part:** the inflation **tracks model flexibility**. A single depth-12 tree
gains most (+0.168), the boosted ensembles next, random forest and MLP less, logistic
regression least (+0.093), and the two trivial baselines gain **nothing**.

That last point is the control: a classifier with no capacity to memorise cannot profit
from a leaky split. It identifies the mechanism as **memorisation**, not as a change in
task difficulty.

**Why it matters:** a published random-split number is inflated *most* for exactly the
flexible architectures most likely to be published. It is not a constant offset a reader
can mentally subtract.

**Network-layer cross-check** (n=5, directional only — significance marks discarded,
see D-013): same sign, comparable magnitude (+0.061 to +0.129), **same capacity
ordering**, on a different layer with different features, a different grouping key and
~100× more rows.

### 4.2 Finding 2 — Corpus precision cannot distinguish these detectors; deployment precision separates them sixfold

At τ = 0.5, π = 0.002, λ_b = 240,000 benign flows/h (both π and λ_b **declared
parameters, not measurements**):

| Model | Macro-F1 | Precision **on corpus** | Recall | FPR | Alerts/h | **PPV in deployment** |
|---|---:|---:|---:|---:|---:|---:|
| rf | 0.852 | 0.926 | 0.954 | 0.262 | 63,306 | **0.081** |
| mlp | 0.847 | 0.933 | 0.937 | 0.234 | 56,571 | **0.036** |
| hgb | 0.844 | 0.928 | 0.945 | 0.257 | 62,114 | **0.129** |
| xgboost | 0.838 | 0.930 | 0.931 | 0.247 | 59,663 | **0.218** |
| logreg | 0.744 | 0.930 | 0.798 | 0.218 | 52,638 | **0.081** |
| majority | 0.434 | 0.766 | 1.000 | 1.000 | 240,481 | 0.002 |

**Corpus precision is flat within 0.007 across all five detectors. Deployment PPV spans
0.036 to 0.218 — a factor of six.** The metric a paper would report cannot tell these
detectors apart; the metric an operator lives with says they are wildly different.

Volumes: 53,000–63,000 alerts/hour, 1.3–1.5 million/day, the large majority false.

The reasoning is Axelsson's (2000) and is not new. **The quantification for a specific
O-RAN detector under a run-disjoint protocol is.**

### 4.3 Finding 3 (unanticipated) — The operator's only runtime control does not work

Threshold required to reach a usable operational precision:

| Model | τ for PPV ≥ 0.25 | Recall there | Alerts/h | τ for PPV ≥ 0.50 |
|---|---|---:|---:|---|
| rf | 0.65 | 0.921 | 57,251 | 0.95 → 7,521 alerts/h, recall 0.418 |
| xgboost | 0.55 | 0.926 | 59,036 | **unreachable** |
| mlp | 0.85 | 0.852 | 44,500 | **unreachable** |
| hgb | 0.99 | 0.898 | 53,632 | **unreachable** |
| logreg | 0.85 | 0.514 | 26,981 | 0.99 → 8,855 alerts/h, recall 0.189 |

**PPV = 0.50 is unreachable at any threshold for four of five detectors.** Their scores
saturate near 1.0 under a group-disjoint split, so raising τ barely moves alert volume —
HGB still emits 53,632 alerts/h at τ = 0.99.

This is a **calibration failure with a direct operational consequence**, and it is
invisible in accuracy, F1 or AUC.

### 4.4 Finding 4 — The near-RT conformance verdict is an authoring choice

**Measurement class: EMULATED** (Windows host, no CPU isolation, single-process Python).
Supports relative ordering and stage decomposition. Does **not** support a conformance
claim on real RIC hardware.

| Model | p50 | p95 | p99 | p99.9 | Min. conforming budget |
|---|---:|---:|---:|---:|---:|
| **FLOOR (no-op)** | 0.01 | 0.02 | **0.10** | 0.53 | — |
| tree | 1.81 | 3.51 | 4.76 | 6.09 | **5 ms** |
| logreg | 2.45 | 4.40 | 6.51 | 13.43 | **10 ms** |
| xgboost | 3.83 | 6.19 | 7.29 | 11.39 | **10 ms** |
| mlp | 2.25 | 4.95 | 8.17 | 13.98 | **10 ms** |
| hgb | 53.16 | 74.76 | 94.62 | 446.06 | **100 ms** |
| rf | 93.41 | 124.55 | 378.05 | 1034.91 | **500 ms** |

The floor experiment ran **first**: platform p99 is 0.103 ms, two orders of magnitude
below the tightest budget, so nothing above is a platform artefact.

O-RAN specifies the near-real-time loop over **10 ms to 1 s**. The same measurements
support four different conclusions:

| Budget | Conforming |
|---|---|
| 1 ms | none |
| 5 ms | tree |
| **10 ms** | tree, logreg, xgboost, mlp |
| 100 ms | + hgb |
| 1000 ms | all |

Reporting the **crossing point** converts an authoring choice into a measurement.

### 4.5 Finding 5 — Feature extraction dominates, for some architectures

Packet-level extraction measured on three DDoS captures with exporter 1.1.0:

| Capture | Size | Flows | ms/flow |
|---|---:|---:|---:|
| ddos_icmp_hping3 | 224 MB | 1,406 | 37.34 |
| ddos_udp_hping3 | 447 MB | 38,340 | 4.49 |
| ddos_syn_hping3 | 1,453 MB | 191,326 | 6.90 |

Median **6.90 ms/flow** against inference of 0.18–0.96 ms → **7× to 39×** for tree, mlp,
logreg and xgboost. **Inverted** for hgb (0.16×) and rf (0.08×), whose own inference
exceeds extraction.

**Two caveats recorded with the result:** the exporter is pure Python at 1.1–4.3 MB/s and
a native one would be perhaps 10× faster; and per-flow cost varies 8× across captures
because it tracks packets-per-flow, not flow count.

---

## 5. Corpus facts established (EXP-001)

| Property | Radio layer | Network layer |
|---|---|---|
| Records | 45,244 → **2,808 windows** | 1,723,817 → **1,640,182** after dedup |
| Features | 22 PHY/MAC → 32 aggregated | 26 → 48 after encoding |
| Sampling | **1.0 Hz**, median gap 1.000 s | n/a |
| Time span | **52.96 days** (2025-05-09 → 2025-07-01) | **no time column at all** |
| Attack prevalence | 76.43% | 94.63% |
| Duplicates | 0 | **83,635 exact rows (4.85%)** |
| Group key | **`session`, 30 runs, 100% label-pure** | `src_ip`, 318 groups |
| Window drop rate | 0.70% | n/a |

**Device-disjoint splitting — the protocol your manuscript states — is NOT supportable.**
`ue_id` has 9 values and one holds 60.8%; `cellid` is constant; `rnti` is reassigned.
The protocol must become **run-disjoint** (bug B-010).

**The CU/DU record-level join is impossible from the published summary artefacts:**
the network CSV has no time column and shares no identifier with the radio layer. Only a
run/category-level association via a hand-written mapping is possible, and even that
joins populations differing by up to 26 percentage points in composition.

The join **does** work from the raw archives (validated at **96.2% median**, min 93.3%,
on 6 Web runs, clock offsets 4–15 s over 250–370 s runs) — but see §7.

---

## 6. Bugs found and fixed

### B-A — Exporter parsed the wrong link layer *(caught by the pilot)*

`D_A`'s captures are **DLT_LINUX_SLL** (Linux cooked, 16-byte header), not Ethernet
(14-byte). Parsing them as Ethernet **did not error**. It byte-shifted every address and
protocol field and produced **5,851 confident, wholly fictional flows** where 908 real
ones existed (`src_ip 184.245.192.168`, `proto 0`).

At scale this would have turned 130 GB into plausible nonsense. Fixed in exporter 1.1.0
with explicit datalink dispatch; unknown link types are now **refused, not guessed**.
Seven regression tests added, including one asserting that parsing SLL as Ethernet does
*not* recover the addresses — the failure mode was silence, so the guard has to be
explicit about it.

### B-B — Dedup policy destroyed real data

The first policy dropped repeated Zeek `uid`s, on the reasonable theory that a `uid` is
unique per connection. **Checking rather than assuming** showed same-`uid` rows differ in
`http_trans_depth`, `files_total_bytes` and `is_GET_mthd` — they are distinct HTTP
transactions within one connection, from the `conn.log`/`http.log`/`files.log` merge.

The policy discarded **35,916 real observations, 98% of them benign**, and pushed apparent
attack prevalence from 94.6% to 96.7%. Corrected to exact-duplicate removal only.

### B-C — My own statistics were wrong *(self-caught)*

I reported the leakage effect as significant for 4 of 6 models using a **percentile
bootstrap CI over 5 split means**. That is the wrong instrument: a bootstrap resampling
five points with replacement can only span the observed values, so it understates
uncertainty. The correct paired t-test gave **p = 0.057–0.15 and no significant result**.

Withdrawn, cause documented (D-012), n raised to 20 on a power calculation **fixed before
the re-run**, and two guards added: the audit returns t-intervals below n=30, and
`bootstrap_ci` warns when called on a small sample. At n=20 the effect **is** established.

### B-D — A finished run silently overwrote another layer's results

The network audit wrote to the same fixed paths as the radio audit and **replaced the
20-seed radio results with 5-seed network data**. The files still parsed and had every
expected column. Had figures been regenerated afterwards, the paper would have carried
network numbers under radio captions with nothing objecting.

Recovered via `git checkout` — results were already committed. Fixed: outputs are named
for the layer they contain, and canonical files refuse overwriting by a run with fewer
seeds or a narrower layer set.

### Also fixed

- `\input` inside a LaTeX `tabular` silently breaks in this TeX install → generator now
  emits **complete tabular environments**; `.gitattributes` pins LF so the fix survives
  checkout.
- The `~1.5 TB` corpus size I recorded in Phase 0 was **wrong** (actual: 16.85 GB). That
  figure was the entire basis of a decision I put to you.
- Gap **G4** ("no O-RAN IDS study reports p99") was **false** — P05 reports ~140 ms.
  Withdrawn.

---

## 7. Decisions taken (all in `configs/decisions.md`)

| ID | Decision | Consequence |
|---|---|---|
| D-001 | Adopt NetsLab-5GORAN-IDD as `D_A` | Gate A1 closed |
| D-004 | Published features both sides | A3 control not applied |
| D-005 | Track C at **Level 2** (real RIC, synthetic E2 load, Linux host) | Not yet executed |
| D-008 | Re-extract from raw archives for C5 | Reversed D-004 for `D_A` |
| D-009 | **Cut 23 phases → 5 experiments** | Thesis → Q1 paper |
| D-010 | Stop bulk download; **C5 withdrawn** | Section VI-C deleted |
| D-011 | Target corpus unresolved; proceed without it | **RQ1 blocked** |
| D-012 | n: 5 → 20; t-intervals not bootstrap | Leakage claim established |
| D-013 | Network audit stays n=5, cross-check only | `src_ip` grouping confound |
| D-014 | Layer-tagged outputs + clobber guard | Results protected |

---

## 8. Claims: what changed

| Claim | Before | Now |
|---|---|---|
| C1 | ">98% in-distribution" | **Moderate** — true only under a *random* split, which is the artefact |
| C5 | "Radio KPIs help in-dist, hurt transfer" | **WITHDRAWN** (D-010), pre-registered outcome |
| C8 | "Default threshold unusable" | **STRONG** — 0.93 → 0.036–0.218 PPV, plus threshold saturation |
| C9 | "Only XGBoost meets p99" | **CONTRADICTED** — 4 of 6 conform at 10 ms; fastest is a decision tree |
| C10 | "Feature extraction dominates" | **MODERATE** — 7–39×, but **architecture-dependent** |
| C13 | "Existing work under-reports" | **WITHDRAWN** — Table VIII deleted, no evidence existed |
| C15 | "Energy differs 13×" | **WITHDRAWN** — RAPL cannot attribute to a container |

**4 of 15 claims carry evidence. 1 is contradicted. 3 withdrawn. 11 unevidenced**, and
the ones that matter most (C2, C3, C4 — transfer) are blocked on a corpus, not effort.

Literature also narrowed the novelty. Three of the draft's "findings" are separately
known: radio-beats-flow in-distribution (Fard et al., CSR 2026, **on this same corpus**),
cross-domain collapse (Hakim et al., 2026), base-rate precision collapse (Axelsson, 2000).

---

## 9. WHAT'S LEFT

### Blocking, in priority order

| # | Item | Why it blocks | Effort |
|---|---|---|---|
| **1** | **Obtain a target corpus, or retitle the paper** | RQ1 — the headline — has no result. Both candidates are behind logins | minutes, if you have IEEE access |
| **2** | **Run Track C at Level 2, or delete the conformance claim** | Latency is emulated on Windows; cannot support a RIC conformance claim | days (needs Linux host + FlexRIC) |
| 3 | Re-run detection under resampled prevalence | Corpus is 76–95% attack; ranking stability untested | hours |
| 4 | Report the `src_ip` grouping confound explicitly | Host-disjoint ≈ attack-disjoint in a testbed | writing only |
| 5 | Align title, abstract, contributions with measured results | Abstract promises transfer results the paper lacks | writing only |
| 6 | Replace the 51 remaining synthetic values | Draft banner must stay up until then | depends on #1 |
| 7 | Native-exporter measurement | Needed before strengthening C10 | days |

### On item 1 — your decision

- **5G-NIDD** `Encoded.zip` (29 MB) — IEEE DataPort, needs an account. Keeps the 5G framing.
- **NF-\* family** (UNSW-NB15, ToN-IoT, BoT-IoT, CSE-CIC-IDS2018) — UQ portal, JS-gated.
  All four were regenerated **with one tool onto one schema**, which would give
  **twelve ordered pairs AND hold the exporter constant by construction** — an empirical
  bound on the confound, which answers the "your gap measures your pipeline" objection
  better than any agreement study. This is what your own plan's risk R4 recommends.
- **Third-party mirrors: refused.** An unattributable corpus is worse than a missing
  experiment.

### If you cannot get a corpus

Retitle to what the work actually measures — *"Evaluation-protocol effects and
operational cost in O-RAN intrusion detection"* — built on the three findings above,
with transfer as future work. Honest, defensible, and publishable.

---

## 10. Reproducing everything

```bash
git clone https://github.com/adeliusa486/oran-ids-deployability
cd oran-ids-deployability
pip install -e ".[dev]"          # or: pip install -r requirements.lock

# data (manual: Zenodo record 18923275)
#   data/raw/d_a/Lower_Layer_Data.db     5.4 MB
#   data/raw/d_a/Network_Dataset.csv   227.2 MB

python scripts/exp001_profile_corpus.py      # corpus verification
python scripts/exp001_join_analysis.py       # CU/DU join feasibility
python experiments/run_leakage_audit.py --layers radio
python experiments/run_alert_burden.py  --layer radio
python experiments/run_latency.py       --layer radio
python analysis/statistical_audit.py
python analysis/make_figures.py
python analysis/make_tables.py
cd paper && latexmk -pdf main.tex

python -m experiments.final_validation       # the honesty check
```

**Environment:** `requirements.lock` pins the 13 imported packages at the versions that
produced every number. Full `pip freeze` in `data/provenance/pip-freeze-full.txt`.

---

## 11. Final validation output

```
  DATA ............... PASS     2 file(s), all checksummed
  SPLITS ............. PASS     disjoint, and the guard fires when violated
  LEAKAGE ............ PASS     n=20 seeds, 7/8 models show a significant effect
  BASELINES .......... PASS     8 architectures incl. the trivial floor
  GENERALISATION ..... BLOCKED  no target corpus (D-011). RQ1 has no result
  STATISTICS ......... PASS     paired tests, effect sizes, Holm correction, power stated
  ROBUSTNESS ......... SKIP     adversarial evaluation cut by D-009; future work
  LATENCY ............ WARN     EMULATED only (floor p99 0.103 ms). No RIC measurement
  RESOURCE ........... BLOCKED  CPU/RAM under load not measured; needs the Linux host
  RIC INTEGRATION .... BLOCKED  Level 2 not executed (D-005)
  FIGURES ............ PASS     3 generated by a committed script
  TABLES ............. PASS     5 generated, all with provenance, all LF
  REFERENCES ......... PASS     bibliography present, no undefined citations
  REPRODUCIBILITY .... PASS     environment, registry, memory and lock present
  MANUSCRIPT ......... BLOCKED  51 synthetic value(s) remain; draft banner correctly up
  CLAIMS ............. PASS     3/15 evidenced; CONTRADICTED and reported: C9
  TESTS .............. PASS     29 passed

  11 PASS   1 WARN   4 BLOCKED   0 FAIL
```

**BLOCKED is a first-class outcome, distinct from FAIL.** "We have not done this and we
say so" is not the same as "we claim something we cannot support". Collapsing the two is
how a validation script becomes decorative.

---

## 12. Key artefacts

| Path | What |
|---|---|
| `MEMORY.md` | Permanent research memory, updated after every experiment |
| `configs/decisions.md` | 14 decisions with rationale and reversal conditions |
| `configs/experiment_registry.yaml` | 27 experiments, gates, dependencies |
| `docs/literature/LITERATURE_MATRIX.csv` | 25 papers × 32 fields, per-cell provenance |
| `docs/literature/GAP_MATRIX.md` | Gaps with strength grades; one withdrawn as false |
| `docs/CLAIM_EVIDENCE_MATRIX.csv` | 15 claims, evidence status, allowed wording |
| `reports/repository_audit.md` | Measured repo state at session start |
| `reports/literature_audit.md` | Search method, coverage, retrieval failures |
| `reports/experiments/EXP-001.md` | Corpus verification |
| `reports/experiments/EXP-002_004_005.md` | The three measured experiments |
| `reports/statistical_audit.md` | Paired tests, Holm, power, what is NOT licensed |
| `reports/final_reviewer_attack.md` | Three reviewer personas, two FATAL findings |
| `src/oran_ids/` | 1,208 LOC: data, splits, models, metrics, exporter, crosslayer |
| `tests/unit/test_exporter.py` | 29 tests |
| `paper/measured_results.tex` | Real results, `\measured{}`-tagged, `\input` only |

---

## 13. The honest one-line verdict

**This is currently a sound methods-and-measurement paper wearing the title of a transfer
paper.** Two of the three deployment criteria are measured and carry findings that are
genuinely new. The third is emulated. The transfer criterion is absent.

The strongest available move is not to word the transfer claims more carefully. It is to
**either get the target corpus or change what the paper claims to be.**
