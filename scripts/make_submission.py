#!/usr/bin/env python3
"""Assemble the IEEE Access submission package outside the repository.

  python scripts/make_submission.py

Output: ../IEEE_Access_Submission/ (next to the repository, because it holds
the author photos, which are not in the public repository).

  01_Manuscript_PDF/          the compiled manuscript (upload as the PDF)
  02_LaTeX_Source/            ONE main.tex with every \\input, table, macro and the
                              bibliography inlined, and only the files it needs,
                              all in one flat directory (no sub-folders, no .bib,
                              .bst or .bbl, no BibTeX run); plus a zip of it
  03_Cover_Letter/            cover letter from the corresponding author (.tex/.pdf/.docx)
  04_Figures/                 every figure as a separate vector PDF and 600-dpi PNG
  05_Author_Biographies_and_Photos/
  06_Submission_Form_Details/ text to paste into the submission system
  07_Supplementary_Material/  the reproducibility package (optional upload)
  README_SUBMISSION_CHECKLIST.md

IEEE Access requires the LaTeX source AND a PDF whose content matches exactly.
The script compiles the flat source in a scratch directory with pdflatex only
(no BibTeX), and stops unless it gives the same page count and text as
paper/main.pdf.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
OUT = ROOT.parent / "IEEE_Access_Submission"
ZIP_REPRO = ROOT.parent / "oran-ids-deployability_reproducibility_package.zip"
STEM = "Ahmad_et_al_IEEE_Access"
TITLE = "What Held-Out Scores Predict About Deploying Intrusion Detection in O-RAN"
DATE = "26 September 2026"
REPO_URL = "https://github.com/adeliusa486/oran-ids-deployability"

AFF = {1: "Faculty of Computer and Information Systems, Islamic University of Madinah, "
          "Al Madinah Al Munawarah, Saudi Arabia",
       2: "Faculty of Computer Information Science, Higher Colleges Of Technology, "
          "Al Mizn- Baniyas North- Abu Dhabi, United Arab Emirates",
       3: "Anuradha and Vikas Sinha Department of Data Science, University of North Texas, "
          "Denton, TX, USA, 76203-5017"}
AUTHORS = [  # name, affiliation index, role
    ("Adeel Ahmad", 1, "Submitting author (ORCID 0009-0007-5868-394X)"),
    ("Arshad Ali", 1, ""),
    ("Eraj Khan", 2, "Corresponding author (ekhan@hct.ac.ae)"),
    ("Gahangir Hossain", 3, ""),
    ("Ali Akarma", 1, ""),
]
CORR = {"name": "Dr. Eraj Khan", "email": "ekhan@hct.ac.ae",
        "lines": ["Faculty of Computer Information Science",
                  "Higher Colleges Of Technology",
                  "Al Mizn- Baniyas North- Abu Dhabi, United Arab Emirates"]}
# the IEEE Access class loads these (logos, bullet, spot colour, fonts)
CLASS_FILES = ["ieeeaccess.cls", "spotcolor.sty", "logo.png", "notaglinelogo.png", "bullet.png"]
FIG_NAMES = {  # label -> file stem in 04_Figures
    "fig:arch": "architecture", "fig:leakage": "protocol_sensitivity",
    "fig:benign": "benign_sessions", "fig:conflict": "label_conflict",
    "fig:transfer": "transfer", "fig:shift": "covariate_shift",
    "fig:threshold": "precision_vs_threshold", "fig:reliability": "reliability",
    "fig:latency": "latency_distribution", "fig:sensitivity": "test_sensitivity",
}
GENERATED_FIG = {"fig:leakage": "fig_rev_leakage", "fig:benign": "fig_rev_benign",
                 "fig:transfer": "fig_rev_transfer", "fig:shift": "fig_rev_shift",
                 "fig:threshold": "fig_rev_threshold", "fig:reliability": "fig_rev_reliability",
                 "fig:latency": "fig_rev_latency", "fig:sensitivity": "fig_rev_sensitivity"}


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")


def pdf_text(pdf: Path) -> str:
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True,
                          errors="replace").stdout


def pdf_pages(pdf: Path) -> int:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


def latex_build(d: Path, main: str = "main", passes: int = 2, bib: bool = False) -> Path:
    tex = ["pdflatex", "-interaction=nonstopmode", main + ".tex"]
    steps = [tex, ["bibtex", main], tex, tex] if bib else [tex] * passes
    for c in steps:
        run(c, d)
    pdf = d / (main + ".pdf")
    log = (d / (main + ".log")).read_text(encoding="latin-1")
    errs = [l for l in log.splitlines() if l.startswith("!")]
    if errs or not pdf.exists():
        sys.exit(f"LaTeX failed in {d}: {errs[:3]}")
    if re.search(r"undefined references|Citation .* undefined|Reference .* undefined", log):
        sys.exit(f"undefined references in {d}")
    return pdf


# ---------------------------------------------------------------------------
def resolve_input(name: str) -> Path:
    p = (PAPER / name).resolve()
    return p if p.suffix == ".tex" else p.with_name(p.name + ".tex")


def inline_inputs(text: str, depth: int = 0) -> str:
    """Replace every \\input{...} by the file's content, recursively, exactly
    as \\input reads it: the file's last line keeps its end-of-line (a space),
    which matters inside boxes such as the \\resizebox around Fig. 1."""
    if depth > 5:
        sys.exit("\\input nested too deeply")

    def sub(m):
        body = inline_inputs(resolve_input(m.group(1)).read_text(encoding="utf-8"), depth + 1)
        return body if body.endswith("\n") else body + "\n"
    return re.sub(r"\\input\{([^}]+)\}", sub, text)


def flat_source(dst: Path) -> list[str]:
    """One main.tex plus the images and class files it loads, in one directory."""
    dst.mkdir(parents=True)
    s = inline_inputs((PAPER / "main.tex").read_text(encoding="utf-8"))
    bib = "\\bibliographystyle{IEEEtran_doi}\n\\bibliography{references}"
    if s.count(bib) != 1:
        sys.exit("bibliography commands not found")
    bbl = (PAPER / "main.bbl").read_text(encoding="utf-8")
    s = s.replace(bib, "% bibliography inlined from main.bbl (IEEEtran_doi style)\n" + bbl.strip())
    figures = set(re.findall(r"\{\.\./figures/generated/([\w.]+)\}", s))
    icons = set(re.findall(r"\\ficon\{(\w+)\}", s))
    icons |= {"f1_" + a for a in re.findall(r"\\fOneAct\{(\w+)\}", s)}
    icons.discard("f1_#1")
    s = (s.replace("../figures/generated/", "").replace("../figures/icons/", "")
          .replace("authors/#1", "#1"))
    if "\\input{" in s or "../" in s:
        sys.exit("a path outside the flat directory is left in main.tex")
    (dst / "main.tex").write_text(s, encoding="utf-8", newline="\n")
    for f in sorted(figures):
        shutil.copy2(ROOT / "figures/generated" / f, dst)
    for i in sorted(icons):
        shutil.copy2(ROOT / "figures/icons" / f"{i}.png", dst)
    for p in sorted((PAPER / "authors").glob("*.jpg")):
        shutil.copy2(p, dst)
    acc = PAPER / "access"
    for name in CLASS_FILES:
        shutil.copy2(acc / name, dst)
    for pat in ("t1*.pfb", "t1*.tfm", "t1*.map", "*.fd"):
        for p in acc.glob(pat):
            shutil.copy2(p, dst)
    return sorted(p.name for p in dst.iterdir())


def figure_numbers() -> dict[str, int]:
    aux = (PAPER / "main.aux").read_text(encoding="latin-1")
    return {lab: int(re.search(r"\\newlabel\{" + re.escape(lab) + r"\}\{\{(\d+)\}", aux).group(1))
            for lab in FIG_NAMES}


def export_figures(dst: Path) -> list[str]:
    dst.mkdir(parents=True)
    nums = figure_numbers()
    tikz = {"fig:arch": r"\resizebox{17.6cm}{!}{\input{fig1_architecture}}",
            "fig:conflict": r"\input{fig_conflict}"}
    made = []
    for lab, stem in FIG_NAMES.items():
        name = f"Fig{nums[lab]:02d}_{stem}"
        if lab in tikz:
            with tempfile.TemporaryDirectory() as td:
                t = Path(td)
                doc = "\n".join([
                    r"\documentclass[border=4pt]{standalone}",
                    r"\usepackage{times}", r"\usepackage[T1]{fontenc}",
                    r"\usepackage{tikz}", r"\usepackage{graphicx}", r"\usepackage{xcolor}",
                    r"\usepackage{amsmath,amssymb}",
                    r"\usetikzlibrary{arrows.meta,positioning,calc,fit,backgrounds,"
                    r"shapes.geometric,shapes.symbols,patterns,decorations.pathreplacing}",
                    r"\input{../tables/generated/numbers}", r"\input{figstyle}",
                    r"\begin{document}", tikz[lab], r"\end{document}", ""])
                s = inline_inputs(doc).replace("../figures/icons/", "")
                (t / "fig.tex").write_text(s, encoding="utf-8")
                for p in (ROOT / "figures/icons").glob("*.png"):
                    shutil.copy2(p, t)
                shutil.copy2(latex_build(t, "fig"), dst / f"{name}.pdf")
        else:
            shutil.copy2(ROOT / "figures/generated" / f"{GENERATED_FIG[lab]}.pdf", dst / f"{name}.pdf")
        run(["pdftoppm", "-r", "600", "-png", "-singlefile", f"{name}.pdf", name], dst)
        made.append(name)
    return sorted(made)


# ---------------------------------------------------------------------------
def paper_abstract_and_keywords() -> tuple[str, list[str]]:
    txt = pdf_text(PAPER / "main.pdf")
    ab = re.search(r"ABSTRACT (.*?)\nINDEX TERMS (.*?)\n", txt, re.S)
    return " ".join(ab.group(1).split()), [k.strip().rstrip(".") for k in ab.group(2).split(",")]


def biographies() -> list[tuple[str, str, str]]:
    s = (PAPER / "main.tex").read_text(encoding="utf-8")
    out = []
    for photo, name, body in re.findall(
            r"\\begin\{IEEEbiography\}\[\{\\authorphoto\{([\w.]+)\}\}\]\{([^}]+)\}\n(.*?)\n\\end\{IEEEbiography\}",
            s, re.S):
        out.append((name, photo, " ".join(body.replace("--", "-").replace("\\", "").split())))
    return out


# ---------------------------------------------------------------------------
LETTER = {
    "opening": ("On behalf of all authors, I am pleased to submit the manuscript above for "
                "consideration as a Research Article in IEEE Access. Machine-learning intrusion "
                "detectors for 5G and O-RAN are often reported above 99% accuracy on a random "
                "split of a single dataset. Our study asks what such a score predicts about the "
                "properties that decide whether a detector can run as an xApp in the RAN "
                "Intelligent Controller: generalization to a site that contributed no training "
                "data, alert burden at a realistic attack base rate, and decision latency in the "
                "near-real-time control loop. We measure all three for six architectures and two "
                "input-blind baselines on three public corpora."),
    "summary": "",
    "findings_intro": "The principal findings are:",
    "findings": [
        ("a random split raises macro-F1 by 0.13 over a session-disjoint split on the radio "
         "layer, and a model-free nearest-neighbor lookup gains about as much, consistent with "
         "the recognition of capture sessions;"),
        ("in 5G-NIDD, 59% of the benign flows are copies of UDP-flood records labeled as "
         "attacks, and a published 99.9% accuracy depends on two record-position fields that "
         "tell these copies apart;"),
        ("detectors transferred between corpora reach 0.61 to 0.78 balanced accuracy on flows "
         "with consistent labels, none exceeds an operational precision of 0.092 at a declared "
         "attack prevalence of 0.002, and none passes a deployability test that combines "
         "generalization, alert burden, and latency;"),
        ("as an xApp in a FlexRIC near-real-time RIC with an emulated E2 node, a window-level "
         "detector completes a decision and its control message in at most 4.95 ms at the 99th "
         "percentile."),
    ],
    "fit": ("The work spans mobile networking, network security, and machine learning, which "
            "matches the multidisciplinary scope of IEEE Access. It closes with reporting "
            "requirements that we hope will help researchers and operators judge claims of "
            "deployable O-RAN detection."),
    "confirm_intro": "In submitting this manuscript, we confirm that:",
    "confirm": [
        ("the work is original, has not been published, and is not under consideration by any "
         "other journal or conference;"),
        ("all authors have approved the manuscript and its author order, and declare no conflict "
         "of interest;"),
        ("all corpora used are public, and the code, configuration, and results are openly "
         "available at " + REPO_URL + ";"),
        "the use of AI assistance is disclosed in the Acknowledgment section, as IEEE policy requires.",
    ],
    "close": ("Thank you for considering our manuscript. I look forward to hearing from you."),
}


def tex_escape(s: str) -> str:
    return (s.replace("\\", r"\textbackslash{}").replace("%", r"\%").replace("&", r"\&")
             .replace("_", r"\_").replace("#", r"\#").replace("\u201c", "``")
             .replace("\u201d", "''").replace("Dr. ", "Dr.~"))


def cover_letter(dst: Path) -> None:
    dst.mkdir(parents=True)
    L = LETTER
    url = lambda s: s.replace(tex_escape(REPO_URL), r"\url{" + REPO_URL + "}")
    authors = ", ".join(n for n, _, _ in AUTHORS)
    details = [("Title", tex_escape(TITLE)),
               ("Article type", "Research Article"),
               ("Authors", tex_escape(authors)),
               ("Corresponding author", tex_escape(CORR["name"]) + r" (\href{mailto:"
                + CORR["email"] + "}{" + CORR["email"] + "})")]
    t = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[a4paper,top=1.4cm,bottom=1.4cm,left=2.2cm,right=2.2cm]{geometry}",
        r"\usepackage{newtxtext}", r"\usepackage[T1]{fontenc}",
        r"\usepackage[dvipsnames]{xcolor}", r"\usepackage{xurl}",
        r"\usepackage[hidelinks]{hyperref}", r"\usepackage{enumitem}",
        r"\usepackage{tabularx}", r"\usepackage{array}",
        r"\definecolor{lhblue}{RGB}{0,72,130}",
        r"\setlength{\parindent}{0pt}", r"\setlength{\parskip}{0.45em}", r"\pagestyle{empty}",
        r"\setlist[itemize]{leftmargin=1.4em,itemsep=0.1em,topsep=0.1em,label=\textcolor{lhblue}{\small$\blacktriangleright$}}",
        r"\usepackage{amssymb}",
        r"\begin{document}",
        # letterhead of the corresponding author
        r"\begin{minipage}[t]{0.36\textwidth}\vspace{0pt}{\Large\bfseries\color{lhblue} "
        + tex_escape(CORR["name"]) + r"}\\[2pt]{\small Corresponding Author}\end{minipage}%"
        + "\n" + r"\hfill\begin{minipage}[t]{0.62\textwidth}\vspace{0pt}\raggedleft\small "
        + r"\\ ".join(tex_escape(x) for x in CORR["lines"])
        + r"\\ \href{mailto:" + CORR["email"] + "}{" + CORR["email"] + r"}\end{minipage}",
        r"\par\vspace{4pt}{\color{lhblue}\rule{\textwidth}{1.2pt}}\par\vspace{2pt}",
        r"\hfill " + DATE,
        r"The Editor-in-Chief\\ \textit{IEEE Access}",
        r"\textbf{Re: Submission of a new manuscript to \textit{IEEE Access}}",
        r"{\small\renewcommand{\arraystretch}{1.15}\begin{tabularx}{\textwidth}{@{}>{\bfseries}l X@{}}",
    ]
    t += [f"{k}: & {v} \\\\" for k, v in details]
    t += [r"\end{tabularx}}", "Dear Editor,", tex_escape(L["opening"]),
          tex_escape(L["findings_intro"]), r"\begin{itemize}"]
    t += [r"\item " + tex_escape(b) for b in L["findings"]]
    t += [r"\end{itemize}", tex_escape(L["fit"]), tex_escape(L["confirm_intro"]), r"\begin{itemize}"]
    t += [r"\item " + url(tex_escape(c)) for c in L["confirm"]]
    t += [r"\end{itemize}", tex_escape(L["close"]),
          r"Yours sincerely,\\[1.6em]"
          r"\textbf{" + tex_escape(CORR["name"]) + r"}\\ Corresponding Author, on behalf of all authors\\ "
          + ", ".join(tex_escape(x) for x in CORR["lines"][:2])
          + r"\\ E-mail: \href{mailto:" + CORR["email"] + "}{" + CORR["email"] + "}",
          r"\end{document}", ""]
    (dst / "cover_letter.tex").write_text("\n\n".join(t), encoding="utf-8")
    pdf = latex_build(dst, "cover_letter")
    if pdf_pages(pdf) != 1:
        sys.exit(f"cover letter runs to {pdf_pages(pdf)} pages")
    for ext in (".aux", ".log", ".out"):
        (dst / ("cover_letter" + ext)).unlink(missing_ok=True)
    cover_letter_docx(dst / "cover_letter.docx", authors)


def cover_letter_docx(path: Path, authors: str) -> None:
    import docx
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor
    L = LETTER
    blue = RGBColor(0, 72, 130)
    d = docx.Document()
    for sec in d.sections:
        sec.top_margin = sec.bottom_margin = Cm(1.6)
        sec.left_margin = sec.right_margin = Cm(2.2)
    st = d.styles["Normal"]
    st.font.name, st.font.size = "Times New Roman", Pt(11)
    st.paragraph_format.space_after = Pt(5)

    head = d.add_table(rows=1, cols=2)
    head.alignment = WD_TABLE_ALIGNMENT.CENTER
    left, right = head.rows[0].cells
    r = left.paragraphs[0].add_run(CORR["name"])
    r.bold, r.font.size, r.font.color.rgb = True, Pt(16), blue
    left.add_paragraph("Corresponding Author").runs[0].font.size = Pt(9.5)
    rp = right.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rr = rp.add_run("\n".join(CORR["lines"] + [CORR["email"]]))
    rr.font.size = Pt(9.5)
    rule = d.add_paragraph()
    pPr = rule._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "12"), ("w:space", "1"), ("w:color", "004882")):
        bottom.set(qn(k), v)
    bdr.append(bottom)
    pPr.append(bdr)

    d.add_paragraph(DATE).alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p = d.add_paragraph("The Editor-in-Chief\n")
    p.add_run("IEEE Access").italic = True
    d.add_paragraph().add_run("Re: Submission of a new manuscript to IEEE Access").bold = True
    tbl = d.add_table(rows=0, cols=2)
    for k, v in (("Title:", TITLE), ("Article type:", "Research Article"), ("Authors:", authors),
                 ("Corresponding author:", f"{CORR['name']} ({CORR['email']})")):
        c1, c2 = tbl.add_row().cells
        c1.paragraphs[0].add_run(k).bold = True
        c2.paragraphs[0].add_run(v)
        c1.width, c2.width = Cm(4.2), Cm(12.4)
    d.add_paragraph("Dear Editor,")
    d.add_paragraph(L["opening"])
    d.add_paragraph(L["findings_intro"])
    for b in L["findings"]:
        d.add_paragraph(b, style="List Bullet")
    d.add_paragraph(L["fit"])
    d.add_paragraph(L["confirm_intro"])
    for c in L["confirm"]:
        d.add_paragraph(c, style="List Bullet")
    d.add_paragraph(L["close"])
    sig = d.add_paragraph("Yours sincerely,\n\n")
    sig.add_run(CORR["name"]).bold = True
    sig.add_run("\nCorresponding Author, on behalf of all authors\n"
                + ", ".join(CORR["lines"][:2]) + f"\nE-mail: {CORR['email']}")
    d.save(path)


# ---------------------------------------------------------------------------
def submission_details(dst: Path, abstract: str, keywords: list[str]) -> None:
    dst.mkdir(parents=True)
    rows = "\n".join(f"| {i} | {n} | {AFF[a]} | {r or '-'} |"
                     for i, (n, a, r) in enumerate(AUTHORS, 1))
    (dst / "abstract.txt").write_text(abstract + "\n", encoding="utf-8")
    (dst / "keywords.txt").write_text("\n".join(keywords) + "\n", encoding="utf-8")
    md = f"""# Submission form details (IEEE Access, Atypon ReX)

