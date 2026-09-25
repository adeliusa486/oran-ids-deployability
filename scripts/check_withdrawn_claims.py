#!/usr/bin/env python3
"""Fail if the manuscript still asserts something we withdrew.

This guard exists because the same failure happened three times in one session,
and each time it was found by reading rather than by a check.

`\\syn{}` marks a fabricated NUMBER. Nothing marked the fabricated or stale
REASONING around it, so:

* the Methodology section described features as "quantile-normalised per corpus",
  which fits a transform on the target corpus and is exactly what A2 forbids. The
  paper described a leak it does not commit.
* the Conclusion asserted claim C5 -- that radio telemetry most improving
  in-distribution accuracy is the most deployment-specific -- two phases after
  C5 was withdrawn under a pre-registered failure criterion.
* the feature count said 24 in three places, including a table row describing a
  Timing family with a measured covariate shift, on a target corpus that
  publishes no inter-arrival statistics at all.

`analysis/make_tables.py` made numbers structural: they arrive by `\\input` from
a generator and cannot be retyped. This does the same for retired prose. A
withdrawn claim is not withdrawn until no sentence in the manuscript asserts it.

Each pattern below names the claim or decision that retired it, so a failure
tells the author where to read rather than only that something is wrong.

Usage:  python scripts/check_withdrawn_claims.py [paper/main.tex]
Exit:   0 clean, 1 if any forbidden assertion survives.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# (compiled pattern, what retired it, what to do instead)
FORBIDDEN: list[tuple[str, str, str]] = [
    (r"quantile[- ]normalis(ed|ation)\s+per\s+corpus",
     "A2 / README non-negotiable",
     "normalisation is fitted on SOURCE training data only; say that instead"),

    (r"24[- ]feature shared space|24 shared|shared subset:\s*24",
     "EXP-026 / configs/features/shared_space.yaml",
     "the shared space is 15 concepts / 18 matrix columns"),

    (r"radio[- ]layer telemetry that most improves",
     "C5, WITHDRAWN by D-010",
     "the ablation claim was withdrawn under a pre-registered failure criterion"),

    (r"factor of six|sixfold|six[- ]fold|spans?\s+0\.036\s+to\s+0\.218",
     "C8 clause, WITHDRAWN by D-018 (bug B-E)",
     "pooled PPV spread is 1.40x; the 6x was a mean-of-folds artefact"),

    (r"only\s+XGBoost\s+(meets|conforms|satisfies)",
     "C9, CONTRADICTED",
     "four of six conform at a 10 ms budget and the fastest is a decision tree"),

    (r"RAPL|energy per decision|mJ per decision",
     "C15, WITHDRAWN",
     "RAPL cannot attribute socket energy to a container"),

    (r"T_?\{?max\}?\s*<\s*250|T_\{\\text\{max\}\}\s*<\s*250",
     "C11, NOT EXECUTED",
     "that figure was the lowest load tested, i.e. an unbounded statement"),

    (r"due to deployment shift|because of deployment shift",
     "D-004 / D-010 / D-015 mandatory wording",
     "Delta_F1 spans deployment AND exporter; it is an upper bound"),

    (r"real[- ]time conformance|near[- ]real[- ]time conformance|"
     r"conforms? to the near[- ]real[- ]time budget",
     "EXP-031, Track C BLOCKED",
     "all latency figures are EMULATED and support no conformance claim"),

    (r"device[- ]disjoint split",
     "B-010",
     "ue_id has 9 values with one holding 60.8%; the protocol is run-disjoint"),

    (r"\bLSTM\b",
     "never implemented",
     "the only sequence models are the GRU and 1D-CNN of EXP-050"),

    # --- retired in the revision of 2026-09-24 -------------------------------
    (r"worse than guessing|beneath (the|that) floor|below a stratified coin|"
     r"wrong side of chance",
     "D-028 (consequence of D-021)",
     "with balanced weights the MLP scores above the stratified floor on D_B"),

    (r"does not predict transfer rank|close to no information",
     "D-028",
     "six architectures cannot settle the rank correlation; report both metrics"),

    (r"every standard calibration method|cannot change the achievable operating "
     r"points at all",
     "D-029",
     "isotonic and Platt can change the ranking; only temperature preserves it"),

    (r"not ours to choose",
     "simulated review R2.6",
     "B is swept; 10 ms is a declared choice, not a specification fact"),

    (r"n\s*=\s*41|41 papers|Reporting practice across surveyed",
     "D-023, C13 WITHDRAWN",
     "the survey was never run; do not report its counts"),

    (r"calibration failure with an immediate",
     "D-029",
     "the target limit is discriminability, not calibration"),

    (r"statistically unambiguous",
     "D-026",
     "report Nadeau-Bengio corrected intervals; several effects are not significant"),

    (r"order-of-magnitude optimi[sz]ation",
     "EXP-030 speed-up is 2.3x to 12.1x",
     "state the measured range"),

    # ---- round-2 review (2026-09-24) ----
    (r"triples the false[- ]alert|false alerts? (rise|rises) from .* per hour|"
     r"\\DriftFwd|\\DriftFAratio|\\DriftFAtemp|Holding out later capture sessions costs",
     "D-030",
     "EXP-051's drift was unseen categories; report EXP-053 (time split with "
     "category coverage, held-out benign sessions)"),

    (r"no detector reaches 0\.05|no threshold helps even in distribution|"
     r"worst case of its interval",
     "D-031",
     "radio operating points carry cluster-bootstrap intervals that reach 1.0; "
     "say the radio alert burden is not determined"),

    (r"collapse factor is not an artifact of the declared prevalence",
     "round-2 R1 consistency audit",
     "the sweep shows the factor is set by the prevalence"),

    (r"IoT Traffic in O-RAN Edge Data Centers",
     "round-2 R3",
     "the corpora hold no IoT-specific traffic and no edge property is measured"),
]

# Lines that are allowed to mention a forbidden phrase because they are the
# comment recording its removal, or the macro definitions themselves.
#
# A sentence REPORTING that a claim was retired must not itself trip the guard,
# or the honest disclosure becomes unpublishable. The exemption therefore covers
# the vocabulary of withdrawal, not just the word itself.
EXEMPT = re.compile(
    r"^\s*%"                                  # a LaTeX comment
    r"|WITHDRAWN|withdrawn|NOT EXECUTED|not executed"
    r"|CONTRADICTED|contradicted"
    r"|was an artefact|artefact of averaging|did not survive"
    r"|not supportable|is not a split|an earlier version"
    # A sentence DENYING a retired claim must not trip the guard. "We make
    # no near-real-time conformance claim" is the correct disclosure, and an
    # earlier version of this exemption list flagged it as the offence.
    r"|support no |supports no |make no |makes no |we do not claim"
    r"|not a near|no near-real-time|no conformance|never claimed"
    r"|no longer|we do not report|never ran|were never run"
    r"|cannot be made|cannot attribute|must not be reused|do not report")


def scan(path: Path) -> list[tuple[int, str, str, str]]:
    hits = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if EXEMPT.search(line):
            continue
        for pat, retired_by, instead in FORBIDDEN:
            if re.search(pat, line, flags=re.IGNORECASE):
                hits.append((n, line.strip()[:110], retired_by, instead))
    return hits


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "paper/main.tex")
    if not path.exists():
        print("manuscript not found: %s" % path)
        return 1

    hits = scan(path)
    if not hits:
        print("OK: no withdrawn or contradicted claim is asserted in %s" % path)
        print("    %d retired patterns checked" % len(FORBIDDEN))
        return 0

    print("FAIL: %d surviving assertion(s) of retired claims in %s\n"
          % (len(hits), path))
    for n, line, retired_by, instead in hits:
        print("  line %d" % n)
        print("    text        : %s" % line)
        print("    retired by  : %s" % retired_by)
        print("    say instead : %s\n" % instead)
    print("A claim is not withdrawn until no sentence asserts it.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
