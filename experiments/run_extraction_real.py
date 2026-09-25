#!/usr/bin/env python3
"""EXP-043 part B: the vectorised exporter on the REAL D_A captures.

EXP-030 measured the vectorised exporter's speed-up (2.3x to 12.1x) on synthetic
captures, because D-010 had stopped the pcap download. The reviewed draft stated
the speed-up without saying so. The three DDoS captures EXP-005 timed with the
reference exporter are still inside `DDOS.zip` in the raw-data root, so the
vectorised exporter can be timed on exactly the traffic the reference saw.

For each capture: extract to a temporary file outside the repository, time
`fast_exporter.extract` (read + parse + group), and record flows, ms per flow,
MB/s and bulk-parse coverage. The reference exporter is re-run on the smallest
capture only (it takes ~1 min there and ~22 min on the largest) and the two are
compared record by record with `assert_equivalent`.

Run on a quiet machine: this is a timing experiment.

Usage:  python experiments/run_extraction_real.py
"""
from __future__ import annotations

import gc
import json
import platform
import shutil
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from oran_ids.ingest import fast_exporter as fx  # noqa: E402
from oran_ids.ingest.exporter import ExporterConfig, export_file  # noqa: E402

OUT = ROOT / "results" / "EXP-043"
ZIP = Path("C:/Users/adeel/oran-ids-data/d_a/DDOS.zip")
TMP = Path("C:/Users/adeel/oran-ids-data/d_a/_tmp_exp043")
CAPTURES = {   # EXP-005 reference measurements, same files
    "ddos_icmp_hping3": dict(ref_flows=1406, ref_ms_per_flow=37.338),
    "ddos_udp_hping3": dict(ref_flows=38340, ref_ms_per_flow=4.49),
    "ddos_syn_hping3": dict(ref_flows=191326, ref_ms_per_flow=6.901),
}


def main() -> int:
    t_start = time.time()
    for d in ("raw", "processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        with zipfile.ZipFile(ZIP) as z:
            for name, ref in CAPTURES.items():
                member = f"DDOS/Network_Layer/{name}.pcap"
                dst = TMP / f"{name}.pcap"
                with z.open(member) as fin, dst.open("wb") as fout:
                    shutil.copyfileobj(fin, fout, 16 << 20)
                mb = dst.stat().st_size / 1e6
                gc.collect()
                t0 = time.perf_counter()
                df, st = fx.extract(dst, ExporterConfig())
                secs = time.perf_counter() - t0
                rec = dict(capture=name, mb=mb, seconds=secs,
                           n_flows=len(df), ms_per_flow=1000 * secs / max(len(df), 1),
                           mb_per_s=mb / secs, ref_flows=ref["ref_flows"],
                           ref_ms_per_flow=ref["ref_ms_per_flow"],
                           speedup_vs_ref=ref["ref_ms_per_flow"]
                           / (1000 * secs / max(len(df), 1)),
                           **{f"parse_{k}": v for k, v in st.as_dict().items()})
                if name in ("ddos_icmp_hping3", "ddos_udp_hping3"):
                    ref_rows = export_file(dst, ExporterConfig())
                    rec.update({f"eq_{k}": v for k, v in
                                fx.assert_equivalent(df, ref_rows).items()})
                rows.append(rec)
                print(f"{name}: {mb:.1f} MB, {len(df)} flows, "
                      f"{rec['ms_per_flow']:.3f} ms/flow, {rec['mb_per_s']:.1f} MB/s,"
                      f" x{rec['speedup_vs_ref']:.1f} vs reference", flush=True)
                dst.unlink()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "processed/extraction_real_captures.csv", index=False)
    (OUT / "statistics/provenance_extraction.json").write_text(json.dumps(dict(
        experiment="EXP-043 part B", source=str(ZIP), captures=list(CAPTURES),
        exporter=f"fast_exporter {fx.FAST_EXPORTER_VERSION}",
        python=platform.python_version(), platform=platform.platform(),
        runtime_s=round(time.time() - t_start, 1)), indent=2), encoding="utf-8")
    print(R.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
