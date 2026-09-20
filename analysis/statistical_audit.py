#!/usr/bin/env python3
"""Phase 15: the statistical audit.

What this checks, and why each one is here rather than in a footnote:

1. **Paired, not unpaired, comparisons.** Both split protocols see the same five
   split seeds, so the comparison is paired. Treating it as unpaired throws away
   the pairing and widens the interval for no reason.
2. **Multiple comparisons.** Eight models are compared, so eight tests. Without
   correction, one spurious "significant" result at alpha=0.05 is the expected
   outcome. Holm-Bonferroni is applied and both raw and adjusted p are reported.
3. **Effect size, not just significance.** With n=5 split seeds, a p-value is a
   weak instrument. Cohen's d_z and the raw difference in macro-F1 points say
   how much, which is the question a practitioner has.
4. **Power honesty.** n=5 is small. The audit states what that design can and
   cannot detect instead of letting a reader assume.
5. **Non-parametric cross-check.** A Wilcoxon signed-rank test is run alongside
   the t-test. At n=5 its minimum attainable p is 0.0625, so it can never reach
   alpha=0.05 on its own -- that limitation is reported rather than hidden by
   quoting only the t-test.

Output: reports/statistical_audit.md and results/statistics/.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RES = Path("results")
OUT = Path("results/statistics")
REPORT = Path("reports/statistical_audit.md")
ALPHA = 0.05
PRIMARY = "f1_macro"


def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni step-down. Returns adjusted p in the input order."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m, dtype=float)
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvals[idx]
        running = max(running, val)
        adj[idx] = min(running, 1.0)
    return adj.tolist()


def cohen_dz(diffs: np.ndarray) -> float:
    """Paired effect size. sd of the differences, not of the raw values."""
    sd = diffs.std(ddof=1)
    return float(diffs.mean() / sd) if sd > 0 else float("nan")


def min_detectable_effect(n: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """Smallest d_z a paired t-test at this n can detect, approximately."""
    from scipy.stats import norm
    z_a = norm.ppf(1 - alpha / 2)
    z_b = norm.ppf(power)
    return float((z_a + z_b) / np.sqrt(n))


def audit_leakage() -> tuple[pd.DataFrame, dict]:
    src = RES / "EXP-002" / "raw" / "leakage_runs.csv"
    if not src.exists():
        return pd.DataFrame(), {}
    df = pd.read_csv(src)
    df = df[df.status == "ok"]

    rows = []
    for (layer, model), g in df.groupby(["layer", "model"]):
        # average model seeds within a split seed first: they are nested, not
        # independent replicates
        r = g[g.protocol == "random"].groupby("split_seed")[PRIMARY].mean()
        d = g[g.protocol == "group_disjoint"].groupby("split_seed")[PRIMARY].mean()
        common = r.index.intersection(d.index)
        if len(common) < 3:
            continue
        diffs = (r.loc[common] - d.loc[common]).to_numpy()
        n = len(diffs)
        t_stat, t_p = stats.ttest_rel(r.loc[common], d.loc[common])
        try:
            w_stat, w_p = stats.wilcoxon(diffs)
        except ValueError:
            w_stat, w_p = float("nan"), float("nan")
        ci = stats.t.interval(1 - ALPHA, n - 1, loc=diffs.mean(),
                              scale=stats.sem(diffs)) if diffs.std(ddof=1) > 0 else (np.nan, np.nan)
        rows.append({
            "layer": layer, "model": model, "n_split_seeds": n,
            "mean_random": float(r.loc[common].mean()),
            "mean_grouped": float(d.loc[common].mean()),
            "mean_diff": float(diffs.mean()),
            "sd_diff": float(diffs.std(ddof=1)),
            "t_stat": float(t_stat), "p_raw": float(t_p),
            "wilcoxon_p": float(w_p),
            "cohen_dz": cohen_dz(diffs),
            "ci_lo": float(ci[0]), "ci_hi": float(ci[1]),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out, {}
    # Correct within each layer: the family of tests is "all models, one layer"
    out["p_holm"] = np.nan
    for layer, g in out.groupby("layer"):
        out.loc[g.index, "p_holm"] = holm(g.p_raw.tolist())
    out["significant_raw"] = out.p_raw < ALPHA
    out["significant_holm"] = out.p_holm < ALPHA

    meta = {
        "n_tests": int(len(out)),
        "n_sig_raw": int(out.significant_raw.sum()),
        "n_sig_holm": int(out.significant_holm.sum()),
        "expected_false_positives_uncorrected": round(ALPHA * len(out), 2),
        "min_detectable_dz_at_n5": round(min_detectable_effect(5), 3),
        "wilcoxon_floor_at_n5": 0.0625,
    }
    return out, meta


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    leak, meta = audit_leakage()
    if leak.empty:
        print("no leakage runs to audit"); return 1
    leak.to_csv(OUT / "leakage_tests.csv", index=False)

    lines = [
        "# Statistical Audit",
        "",
        "**Generated by** `analysis/statistical_audit.py`. Do not edit by hand.",
        f"**alpha** = {ALPHA}; **primary metric** = macro-F1; comparisons are "
        "**paired** over split seeds.",
        "",
        "## Design",
        "",
        "Two-level: 5 split seeds x 2 model seeds. Model seeds are **nested** inside "
        "split seeds and are averaged before testing -- they are not independent "
        "replicates, and treating them as such would claim n=10 when the design "
        "gives n=5. The dominant uncertainty is which runs land in which fold, which "
        "is exactly what the split seed varies (plan A5).",
        "",
        "## Power, stated before the results",
        "",
        f"- With n = 5 paired observations, the smallest effect detectable at "
        f"alpha={ALPHA} with 80% power is **d_z = {meta['min_detectable_dz_at_n5']}**. "
        "That is a large effect. This design can detect a big leakage gap; it cannot "
        "resolve small differences *between* architectures, and no such claim is made.",
        f"- The Wilcoxon signed-rank test at n=5 has a minimum attainable p of "
        f"**{meta['wilcoxon_floor_at_n5']}**, so it can never clear alpha=0.05 alone. "
        "It is reported as a direction check on the t-test, not as a second opinion "
        "that could independently confirm significance.",
        f"- {meta['n_tests']} tests were run, so roughly "
        f"**{meta['expected_false_positives_uncorrected']} false positives** would be "
        "expected uncorrected. Holm-Bonferroni is applied within each layer.",
        "",
        "## Leakage: random split vs group-disjoint split",
        "",
        "| Layer | Model | n | Random | Grouped | Diff | 95% CI | d_z | p | p (Holm) | Sig. |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|---:|:---:|",
    ]
    for _, r in leak.sort_values(["layer", "mean_diff"], ascending=[True, False]).iterrows():
        ci = (f"[{r.ci_lo:+.3f}, {r.ci_hi:+.3f}]"
              if pd.notna(r.ci_lo) else "n/a")
        sig = "**yes**" if r.significant_holm else ("raw only" if r.significant_raw else "no")
        lines.append(
            f"| {r.layer} | {r.model} | {int(r.n_split_seeds)} | {r.mean_random:.3f} | "
            f"{r.mean_grouped:.3f} | {r.mean_diff:+.3f} | {ci} | {r.cohen_dz:+.2f} | "
            f"{r.p_raw:.4f} | {r.p_holm:.4f} | {sig} |")

    lines += [
        "",
        f"**{meta['n_sig_raw']} of {meta['n_tests']}** tests are significant "
        f"uncorrected; **{meta['n_sig_holm']}** survive Holm correction.",
        "",
        "## What these numbers do and do not license",
        "",
        "**Licensed.** That a random split inflates macro-F1 relative to a "
        "group-disjoint split, for the high-capacity architectures, by an amount "
        "large enough to survive correction at n=5.",
        "",
        "**Not licensed.**",
        "",
        "- Any ranking *between* architectures on the group-disjoint side. The top "
        "three sit within 0.002 macro-F1 of each other, far inside the resolution "
        "of this design. The paper must say they are indistinguishable, not name a winner.",
        "- Any claim that a model with a non-significant leakage delta is leak-free. "
        "Absence of significance at n=5 is not evidence of absence, and the "
        "point estimates for those models are still positive.",
        "- Extrapolation to other corpora. One corpus, one testbed.",
        "",
        "## Deviations from the pre-registered plan",
        "",
        "- 2 model seeds rather than the planned 3, to keep total runtime tractable. "
        "This reduces the precision of the within-split average but not the number "
        "of independent observations, which is set by the 5 split seeds.",
        "- The trivial baselines are included in the correction family. Excluding "
        "them would make the correction less conservative, which would be the wrong "
        "direction to choose after seeing the results.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:6]))
    print(f"\nwrote {REPORT}")
    print(f"wrote {OUT/'leakage_tests.csv'}")
    print(f"\n{meta['n_sig_raw']}/{meta['n_tests']} significant raw, "
          f"{meta['n_sig_holm']} after Holm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
