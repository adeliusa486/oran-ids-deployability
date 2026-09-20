# Literature Audit — Pass 1

**Experiment:** EXP-000 (Phase 0)
**Date:** 2026-09-20
**Output artefacts:** `docs/literature/LITERATURE_MATRIX.csv` (25 entries),
`docs/literature/GAP_MATRIX.md`
**Purpose of this document:** record *how* the literature was searched, how far the
search got, and how much confidence the resulting matrix can carry. The findings
themselves live in the gap matrix; this is the methods-and-limits record for them.

---

## 1. Why this document exists separately

A literature matrix with 25 filled rows looks authoritative regardless of how it was
built. This audit exists so that the matrix cannot be mistaken for something stronger
than it is. The headline number to carry forward is not "25 papers reviewed" but:

> **0 full texts read. 11 abstracts or landing pages retrieved. 4 entries from search
> snippets only. 9 entries from title and URL only. 1 canonical reference cited from
> established metadata.**

Any gap claim that depends on an entry in the last two categories is provisional.

---

## 2. Search protocol executed

**Tooling:** web search and page retrieval. No institutional database access (IEEE
Xplore, ACM DL and ScienceDirect full text were not available; one retrieval attempt
returned HTTP 403).

**Queries issued (11):**

1. NetsLab 5G O-RAN IDD dataset intrusion detection radio KPI physical testbed
2. O-RAN intrusion detection dataset packet traces synchronised E2SM-KPM radio KPIs labelled attacks
3. "Performance Analysis of an AI-Based IDS xApp" O-RAN Near-RT RIC inference latency scaling 2026
4. ARGOS O-RAN intrusion detection xApp Near-RT RIC testbed UE telemetry overhead
5. MobiWatch 6G-XSec open-source O-RAN xApp deep learning anomaly detection MobiFlow OpenAirInterface
6. network intrusion detection cross-dataset generalization fails "base rate fallacy" alert burden operational precision evaluation critique
7. O-RAN data manipulation attack shared data layer SDL anomaly detection xApp poisoning 2025 2026
8. 5G-SPECTOR NDSS 2024 MobieXpert xApp MobiFlow layer-3 attack detection O-RAN abstract authors
9. O-RAN near-real-time RIC control loop latency requirement 10 ms to 1 second specification WG3 E2 indication

**Pages retrieved successfully (9):** Zenodo 18923275 (NetsLab-5GORAN-IDD),
netslab.ucd.ie dataset page, arXiv 2606.22450, arXiv 2607.01583, arXiv 2506.06916,
arXiv 2403.04113, arXiv 2512.01596, arXiv 2510.18160, arXiv 2607.00553,
arXiv 2511.21803, Zenodo 21198102, IEEE DataPort 5G-NIDD page.

**Retrieval failures (2):**

| Target | Failure | Consequence |
|---|---|---|
| ScienceDirect S152614922600202X (P05) | HTTP 403 | One of only two latency comparators is unverified. Its fields in the matrix come from search snippets and are marked `WEAK`. **Must be obtained before any latency claim is written.** |
| NDSS 2024 5G-SPECTOR PDF (P08) | binary PDF could not be parsed | Author list and venue confirmed from NDSS metadata; detection and overhead numbers unverified |

---

## 3. Coverage assessment against the master protocol's required venues

The protocol names arXiv, IEEE Xplore, ACM DL, USENIX, NDSS, CNS, INFOCOM, GLOBECOM,
ICC, TNSM, TIFS, TDSC, TMC, TWC, TCCN, IEEE Network, Computer Networks, FGCS, Elsevier,
Springer, OpenReview, GitHub, Zenodo, Kaggle, institutional repositories, O-RAN SC,
OpenAirInterface, FlexRIC and srsRAN.

| Venue class | Reached | Notes |
|---|---|---|
| arXiv | **yes** — 14 entries | primary source for this pass |
| NDSS | partial — 1 entry (P08), PDF unparsed | |
| ACM DL | metadata only — P12 (`10.1145/3733814.3765495`), P13 (`10.1145/357830.357849`) | no full text |
| IEEE Xplore | metadata only — P01, P02 descriptors, P07, P10 | no full text |
| ScienceDirect / Elsevier | **failed** — 403 | P05 unverified |
| Zenodo | **yes** — 2 records (P01, P23) | |
| Kaggle | indirect — DOI recorded for P01, page not retrieved | |
| IEEE DataPort | **yes** — 1 (P02) | |
| GitHub | metadata only — 5GSEC/MobiWatch, 5GSEC/5G-Spector, oran-dos-kpm-dataset | repositories **not cloned or inspected** |
| USENIX, CNS, INFOCOM, GLOBECOM, ICC, TNSM, TIFS, TDSC, TMC, TWC, TCCN, IEEE Network, Computer Networks, FGCS, Springer, OpenReview | **not reached** | |
| O-RAN SC, OpenAirInterface, FlexRIC, srsRAN repositories | **not reached** | required for Track C (Phase 10); deferred |

**Honest coverage grade: partial.** Sufficient to establish the primary gap (G1 in the
gap matrix), which rests on a coverage *pattern* rather than on any individual paper.
Insufficient to support absence claims about specific criteria (G4, G7).

---

## 4. Findings that change the project, ranked by consequence

### 4.1 Gate A1 is provisionally resolvable (highest consequence)

