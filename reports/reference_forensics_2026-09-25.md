# Reference forensics, 2026-09-25

Manuscript: *What Held-Out Accuracy Predicts About Deploying Intrusion Detection in
O-RAN*. Every printed reference was checked against independent records. Nothing in
this report was filled in from memory.

How it was done:

- `scripts/audit_references_forensic.py` resolves every DOI at doi.org, reads the
  Crossref record (title, subtitle, ordered author list, venue, type, year, volume,
  issue, pages) and a second, independent OpenAlex record. It then compares the
  author lists with the .bib position by position. Raw output:
  `reports/reference_forensics_2026-09-25.json`.
- The 16 entries without a Crossref DOI were checked on the publisher's own page:
  USENIX, PMLR, JMLR, NeurIPS, arXiv, the WAUJPAS article page, the ETSI PDFs, and
  DataCite for the IEEE DataPort DOI.
- `scripts/audit_pdf_links.py` reads every hyperlink in the final `paper/main.pdf`.
  Raw output: `reports/pdf_links_2026-09-25.json`.
- Each citation was read against the sentence that cites it. Where the source says
  less than the sentence, the sentence was changed. The source was never stretched to fit.

## Report A: executive result

| Item | Count |
|---|---|
| References printed | 62 |
| Citation commands in the text | 97 citation links in the PDF |
| Verified | 62 |
| Partial | 0 |
| Needs manual review | 0 (one name-spelling note, see Report C) |
| Problematic | 0 after fixes |
| Likely fabricated | 0 |
| Duplicates | 0 (three 5G-NIDD records are three different objects, see Report D) |
| Wrong DOI | 0 |
| DOIs that resolve | 47 of 47 (46 Crossref, 1 DataCite) |
| Missing DOI where one exists | 0 |
| Author problems | 0 after fix F3 |
| Publication-type problems | 0 after fix F5 |
| Citation-support problems | 0 after fixes F6, F7 |
| Broken URLs | 0 (one journal page refuses scripted requests but opens in a browser) |
| Broken repository links | 0 |
| Non-clickable PDF links | 0 broken. 5 references inside compressed ranges such as [1]–[3] have no link of their own, which is standard IEEE `cite` behaviour |

**Overall reference integrity: PASS WITH WARNINGS.** The warnings are the two
notes in Reports C and G. Neither is an error in the manuscript.

## Fixes made during this audit

| ID | Problem found | Fix |
|---|---|---|
| F1 | The final PDF had no hyperlinks at all. The IEEE Access class loads hyperref only in its JTEHM mode | `\usepackage[hidelinks,bookmarks=false]{hyperref}`. The page looks the same, and citations, cross-references, URLs and DOIs are now clickable |
| F2 | No DOI was printed in the bibliography. IEEEtran.bst ignores the doi field, but IEEE reference style ends an entry with "doi: …" | New `paper/IEEEtran_doi.bst`, identical to IEEEtran.bst v1.14 except that an entry with a DOI ends with a linked "doi: …" |
| F3 | Author names of the ICCCN 2026 paper (Obiuwevwi et al.) followed the arXiv spelling, not the published record | Now "V. Nannou" and "M. E. Ur Rahman", as in the DOI record IEEE deposited. The arXiv spelling is kept in a .bib comment |
| F4 | I introduced an error while fixing F3: a `%` comment inside the BibTeX entry emptied reference [21] in the PDF | Comment moved outside the entry. `scripts/build_paper.py` now fails on any BibTeX warning or error, so an empty reference cannot pass silently again |
| F5 | Apruzzese et al. was described as a survey ("surveyed in") | Now "examined across security domains in". The paper is a broad analysis of ML in security practice, not only a survey |
| F6 | Shi et al. (edge computing vision, 2016) was cited for "the near-real-time RIC runs close to the cells it controls". It says nothing about the RIC | Replaced by Bonati et al. and Polese et al., which describe RIC placement. Shi et al. is no longer cited |
| F7 | One sentence cited ColO-RAN and FlexRIC as if they were detection work | Split: those two are cited for xApp platforms, and 5G-Spector and Det-RAN for detectors |
| F8 | Page ranges missing for Niknam et al. and Scalingi et al. | Added from Crossref: pp. 215–220 and 41–50 |
| F9 | O-RAN WG3 and WG11 documents sit behind a licence click-through and could not be checked | Replaced by their public ETSI editions, both opened and read (see Report G) |
| F10 | λ_b had no source | Added Jin et al. (CoNEXT 2013), Crossref-checked. The quoted sentence was read in the arXiv version |

