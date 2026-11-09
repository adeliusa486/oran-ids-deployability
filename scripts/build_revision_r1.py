#!/usr/bin/env python3
"""Build every file of the IEEE Access resubmission (revision 1) in one go.

  python scripts/build_revision_r1.py

Order (each step uses the previous one's output):
  1. analysis/make_assets_r1.py         numbers, tables, data figures
  2. paper/r1/main.tex                  modular build (pdflatex x3)
  3. scripts/flatten_r1.py              flat LaTeX source + clean PDF + source zip
  4. scripts/highlight_changes.py       yellow-highlighted PDF against the first submission
  5. paper/r1/response/response_r1.tex  response letter (PDF, LaTeX, DOCX)
  6. Revision_1/06_Cover_Letter          cover letter (PDF, DOCX)
  7. figures                            each figure as vector PDF and 600-dpi PNG

Output: ../IEEE_Access_Submission/Revision_1/0x_*/
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R1 = ROOT / "paper" / "r1"
SUB = ROOT.parent / "IEEE_Access_Submission"
REV = SUB / "Revision_1"
STEM = "Ali-et-al-IEEE-Access-R1"             # first author: Arshad Ali
RESP_NAME = "Response-to-Reviewers-Access-2026-49092"
COVER_NAME = "Cover-Letter-R1"
FIRST_PDF = SUB / "01_Manuscript_PDF" / "main.pdf"


def run(cmd, cwd=ROOT, check=True):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if check and r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f"failed: {' '.join(map(str, cmd))}")
    return r


def latex(tex: str, cwd: Path, n: int = 3):
    for _ in range(n):
        run(["pdflatex", "-interaction=nonstopmode", tex], cwd=cwd, check=False)
    log = (cwd / (Path(tex).stem + ".log")).read_text(encoding="utf-8", errors="replace")
    errs = [l for l in log.splitlines() if l.startswith("!")]
    if errs:
        raise SystemExit(f"LaTeX errors in {cwd / tex}: {errs[:3]}")


def main() -> int:
    print("1. assets");               run([sys.executable, "analysis/make_assets_r1.py"])
    print("2. modular manuscript");   latex("main.tex", R1)
    print("3. flat source")
    flat = REV / "03_Main_Manuscript" / "LaTeX_Source"
    if flat.exists():
        shutil.rmtree(flat)
    run([sys.executable, "scripts/flatten_r1.py", str(flat)])
    clean_pdf = REV / "03_Main_Manuscript" / f"{STEM}-Clean.pdf"
    shutil.copy(flat / "main.pdf", clean_pdf)
    for f in flat.glob("main.*"):
        if f.suffix in (".aux", ".log", ".out"):
            f.unlink()
    with zipfile.ZipFile(REV / "03_Main_Manuscript" / f"{STEM}-LaTeX-Source.zip", "w",
                         zipfile.ZIP_DEFLATED) as z:
        for f in sorted(flat.iterdir()):
            if f.name != "main.pdf":
                z.write(f, f.name)
    print("4. highlighted PDF")
    hl = REV / "02_Highlighted_PDF"
    hl.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "scripts/highlight_changes.py", str(FIRST_PDF), str(clean_pdf),
         str(hl / f"{STEM}-Highlighted.pdf"), "--report", str(hl / "highlight-report.json"),
         # only the passages changed in answer to a reviewer (drop this line to mark every changed word)
         "--passages", str(R1 / "highlight_passages.json")])
    print("5. response letter")
    latex("response_r1.tex", R1 / "response", n=2)
    resp = REV / "01_Response_to_Reviewers"
    (resp / "LaTeX_Source").mkdir(parents=True, exist_ok=True)
    # one PDF: the letter followed by the highlighted manuscript, links inside
    run([sys.executable, "scripts/merge_response.py", str(R1 / "response" / "response_r1.pdf"),
         str(hl / f"{STEM}-Highlighted.pdf"), str(resp / f"{RESP_NAME}.pdf")])
    for f in list((R1 / "response").glob("response_*.tex")) + [R1 / "numbers_r1.tex"]:
        shutil.copy(f, resp / "LaTeX_Source" / f.name)
    t = (resp / "LaTeX_Source" / "response_r1.tex").read_text(encoding="utf-8")
    t = t.replace(r"\externaldocument[M-]{../main}",
                  r"\externaldocument[M-]{../../03_Main_Manuscript/LaTeX_Source/main}  % compile main.tex there first")
    t = t.replace(r"\input{../numbers_r1}", r"\input{numbers_r1}")
    t = t.replace(r"{../02_Highlighted_PDF/", r"{../../02_Highlighted_PDF/")  # one folder deeper
    (resp / "LaTeX_Source" / "response_r1.tex").write_text(t, encoding="utf-8")
    run([sys.executable, "scripts/response_to_docx.py", str(R1 / "main.aux"),
         str(resp / f"{RESP_NAME}.docx")])
    print("6. cover letter")
    cl = REV / "06_Cover_Letter"
    shutil.copy(R1 / "numbers_r1.tex", cl / "numbers_r1.tex")
    latex(f"{COVER_NAME}.tex", cl, n=2)
    run(["pandoc", f"{COVER_NAME}.tex", "-f", "latex", "-t", "docx", "-o", f"{COVER_NAME}.docx"], cwd=cl)
    for f in cl.glob(f"{COVER_NAME}.*"):
        if f.suffix in (".aux", ".log", ".out"):
            f.unlink()
    print("7. figures")
    figs = REV / "04_Figures"
    figs.mkdir(parents=True, exist_ok=True)
    latex("_f1prev.tex", R1, n=1)
    latex("_f2prev.tex", R1, n=1)
    pairs = {"Fig01-Architecture": R1 / "_f1prev.pdf", "Fig02-Label-Conflict": R1 / "_f2prev.pdf",
             "Fig03-Transfer": R1 / "figs/fig_transfer.pdf", "Fig04-Covariate-Shift": R1 / "figs/fig_shift.pdf",
             "Fig05-Label-Efficient": R1 / "figs/fig_label_efficient.pdf",
             "Fig06-Deployability-Test": R1 / "figs/fig_test.pdf", "Fig07-Benign-Sessions": R1 / "figs/fig_benign.pdf"}
    import fitz
    for name, src in pairs.items():
        shutil.copy(src, figs / f"{name}.pdf")
        d = fitz.open(figs / f"{name}.pdf")
        d[0].get_pixmap(dpi=600).save(figs / f"{name}.png")
    print("done:", REV)
    return 0


if __name__ == "__main__":
    sys.exit(main())
