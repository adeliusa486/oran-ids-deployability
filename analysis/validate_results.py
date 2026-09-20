#!/usr/bin/env python3
"""Phase 14 validation gate.

Refuses to let bad results reach figure generation. Exits non-zero on any
failure so `make paper` cannot silently produce a misleading plot.

The placeholder-leakage check exists because this manuscript began life with
fully synthetic numbers; a leftover value must fail the build, not survive it.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Values from the synthetic draft. If a computed metric lands exactly on one of
# these, it is far more likely a leftover than a coincidence.
SYNTHETIC_SENTINELS = {
    99.25, 99.03, 98.22, 98.88, 98.66,
    71.39, 68.34, 63.48, 66.21, 61.61,
    27.86, 30.69, 34.74, 32.67, 37.05,
    0.187, 0.021, 74.16, 58.91, 96.94,
}

CHECKS = [
    "missing_runs", "duplicate_runs", "nan_or_inf", "out_of_range",
    "inconsistent_n", "crashed_runs", "stale_artefacts", "placeholder_leakage",
]


def fail(check: str, detail: str) -> None:
    print(f"FAIL [{check}] {detail}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", default="results/raw")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    raw = Path(args.indir)
    if not raw.exists() or not any(raw.rglob("*.parquet")):
        fail("missing_runs", f"no result files under {raw}")
        print("\nNothing to validate. Run experiments first (make experiments-track-a).")
        return 1

    raise NotImplementedError(
        "Implement the checks listed in IMPLEMENTATION_PLAN.md section 18.1:\n  - "
        + "\n  - ".join(CHECKS)
        + "\n\nEach must exit non-zero. Do not soften any of them into a warning."
    )


if __name__ == "__main__":
    sys.exit(main())
