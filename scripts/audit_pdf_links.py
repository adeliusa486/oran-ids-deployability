#!/usr/bin/env python3
"""Audit the hyperlinks in paper/main.pdf.

  * every citation link ("cite.<key>") must land on the page that holds that
    key's bibliography item, and every cited key must have a link;
  * every cross-reference link (figure, table, section, equation, algorithm)
    must resolve to a destination;
  * every external link is listed with its target; DOI links are checked to
    match a DOI in paper/references.bib; the repository link is listed.

Usage:  python scripts/audit_pdf_links.py [--check-web]
Output: reports/pdf_links_2026-09-25.json
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    d = fitz.open(ROOT / "paper/main.pdf")
    bbl = (ROOT / "paper/main.bbl").read_text(encoding="utf-8")
    keys = re.findall(r"\\bibitem\{([^}]+)\}", bbl)
    dests = d.resolve_names() if hasattr(d, "resolve_names") else {}
    internal, external, broken = Counter(), [], []
    cite_targets = {}
    for pno, page in enumerate(d, start=1):
        for ln in page.get_links():
            if ln["kind"] == fitz.LINK_URI:
                external.append(dict(page=pno, uri=ln["uri"]))
            elif ln["kind"] in (fitz.LINK_NAMED, fitz.LINK_GOTO):
                name = ln.get("nameddest") or ln.get("name") or ""
                kind = name.split(".")[0] if name else "goto"
                internal[kind] += 1
                if name.startswith("cite."):
                    tgt = dests.get(name, {}).get("page")
                    cite_targets.setdefault(name[5:], set()).add(tgt)
                    if tgt is None:
                        broken.append(dict(page=pno, name=name))
                elif name and name not in dests:
                    broken.append(dict(page=pno, name=name))
    # where does each bibliography item sit? find the "[n]" label page
    bib_page = {}
    for pno, page in enumerate(d, start=1):
        txt = page.get_text()
        if "REFERENCES" in txt or bib_page:
            for i, k in enumerate(keys, start=1):
                if k not in bib_page and re.search(rf"\[{i}\]", txt):
                    bib_page[k] = pno
    wrong = []
    for k, pages in cite_targets.items():
        # resolve_names pages are 0-based
        pg = {p + 1 for p in pages if p is not None}
        if k in bib_page and bib_page[k] not in pg:
            wrong.append(dict(key=k, link_page=sorted(pg), bib_page=bib_page[k]))
    missing = [k for k in keys if k not in cite_targets]
    bibdoi = set(re.findall(r"doi\s*=\s*\{([^}]+)\}", (ROOT / "paper/references.bib").read_text(encoding="utf-8")))
    doi_links = [e for e in external if "doi.org/" in e["uri"]]
    bad_doi = [e for e in doi_links if e["uri"].split("doi.org/", 1)[1] not in bibdoi]
    web = {}
    if "--check-web" in sys.argv:
        for u in sorted({e["uri"] for e in external if "doi.org/" not in e["uri"]}):
            try:
                req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}, method="GET")
                with urllib.request.urlopen(req, timeout=30) as r:
                    web[u] = r.status
            except Exception as e:  # noqa: BLE001
                web[u] = str(getattr(e, "code", e))[:40]
    res = dict(bib_items=len(keys), cited_keys_with_links=len(cite_targets),
               cite_links_missing_for=missing, cite_links_wrong_page=wrong,
               internal_link_counts=dict(internal), broken_internal=broken,
               external_links=len(external), doi_links=len(doi_links),
               doi_links_not_in_bib=bad_doi, other_urls=sorted({e["uri"] for e in external if "doi.org/" not in e["uri"]}),
               web_status=web)
    out = ROOT / "reports/pdf_links_2026-09-25.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k, v in res.items():
        if k not in ("other_urls", "web_status"):
            print(f"{k}: {v}")
    print("other URLs:")
    for u in res["other_urls"]:
        print("  ", u, web.get(u, ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
