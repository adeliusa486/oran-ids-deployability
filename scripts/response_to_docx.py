#!/usr/bin/env python3
"""Make a Word copy of the response letter with every reference resolved.

The response letter (paper/r1/response/response_r1.tex) cites the revised
manuscript's sections, tables, figures and pages through xr-hyper. pandoc
cannot follow those, so this script writes a resolved copy first: \\Sec, \\Tab,
\\Fig and \\Pg are replaced by the numbers in the manuscript's main.aux, the
number macros are inlined so pandoc can expand them, and the boxed reviewer
comments become quotations. pandoc then writes the .docx.

Usage:  python scripts/response_to_docx.py MAIN_AUX OUT.docx
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESP = ROOT / "paper" / "r1" / "response"


def _group(s: str, i: int) -> tuple[str, int]:
    """The balanced brace group starting at s[i] == '{'; returns (content, end)."""
    assert s[i] == "{"
    depth = 0
    for j in range(i, len(s)):
        depth += {"{": 1, "}": -1}.get(s[j], 0)
        if depth == 0:
            return s[i + 1:j], j + 1
    raise ValueError("unbalanced")


def labels(aux: Path) -> dict:
    out = {}
    for line in aux.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\\newlabel\{([^}]+)\}\{", line)
        if not m:
            continue
        outer, _ = _group(line, m.end() - 1)
        num, k = _group(outer, 0)
        page, _ = _group(outer, k)
        num = re.sub(r"\\mbox\s*", "", num).replace("{", "").replace("}", "").strip()
        out[m.group(1)] = (num, page)
    return out


def main() -> int:
    aux, out_docx = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    L = labels(aux)
    body = (RESP / "response_r1.tex").read_text(encoding="utf-8")
    body = re.sub(r"\\input\{(response_body[^}]*)\}",
                  lambda m: (RESP / (m.group(1) + ".tex")).read_text(encoding="utf-8"), body)
    body = re.sub(r"\\input\{(response_body[^}]*)\}",
                  lambda m: (RESP / (m.group(1) + ".tex")).read_text(encoding="utf-8"), body)
    numbers = (ROOT / "paper/r1/numbers_r1.tex").read_text(encoding="utf-8")
    body = body[body.index("\\begin{document}"):]      # macro definitions stay out

    def num(key):
        v = L.get(key)
        if v is None:
            raise KeyError(f"label {key} not in {aux}")
        return v

    # The Word copy cannot carry the appended manuscript, so locations are
    # plain text with the page number (the PDF letter has the links).
    def loc(kind, key):
        n, p = num(key)
        return kind + n + " (p. " + p + ")"

    body = re.sub(r"\\Sec\{([^}]+)\}", lambda m: loc("Section ", m.group(1)), body)
    body = re.sub(r"\\Tab\{([^}]+)\}", lambda m: loc("Table ", m.group(1)), body)
    body = re.sub(r"\\Fig\{([^}]+)\}", lambda m: loc("Fig. ", m.group(1)), body)
    body = re.sub(r"\\Pg\{([^}]+)\}", lambda m: "p. " + num(m.group(1))[1], body)
    body = body.replace("\\Abs", "Abstract (p. 1)")
    body = body.replace(
        "For convenience, the revised manuscript, with the changes made in response to the reviewers "
        "highlighted in yellow, is appended to this letter. Each concern heading, and each section, table, "
        "figure and page we cite, is a link to the corresponding page of the appended manuscript; page "
        "numbers refer to the revised manuscript.",
        "Section, table, figure and page numbers refer to the revised manuscript; the changes made in "
        "response to the reviewers are highlighted in yellow in the Highlighted PDF.")
    if "appended to this letter" in body:
        raise SystemExit("response_to_docx: the letter's sentence about the appended manuscript changed; update it here")
    body = body.replace(", and each location in the last column links to that page of the appended manuscript.",
                        "; the last column gives the location in the revised manuscript.")
    body = re.sub(r"Fig\.~\\ref\{M-([^}]+)\}", lambda m: "Fig. " + num(m.group(1))[0], body)
    body = re.sub(r"Table~\\ref\{M-([^}]+)\}", lambda m: "Table " + num(m.group(1))[0], body)
    body = re.sub(r"\\ref\{M-([^}]+)\}", lambda m: num(m.group(1))[0], body)

    def concern(m):
        r, c = re.match(r"R(\d)\.(\d+)", m.group(1)).groups()
        return "\\subsection*{Reviewer \\#" + r + ", Concern \\#" + c + "}\n\\begin{quote}\\itshape "
    body = re.sub(r"\\begin\{concern\}\{([^}]*)\}", concern, body)
    body = body.replace("\\end{concern}", "\\end{quote}")
    # preamble: keep the document; drop packages pandoc does not need
    start = 0
    pre = ("\\documentclass{article}\n"
           "\\newcommand{\\DA}{$\\mathcal{D}_{A}$}\n\\newcommand{\\DB}{$\\mathcal{D}_{B}$}\n"
           "\\newcommand{\\DC}{$\\mathcal{D}_{C}$}\n"
           "\\newcommand{\\response}{\\par\\textbf{Author response:} }\n"
           "\\newcommand{\\action}{\\par\\textbf{Author action:} }\n")
    numbers = numbers.replace("\\mbox", "")
    tex = pre + numbers + "\n" + body[start:]
    tmp = RESP / "_resolved_for_docx.tex"
    tmp.write_text(tex, encoding="utf-8")
    cmd = ["pandoc", str(tmp.name), "-f", "latex", "-t", "docx", "-o", str(out_docx)]
    ref = RESP / "ieee_access_response_template.docx"      # official IEEE Access template
    if ref.exists():
        cmd += ["--reference-doc", str(ref)]
    r = subprocess.run(cmd, cwd=RESP, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[:2000])
        return 1
    print(f"wrote {out_docx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
