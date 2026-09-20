"""The vectorised exporter must agree with the reference, or it is not an optimisation.

A faster extractor that produces different flow records is a second bug wearing a
benchmark result. These tests pin the agreement, and pin the two refusals that
exist because guessing is what produced 5,851 fictional flows in B-A.
"""
from __future__ import annotations

import struct
from pathlib import Path

import pytest

from oran_ids.ingest import fast_exporter as fx
from oran_ids.ingest.exporter import ExporterConfig, export_file

DLT_LINUX_SLL, DLT_EN10MB = 113, 1


def build_pcap(path: Path, packets, linktype: int = DLT_LINUX_SLL) -> Path:
    """``packets`` is a list of (ts, src, dst, sport, dport, payload_len)."""
    if linktype == DLT_LINUX_SLL:
        link = struct.pack(">HHH", 0, 1, 6) + b"\x00" * 8 + struct.pack(">H", 0x0800)
    else:
        link = b"\x00" * 12 + struct.pack(">H", 0x0800)
    assert len(link) == (16 if linktype == DLT_LINUX_SLL else 14)

    out = [struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, linktype)]
    for ts, src, dst, sp, dp, plen in packets:
        ip_len = 20 + 20 + plen
        ipv4 = (b"\x45\x00" + struct.pack(">H", ip_len)
                + b"\x00\x01\x00\x00\x40\x06\x00\x00"
                + struct.pack(">II", src, dst))
        tcp = (struct.pack(">HH", sp, dp) + struct.pack(">II", 1, 1)
               + b"\x50\x10\xff\xff\x00\x00\x00\x00")
        pkt = link + ipv4 + tcp + b"\x00" * plen
        out.append(struct.pack("<IIII", int(ts), int((ts % 1) * 1e6),
                               len(pkt), len(pkt)))
        out.append(pkt)
    path.write_bytes(b"".join(out))
    return path


A, B = 0x0A000001, 0xAC1F0086          # 10.0.0.1, 172.31.0.134


def test_agrees_with_reference_on_a_simple_capture(tmp_path):
    p = build_pcap(tmp_path / "a.pcap", [
        (1700000000.0, A, B, 1234, 80, 0),
        (1700000000.1, B, A, 80, 1234, 100),
        (1700000000.2, A, B, 1234, 80, 50),
    ])
    fast, st = fx.extract(p, ExporterConfig())
    ref = export_file(p, ExporterConfig())
    rep = fx.assert_equivalent(fast, ref)
    assert rep["agrees"], rep
    assert st.coverage == 1.0


def test_agrees_across_many_interleaved_flows(tmp_path):
    """Interleaving matters: contiguous per-flow packets hide ordering bugs."""
    pkts = []
    for i in range(40):
        for f in range(25):
            pkts.append((1700000000.0 + i * 0.01, A + f, B, 2000 + f, 80, f))
    p = build_pcap(tmp_path / "b.pcap", pkts)
    fast, st = fx.extract(p, ExporterConfig())
    rep = fx.assert_equivalent(fast, export_file(p, ExporterConfig()))
    assert rep["agrees"], rep
    assert rep["n_keys_both"] == 25
    assert rep["total_pkts_fast"] == rep["total_pkts_ref"] == 1000


def test_byte_counts_are_ip_layer_not_payload(tmp_path):
    """The D-015 distinction, enforced at the exporter too.

    ``total_ip_bytes`` must count the IP header, so a payload-free packet is 40
    bytes and not 0. Zeek's payload-only column is exactly the trap that would
    have manufactured the paper's transfer gap.
    """
    p = build_pcap(tmp_path / "c.pcap", [(1700000000.0, A, B, 1234, 80, 0)])
    fast, _ = fx.extract(p, ExporterConfig())
    assert fast["total_ip_bytes"].iloc[0] == 40


def test_idle_timeout_splits_a_reused_five_tuple(tmp_path):
    cfg = ExporterConfig(idle_timeout_s=30.0)
    p = build_pcap(tmp_path / "d.pcap", [
        (1700000000.0, A, B, 1234, 80, 0),
        (1700000001.0, A, B, 1234, 80, 0),
        (1700000200.0, A, B, 1234, 80, 0),      # 199 s later: a new flow
    ])
    fast, _ = fx.extract(p, cfg)
    assert len(fast) == 2, "idle timeout did not split the reused 5-tuple"


def test_unknown_link_type_is_refused_not_guessed(tmp_path):
    p = build_pcap(tmp_path / "e.pcap", [(1700000000.0, A, B, 1, 2, 0)],
                   linktype=DLT_EN10MB)
    raw = bytearray(p.read_bytes())
    raw[20:24] = struct.pack("<I", 999)          # a link type nobody knows
    p.write_bytes(bytes(raw))
    with pytest.raises(ValueError, match="Refusing to guess"):
        fx.extract(p, ExporterConfig())


def test_ethernet_capture_is_parsed_at_the_right_offset(tmp_path):
    """The other half of B-A: 14 bytes for Ethernet, 16 for SLL."""
    p = build_pcap(tmp_path / "f.pcap",
                   [(1700000000.0, A, B, 1234, 80, 10)], linktype=DLT_EN10MB)
    fast, st = fx.extract(p, ExporterConfig())
    assert st.coverage == 1.0
    assert fast["src_ip"].iloc[0] == "10.0.0.1"
    assert fast["dst_ip"].iloc[0] == "172.31.0.134"


def test_empty_capture_does_not_raise(tmp_path):
    p = build_pcap(tmp_path / "g.pcap", [])
    fast, st = fx.extract(p, ExporterConfig())
    assert len(fast) == 0 and st.n_records == 0


def test_parse_stats_account_for_every_record(tmp_path):
    """Skipped packets are counted. A benchmark that drops the hard ones lies."""
    p = build_pcap(tmp_path / "h.pcap",
                   [(1700000000.0 + i, A + i, B, 100 + i, 80, 0) for i in range(5)])
    _, st = fx.extract(p, ExporterConfig())
    accounted = (st.n_parsed + st.n_skipped_link + st.n_skipped_not_ipv4
                 + st.n_skipped_ip_options)
    assert accounted == st.n_records
