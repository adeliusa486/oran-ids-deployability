"""Guards on the D_A/D_B shared feature space.

The failure mode these tests exist for is silence. Every bug below produces a
matrix of the right shape, full of plausible floats, that a model will happily
fit and score. Nothing raises. The number is simply wrong, and the wrongness
looks exactly like a scientific finding about deployment shift.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from oran_ids.features import shared as sh


def d_a_row(**kw) -> pd.DataFrame:
    base = dict(duration=1.0, src_bytes=0, dst_bytes=0, src_ip_bytes=1000,
                dst_ip_bytes=500, src_pkts=10, dst_pkts=5, proto="tcp")
    base.update(kw)
    return pd.DataFrame([base])


def d_b_row(**kw) -> pd.DataFrame:
    base = dict(Dur=1.0, SrcBytes=1000, DstBytes=500, SrcPkts=10, DstPkts=5,
                TotPkts=15, TotBytes=1500, Proto="tcp")
    base.update(kw)
    return pd.DataFrame([base])


# --------------------------------------------------------------------------
# D-015. The one that would have inflated every transfer gap in the paper.
# --------------------------------------------------------------------------

def test_d_a_uses_ip_bytes_not_payload_bytes():
    """Zeek payload bytes are median 0; Argus SrcBytes is header-inclusive.

    If this ever regresses to ``src_bytes``, the source matrix becomes a column
    of zeros against a target column of real byte counts, and the resulting
    Delta_F1 measures our own preprocessing rather than deployment shift.
    """
    # Payload 0, IP bytes 1000: the real shape of a SYN flood record in D_A.
    out = sh.from_d_a(d_a_row(src_bytes=0, src_ip_bytes=1000))
    assert out["src_bytes"].iloc[0] == pytest.approx(np.log1p(1000), rel=1e-6)

    # And it must not be reading the payload column even when that is non-zero.
    out2 = sh.from_d_a(d_a_row(src_bytes=999999, src_ip_bytes=1000))
    assert out2["src_bytes"].iloc[0] == pytest.approx(np.log1p(1000), rel=1e-6)


def test_identical_flows_map_to_identical_vectors():
    """The whole experiment rests on this: equal traffic, equal feature vector.

    Same duration, same header-inclusive byte counts, same packet counts, same
    protocol -- expressed in each exporter's own schema -- must produce the same
    18 numbers. Any asymmetry in the derived arithmetic shows up here.
    """
    a = sh.from_d_a(d_a_row())
    b = sh.from_d_b(d_b_row())
    sh.assert_compatible(a, b)
    np.testing.assert_allclose(a.to_numpy(), b.to_numpy(), rtol=1e-6)


# --------------------------------------------------------------------------
# Matrix compatibility
# --------------------------------------------------------------------------

def test_column_order_is_canonical_for_both_corpora():
    assert tuple(sh.from_d_a(d_a_row()).columns) == sh.COLUMNS
    assert tuple(sh.from_d_b(d_b_row()).columns) == sh.COLUMNS
    assert len(sh.COLUMNS) == 18


def test_absent_protocol_still_emits_its_column():
    """A corpus with no ICMP must not produce a narrower matrix.

    Learning one-hot levels per corpus is the classic way source and target end
    up with different widths -- or worse, the same width with different meanings.
    """
    out = sh.from_d_b(pd.concat([d_b_row(Proto="tcp"), d_b_row(Proto="udp")]))
    assert tuple(out.columns) == sh.COLUMNS
    assert out["proto_icmp"].sum() == 0


def test_unknown_protocol_becomes_other_not_a_new_column():
    out = sh.from_d_b(d_b_row(Proto="sctp"))
    assert out["proto_other"].iloc[0] == 1
    assert out["proto_tcp"].iloc[0] == 0
    assert tuple(out.columns) == sh.COLUMNS


def test_protocol_case_does_not_silently_become_other():
    """A capitalised 'TCP' collapsing to 'other' is a shift we invented."""
    assert sh.from_d_b(d_b_row(Proto="TCP"))["proto_tcp"].iloc[0] == 1


def test_assert_compatible_rejects_permuted_columns():
    """Permuted columns do not raise inside sklearn. They predict, confidently."""
    a = sh.from_d_a(d_a_row())
    b = sh.from_d_b(d_b_row())[list(reversed(sh.COLUMNS))]
    with pytest.raises(ValueError, match="mismatch"):
        sh.assert_compatible(a, b)


# --------------------------------------------------------------------------
# Degenerate inputs. Both corpora contain all of these.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("kw", [
    dict(Dur=0.0),                                   # instantaneous flow
    dict(SrcPkts=0, DstPkts=0, TotPkts=0),           # no packets counted
    dict(SrcBytes=0, DstBytes=0, TotBytes=0),        # no bytes counted
    dict(Dur=0.0, SrcPkts=0, DstPkts=0, TotPkts=0,
         SrcBytes=0, DstBytes=0, TotBytes=0),        # all of it at once
])
def test_degenerate_rows_stay_finite(kw):
    out = sh.from_d_b(d_b_row(**kw))
    assert np.isfinite(out.to_numpy()).all(), f"non-finite value from {kw}"


def test_missing_source_column_raises_rather_than_filling():
    with pytest.raises(KeyError, match="shared-space"):
        sh.from_d_a(d_a_row().drop(columns=["src_ip_bytes"]))


def test_spec_counts_match_the_implementation():
    """The committed table and the code must not drift apart."""
    spec = sh.load_spec()["counts"]
    assert spec["model_matrix_columns"] == len(sh.COLUMNS)
    assert spec["base_numeric"] == len(sh.BASE_NUMERIC)
    assert spec["derived"] == len(sh.DERIVED)
    assert spec["shared_concepts"] == 15
