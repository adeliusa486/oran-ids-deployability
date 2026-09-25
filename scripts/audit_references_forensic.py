#!/usr/bin/env python3
"""Forensic check of paper/references.bib against independent records.

For every entry that the paper cites:
  * doi.org      does the DOI resolve (HTTP status, final host)?
  * Crossref     title + subtitle, ordered author list, container, type, year,
                 volume, issue, pages (entries with a DOI);
  * OpenAlex     second, independent record: ordered author list, title, year,
                 venue, type (by DOI, or by title search when there is no DOI);
and compares the ordered author lists position by position (family names,
accents folded, then initials of given names).

Only metadata is checked. Whether each source supports its sentence is read by
hand and recorded in reports/reference_forensics_2026-09-25.md.

Usage:  python scripts/audit_references_forensic.py
Output: reports/reference_forensics_2026-09-25.json
"""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "oran-ids reference forensics (mailto:adeelahmada485@gmail.com)"}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2)
        except Exception:  # noqa: BLE001
            time.sleep(2)
    return None


def doi_resolves(doi):
    """HEAD-style check at doi.org without following the redirect."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    op = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request("https://doi.org/" + urllib.parse.quote(doi, safe="/"),
                                 headers=UA, method="GET")
    try:
        r = op.open(req, timeout=30)
        return r.status, r.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location", "")
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:80]


def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[{}\\'\"`^~]", "", s)
    return re.sub(r"[^a-z]", "", s.lower())


def tex_to_text(s):
    s = re.sub(r"\\[\"'`^~]\{?([A-Za-z])\}?", r"\1", s or "")
    s = s.replace("{\\i}", "i")
    return re.sub(r"[{}]", "", s)


def parse_bib(text):
    out = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", text, re.S):
        typ, key, body = m.groups()
        f = {"_type": typ.lower(), "_key": key}
        for k, v in re.findall(r"(\w+)\s*=\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}", body):
            f[k.lower()] = re.sub(r"\s+", " ", v).strip()
        out.append(f)
    return out


def bib_authors(s):
    res = []
    for a in (s or "").split(" and "):
        a = tex_to_text(a.strip())
        if not a:
            continue
        if "," in a:
            fam, given = a.split(",", 1)
        else:
            parts = a.split()
            fam, given = parts[-1], " ".join(parts[:-1])
        res.append((fam.strip(), given.strip()))
    return res


def initials(given):
    return "".join(w[0].lower() for w in re.split(r"[\s.\-]+", given) if w)


def compare(bib, off):
    """Position-by-position comparison of two ordered author lists."""
    issues = []
    n = max(len(bib), len(off))
    for i in range(n):
        b = bib[i] if i < len(bib) else None
        o = off[i] if i < len(off) else None
        if b is None:
            issues.append(f"missing author {i+1}: {o[1]} {o[0]}")
            continue
        if o is None:
            issues.append(f"extra author {i+1}: {b[1]} {b[0]}")
            continue
        if fold(b[0]) != fold(o[0]):
            # family names differ: same person with a split surname, or another person
            if fold(b[0]) in fold(o[1] + o[0]) or fold(o[0]) in fold(b[1] + b[0]):
                issues.append(f"name form {i+1}: bib '{b[1]} {b[0]}' vs record '{o[1]} {o[0]}'")
            else:
                issues.append(f"MISMATCH {i+1}: bib '{b[1]} {b[0]}' vs record '{o[1]} {o[0]}'")
        elif o[1] and b[1] and initials(b[1])[:1] != initials(o[1])[:1]:
            issues.append(f"initial {i+1}: bib '{b[1]}' vs record '{o[1]}'")
    return issues


def crossref(doi):
    m = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/"))
    if not m:
        return None
    m = m["message"]
    year = None
    for k in ("published-print", "published-online", "issued"):
        d = m.get(k, {}).get("date-parts")
        if d and d[0] and d[0][0]:
            year = d[0][0]
            break
    return dict(title=(m.get("title") or [""])[0], subtitle=(m.get("subtitle") or [""])[0],
                authors=[(a.get("family", a.get("name", "")), a.get("given", ""))
                         for a in m.get("author", [])],
                container=(m.get("container-title") or [""])[0], type=m.get("type"),
                year=year, volume=m.get("volume"), issue=m.get("issue"),
                page=m.get("page"), article=m.get("article-number"),
                publisher=m.get("publisher"))


def openalex(doi=None, title=None):
    if doi:
        w = get_json("https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(doi, safe="/"))
    else:
        q = urllib.parse.quote(re.sub(r"[^\w\s-]", " ", title)[:200])
        r = get_json(f"https://api.openalex.org/works?search={q}&per-page=1")
        res = (r or {}).get("results") or []
        w = res[0] if res else None
    if not w:
        return None
    auth = []
    for a in w.get("authorships", []):
        nm = a.get("raw_author_name") or a.get("author", {}).get("display_name", "")
        parts = nm.split()
        auth.append((parts[-1] if parts else "", " ".join(parts[:-1])))
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
    return dict(title=w.get("title"), year=w.get("publication_year"), type=w.get("type"),
                venue=src, doi=(w.get("doi") or "").replace("https://doi.org/", ""),
                authors=auth)


def main():
    tex = "".join(p.read_text(encoding="utf-8") for p in (ROOT / "paper").glob("*.tex")
                  if not p.name.startswith(("_", "diff")))
    cited = {k.strip() for g in re.findall(r"\\cite\{([^}]*)\}", tex) for k in g.split(",")}
    bib = [e for e in parse_bib((ROOT / "paper/references.bib").read_text(encoding="utf-8"))
           if e["_key"] in cited]
    rows = []
    for e in bib:
        rec = dict(key=e["_key"], bibtype=e["_type"], title=tex_to_text(e.get("title", "")),
                   year=e.get("year"), doi=e.get("doi"), venue=tex_to_text(e.get("journal") or e.get("booktitle") or e.get("howpublished") or e.get("institution") or ""),
                   volume=e.get("volume"), number=e.get("number"), pages=e.get("pages"),
                   bib_authors=bib_authors(e.get("author")))
        if e.get("doi"):
            rec["doi_org"] = doi_resolves(e["doi"])
            rec["crossref"] = crossref(e["doi"])
            rec["openalex"] = openalex(doi=e["doi"])
        else:
            rec["openalex"] = openalex(title=rec["title"])
        for src in ("crossref", "openalex"):
            r = rec.get(src)
            if r and r.get("authors"):
                rec[f"author_issues_{src}"] = compare(rec["bib_authors"], r["authors"])
        rows.append(rec)
        cr = rec.get("crossref") or {}
        print(f"{e['_key']:32s} doi.org={rec.get('doi_org', ('-',))[0]} "
              f"cr_auth={len(cr.get('authors', []))} bib_auth={len(rec['bib_authors'])} "
              f"issues={len(rec.get('author_issues_crossref', []))}/{len(rec.get('author_issues_openalex', []))}",
              flush=True)
        time.sleep(0.3)
    out = ROOT / "reports/reference_forensics_2026-09-25.json"
    out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", out, len(rows), "entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
