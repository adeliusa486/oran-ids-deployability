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


def _tex_setup():
    """The paper uses the official IEEE Access class, kept with its fonts and
    logos in paper/access/. MiKTeX takes -include-directory; TeX Live reads the
    kpathsea search-path variables (a trailing separator keeps the defaults)."""
    ver = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True,
                         errors="ignore").stdout
    if "MiKTeX" in ver:
        return ["-include-directory=access"], None
    env = dict(os.environ)
    add = "." + os.pathsep + str(PAPER / "access") + "//" + os.pathsep
    for var in ("TEXINPUTS", "TFMFONTS", "T1FONTS", "TEXFONTMAPS", "ENCFONTS", "BSTINPUTS"):
        env[var] = add + env.get(var, "")
    return [], env


def run(cmd, env=None):
    return subprocess.run(cmd, cwd=PAPER, capture_output=True, text=True,
                          errors="ignore", env=env)


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
        extra, env = _tex_setup()
        tex = ["pdflatex", *extra, "-interaction=nonstopmode", "main.tex"]
        for cmd in (tex, ["bibtex", "main"], tex, tex):
            run(cmd, env)
    finally:
        for p in procs:
            p.resume()
        if procs:
            with log.open("a", encoding="utf-8") as fh:
                fh.write(f"{dt.datetime.now().isoformat(timespec='seconds')} resumed\n")
    text = (PAPER / "main.log").read_text(encoding="utf-8", errors="ignore")
    errors = re.findall(r"^! .*", text, re.M)
    undef = re.findall(r"(Citation|Reference) `[^']+' on page \d+ undefined", text)
    # "while \output is active" overfulls come from the IEEE Access page header
    # (the untouched sample access.tex produces the same ones); they are not ours
    over = re.findall(r"Overfull \\hbox \((\d+\.\d+)pt too wide\)(?! has occurred while)", text)
    big = [float(o) for o in over if float(o) > 10]
    pages = re.search(r"Output written on main\.pdf \((\d+) pages", text)
    print(f"pages: {pages.group(1) if pages else 'NO PDF'}")
    print(f"errors: {len(errors)}  undefined refs/cites: {len(undef)}  "
          f"overfull boxes > 10pt: {len(big)}")
    for e in errors[:10]:
        print("  ", e)
    for u in sorted(set(undef))[:10]:
        print("  undefined:", u)
    # BibTeX problems (a broken entry prints as an empty reference, which LaTeX
    # does not report): count warnings and errors in main.blg
    blg = (PAPER / "main.blg").read_text(encoding="utf-8", errors="ignore") \
        if (PAPER / "main.blg").exists() else ""
    bibwarn = re.findall(r"^Warning--.*", blg, re.M)
    biberr = re.search(r"\(There (?:was|were) (\d+) error", blg)
    nbiberr = int(biberr.group(1)) if biberr else 0
    print(f"bibtex warnings: {len(bibwarn)}  bibtex errors: {nbiberr}")
    for w in bibwarn[:10]:
        print("  ", w)
    return 0 if pages and not errors and not undef and not bibwarn and not nbiberr else 1


if __name__ == "__main__":
    sys.exit(main())
