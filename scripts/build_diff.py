#!/usr/bin/env python3
"""Build paper/diff.pdf: track changes from the reviewed manuscript to main.tex.

latexdiff needs the Perl module Algorithm::Diff, which Git's Perl lacks on this
host; pass its directory with --perl-lib (the pure-Perl file from CPAN,
Algorithm-Diff 1.201, lib/Algorithm/Diff.pm).

Three fixes are applied to latexdiff's output, each for a reproducible failure:
  * the reviewed draft's \\measured{} and \\syn{} macros, used by deleted text,
    are defined in the preamble;
  * the inlined bibliography, which latexdiff marks up and breaks, is replaced
    by \\bibliography{references} and bibtex is run;
  * colour-only markup (CFONT) is used, because ulem strike-out inside a deleted
    \\subsection raises "Improper \\prevdepth".
Tables, algorithms, TikZ pictures and multi-line equations are compared as
whole blocks (old shown deleted, new shown added).

Usage:  python scripts/build_diff.py --perl-lib /c/path/to/perl5
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
LATEXDIFF = "/c/Users/adeel/AppData/Local/Programs/MiKTeX/scripts/latexdiff/latexdiff"


def _no_blank_lines_in_captions(tex: str) -> str:
    out, lines, depth = [], tex.split("\n"), 0
    for ln in lines:
        if depth > 0 and ln.strip() == "":
            continue
        code = ln
        k = 0
        while True:  # strip an unescaped comment
            k = code.find("%", k)
            if k < 0:
                break
            if k == 0 or code[k - 1] != "\\":
                code = code[:k]
                break
            k += 1
        if depth == 0:
            c = code.find("\\caption{")
            if c >= 0:
                depth = 0
                seg = code[c + len("\\caption"):]
                for ch in seg:
                    depth += (ch == "{") - (ch == "}")
                    if depth == 0:
                        break
                depth = max(depth, 0)
        else:
            for ch in code:
                depth += (ch == "{") - (ch == "}")
                if depth <= 0:
                    depth = 0
                    break
        out.append(ln)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perl-lib", required=True)
    ap.add_argument("--old", default="_original/main_reviewed.tex")
    a = ap.parse_args()
    (PAPER / "_old.tex").write_text((PAPER / a.old).read_text(encoding="utf-8"),
                                    encoding="utf-8")
    cmd = ["perl", "-I", a.perl_lib, LATEXDIFF, "--flatten", "--type=CFONT",
           "--exclude-textcmd=caption",  # round 2: inline markup broke captions
           "--math-markup=0", "--disable-citation-markup",
           "--config=PICTUREENV=(?:picture|DIFnomarkup|tabular|algorithmic|"
           "tikzpicture|split|equation)[\\w\\d*@]*",
           "_old.tex", "main.tex"]
    r = subprocess.run(cmd, cwd=PAPER, capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(r.stderr[-2000:])
        return 1
    tex = r.stdout
    tex = tex.replace("\\begin{document}",
                      "\\providecommand{\\measured}[1]{#1}\n"
                      "\\providecommand{\\syn}[1]{#1}\n\\begin{document}", 1)
    # Replace the inlined bibliography (and latexdiff's markup of it).
    start = tex.find("\\begin{thebibliography}")
    end = tex.rfind("\\end{thebibliography}")
    if start != -1 and end != -1 and start < end:
        start = tex.rfind("\n", 0, start) + 1
        tex = (tex[:start] + "\\bibliography{references}\n"
               + tex[end + len("\\end{thebibliography}"):])
    if "\\bibliographystyle" not in tex:
        tex = tex.replace("\\bibliography{references}",
                          "\\bibliographystyle{IEEEtran}\n\\bibliography{references}", 1)
    # round 2: when latexdiff pairs a new caption with an old one, deleted old
    # paragraphs leave blank lines inside the \caption argument, which ends the
    # argument ("File ended while scanning use of \@xdblarg"). Remove blank lines
    # inside every \caption{...}, counting braces outside comments.
    tex = _no_blank_lines_in_captions(tex)
    # latexdiff marks the value of the class's \titlepgskip=-21pt as added text,
    # which breaks the assignment; put the plain assignment back
    tex = re.sub(r"\\titlepgskip\\DIFadd\{=(-?[\d.]+pt)\s*\}", r"\\titlepgskip=\1", tex)
    (PAPER / "diff.tex").write_text(tex, encoding="utf-8")
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_paper import _tex_setup  # the IEEE Access class lives in paper/access
    extra, env = _tex_setup()
    tex_cmd = ["pdflatex", *extra, "-interaction=nonstopmode", "diff.tex"]
    for step in (tex_cmd, ["bibtex", "diff"], tex_cmd, tex_cmd):
        try:
            subprocess.run(step, cwd=PAPER, capture_output=True, timeout=300, env=env)
        except subprocess.TimeoutExpired:
            print(f"timed out: {' '.join(step)}")
            return 1
    log = (PAPER / "diff.log").read_text(encoding="utf-8", errors="ignore")
    errors = re.findall(r"^! .*", log, re.M)
    pages = re.search(r"Output written on diff\.pdf \((\d+) pages", log)
    print(f"diff.pdf pages: {pages.group(1) if pages else 'NO PDF'}; "
          f"errors: {len(errors)}")
    for e in sorted(set(errors))[:10]:
        print("  ", e)
    return 0 if pages and not errors else 1


if __name__ == "__main__":
    sys.exit(main())
