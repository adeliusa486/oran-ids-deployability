#!/usr/bin/env python3
"""EXP-030: how much of the feature-extraction cost is Python?

EXP-005 found packet-level extraction costing 4.49-37.34 ms per flow against
0.18-0.96 ms of inference, and recorded the caveat that its exporter is a
pure-Python reference running at 1.1-4.3 MB/s.

EXP-031 turned that caveat into the main question. Obiuwevwi et al. (2026)
measure 1-5 microseconds of inference inside a real Near-RT RIC. Against
microsecond inference, extraction is not the larger half of the latency budget --
it is the entire budget, and the only interesting number is its floor.

Three implementations are compared:

  reference     src/oran_ids/ingest/exporter.py, per-packet dpkt object graph
  vectorised    src/oran_ids/ingest/fast_exporter.py, bulk NumPy header extraction
  precomputed   features already in the corpus CSV -- zero extraction cost at
                inference time, at the price of an external exporter in the path

**On the capture used.** The original D_A pcaps are not on disk: D-010 stopped
the 16.85 GB bulk download, and EXP-005's numbers were measured before that.
Extraction throughput is a function of packet count, flow count, packets-per-flow
and link type, none of which depend on payload semantics, so this benchmark uses
synthetic captures with those four quantities controlled exactly. That is a
fair instrument for an implementation comparison and a poor one for an absolute
claim, so the reference implementation is re-measured here too and its throughput
checked against the 1.1-4.3 MB/s band recorded on the real captures. If it lands
outside that band, the synthetic capture is not representative and the comparison
is reported as such rather than quietly used.

Captures are DLT_LINUX_SLL (113), matching D_A -- the link type whose
misparsing as Ethernet was bug B-A.

Usage:  python experiments/run_extraction_benchmark.py [--quick]
"""
from __future__ import annotations

import argparse
import json
import platform
import struct
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.ingest.exporter import EXPORTER_VERSION, ExporterConfig, export_file  # noqa: E402
from oran_ids.ingest import fast_exporter as fx  # noqa: E402

warnings.filterwarnings("ignore")

OUT = Path("results/EXP-030")
SCRATCH = Path("results/EXP-030/_captures")

# EXP-005's real captures, for calibration. Packets-per-flow is what drives
# per-flow cost, and it varies 8x across these three.
REAL_REFERENCE = {
    "ddos_icmp_hping3": dict(mb=224.2, flows=1406, ms_per_flow=37.338, mb_per_s=4.3),
    "ddos_udp_hping3": dict(mb=447.0, flows=38340, ms_per_flow=4.49, mb_per_s=2.6),
    "ddos_syn_hping3": dict(mb=1452.5, flows=191326, ms_per_flow=6.901, mb_per_s=1.1),
}

DLT_LINUX_SLL = 113


def write_synthetic_pcap(path: Path, *, n_flows: int, pkts_per_flow: int,
                         payload_bytes: int = 0, seed: int = 7) -> dict:
    """A DLT_LINUX_SLL capture with an exactly known flow and packet structure.

    Packets are interleaved across flows, as they are in a real capture: emitting
    each flow's packets contiguously would give the reference exporter a
    cache-friendly pattern it does not enjoy in practice.
    """
    rng = np.random.default_rng(seed)
    path.parent.mkdir(parents=True, exist_ok=True)

    ip_len = 20 + 20 + payload_bytes            # IPv4 + TCP + payload
    # DLT_LINUX_SLL: packet type (2) + ARPHRD type (2) + address length (2)
    # + address (8) + protocol (2) = 16 bytes. The 16-versus-14 difference
    # against Ethernet is exactly what bug B-A got wrong.
    sll = struct.pack(">HHH", 0, 1, 6) + b"\x00" * 8 + struct.pack(">H", 0x0800)
    assert len(sll) == 16

    srcs = rng.integers(0x0A000001, 0x0A00FFFF, size=n_flows, dtype=np.int64)
    dsts = np.full(n_flows, 0xAC1F0086, dtype=np.int64)     # 172.31.0.134
    sports = rng.integers(1024, 65535, size=n_flows, dtype=np.int64)
    dports = np.full(n_flows, 80, dtype=np.int64)

    order = np.tile(np.arange(n_flows), pkts_per_flow)
    rng.shuffle(order)

    chunks = [struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, DLT_LINUX_SLL)]
    t0 = 1_700_000_000
    for i, f in enumerate(order):
        ts = t0 + i * 0.0001
        ipv4 = (b"\x45\x00" + struct.pack(">H", ip_len) + b"\x00\x01\x00\x00\x40\x06"
                + b"\x00\x00" + struct.pack(">II", int(srcs[f]), int(dsts[f])))
        tcp = (struct.pack(">HH", int(sports[f]), int(dports[f]))
               + struct.pack(">II", 1, 1) + b"\x50\x10\xff\xff\x00\x00\x00\x00")
        pkt = sll + ipv4 + tcp + b"\x00" * payload_bytes
        chunks.append(struct.pack("<IIII", int(ts), int((ts % 1) * 1e6),
                                  len(pkt), len(pkt)))
        chunks.append(pkt)

    blob = b"".join(chunks)
    path.write_bytes(blob)
    return dict(path=str(path), bytes=len(blob), mb=len(blob) / 1e6,
                n_flows=n_flows, pkts_per_flow=pkts_per_flow,
                n_packets=n_flows * pkts_per_flow, link_type=DLT_LINUX_SLL)


