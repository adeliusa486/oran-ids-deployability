# Response to reviewers, round 2

Manuscript: "Intrusion Detection for O-RAN: What Held-Out Accuracy Predicts About
Deployment" (formerly "Intrusion Detection for IoT Traffic in O-RAN Edge Data
Centers: Why Accuracy Alone Is Not Enough"). Review answered:
`reports/peer_review_round2_2026-09-24.md`. Every change is logged in `MEMORY.md`;
decisions D-030 to D-033 in `configs/decisions.md`. Section and table numbers
refer to the revised PDF. All numbers below come from the final runs (EXP-053 to EXP-057).

We thank the reviewers. Three of their questions led to findings that change the
paper more than any requested fix: the radio capture schedule (R1-W6), the
target corpus's labels (R1-W1, R2 on the plateau), and the published pipeline
(R2-C2).

---

## Reviewer 1

**R1-W1. The transfer gap mixes target difficulty with transfer failure.**
Agreed, and the cause is stronger than the reviewer suspected. Asking why four
architectures sit at BA 0.751-0.752 on D_B led to an audit of D_B's labels
(new EXP-057, `analysis/label_conflict_audit.py`). 52% of 5G-NIDD flows share
every field except row index, Seq and Offset with a flow of the opposite label.
All of them are in the two UDP-flood captures. Each of the 281,529 UDPFlood flows
of capture file 15 has an identical copy labelled Benign in file 5, in equal
counts for 33,704 of 33,708 distinct records; the copies are 59% of the corpus's
benign class. No classifier that reads the record can exceed BA 0.766 (native
fields) or 0.753 (our 18 shared columns), in sample. The 0.75 plateau is that
ceiling. New subsection VI-C "The Target Corpus: Labels and a Published Result",
new Table (tab:conflict). We also added in-target references (EXP-054): models
trained and tested on D_B by random, capture-file-disjoint and base-station-
disjoint split, with and without the conflicting copies (Table tab:target_ref).
In the shared space, in-target BA is 0.71-0.75 on a random split (the ceiling),
0.84-0.92 without the copies in the test set, and 0.93-0.98 on held-out capture
files; across the two base stations it is 0.62-0.65, and 0.97-0.99 from station 2
to 1 once the copies leave the test set. Transfer from D_A reaches 0.53-0.63 on
all flows but 0.61-0.78 on flows with consistent labels (0.74-0.78 for the five
nonlinear architectures, 0.61 for LR), 0.06-0.25 below the in-target reference,
and the loss from source is significant for 1 of 6 on those flows. The conflicts
reverse which detector looks transferable: LR looks best on all flows because it
detects no UDP flood, and so flags none of the benign-labelled copies, while RF
and the MLP flag 80-85% of them. Section VI-D, paragraph "The target's labels". Every D_B result is given with and without the
conflicting copies; no label was changed (D-032).

**R1-W2. Drift in macro-F1 across a prevalence shift.** **R1-W6. Category coverage of time-disjoint splits.**
Checking coverage first (EXP-053 A) showed the design cannot work on this
corpus: the radio capture is ordered by scenario (nine benign sessions on days
0-6, attack categories in blocks on days 47-53, one benign session last), and
every radio label is a session label. Every forward session-order split of
EXP-051 held out 1-4 attack categories and tested a single benign session. The
drift claim ("costs a further 0.26 and roughly triples the false-alert rate") is
withdrawn (D-030). Replacement (Section VI-B, Tables tab:timesplit and
tab:benign): holding out the latest session of every category (coverage fixed)
gives BA 0.52-0.57, but 12-32% of 50 draws that hold out a random session of
every category score as low; holding out the earliest gives 0.95-0.99. Time
order stays inside session-to-session variation. Held out one at a time, six
benign sessions draw FPR 0.00-0.07 and three (sessions 4, 8, 29, days 3, 6, 53)
draw 0.81-0.98. All metrics are balanced accuracy and ROC-AUC with both
baselines; macro-F1 is kept only for comparison.

**R1-W3. Wrong unit for drift false alerts.** Fixed: all radio alert volumes are
per benign UE-hour (FPR x 225). The EXP-051 figures that used 240,000 flows per
hour are withdrawn with the drift claim.

**R1-W4. Pooled intervals count samples several times.** Agreed. Intervals for
pooled operating points now come from a cluster bootstrap (2,000 replicates)
that resamples split seeds and clusters: radio sessions, D_A source addresses,
D_B capture files (Section IV-E, Table XIII, D-031). The counts per cluster come
from EXP-056, deterministic re-runs that reproduce EXP-046 and EXP-041 exactly
(asserted in `analysis/revision_stats.py`). The radio result changes: the pooled
FPR interval for LR widens from Wilson [0.21, 0.24] to [0.02, 0.55]; across
architectures FPR runs 0.01-0.65 and PPV at tau 0.5 0.0028-0.13; the
best-threshold PPV interval reaches 1.0 for four of six architectures. The claim
"no radio threshold reaches 0.05" is withdrawn; the text now says the radio alert
burden is not determined by ten benign sessions (Section VI-E). Flow intervals:
D_B FPR 0.009-0.796 across architectures, held-out D_A 0.027-0.611. On D_B without
the copies, FPR is 0.026-0.183 (6,158-44,003 false alerts per hour) and no
threshold with recall above 10% exceeds operational precision 0.063; the
deployability test still fails for all six (best PPV at recall >= 0.5: 0.042).

