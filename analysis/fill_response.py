#!/usr/bin/env python3
"""Fill the response-to-reviewers template from the compiled manuscript.

[[label]] becomes "Section VI-A", "Table V", "Fig. 3" or "Eq. (7)", read from
paper/main.aux; [[N:Macro]] becomes the value defined in
tables/generated/numbers.tex. An unresolved placeholder is an error: a response
letter must not quote a number or a reference the manuscript does not contain.

Usage:  python analysis/fill_response.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "reports" / "response_to_reviewers_template.md"
OUT = ROOT / "reports" / "response_to_reviewers_2026-09-24.md"


def labels() -> dict[str, str]:
    aux = (ROOT / "paper" / "main.aux").read_text(encoding="utf-8", errors="ignore")
    out = {}
    for key, num in re.findall(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}", aux):
        if key.startswith("sec:"):
            out[key] = f"Section {num}"
        elif key.startswith("tab:"):
            out[key] = f"Table {num}"
        elif key.startswith("fig:"):
            out[key] = f"Fig. {num}"
        elif key.startswith("eq:"):
            out[key] = f"Eq. ({num})"
        elif key.startswith("alg:"):
            out[key] = f"Algorithm {num}"
    return out


def macros() -> dict[str, str]:
    t = (ROOT / "tables" / "generated" / "numbers.tex").read_text(encoding="utf-8")
    out = {}
    for name, val in re.findall(r"\\newcommand\{\\(\w+)\}\{(.*?)\}(?:\s*%.*)?$", t, re.M):
        out[name] = val.replace("{,}", ",").replace("\\,", " ").replace("\\", "")
    tex = (ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    abstract = tex.split("\\begin{abstract}")[1].split("\\end{abstract}")[0]
    out["AbstractWords"] = str(len(abstract.split()))
    return out


def main() -> int:
    L, M = labels(), macros()
    text = TEMPLATE.read_text(encoding="utf-8")
    missing = []

    def sub(m):
        key = m.group(1)
        if key.startswith("N:"):
            v = M.get(key[2:])
        else:
            v = L.get(key)
        if v is None:
            missing.append(key)
            return m.group(0)
        return v

    filled = re.sub(r"\[\[([^\]]+)\]\]", sub, text)
    if missing:
        print("UNRESOLVED:", sorted(set(missing)))
        return 1
    OUT.write_text(filled, encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