## Report B: reference-by-reference audit

"Checked against" names the independent records used. "Authors" gives the bib count
against the official count, after a position-by-position check of every name. "PDF link"
says whether the in-text citation is clickable.

| # | Key | Type | DOI | Checked against | Authors (bib vs official) | PDF link | Citation support | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | `polese2023understanding` | journal article | 10.1109/COMST.2023.3239220 | doi.org 302, Crossref, OpenAlex | 5 of 5, order checked (Crossref) | yes | FULL: O-RAN disaggregation, RIC, E2SM-KPM/RC, near-RT RIC placement. Source: Survey of O-RAN architecture, interfaces and RIC service models. | **VERIFIED** |
| 2 | `abdalla2022toward` | journal article | 10.1109/MNET.108.2100659 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | range endpoint only | FULL: O-RAN disaggregates the base station and adds a RIC. Source: Overview article on O-RAN architecture and its limits. | **VERIFIED** |
| 3 | `niknam2022intelligent` | conference paper | 10.1109/GCWkshps56602.2022.10008676 | doi.org 302, Crossref, OpenAlex | 8 of 8, order checked (Crossref) | yes | FULL: same background sentence. Source: Paper on intelligent O-RAN architecture for B5G/6G. | **VERIFIED** |
| 4 | `bonati2021intelligence` | journal article | 10.1109/MCOM.101.2001120 | doi.org 302, Crossref, OpenAlex | 5 of 5, order checked (Crossref) | yes | FULL: near-RT RIC runs close to the cells it controls. Source: Describes near-RT RIC control loops at the RAN edge. | **VERIFIED** |
| 5 | `antonakakis2017mirai` | conference paper | none (no DOI issued) | usenix.org (19 authors, pp. 1093-1110) | 19, order checked (usenix.org) | yes | FULL: compromised IoT devices are a documented source of volumetric attacks. Source: Measurement study of the Mirai IoT botnet and its DDoS attacks. | **VERIFIED** |
| 6 | `kolias2017ddos` | journal article | 10.1109/MC.2017.201 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | yes | FULL: same. Source: Article on Mirai and other IoT DDoS botnets. | **VERIFIED** |
| 7 | `polese2023coloran` | journal article | 10.1109/TMC.2022.3188013 | doi.org 302, Crossref, OpenAlex | 5 of 5, order checked (Crossref) | yes | FULL: platforms for building xApps exist. Source: ColO-RAN develops ML-based xApps on experimental platforms. | **VERIFIED** |
| 8 | `schmidt2021flexric` | conference paper | 10.1145/3485983.3494870 | doi.org 302, Crossref, OpenAlex | 3 of 3, order checked (Crossref) | yes | FULL: platforms for building xApps exist. Source: FlexRIC is an SDK for building RICs and xApps. | **VERIFIED** |
| 9 | `wen2024spector` | conference paper | 10.14722/ndss.2024.24527 | doi.org 302, Crossref, OpenAlex | 5 of 5, order checked (Crossref) | yes | FULL: detectors in or beside the O-RAN loop have been built, and 5G-Spector does L3 attack detection as an O-RAN compliant service. Source: Title and paper: O-RAN compliant layer-3 cellular attack detection service. | **VERIFIED** |
| 10 | `scalingi2024detran` | conference paper | 10.1109/INFOCOM52122.2024.10621223 | doi.org 302, Crossref, OpenAlex | 5 of 5, order checked (Crossref) | yes | FULL: Det-RAN detects attacks from cross-layer data in real time. Source: Title and paper: data-driven cross-layer real-time attack detection in 5G open RANs. | **VERIFIED** |
| 11 | `samarakoon2022niddarxiv` | preprint or dataset | none (no DOI issued) | arxiv.org/abs/2212.01298 (8 authors) | 8, order checked (arxiv.org/abs/2212.01298) | yes | FULL: authors report binary accuracy 99.85 to 99.95% for four of five classifiers on a random 70/30 split. Source: Its accuracy table, and our reproduction (EXP-055) matches it. | **VERIFIED** |
| 12 | `ilias2024moe5g` | preprint or dataset | none (no DOI issued) | arxiv.org/abs/2412.03483 (5 authors) | 5, order checked (arxiv.org/abs/2412.03483) | yes | FULL: later work reports weighted F1 of up to 99.95%. Source: arXiv v2 abstract: 'weighted F1-score up to 99.95%' on 5G-NIDD. | **VERIFIED** |
| 13 | `layeghy2022generalisability` | journal article | 10.1016/j.compeleceng.2023.108692 | doi.org 302, Crossref, OpenAlex | 2 of 2, order checked (Crossref) | yes | FULL: intrusion detectors transfer poorly between independently collected datasets. Source: Cross-domain evaluation of ML-based NIDS across datasets. | **VERIFIED** |
| 14 | `layeghy2023benchmarking` | journal article | 10.1016/j.jisa.2023.103689 | doi.org 302, Crossref, OpenAlex | 3 of 3, order checked (Crossref) | yes | FULL: same. Source: Compares synthetic and real-world NIDS datasets, finds poor transfer. | **VERIFIED** |
| 15 | `axelsson2000baserate` | journal article | 10.1145/357830.357849 | doi.org 302, Crossref, OpenAlex | 1 of 1, order checked (Crossref) | yes | FULL: base-rate argument. Source: The original base-rate fallacy paper for intrusion detection. | **VERIFIED** |
| 16 | `sommer2010outside` | conference paper | 10.1109/SP.2010.25 | doi.org 302, Crossref, OpenAlex | 2 of 2, order checked (Crossref) | yes | FULL: closed-world critique. Source: The original closed-world critique of ML for NIDS. | **VERIFIED** |
| 17 | `etsi_e2gap` | standard or specification | none (no DOI issued) | etsi.org PDF, title page and clause read | 1, order checked (etsi.org PDF, title page and clause read) | yes | FULL: near-RT latency requirements from 10 ms to 1 s. Source: Clause read in the PDF: 'E2 interface shall support latency requirements for near-real-time optimization, i.e. from 10 milliseconds up to 1 second'. | **VERIFIED** |
| 18 | `arp2022dosdonts` | conference paper | none (no DOI issued) | usenix.org (8 authors, pp. 3971-3988) | 8, order checked (usenix.org) | yes | FULL: evaluation pitfalls in security ML, sampling bias and leakage. Source: Catalogue of ten pitfalls including sampling bias and data snooping. | **VERIFIED** |
| 19 | `pendlebury2019tesseract` | conference paper | none (no DOI issued) | usenix.org (5 authors, pp. 729-746) | 5, order checked (usenix.org) | yes | FULL: temporal and spatial bias formalized. Source: Defines spatial and temporal bias constraints for malware classification. | **VERIFIED** |
| 20 | `abraheem2026bidirectional` | journal article | none (no DOI issued) | waujpas.com article page (2 authors, vol. 4 no. 2, 7 Aug 2026) | 2, order checked (waujpas.com article page) | yes | FULL: XGBoost transfer between our two corpora on 15 harmonized features, BA 0.50-0.56 and 0.52-0.83. Source: Journal page: XGBoost, 15 harmonized features, per-task BA 0.505/0.500/0.558 and 0.518/0.807/0.834. | **VERIFIED** |
| 21 | `obiuwevwi2026realtime` | conference paper | 10.1109/ICCCN69946.2026.11662852 | doi.org 302, Crossref, OpenAlex | 10 of 10, order checked (Crossref) | yes | FULL: inference inside a real near-RT RIC measured, microsecond range for LR and a small MLP. Source: Abstract (arXiv v2): OAI + FlexRIC testbed, LR 1-5 us, MLP 10-25 us. | **VERIFIED** |
| 22 | `nugraha2025fivegdatasets` | conference paper | 10.1109/CSR64739.2025.11130023 | doi.org 302, Crossref, OpenAlex | 10 of 10, order checked (Crossref) | yes | FULL: D_C: 5G core testbed (Open5GS), flow files with SYN, ICMP, PFCP attacks. Source: Dataset paper and repository files used in EXP-058. | **VERIFIED** |
| 23 | `bonati2023openrangym` | journal article | 10.1016/j.comnet.2022.109502 | doi.org 302, Crossref, OpenAlex | 5 of 5, order checked (Crossref) | yes | FULL: platforms make experimental xApps practical. Source: OpenRAN Gym: AI/ML development and testing for O-RAN. | **VERIFIED** |
| 24 | `bonati2021scope` | conference paper | 10.1145/3458864.3466863 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | yes | FULL: same. Source: SCOPE prototyping platform for NextG. | **VERIFIED** |
| 25 | `nikaein2014oai` | journal article | 10.1145/2677046.2677053 | doi.org 302, Crossref, OpenAlex | 6 of 6, order checked (Crossref) | yes | FULL: open radio stacks. Source: OpenAirInterface platform paper. | **VERIFIED** |
| 26 | `gomez2016srslte` | conference paper | 10.1145/2980159.2980163 | doi.org 302, Crossref, OpenAlex | 6 of 6, order checked (Crossref) | yes | FULL: open radio stacks. Source: srsLTE platform paper. | **VERIFIED** |
| 27 | `etsi_wg11_threat` | standard or specification | none (no DOI issued) | etsi.org PDF, title page and clauses read | 1, order checked (etsi.org PDF, title page and clauses read) | yes | FULL: the O-RAN Alliance threat model identifies the RIC and xApps as attack surface. Source: Clauses 7.4.1.4 (threats against Near-RT RIC) and 7.4.1.6 (threats against xApps), read in the PDF. | **VERIFIED** |
| 28 | `liyanage2023openran` | journal article | 10.1016/j.jnca.2023.103621 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | yes | FULL: independent analyses of O-RAN security. Source: Open RAN security challenges article. | **VERIFIED** |
| 29 | `mimran2022security` | journal article | 10.1016/j.cose.2022.102890 | doi.org 302, Crossref, OpenAlex | 8 of 8, order checked (Crossref) | yes | FULL: same. Source: Security analysis of open radio access networks. | **VERIFIED** |
| 30 | `groen2025implementing` | journal article | 10.1109/MNET.2024.3434419 | doi.org 302, Crossref, OpenAlex | 7 of 7, order checked (Crossref) | yes | FULL: security mechanisms across O-RAN interfaces implemented and measured. Source: Title and paper: implementing and evaluating security in O-RAN interfaces. | **VERIFIED** |
| 31 | `fard2026crosslayer` | preprint or dataset | none (no DOI issued) | arxiv.org/abs/2606.22450 (3 authors) | 3, order checked (arxiv.org/abs/2606.22450) | yes | FULL: fusion of radio telemetry and flow records on NetsLab-5GORAN-IDD. Source: arXiv HTML: 'We evaluate on the NetsLab-5GORAN-IDD dataset ... pairs CU Zeek flow records with DU radio telemetry'. It is a preprint and the paper does not call it peer reviewed. | **VERIFIED** |
| 32 | `koroniotis2019botiot` | journal article | 10.1016/j.future.2019.05.041 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | yes | FULL: IoT benchmark corpora exist. Source: Bot-IoT dataset paper. | **VERIFIED** |
| 33 | `moustafa2021toniot` | journal article | 10.1016/j.scs.2021.102994 | doi.org 302, Crossref, OpenAlex | 1 of 1, order checked (Crossref) | range endpoint only | FULL: same. Source: TON_IoT dataset paper. | **VERIFIED** |
| 34 | `ferrag2022edgeiiot` | journal article | 10.1109/ACCESS.2022.3165809 | doi.org 302, Crossref, OpenAlex | 5 of 5, order checked (Crossref) | range endpoint only | FULL: same. Source: Edge-IIoTset dataset paper. | **VERIFIED** |
| 35 | `neto2023ciciot` | journal article | 10.3390/s23135941 | doi.org 302, Crossref, OpenAlex | 6 of 6, order checked (Crossref) | range endpoint only | FULL: same. Source: CICIoT2023 dataset paper. | **VERIFIED** |
| 36 | `sharafaldin2018cicids` | conference paper | 10.5220/0006639801080116 | doi.org 302, Crossref, OpenAlex | 3 of 3, order checked (Crossref) | yes | FULL: same (CIC-IDS2017). Source: CIC-IDS2017 dataset paper. | **VERIFIED** |
| 37 | `samarakoon2022nidd` | preprint or dataset | 10.21227/xtep-hv36 | DataCite record for 10.21227/xtep-hv36 (not a Crossref DOI) | 8, order checked (DataCite record for 10.21227/xtep-hv36) | yes | FULL: 5G-NIDD, captured on a functioning 5G test network (dataset record). Source: IEEE DataPort record, DataCite DOI. | **VERIFIED** |
| 38 | `siriwardhana2025descriptor` | journal article | 10.1109/IEEEDATA.2025.3592888 | doi.org 302, Crossref, OpenAlex | 8 of 8, order checked (Crossref) | yes | FULL: same (peer-reviewed descriptor). Source: IEEE Data Descriptions descriptor of 5G-NIDD. | **VERIFIED** |
| 39 | `abedzadeh2025netslab` | journal article | 10.1109/IEEEDATA.2025.3614167 | doi.org 302, Crossref, OpenAlex | 5 of 5, order checked (Crossref) | yes | FULL: NetsLab-5GORAN-IDD pairs flow records with radio telemetry from an O-RAN testbed. Source: IEEE Data Descriptions descriptor. Fard et al. describe the same pairing. | **VERIFIED** |
| 40 | `sarhan2021netflow` | conference paper | 10.1007/978-3-030-72802-1_9 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | yes | FULL: standardized NetFlow feature sets. Source: NetFlow datasets for ML-based NIDS. | **VERIFIED** |
| 41 | `sarhan2022standard` | journal article | 10.1007/s11036-021-01843-0 | doi.org 302, Crossref, OpenAlex | 3 of 3, order checked (Crossref) | yes | FULL: same. Source: Standard feature set for NIDS datasets. | **VERIFIED** |
| 42 | `engelen2021troubleshooting` | conference paper | 10.1109/SPW53761.2021.00009 | doi.org 302, Crossref, OpenAlex | 3 of 3, order checked (Crossref) | yes | FULL: labeling and flow-construction faults in CIC-IDS2017. Source: Title and paper: troubleshooting CICIDS2017. | **VERIFIED** |
| 43 | `flood2024smells` | conference paper | 10.1109/EuroSP60621.2024.00042 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | yes | FULL: design flaws that let a classifier score well without learning the attack recur across NIDS benchmarks. Source: Bad design smells in benchmark NIDS datasets. | **VERIFIED** |
| 44 | `kapoor2023leakage` | journal article | 10.1016/j.patter.2023.100804 | doi.org 302, Crossref, OpenAlex | 2 of 2, order checked (Crossref) | yes | FULL: leakage. Source: Leakage taxonomy across ML-based science. | **VERIFIED** |
| 45 | `apruzzese2023role` | journal article | 10.1145/3545574 | doi.org 302, Crossref, OpenAlex | 7 of 7, order checked (Crossref) | yes | FULL after rewording: the gap between reported and operational effectiveness is examined across security domains. Source: Broad analysis of ML in cybersecurity practice. The earlier word 'surveyed' was changed because the paper is more than a survey. | **VERIFIED** |
| 46 | `kus2022falsesense` | conference paper | 10.1145/3494107.3522773 | doi.org 302, Crossref, OpenAlex | 8 of 8, order checked (Crossref) | yes | FULL: industrial IDS show the same pattern when re-evaluated on data they were not tuned on. Source: Revisits ML-based industrial IDS and finds poor generalization to unseen attacks. | **VERIFIED** |
| 47 | `dhooge2020interdataset` | journal article | 10.1016/j.jisa.2020.102564 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | yes | FULL: cross-dataset generalization is poor. Source: Inter-dataset generalization study. | **VERIFIED** |
| 48 | `saerens2002adjusting` | journal article | 10.1162/089976602753284446 | doi.org 302, Crossref, OpenAlex | 3 of 3, order checked (Crossref) | yes | FULL: EM prior adjustment. Source: The EM procedure for new priors. | **VERIFIED** |
| 49 | `lipton2018bbse` | conference paper | none (no DOI issued) | proceedings.mlr.press v80 (3 authors, pp. 3122-3130) | 3, order checked (proceedings.mlr.press v80) | yes | FULL: black-box shift estimation. Source: BBSE paper (PMLR page checked). | **VERIFIED** |
| 50 | `guo2017calibration` | conference paper | none (no DOI issued) | proceedings.mlr.press v70 (4 authors, pp. 1321-1330) | 4, order checked (proceedings.mlr.press v70) | yes | FULL: calibration and temperature scaling. Source: PMLR page checked. | **VERIFIED** |
| 51 | `ovadia2019trust` | conference paper | none (no DOI issued) | proceedings.neurips.cc (9 authors) | 9, order checked (proceedings.neurips.cc) | range endpoint only | FULL: calibration under shift. Source: NeurIPS proceedings page checked. | **VERIFIED** |
| 52 | `fawcett2007pav` | journal article | 10.1007/s10994-007-5011-0 | doi.org 302, Crossref, OpenAlex | 2 of 2, order checked (Crossref) | yes | FULL: isotonic regression yields the ROC convex hull on its fitting data. Source: Exactly the paper's result (PAV = ROC convex hull). | **VERIFIED** |
| 53 | `rabanser2019failing` | conference paper | none (no DOI issued) | papers.nips.cc (3 authors) | 3, order checked (papers.nips.cc) | yes | FULL: shift detection from unlabeled data. Source: NeurIPS proceedings page checked. | **VERIFIED** |
| 54 | `sun2016coral` | conference paper | 10.1609/aaai.v30i1.10306 | doi.org 302, Crossref, OpenAlex | 3 of 3, order checked (Crossref) | yes | FULL: CORAL covariance alignment. Source: The CORAL paper. | **VERIFIED** |
| 55 | `nadeau2003inference` | journal article | 10.1023/A:1024068626366 | doi.org 302, Crossref, OpenAlex | 2 of 2, order checked (Crossref) | yes | FULL: corrected resampled t-test, variance factor 1/J + n_test/n_train. Source: The source of that correction. | **VERIFIED** |
| 56 | `breiman2001random` | journal article | 10.1023/A:1010933404324 | doi.org 302, Crossref, OpenAlex | 1 of 1, order checked (Crossref) | yes | FULL: random forest. Source: Original paper. | **VERIFIED** |
| 57 | `chen2016xgboost` | conference paper | 10.1145/2939672.2939785 | doi.org 302, Crossref, OpenAlex | 2 of 2, order checked (Crossref) | yes | FULL: XGBoost. Source: Original paper. | **VERIFIED** |
| 58 | `pedregosa2011scikit` | journal article | none (no DOI issued) | jmlr.org (16 authors, 12:2825-2830) | 16, order checked (jmlr.org) | yes | FULL: scikit-learn (HGB is its estimator). Source: JMLR page checked. | **VERIFIED** |
| 59 | `cho2014gru` | conference paper | 10.3115/v1/D14-1179 | doi.org 302, Crossref, OpenAlex | 7 of 7, order checked (Crossref) | yes | FULL: GRU. Source: The paper that introduced the GRU cell. | **VERIFIED** |
| 60 | `liu2008isolation` | conference paper | 10.1109/ICDM.2008.17 | doi.org 302, Crossref, OpenAlex | 3 of 3, order checked (Crossref) | yes | FULL: isolation forest. Source: Original paper. | **VERIFIED** |
| 61 | `jin2013softcell` | conference paper | 10.1145/2535372.2535377 | doi.org 302, Crossref, OpenAlex | 4 of 4, order checked (Crossref) | yes | FULL: several hundred flows per second at a heavily loaded LTE base station. Source: arXiv version: 'we expect the actual flow arrival rate to be around several hundred flows per second' (99.999th percentile of bearer arrivals). | **VERIFIED** |
| 62 | `lundberg2017shap` | conference paper | none (no DOI issued) | papers.nips.cc (2 authors) | 2, order checked (papers.nips.cc) | yes | FULL: feature attribution (future work only). Source: SHAP paper, NeurIPS page checked. | **VERIFIED** |