**R1-W5. Claims without results.** All four were completed: Table VI (GRU +0.165,
1D-CNN +0.189 random-split gain, Holm-adjusted p <= 0.02 within the pair),
Section VI-G (latency; radio path meets 1 ms), Table XI (robust subset: source
BA 0.80-0.94, target 0.48-0.53; CORAL: target 0.47-0.60, only the MLP gains),
B_min in Table XVI (1 ms). The interim "still running" guards were removed, so a
missing result now fails the build.

**Minor points.**
1. Session recovery: every one of the 30 recovered sessions is label-pure, and the
   timeline (`radio_session_timeline()`, `results/EXP-053/processed/session_timeline.csv`)
   matches the capture schedule; a merged session would mix categories.
2. The category-stratified argument is withdrawn as evidence (Section VI-A).
3. Table XII: the text now says no loss is significant.
4. Holm family defined (Section IV-E).
5. The "outside the control range" count is gone with EXP-051; EXP-053 reports
   the share of control draws at or below the time split, descriptively.
6. Calibration caption notes the different split design.
7. Table XV prints bounds and plain decimals.
Consistency items: NN gain now computed from the displayed values (0.15 =
0.96 - 0.81); DiD and reverse-direction ranges at three decimals as in the tables;
the collapse-factor sentence rewritten (the factor is arithmetic in pi); Table V
caption no longer defines an unused asterisk; Table XI has robust and CORAL rows;
Fig. 2 names each rung's layer and metric and adds t_q.

## Reviewer 2

**R2-C1. The >99% premise is uncited.** Now cited: the 5G-NIDD authors report
binary accuracy of 99.85-99.95% for four of five classifiers on a random 70/30
split (Samarakoon et al., arXiv:2212.01298, Table X), and later work reports
weighted F1 up to 99.95% (Ilias et al., arXiv:2412.03483). Sections I and II.

**R2-C2. No published pipeline is reproduced.** Done (EXP-055,
`experiments/run_published_pipeline.py`). We reproduced the 5G-NIDD authors' own
pipeline (Encoded.csv, ANOVA top-10 features, z-score, random 70/30,
DT/RF/KNN/NB/MLP). Our ANOVA F-scores rank the features in exactly their order
(each 1/0.7 of theirs: they ranked on the training split), and we obtain
accuracy 99.87-99.96% (NB 92.7%), matching their Table X. Their first and second
features are Seq and Offset, a record's position in its capture file. Removing
only those two drops DT, RF and the MLP to 76.8-76.9% accuracy (BA 0.70-0.71, FPR
0.59), yet RF still scores 0.9999 on the test flows without the conflicting
copies: the counters resolve the label conflict, they do not detect attacks.
Held out by capture file, BA averages 0.86-0.92 with the published features and
0.80 without the counters, with single folds from 0.50 (accuracy 1.6%) to 1.00;
across base stations it is 0.76-0.89 and 0.66-0.69 (Table tab:ladder). The pipeline passes our
deployability test on its own split (DT and RF: PPV 0.79, 129 false alerts per
hour) and fails it one rung later, which also answers the point that the test
never passed (Section VII-B).

**R2-C3. The target is not separable in the shared space.** See R1-W1: the
limit is label conflicts, not the projection; without the conflicting copies the
shared space separates D_B at BA 0.97-0.99 on held-out capture files.

**R2-C4. Drift uses the metric the paper rejects.** See R1-W2; withdrawn and
replaced.

**Other points.** 1-NN row added to Table V (random 0.958, run-disjoint 0.814,
category-stratified 0.794), with the observation that it scores within 0.04 of
the best architecture. The identical results of four architectures on D_B are
the label-conflict ceiling. The Platt inversion is diagnosed
(`analysis/platt_diagnosis.py`): in that seed the tree's calibration fold had
ROC-AUC 0.48 against 0.97 on test, so the fitted slope was -0.55; the abstract no
longer generalises from it. "Best PPV" is labelled an oracle-threshold upper
bound. The abstract's "no detector reaches 0.05" is withdrawn (R1-W4); the
estimator spread 1.45 vs 16.0 is labelled as a ratio; the rank-correlation
sentence is rewritten. Algorithm 1 now sends a late action and records the
violation, and the text states the policy. pi, lambda_b and A_max remain declared
operator parameters; the verdict's insensitivity to them is stated in VII-B.

## Reviewer 3

- Abraheem and Edhirig's numbers and what this paper adds: Section II.
- Radio labelling: session-level labels and the capture schedule are described
  in Section IV-A; the capture-period confound is a new Limitations item.
- D_B group key: capture files recovered from Offset resets (20 files, two
  per-station passes; Combined.csv restarts its row index where the second pass
  begins). Used for in-target references and the bootstrap.
- Title changed; IoT and edge-data-center framing removed from the title and
  the introduction; keyword "IoT security" replaced by "label quality".
- Literature added: D'hooge et al. (JISA 2020), Engelen et al. (SPW 2021), Flood
  et al. (EuroS&P 2024), Kus et al. (CPSS 2022), all Crossref-verified; RICARCH
  cited as O-RAN.WG3.RICARCH-R003-v04.00.
- Robust subset qualified (not invariant; 40 vs 42 bytes); within-protocol
  separability is not added, but the robust-subset transfer result (target BA
  0.48-0.53) shows the columns carry the shift.
- Per-host or per-incident precision is not added: neither corpus supports
  incident grouping (D_B has no addresses). Stated in Limitations.
- Attacker addresses per split side: not added (open item).

## Still open

Author biographies and photographs; real RIC
(EXP-031 blocked); third corpus.