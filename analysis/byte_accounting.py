#!/usr/bin/env python3
"""EXP-074 part C: how each exporter counts bytes (reviewer R1.9, D-035).

Reports, label-blind,
  * the smallest bytes per packet by protocol in 5G-NIDD as exported by Argus
    (Combined.csv), in NetsLab-5GORAN-IDD as exported by Zeek (ip_bytes), and
    in our Zeek re-extraction of the same 5G-NIDD captures;
  * in the raw 5G-NIDD captures, the link type and the share of frames whose
    length exceeds the IP total length by exactly 14 bytes (an Ethernet header).

Usage:  python analysis/byte_accounting.py
Output: results/EXP-074/byte_accounting.json
"""
from __future__ import annotations

import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

import dpkt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/EXP-074"
PCAPS = [("BS1_GTP_removed.zip", "BS1_GTP_removed/SYNScan_BS1_nogtp.pcapng"),
         ("BS1_GTP_removed.zip", "BS1_GTP_removed/UDPflood_BS1_nogtp.pcapng"),
         ("BS2_GTP_removed.zip", "BS2 GTP removed/SYNflood_BS2_nogtp.pcapng"),
         ("BS2_GTP_removed.zip", "BS2 GTP removed/Goldeneye_BS2_nogtp.pcapng")]
N_PER_FILE = 300_000


def minima(df, proto, b, p):
    d = df[df[p] > 0]
    out = {}
    for k, g in d.groupby(proto):
        if len(g) >= 100:
            bpp = g[b] / g[p]
            out[str(k).lower()] = dict(n=int(len(g)), min=float(bpp.min()),
                                       median=float(bpp.median()))
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    b = pd.read_csv(ROOT / "data/raw/d_b/Combined.csv",
                    usecols=["Proto", "SrcBytes", "SrcPkts"], low_memory=False)
    res["argus_5gnidd"] = minima(b, "Proto", "SrcBytes", "SrcPkts")
    a = pd.read_csv(ROOT / "data/raw/d_a/Network_Dataset.csv",
                    usecols=["proto", "src_ip_bytes", "src_pkts"], low_memory=False)
    res["zeek_netslab"] = minima(a, "proto", "src_ip_bytes", "src_pkts")
    z = pd.read_parquet(ROOT / "data/processed/d_b_zeek.parquet")
    res["zeek_5gnidd"] = minima(z, "proto", "orig_ip_bytes", "orig_pkts")

    tot, hdr14, links = 0, 0, Counter()
    per_file = []
    for zname, member in PCAPS:
        n = h = 0
        with zipfile.ZipFile(ROOT / "data/raw/d_b/pcap" / zname) as zf, zf.open(member) as fh:
            rd = dpkt.pcapng.Reader(fh)
            links[int(rd.datalink())] += 1
            for _ts, buf in rd:
                try:
                    ip = dpkt.ethernet.Ethernet(buf).data
                except Exception:
                    continue
                if not isinstance(ip, dpkt.ip.IP):
                    continue
                n += 1
                h += int(len(buf) - ip.len == 14)
                if n >= N_PER_FILE:
                    break
        per_file.append(dict(file=member, ipv4_frames=n, header_14=h, share=h / max(n, 1)))
        tot += n
        hdr14 += h
        print(per_file[-1], flush=True)
    res["pcap"] = dict(link_types=dict(links), files=per_file, frames=tot,
                       share_header_14=hdr14 / max(tot, 1))
    (OUT / "byte_accounting.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "pcap"}, indent=1))
    print("pcap share with 14-byte header:", res["pcap"]["share_header_14"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
