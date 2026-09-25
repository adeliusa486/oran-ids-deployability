# Round-2 revision: status and what is left

Updated 2026-09-25 13:55 (AST). The checklist of the handover prompt below is
done; what remains open is at the end.

## Done

- EXP-053 (time order, benign sessions), EXP-054 (in-target references),
  EXP-055 (published pipeline ladder), EXP-056 (cluster-bootstrap counts),
  EXP-057 (5G-NIDD label-conflict audit): all complete, analysed, in the paper.
- Manuscript: new title, abstract (237 words), contributions, Sections II, IV,
  VI-A..VI-G, VII-B, IX, X; Fig. 2; new Tables tab:timesplit, tab:benign,
  tab:conflict, tab:target_ref, tab:ladder; Table XIII with cluster-bootstrap
  intervals and a "D_B without conflicts" block. Every number is a macro.
- Checks: build 17 pages, 0 errors, 0 undefined refs, 0 overfull boxes;
  check_withdrawn_claims OK (23 patterns); check_no_placeholders OK;
  pytest 61/61; diff.pdf (track changes vs the reviewed manuscript) 22 pages.
- Records: MEMORY.md change log, configs/decisions.md D-030..D-033,
  experiment registry EXP-053..057, docs/claims.yaml C19..C22,
  reports/response_to_reviewers_round2.md, EXPERIMENTS.md (one-file record),
  README status.

## Still open (not doable on this host or needs Adeel)

- Author names, affiliations, biographies (placeholders in main.tex).
- IEEE Access class file (ieeeaccess.cls) is not installed; the paper builds in
  IEEEtran journal layout. Move content into the Access template at submission.
- Real near-RT RIC measurement (EXP-031 blocked: WSL2/Docker cannot start).
- Third corpus with paired radio telemetry; single-exporter re-extraction.
- Attacker addresses per split side for D_A (reviewer 3, optional).
- Optional: EXP-054 used 3 seeds (random, file) and one draw per base-station
  direction; EXP-056 flows 10 of 20 seeds; EXP-055 2 repeats with KNN at R0 only.
  More seeds would tighten intervals but not change any conclusion stated.
- Optional: report the 5G-NIDD duplication to the dataset authors.

## If a new session continues

Read MEMORY.md from "2026-09-24 (round 2" to the end. Regenerate with
`python analysis/revision_stats.py && python analysis/make_numbers.py &&
python analysis/make_tables_v2.py && python analysis/make_figures_v2.py &&
python scripts/build_paper.py`. Never type a number into main.tex; never write
LaTeX through a bash heredoc (backslash-t becomes a tab).
