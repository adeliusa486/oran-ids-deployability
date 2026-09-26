#!/usr/bin/env python3
"""Assemble the IEEE Access submission package outside the repository.

  python scripts/make_submission.py

Output: ../IEEE_Access_Submission/ (next to the repository, because it holds
the author photos, which are not in the public repository).

  01_Manuscript_PDF/          the compiled manuscript (upload as "Main Document" PDF)
  02_LaTeX_Source/            flat, self-contained source that compiles on its own,
                              plus a zip of it (upload as the LaTeX source)
  03_Cover_Letter/            cover letter as .tex, .pdf and .docx
  04_Figures/                 every figure as a separate vector PDF and 600-dpi PNG
  05_Author_Biographies_and_Photos/
  06_Submission_Form_Details/ text to paste into the submission system
  07_Supplementary_Material/  the reproducibility package (optional upload)
  README_SUBMISSION_CHECKLIST.md

IEEE Access requires the LaTeX (or Word) source AND a PDF whose content
matches exactly; the script rebuilds the flat source in a scratch directory and
refuses to finish unless its text equals that of paper/main.pdf.
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

AUTHORS = [  # name, affiliation index, role
    ("Adeel Ahmad", 1, "Submitting author (ORCID 0009-0007-5868-394X)"),
    ("Arshad Ali", 1, ""),
    ("Eraj Khan", 2, "Corresponding author (ekhan@hct.ac.ae)"),
    ("Gahangir Hossain", 3, ""),
    ("Ali Akarma", 1, ""),
]
TEX_FILES = ["main.tex", "latency_section.tex", "predicate_section.tex",
             "fig1_architecture.tex", "fig_conflict.tex", "figstyle.tex"]
CLASS_FILES = ["ieeeaccess.cls", "spotcolor.sty", "logo.png", "notaglinelogo.png", "bullet.png"]
FIG_NAMES = {  # label -> file stem in 04_Figures
    "fig:arch": "architecture", "fig:leakage": "protocol_sensitivity",
    "fig:benign": "benign_sessions", "fig:conflict": "label_conflict",
    "fig:transfer": "transfer", "fig:shift": "covariate_shift",
    "fig:threshold": "precision_vs_threshold", "fig:reliability": "reliability",
    "fig:latency": "latency_distribution", "fig:sensitivity": "test_sensitivity",
}


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    return r


def pdf_text(pdf: Path) -> str:
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True,
                          errors="replace").stdout


def pdf_pages(pdf: Path) -> int:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


def latex_build(d: Path, main: str = "main", bib: bool = True) -> Path:
    tex = ["pdflatex", "-interaction=nonstopmode", main + ".tex"]
    steps = [tex, ["bibtex", main], tex, tex] if bib else [tex, tex]
    for c in steps:
        run(c, d)
    pdf = d / (main + ".pdf")
    log = (d / (main + ".log")).read_text(encoding="latin-1")
    errs = [l for l in log.splitlines() if l.startswith("!")]
    if errs or not pdf.exists():
        sys.exit(f"LaTeX failed in {d}: {errs[:3]}")
    return pdf


# ---------------------------------------------------------------------------
def flat_source(dst: Path) -> None:
    """Copy every file the manuscript needs into one directory tree and rewrite
    the ../tables, ../figures and ../figures/icons paths to local ones."""
    (dst / "tables").mkdir(parents=True)
    (dst / "figures").mkdir()
    (dst / "icons").mkdir()
    (dst / "authors").mkdir()
    tables, figures, icons = set(), set(), set()
    for name in TEX_FILES:
        s = (PAPER / name).read_text(encoding="utf-8")
        tables |= set(re.findall(r"\\input\{\.\./tables/generated/([\w]+)\}", s))
        figures |= set(re.findall(r"\{\.\./figures/generated/([\w.]+)\}", s))
        icons |= set(re.findall(r"\\ficon\{(\w+)\}", s))
        # \fOneAct{lock}{...} draws the icon f1_lock
        icons |= {"f1_" + a for a in re.findall(r"\\fOneAct\{(\w+)\}", s)}
        icons.discard("f1_#1")
        s = (s.replace("../tables/generated/", "tables/")
              .replace("../figures/generated/", "figures/")
              .replace("../figures/icons/", "icons/"))
        (dst / name).write_text(s, encoding="utf-8", newline="\n")
    for t in sorted(tables):
        shutil.copy2(ROOT / "tables/generated" / f"{t}.tex", dst / "tables")
    for f in sorted(figures):
        shutil.copy2(ROOT / "figures/generated" / f, dst / "figures")
    for i in sorted(icons):
        shutil.copy2(ROOT / "figures/icons" / f"{i}.png", dst / "icons")
    for p in sorted((PAPER / "authors").glob("*.jpg")):
        shutil.copy2(p, dst / "authors")
    for name in ("references.bib", "IEEEtran_doi.bst", "main.bbl"):
        shutil.copy2(PAPER / name, dst)
    acc = PAPER / "access"
    for name in CLASS_FILES:
        shutil.copy2(acc / name, dst)
    for pat in ("t1*.pfb", "t1*.tfm", "t1*.map", "*.fd"):
        for p in acc.glob(pat):
            shutil.copy2(p, dst)


def figure_numbers() -> dict[str, int]:
    aux = (PAPER / "main.aux").read_text(encoding="latin-1")
    out = {}
    for lab in FIG_NAMES:
        m = re.search(r"\\newlabel\{" + re.escape(lab) + r"\}\{\{(\d+)\}", aux)
        out[lab] = int(m.group(1))
    return out


def export_figures(src: Path, dst: Path) -> list[str]:
    dst.mkdir(parents=True)
    nums = figure_numbers()
    made = []
    tikz = {"fig:arch": ("fig1_architecture", r"\resizebox{17.6cm}{!}{\input{fig1_architecture}}"),
            "fig:conflict": ("fig_conflict", r"\input{fig_conflict}")}
    for lab, stem in FIG_NAMES.items():
        name = f"Fig{nums[lab]:02d}_{stem}"
        if lab in tikz:
            with tempfile.TemporaryDirectory() as td:
                t = Path(td)
                for p in src.iterdir():
                    if p.is_file():
                        shutil.copy2(p, t)
                shutil.copytree(src / "tables", t / "tables")
                shutil.copytree(src / "icons", t / "icons")
                doc = "\n".join([
                    r"\documentclass[border=4pt]{standalone}",
                    r"\usepackage{times}", r"\usepackage[T1]{fontenc}",
                    r"\usepackage{tikz}", r"\usepackage{graphicx}", r"\usepackage{xcolor}",
                    r"\usepackage{amsmath,amssymb}",
                    r"\usetikzlibrary{arrows.meta,positioning,calc,fit,backgrounds,"
                    r"shapes.geometric,shapes.symbols,patterns,decorations.pathreplacing}",
                    r"\input{tables/numbers}", r"\input{figstyle}",
                    r"\begin{document}", tikz[lab][1], r"\end{document}", ""])
                (t / "fig.tex").write_text(doc, encoding="utf-8")
                pdf = latex_build(t, "fig", bib=False)
                shutil.copy2(pdf, dst / f"{name}.pdf")
        else:
            fig = {"fig:leakage": "fig_rev_leakage", "fig:benign": "fig_rev_benign",
                   "fig:transfer": "fig_rev_transfer", "fig:shift": "fig_rev_shift",
                   "fig:threshold": "fig_rev_threshold", "fig:reliability": "fig_rev_reliability",
                   "fig:latency": "fig_rev_latency", "fig:sensitivity": "fig_rev_sensitivity"}[lab]
            shutil.copy2(ROOT / "figures/generated" / f"{fig}.pdf", dst / f"{name}.pdf")
        run(["pdftoppm", "-r", "600", "-png", "-singlefile", f"{name}.pdf", name], dst)
        made.append(name)
    return sorted(made)


# ---------------------------------------------------------------------------
def paper_abstract_and_keywords() -> tuple[str, list[str]]:
    txt = pdf_text(PAPER / "main.pdf")
    ab = re.search(r"ABSTRACT (.*?)\nINDEX TERMS (.*?)\n", txt, re.S)
    abstract = " ".join(ab.group(1).split())
    keywords = [k.strip().rstrip(".") for k in ab.group(2).split(",")]
    return abstract, keywords


def biographies() -> list[tuple[str, str, str]]:
    s = (PAPER / "main.tex").read_text(encoding="utf-8")
    out = []
    for photo, name, body in re.findall(
            r"\\begin\{IEEEbiography\}\[\{\\authorphoto\{([\w.]+)\}\}\]\{([^}]+)\}\n(.*?)\n\\end\{IEEEbiography\}",
            s, re.S):
        body = body.replace("--", "-").replace("\\", "")
        out.append((name, photo, " ".join(body.split())))
    return out


LETTER = {
    "opening": ("On behalf of all authors, I submit the manuscript \u201c" + TITLE + "\u201d "
                "for consideration as a Research Article in IEEE Access."),
    "body": [
        ("Machine-learning intrusion detectors for 5G and O-RAN are often reported above 99% "
         "accuracy on a random split of one dataset. Our paper asks what such a score predicts "
         "about the properties that decide whether a detector can run as an xApp in the RAN "
         "Intelligent Controller: generalization to a site that contributed no training data, "
         "alert burden at a realistic attack base rate, and decision latency within the "
         "near-real-time control loop. We measure all three for the same six architectures and "
         "two input-blind baselines on three public corpora."),
        "The main findings are:",
    ],
    "bullets": [
        ("On the radio layer of an O-RAN corpus, a random split raises macro-F1 by 0.13 over a "
         "session-disjoint split, and a model-free nearest-neighbor lookup gains about as much, "
         "consistent with the recognition of capture sessions."),
        ("In 5G-NIDD, 59% of the benign flows are copies of UDP-flood records labeled as attacks, "
         "and a published 99.9% accuracy depends on two record-position fields that tell these "
         "copies apart."),
        ("Detectors transferred between corpora reach 0.61 to 0.78 balanced accuracy on flows "
         "with consistent labels; at a declared attack prevalence of 0.002, none exceeds an "
         "operational precision of 0.092, and none passes a deployability test that combines "
         "generalization, alert burden, and latency."),
        ("Running as an xApp in a FlexRIC near-real-time RIC with an emulated E2 node, a "
         "window-level detector completes a decision and its control message in at most 4.95 ms "
         "at the 99th percentile."),
    ],
    "fit": ("The paper spans mobile networking, network security, and machine learning, which "
            "fits the multidisciplinary scope of IEEE Access, and it closes with reporting "
            "requirements for studies that claim a deployable O-RAN detection capability."),
    "confirm_intro": "We confirm that:",
    "confirm": [
        ("the manuscript is original, has not been published, and is not under consideration "
         "by any other journal or conference;"),
        "all authors have read and approved the submission and agree to its order of authorship;",
        "the authors declare no conflict of interest;",
        ("all three corpora are public, and the code, configuration, per-split results, and "
         "generators for every table, figure, and in-text number are openly available at "
         + REPO_URL + ";"),
        ("the use of AI assistance is disclosed in the Acknowledgment section, as IEEE policy "
         "requires."),
    ],
    "correspondence": ("Correspondence should be addressed to Dr. Eraj Khan, Faculty of Computer "
                       "Information Science, Higher Colleges Of Technology, Al Mizn- Baniyas "
                       "North- Abu Dhabi, United Arab Emirates (e-mail: ekhan@hct.ac.ae)."),
    "close": "Thank you for considering our manuscript.",
    "signature": ["Sincerely,", "", "Adeel Ahmad", "Submitting author, on behalf of all authors",
                  "Faculty of Computer and Information Systems, Islamic University of Madinah, "
                  "Al Madinah Al Munawarah, Saudi Arabia",
                  "ORCID: 0009-0007-5868-394X"],
}


def tex_escape(s: str) -> str:
    return (s.replace("\\", r"\textbackslash{}").replace("%", r"\%").replace("&", r"\&")
             .replace("_", r"\_").replace("#", r"\#").replace("\u201c", "``").replace("\u201d", "''"))


def cover_letter(dst: Path) -> None:
    dst.mkdir(parents=True)
    L = LETTER
    url = lambda s: s.replace(tex_escape(REPO_URL), r"\url{" + REPO_URL + "}")
    parts = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[a4paper,margin=1.9cm]{geometry}",
        r"\usepackage{times}", r"\usepackage[T1]{fontenc}", r"\usepackage{xurl}",
        r"\usepackage{enumitem}", r"\setlength{\parindent}{0pt}", r"\setlength{\parskip}{0.55em}",
        r"\pagestyle{empty}", r"\begin{document}", r"\enlargethispage{4\baselineskip}",
        r"\hfill " + DATE,
        r"The Editor-in-Chief\\ \textit{IEEE Access}",
        r"\textbf{Subject:} Submission of a Research Article, ``" + tex_escape(TITLE) + "''",
        "Dear Editor,", tex_escape(L["opening"])]
    parts += [tex_escape(p) for p in L["body"]]
    parts.append(r"\vspace{-0.6em}\begin{itemize}[leftmargin=1.5em,itemsep=0.2em]")
    parts += [r"\item " + tex_escape(b) for b in L["bullets"]]
    parts.append(r"\end{itemize}")
    parts += [tex_escape(L["fit"]), tex_escape(L["confirm_intro"]),
              r"\vspace{-0.6em}\begin{itemize}[leftmargin=1.5em,itemsep=0.2em]"]
    parts += [r"\item " + url(tex_escape(c)) for c in L["confirm"]]
    parts += [r"\end{itemize}", tex_escape(L["correspondence"]).replace("Dr. ", "Dr.~"),
              tex_escape(L["close"]),
              r"\\ ".join(tex_escape(x) if x else r"\vspace{0.4em}" for x in L["signature"]),
              r"\end{document}", ""]
    (dst / "cover_letter.tex").write_text("\n\n".join(parts), encoding="utf-8")
    latex_build(dst, "cover_letter", bib=False)
    for ext in (".aux", ".log", ".out"):
        (dst / ("cover_letter" + ext)).unlink(missing_ok=True)

    import docx
    from docx.shared import Pt
    d = docx.Document()
    st = d.styles["Normal"]
    st.font.name, st.font.size = "Times New Roman", Pt(11)
    d.add_paragraph(DATE).alignment = 2
    d.add_paragraph("The Editor-in-Chief\nIEEE Access")
    p = d.add_paragraph()
    p.add_run("Subject: ").bold = True
    p.add_run(f"Submission of a Research Article, \u201c{TITLE}\u201d")
    d.add_paragraph("Dear Editor,")
    d.add_paragraph(L["opening"])
    for b in L["body"]:
        d.add_paragraph(b)
    for b in L["bullets"]:
        d.add_paragraph(b, style="List Bullet")
    d.add_paragraph(L["fit"])
    d.add_paragraph(L["confirm_intro"])
    for c in L["confirm"]:
        d.add_paragraph(c, style="List Bullet")
    d.add_paragraph(L["correspondence"])
    d.add_paragraph(L["close"])
    d.add_paragraph("\n".join(L["signature"]))
    d.save(dst / "cover_letter.docx")


# ---------------------------------------------------------------------------
def submission_details(dst: Path, abstract: str, keywords: list[str]) -> None:
    dst.mkdir(parents=True)
    words = len(abstract.split())
    aff = {1: "Faculty of Computer and Information Systems, Islamic University of Madinah, "
              "Al Madinah Al Munawarah, Saudi Arabia",
           2: "Faculty of Computer Information Science, Higher Colleges Of Technology, "
              "Al Mizn- Baniyas North- Abu Dhabi, United Arab Emirates",
           3: "Anuradha and Vikas Sinha Department of Data Science, University of North Texas, "
              "Denton, TX, USA, 76203-5017"}
    rows = "\n".join(f"| {i} | {n} | {aff[a]} | {r or '-'} |"
                     for i, (n, a, r) in enumerate(AUTHORS, 1))
    (dst / "abstract.txt").write_text(abstract + "\n", encoding="utf-8")
    (dst / "keywords.txt").write_text("\n".join(keywords) + "\n", encoding="utf-8")
    md = f"""# Submission form details (IEEE Access, Atypon ReX)

