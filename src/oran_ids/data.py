"""Corpus loaders for D_A, with the policies EXP-001 said were mandatory.

Three things this module refuses to do silently, because each is a documented
way a NIDS result becomes unpublishable:

1. **Deduplicate without reporting.** ``Network_Dataset.csv`` has 4.85% exact
   duplicate rows and 6.94% duplicate Zeek ``uid``s (B-007). Duplicates that
   straddle a split put the same connection in train and test. The dedup rate is
   returned, not hidden.
2. **Use an identifier as a feature.** Source and destination IP are the group
   key and the target host; feeding them to a classifier lets it memorise
   "attacks come from 172.31.0.134". They are dropped from every feature set.
3. **Map a label it does not recognise.** An unmapped label raises rather than
   becoming a silent ``other`` (B-008).

Port numbers are kept in the full feature set and excluded from the
``transferable`` set. They are informative in-distribution and a documented
transfer hazard: Hakim et al. (2026) report their most influential port feature
appearing in source-domain attacks at 96-435x the target-domain rate.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RAW_DA = Path("data/raw/d_a")
RAW_DB = Path("data/raw/d_b")
TARGET_ACCESS_LOG = Path("results/EXP-026/logs/target_access.log")
LABEL_MAP_PATH = Path("configs/labels/canonical_map.yaml")

# Columns that identify a record or its host. Never features.
NETWORK_IDENTITY = ("uid", "src_ip", "dst_ip")
# Columns that are the label, or leak it directly.
NETWORK_LABELS = ("attack_category", "attack_type", "traffic_type")
# Deployment-specific by construction; excluded from the transferable set.
NETWORK_PORTS = ("src_port", "dst_port")
# Low-cardinality categoricals worth one-hot encoding. `history` is excluded:
# it is a Zeek-specific state string with hundreds of values and no counterpart
# in any other exporter, so it cannot appear in a shared feature space.
NETWORK_CATEGORICAL = ("proto", "service", "conn_state")

RADIO_IDENTITY = ("rnti", "cellid", "ue_id")
RADIO_LABELS = ("traffic_type", "attack_category", "attack_subcategory")

SESSION_GAP_S = 300.0   # EXP-001: recovers 30 runs, 100% label-pure


@dataclass
class Corpus:
    """A loaded corpus, ready to split. ``X`` is numeric and NaN-free."""

    name: str
    X: pd.DataFrame
    y: np.ndarray                 # binary: 1 attack, 0 benign
    category: np.ndarray          # canonical multi-class label
    groups: np.ndarray            # split-grouping key
    group_name: str
    provenance: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.X)

    def summary(self) -> dict:
        return {
            "corpus": self.name,
            "n_rows": int(len(self.X)),
            "n_features": int(self.X.shape[1]),
            "attack_prevalence_pct": round(float(self.y.mean() * 100), 2),
            "group_key": self.group_name,
            "n_groups": int(len(np.unique(self.groups))),
            "categories": {k: int(v) for k, v in
                           pd.Series(self.category).value_counts().items()},
            **self.provenance,
        }


def load_label_map() -> dict:
    return yaml.safe_load(LABEL_MAP_PATH.read_text(encoding="utf-8"))


def _apply_canonical(series: pd.Series, mapping: dict, where: str) -> pd.Series:
    out = series.map(mapping)
    if out.isna().any():
        unmapped = sorted(series[out.isna()].unique())
        raise ValueError(
            f"{where}: unmapped label(s) {unmapped}. Add them to "
            f"{LABEL_MAP_PATH} deliberately -- an unmapped label must never "
            f"become a silent 'other'."
        )
    return out


def load_network(path: Path | None = None, *, dedup: bool = True,
                 feature_set: str = "full") -> Corpus:
    """Load the CU flow records.

    ``feature_set``:
      ``full``          every numeric feature plus one-hot categoricals and ports
      ``transferable``  drops ports, which are a documented transfer hazard
    """
    path = path or (RAW_DA / "Network_Dataset.csv")
    df = pd.read_csv(path, low_memory=False)
    n_raw = len(df)

    prov = {"source_file": path.name, "n_rows_raw": n_raw}

    if dedup:
        # Exact duplicate rows only.
        #
        # An earlier version also dropped repeated Zeek `uid`s, on the theory
        # that a uid is unique per connection so a repeat meant the summary had
        # concatenated captures without namespacing. Checking rather than
        # assuming showed that is wrong: same-uid rows differ in
        # http_trans_depth, files_total_bytes and is_GET_mthd. They are distinct
        # HTTP transactions inside one TCP connection, produced by the
        # conn.log/http.log/files.log merge. Dropping them discarded 35,916 real
        # observations, 98% of them benign, and pushed apparent attack
        # prevalence from 94.6% to 96.7%.
        #
        # Exact-duplicate removal is safe by comparison: two genuinely distinct
        # connections carry distinct uids, so byte-identical rows (uid included)
        # are merge artefacts.
        #
        # Same-uid rows share an src_ip and therefore land on the same side of
        # any src_ip-grouped split, so they cannot leak across it.
        df = df.drop_duplicates()
        prov.update(
            n_exact_duplicates_removed=int(n_raw - len(df)),
            exact_duplicate_pct=round(100 * (n_raw - len(df)) / n_raw, 3),
            n_multi_transaction_uids_kept=int(df["uid"].duplicated().sum()),
            dedup_policy="drop exact duplicate rows only; repeated uids are "
                         "multi-transaction connections and are KEPT",
        )
    else:
        prov["dedup_policy"] = "NONE -- for the leakage audit only"

    lm = load_label_map()
    category = _apply_canonical(
        df["attack_category"], lm["corpus_d_a"]["network_layer"]["map"], "D_A network")
    y = df["traffic_type"].to_numpy(dtype=np.int8)
    groups = df["src_ip"].to_numpy()

    drop = set(NETWORK_IDENTITY) | set(NETWORK_LABELS) | {"history"}
    if feature_set == "transferable":
        drop |= set(NETWORK_PORTS)
    elif feature_set != "full":
        raise ValueError(f"unknown feature_set {feature_set!r}")

    feat = df.drop(columns=[c for c in drop if c in df.columns])
    cats = [c for c in NETWORK_CATEGORICAL if c in feat.columns]
    X = pd.get_dummies(feat, columns=cats, dummy_na=False, dtype=np.int8)
    X = X.apply(pd.to_numeric, errors="coerce").astype(np.float32)
    n_nan = int(X.isna().sum().sum())
    X = X.fillna(0.0)

    prov.update(n_rows_used=int(len(X)), feature_set=feature_set,
                n_nan_filled=n_nan, ports_included=feature_set == "full")
    return Corpus("d_a_network", X.reset_index(drop=True), y,
                  category.to_numpy(), groups, "src_ip", prov)


def load_radio(path: Path | None = None, *, window: bool = True) -> Corpus:
    """Load the DU radio telemetry, grouped into runs recovered from the clock.

    With ``window=True`` the 1 Hz records are aggregated into the 16-record
    windows declared in ``configs/base.yaml`` (16 seconds at the measured
    sampling rate). Cumulative byte counters are first-differenced before
    aggregation, for the reason given in ``features/crosslayer.py``: a
    monotonically rising counter aggregated as a mean encodes absolute capture
    time, which is a run fingerprint.
    """
    path = path or (RAW_DA / "Lower_Layer_Data.db")
    con = sqlite3.connect(path)
    df = pd.read_sql("SELECT * FROM lower_layer_data", con)
    con.close()

    prov = {"source_file": path.name, "n_records_raw": int(len(df))}

    df["ts"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.sort_values("ts").reset_index(drop=True)
    gaps = df["ts"].diff().dt.total_seconds()
    df["session"] = (gaps > SESSION_GAP_S).cumsum()

    purity = df.groupby("session")["attack_category"].nunique()
    prov.update(n_sessions=int(df["session"].nunique()),
                sessions_label_pure=int((purity == 1).sum()),
                session_gap_s=SESSION_GAP_S)

    # Per-UE differencing of cumulative counters.
    df = df.sort_values(["ue_id", "ts"])
    for col in ("dlBytes", "ulBytes"):
        dt = df.groupby("ue_id")["timestamp"].diff() / 1000.0
        delta = df.groupby("ue_id")[col].diff().clip(lower=0)
        df[f"{col}_rate"] = (delta / dt).replace([np.inf, -np.inf], np.nan)
    df = df.sort_values("ts").reset_index(drop=True)

    lm = load_label_map()
    numeric = [c for c in df.columns
               if c not in set(RADIO_IDENTITY) | set(RADIO_LABELS)
               | {"ts", "timestamp", "session", "pmi", "in_sync", "dlBytes", "ulBytes"}
               and pd.api.types.is_numeric_dtype(df[c])]

    if not window:
        category = _apply_canonical(
            df["attack_category"], lm["corpus_d_a"]["radio_layer"]["map"], "D_A radio")
        X = df[numeric].astype(np.float32).fillna(0.0)
        prov.update(n_rows_used=int(len(X)), windowed=False)
        return Corpus("d_a_radio", X.reset_index(drop=True),
                      df["traffic_type"].to_numpy(np.int8),
                      category.to_numpy(), df["session"].to_numpy(), "session", prov)

    # 16-record non-overlapping windows within (session, ue_id).
    df["_w"] = df.groupby(["session", "ue_id"]).cumcount() // 16
    grp = df.groupby(["session", "ue_id", "_w"])
    keep = grp["ts"].transform("size") == 16
    n_dropped = int((~keep).sum())
    dfw = df[keep]

    agg = dfw.groupby(["session", "ue_id", "_w"])
    feats = agg[numeric].agg(["mean", "std"])
    feats.columns = [f"{a}_{b}" for a, b in feats.columns]
    meta = agg.agg(category_raw=("attack_category", lambda s: s.mode().iat[0]),
                   y=("traffic_type", lambda s: int(s.max())))
    out = feats.join(meta).reset_index()

    category = _apply_canonical(
        out["category_raw"], lm["corpus_d_a"]["radio_layer"]["map"], "D_A radio window")
    X = out[[c for c in out.columns if c.endswith(("_mean", "_std"))]]
    X = X.astype(np.float32).fillna(0.0)

    prov.update(n_rows_used=int(len(out)), windowed=True, window_records=16,
                window_seconds=16, records_dropped_short=n_dropped,
                drop_rate_pct=round(100 * n_dropped / len(df), 2))
    return Corpus("d_a_radio_w16", X.reset_index(drop=True),
                  out["y"].to_numpy(np.int8), category.to_numpy(),
                  out["session"].to_numpy(), "session", prov)


def radio_session_timeline(path: Path | None = None) -> pd.DataFrame:
    """One row per radio capture session, in time order, with its category.

    Uses the session rule of ``load_radio`` (a gap over ``SESSION_GAP_S``
    starts a new session), so session ids match ``load_radio().groups``.
    Round-2 review R1-W6 asked whether time-ordered splits hold out whole
    attack categories. This table answers it: the capture ran the benign
    sessions first, then each attack category in a block.
    """
    path = path or (RAW_DA / "Lower_Layer_Data.db")
    con = sqlite3.connect(path)
    df = pd.read_sql("SELECT timestamp, ue_id, attack_category, traffic_type "
                     "FROM lower_layer_data", con)
    con.close()
    df["ts"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.sort_values("ts").reset_index(drop=True)
    df["session"] = (df["ts"].diff().dt.total_seconds() > SESSION_GAP_S).cumsum()
    lm = load_label_map()
    df["category"] = _apply_canonical(
        df["attack_category"], lm["corpus_d_a"]["radio_layer"]["map"],
        "D_A radio (timeline)").to_numpy()
    out = df.groupby("session").agg(
        start=("ts", "min"), end=("ts", "max"), n_records=("ts", "size"),
        n_ues=("ue_id", "nunique"), n_categories=("category", "nunique"),
        category=("category", "first"),
        attack_share=("traffic_type", "mean")).reset_index()
    out["duration_min"] = (out.end - out.start).dt.total_seconds() / 60.0
    out["day"] = (out.start - out.start.min()).dt.total_seconds() / 86400.0
    return out


def load_radio_sequences(path: Path | None = None):
    """The windows of ``load_radio(window=True)`` as raw 16-step sequences.

    EXP-050 (review R4) needs a sequence model over KPM windows. It must see the
    SAME windows as every other radio-layer model, in the same order with the
    same labels, or its scores are not comparable. This repeats
    ``load_radio``'s preprocessing line for line and stops before the mean/std
    aggregation. Callers assert equality against ``load_radio()``.

    Returns ``(seq, y, category, session, feature_names)`` with ``seq`` of shape
    ``(n_windows, 16, n_features)``, NaN filled with 0 as in ``load_radio``.
    """
    path = path or (RAW_DA / "Lower_Layer_Data.db")
    con = sqlite3.connect(path)
    df = pd.read_sql("SELECT * FROM lower_layer_data", con)
    con.close()

    df["ts"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.sort_values("ts").reset_index(drop=True)
    gaps = df["ts"].diff().dt.total_seconds()
    df["session"] = (gaps > SESSION_GAP_S).cumsum()

    df = df.sort_values(["ue_id", "ts"])
    for col in ("dlBytes", "ulBytes"):
        dt = df.groupby("ue_id")["timestamp"].diff() / 1000.0
        delta = df.groupby("ue_id")[col].diff().clip(lower=0)
        df[f"{col}_rate"] = (delta / dt).replace([np.inf, -np.inf], np.nan)
    df = df.sort_values("ts").reset_index(drop=True)

    lm = load_label_map()
    numeric = [c for c in df.columns
               if c not in set(RADIO_IDENTITY) | set(RADIO_LABELS)
               | {"ts", "timestamp", "session", "pmi", "in_sync", "dlBytes", "ulBytes"}
               and pd.api.types.is_numeric_dtype(df[c])]

    df["_w"] = df.groupby(["session", "ue_id"]).cumcount() // 16
    keep = df.groupby(["session", "ue_id", "_w"])["ts"].transform("size") == 16
    dfw = df[keep].sort_values(["session", "ue_id", "_w", "ts"], kind="mergesort")

    seq = (dfw[numeric].astype(np.float32).fillna(0.0).to_numpy()
           .reshape(-1, 16, len(numeric)))
    meta = dfw.groupby(["session", "ue_id", "_w"]).agg(
        category_raw=("attack_category", lambda s: s.mode().iat[0]),
        y=("traffic_type", lambda s: int(s.max()))).reset_index()
    category = _apply_canonical(
        meta["category_raw"], lm["corpus_d_a"]["radio_layer"]["map"],
        "D_A radio window (sequences)")
    return (seq, meta["y"].to_numpy(np.int8), category.to_numpy(),
            meta["session"].to_numpy(), list(numeric))


# ---------------------------------------------------------------------------
# The shared feature space, and the target corpus.
# ---------------------------------------------------------------------------

def _log_target_access(what: str) -> None:
    """A11: every read of the target corpus is logged, with a timestamp.

    The non-negotiable is not "do not read D_B" -- it must be read to be
    evaluated on. It is that no source-side choice may be made *after* looking at
    it. An append-only log is what makes that auditable after the fact rather
    than a promise in a methods section.
    """
    import datetime as _dt
    TARGET_ACCESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with TARGET_ACCESS_LOG.open("a", encoding="utf-8") as fh:
        stamp = _dt.datetime.now().isoformat(timespec="seconds")
        print(stamp, what, sep="\t", file=fh)


def load_network_shared(path: Path | None = None, *, dedup: bool = True,
                        nrows: int | None = None) -> Corpus:
    """D_A CU flow records, projected onto the D_A/D_B shared space.

    This is the SOURCE side of the transfer experiment. It deliberately does not
    reuse ``load_network``'s full feature set: a transfer gap measured between a
    48-column source model and an 18-column target space would be measuring the
    projection, not the deployment.
    """
    from .features import shared as _sh

    path = path or (RAW_DA / "Network_Dataset.csv")
    df = pd.read_csv(path, low_memory=False, nrows=nrows)
    n_raw = len(df)
    prov = {"source_file": path.name, "n_rows_raw": n_raw,
            "space": "shared_d_a_d_b", "spec": str(_sh.SPEC_PATH)}

    if dedup:
        df = df.drop_duplicates()
        prov.update(n_exact_duplicates_removed=int(n_raw - len(df)),
                    dedup_policy="drop exact duplicate rows only (B-007)")

    lm = load_label_map()
    category = _apply_canonical(
        df["attack_category"], lm["corpus_d_a"]["network_layer"]["map"],
        "D_A network (shared space)")
    y = df["traffic_type"].to_numpy(dtype=np.int8)
    groups = df["src_ip"].to_numpy()
    X = _sh.from_d_a(df)

    prov.update(n_rows_used=int(len(X)), n_features=int(X.shape[1]))
    return Corpus("d_a_network_shared", X, y, category.to_numpy(),
                  groups, "src_ip", prov)


def d_b_capture_files(offset) -> np.ndarray:
    """1-based capture-file id for each 5G-NIDD record, in file order.

    Argus's ``Offset`` is a byte offset inside one output file, so it falls at
    every file boundary of the concatenated ``Combined.csv``. The file has 20
    such segments: two passes over the same ten captures, one per base station
    (round-2 review, EXP-054/055).
    """
    offset = np.asarray(offset)
    return np.cumsum(np.r_[True, offset[1:] < offset[:-1]]).astype(int)


def load_target_d_b(path: Path | None = None, *, nrows: int | None = None,
                    reason: str = "unspecified",
                    groups: str = "none") -> Corpus:
    """D_B = 5G-NIDD, the independent target corpus. TRANSFER-ONLY.

    Never split, never trained on, never used to fit a scaler or pick a
    threshold. It carries no IP addresses and no ports, so no group key exists
    and none is needed.

    Every call appends to ``results/EXP-026/logs/target_access.log``.
    """
    from .features import shared as _sh

    path = path or (RAW_DB / "Combined.csv")
    _log_target_access(f"load_target_d_b(nrows={nrows}) reason={reason}")

    df = pd.read_csv(path, low_memory=False, nrows=nrows)
    n_raw = len(df)
    prov = {"source_file": path.name, "n_rows_raw": n_raw,
            "space": "shared_d_a_d_b", "role": "transfer_only",
            "licence": "CC-BY-4.0",
            "obtained_from": "https://etsin.fairdata.fi/dataset/"
                             "9d13ef28-2ca7-44b0-9950-225359afac65"}

    if groups == "capture_file":
        # computed on the raw row order, before deduplication
        df["_capture_file"] = d_b_capture_files(df["Offset"].to_numpy())
        # EXP-057: 281,525 benign-labelled records are exact copies of records
        # labelled UDPFlood elsewhere in the corpus. Mark every benign flow
        # whose full record (all fields but the row index, Seq, Offset and the
        # labels) also occurs with an attack label, so evaluations can be
        # reported with and without them. The mark is a group suffix, never a
        # feature.
        content = [c for c in df.columns if c not in
                   ("Unnamed: 0", "Seq", "Offset", "Label", "Attack Type",
                    "Attack Tool", "_capture_file")]
        h = pd.util.hash_pandas_object(df[content], index=False).to_numpy()
        is_att = (df["Label"] != "Benign").to_numpy()
        att_keys = set(h[is_att])
        conflict = (~is_att) & np.fromiter((k in att_keys for k in h), bool, len(h))
        df["_capture_file"] = [f"{f}|c" if c else str(f)
                               for f, c in zip(df["_capture_file"], conflict)]
        prov["n_benign_with_attack_twin"] = int(conflict.sum())
    elif groups != "none":
        raise ValueError(f"unknown groups {groups!r}")
    # exact duplicates of the published columns only, so the helper column
    # never changes which rows survive (the one duplicate is row 0 of each
    # base station's file, where the row index restarts)
    df = df.drop_duplicates(subset=[c for c in df.columns if c != "_capture_file"])
    prov["n_exact_duplicates_removed"] = int(n_raw - len(df))

    lm = load_label_map()["corpus_d_b"]
    y = _apply_canonical(df[lm["binary_column"]], lm["binary_map"],
                         "D_B binary").to_numpy(dtype=np.int8)
    category = _apply_canonical(df[lm["category_column"]], lm["map"],
                                "D_B category").to_numpy()
    X = _sh.from_d_b(df)

    if groups == "capture_file":
        g = df["_capture_file"].to_numpy()
        prov.update(n_rows_used=int(len(X)), n_features=int(X.shape[1]),
                    group_key="capture_file (resets of Argus Offset, 20 files)",
                    n_groups=int(len(np.unique(g))))
        return Corpus("d_b_5gnidd_shared", X, y, category, g, "capture_file", prov)
    # D_B carries no address or port. Without groups="capture_file" it is
    # evaluated whole and no group key is used.
    g = np.zeros(len(X), dtype=np.int8)
    prov.update(n_rows_used=int(len(X)), n_features=int(X.shape[1]),
                group_key="none (evaluated whole)")
    return Corpus("d_b_5gnidd_shared", X, y, category, g,
                  "none", prov)


RAW_DC = Path("data/raw/d_c")
D_C_FILES = {"004-syn-flood.csv": "syn_flood", "005-icmp-flood.csv": "icmp_flood",
             "003a-pfcp.csv": "pfcp_deletion"}
D_C_LABELS = {"malicious": 1, "benign": 0, "background": 0}


def load_target_d_c(*, reason: str = "unspecified", groups: str = "capture_file",
                    background: bool = True) -> Corpus:
    """D_C = the DLTeamTUC 5G datasets (Nugraha et al., IEEE CSR 2025): NFStream
    flow records from an Open5GS 5G core in Docker. A third corpus, a third
    flow exporter, a third site (EXP-058). Only the three flow-level files are
    used; the others hold per-interval NAS message counts, not flows.

    Labels: "malicious" is attack; "benign" (user traffic) and "background"
    (the core's own signalling) are benign. ``background=False`` drops the
    background flows. Categories name the attack of each file (syn_flood,
    icmp_flood, pfcp_deletion), and "benign" / "background" otherwise. The
    group key is the capture file. Every call is logged like D_B.
    """
    from .features import shared as _sh

    _log_target_access(f"load_target_d_c(background={background}) reason={reason}")
    frames = []
    for name, attack in D_C_FILES.items():
        df = pd.read_csv(RAW_DC / name, low_memory=False)
        unknown = set(df["label"].unique()) - set(D_C_LABELS)
        if unknown:
            raise ValueError(f"D_C {name}: unmapped label(s) {sorted(unknown)}")
        df["_file"] = name
        df["_category"] = np.where(df["label"] == "malicious", attack, df["label"])
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    n_raw = len(df)
    if not background:
        df = df[df["label"] != "background"].reset_index(drop=True)
    y = df["label"].map(D_C_LABELS).to_numpy(np.int8)
    X = _sh.from_d_c(df)
    g = (df["_file"].to_numpy() if groups == "capture_file"
         else np.zeros(len(df), dtype=np.int8))
    prov = {"source_files": list(D_C_FILES), "n_rows_raw": n_raw,
            "n_rows_used": int(len(X)), "n_features": int(X.shape[1]),
            "background_included": background, "exporter": "NFStream",
            "byte_accounting": "link layer; Ethernet and GTP-U overhead removed per packet",
            "group_key": groups, "n_groups": int(len(np.unique(g)))}
    return Corpus("d_c_5gdatasets_shared", X, y, df["_category"].to_numpy(), g,
                  groups, prov)


__all__ = ["Corpus", "load_network", "load_radio", "load_label_map", "load_target_d_c",
           "load_network_shared", "load_target_d_b", "radio_session_timeline",
           "d_b_capture_files"]
