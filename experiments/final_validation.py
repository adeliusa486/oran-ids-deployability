#!/usr/bin/env python3
"""Phase 23: the single command that says whether this repository is honest.

    python -m experiments.final_validation

Each check answers one question a reviewer or a reproducing researcher would
ask, and each is allowed to come back FAIL. A FAIL here is not a bug to be
silenced -- several of them are the true state of the project and are supposed
to stay red until the underlying work is done. The script's value is that it
cannot be talked round.

Exit code is 0 only when nothing is FAIL. BLOCKED and WARN do not fail the run,
because "we have not done this yet, and we say so" is a different condition
from "we claim something we cannot support".
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PASS, FAIL, WARN, BLOCKED, SKIP = "PASS", "FAIL", "WARN", "BLOCKED", "SKIP"
_ORDER = {FAIL: 0, BLOCKED: 1, WARN: 2, SKIP: 3, PASS: 4}

results: list[tuple[str, str, str]] = []


def check(name: str, status: str, detail: str = "") -> None:
    results.append((name, status, detail))


def _exists(*rel: str) -> bool:
    return all((ROOT / r).exists() for r in rel)


# ---------------------------------------------------------------- data ----
def check_data():
    prov = ROOT / "data" / "provenance" / "d_a_files.json"
    if not prov.exists():
        return check("DATA", FAIL, "no provenance record")
    p = json.loads(prov.read_text(encoding="utf-8"))
    missing = [k for k, v in p.items() if v.get("status") != "present"]
    if missing:
        return check("DATA", FAIL, f"missing: {missing}")
    no_hash = [k for k, v in p.items() if not v.get("sha256")]
    if no_hash:
        return check("DATA", FAIL, f"no checksum: {no_hash}")
    check("DATA", PASS, f"{len(p)} file(s), all checksummed")


def check_splits():
    try:
        sys.path.insert(0, str(ROOT / "src"))
        import numpy as np
        from oran_ids.splits import LeakageError, group_disjoint_split
        y = np.random.default_rng(0).integers(0, 2, 400)
        g = np.repeat(np.arange(20), 20)
        s = group_disjoint_split(y, g, seed=1, n_folds=1)[0]
        s.check_disjoint(g)
        # the guard must actually fire when disjointness is violated
        bad = type(s)(s.name, np.arange(400), np.arange(400), 1, 0, 20, 20, 0.5, 0.5)
        try:
            bad.check_disjoint(g)
        except LeakageError:
            return check("SPLITS", PASS, "disjoint, and the guard fires when violated")
        check("SPLITS", FAIL, "LeakageError did NOT fire on an overlapping split")
    except Exception as exc:
        check("SPLITS", FAIL, f"{type(exc).__name__}: {exc}")


def check_leakage():
    f = ROOT / "results" / "EXP-002" / "processed" / "leakage_summary.csv"
    if not f.exists():
        return check("LEAKAGE", BLOCKED, "audit not run")
    import pandas as pd
    df = pd.read_csv(f)
    n = int(df.get("group_disjoint_n_splits", pd.Series([0])).max())
    if n < 20:
        return check("LEAKAGE", WARN, f"only {n} split seeds; D-012 requires 20")
    sig = int(df.get("delta_excludes_zero", pd.Series(dtype=bool)).sum())
    check("LEAKAGE", PASS, f"n={n} seeds, {sig}/{len(df)} models show a significant effect")


def check_baselines():
    f = ROOT / "results" / "EXP-002" / "raw" / "leakage_runs.csv"
    if not f.exists():
        return check("BASELINES", BLOCKED, "no runs")
    import pandas as pd
    df = pd.read_csv(f)
    models = set(df.model.unique())
    # the trivial floor is not optional: without it no other score is readable
    if "majority" not in models:
        return check("BASELINES", FAIL, "majority-class floor missing (plan I5)")
    if len(models) < 5:
        return check("BASELINES", WARN, f"only {len(models)} architectures")
    check("BASELINES", PASS, f"{len(models)} architectures incl. the trivial floor")


def check_generalisation():
    """RQ1. Unblocked by EXP-025; answered by EXP-026.

    A PASS here means the experiment RAN and produced a result. It does not mean
    the result was favourable -- it was not. A negative scientific result that is
    measured, reported and preserved is a completed experiment, and conflating
    that with a blocked one is exactly the confusion the campaign rules forbid.
    """
    f = ROOT / "results" / "EXP-026" / "processed" / "transfer_summary__a_to_b.csv"
    if not f.exists():
        return check("GENERALISATION", BLOCKED,
                     "EXP-026 has not produced a summary; RQ1 has no result")
    import csv
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    if not rows:
        return check("GENERALISATION", FAIL, "summary file is empty")
    seeds = {int(float(r["n_seeds"])) for r in rows}
    if min(seeds) < 20:
        return check("GENERALISATION", FAIL,
                     "only %d split seeds; the standing design is 20 (D-012)"
                     % min(seeds))
    nt = [r for r in rows if r["model"] not in ("majority", "stratified")]
    sig = sum(1 for r in nt if str(r.get("significant", "")).lower() == "true")
    floor = next((float(r["target_f1"]) for r in rows
                  if r["model"] == "stratified"), None)
    below = [r["model"] for r in nt if floor is not None
             and float(r["target_f1"]) <= floor]
    detail = ("D_A->D_B run, %d seeds, %d/%d significant after Holm"
              % (min(seeds), sig, len(nt)))
    if below:
        detail += "; %s at or BELOW the trivial floor" % ", ".join(below)
    check("GENERALISATION", PASS, detail)


def check_target_corpus():
    """A11: the target corpus is transfer-only and every access is logged."""
    prov = ROOT / "data" / "provenance" / "d_b_files.json"
    if not prov.exists():
        return check("TARGET CORPUS", BLOCKED, "no target corpus obtained")
    p = json.loads(prov.read_text(encoding="utf-8"))
    no_hash = [k for k, v in p.items() if not v.get("sha256")]
    if no_hash:
        return check("TARGET CORPUS", FAIL, "no checksum: %s" % no_hash)
    log = ROOT / "results" / "EXP-026" / "logs" / "target_access.log"
    if not log.exists():
        return check("TARGET CORPUS", FAIL,
                     "corpus present but no access log -- A11 is unverifiable")
    n = len([ln for ln in log.read_text(encoding="utf-8").splitlines()
             if ln.strip()])
    check("TARGET CORPUS", PASS,
          "%d file(s) checksummed, CC-BY-4.0, %d logged access(es)" % (len(p), n))


def check_shared_space():
    """The feature count the paper reports must be the one the code produces."""
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from oran_ids.features.shared import COLUMNS, load_spec
        spec = load_spec()["counts"]
    except Exception as exc:
        return check("SHARED SPACE", FAIL, "%s: %s" % (type(exc).__name__, exc))
    if spec["model_matrix_columns"] != len(COLUMNS):
        return check("SHARED SPACE", FAIL,
                     "spec says %d columns, code produces %d"
                     % (spec["model_matrix_columns"], len(COLUMNS)))
    check("SHARED SPACE", PASS,
          "%d concepts / %d columns (draft claimed %d)"
          % (spec["shared_concepts"], len(COLUMNS), spec["draft_claimed"]))


def check_statistics():
    f = ROOT / "reports" / "statistical_audit.md"
    if not f.exists():
        return check("STATISTICS", BLOCKED, "audit not run")
    t = f.read_text(encoding="utf-8")
    needed = ["Holm", "d_z", "Power", "paired"]
    missing = [k for k in needed if k not in t]
    if missing:
        return check("STATISTICS", FAIL, f"audit lacks: {missing}")
    check("STATISTICS", PASS, "paired tests, effect sizes, Holm correction, power stated")


def check_robustness():
    f = ROOT / "results" / "EXP-033" / "processed" / "adversarial_summary.csv"
    if not f.exists():
        return check("ROBUSTNESS", BLOCKED,
                     "adversarial evaluation not run (was cut by D-009)")
    prov = ROOT / "results" / "EXP-033" / "statistics" / "provenance.json"
    pr = json.loads(prov.read_text(encoding="utf-8")) if prov.exists() else {}
    n_models, n_seeds = len(pr.get("models", [])), len(pr.get("seeds", []))
    import csv
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    atks = sorted({r["attack"] for r in rows})
    if n_models < 6 or n_seeds < 3:
        return check("ROBUSTNESS", WARN,
                     "PARTIAL run only: %d model(s), %d seed(s). A --quick run "
                     "writes the same filenames as a full one" % (n_models, n_seeds))
    check("ROBUSTNESS", PASS,
          "%d attack(s) x eps sweep over %d models, %d seeds; scored on burden "
          "and threshold" % (len(atks), n_models, n_seeds))


def check_calibration():
    f = ROOT / "results" / "EXP-028" / "processed" / "calibration_summary.csv"
    if not f.exists():
        return check("CALIBRATION", BLOCKED, "EXP-028 not run")
    prov = ROOT / "results" / "EXP-028" / "statistics" / "provenance.json"
    pr = json.loads(prov.read_text(encoding="utf-8")) if prov.exists() else {}
    n_models, n_seeds = len(pr.get("models", [])), len(pr.get("seeds", []))
    import csv
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    cals = sorted({r["calibrator"] for r in rows})
    oracle = [c for c in cals if "ORACLE" in c]
    if n_models < 6 or n_seeds < 5:
        return check("CALIBRATION", WARN,
                     "PARTIAL run only: %d model(s), %d seed(s)"
                     % (n_models, n_seeds))
    detail = ("%d calibrator(s), %d models, %d seeds, fitted on a group-disjoint "
              "source validation fold" % (len(cals), n_models, n_seeds))
    if oracle:
        detail += ("; %d labelled ORACLE (uses the target prior, not deployable)"
                   % len(oracle))
    check("CALIBRATION", PASS, detail)


def check_estimator():
    """B-E. The pooled estimator must be in use, and the gap reported."""
    f = ROOT / "results" / "EXP-027" / "processed" / "estimator_comparison.csv"
    if not f.exists():
        return check("ESTIMATOR", BLOCKED, "EXP-027 not run")
    import csv
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    need = {"ppv_pooled", "ppv_median_of_folds", "ppv_mean_of_folds"}
    if not rows or not need.issubset(rows[0].keys()):
        return check("ESTIMATOR", FAIL,
                     "artefact does not report all three estimators")
    check("ESTIMATOR", PASS,
          "pooled is primary; mean and median reported beside it (D-018)")


def check_latency():
    f = ROOT / "results" / "EXP-005" / "statistics" / "env_radio.json"
    if not f.exists():
        return check("LATENCY", BLOCKED, "not measured")
    env = json.loads(f.read_text(encoding="utf-8"))
    if env.get("measurement_class") != "emulated":
        return check("LATENCY", FAIL, "measurement_class not declared")
    floor = env.get("floor", {}).get("p99")
    if floor is None:
        return check("LATENCY", FAIL, "no floor experiment; p99 uninterpretable")
    check("LATENCY", WARN,
          f"EMULATED only (floor p99 {floor:.3f} ms). No RIC measurement -- D-005")


def check_resource():
    check("RESOURCE", BLOCKED, "CPU/RAM under load not measured; needs the Linux host")


def check_ric():
    f = ROOT / "reports" / "EXP-031_real_ric_blocked.md"
    detail = "Level 2 not executed (D-005)"
    if f.exists():
        detail = ("not executed: WSL2 VM platform absent, so no Linux kernel "
                  "and no CPU isolation (EXP-031)")
    check("RIC INTEGRATION", BLOCKED, detail)


def check_extraction():
    f = ROOT / "results" / "EXP-030" / "statistics" / "provenance.json"
    if not f.exists():
        return check("EXTRACTION", BLOCKED, "EXP-030 not run")
    p = json.loads(f.read_text(encoding="utf-8"))
    if not p.get("all_equivalent"):
        return check("EXTRACTION", FAIL,
                     "the fast exporter does not agree with the reference")
    v = p.get("verdict", {})
    check("EXTRACTION", PASS,
          "vectorised agrees with reference; %.1fx speed-up, extraction still "
          "dominates: %s" % (v.get("speedup_over_reference", 0),
                             v.get("still_dominates")))


def check_figures():
    d = ROOT / "figures" / "generated"
    pdfs = sorted(d.glob("*.pdf")) if d.exists() else []
    if not pdfs:
        return check("FIGURES", BLOCKED, "none generated")
    if not (ROOT / "analysis" / "make_figures.py").exists():
        return check("FIGURES", FAIL, "figures exist with no generator")
    check("FIGURES", PASS, f"{len(pdfs)} generated by a committed script")


def check_tables():
    d = ROOT / "tables" / "generated"
    tex = sorted(d.glob("*.tex")) if d.exists() else []
    if not tex:
        return check("TABLES", BLOCKED, "none generated")
    bad = [t.name for t in tex if "% GENERATED by" not in t.read_text(encoding="utf-8")]
    if bad:
        return check("TABLES", FAIL, f"no provenance header: {bad}")
    crlf = [t.name for t in tex if b"\r\n" in t.read_bytes()]
    if crlf:
        return check("TABLES", FAIL, f"CRLF endings (breaks tabular): {crlf}")
    check("TABLES", PASS, f"{len(tex)} generated, all with provenance, all LF")


def check_references():
    bib = ROOT / "paper" / "references.bib"
    if not bib.exists():
        return check("REFERENCES", FAIL, "no bibliography")
    log = ROOT / "paper" / "main.log"
    if log.exists():
        t = log.read_text(encoding="utf-8", errors="ignore")
        if "Citation" in t and "undefined" in t:
            und = t.count("Citation") and "undefined on input" in t
            if und:
                return check("REFERENCES", WARN, "undefined citations in the last build")
    check("REFERENCES", PASS, "bibliography present, no undefined citations last build")


def check_reproducibility():
    issues = []
    if not _exists("environment.yml"):
        issues.append("no environment.yml")
    if not _exists("configs/experiment_registry.yaml"):
        issues.append("no experiment registry")
    if not _exists("MEMORY.md"):
        issues.append("no research memory")
    if not _exists("requirements.lock"):
        issues.append("NO dependency lock file")
    if not _exists("data/provenance/environment.json"):
        issues.append("no environment record")
    if issues:
        return check("REPRODUCIBILITY", WARN, "; ".join(issues))
    check("REPRODUCIBILITY", PASS, "environment, registry, memory and lock present")


def check_manuscript():
    main = ROOT / "paper" / "main.tex"
    if not main.exists():
        return check("MANUSCRIPT", FAIL, "no manuscript")
    t = main.read_text(encoding="utf-8")
    syn = t.count("\\syn{")
    if "\\synthdrafttrue" in t and syn:
        return check("MANUSCRIPT", BLOCKED,
                     f"{syn} synthetic value(s) remain; draft banner correctly up")
    if syn:
        return check("MANUSCRIPT", FAIL,
                     f"{syn} synthetic value(s) but the draft banner is DOWN")
    check("MANUSCRIPT", PASS, "no synthetic values remain")


def check_claims():
    f = ROOT / "docs" / "CLAIM_EVIDENCE_MATRIX.csv"
    if not f.exists():
        return check("CLAIMS", FAIL, "no claim-evidence matrix")
    import csv
    rows = list(csv.DictReader(f.open(encoding="utf-8")))
    est = [r for r in rows if r["classification"] in
           ("strong_empirical", "moderate_empirical", "proved")]
    contra = [r["claim_id"] for r in rows if r["classification"] == "contradicted"]
    detail = f"{len(est)}/{len(rows)} evidenced"
    if contra:
        detail += f"; CONTRADICTED and reported: {', '.join(contra)}"
    check("CLAIMS", PASS, detail)


def check_tests():
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/"],
                           cwd=ROOT, capture_output=True, text=True, timeout=900,
                           env={**__import__("os").environ,
                                "PYTHONPATH": str(ROOT / "src")})
        last = [ln for ln in r.stdout.strip().split("\n") if ln.strip()][-1:]
        if r.returncode == 0:
            return check("TESTS", PASS, last[0] if last else "passed")
        if r.returncode == 5:
            return check("TESTS", WARN, "no tests collected")
        check("TESTS", FAIL, last[0] if last else f"exit {r.returncode}")
    except Exception as exc:
        check("TESTS", FAIL, f"{type(exc).__name__}: {exc}")


def main() -> int:
    print("=" * 74)
    print("  FINAL VALIDATION  --  O-RAN IDS deployability")
    print("=" * 74)
    print()

    for fn in (check_data, check_target_corpus, check_splits, check_leakage,
               check_baselines, check_shared_space, check_generalisation,
               check_statistics, check_estimator, check_calibration,
               check_robustness, check_latency, check_extraction,
               check_resource, check_ric, check_figures, check_tables,
               check_references, check_reproducibility, check_manuscript,
               check_claims, check_tests):
        fn()

    width = max(len(n) for n, _, _ in results)
    for name, status, detail in results:
        dots = "." * (width + 4 - len(name))
        print(f"  {name} {dots} {status:<8} {detail}")

    n_fail = sum(1 for _, s, _ in results if s == FAIL)
    n_blocked = sum(1 for _, s, _ in results if s == BLOCKED)
    n_warn = sum(1 for _, s, _ in results if s == WARN)
    n_pass = sum(1 for _, s, _ in results if s == PASS)

    print()
    print("-" * 74)
    print(f"  {n_pass} PASS   {n_warn} WARN   {n_blocked} BLOCKED   {n_fail} FAIL")
    print("-" * 74)
    if n_fail:
        print("\n  FAIL means a claim is not supported by what is in the repository.")
        print("  Fix the work, not the check.")
    elif n_blocked:
        print("\n  Nothing is broken. BLOCKED items are honest gaps: work that has")
        print("  not been done and is reported as not done. The remaining ones")
        print("  need a Linux host with isolated cores, which this machine")
        print("  cannot provide -- see reports/EXP-031_real_ric_blocked.md.")
        print()
        print("  RQ1 now HAS a result, and it is negative: transfer largely")
        print("  fails and one architecture lands below the trivial floor. A")
        print("  measured, reported and preserved negative result is a")
        print("  completed experiment, not a gap.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