## Report C: author forensics

Every author list was compared position by position with Crossref (46 DOI entries),
OpenAlex, and the official pages for the 16 entries without a Crossref DOI.
No missing author, extra author, or order error remains.

One note, not an error in the manuscript: for Obiuwevwi et al. (ICCCN 2026), the DOI
record spells two co-authors "Valentina Nannou" and "Muhammad Enayet Ur Rahman", and the
authors' own arXiv version spells them "Valentina Nanou" and "Muhammad Enayetur Rahman".
The paper cites the published version, so it follows the DOI record. IEEE Xplore renders its
pages with JavaScript and could not be read directly, so check the page before submission.

Harmless formatting differences seen and accepted: OpenAlex stores some names as
"Family, Given". "Alex Smola" and "Alexander J. Smola" are the same person. "Habibi Lashkari",
"Montes de Oca", "Brdalo Rapa", "Di Franco" and "De Turck" are compound family names,
matched in full.

## Report D: suspicious or duplicate references

None is suspicious. The three 5G-NIDD records are different objects cited for different
things: the IEEE DataPort dataset record (DataCite DOI), the arXiv paper whose accuracy table
the paper reproduces, and the peer-reviewed IEEE Data Descriptions descriptor. All three are
needed. Two .bib entries (`gorbil2016signalling`, `shi2016edge`) are not cited any more, so
BibTeX does not print them. They stay in the .bib because the latexdiff build of the
earlier version still cites them.

