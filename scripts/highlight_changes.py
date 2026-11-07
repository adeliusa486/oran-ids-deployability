#!/usr/bin/env python3
"""Mark every change of a revised manuscript with yellow PDF highlights.

IEEE Access asks for "your updated manuscript with all your individual changes
highlighted, including grammatical changes (preferably with the yellow
highlight tool within the pdf file)". This script compares the words of the
submitted PDF with those of the revised PDF and adds a yellow highlight
annotation (the same object a PDF reader's highlight tool creates) over every
word of the revised PDF that is new or changed. Text in tables and in figures
with real text (TikZ, matplotlib with embedded fonts) is compared too.

  * words are compared in reading order after normalisation: hyphenation at
    line ends is undone, ligatures and typographic quotes are folded, and
    case is kept (a changed capital is a change);
  * difflib's matcher aligns the two word sequences; words in 'insert' and
    'replace' blocks are highlighted, one annotation per run of words on a
    line;
  * deletions cannot be shown in the revised PDF; the response letter lists
    them.

Usage:  python scripts/highlight_changes.py OLD.pdf NEW.pdf OUT.pdf [--report report.json]
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata

import fitz  # PyMuPDF

YELLOW = (1.0, 0.92, 0.23)
FOLD = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
        "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-",
        "—": "-", "−": "-", " ": " "}


def norm(w: str) -> str:
    w = unicodedata.normalize("NFKC", "".join(FOLD.get(ch, ch) for ch in w))
    return w.strip()


def words(doc):
    """[(token, page, rect)] in reading order, hyphenation at line ends undone."""
    out = []
    for pno, page in enumerate(doc):
        ws = page.get_text("words", sort=True)     # x0 y0 x1 y1 word block line wno
        for w in ws:
            t = norm(w[4])
            if t:
                out.append([t, pno, fitz.Rect(w[:4]), (w[5], w[6])])
    merged = []
    i = 0
    while i < len(out):
        t, p, r, ln = out[i]
        if (t.endswith("-") and len(t) > 2 and i + 1 < len(out)
                and out[i + 1][3] != ln and re.match(r"[a-z]", out[i + 1][0])):
            nxt = out[i + 1]
            merged.append((t[:-1] + nxt[0], [(p, r), (nxt[1], nxt[2])]))
            i += 2
            continue
        merged.append((t, [(p, r)]))
        i += 1
    return merged


def runs(rects):
    """Merge rectangles of consecutive words that lie on one line."""
    out = []
    for p, r in rects:
        if out and out[-1][0] == p and abs(out[-1][1].y0 - r.y0) < 2 and \
                abs(out[-1][1].y1 - r.y1) < 2 and r.x0 - out[-1][1].x1 < 12:
            out[-1][1] |= r
        else:
            out.append([p, fitz.Rect(r)])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("out")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    old = fitz.open(a.old)
    new = fitz.open(a.new)
    wo = words(old)
    wn = words(new)
    sm = difflib.SequenceMatcher(None, [w[0] for w in wo], [w[0] for w in wn], autojunk=False)
    marked = []
    n_changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("insert", "replace"):
            for j in range(j1, j2):
                marked.extend(wn[j][1])
            n_changed += j2 - j1
    by_page = {}
    for p, r in runs(marked):
        by_page.setdefault(p, []).append(r)
    n_annots = 0
    for p, rects in by_page.items():
        page = new[p]
        for r in rects:
            annot = page.add_highlight_annot(r)
            annot.set_colors(stroke=YELLOW)
            annot.set_info(title="Revision 1", content="changed or new in the revision")
            annot.update()
            n_annots += 1
    new.save(a.out, garbage=3, deflate=True)
    rep = dict(old_words=len(wo), new_words=len(wn), new_or_changed_words=n_changed,
               share_changed=round(n_changed / max(len(wn), 1), 3), annotations=n_annots,
               pages=len(new), ratio=round(sm.ratio(), 3))
    print(json.dumps(rep, indent=1))
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