Paste these into the submission system. Items marked **[fill in]** need the authors.

## Manuscript
- **Title:** {TITLE}
- **Running head:** Held-Out Scores and Deployment of O-RAN Intrusion Detection
- **Manuscript type:** Research Article
- **Subject categories** (as used in your previous IEEE Access submission; pick the closest offered):
  Communications technology; Computational and artificial intelligence; Computers and information processing
- **Pages:** 19 (IEEE Access template, two columns)

## Abstract ({words} words; IEEE Access limit 250)
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

- **Submitting author:** Adeel Ahmad, ORCID https://orcid.org/0009-0007-5868-394X (must be public and populated).
- **Corresponding author:** Eraj Khan, ekhan@hct.ac.ae.
- **E-mail addresses and ORCIDs of the other authors:** **[fill in]** (the system may ask for them).

## Declarations
- **Originality:** not published and not under consideration elsewhere. **[confirm]**
- **Conflict of interest:** none declared. **[confirm]**
- **Funding:** the paper names no funding source. **[fill in if any, e.g. a university grant]**
- **Data availability:** all three corpora are public (NetsLab-5GORAN-IDD and 5G-NIDD under CC-BY-4.0; the 5G core
  datasets from their authors' repository). Code and results: {REPO_URL}
- **AI use:** disclosed in the Acknowledgment section of the manuscript (required by IEEE policy).
- **Previously submitted to IEEE Access?** No (the earlier submission b57487b2 was a different paper). No list of updates needed.

## Reviewers (optional)
- Suggested reviewers: **[optional, fill in]** (independent researchers in O-RAN security or network intrusion
  detection; no co-authors or colleagues from your institutions).
- Opposed reviewers: none.
"""
    (dst / "submission_details.md").write_text(md, encoding="utf-8")


def checklist(out: Path, figs: list[str], pages: int) -> None:
    md = f"""# IEEE Access submission package

Paper: **{TITLE}**
Built {DATE} from the repository by `scripts/make_submission.py`. Manuscript: {pages} pages.

## What to upload (Atypon ReX)

| Upload slot | File |
|---|---|
| Main document (PDF) | `01_Manuscript_PDF/{STEM}_manuscript.pdf` |
| LaTeX source | `02_LaTeX_Source/{STEM}_LaTeX_source.zip` (or the files in `02_LaTeX_Source/source/`) |
| Cover letter | `03_Cover_Letter/cover_letter.pdf` (Word version: `cover_letter.docx`) |
| Figures (if asked separately) | `04_Figures/` ({len(figs)} figures, vector PDF and 600-dpi PNG) |
| Author photos (if asked separately) | `05_Author_Biographies_and_Photos/` |
| Supplementary material (optional) | `07_Supplementary_Material/` (the code is also public on GitHub) |

Form fields (title, abstract, keywords, authors, declarations): `06_Submission_Form_Details/submission_details.md`.

## Checked by the build script
- The flat LaTeX source compiles on its own with the official IEEE Access class and its text matches the PDF exactly
  (IEEE Access requires the source and PDF content to match).
- PDF under the 40 MB limit.
- Abstract at most 250 words; keywords between 3 and 10; biographies with photos for all five authors.
- AI use disclosed in the Acknowledgment section.

## Still for the authors
- [ ] Read the cover letter and confirm its declarations (originality, no conflict of interest).
- [ ] Confirm the wording of the AI-use disclosure in the Acknowledgment (edit if your use differs).
- [ ] Funding statement, if any.
- [ ] E-mail addresses and ORCIDs of all co-authors for the submission form.
- [ ] Eraj Khan's Ph.D. year in his biography (optional).
- [ ] Optional: suggested reviewers.
- [ ] All authors approve the final PDF.
"""
    (out / "README_SUBMISSION_CHECKLIST.md").write_text(md, encoding="utf-8")


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    pdf = PAPER / "main.pdf"
    pages = pdf_pages(pdf)

    d1 = OUT / "01_Manuscript_PDF"
    d1.mkdir()
    shutil.copy2(pdf, d1 / f"{STEM}_manuscript.pdf")
    if pdf.stat().st_size > 40e6:
        sys.exit("manuscript PDF exceeds 40 MB")

    d2 = OUT / "02_LaTeX_Source"
    src = d2 / "source"
    flat_source(src)
    with tempfile.TemporaryDirectory() as td:
        t = Path(td) / "build"
        shutil.copytree(src, t)
        built = latex_build(t)
        if pdf_pages(built) != pages:
            sys.exit(f"flat source gives {pdf_pages(built)} pages, not {pages}")
        norm = lambda s: " ".join(s.split())
        if norm(pdf_text(built)) != norm(pdf_text(pdf)):
            sys.exit("flat source does not reproduce the text of paper/main.pdf")
    with zipfile.ZipFile(d2 / f"{STEM}_LaTeX_source.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(src))

    cover_letter(OUT / "03_Cover_Letter")
    figs = export_figures(src, OUT / "04_Figures")

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

    checklist(OUT, figs, pages)
    print(f"wrote {OUT}")
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and "source" not in p.parts:
            print(f"  {p.relative_to(OUT)}  ({p.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
