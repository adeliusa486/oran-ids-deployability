#!/usr/bin/env python3
"""Check every entry of paper/references.bib against Crossref (and arXiv).

For an entry with a DOI: resolve it at api.crossref.org and compare the title,
the first author's family name, the year and the author count with the .bib.
For an entry without a DOI: search Crossref by title and first author, and
arXiv by title for e-prints; report the best match so a human can decide.
Only metadata is checked here. Whether a source supports the sentence that
cites it is a reading task, recorded by hand in the audit report.

Usage:  python scripts/verify_references.py [--out reports/reference_check.csv]
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "oran-ids-deployability reference check (mailto:adeelahmada485@gmail.com)"


def get(url: str, timeout: int = 20) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:  # noqa: BLE001 -- network flakiness, retried
            time.sleep(1.5)
    return None


def norm(s: str) -> str:
    s = re.sub(r"[{}\\]", "", s or "")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return re.sub(r"[^a-z0-9 ]", "", s)


def parse_bib(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", text, re.S):
        typ, key, body = m.groups()
        f = {"_type": typ.lower(), "_key": key}
        for k, v in re.findall(r"(\w+)\s*=\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}",
                               body):
            f[k.lower()] = re.sub(r"\s+", " ", v).strip()
        out.append(f)
    return out


def first_family(authors: str) -> str:
    a = (authors or "").split(" and ")[0].strip()
    a = re.sub(r"[{}\\'\"`^~]", "", a)
    return (a.split(",")[0] if "," in a else a.split(" ")[-1]).strip().lower()


def crossref_doi(doi: str) -> dict | None:
    raw = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    if not raw:
        return None
    return json.loads(raw)["message"]


def crossref_search(title: str, author: str) -> dict | None:
    q = urllib.parse.urlencode({"query.bibliographic": title, "query.author": author,
                                "rows": 1})
    raw = get("https://api.crossref.org/works?" + q)
    if not raw:
        return None
    items = json.loads(raw)["message"]["items"]
    return items[0] if items else None


def arxiv_search(title: str) -> dict | None:
    q = urllib.parse.urlencode({"search_query": 'ti:"%s"' % title[:200],
                                "max_results": 1})
    raw = get("http://export.arxiv.org/api/query?" + q)
    if not raw:
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = ET.fromstring(raw).find("a:entry", ns)
    if e is None:
        return None
    return {"title": e.findtext("a:title", "", ns), "id": e.findtext("a:id", "", ns),
            "published": e.findtext("a:published", "", ns),
            "authors": [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)]}


def year_of(msg: dict) -> str:
    for k in ("published-print", "published-online", "issued", "published"):
        d = msg.get(k, {}).get("date-parts")
        if d and d[0] and d[0][0]:
            return str(d[0][0])
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/reference_check.csv")
    args = ap.parse_args()
    bib = parse_bib((ROOT / "paper/references.bib").read_text(encoding="utf-8"))
    rows = []
    for e in bib:
        key, title = e["_key"], e.get("title", "")
        fam = first_family(e.get("author", ""))
        n_auth = len([a for a in e.get("author", "").split(" and ") if a.strip()])
        rec = dict(key=key, bib_year=e.get("year", ""), bib_doi=e.get("doi", ""),
                   bib_first_author=fam, bib_n_authors=n_auth, title=title[:90])
        if e.get("doi"):
            m = crossref_doi(e["doi"])
            if m is None:
                rec.update(check="DOI_NOT_RESOLVED")
            else:
                t = (m.get("title") or [""])[0]
                sim = difflib.SequenceMatcher(None, norm(t), norm(title)).ratio()
                auths = m.get("author", [])
                cf = (auths[0].get("family", "") if auths else "").lower()
                rec.update(cr_title=t[:90], title_sim=round(sim, 3), cr_year=year_of(m),
                           cr_first_author=cf, cr_n_authors=len(auths),
                           cr_venue=(m.get("container-title") or [""])[0][:60])
                ok = (sim > 0.9 and rec["cr_year"] == e.get("year", "")
                      and norm(cf) in norm(fam) + norm(e.get("author", "")))
                rec["check"] = "OK" if ok else "MISMATCH"
        else:
            m = crossref_search(title, fam)
            best = None
            if m:
                t = (m.get("title") or [""])[0]
                sim = difflib.SequenceMatcher(None, norm(t), norm(title)).ratio()
                best = dict(cr_title=t[:90], title_sim=round(sim, 3), cr_year=year_of(m),
                            cr_doi=m.get("DOI", ""),
                            cr_venue=(m.get("container-title") or [""])[0][:60])
            if (best is None or best["title_sim"] < 0.9) and (
                    "arxiv" in json.dumps(e).lower() or e["_type"] == "misc"):
                a = arxiv_search(re.sub(r"[{}]", "", title))
                if a:
                    sim = difflib.SequenceMatcher(None, norm(a["title"]), norm(title)).ratio()
                    if best is None or sim > best["title_sim"]:
                        best = dict(cr_title=a["title"][:90], title_sim=round(sim, 3),
                                    cr_year=a["published"][:4], cr_doi=a["id"],
                                    cr_venue="arXiv")
            rec.update(best or {})
            rec["check"] = ("FOUND_NO_DOI_IN_BIB" if best and best["title_sim"] >= 0.9
                            else "NOT_FOUND")
        rows.append(rec)
        print(f"{rec['check']:20s} {key}")
        time.sleep(0.25)
    cols = sorted({k for r in rows for k in r}, key=lambda c: (c != "key", c))
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
