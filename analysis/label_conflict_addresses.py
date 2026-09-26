#!/usr/bin/env python3
"""EXP-062: where the conflicting 5G-NIDD records come from.

EXP-057 found that 52% of 5G-NIDD flows share their record content with a flow of
the opposite label, all in the two UDP-flood captures, and could not say which
label is right: Combined.csv and Encoded.csv carry no addresses. The dataset's
BTS1_BTS2_fields_preserved.csv does (SrcAddr, DstAddr, ports, StartTime), and it
aligns with Encoded.csv row for row (Offset, Seq and Label equal on every row,
checked below).

This audit reports, per capture file, the source and destination hosts of
  * the benign flows whose record also occurs as an attack (the benign copies),
  * the other benign flows,
  * the attack flows,
and for the benign copies whether their host pair, protocol and time window are
those of a flow labeled as attack in another capture. StartTime in the file is
minutes:seconds only, so time windows are compared within the hour.

Inputs  data/raw/d_b/Encoded.csv
        data/raw/d_b/pcap/BTS1_BTS2_fields_preserved.zip (Fairdata file
        /BTS1_BTS2_fields_preserved.zip, fetched with scripts/fetch_5gnidd_file.py)
Output  results/EXP-062/processed/hosts_by_file.csv
        results/EXP-062/statistics/conflict_addresses.json

Usage:  python analysis/label_conflict_addresses.py
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
sys.path.insert(0, str(ROOT / "analysis"))
from label_conflict_audit import ID_COLS, LABELS, keys  # noqa: E402
from oran_ids.data import _log_target_access, d_b_capture_files  # noqa: E402

OUT = ROOT / "results" / "EXP-062"
RAW = ROOT / "data" / "raw" / "d_b"
FP = RAW / "pcap" / "BTS1_BTS2_fields_preserved.zip"


def top(s: pd.Series, n: int = 3) -> str:
    return json.dumps(s.value_counts().head(n).to_dict())


def main() -> int:
    for d in ("processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    _log_target_access("EXP-062 addresses of conflicting records (Encoded.csv, fields_preserved)")
    enc = pd.read_csv(RAW / "Encoded.csv", low_memory=False)
    fp = pd.read_csv(zipfile.ZipFile(FP).open("BTS1_BTS2_fields_preserved.csv"),
                     low_memory=False,
                     usecols=["StartTime", "SrcAddr", "DstAddr", "Proto", "Seq", "Offset",
                              "Label", "Attack Type"])
    aligned = (len(enc) == len(fp)
               and np.array_equal(enc.Offset.to_numpy(), fp.Offset.to_numpy())
               and np.array_equal(enc.Seq.to_numpy(), fp.Seq.to_numpy())
               and bool((enc.Label.to_numpy() == fp.Label.to_numpy()).all()))
    if not aligned:
        raise AssertionError("fields_preserved and Encoded.csv rows do not align")

    y = (enc.Label != "Benign").to_numpy(np.int8)
    files = d_b_capture_files(enc.Offset.to_numpy())
    content = (enc.drop(columns=list(ID_COLS + LABELS))
               .apply(pd.to_numeric, errors="coerce").fillna(0.0))
    k = keys(content)
    d = pd.DataFrame(dict(k=k, y=y, f=files, src=fp.SrcAddr, dst=fp.DstAddr,
                          proto=fp.Proto, t=fp.StartTime, atype=enc["Attack Type"]))
    g = d.groupby("k").y.agg(["min", "max"])
    d["mixed"] = d.k.isin(g[(g["min"] == 0) & (g["max"] == 1)].index)
    d["group"] = np.select([(d.y == 0) & d.mixed, d.y == 0], ["benign_copy", "benign_other"],
                           "attack")

    rows = []
    for (f, grp), s in d.groupby(["f", "group"]):
        rows.append(dict(file=int(f), site=1 if f <= 10 else 2, group=grp, n=len(s),
                         attack_types=top(s.atype), src_top=top(s.src), dst_top=top(s.dst),
                         proto_top=top(s.proto), t_first=str(s.t.min()), t_last=str(s.t.max())))
    H = pd.DataFrame(rows)
    H.to_csv(OUT / "processed/hosts_by_file.csv", index=False)

    # the benign copies against the attack flows of other files
    cp = d[d.group == "benign_copy"]
    att = d[d.y == 1]
    pairs = cp.groupby(["f", "src", "dst", "proto"]).agg(
        n=("k", "size"), t_first=("t", "min"), t_last=("t", "max")).reset_index()
    out = []
    for _, p in pairs.iterrows():
        m = att[(att.src == p.src) & (att.dst == p.dst) & (att.proto == p.proto)
                & (att.f != p.f)]
        own = att[(att.f == p.f)]
        out.append(dict(
            benign_file=int(p.f), src=p.src, dst=p.dst, proto=p.proto, benign_copies=int(p.n),
            benign_window=f"{p.t_first}-{p.t_last}",
            attack_files_same_hosts=sorted(int(x) for x in m.f.unique()),
            attack_flows_same_hosts=int(len(m)),
            attack_types_same_hosts=m.atype.value_counts().to_dict(),
            attack_window_same_hosts=(f"{m.t.min()}-{m.t.max()}" if len(m) else ""),
            own_file_attack_sources=own.src.value_counts().head(3).to_dict(),
            own_file_attack_types=own.atype.value_counts().to_dict()))
    # which pass is which base station: the per-station release (BS1_each_attack_csv)
    # against the 20 capture files recovered from Offset resets
    site = []
    bs1 = RAW / "pcap" / "BS1_each_attack_csv.zip"
    if bs1.exists():
        Z = zipfile.ZipFile(bs1)
        per_file = d.groupby("f").agg(n=("k", "size"),
                                      src=("src", lambda s: s[d.loc[s.index, "y"] == 1]
                                           .value_counts().index[0]
                                           if (d.loc[s.index, "y"] == 1).any() else ""))
        for name in sorted(n for n in Z.namelist() if n.endswith(".csv")):
            b = pd.read_csv(Z.open(name), usecols=["SrcAddr", "Label"], low_memory=False)
            src = (b[b.Label != "Benign"].SrcAddr.value_counts().index[0]
                   if (b.Label != "Benign").any() else "")
            match = per_file[(per_file.n == len(b)) & (per_file.src == src)].index.tolist()
            site.append(dict(bs1_file=name.split("/")[-1], rows=len(b), attacker=src,
                             matching_capture_files=[int(x) for x in match]))
    stats = dict(
        experiment="EXP-062", aligned_rows=int(len(enc)),
        bs1_files_matched=sum(len(s["matching_capture_files"]) == 1 for s in site),
        bs1_files=len(site),
        bs1_matches_first_pass=bool(site) and all(
            s["matching_capture_files"] and s["matching_capture_files"][0] <= 10 for s in site),
        site_check=site,
        benign_copies=int(len(cp)),
        benign_copies_share_top_pair=float(pairs.n.max() / len(cp)) if len(cp) else float("nan"),
        pairs=out)
    (OUT / "statistics/conflict_addresses.json").write_text(json.dumps(stats, indent=2),
                                                            encoding="utf-8")
    print(H[H.group != "benign_other"].to_string(index=False))
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