## Report E: citation context

All 62 sources support the sentences that cite them (the table above gives the claim and the
evidence for each). Three sentences were rewritten so that they claim no more than their
sources: F5, F6 and F7. The numbers attributed to prior work were each read in the source:
99.85–99.95% (5G-NIDD authors), 99.95% weighted F1 (Ilias et al., arXiv v2), BA 0.50–0.56 and
0.52–0.83 (Abraheem and Edhirig), 1–5 µs and 10–25 µs (Obiuwevwi et al.), 10 ms to 1 s
(ETSI TS 104 038), "several hundred flows per second" (Jin et al.).

"Did this really happen?" checks for the prior-work claims that matter most:

- Obiuwevwi et al. did deploy models inside an xApp on an OAI + FlexRIC near-RT RIC and
  measured inference there. The paper says only that, and compares magnitudes "for context only".
- Abraheem and Edhirig did run XGBoost zero-shot transfer in both directions between the same
  two corpora. Their numbers match the paper's summary.
- Fard et al. did use NetsLab-5GORAN-IDD and fuse radio and flow records. It is an arXiv
  preprint, and the paper does not call it peer reviewed.
- The 5G-NIDD authors' 99.9% was reproduced in EXP-055, not only quoted.

## Report F: DOIs

All 47 DOIs are correct and resolve to the cited work (doi.org returns a redirect for each,
and the Crossref or DataCite title, authors and year match). No DOI is duplicated. None
points to another publication. The 15 references without a DOI are USENIX, PMLR, JMLR and
NeurIPS papers, arXiv preprints, a journal that assigns none that resolves, and ETSI documents.
These publishers issue no DOI for them, so none is missing.

