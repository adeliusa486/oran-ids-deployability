#!/usr/bin/env python3
"""EXP-001: can the CU flow records be joined to the DU radio telemetry?

Claim C5 (the radio-KPI feature-family ablation) requires a joined feature vector.
This script establishes at what granularity, if any, the two published summary
artefacts can be joined, and reports the consequence for C5.

The test is deliberately ordered from strongest join to weakest, and stops at the
strongest one that actually works:

  L0  record level, on a shared flow/UE identifier
  L1  record level, on a shared time axis within JOIN_TOLERANCE_S
  L2  run level, on (attack_category, attack_type <-> attack_subcategory)
  L3  category level only
  L4  no join

Outputs: results/EXP-001/statistics/join_analysis.json and a printed verdict.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/d_a")
OUT = Path("results/EXP-001")
JOIN_TOLERANCE_S = 1.0

# Normalisation for the run-level key. The two layers use different spellings.
CAT_NORM = {
    "benign": "benign", "dos": "dos", "ddos": "ddos", "probe": "probe",
    "bruteforce": "bruteforce", "web": "web",
    "Benign": "benign", "DoS": "dos", "DDoS": "ddos", "Probe": "probe",
    "BruteForce": "bruteforce", "Web Attacks": "web",
}


def main() -> int:
    (OUT / "statistics").mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(RAW / "Lower_Layer_Data.db")
    radio = pd.read_sql("SELECT * FROM lower_layer_data", con)
    con.close()
    net = pd.read_csv(RAW / "Network_Dataset.csv", low_memory=False)

    res: dict = {"experiment": "EXP-001", "question": "CU/DU join feasibility"}

    radio_cols, net_cols = set(radio.columns), set(net.columns)
    res["shared_columns"] = sorted(radio_cols & net_cols)

    # ---- L0: shared record-level identifier -------------------------------
    id_like_radio = {"ue_id", "rnti", "cellid"}
    id_like_net = {"uid", "src_ip", "dst_ip", "src_port", "dst_port"}
    res["L0_record_id"] = {
        "radio_identifiers": sorted(id_like_radio & radio_cols),
        "network_identifiers": sorted(id_like_net & net_cols),
        "shared": sorted((id_like_radio & radio_cols) & (id_like_net & net_cols)),
        "possible": bool((id_like_radio & radio_cols) & (id_like_net & net_cols)),
    }

    # ---- L1: shared time axis ---------------------------------------------
    def time_cols(cols):
        return sorted(c for c in cols
                      if any(k in c.lower() for k in ("timestamp", "time", "ts", "epoch", "date"))
                      and c not in ("src_pkts", "dst_pkts"))

    res["L1_time"] = {
        "radio_time_columns": time_cols(radio_cols),
        "network_time_columns": time_cols(net_cols),
        "possible": bool(time_cols(radio_cols) and time_cols(net_cols)),
        "tolerance_s": JOIN_TOLERANCE_S,
        "note": ("Network_Dataset.csv carries no time field. Zeek's conn.log 'ts' was "
                 "dropped when the summary CSV was built, so there is no axis to join on."),
    }

    # ---- L2: run level -----------------------------------------------------
    radio["cat_n"] = radio["attack_category"].map(CAT_NORM)
    net["cat_n"] = net["attack_category"].map(CAT_NORM)
    r_unmapped = radio.loc[radio.cat_n.isna(), "attack_category"].unique().tolist()
    n_unmapped = net.loc[net.cat_n.isna(), "attack_category"].unique().tolist()

    r_sub = sorted(radio["attack_subcategory"].dropna().unique())
    n_typ = sorted(net["attack_type"].dropna().unique())
    res["L2_run"] = {
        "radio_subcategories": {"n": len(r_sub), "values": r_sub},
        "network_attack_types": {"n": len(n_typ), "values": n_typ},
        "exact_string_overlap": sorted(set(r_sub) & set(n_typ)),
        "unmapped_radio_categories": r_unmapped,
        "unmapped_network_categories": n_unmapped,
        "possible_at_category_level": bool(not r_unmapped and not n_unmapped),
        "note": ("Subcategory vocabularies differ in both spelling and granularity "
                 "(radio 19 values, network 15). A run-level join needs a hand-written, "
                 "auditable mapping table, not a string match."),
    }

    # ---- class balance divergence -----------------------------------------
    rb = radio["cat_n"].value_counts(normalize=True).mul(100).round(2)
    nb = net["cat_n"].value_counts(normalize=True).mul(100).round(2)
    bal = pd.DataFrame({"radio_pct": rb, "network_pct": nb}).fillna(0)
    bal["abs_diff"] = (bal.radio_pct - bal.network_pct).abs().round(2)
    res["class_balance_divergence"] = bal.to_dict("index")
    res["attack_prevalence_pct"] = {
        "radio": round(float((radio.traffic_type == 1).mean() * 100), 2),
        "network": round(float((net.traffic_type == 1).mean() * 100), 2),
    }

    # ---- verdict -----------------------------------------------------------
    if res["L0_record_id"]["possible"]:
        level, verdict = "L0", "record-level join on a shared identifier"
    elif res["L1_time"]["possible"]:
        level, verdict = "L1", "record-level join on time"
    elif res["L2_run"]["possible_at_category_level"]:
        level, verdict = "L2/L3", "run- or category-level join only, via a hand-written mapping"
    else:
        level, verdict = "L4", "no join"
    res["verdict"] = {"level": level, "description": verdict}

    res["consequence_for_C5"] = (
        "A record-level join is NOT possible from the published summary artefacts. "
        "The network CSV has no time field and no UE identifier; the radio DB has no "
        "flow or IP identifier. Claim C5 as written requires a joined feature vector, "
        "so from these artefacts alone it cannot be evaluated. Three routes remain: "
        "(a) re-extract from the raw per-category archives, whose .pcap and .txt files "
        "both carry timestamps, which means downloading the 16.4 GB and reversing "
        "decision D-004; (b) restrict C5 to run-level late fusion, which is a weaker "
        "and different claim and must be renamed; (c) withdraw C5. "
        "Note that prior work (Fard et al., IEEE CSR 2026) does fuse these modalities, "
        "which is evidence that route (a) is achievable."
    )

    out = OUT / "statistics" / "join_analysis.json"
    out.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")

    print("=== CU / DU JOIN ANALYSIS ===")
    print("shared columns between the two layers:", res["shared_columns"])
    print("L0 record-level identifier :", "POSSIBLE" if res["L0_record_id"]["possible"] else "NOT POSSIBLE")
    print("     radio ids  :", res["L0_record_id"]["radio_identifiers"])
    print("     network ids:", res["L0_record_id"]["network_identifiers"])
    print("L1 time-axis join          :", "POSSIBLE" if res["L1_time"]["possible"] else "NOT POSSIBLE")
    print("     radio time cols  :", res["L1_time"]["radio_time_columns"])
    print("     network time cols:", res["L1_time"]["network_time_columns"] or "NONE")
    print("L2 run-level join          :",
          "POSSIBLE via mapping" if res["L2_run"]["possible_at_category_level"] else "NOT POSSIBLE")
    print("     radio subcategories:", res["L2_run"]["radio_subcategories"]["n"])
    print("     network attack_types:", res["L2_run"]["network_attack_types"]["n"])
    print("     exact string overlap:", res["L2_run"]["exact_string_overlap"] or "NONE")
    print("\nVERDICT:", level, "-", verdict)
    print("\nattack prevalence: radio %.2f%%  network %.2f%%"
          % (res["attack_prevalence_pct"]["radio"], res["attack_prevalence_pct"]["network"]))
    print("\nclass balance divergence (percentage points):")
    print(bal.to_string())
    print("\nwritten ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
