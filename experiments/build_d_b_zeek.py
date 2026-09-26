#!/usr/bin/env python3
"""EXP-063: 5G-NIDD re-extracted with Zeek, labeled from the published labels.

D_A was exported by Zeek and D_B by Argus, so every D_A -> D_B gap mixes a change
of deployment with a change of exporter. This script builds D_B with Zeek
(scripts/zeek/02_run_zeek.sh on the dataset's GTP-removed pcapng files) so the
transfer can be repeated with one exporter on both sides.

Labels. In every 5G-NIDD capture the published attack flows are the traffic of
one or two host pairs (attacker -> victim), EXP-062. A Zeek flow is labeled
attack iff its unordered host pair is an attack pair of the same capture in the
published labels (BTS1_BTS2_fields_preserved.csv). Before use, the rule is
applied to the published Argus flows themselves and must reproduce their labels;
the agreement per capture is recorded. The benign flows of the host pair that
EXP-062 identified as the second attacker's flood (file 5) are marked as copies,
as the Argus copies are, so every result can be given with and without them.

Captures map to the 20 capture files of the Argus release by attack session:
BS1 is files 1-10 (EXP-062 checked all ten), BS2 is files 11-20 in the same
order; the mapping is checked by the attack pairs found in each Zeek log.

Output  data/processed/d_b_zeek.parquet (git-ignored)
        results/EXP-063/processed/label_rule_check.csv, zeek_capture_summary.csv
        results/EXP-063/statistics/build.json

Usage:  python experiments/build_d_b_zeek.py
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from oran_ids.data import _log_target_access, d_b_capture_files  # noqa: E402

LOGS = ROOT / "data" / "interim" / "d_b_zeek"
FP = ROOT / "data" / "raw" / "d_b" / "pcap" / "BTS1_BTS2_fields_preserved.zip"
OUT = ROOT / "results" / "EXP-063"
PARQUET = ROOT / "data" / "processed" / "d_b_zeek.parquet"
SESSION = {"synscan": 1, "tcpconnect": 2, "udpscan": 3, "icmpflood": 4, "udpflood": 5,
           "synflood": 6, "goldeneye": 7, "slowloris": 8, "torshammer": 9, "ssh": 10}
COPY_FILE, COPY_PAIR = 5, frozenset({"10.155.15.7", "10.41.150.68"})


def read_conn(path: Path) -> pd.DataFrame:
    fields = next(ln for ln in path.open() if ln.startswith("#fields")).rstrip("\n").split("\t")[1:]
    return pd.read_csv(path, sep="\t", comment="#", names=fields, low_memory=False,
                       na_values=["-"], keep_default_na=False)


def pair(a: pd.Series, b: pd.Series) -> pd.Series:
    return pd.Series([frozenset((x, y)) for x, y in zip(a, b)], index=a.index)


def main() -> int:
    for d in ("processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    _log_target_access("EXP-063 build D_B from Zeek conn logs (labels from fields_preserved)")

    fp = pd.read_csv(zipfile.ZipFile(FP).open("BTS1_BTS2_fields_preserved.csv"),
                     low_memory=False, usecols=["SrcAddr", "DstAddr", "Offset", "Label",
                                                "Attack Type"])
    fp["file"] = d_b_capture_files(fp.Offset.to_numpy())
    fp["pair"] = pair(fp.SrcAddr, fp.DstAddr)
    fp["attack"] = (fp.Label != "Benign").astype(int)
    att = fp[fp.attack == 1].groupby(["file", "pair"])["Attack Type"].agg(
        lambda s: s.mode().iat[0]).reset_index()
    rule = {(r.file, r.pair): r["Attack Type"] for _, r in att.iterrows()}

    # the rule must reproduce the published labels on the published flows
    fp["rule"] = [int((f, p) in rule) for f, p in zip(fp.file, fp.pair)]
    chk = fp.groupby("file")[["attack", "rule"]].apply(lambda s: pd.Series(dict(
        n=len(s), attack=int(s.attack.sum()), agree=float((s.rule == s.attack).mean()),
        attack_pairs=int(sum(1 for k in rule if k[0] == s.name))))).reset_index()
    chk.to_csv(OUT / "processed/label_rule_check.csv", index=False)
    overall = float((fp.rule == fp.attack).mean())
    print(chk.to_string(index=False), f"\noverall agreement {overall:.6f}", flush=True)

    frames, summ = [], []
    for st, base in (("BS1", 0), ("BS2", 10)):
        for log in sorted((LOGS / st).glob("*.conn.log")):
            sess = log.name.split("_")[0].lower()   # BS2 writes "SYNscan"
            f = SESSION[sess] + base
            z = read_conn(log)
            z["file"] = f
            z["pair"] = pair(z["id.orig_h"], z["id.resp_h"])
            z["attack_type"] = [rule.get((f, p), "Benign") for p in z.pair]
            z["y"] = (z.attack_type != "Benign").astype(np.int8)
            z["copy"] = (z.file == COPY_FILE) & (z.y == 0) & (z.pair == COPY_PAIR)
            frames.append(z)
            summ.append(dict(station=st, capture=log.name, file=f, flows=len(z),
                             attack=int(z.y.sum()), copies=int(z["copy"].sum()),
                             argus_flows=int((fp.file == f).sum()),
                             argus_attack=int(fp[fp.file == f].attack.sum())))
    S = pd.DataFrame(summ).sort_values("file")
    S.to_csv(OUT / "processed/zeek_capture_summary.csv", index=False)
    print(S.to_string(index=False), flush=True)
    Z = pd.concat(frames, ignore_index=True)
    keep = ["file", "id.orig_h", "id.resp_h", "proto", "service", "duration", "orig_bytes",
            "resp_bytes", "conn_state", "orig_pkts", "orig_ip_bytes", "resp_pkts",
            "resp_ip_bytes", "attack_type", "y", "copy"]
    PARQUET.parent.mkdir(parents=True, exist_ok=True)
    Z[keep].to_parquet(PARQUET, index=False)
    zv = (LOGS / "zeek_version.txt").read_text().strip() if (LOGS / "zeek_version.txt").exists() else ""
    (OUT / "statistics/build.json").write_text(json.dumps(dict(
        experiment="EXP-063", zeek=zv, flows=int(len(Z)), attack=int(Z.y.sum()),
        attack_share=float(Z.y.mean()), copies=int(Z["copy"].sum()),
        argus_flows=int(len(fp)), argus_attack=int(fp.attack.sum()),
        label_rule_agreement_on_argus=overall,
        captures=int(len(S))), indent=2), encoding="utf-8")
    print(f"wrote {PARQUET} ({len(Z)} flows, attack {Z.y.mean():.4f}, copies {int(Z['copy'].sum())})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
