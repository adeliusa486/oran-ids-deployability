#!/usr/bin/env python3
"""One entry point for reproducing the paper. See REPRODUCE.md.

  python scripts/reproduce.py check          environment, packages and data checksums
  python scripts/reproduce.py paper          regenerate every statistic, macro, table
                                             and figure from the committed results/,
                                             build paper/main.pdf, and verify that
                                             the regenerated numbers and tables equal
                                             the ones shipped (minutes, no raw data)
  python scripts/reproduce.py list           every experiment and its exact command
  python scripts/reproduce.py experiment EXP-055   re-run one experiment from raw data
  python scripts/reproduce.py all            re-run the experiments the paper uses
                                             (raw data needed; many hours)
  python scripts/reproduce.py freeze         (maintainers) record the expected outputs

"Equal" ignores LaTeX comment lines, which carry the generation date and commit.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
EXPECTED = ROOT / "reproducibility" / "expected_outputs.json"
GENERATED = sorted((ROOT / "tables" / "generated").glob("*.tex"))

# Experiments behind the current manuscript, in the order they may be re-run.
# Each is (id, what it answers, command, needs raw data, approximate time on the
# authors' 14-core laptop, table/section it feeds).
EXPERIMENTS = [
    ("EXP-041", "cross-corpus transfer D_A->D_B (and reverse)",
     [["experiments/run_transfer_v2.py", "--exp", "EXP-041", "--direction", "a_to_b", "--sweeps", "--reliability"],
      ["experiments/run_transfer_v2.py", "--exp", "EXP-041", "--direction", "b_to_a"]],
     True, "2-4 h", "VI-D, Tables of transfer, per-category, pooled"),
    ("EXP-042", "random vs run-disjoint vs category-stratified; 1-NN probe",
     [["experiments/run_leakage_v2.py"]], True, "20 min", "VI-A, Table of protocol sensitivity"),
    ("EXP-043", "per-stage latency, ONNX Runtime; extraction on real captures",
     [["experiments/run_latency_v2.py"], ["experiments/run_extraction_real.py"]],
     True, "40 min (run alone, quiet machine)", "VI-G, latency table"),
    ("EXP-044", "calibration and label-free prior estimation",
     [["experiments/run_calibration.py", "--estimate-prior", "--out", "results/EXP-044"]],
     True, "1-2 h", "VI-F, calibration table"),
    ("EXP-045", "domain classifier, exporter-robust subset",
     [["experiments/run_exporter_sensitivity.py"],
      ["experiments/run_transfer_v2.py", "--exp", "EXP-045", "--features", "robust", "--sweeps"]],
     True, "2-3 h", "VI-E, arms table"),
    ("EXP-046", "radio alert burden from pooled counts",
     [["experiments/run_alert_burden_v2.py"]], True, "15 min", "VI-F, pooled table"),
    ("EXP-047", "cost of the shared space on D_A",
     [["experiments/run_transfer_v2.py", "--exp", "EXP-047", "--features", "transferable", "--source-only"]],
     True, "1-2 h", "VI-E, harmonisation table"),
    ("EXP-048", "benign-only novelty detectors",
     [["experiments/run_unsupervised.py"]], True, "30 min", "VI-E, arms table"),
    ("EXP-049", "CORAL adaptation",
     [["experiments/run_transfer_v2.py", "--exp", "EXP-049", "--adapt", "coral"]],
     True, "2 h", "VI-E, arms table"),
    ("EXP-050", "GRU and 1D-CNN on raw KPM windows (needs the [seq] extra: torch)",
     [["experiments/run_sequence_model.py"]], True, "2 h", "VI-A, sequence table"),
    ("EXP-053", "time order with category coverage; held-out benign sessions",
     [["experiments/run_drift_v3.py", "--reps", "50"]], True, "15 min", "VI-B, two tables"),
    ("EXP-054", "in-target references on D_B",
     [["experiments/run_target_reference.py", "--seeds", "3", "--native-seeds", "2"]],
     True, "1 h", "VI-C, target reference table"),
    ("EXP-055", "the 5G-NIDD authors' pipeline down the ladder",
     [["experiments/run_published_pipeline.py", "--repeats", "2"]],
     True, "3 h", "VI-C, ladder table; VII-B"),
    ("EXP-056", "per-cluster counts for the cluster bootstrap",
     [["experiments/run_alert_burden_v2.py", "--out", "results/EXP-056", "--by-session"],
      ["experiments/run_transfer_v2.py", "--exp", "EXP-056", "--direction", "a_to_b", "--sweeps",
       "--group-counts", "--seeds", "10"]],
     True, "2 h", "VI-F, pooled table; VI-D clean target"),
    ("EXP-057", "5G-NIDD label-conflict audit",
     [["analysis/label_conflict_audit.py"]], True, "5 min", "VI-C, conflict table"),
    ("diag", "Platt inversion diagnosis (EXP-044 seed 110)",
     [["analysis/platt_diagnosis.py"]], True, "2 min", "VI-F"),
]

PACKAGES = ["numpy", "pandas", "scipy", "sklearn", "xgboost", "matplotlib", "yaml",
            "onnxruntime", "skl2onnx", "statsmodels", "pyarrow"]


def _content_hash(path: Path) -> str:
    """SHA-256 of a generated LaTeX file without its comment lines."""
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines()
             if not ln.lstrip().startswith("%")]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args: list[str]) -> None:
    print("  $ python " + " ".join(args), flush=True)
    t0 = time.time()
    subprocess.run([PY, *args], cwd=ROOT, check=True)
    print(f"    done in {time.time() - t0:.0f} s", flush=True)


def cmd_check() -> int:
    ok = True
    print(f"python {sys.version.split()[0]} ({PY})")
    for p in PACKAGES:
        try:
            m = importlib.import_module(p)
            print(f"  {p:<12} {getattr(m, '__version__', '?')}")
        except ImportError:
            print(f"  {p:<12} MISSING")
            ok = False
    tex = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True)
    print("  pdflatex    ", (tex.stdout.splitlines() or ["MISSING"])[0])
    for corpus in ("d_a", "d_b"):
        manifest = json.loads((ROOT / "data/provenance" / f"{corpus}_files.json").read_text())
        for name, info in manifest.items():
            path = ROOT / "data/raw" / corpus / name
            want = info.get("sha256") if isinstance(info, dict) else info
            if not path.exists():
                print(f"  data {corpus}/{name}: not present (needed only to re-run experiments)")
                continue
            got = _file_sha256(path)
            good = want is None or got == want
            ok &= good
            print(f"  data {corpus}/{name}: {'OK' if good else 'CHECKSUM MISMATCH'}")
    return 0 if ok else 1


def _regenerate() -> None:
    run(["analysis/revision_stats.py"])
    run(["analysis/make_numbers.py"])
    run(["analysis/make_tables_v2.py"])
    run(["analysis/make_figures_v2.py"])


def cmd_paper() -> int:
    if not EXPECTED.exists():
        print("reproducibility/expected_outputs.json is missing")
        return 1
    expected = json.loads(EXPECTED.read_text())
    print("1/3 regenerating statistics, macros, tables and figures from results/")
    _regenerate()
    print("2/3 comparing regenerated numbers and tables with the shipped ones")
    bad = []
    for name, digest in expected.items():
        path = ROOT / name
        if not path.exists() or _content_hash(path) != digest:
            bad.append(name)
    for name in bad:
        print(f"  DIFFERS: {name}")
    print(f"  {len(expected) - len(bad)} of {len(expected)} generated files identical")
    print("3/3 building the paper and running the guards")
    run(["scripts/build_paper.py"])
    run(["scripts/check_withdrawn_claims.py"])
    run(["scripts/check_no_placeholders.py", "paper/main.tex", "paper/latency_section.tex",
         "paper/predicate_section.tex"])
    print("paper/main.pdf rebuilt." + ("" if not bad else " SOME OUTPUTS DIFFER, see above."))
    return 1 if bad else 0


def cmd_list() -> int:
    for eid, what, cmds, raw, dur, where in EXPERIMENTS:
        print(f"{eid}  {what}\n    feeds: {where}\n    time:  {dur}"
              f"{'   (needs raw data)' if raw else ''}")
        for c in cmds:
            print("    $ python " + " ".join(c))
    return 0


def cmd_experiment(eid: str) -> int:
    for e in EXPERIMENTS:
        if e[0] == eid:
            for c in e[2]:
                run(c)
            print("Now run: python scripts/reproduce.py paper")
            return 0
    print(f"unknown experiment {eid}; see `python scripts/reproduce.py list`")
    return 1


def cmd_all() -> int:
    for e in EXPERIMENTS:
        print(f"== {e[0]}: {e[1]} ({e[4]})")
        for c in e[2]:
            run(c)
    return cmd_paper()


def cmd_freeze() -> int:
    EXPECTED.parent.mkdir(parents=True, exist_ok=True)
    out = {str(p.relative_to(ROOT)).replace("\\", "/"): _content_hash(p) for p in GENERATED}
    EXPECTED.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"recorded {len(out)} generated files in {EXPECTED.relative_to(ROOT)}")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in {"check", "paper", "list", "experiment",
                                                  "all", "freeze"}:
        print(__doc__)
        return 2
    c = sys.argv[1]
    if c == "experiment":
        return cmd_experiment(sys.argv[2] if len(sys.argv) > 2 else "")
    return {"check": cmd_check, "paper": cmd_paper, "list": cmd_list,
            "all": cmd_all, "freeze": cmd_freeze}[c]()


if __name__ == "__main__":
    sys.exit(main())
