#!/usr/bin/env python3
"""Write reports/reference_forensics_2026-09-25.md from the audit data.

Inputs:  reports/reference_forensics_2026-09-25.json (scripts/audit_references_forensic.py)
         reports/pdf_links_2026-09-25.json           (scripts/audit_pdf_links.py)
         paper/main.bbl                               (citation numbers)
The per-reference support judgments in SUPPORT are hand-written readings of each
source against the sentence that cites it. Sources for no-DOI entries were
checked on the publisher's own page (listed in OFFICIAL).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# key -> (support level, claim in the manuscript, evidence in the source)
SUPPORT = {
 "polese2023understanding": ("FULL", "O-RAN disaggregation, RIC, E2SM-KPM/RC, near-RT RIC placement", "Survey of O-RAN architecture, interfaces and RIC service models."),
 "abdalla2022toward": ("FULL", "O-RAN disaggregates the base station and adds a RIC", "Overview article on O-RAN architecture and its limits."),
 "niknam2022intelligent": ("FULL", "same background sentence", "Paper on intelligent O-RAN architecture for B5G/6G."),
 "bonati2021intelligence": ("FULL", "near-RT RIC runs close to the cells it controls", "Describes near-RT RIC control loops at the RAN edge."),
 "antonakakis2017mirai": ("FULL", "compromised IoT devices are a documented source of volumetric attacks", "Measurement study of the Mirai IoT botnet and its DDoS attacks."),
 "kolias2017ddos": ("FULL", "same", "Article on Mirai and other IoT DDoS botnets."),
 "polese2023coloran": ("FULL", "platforms for building xApps exist", "ColO-RAN develops ML-based xApps on experimental platforms."),
 "schmidt2021flexric": ("FULL", "platforms for building xApps exist", "FlexRIC is an SDK for building RICs and xApps."),
 "wen2024spector": ("FULL", "detectors in or beside the O-RAN loop have been built, and 5G-Spector does L3 attack detection as an O-RAN compliant service", "Title and paper: O-RAN compliant layer-3 cellular attack detection service."),
 "scalingi2024detran": ("FULL", "Det-RAN detects attacks from cross-layer data in real time", "Title and paper: data-driven cross-layer real-time attack detection in 5G open RANs."),
 "samarakoon2022niddarxiv": ("FULL", "authors report binary accuracy 99.85 to 99.95% for four of five classifiers on a random 70/30 split", "Its accuracy table, and our reproduction (EXP-055) matches it."),
 "ilias2024moe5g": ("FULL", "later work reports weighted F1 of up to 99.95%", "arXiv v2 abstract: 'weighted F1-score up to 99.95%' on 5G-NIDD."),
 "layeghy2022generalisability": ("FULL", "intrusion detectors transfer poorly between independently collected datasets", "Cross-domain evaluation of ML-based NIDS across datasets."),
 "layeghy2023benchmarking": ("FULL", "same", "Compares synthetic and real-world NIDS datasets, finds poor transfer."),
 "axelsson2000baserate": ("FULL", "base-rate argument", "The original base-rate fallacy paper for intrusion detection."),
 "sommer2010outside": ("FULL", "closed-world critique", "The original closed-world critique of ML for NIDS."),
 "etsi_e2gap": ("FULL", "near-RT latency requirements from 10 ms to 1 s", "Clause read in the PDF: 'E2 interface shall support latency requirements for near-real-time optimization, i.e. from 10 milliseconds up to 1 second'."),
 "arp2022dosdonts": ("FULL", "evaluation pitfalls in security ML, sampling bias and leakage", "Catalogue of ten pitfalls including sampling bias and data snooping."),
 "pendlebury2019tesseract": ("FULL", "temporal and spatial bias formalized", "Defines spatial and temporal bias constraints for malware classification."),
 "abraheem2026bidirectional": ("FULL", "XGBoost transfer between our two corpora on 15 harmonized features, BA 0.50-0.56 and 0.52-0.83", "Journal page: XGBoost, 15 harmonized features, per-task BA 0.505/0.500/0.558 and 0.518/0.807/0.834."),
 "obiuwevwi2026realtime": ("FULL", "inference inside a real near-RT RIC measured, microsecond range for LR and a small MLP", "Abstract (arXiv v2): OAI + FlexRIC testbed, LR 1-5 us, MLP 10-25 us."),
 "nugraha2025fivegdatasets": ("FULL", "D_C: 5G core testbed (Open5GS), flow files with SYN, ICMP, PFCP attacks", "Dataset paper and repository files used in EXP-058."),
 "bonati2023openrangym": ("FULL", "platforms make experimental xApps practical", "OpenRAN Gym: AI/ML development and testing for O-RAN."),
 "bonati2021scope": ("FULL", "same", "SCOPE prototyping platform for NextG."),
 "nikaein2014oai": ("FULL", "open radio stacks", "OpenAirInterface platform paper."),
 "gomez2016srslte": ("FULL", "open radio stacks", "srsLTE platform paper."),
 "etsi_wg11_threat": ("FULL", "the O-RAN Alliance threat model identifies the RIC and xApps as attack surface", "Clauses 7.4.1.4 (threats against Near-RT RIC) and 7.4.1.6 (threats against xApps), read in the PDF."),
 "liyanage2023openran": ("FULL", "independent analyses of O-RAN security", "Open RAN security challenges article."),
 "mimran2022security": ("FULL", "same", "Security analysis of open radio access networks."),
 "groen2025implementing": ("FULL", "security mechanisms across O-RAN interfaces implemented and measured", "Title and paper: implementing and evaluating security in O-RAN interfaces."),
 "fard2026crosslayer": ("FULL", "fusion of radio telemetry and flow records on NetsLab-5GORAN-IDD", "arXiv HTML: 'We evaluate on the NetsLab-5GORAN-IDD dataset ... pairs CU Zeek flow records with DU radio telemetry'. It is a preprint and the paper does not call it peer reviewed."),
 "koroniotis2019botiot": ("FULL", "IoT benchmark corpora exist", "Bot-IoT dataset paper."),
 "moustafa2021toniot": ("FULL", "same", "TON_IoT dataset paper."),
 "ferrag2022edgeiiot": ("FULL", "same", "Edge-IIoTset dataset paper."),
 "neto2023ciciot": ("FULL", "same", "CICIoT2023 dataset paper."),
 "sharafaldin2018cicids": ("FULL", "same (CIC-IDS2017)", "CIC-IDS2017 dataset paper."),
 "samarakoon2022nidd": ("FULL", "5G-NIDD, captured on a functioning 5G test network (dataset record)", "IEEE DataPort record, DataCite DOI."),
 "siriwardhana2025descriptor": ("FULL", "same (peer-reviewed descriptor)", "IEEE Data Descriptions descriptor of 5G-NIDD."),
 "abedzadeh2025netslab": ("FULL", "NetsLab-5GORAN-IDD pairs flow records with radio telemetry from an O-RAN testbed", "IEEE Data Descriptions descriptor. Fard et al. describe the same pairing."),
 "sarhan2021netflow": ("FULL", "standardized NetFlow feature sets", "NetFlow datasets for ML-based NIDS."),
 "sarhan2022standard": ("FULL", "same", "Standard feature set for NIDS datasets."),
 "engelen2021troubleshooting": ("FULL", "labeling and flow-construction faults in CIC-IDS2017", "Title and paper: troubleshooting CICIDS2017."),
 "flood2024smells": ("FULL", "design flaws that let a classifier score well without learning the attack recur across NIDS benchmarks", "Bad design smells in benchmark NIDS datasets."),
 "kapoor2023leakage": ("FULL", "leakage", "Leakage taxonomy across ML-based science."),
 "apruzzese2023role": ("FULL after rewording", "the gap between reported and operational effectiveness is examined across security domains", "Broad analysis of ML in cybersecurity practice. The earlier word 'surveyed' was changed because the paper is more than a survey."),
 "kus2022falsesense": ("FULL", "industrial IDS show the same pattern when re-evaluated on data they were not tuned on", "Revisits ML-based industrial IDS and finds poor generalization to unseen attacks."),
 "dhooge2020interdataset": ("FULL", "cross-dataset generalization is poor", "Inter-dataset generalization study."),
 "saerens2002adjusting": ("FULL", "EM prior adjustment", "The EM procedure for new priors."),
 "lipton2018bbse": ("FULL", "black-box shift estimation", "BBSE paper (PMLR page checked)."),
 "guo2017calibration": ("FULL", "calibration and temperature scaling", "PMLR page checked."),
 "ovadia2019trust": ("FULL", "calibration under shift", "NeurIPS proceedings page checked."),
 "fawcett2007pav": ("FULL", "isotonic regression yields the ROC convex hull on its fitting data", "Exactly the paper's result (PAV = ROC convex hull)."),
 "rabanser2019failing": ("FULL", "shift detection from unlabeled data", "NeurIPS proceedings page checked."),
 "sun2016coral": ("FULL", "CORAL covariance alignment", "The CORAL paper."),
 "nadeau2003inference": ("FULL", "corrected resampled t-test, variance factor 1/J + n_test/n_train", "The source of that correction."),
 "breiman2001random": ("FULL", "random forest", "Original paper."),
 "chen2016xgboost": ("FULL", "XGBoost", "Original paper."),
 "pedregosa2011scikit": ("FULL", "scikit-learn (HGB is its estimator)", "JMLR page checked."),
 "cho2014gru": ("FULL", "GRU", "The paper that introduced the GRU cell."),
 "liu2008isolation": ("FULL", "isolation forest", "Original paper."),
 "jin2013softcell": ("FULL", "several hundred flows per second at a heavily loaded LTE base station", "arXiv version: 'we expect the actual flow arrival rate to be around several hundred flows per second' (99.999th percentile of bearer arrivals)."),
 "lundberg2017shap": ("FULL", "feature attribution (future work only)", "SHAP paper, NeurIPS page checked."),
}

OFFICIAL = {
 "antonakakis2017mirai": "usenix.org (19 authors, pp. 1093-1110)",
 "arp2022dosdonts": "usenix.org (8 authors, pp. 3971-3988)",
 "pendlebury2019tesseract": "usenix.org (5 authors, pp. 729-746)",
 "pedregosa2011scikit": "jmlr.org (16 authors, 12:2825-2830)",
 "lipton2018bbse": "proceedings.mlr.press v80 (3 authors, pp. 3122-3130)",
 "guo2017calibration": "proceedings.mlr.press v70 (4 authors, pp. 1321-1330)",
 "ovadia2019trust": "proceedings.neurips.cc (9 authors)",
 "rabanser2019failing": "papers.nips.cc (3 authors)",
 "lundberg2017shap": "papers.nips.cc (2 authors)",
 "samarakoon2022niddarxiv": "arxiv.org/abs/2212.01298 (8 authors)",
 "ilias2024moe5g": "arxiv.org/abs/2412.03483 (5 authors)",
 "fard2026crosslayer": "arxiv.org/abs/2606.22450 (3 authors)",
 "abraheem2026bidirectional": "waujpas.com article page (2 authors, vol. 4 no. 2, 7 Aug 2026)",
 "etsi_e2gap": "etsi.org PDF, title page and clause read",
 "etsi_wg11_threat": "etsi.org PDF, title page and clauses read",
 "samarakoon2022nidd": "DataCite record for 10.21227/xtep-hv36 (not a Crossref DOI)",
}

TYPE = {"article": "journal article", "inproceedings": "conference paper",
        "misc": "preprint or dataset", "techreport": "standard or specification"}


def main():
    R = {r["key"]: r for r in json.loads((ROOT / "reports/reference_forensics_2026-09-25.json").read_text(encoding="utf-8"))}
    L = json.loads((ROOT / "reports/pdf_links_2026-09-25.json").read_text(encoding="utf-8"))
    bbl = (ROOT / "paper/main.bbl").read_text(encoding="utf-8")
    order = re.findall(r"\\bibitem\{([^}]+)\}", bbl)
    nolink = set(L["cite_links_missing_for"])
    rows, author_issues, counts = [], [], dict(verified=0, warning=0, problem=0)
    for n, key in enumerate(order, 1):
        r = R.get(key, {})
        cr, oa = r.get("crossref"), r.get("openalex")
        ai_cr = r.get("author_issues_crossref", [])
        real = [i for i in ai_cr if i.startswith(("MISMATCH", "missing", "extra"))]
        nb = len(r.get("bib_authors", []))
        if cr:
            auth = f"{nb} of {len(cr['authors'])}, order checked (Crossref)"
            src = "doi.org " + str((r.get("doi_org") or ["?"])[0]) + ", Crossref, OpenAlex"
        elif key in OFFICIAL:
            auth = f"{nb}, order checked ({OFFICIAL[key].split(' (')[0]})"
            src = OFFICIAL[key]
        else:
            auth = f"{nb}"
            src = "n/a"
        level, claim, ev = SUPPORT.get(key, ("NOT RECORDED", "", ""))
        status = "VERIFIED"
        if real:
            status = "WARNING"
            author_issues.append((n, key, real))
        if level not in ("FULL", "FULL after rewording"):
            status = "WARNING"
        counts["verified" if status == "VERIFIED" else "warning"] += 1
        doi = r.get("doi") or "none (no DOI issued)"
        pdf = "range endpoint only" if key in nolink else "yes"
        rows.append(f"| {n} | `{key}` | {TYPE.get(r.get('bibtype'), r.get('bibtype'))} | {doi} | {src} | {auth} | {pdf} | {level}: {claim}. Source: {ev} | **{status}** |")
    head = ["| # | Key | Type | DOI | Checked against | Authors (bib vs official) | PDF link | Citation support | Status |",
            "|---|---|---|---|---|---|---|---|---|"]
    out = ROOT / "reports/_forensic_table.md"
    out.write_text("\n".join(head + rows) + "\n", encoding="utf-8")
    print(counts, "author issues:", author_issues)


if __name__ == "__main__":
    main()
