#!/usr/bin/env python3
"""EXP-072 part B: how do the per-station 5G-NIDD captures relate? (R2.2a, R2.2b)

Part A (label_conflict_pcap.py) found that every packet of station 2's attacker
in the station-1 UDP-flood capture occurs in the station-2 capture with the
same timestamp to the microsecond, and that both files start at the same
microsecond. Two capture points would not record identical timestamps; the
two files look like one recording divided per station.

This part reads all 20 GTP-removed captures and reports, per file, the packet
count, the first and last timestamp and the Ethernet source addresses, and,
per attack type, how many packets the station-1 and station-2 files share
(same timestamp, addresses, IP identification and length). It answers whether
the overlap is specific to the UDP-flood pair, and whether file 15 is a subset
of file 5.

Usage:  python analysis/label_conflict_pcap_pairs.py     (about 20-30 minutes)
Output: results/EXP-072/pairs.json, results/EXP-072/files.csv
"""
from __future__ import annotations

import json
import socket
import sys
import time
import zipfile
from collections import Counter
from pathlib import Path

import dpkt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PCAP = ROOT / "data/raw/d_b/pcap"
OUT = ROOT / "results/EXP-072"
ZIPS = {1: (PCAP / "BS1_GTP_removed.zip", "BS1_GTP_removed/{}_BS1_nogtp.pcapng"),
        2: (PCAP / "BS2_GTP_removed.zip", "BS2 GTP removed/{}_BS2_nogtp.pcapng")}
# attack sessions in the order of the capture files (files 1-10 and 11-20)
ATTACKS = ["ICMPflood", "UDPflood", "SYNflood", "HTTPflood?", "SlowrateDoS?"]
NAMES = {1: ["Goldeneye", "ICMPflood", "Slowloris", "SSH", "SYNflood", "SYNScan",
             "TCPConnect", "Torshammer", "UDPflood", "UDPScan"],
         2: ["Goldeneye", "ICMPflood", "Slowloris", "SSH", "SYNflood", "SYNscan",
             "TCPConnect", "Torshammer", "UDPflood", "UDPScan"]}


def keys(zpath: Path, member: str):
    t0 = time.time()
    ks, macs, n = set(), Counter(), 0
    first = last = None
    with zipfile.ZipFile(zpath) as zf, zf.open(member) as fh:
        for ts, buf in dpkt.pcapng.Reader(fh):
            n += 1
            first = ts if first is None else first
            last = ts
            try:
                eth = dpkt.ethernet.Ethernet(buf)
            except Exception:
                continue
            ip = eth.data
            if isinstance(ip, dpkt.ip.IP):
                ks.add((round(float(ts), 6), ip.src, ip.dst, ip.id, ip.len))
                macs[":".join(f"{x:02x}" for x in eth.src)] += 1
    return ks, dict(packets=n, ipv4_keys=len(ks), first=first, last=last,
                    top_eth_src=macs.most_common(4), read_s=round(time.time() - t0, 1))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files, pairs = [], []
    for i in range(10):
        k = {}
        info = {}
        for st in (1, 2):
            name = NAMES[st][i]
            zpath, pattern = ZIPS[st]
            k[st], info[st] = keys(zpath, pattern.format(name))
            files.append(dict(station=st, capture=name, **{x: y for x, y in info[st].items()
                                                         if x != "top_eth_src"},
                              top_eth_src=json.dumps(info[st]["top_eth_src"])))
            print(f"BS{st} {name}: {info[st]['packets']:,} packets "
                  f"({info[st]['read_s']} s)", flush=True)
        shared = len(k[1] & k[2])
        pairs.append(dict(capture=NAMES[1][i],
                          bs1_keys=len(k[1]), bs2_keys=len(k[2]), shared=shared,
                          share_of_bs1=shared / max(len(k[1]), 1),
                          share_of_bs2=shared / max(len(k[2]), 1),
                          same_first_ts=info[1]["first"] == info[2]["first"],
                          first_bs1=info[1]["first"], first_bs2=info[2]["first"],
                          last_bs1=info[1]["last"], last_bs2=info[2]["last"]))
        print(json.dumps(pairs[-1]), flush=True)
        del k
    pd.DataFrame(files).to_csv(OUT / "files.csv", index=False)
    (OUT / "pairs.json").write_text(json.dumps(pairs, indent=2, default=str), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
