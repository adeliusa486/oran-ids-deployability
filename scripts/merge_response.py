#!/usr/bin/env python3
"""Append the highlighted manuscript to the response letter as one PDF.

The letter (paper/r1/response/response_r1.pdf) links every location to a page
of the highlighted manuscript as a link to another file. This script appends
the highlighted manuscript, keeping its yellow highlights and its own links,
and turns every such link into a jump inside the combined file. It also adds
bookmarks and page labels (letter pages R1, R2, ...; manuscript pages 1, 2, ...
as printed on the manuscript).

Usage:  python scripts/merge_response.py LETTER.pdf HIGHLIGHTED.pdf OUT.pdf
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz  # PyMuPDF


def main() -> int:
    letter_p, hl_p, out_p = map(Path, sys.argv[1:4])
    doc = fitz.open(letter_p)
    hl = fitz.open(hl_p)
    n_letter, n_ms = len(doc), len(hl)
    n_hl_annots = sum(len(list(p.annots())) for p in hl)
    doc.insert_pdf(hl, links=True, annots=True)
    # insert_pdf keeps web links but drops the manuscript's named-destination
    # links (citations, section/table/figure references); re-create them.
    have = {(p, tuple(round(v, 1) for v in ln["from"])) for p in range(n_letter, len(doc))
            for ln in doc[p].get_links()}
    readded = 0
    for p in range(n_ms):
        for ln in hl[p].get_links():
            if ln["kind"] not in (fitz.LINK_GOTO, fitz.LINK_NAMED) or not (0 <= ln.get("page", -1) < n_ms):
                continue
            key = (n_letter + p, tuple(round(v, 1) for v in ln["from"]))
            if key in have:
                continue
            doc[n_letter + p].insert_link({"kind": fitz.LINK_GOTO, "from": ln["from"],
                                           "page": n_letter + ln["page"], "to": ln.get("to", fitz.Point(0, 0)),
                                           "zoom": 0})
            readded += 1

    moved, stray = 0, []
    for pno in range(n_letter):
        page = doc[pno]
        for ln in page.get_links():
            if ln["kind"] != fitz.LINK_GOTOR:
                continue
            target = ln["page"]
            if not (0 <= target < n_ms) or Path(ln.get("file", "")).name != hl_p.name:
                stray.append((pno + 1, ln.get("file"), target))
                continue
            page.update_link({"kind": fitz.LINK_GOTO, "xref": ln["xref"], "from": ln["from"],
                              "page": n_letter + target, "to": fitz.Point(0, 0), "zoom": 0})
            moved += 1

    doc.set_toc([[1, "Response to the reviewers", 1],
                 [1, "Revised manuscript (changes for the reviewers highlighted)", n_letter + 1]])
    doc.set_page_labels([{"startpage": 0, "prefix": "R", "style": "D", "firstpagenum": 1},
                         {"startpage": n_letter, "prefix": "", "style": "D", "firstpagenum": 1}])
    meta = doc.metadata or {}
    meta.update(title="Response to the reviewers, Access-2026-49092",
                subject="Response to the reviewers with the highlighted revised manuscript appended")
    doc.set_metadata(meta)
    doc.save(out_p, garbage=3, deflate=True)

    # verify the saved file
    chk = fitz.open(out_p)
    left = sum(1 for p in range(n_letter) for ln in chk[p].get_links() if ln["kind"] == fitz.LINK_GOTOR)
    hl_after = sum(1 for p in range(n_letter, len(chk)) for a in chk[p].annots()
                   if a.type[1] == "Highlight")
    notes = sum(1 for p in range(n_letter, len(chk)) for a in chk[p].annots()
                if a.type[1] == "Highlight" and (a.info.get("content") or a.info.get("title")))
    print(f"manuscript internal links re-created {readded}")
    print(f"letter {n_letter} p + manuscript {n_ms} p = {len(chk)} p; links redirected {moved}; "
          f"external links left {left}; stray {stray}; highlights {hl_after}/{n_hl_annots} kept; "
          f"highlights with note text {notes}")
    return 0 if (left == 0 and not stray and notes == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
