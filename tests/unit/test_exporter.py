"""Tests for the single flow exporter.

The exporter is the A3 control: if it is wrong or non-deterministic, the
headline cross-deployment number is not interpretable. These tests pin the
behaviour that could otherwise drift silently between corpora or between runs.
"""
from __future__ import annotations

import socket
from pathlib import Path

import dpkt
import pytest

from oran_ids.ingest import EXPORTER_VERSION, FEATURE_COLUMNS, ExporterConfig, export_file


# --------------------------------------------------------------------------
# helpers: build a pcap on disk from a packet spec, so tests read like traffic
# --------------------------------------------------------------------------
def _tcp_packet(src: str, dst: str, sport: int, dport: int, flags: int,
                payload: bytes = b"", ttl: int = 64) -> bytes:
    tcp = dpkt.tcp.TCP(sport=sport, dport=dport, flags=flags, data=payload)
    tcp.off = 5
    ip = dpkt.ip.IP(src=socket.inet_aton(src), dst=socket.inet_aton(dst),
                    p=dpkt.ip.IP_PROTO_TCP, ttl=ttl, data=tcp)
    ip.len = len(bytes(ip))
    eth = dpkt.ethernet.Ethernet(src=b"\x00" * 6, dst=b"\x11" * 6,
                                 type=dpkt.ethernet.ETH_TYPE_IP, data=ip)
    return bytes(eth)


def _udp_packet(src: str, dst: str, sport: int, dport: int, payload: bytes = b"") -> bytes:
    udp = dpkt.udp.UDP(sport=sport, dport=dport, data=payload)
    udp.ulen = len(bytes(udp))
    ip = dpkt.ip.IP(src=socket.inet_aton(src), dst=socket.inet_aton(dst),
                    p=dpkt.ip.IP_PROTO_UDP, ttl=64, data=udp)
    ip.len = len(bytes(ip))
    eth = dpkt.ethernet.Ethernet(src=b"\x00" * 6, dst=b"\x11" * 6,
                                 type=dpkt.ethernet.ETH_TYPE_IP, data=ip)
    return bytes(eth)


def _write_pcap(path: Path, packets: list[tuple[float, bytes]]) -> Path:
    with path.open("wb") as fh:
        writer = dpkt.pcap.Writer(fh)
        for ts, buf in packets:
            writer.writepkt(buf, ts=ts)
    return path


SYN, SYNACK, ACK, PSH_ACK, FIN_ACK, RST = 0x02, 0x12, 0x10, 0x18, 0x11, 0x04


@pytest.fixture
def handshake_pcap(tmp_path: Path) -> Path:
    """A complete TCP handshake, one data exchange, and a clean close."""
    p = [
        (1000.0, _tcp_packet("10.0.0.1", "10.0.0.2", 1234, 80, SYN)),
        (1000.1, _tcp_packet("10.0.0.2", "10.0.0.1", 80, 1234, SYNACK)),
        (1000.2, _tcp_packet("10.0.0.1", "10.0.0.2", 1234, 80, ACK)),
        (1000.3, _tcp_packet("10.0.0.1", "10.0.0.2", 1234, 80, PSH_ACK, b"GET / HTTP/1.1\r\n")),
        (1000.5, _tcp_packet("10.0.0.2", "10.0.0.1", 80, 1234, PSH_ACK, b"HTTP/1.1 200 OK\r\n\r\n")),
        (1000.6, _tcp_packet("10.0.0.1", "10.0.0.2", 1234, 80, FIN_ACK)),
    ]
    return _write_pcap(tmp_path / "handshake.pcap", p)


# --------------------------------------------------------------------------
# schema and contract
# --------------------------------------------------------------------------
def test_emitted_columns_match_the_declared_contract(handshake_pcap):
    rows = export_file(handshake_pcap)
    assert rows, "a complete TCP exchange must produce at least one flow"
    assert tuple(rows[0].keys()) == FEATURE_COLUMNS, (
        "column set or order drifted from FEATURE_COLUMNS; downstream code and the "
        "shared-feature-space assertion both depend on this being stable"
    )


