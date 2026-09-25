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

## Still open

- Author biographies and photographs (the IEEE Access class expects them; the
  paper currently has one-line biographies with the affiliation only).
- Corresponding-author line and e-mail addresses (not given yet).
- Real near-RT RIC measurement (EXP-031 blocked on this host).
- A LICENSE file for the public repository (not chosen yet).
- Optional, deliberately left out: more seeds for EXP-054/055/056, a third
  corpus, attacker addresses per split side, informing the 5G-NIDD authors.

Done on 2026-09-25: authors and affiliation set; paper moved to the official
IEEE Access class (template of 2026-05-13, `paper/access/`, three documented
compatibility fixes in the preamble); `REPRODUCE.md` and
`scripts/reproduce.py` (Level 1 reproduces 36 of 36 generated files); new
README; reproducibility zip; pushed to GitHub.

## If a new session continues

Read MEMORY.md from "2026-09-24 (round 2" to the end. Regenerate with
`python analysis/revision_stats.py && python analysis/make_numbers.py &&
python analysis/make_tables_v2.py && python analysis/make_figures_v2.py &&
python scripts/build_paper.py`. Never type a number into main.tex; never write
LaTeX through a bash heredoc (backslash-t becomes a tab).