def time_it(fn, *a, **kw):
    import gc
    gc.collect()
    t0 = time.perf_counter()
    r = fn(*a, **kw)
    return r, time.perf_counter() - t0


def peak_rss_mb() -> float:
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1e6
    except Exception:
        return float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    for d in ("raw", "processed", "statistics", "logs"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)

    # (n_flows, pkts_per_flow) chosen to bracket the real captures' shapes:
    # the ICMP flood was 1,406 flows over 224 MB (many packets per flow), the
    # SYN flood 191,326 flows (few packets per flow).
    shapes = ([(200, 20), (2_000, 10)] if args.quick else
              [(200, 200), (2_000, 50), (20_000, 10), (50_000, 4), (100_000, 2)])

    rows = []
    for n_flows, ppf in shapes:
        cap = SCRATCH / ("syn_%df_%dp.pcap" % (n_flows, ppf))
        meta = write_synthetic_pcap(cap, n_flows=n_flows, pkts_per_flow=ppf)
        print("\ncapture: %(n_flows)d flows x %(pkts_per_flow)d pkts = "
              "%(n_packets)d packets, %(mb).1f MB" % meta, flush=True)

        rss0 = peak_rss_mb()
        ref_rows, t_ref = time_it(export_file, cap, ExporterConfig())
        rss_ref = peak_rss_mb() - rss0

        rss0 = peak_rss_mb()
        (fast_df, st), t_fast = time_it(fx.extract, cap, ExporterConfig())
        rss_fast = peak_rss_mb() - rss0

        eq = fx.assert_equivalent(fast_df, ref_rows)

        for impl, secs, nflows_out, rss in (
                ("reference_python", t_ref, len(ref_rows), rss_ref),
                ("vectorised_numpy", t_fast, len(fast_df), rss_fast)):
            rows.append(dict(
                implementation=impl, n_flows_declared=n_flows,
                pkts_per_flow=ppf, n_packets=meta["n_packets"],
                mb=meta["mb"], seconds=secs,
                mb_per_s=meta["mb"] / secs if secs else float("nan"),
                pkts_per_s=meta["n_packets"] / secs if secs else float("nan"),
                n_flows_emitted=nflows_out,
                ms_per_flow=1000 * secs / max(nflows_out, 1),
                us_per_packet=1e6 * secs / max(meta["n_packets"], 1),
                rss_delta_mb=rss,
                parse_coverage=st.coverage if impl == "vectorised_numpy" else 1.0))
            print("  %-18s %7.2fs  %6.1f MB/s  %8.3f ms/flow  %6.2f us/pkt"
                  % (impl, secs, meta["mb"] / secs, 1000 * secs / max(nflows_out, 1),
                     1e6 * secs / meta["n_packets"]), flush=True)
        print("  equivalence: %s" % {k: eq[k] for k in
                                     ("agrees", "n_keys_both", "n_pkt_mismatch",
                                      "n_byte_mismatch", "n_keys_fast_only",
                                      "n_keys_ref_only") if k in eq}, flush=True)
        print("  bulk parse coverage: %.4f  %s" % (st.coverage, st.as_dict()),
              flush=True)
        rows[-1]["equivalent"] = eq.get("agrees", False)
        rows[-2]["equivalent"] = eq.get("agrees", False)
        cap.unlink(missing_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "raw/extraction_benchmark.csv", index=False)

    # ---- calibration against the real captures --------------------------
    ref = df[df.implementation == "reference_python"]
    band = (min(v["mb_per_s"] for v in REAL_REFERENCE.values()),
            max(v["mb_per_s"] for v in REAL_REFERENCE.values()))
    in_band = bool(((ref.mb_per_s >= band[0] * 0.5)
                    & (ref.mb_per_s <= band[1] * 2.0)).mean() >= 0.5)
    print("\n=== calibration against EXP-005's real captures ===")
    print("  real-capture band        : %.1f - %.1f MB/s" % band)
    print("  synthetic, reference impl: %.1f - %.1f MB/s"
          % (ref.mb_per_s.min(), ref.mb_per_s.max()))
    print("  representative (within 2x of the band): %s" % in_band)

    # ---- the comparison --------------------------------------------------
    piv = df.pivot_table(index=["n_flows_declared", "pkts_per_flow"],
                         columns="implementation",
                         values=["mb_per_s", "ms_per_flow", "us_per_packet"])
    speed = (piv[("mb_per_s", "vectorised_numpy")]
             / piv[("mb_per_s", "reference_python")])
    summary = pd.DataFrame({
        "mb_per_s_reference": piv[("mb_per_s", "reference_python")],
        "mb_per_s_vectorised": piv[("mb_per_s", "vectorised_numpy")],
        "speedup": speed,
        "ms_per_flow_reference": piv[("ms_per_flow", "reference_python")],
        "ms_per_flow_vectorised": piv[("ms_per_flow", "vectorised_numpy")],
        "us_per_pkt_reference": piv[("us_per_packet", "reference_python")],
        "us_per_pkt_vectorised": piv[("us_per_packet", "vectorised_numpy")],
    }).reset_index()
    summary.to_csv(OUT / "processed/extraction_speedup.csv", index=False)

    print("\n=== implementation comparison ===")
    print(summary.to_string(index=False, float_format=lambda v: "%.3f" % v))

    # ---- what it means against microsecond inference ---------------------
    # Obiuwevwi et al. 2026: 1-5 us logreg, 10-25 us MLP on a real Near-RT RIC.
    best_ms_per_flow = float(summary["ms_per_flow_vectorised"].min())
    verdict = dict(
        best_vectorised_ms_per_flow=best_ms_per_flow,
        deployed_inference_us_obiuwevwi_2026=dict(logreg=[1, 5], mlp=[10, 25]),
        extraction_over_deployed_inference_ratio=dict(
            logreg=best_ms_per_flow * 1000 / 3.0,
            mlp=best_ms_per_flow * 1000 / 17.5),
        speedup_over_reference=float(summary["speedup"].max()),
        still_dominates=bool(best_ms_per_flow * 1000 > 25.0))
    print("\n=== against deployed (not prototype) inference ===")
    print("  best vectorised extraction : %.4f ms/flow" % best_ms_per_flow)
    print("  vs 1-5 us logreg           : %.0fx" %
          verdict["extraction_over_deployed_inference_ratio"]["logreg"])
    print("  vs 10-25 us MLP            : %.0fx" %
          verdict["extraction_over_deployed_inference_ratio"]["mlp"])
    print("  extraction still dominates : %s" % verdict["still_dominates"])

    prov = dict(
        experiment="EXP-030", exporter_version=EXPORTER_VERSION,
        fast_exporter_version=fx.FAST_EXPORTER_VERSION,
        capture="SYNTHETIC -- original D_A pcaps not on disk (D-010)",
        link_type=DLT_LINUX_SLL, shapes=shapes,
        calibration_band_mb_per_s=list(band),
        calibration_representative=in_band,
        real_capture_reference=REAL_REFERENCE,
        all_equivalent=bool(df.get("equivalent", pd.Series([False])).all()),
        verdict=verdict,
        python=platform.python_version(), platform=platform.platform())
    (OUT / "statistics/provenance.json").write_text(
        json.dumps(prov, indent=2, default=str), encoding="utf-8")

    try:
        SCRATCH.rmdir()
    except OSError:
        pass
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
