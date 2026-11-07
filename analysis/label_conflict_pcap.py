#!/usr/bin/env python3
"""EXP-072: are the benign-labelled 5G-NIDD flood copies the same packets? (R2.2c)

EXP-062 traced the 281,525 benign-labelled copies in capture file 5 (base
station 1) to the host pair of the UDP flood labelled in file 15 (base station
2), from the addresses of the fields-preserved release. Reviewer 2 asked for
confirmation in the raw captures: if file 5 recorded station 2's flood, the
SAME packets appear in both captures, with equal IP identification, length,
ports, TTL and payload, at a near-constant time offset.

This script reads the two GTP-removed UDP-flood captures straight from the
dataset's zip files and, for every packet towards the flood target, records the
fields above plus the Ethernet addresses (which show on which link each capture
saw the packet). It then

  1. matches packets of each attacker across the two captures on
     (src, dst, sport, dport, IP id, IP length, TTL, payload digest), nearest in
     time, and reports the match rate and the distribution of time offsets;
  2. reports each capture's time window and each attacker's first and last
     packet in each capture, which answers why file 15 holds no copies of
     station 1's flood (R2.2b).

Usage:  python analysis/label_conflict_pcap.py      (about 5-10 minutes)
Output: results/EXP-072/
"""
from __future__ import annotations

import hashlib
import json
import socket
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import dpkt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PCAP = ROOT / "data/raw/d_b/pcap"
OUT = ROOT / "results/EXP-072"
CAPTURES = {
    "file5_bs1": (PCAP / "BS1_GTP_removed.zip", "BS1_GTP_removed/UDPflood_BS1_nogtp.pcapng"),
    "file15_bs2": (PCAP / "BS2_GTP_removed.zip", "BS2 GTP removed/UDPflood_BS2_nogtp.pcapng"),
}
TARGET = "10.41.150.68"
ATTACKERS = {"10.155.15.7": "station-2 attacker", "10.155.15.4": "station-1 attacker"}
MATCH_WINDOW_S = 2.0      # IP id wraps every 65,536 packets; match nearest in time


def mac(b: bytes) -> str:
    return ":".join(f"{x:02x}" for x in b)


def read_capture(name: str, zpath: Path, member: str) -> tuple[pd.DataFrame, dict]:
    t0 = time.time()
    rows = []
    n_all, ts_first, ts_last = 0, None, None
    macs = defaultdict(int)
    with zipfile.ZipFile(zpath) as zf, zf.open(member) as fh:
        rd = dpkt.pcapng.Reader(fh)
        for ts, buf in rd:
            n_all += 1
            ts_first = ts if ts_first is None else ts_first
            ts_last = ts
            try:
                eth = dpkt.ethernet.Ethernet(buf)
            except Exception:
                continue
            ip = eth.data
            if not isinstance(ip, dpkt.ip.IP):
                continue
            src, dst = socket.inet_ntoa(ip.src), socket.inet_ntoa(ip.dst)
            if dst != TARGET or src not in ATTACKERS:
                continue
            sport = dport = -1
            payload = b""
            l4 = ip.data
            if isinstance(l4, dpkt.udp.UDP):
                sport, dport, payload = l4.sport, l4.dport, bytes(l4.data)
            elif isinstance(l4, (bytes, bytearray)):
                payload = bytes(l4)
            dig = hashlib.blake2b(payload, digest_size=8).hexdigest()
            macs[(src, mac(eth.src), mac(eth.dst))] += 1
            rows.append((float(ts), src, dst, int(ip.p), sport, dport, int(ip.id),
                         int(ip.len), int(ip.ttl), dig, len(payload)))
    df = pd.DataFrame(rows, columns=["ts", "src", "dst", "proto", "sport", "dport",
                                     "ip_id", "ip_len", "ttl", "payload_digest",
                                     "payload_len"])
    info = dict(capture=name, member=member, packets_total=n_all,
                window_start=ts_first, window_end=ts_last,
                window_s=None if ts_first is None else ts_last - ts_first,
                packets_to_target=len(df),
                ethernet=[dict(src=k[0], eth_src=k[1], eth_dst=k[2], packets=v)
                          for k, v in sorted(macs.items(), key=lambda kv: -kv[1])],
                read_s=round(time.time() - t0, 1))
    print(f"{name}: {n_all:,} packets, {len(df):,} to {TARGET} ({info['read_s']} s)",
          flush=True)
    return df, info


def match(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """Nearest-in-time partner in b for each packet of a with an equal key."""
    key = ["src", "dst", "proto", "sport", "dport", "ip_id", "ip_len", "ttl",
           "payload_digest"]
    b_groups = {k: g["ts"].to_numpy() for k, g in b.groupby(key, sort=False)}
    dt = np.full(len(a), np.nan)
    for i, (k, g) in enumerate(a.groupby(key, sort=False)):
        tb = b_groups.get(k)
        if tb is None:
            continue
        tb = np.sort(tb)
        ta = g["ts"].to_numpy()
        j = np.clip(np.searchsorted(tb, ta), 1, len(tb) - 1) if len(tb) > 1 else np.zeros(len(ta), int)
        cand = np.stack([tb[np.maximum(j - 1, 0)], tb[j]], axis=1)
        d = cand - ta[:, None]
        best = d[np.arange(len(ta)), np.abs(d).argmin(axis=1)]
        dt[g.index.to_numpy()] = best
    out = a[["ts", "src"]].copy()
    out["dt"] = dt
    out["matched"] = np.abs(out["dt"]) <= MATCH_WINDOW_S
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    frames, infos = {}, {}
    for name, (z, m) in CAPTURES.items():
        frames[name], infos[name] = read_capture(name, z, m)

    summary = dict(captures=infos, attackers=ATTACKERS, target=TARGET,
                   match_window_s=MATCH_WINDOW_S, per_attacker={})
    for src, role in ATTACKERS.items():
        entry = {"role": role}
        for name, df in frames.items():
            d = df[df["src"] == src]
            entry[name] = dict(packets=int(len(d)),
                               first=None if d.empty else float(d["ts"].min()),
                               last=None if d.empty else float(d["ts"].max()),
                               ttl_values=sorted(map(int, d["ttl"].unique()))[:5],
                               ip_len_mode=None if d.empty else int(d["ip_len"].mode().iloc[0]))
        a = frames["file5_bs1"]
        b = frames["file15_bs2"]
        a_src = a[a["src"] == src].reset_index(drop=True)
        b_src = b[b["src"] == src].reset_index(drop=True)
        if len(a_src) and len(b_src):
            m = match(a_src, b_src)
            mm = m[m["matched"]]
            entry["bs1_packets_found_in_bs2"] = dict(
                n=int(len(a_src)), matched=int(len(mm)),
                share=float(len(mm) / len(a_src)),
                offset_median_s=float(mm["dt"].median()) if len(mm) else None,
                offset_iqr_s=(float(mm["dt"].quantile(0.75) - mm["dt"].quantile(0.25))
                              if len(mm) else None),
                offset_p01_s=float(mm["dt"].quantile(0.01)) if len(mm) else None,
                offset_p99_s=float(mm["dt"].quantile(0.99)) if len(mm) else None)
            m.sample(min(len(m), 200_000), random_state=0).to_csv(
                OUT / f"match_offsets_{src.replace('.', '_')}.csv", index=False)
        summary["per_attacker"][src] = entry
        print(json.dumps(entry, indent=1), flush=True)

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str),
                                      encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