Paste these into the submission system. Items marked **[fill in]** need the authors.

## Manuscript
- **Title:** {TITLE}
- **Running head:** Held-Out Scores and Deployment of O-RAN Intrusion Detection
- **Manuscript type:** Research Article
- **Subject categories** (as in your previous IEEE Access submission; pick the closest offered):
  Communications technology; Computational and artificial intelligence; Computers and information processing
- **Pages:** 19 (IEEE Access template, two columns)
- **LaTeX main file:** `main.tex` (single file; compile with pdflatex, no BibTeX needed)

## Abstract ({len(abstract.split())} words; IEEE Access limit 250)
{abstract}

## Keywords (3 to 10 required)
Index terms printed in the paper: {", ".join(keywords)}.

The submission system offers keywords from the IEEE Thesaurus. Closest matches to select:
Intrusion detection; Open RAN (or Radio access networks); 5G mobile communication; Machine learning;
Network security; Benchmark testing; Data models; Telemetry; Latency.

## Authors (order as in the paper)
| # | Name | Affiliation | Role |
|---|---|---|---|
{rows}

- **Corresponding author:** Dr. Eraj Khan, ekhan@hct.ac.ae (the cover letter is signed by him).
- **Submitting author:** whoever uploads; the account needs a public, populated ORCID
  (Adeel Ahmad: https://orcid.org/0009-0007-5868-394X).
- **E-mail addresses and ORCIDs of the other authors:** **[fill in]** (the system may ask for them).

## Declarations
- **Originality:** not published and not under consideration elsewhere. **[confirm]**
- **Conflict of interest:** none declared. **[confirm]**
- **Funding:** the paper names no funding source. **[fill in if any]**
- **Data availability:** all three corpora are public (NetsLab-5GORAN-IDD and 5G-NIDD under CC-BY-4.0; the 5G core
  datasets from their authors' repository). Code and results: {REPO_URL}
- **AI use:** disclosed in the Acknowledgment section of the manuscript (required by IEEE policy).
- **Previously submitted to IEEE Access?** No (the earlier submission b57487b2 was a different paper).

## Reviewers (optional)
- Suggested reviewers: **[optional, fill in]** (independent researchers in O-RAN security or network intrusion
  detection; no co-authors or colleagues from your institutions).
- Opposed reviewers: none.
"""
    (dst / "submission_details.md").write_text(md, encoding="utf-8")


def checklist(out: Path, figs: list[str], pages: int, src_files: list[str]) -> None:
    md = f"""# IEEE Access submission package

Paper: **{TITLE}**
Built {DATE} by `scripts/make_submission.py`. Manuscript: {pages} pages.

## What to upload (Atypon ReX)

| Upload slot | File |
|---|---|
| Main document (PDF) | `01_Manuscript_PDF/{STEM}_manuscript.pdf` |
| LaTeX source | `02_LaTeX_Source/{STEM}_LaTeX_source.zip` (main file: `main.tex`) |
| Cover letter | `03_Cover_Letter/cover_letter.pdf` (Word version: `cover_letter.docx`) |
| Figures (only if asked separately) | `04_Figures/` ({len(figs)} figures, vector PDF and 600-dpi PNG) |
| Author photos (only if asked separately) | `05_Author_Biographies_and_Photos/` |
| Supplementary material (optional) | `07_Supplementary_Material/` (the code is also public on GitHub) |

Form fields: `06_Submission_Form_Details/submission_details.md`.

## LaTeX source ({len(src_files)} files, one flat directory)
- `main.tex` is the only .tex file: every section, table, number macro and figure is inlined, and the
  bibliography is embedded, so the system needs neither BibTeX nor any .bib/.bst/.bbl file.
- Also included: the figure PDFs, the icon PNGs of Figs. 1 and 4, the five author photos, and the files the
  official IEEE Access class loads (`ieeeaccess.cls`, `spotcolor.sty`, logos, fonts). Nothing else.
- Checked: compiles with two pdflatex runs, 0 errors, no undefined references, and gives the same
  {pages} pages and the same text as the PDF.

## Still for the authors
- [ ] Dr. Eraj Khan reads and approves the cover letter he signs.
- [ ] Confirm the declarations (originality, no conflict of interest) and add funding if any.
- [ ] Confirm the wording of the AI-use disclosure in the Acknowledgment.
- [ ] E-mail addresses and ORCIDs of all co-authors for the submission form.
- [ ] Optional: suggested reviewers; Eraj Khan's Ph.D. year in his biography.
- [ ] All authors approve the final PDF.
"""
    (out / "README_SUBMISSION_CHECKLIST.md").write_text(md, encoding="utf-8")


def sync_into(stage: Path, out: Path) -> None:
    """Make `out` identical to `stage` without removing directories that
    Windows may hold open (an Explorer window, a PDF viewer)."""
    out.mkdir(exist_ok=True)
    want = {p.relative_to(stage) for p in stage.rglob("*")}
    for p in sorted(out.rglob("*"), key=lambda q: len(q.parts), reverse=True):
        if p.relative_to(out) not in want:
            try:
                p.unlink() if p.is_file() else p.rmdir()
            except OSError as exc:
                print(f"  could not remove {p} ({exc.strerror}); close it and rerun")
    for p in sorted(stage.rglob("*")):
        q = out / p.relative_to(stage)
        if p.is_dir():
            q.mkdir(exist_ok=True)
        else:
            shutil.copy2(p, q)


def main() -> int:
    global OUT
    final = OUT
    stage_root = Path(tempfile.mkdtemp(prefix="ieee_access_"))
    OUT = stage_root / "pkg"
    OUT.mkdir()
    try:
        rc = build()
    finally:
        OUT = final
    sync_into(stage_root / "pkg", final)
    shutil.rmtree(stage_root, ignore_errors=True)
    print(f"wrote {final}")
    return rc


def build() -> int:
    pdf = PAPER / "main.pdf"
    pages = pdf_pages(pdf)
    if pdf.stat().st_size > 40e6:
        sys.exit("manuscript PDF exceeds 40 MB")

    d1 = OUT / "01_Manuscript_PDF"
    d1.mkdir()
    shutil.copy2(pdf, d1 / f"{STEM}_manuscript.pdf")

    d2 = OUT / "02_LaTeX_Source"
    src = d2 / "source"
    src_files = flat_source(src)
    with tempfile.TemporaryDirectory() as td:
        t = Path(td) / "build"
        shutil.copytree(src, t)
        built = latex_build(t, "main", passes=3)
        if pdf_pages(built) != pages:
            sys.exit(f"flat source gives {pdf_pages(built)} pages, not {pages}")
        # same words, same counts (pdftotext may read a table's columns in a
        # different order after sub-pixel differences, so order is not compared)
        from collections import Counter
        if Counter(pdf_text(built).split()) != Counter(pdf_text(pdf).split()):
            sys.exit("flat source does not reproduce the text of paper/main.pdf")
    with zipfile.ZipFile(d2 / f"{STEM}_LaTeX_source.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.iterdir()):
            z.write(p, p.name)

    cover_letter(OUT / "03_Cover_Letter")
    figs = export_figures(OUT / "04_Figures")

    d5 = OUT / "05_Author_Biographies_and_Photos"
    d5.mkdir()
    lines = []
    for i, (name, photo, body) in enumerate(biographies(), 1):
        shutil.copy2(PAPER / "authors" / photo, d5 / f"{i}_{photo}")
        lines += [f"{i}. {name.upper()} {body}", ""]
    (d5 / "biographies.txt").write_text("\n".join(lines), encoding="utf-8")

    abstract, keywords = paper_abstract_and_keywords()
    if len(abstract.split()) > 250 or not 3 <= len(keywords) <= 10:
        sys.exit("abstract or keyword count outside IEEE Access limits")
    submission_details(OUT / "06_Submission_Form_Details", abstract, keywords)

    d7 = OUT / "07_Supplementary_Material"
    d7.mkdir()
    if ZIP_REPRO.exists():
        shutil.copy2(ZIP_REPRO, d7)
    (d7 / "README.txt").write_text(
        "Optional supplementary upload: code, configuration, per-split results and\n"
        "generators for every table, figure and number. Also public at\n" + REPO_URL + "\n",
        encoding="utf-8")

    checklist(OUT, figs, pages, src_files)
    print(f"wrote {OUT}")
    print(f"LaTeX source: {len(src_files)} files: {', '.join(src_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