def test_version_is_pinned():
    assert EXPORTER_VERSION == "1.0.0"


def test_config_fingerprint_changes_with_semantics():
    a = ExporterConfig().fingerprint()
    b = ExporterConfig(active_timeout_s=60.0).fingerprint()
    c = ExporterConfig(idle_timeout_s=15.0).fingerprint()
    assert a != b != c and a != c, (
        "the fingerprint must distinguish exporter semantics, or the manifest "
        "cannot prove both corpora were extracted the same way"
    )


# --------------------------------------------------------------------------
# determinism -- the byte-identical-rerun guarantee
# --------------------------------------------------------------------------
def test_two_runs_over_the_same_file_agree_exactly(handshake_pcap):
    assert export_file(handshake_pcap) == export_file(handshake_pcap)


def test_emission_order_is_total_and_stable(tmp_path):
    """Flows starting at the same instant must still have a defined order."""
    pkts = []
    for i in range(20):
        pkts.append((1000.0, _tcp_packet("10.0.0.1", f"10.0.0.{i + 2}", 1000 + i, 80, SYN)))
    path = _write_pcap(tmp_path / "simul.pcap", pkts)
    first = [r["flow_id"] for r in export_file(path)]
    second = [r["flow_id"] for r in export_file(path)]
    assert first == second
    assert first == sorted(first), "ties must break on flow_id, not on dict order"


# --------------------------------------------------------------------------
# direction inference
# --------------------------------------------------------------------------
def test_direction_is_fixed_by_the_first_packet(handshake_pcap):
    row = export_file(handshake_pcap)[0]
    assert row["src_ip"] == "10.0.0.1", "the initiator must be the forward direction"
    assert row["fwd_pkts"] == 4 and row["bwd_pkts"] == 2


def test_reverse_packets_join_the_same_flow(handshake_pcap):
    assert len(export_file(handshake_pcap)) == 1, (
        "bidirectional keying must not split a conversation into two flows"
    )


def test_unidirectional_mode_splits_the_conversation(handshake_pcap):
    rows = export_file(handshake_pcap, ExporterConfig(bidirectional=False))
    assert len(rows) == 2


def test_unimplemented_direction_policy_is_refused(handshake_pcap):
    with pytest.raises(ValueError, match="direction_policy"):
        export_file(handshake_pcap, ExporterConfig(direction_policy="port_heuristic"))


# --------------------------------------------------------------------------
# timeouts -- the parameters most likely to differ between two exporters
# --------------------------------------------------------------------------
def test_idle_timeout_splits_a_gap(tmp_path):
    p = [
        (1000.0, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53)),
        (1005.0, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53)),
        # a gap wider than the 30 s idle timeout
        (1100.0, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53)),
    ]
    path = _write_pcap(tmp_path / "idle.pcap", p)
    assert len(export_file(path)) == 2


def test_idle_timeout_does_not_split_below_the_threshold(tmp_path):
    p = [
        (1000.0, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53)),
        (1020.0, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53)),
    ]
    path = _write_pcap(tmp_path / "noidle.pcap", p)
    assert len(export_file(path)) == 1


def test_active_timeout_splits_a_long_flow(tmp_path):
    p = [(1000.0 + i * 10.0, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53)) for i in range(30)]
    path = _write_pcap(tmp_path / "active.pcap", p)
    rows = export_file(path)
    assert len(rows) >= 2, "a 290 s flow must be cut by the 120 s active timeout"
    for r in rows:
        assert r["duration"] <= ExporterConfig().active_timeout_s + 10.0


