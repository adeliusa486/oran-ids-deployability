#!/usr/bin/env python3
"""Build paper/main.pdf: pdflatex -> bibtex -> pdflatex -> pdflatex.

If a latency measurement (run_latency_v2.py or run_extraction_real.py) is
running, it is suspended for the few seconds of the build and resumed
afterwards, so the compile does not contaminate its tail quantiles. The
suspended interval inflates at most the one call in flight; the fact is
written to results/EXP-043/logs/suspensions.log.

Usage:  python scripts/build_paper.py
Exit:   0 on a clean build; 1 if LaTeX reported errors or undefined references.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
TIMING = ("run_latency_v2.py", "run_extraction_real.py")


def timing_procs():
    try:
        import psutil
    except ImportError:
        return []
    me = os.getpid()
    out = []
    for p in psutil.process_iter(["pid", "cmdline"]):
        if p.pid == me or not p.info["cmdline"]:
            continue
        if any(c.endswith(TIMING) for c in p.info["cmdline"]):
            out.append(p)
    return out


def run(cmd):
    return subprocess.run(cmd, cwd=PAPER, capture_output=True, text=True,
                          errors="ignore")


def main() -> int:
    procs = timing_procs()
    log = ROOT / "results/EXP-043/logs/suspensions.log"
    for p in procs:
        p.suspend()
    if procs:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"{dt.datetime.now().isoformat(timespec='seconds')} suspended "
                     f"{[p.pid for p in procs]} for a paper build\n")
    try:
        for cmd in (["pdflatex", "-interaction=nonstopmode", "main.tex"],
                    ["bibtex", "main"],
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                    ["pdflatex", "-interaction=nonstopmode", "main.tex"]):
            run(cmd)
    finally:
        for p in procs:
            p.resume()
        if procs:
            with log.open("a", encoding="utf-8") as fh:
                fh.write(f"{dt.datetime.now().isoformat(timespec='seconds')} resumed\n")
    text = (PAPER / "main.log").read_text(encoding="utf-8", errors="ignore")
    errors = re.findall(r"^! .*", text, re.M)
    undef = re.findall(r"(Citation|Reference) `[^']+' on page \d+ undefined", text)
    over = re.findall(r"Overfull \\hbox \((\d+\.\d+)pt too wide\)", text)
    big = [float(o) for o in over if float(o) > 10]
    pages = re.search(r"Output written on main\.pdf \((\d+) pages", text)
    print(f"pages: {pages.group(1) if pages else 'NO PDF'}")
    print(f"errors: {len(errors)}  undefined refs/cites: {len(undef)}  "
          f"overfull boxes > 10pt: {len(big)}")
    for e in errors[:10]:
        print("  ", e)
    for u in sorted(set(undef))[:10]:
        print("  undefined:", u)
    return 0 if pages and not errors and not undef else 1


if __name__ == "__main__":
    sys.exit(main())