One DOI was deliberately left out. The WAUJPAS article page prints 10.63318/waujpasv4i2_24,
and doi.org answers 404 for it. The entry keeps the journal's article URL instead.

## Report G: URLs and repository

| URL | Purpose | Result |
|---|---|---|
| https://github.com/adeliusa486/oran-ids-deployability | code and data repository | 200, public, owner adeliusa486, README and code present. It holds commit f31e985, which is behind the working tree until the push (see the sync section) |
| https://www.etsi.org/…/ts_104038v040100p.pdf | ETSI TS 104 038 (O-RAN E2GAP) | 200, PDF read |
| https://www.etsi.org/…/tr_104106v030000p.pdf | ETSI TR 104 106 (O-RAN WG11 threat model) | 200, PDF read |
| https://arxiv.org/abs/2212.01298, 2412.03483, 2606.22450 | preprints | 200 |
| https://www.usenix.org/… (antonakakis, arp) | proceedings pages | 200 |
| https://jmlr.org/papers/v12/pedregosa11a.html | JMLR page | 200 |
| https://papers.nips.cc/…8a20a862… | NeurIPS page | 200 |
| https://waujpas.com/index.php/journal/article/view/509 | journal article page | opens in a browser (read during the audit), returns 500 to a scripted request |
| 47 × https://doi.org/… | DOI links | all resolve |