NetsLab-5GORAN-IDD (P01) supplies the three properties the plan's A1 requires. See
`reports/repository_audit.md` §6 for the caveats. This converts the project's blocking
risk into a verification task.

### 4.2 The near-RT budget is a range, and the choice decides the verdict

P04 assumes 10 ms; P05 assumes 1000 ms; the O-RAN near-real-time control loop is
specified over 10 ms to 1 s. Both papers reach a positive deployability verdict while
reporting latencies five orders of magnitude apart.

Our manuscript currently asserts `B = 10 ms` and derives a binary predicate from it.
As it stands, the paper's central verdict is an authoring choice wearing the clothes of
a measurement. The fix is to sweep `B` and report the crossing point per architecture.
This is improvement **I11** and it strengthens rather than weakens the contribution.

### 4.3 Half of our sharpest claim is now prior work

P03 establishes, in-distribution and on the corpus we intend to adopt, that radio
features match or exceed network-flow features. Claim C5's first half is therefore
theirs. Only the transfer sign-flip remains ours. C5 must be rescoped, not defended.

### 4.4 Inference is not where the latency is

P04 measures a C-exported logistic regression at 1–5 µs and an MLP at 10–25 µs inside a
real FlexRIC xApp. Any latency story of ours that is about *inference cost* is already
answered. Our claim C10 — that feature construction dominates — becomes the load-bearing
latency claim and must be measured with a per-stage breakdown.

### 4.5 Cross-domain IDS failure is not, by itself, novel

P14 (2026) reports exactly that result for IIoT, on a shared feature space, under
imbalanced distributions. Our RQ1 must be framed as the O-RAN instance of a known
phenomenon, measured jointly with deployment criteria — never as a discovery.

P14 also reports that the evaluation protocol can reverse which target appears harder.
That is a direct threat to the stability of our per-architecture `Δ_F1` ordering and
must be tested (improvement **I12**).

### 4.6 An independent third corpus may exist

P23 (O-RAN E2SM-KPM DoS dataset, University of Regina, MIT licence, 69.8 MB) is a
plausible Phase 13 external-validation corpus: different site, different team, small
enough to handle. Its Zenodo record has no description, so feature overlap with our
shared space is unknown and must be checked by inspecting the GitHub repository.

---

## 5. Claims in the current manuscript that the literature does not support

| Manuscript element | Problem | Required action |
|---|---|---|
| `D_A` described as "an OpenRAN Gym style softwarised deployment" citing platform papers | P21 is a platform paper, not a corpus. This is gate A1's exact error | replace with a real corpus citation (P01) once verified |
| C5 "radio KPIs raise in-distribution F1" | prior work (P03) | rescope to the transfer half |
| C9 "only XGBoost meets the p99 budget" | verdict depends on an unjustified single budget | sweep `B` |
| C13 / Table VIII "existing work under-reports these criteria" | no screening study has been executed; this audit is **not** one — it is a targeted search, not a systematic survey | execute Track D with a pre-registered protocol, or delete the table (plan A9) |
| C15 energy per decision | no retrieved source measures container-attributed energy, and A8 says our method cannot either | accept I9 and drop the column |
| Introduction: "compromised IoT devices are a documented source of control-plane signalling overload" | currently uncited | P15 (StormShield) is a candidate; must be retrieved first |

**Note on C13.** It would be convenient to treat this audit's coverage table as evidence
for C13. It is not. A gap matrix built from 11 abstracts through keyword search has
selection bias by construction: it over-samples work that mentions latency or transfer
because those were the search terms. A claim about *reporting prevalence* in a
literature requires a screening protocol with an enumerated candidate pool, inclusion
and exclusion criteria and a second coder. Using this document for C13 would be the
kind of thing this project exists to avoid.

---

## 6. What the next literature pass must do

Ordered by how much a project decision depends on it.

1. **Retrieve P05** by any legitimate route. Blocks the latency narrative.
2. **Read P03 and P04 in full.** Blocks the novelty statement in `GAP_MATRIX.md` §5.
3. **Read the NetsLab descriptor (P01) in full.** Blocks split design (A4) and windowing (A12).
4. **Inspect the P23 GitHub repository.** Decides whether Phase 13 has a corpus.
5. **Resolve the 9 title-only entries.** Decides the strength grade of gaps G4, G5 and G7.
6. **Reach the unreached venues**, in particular TNSM, TIFS, TDSC and the O-RAN SC / FlexRIC / srsRAN repositories. The last group is a Phase 10 prerequisite.
7. **Search terms not yet used**, to counter the selection bias noted in §5: "O-RAN IDS reproducibility", "xApp benchmark", "RAN telemetry drift", "concept drift 5G intrusion detection", "federated IDS O-RAN", "O-RAN security survey 2026".

---

## 7. Audit verdict

| Dimension | Verdict |
|---|---|
| Search breadth | **PARTIAL** — arXiv-dominated, paywalled venues unreached |
| Search depth | **SHALLOW** — 0 full texts |
| Matrix provenance discipline | **PASS** — every cell carries a verification status; `unknown` is distinguished from `no` |
| Primary gap (G1) supported | **YES** — rests on a coverage pattern, not on a single source |
| Absence gaps (G4, G7) supported | **NOT YET** — depend on unresolved title-only entries |
| Gate A1 informed | **YES** — candidate corpus identified |
| Novelty statement produced | **YES**, provisional, deliberately narrow |
