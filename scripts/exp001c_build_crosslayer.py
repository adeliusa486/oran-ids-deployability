#!/usr/bin/env python3
"""EXP-001c: build the run-level cross-layer dataset from D_A's raw archives.

Answers the question D-008 route (a) was authorised to answer: can CU flow
records be joined to DU radio telemetry, and for what fraction of windows?

For each category archive:
  1. extract <Category>/{Network_Layer/*.pcap, Lower_Layer/*.txt}
  2. pair them by file stem -- the stem IS the run identifier
  3. run the pinned exporter over the pcap (one exporter, both corpora: A3)
  4. parse the DU telemetry and difference its cumulative counters
  5. project both onto one absolute-time window grid per run
  6. join on the window index, and record what failed to join
  7. write per-run parquet, then delete the extracted pcaps

Disk: the archives expand roughly 8x, so extraction is per-category with
cleanup between. Do not extract everything first.

Usage:
    python scripts/exp001c_build_crosslayer.py --categories Web
    python scripts/exp001c_build_crosslayer.py --all
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from oran_ids.features.crosslayer import (  # noqa: E402
    WindowSpec,
    aggregate_network,
    aggregate_radio,
    difference_counters,
    parse_radio_file,
    window_grid,
)
from oran_ids.ingest import EXPORTER_VERSION, ExporterConfig, export_file  # noqa: E402

DATA_ROOT = Path("C:/Users/adeel/oran-ids-data/d_a")
OUT = Path("results/EXP-001c")
PROCESSED = Path("data/processed/d_a")

# Archive stem -> canonical category (configs/labels/canonical_map.yaml).
CATEGORIES = {
    "Web": "web", "DoS": "dos", "DDOS": "ddos",
    "BruteForce": "bruteforce", "Benign": "benign",
}


def extract(archive: Path, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["unzip", "-o", "-q", str(archive), "-d", str(dest)], check=True)
    return dest


def find_runs(root: Path) -> list[tuple[str, Path | None, Path | None]]:
    """Pair pcap and telemetry by file stem. Unpaired files are returned too,
    with a None on the missing side, so the pairing gap is reported rather than
    quietly dropped."""
    pcaps = {p.stem: p for p in root.rglob("Network_Layer/*.pcap")}
    txts = {p.stem: p for p in root.rglob("Lower_Layer/*.txt")}
    return [(stem, pcaps.get(stem), txts.get(stem))
            for stem in sorted(set(pcaps) | set(txts))]


def build_run(run_id: str, pcap: Path, txt: Path, category: str,
              spec: WindowSpec, cfg: ExporterConfig) -> tuple[pd.DataFrame, dict]:
    t0 = time.perf_counter()
    flows = export_file(pcap, cfg)
    t_export = time.perf_counter() - t0

    radio = difference_counters(parse_radio_file(txt))

    if not flows or not radio:
        return pd.DataFrame(), {
            "run_id": run_id, "category": category, "status": "EMPTY_LAYER",
            "n_flows": len(flows), "n_radio": len(radio),
        }

    f_lo, f_hi = min(f["first_ts"] for f in flows), max(f["last_ts"] for f in flows)
    r_lo, r_hi = radio[0]["_ts"], radio[-1]["_ts"]

    # Intersection of the two capture windows: outside it one layer simply was
    # not recording, which is a pairing fact, not a join failure.
    lo, hi = max(f_lo, r_lo), min(f_hi, r_hi)
    overlap_s = max(0.0, hi - lo)
    union_s = max(f_hi, r_hi) - min(f_lo, r_lo)

    rows, n_net_only, n_radio_only = [], 0, 0
    for idx, ws, we in window_grid(lo, hi, spec):
        if we > hi:
            break
        net = aggregate_network(flows, ws, we)
        rad = aggregate_radio(radio, ws, we)
        has_net, has_rad = net["net_n_flows"] > 0, rad["radio_n_records"] > 0
        if not has_net and has_rad:
            n_radio_only += 1
        if has_net and not has_rad:
            n_net_only += 1
        if spec.require_network and not has_net:
            continue
        if spec.require_radio and not has_rad:
            continue
        rows.append({
            "run_id": run_id, "category": category,
            "window_index": idx, "window_start": ws, "window_end": we,
            **net, **rad,
        })

    df = pd.DataFrame(rows)
    n_grid = len(window_grid(lo, hi, spec))
    stats = {
        "run_id": run_id, "category": category, "status": "OK",
        "n_flows": len(flows), "n_radio_records": len(radio),
        "pcap_mb": round(pcap.stat().st_size / 1e6, 1),
        "export_s": round(t_export, 1),
        "pcap_start": f_lo, "pcap_end": f_hi,
        "radio_start": r_lo, "radio_end": r_hi,
        "start_offset_s": round(f_lo - r_lo, 3),
        "overlap_s": round(overlap_s, 1),
        "union_s": round(union_s, 1),
        "overlap_fraction": round(overlap_s / union_s, 4) if union_s > 0 else 0.0,
        "windows_in_grid": n_grid,
        "windows_joined": len(df),
        "join_rate": round(len(df) / n_grid, 4) if n_grid else 0.0,
        "windows_network_only": n_net_only,
        "windows_radio_only": n_radio_only,
    }
    return df, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", nargs="*", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--width-s", type=float, default=16.0)
    ap.add_argument("--stride-s", type=float, default=16.0)
    ap.add_argument("--keep-extracted", action="store_true")
    args = ap.parse_args()

    cats = list(CATEGORIES) if args.all else (args.categories or ["Web"])
    spec = WindowSpec(width_s=args.width_s, stride_s=args.stride_s)
    cfg = ExporterConfig()

    for d in (OUT / "processed", OUT / "statistics", OUT / "logs"):
        d.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    all_stats, frames = [], []
    for cat in cats:
        archive = DATA_ROOT / f"{cat}.zip"
        if not archive.exists():
            print(f"SKIP {cat}: {archive} not present yet")
            continue
        canonical = CATEGORIES[cat]
        print(f"\n=== {cat} -> {canonical} ===")
        dest = DATA_ROOT / "extracted" / cat
        if not (dest / cat).exists() and not any(dest.rglob("*.pcap")):
            print(f"  extracting {archive.name} ({archive.stat().st_size/1e9:.2f} GB)...")
            extract(archive, dest)

        runs = find_runs(dest)
        print(f"  {len(runs)} run(s) found")
        for run_id, pcap, txt in runs:
            if pcap is None or txt is None:
                missing = "pcap" if pcap is None else "telemetry"
                print(f"    {run_id:34s} UNPAIRED (no {missing})")
                all_stats.append({"run_id": run_id, "category": canonical,
                                  "status": f"UNPAIRED_NO_{missing.upper()}"})
                continue
            df, st = build_run(run_id, pcap, txt, canonical, spec, cfg)
            all_stats.append(st)
            if not df.empty:
                df.to_parquet(PROCESSED / f"{canonical}__{run_id}.parquet", index=False)
                frames.append(df)
            print(f"    {run_id:34s} {st.get('n_flows',0):>7,} flows  "
                  f"{st.get('n_radio_records',0):>5,} radio  "
                  f"join {st.get('join_rate',0):>6.1%}  "
                  f"offset {st.get('start_offset_s',0):>+8.1f}s  "
                  f"{st.get('export_s',0):>5.1f}s")

        if not args.keep_extracted:
            shutil.rmtree(dest, ignore_errors=True)
            print(f"  cleaned extracted/{cat}")

    stats = pd.DataFrame(all_stats)
    stats.to_csv(OUT / "statistics" / "run_join_stats.csv", index=False)

    ok = stats[stats.status == "OK"] if "status" in stats else pd.DataFrame()
    summary = {
        "exporter_version": EXPORTER_VERSION,
        "exporter_fingerprint": cfg.fingerprint(),
        "window": {"width_s": spec.width_s, "stride_s": spec.stride_s,
                   "overlapping": spec.overlapping},
        "categories": cats,
        "n_runs_total": int(len(stats)),
        "n_runs_ok": int(len(ok)),
        "n_runs_unpaired": int((stats.status.str.startswith("UNPAIRED")).sum())
        if "status" in stats else 0,
        "total_windows_joined": int(ok.windows_joined.sum()) if len(ok) else 0,
        "median_join_rate": float(ok.join_rate.median()) if len(ok) else 0.0,
        "min_join_rate": float(ok.join_rate.min()) if len(ok) else 0.0,
        "median_overlap_fraction": float(ok.overlap_fraction.median()) if len(ok) else 0.0,
        "median_abs_start_offset_s": float(ok.start_offset_s.abs().median()) if len(ok) else 0.0,
        "max_abs_start_offset_s": float(ok.start_offset_s.abs().max()) if len(ok) else 0.0,
    }
    (OUT / "statistics" / "join_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== SUMMARY ===")
    for k, v in summary.items():
        print(f"  {k:28s} {v}")
    if frames:
        allf = pd.concat(frames, ignore_index=True)
        print(f"\n  joined windows: {len(allf):,}  features: {allf.shape[1]}")
        print(f"  runs: {allf.run_id.nunique()}  categories: "
              f"{allf.category.value_counts().to_dict()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