No shortened, tracking or malformed URL is present.

## Report H: PDF hyperlinks

| Link type | Expected | Working |
|---|---|---|
| Citation links | 97 | 97, each lands on the page of its bibliography item |
| DOI links in the bibliography | 47 DOIs (59 link rectangles, some DOIs wrap onto two lines) | all |
| Repository link | 1 | 1 |
| Other external links | 10 | 10 |
| Cross-references: figures 15, tables 41, sections 33, equations 7, algorithm 2 | 98 | 98, none broken |

The 5 references that sit inside compressed ranges such as [1]–[3] (Abdalla et al., the three
IoT dataset papers, Ovadia et al.) have no link of their own. IEEE's `cite` package links range
endpoints only. This is normal for IEEE papers and is not an error.

## Report I: publication types

Every entry's BibTeX type matches the record: 29 journal articles (the WAUJPAS article among
them), 27 conference papers, 3 arXiv preprints, 1 dataset record (IEEE DataPort), and 2 ETSI
documents (one TS, one TR). No conference paper is called a journal paper. No preprint is
called peer reviewed. The two IEEE Data Descriptions articles are descriptors, and the
paper uses them as dataset descriptions. Crossref classes the AAAI proceedings (Sun et al.)
as a journal volume. The .bib keeps the conference form, which AAAI also uses.

## Report J: final blockers

| Severity | Issue |
|---|---|
| CRITICAL | none |
| HIGH | none |
| MEDIUM | none |
| LOW | Check the two ICCCN author spellings on IEEE Xplore (Report C). Push the synced repository so the paper's GitHub link shows the current code |

## Report K: verdict

| Dimension | Score |
|---|---|
| Reference integrity | 9.5/10 |
| Citation integrity | 9.5/10 |
| Authorship accuracy | 9.5/10 (one spelling pair rests on the publisher record) |
| DOI accuracy | 10/10 |
| Bibliographic accuracy | 9/10 (NeurIPS 2019 and ICCCN entries carry no page numbers, and none were invented) |
| Link and PDF integrity | 9.5/10 |
| Overall reference readiness | 9.5/10 |

**GO.** No critical or unresolved reference issue remains.
