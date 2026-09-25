#!/usr/bin/env python3
"""EXP-057: records of 5G-NIDD that carry both labels.

Found while answering the round-2 review (R1-W1: why do four architectures
plateau at balanced accuracy 0.75 on D_B?). Many 5G-NIDD flow records are
byte-for-byte identical in every Argus field except the record counter (Seq)
and the file offset (Offset), yet carry opposite labels. No classifier that
reads the record content can separate them, so they set a ceiling on balanced
accuracy for every model trained or tested on D_B.

This audit reports, from the published files only:

  * the share of flows whose record (all Encoded.csv fields except Unnamed: 0,
    Seq, Offset and the labels) also occurs with the opposite label, per capture
    file and overall;
  * the same for the 18-column shared space of this paper;
  * the in-sample ceiling on balanced accuracy for any deterministic function of
    the record: predict attack for a distinct record iff its attack count, as a
    share of all attacks, exceeds its benign count as a share of all benign
    flows. This is the balanced-accuracy-optimal lookup, evaluated on the data it
    was built from, so no classifier can exceed it on these flows;
  * the same ceiling with Seq and Offset added back, which the published
    pipeline of Samarakoon et al. (arXiv:2212.01298) ranks first and second;
  * the largest conflicting records, with their files and attack types.

Capture files are recovered from resets of Offset (20 files, two passes, one
per base station). Every read of D_B is logged.

Usage:  python analysis/label_conflict_audit.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from oran_ids.data import _log_target_access, d_b_capture_files  # noqa: E402
from oran_ids.features import shared as _sh  # noqa: E402

OUT = ROOT / "results" / "EXP-057"
RAW = ROOT / "data" / "raw" / "d_b"
ID_COLS = ("Unnamed: 0", "Seq", "Offset")
LABELS = ("Label", "Attack Type", "Attack Tool")


def keys(X: pd.DataFrame) -> np.ndarray:
    return pd.util.hash_pandas_object(X.round(9), index=False).to_numpy()


def ceiling(k: np.ndarray, y: np.ndarray) -> dict:
    """Balanced-accuracy-optimal lookup on distinct records, in sample."""
    d = pd.DataFrame(dict(k=k, y=y))
    g = d.groupby("k").y.agg(n1="sum", n="size")
    g["n0"] = g.n - g.n1
    n1_all, n0_all = int(y.sum()), int((1 - y).sum())
    pred = (g.n1 / n1_all > g.n0 / n0_all).astype(int)
    tpr = float((pred * g.n1).sum() / n1_all)
    tnr = float(((1 - pred) * g.n0).sum() / n0_all)
    mixed = g[(g.n1 > 0) & (g.n0 > 0)]
    in_mixed = d.k.isin(mixed.index).to_numpy()
    return dict(n_distinct=int(len(g)), n_conflicting_records=int(len(mixed)),
                flows_in_conflicting=int(in_mixed.sum()),
                share_in_conflicting=float(in_mixed.mean()),
                benign_share_in_conflicting=float(in_mixed[y == 0].mean()),
                attack_share_in_conflicting=float(in_mixed[y == 1].mean()),
                ba_ceiling=(tpr + tnr) / 2, ceiling_tpr=tpr, ceiling_tnr=tnr), in_mixed


def main() -> int:
    for d in ("processed", "statistics"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    _log_target_access("EXP-057 label-conflict audit (Encoded.csv, Combined.csv)")
    enc = pd.read_csv(RAW / "Encoded.csv", low_memory=False)
    comb = pd.read_csv(RAW / "Combined.csv", low_memory=False,
                       usecols=["Dur", "SrcBytes", "DstBytes", "SrcPkts", "DstPkts",
                                "TotPkts", "TotBytes", "Proto", "Offset", "Label"])
    if not (np.array_equal(enc.Offset.to_numpy(), comb.Offset.to_numpy())
            and (enc.Label.to_numpy() == comb.Label.to_numpy()).all()):
        raise AssertionError("Encoded.csv and Combined.csv rows do not align")
    y = (enc.Label != "Benign").to_numpy(np.int8)
    files = d_b_capture_files(enc.Offset.to_numpy())
    content = (enc.drop(columns=list(ID_COLS + LABELS))
               .apply(pd.to_numeric, errors="coerce").fillna(0.0))
    with_pos = (enc.drop(columns=["Unnamed: 0"] + list(LABELS))
                .apply(pd.to_numeric, errors="coerce").fillna(0.0))
    shared = _sh.from_d_b(comb)

    rows, masks = [], {}
    for name, X in (("native_content", content), ("native_with_seq_offset", with_pos),
                    ("shared18", shared)):
        rec, masks[name] = ceiling(keys(X), y)
        rows.append(dict(feature_space=name, n_features=int(X.shape[1]),
                         n_flows=int(len(y)), **rec))
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "processed/ceilings.csv", index=False)
    print(S.to_string(index=False, float_format=lambda v: "%.4f" % v))

    pf = pd.DataFrame(dict(file=files, y=y, atype=enc["Attack Type"].to_numpy(),
                           mixed_native=masks["native_content"],
                           mixed_shared=masks["shared18"]))
    per_file = pf.groupby("file").agg(
        n=("y", "size"), attack_share=("y", "mean"),
        attack_type=("atype", lambda s: s[s != "Benign"].mode().iat[0]
                     if (s != "Benign").any() else "none"),
        conflicting_native=("mixed_native", "mean"),
        conflicting_shared=("mixed_shared", "mean"),
        benign_conflicting_native=("mixed_native", lambda m: float(
            m[pf.loc[m.index, "y"] == 0].mean()) if (pf.loc[m.index, "y"] == 0).any()
            else float("nan")))
    per_file["site"] = np.where(per_file.index <= 10, 1, 2)
    per_file.to_csv(OUT / "processed/per_file.csv")
    print(per_file.to_string(float_format=lambda v: "%.3f" % v))

    # pairing: benign-labelled copies against attack-labelled copies of the
    # same record in other files (the counts turned out to match record by record)
    k = keys(content)
    d0 = pd.DataFrame(dict(k=k, y=y, f=files))
    ben = d0[d0.y == 0].groupby(["k", "f"]).size().rename("benign").reset_index()
    att = d0[d0.y == 1].groupby(["k", "f"]).size().rename("attack").reset_index()
    pair = ben.merge(att, on="k", suffixes=("_b", "_a"))
    pair = pair[pair.f_b != pair.f_a]
    by_files = (pair.groupby(["f_b", "f_a"])
                .agg(records=("k", "nunique"), benign_flows=("benign", "sum"),
                     attack_flows=("attack", "sum"),
                     equal_counts=("k", lambda s: int((pair.loc[s.index, "benign"]
                                                        == pair.loc[s.index, "attack"]).sum())),
                     within_one=("k", lambda s: int(((pair.loc[s.index, "benign"]
                                                      - pair.loc[s.index, "attack"]).abs() <= 1).sum())))
                .reset_index().sort_values("benign_flows", ascending=False))
    by_files.to_csv(OUT / "processed/pairing_between_files.csv", index=False)
    print(by_files.head(5).to_string(index=False))
    main_pair = by_files.iloc[0]
    n_att_file = int(((files == main_pair.f_a) & (y == 1)).sum())
    twin_att = int(d0[(d0.f == main_pair.f_a) & (d0.y == 1)].k.isin(
        set(d0[(d0.f == main_pair.f_b) & (d0.y == 0)].k)).sum())
    (OUT / "statistics/pairing.json").write_text(json.dumps(dict(
        benign_file=int(main_pair.f_b), attack_file=int(main_pair.f_a),
        records=int(main_pair.records), benign_flows=int(main_pair.benign_flows),
        attack_flows=int(main_pair.attack_flows), equal_counts=int(main_pair.equal_counts),
        within_one=int(main_pair.within_one),
        attack_flows_in_attack_file=n_att_file,
        attack_flows_with_benign_twin=twin_att,
        benign_total=int((y == 0).sum()),
        benign_in_benign_file=int(((files == main_pair.f_b) & (y == 0)).sum())),
        indent=2), encoding="utf-8")

    # the largest conflicting records, native content space
    d = pd.DataFrame(dict(k=k, y=y, atype=enc["Attack Type"].to_numpy(), f=files))
    g = d.groupby("k").y.agg(n1="sum", n="size")
    g = g[(g.n1 > 0) & (g.n1 < g.n)].sort_values("n", ascending=False).head(10)
    top = []
    for kk, r in g.iterrows():
        idx = np.flatnonzero(k == kk)
        rec0 = content.iloc[idx[0]]
        top.append(dict(n=int(r.n), attack=int(r.n1), benign=int(r.n - r.n1),
                        by_file_and_type=json.dumps({f"{a}|{b}": int(c) for (a, b), c in
                                                     d.iloc[idx].groupby(["f", "atype"]).size().items()}),
                        nonzero_fields=json.dumps({c: float(v) for c, v in rec0.items() if v != 0})))
    pd.DataFrame(top).to_csv(OUT / "processed/top_conflicting_records.csv", index=False)
    print(pd.DataFrame(top)[["n", "attack", "benign", "by_file_and_type"]].to_string(index=False))

    (OUT / "statistics/provenance.json").write_text(json.dumps(dict(
        experiment="EXP-057", question="round-2 R1-W1: the BA 0.75 plateau on D_B",
        content_space="Encoded.csv minus Unnamed: 0, Seq, Offset and the three labels",
        ceiling_rule="attack iff n_attack(record)/N_attack > n_benign(record)/N_benign, in sample",
        capture_files="resets of Offset (20)", n_flows=int(len(y)),
        attack_prevalence=float(y.mean())), indent=2), encoding="utf-8")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
