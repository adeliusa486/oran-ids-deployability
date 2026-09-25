# Revision validation report, 2026-09-24

For the authors only. It says what this revision changed, what it could not fix, and where a skeptical reviewer can still push.

## 1. Projected values

None. The manuscript-revision skill allows "implementation target" values for experiments that were not run. This revision uses none. Every number in `paper/main.tex` reaches the text through `tables/generated/numbers.tex` or a generated table, computed from files under `results/` that were produced on this machine during the revision or earlier campaigns. `scripts/check_withdrawn_claims.py` passes on the revised manuscript and fails on the reviewed one.

Experiments the reviewers asked for that were not run are named in the manuscript's Limitations and in the response letter, not simulated:

| Request | Why not run |
|---|---|
| Re-extract 5G-NIDD with Zeek (single-exporter control) | Our copy of 5G-NIDD has Argus flow CSVs only, and Zeek does not run on this Windows host without WSL, which EXP-031 found blocked |
| Third independent O-RAN corpus | No public corpus with paired radio telemetry beyond NetsLab-5GORAN-IDD was available |
| Live Near-RT RIC proof of concept, CPU and memory under load | Same blocker as EXP-031 (no Virtual Machine Platform, so no Docker Linux engine) |
| Official IEEE Access class | Distributed through the IEEE Author Center and Overleaf, not with the sources; apply at submission |

## 2. Claims softened or withdrawn

| Reviewed draft said | Revised manuscript says | Why |
|---|---|---|
| The source-best MLP transfers below the stratified floor, worse than guessing | The MLP scores above the floor | The MLP had no class weighting (D-021) |
| In-distribution rank does not predict transfer rank | Six architectures cannot settle it: 0.83 in macro-F1, -0.26 in balanced accuracy | D-028 |
| Random-split inflation is significant for all six models after Holm | Consistent in direction, not significant per model under the corrected test (p = 0.06 for the average) | Nadeau-Bengio correction (D-026) |
| All six degrade significantly (macro-F1) | Macro-F1 loss equals the floor's; balanced accuracy loss is significant for 5 of 6 | D-027 |
| Every calibration method is monotone and cannot change operating points | Only temperature scaling preserves order; isotonic and Platt can change the ranking | D-029 |
| A deployment cannot know the target prior | Tested: EM and BBSE fail here because class-conditional distributions shift | EXP-044 |
| Feature extraction dominates, even after an order-of-magnitude optimization | Measured per stage on one host; feature construction dominates for flow detectors in this Python pipeline | EXP-043 |
| 0 of 41 surveyed papers report all three criteria | Removed | The survey was never run (D-023) |
| The deployability test fails every model | Still fails every model, now for reasons the tables support | D-028, EXP-052 |

## 3. Remaining risks

- **Exporter confound.** The strongest remaining objection. The domain classifier and robust subset show traffic composition differs, which argues the gap is not only tooling, but they do not measure how much tooling contributes. A reviewer can still say the headline transfer number is not a deployment-shift estimate. The paper no longer claims it is.
- **Thirty sessions.** The radio-layer protocol and temporal results rest on 30 label-pure capture sessions. The corrected intervals are wide and the paper now says so. A reviewer may ask for more capture runs; the raw archives of NetsLab-5GORAN-IDD (16.85 GB) would allow more sessions only if the dataset has more runs than the published summaries expose.
- **Emulated latency.** Now measured carefully and honestly scoped, but still not a RIC measurement.
- **Author block and template.** Placeholders remain for the authors to fill.
- **Scope of the novelty.** The contribution is an evaluation, not a method. Reviewers who expect a new detector will still say so; the Introduction now states the contribution precisely.

## 4. Readiness

The manuscript compiles without errors or undefined references, every figure and table is cited, and every in-text number is generated. What the authors must still do before submission: fill the author block and biographies, move the content into the official IEEE Access class, and decide whether to run the single-exporter control on a Linux host, which would remove the largest remaining objection.