# --------------------------------------------------------------------------
# feature correctness
# --------------------------------------------------------------------------
def test_counts_and_duration(handshake_pcap):
    row = export_file(handshake_pcap)[0]
    assert row["total_pkts"] == 6
    assert row["duration"] == pytest.approx(0.6, abs=1e-6)
    assert row["fwd_bytes"] == len(b"GET / HTTP/1.1\r\n")
    assert row["bwd_bytes"] == len(b"HTTP/1.1 200 OK\r\n\r\n")


def test_tcp_flag_counts(handshake_pcap):
    row = export_file(handshake_pcap)[0]
    assert row["flag_syn"] == 2, "SYN and SYN-ACK both carry the SYN bit"
    assert row["flag_fin"] == 1
    assert row["flag_ack"] == 5
    assert row["flag_rst"] == 0
    assert row["handshake_complete"] == 1


def test_incomplete_handshake_is_flagged_but_kept_by_default(tmp_path):
    """SYN scanning is the case this must get right: the flows are the signal."""
    p = [(1000.0 + i * 0.001, _tcp_packet("10.0.0.1", "10.0.0.2", 1234, 80 + i, SYN))
         for i in range(5)]
    path = _write_pcap(tmp_path / "scan.pcap", p)
    rows = export_file(path)
    assert len(rows) == 5
    assert all(r["handshake_complete"] == 0 for r in rows)


def test_drop_incomplete_handshakes_when_asked(tmp_path):
    p = [(1000.0 + i * 0.001, _tcp_packet("10.0.0.1", "10.0.0.2", 1234, 80 + i, SYN))
         for i in range(5)]
    path = _write_pcap(tmp_path / "scan2.pcap", p)
    assert export_file(path, ExporterConfig(drop_incomplete_handshakes=True)) == []


def test_rates_are_zero_not_infinite_for_a_single_packet(tmp_path):
    path = _write_pcap(tmp_path / "one.pcap",
                       [(1000.0, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53))])
    row = export_file(path)[0]
    assert row["duration"] == 0.0
    assert row["pkts_per_s"] == 0.0 and row["bytes_per_s"] == 0.0


def test_ratios_are_finite_for_unidirectional_flows(tmp_path):
    path = _write_pcap(tmp_path / "uni.pcap",
                       [(1000.0 + i * 0.01, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53, b"x" * 100))
                        for i in range(10)])
    row = export_file(path)[0]
    assert row["bwd_pkts"] == 0
    assert row["pkts_ratio"] == pytest.approx(10.0)
    assert row["bytes_ratio"] == pytest.approx(1000.0)


def test_iat_statistics(tmp_path):
    path = _write_pcap(tmp_path / "iat.pcap",
                       [(1000.0 + i * 0.5, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53))
                        for i in range(5)])
    row = export_file(path)[0]
    assert row["iat_mean"] == pytest.approx(0.5, abs=1e-6)
    assert row["iat_std"] == pytest.approx(0.0, abs=1e-6)
    assert row["iat_min"] == pytest.approx(0.5, abs=1e-6)


def test_empty_capture_yields_no_flows(tmp_path):
    assert export_file(_write_pcap(tmp_path / "empty.pcap", [])) == []


def test_non_ip_traffic_is_skipped(tmp_path):
    arp = dpkt.ethernet.Ethernet(src=b"\x00" * 6, dst=b"\xff" * 6,
                                 type=dpkt.ethernet.ETH_TYPE_ARP, data=dpkt.arp.ARP())
    path = _write_pcap(tmp_path / "arp.pcap", [(1000.0, bytes(arp))])
    assert export_file(path) == []


def test_float_features_are_rounded_to_fixed_precision(tmp_path):
    """Guards the byte-identical guarantee against last-bit drift."""
    path = _write_pcap(tmp_path / "prec.pcap",
                       [(1000.0 + i / 3.0, _udp_packet("10.0.0.1", "10.0.0.2", 5000, 53))
                        for i in range(4)])
    row = export_file(path)[0]
    for k, v in row.items():
        if isinstance(v, float):
            assert v == round(v, 9), f"{k} was not rounded"
