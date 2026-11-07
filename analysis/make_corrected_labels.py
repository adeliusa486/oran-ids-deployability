#!/usr/bin/env python3
"""EXP-072 part C: a corrected label file for 5G-NIDD (Reviewer 2, R2.2d).

Writes the rows of 5G-NIDD's Combined.csv whose label we correct, with the
published and the corrected labels side by side, so that any user can apply
(or ignore) the correction by row position. Nothing in the published files is
changed.

The corrected rows are the benign-labelled flows of capture file 5 (base
station 1, UDP-flood session) that are content copies of the UDP-flood flows of
capture file 15 (base station 2): identical in every field except the row
index, Seq and Offset (EXP-057), all UDP from 10.155.15.7 to 10.41.150.68 in
the fields-preserved release (EXP-062), and, in the raw captures, the same
packets as station 2's flood with identical timestamps (EXP-072 part A).

Usage:  python analysis/make_corrected_labels.py
Output: results/EXP-072/corrected_labels/
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from oran_ids.data import d_b_capture_files  # noqa: E402

RAW = ROOT / "data/raw/d_b"
OUT = ROOT / "results/EXP-072/corrected_labels"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    comb = pd.read_csv(RAW / "Combined.csv", low_memory=False)
    fp = pd.read_csv(zipfile.ZipFile(RAW / "pcap/BTS1_BTS2_fields_preserved.zip")
                     .open("BTS1_BTS2_fields_preserved.csv"),
                     usecols=["SrcAddr", "DstAddr", "Sport", "Dport", "Proto", "Seq"],
                     low_memory=False)
    if len(fp) != len(comb) or not (fp["Seq"].to_numpy() == comb["Seq"].to_numpy()).all():
        raise AssertionError("fields-preserved release does not align with Combined.csv")
    cf = d_b_capture_files(comb["Offset"].to_numpy())
    content = [c for c in comb.columns if c not in
               ("Unnamed: 0", "Seq", "Offset", "Label", "Attack Type", "Attack Tool")]
    h = pd.util.hash_pandas_object(comb[content], index=False).to_numpy()
    is_att = (comb["Label"] != "Benign").to_numpy()
    att_keys = set(h[is_att])
    copy = (~is_att) & np.fromiter((k in att_keys for k in h), bool, len(h))

    # every corrected row must be a file-5 UDP flow of the station-2 attacker
    sel = comb.loc[copy]
    assert set(cf[copy]) == {5}
    assert (fp.loc[copy, "SrcAddr"] == "10.155.15.7").all()
    assert (fp.loc[copy, "DstAddr"] == "10.41.150.68").all()
    assert (fp.loc[copy, "Proto"] == "udp").all()
    twin = comb.loc[(cf == 15) & is_att, ["Label", "Attack Type", "Attack Tool"]].drop_duplicates()
    assert len(twin) == 1, twin
    lab, typ, tool = twin.iloc[0]

    out = pd.DataFrame({
        "row_position": np.flatnonzero(copy),          # 0-based data row in Combined.csv
        "unnamed_0": sel["Unnamed: 0"].to_numpy(),
        "Seq": sel["Seq"].to_numpy(), "Offset": sel["Offset"].to_numpy(),
        "capture_file": cf[copy],
        "SrcAddr": fp.loc[copy, "SrcAddr"].to_numpy(), "DstAddr": fp.loc[copy, "DstAddr"].to_numpy(),
        "Label_published": sel["Label"].to_numpy(),
        "AttackType_published": sel["Attack Type"].to_numpy(),
        "AttackTool_published": sel["Attack Tool"].to_numpy(),
        "Label_corrected": lab, "AttackType_corrected": typ, "AttackTool_corrected": tool})
    path = OUT / "5G-NIDD_Combined_corrected_labels.csv.gz"
    out.to_csv(path, index=False, compression="gzip")
    meta = dict(
        rows_corrected=int(copy.sum()),
        attack_flows_in_file_15=int(((cf == 15) & is_att).sum()),
        benign_total=int((~is_att).sum()),
        share_of_benign_class=float(copy.sum() / (~is_att).sum()),
        corrected_to=dict(Label=lab, AttackType=typ, AttackTool=tool),
        combined_csv_sha256=sha256(RAW / "Combined.csv"),
        output=str(path.relative_to(ROOT)), output_sha256=sha256(path),
        how_to_apply="df = pd.read_csv('Combined.csv'); c = pd.read_csv(this_file); "
                     "df.loc[c.row_position, ['Label','Attack Type','Attack Tool']] = "
                     "c[['Label_corrected','AttackType_corrected','AttackTool_corrected']].values")
    (OUT / "README.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
