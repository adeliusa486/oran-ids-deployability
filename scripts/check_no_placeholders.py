#!/usr/bin/env python3
"""Fail the build if any synthetic-draft marker survives into the manuscript.

Wire into CI. This is the structural guard that a placeholder cannot be
mistaken for a measurement.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

PATTERNS = {
    r"\\syn\{": "synthetic-value macro",
    r"\[SYNTHETIC\]": "synthetic block marker",
    r"\\synthdrafttrue": "draft banner still enabled",
    r"\bTBD\b": "TBD placeholder",
    r"\bXXX\b": "XXX placeholder",
    r"\[MEASURED [A-Z ]+\]": "unfilled abstract placeholder",
}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_no_placeholders.py <file.tex> [...]", file=sys.stderr)
        return 2

    bad = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"FAIL missing file: {path}", file=sys.stderr)
            bad += 1
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if line.lstrip().startswith("%"):
                continue
            for pat, desc in PATTERNS.items():
                if re.search(pat, line):
                    print(f"FAIL {path}:{lineno}: {desc}", file=sys.stderr)
                    bad += 1

    if bad:
        print(f"\n{bad} placeholder(s) remain. The paper is not submittable.", file=sys.stderr)
        return 1
    print("OK: no placeholders found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
