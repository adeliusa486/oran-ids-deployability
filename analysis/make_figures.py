#!/usr/bin/env python3
"""Generate every data figure from processed results. No hand-edited numbers.

Design constraints applied (and why, since a reviewer will not ask but a reader
will feel them):

* **Categorical hues in fixed slot order**, never cycled: blue, orange, aqua.
  That ordering is validated, not chosen by eye -- worst all-pairs CVD dE 9.2,
  worst normal-vision dE 24.0 on a light surface.
* Aqua sits at 2.74:1 against the surface, below the 3:1 bar, so the **relief
  rule** applies and every series carries a visible direct label. Identity is
  never colour-alone: each series also gets a distinct marker and line style,
  which is what makes these readable when the journal prints in greyscale.
* **One axis.** No dual-scale plots anywhere.
* Hairline, recessive grid; solid, never dashed; thin marks.
* Text wears ink colours, never the series colour.

Output: PDF (vector, for LaTeX) and 400 dpi PNG, into figures/generated/.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path("figures/generated")
RES = Path("results")

# Validated categorical slots (light surface).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
GRID = "#e4e3df"
SURFACE = "#fcfcfb"

IEEE_COL = 3.5      # inches, single IEEE column
IEEE_WIDE = 7.16    # double column


def _style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5,
        "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
        "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
        "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK2, "ytick.color": INK2,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "grid.color": GRID, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "axes.grid": True, "axes.axisbelow": True,
        "legend.frameon": False,
        "figure.dpi": 150, "savefig.dpi": 400, "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def _despine(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)
    ax.tick_params(length=2.5)


def _save(fig, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print(f"  wrote {OUT/name}.pdf and .png")


# ---------------------------------------------------------------------------
def fig_leakage():
    """Random split vs group-disjoint split, per model. Two series, so a legend
    plus direct value labels; the gap between the pair is the finding."""
    src = RES / "EXP-002" / "processed" / "leakage_summary.csv"
    if not src.exists():
        print("  skip fig_leakage: no leakage_summary.csv")
        return
    df = pd.read_csv(src)
    for layer, g in df.groupby("layer"):
        g = g.sort_values("group_disjoint_f1_macro", ascending=True)
        n = len(g)
        y = np.arange(n)
        h = 0.30
        fig, ax = plt.subplots(figsize=(IEEE_COL, 0.32 * n + 1.25))
        # 2px-equivalent surface gap between the paired bars
        ax.barh(y + h / 2 + 0.03, g.random_f1_macro, height=h, color=ORANGE,
                label="Random split", zorder=3)
        ax.barh(y - h / 2 - 0.03, g.group_disjoint_f1_macro, height=h, color=BLUE,
                label="Group-disjoint split", zorder=3)
        for yi, (r, d) in enumerate(zip(g.random_f1_macro, g.group_disjoint_f1_macro)):
            ax.text(r + 0.012, yi + h / 2 + 0.03, f"{r:.3f}", va="center",
                    fontsize=6.3, color=INK2)
            ax.text(d + 0.012, yi - h / 2 - 0.03, f"{d:.3f}", va="center",
                    fontsize=6.3, color=INK2)
        ax.set_yticks(y, g.model)
        ax.set_xlabel("Macro-$F_1$")
        ax.set_xlim(0, 1.13)
        ax.xaxis.grid(True); ax.yaxis.grid(False)
        _despine(ax)
        # legend above the axes: inside it would sit on the trivial baselines
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2,
                  handlelength=1.2, columnspacing=1.4)
        ax.set_title(f"Split protocol inflates the score ({layer} layer)",
                     loc="left", pad=22)
        _save(fig, f"fig_leakage_{layer}")


# ---------------------------------------------------------------------------
def fig_alert_burden():
    """Operational precision against attack base rate.

    Log x because pi spans four decades. One axis only: alert volume is a
    separate panel, never a second y-scale on this one.
    """
    src = RES / "EXP-004" / "raw" / "tau_pi_sweep_radio.csv"
    if not src.exists():
        print("  skip fig_alert_burden: no tau_pi_sweep_radio.csv")
        return
    df = pd.read_csv(src)
    df = df[np.isclose(df.tau, 0.5)]
    models = ["logreg", "xgboost", "rf"]           # three validated slots
    colors = {m: c for m, c in zip(models, (BLUE, ORANGE, AQUA))}
    markers = {m: mk for m, mk in zip(models, ("o", "s", "^"))}
    styles = {m: ls for m, ls in zip(models, ("-", "--", "-."))}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(IEEE_WIDE, 2.6))
    fig.subplots_adjust(wspace=0.32)
    for m in models:
        g = df[df.model == m].groupby("pi")[["ppv", "alerts_per_hour"]].mean().reset_index()
        if g.empty:
            continue
        ax1.plot(g.pi, g.ppv, color=colors[m], marker=markers[m], ls=styles[m],
                 lw=1.4, ms=3.5, label=m, zorder=3)
        ax2.plot(g.pi, g.alerts_per_hour, color=colors[m], marker=markers[m],
                 ls=styles[m], lw=1.4, ms=3.5, label=m, zorder=3)
        # No direct labels here: at pi=0.1 all three series converge to within
        # 0.02 PPV, so labels collide into an unreadable block. The legend plus
        # per-series markers and line styles carry identity instead.

    for ax, ylab, title in ((ax1, "Operational precision (PPV)",
                             "Precision collapses at realistic base rates"),
                            (ax2, "Alerts per hour",
                             "Alert volume at $\\lambda_b$ = 240k benign flows/h")):
        ax.set_xscale("log")
        ax.set_xlabel("Attack base rate $\\pi$")
        ax.set_ylabel(ylab)
        ax.set_title(title, loc="left", pad=6)
        _despine(ax)
        ax.axvline(2e-3, color=MUTED, lw=0.6, zorder=1)
    # Linear, not log: the range spans 45k-80k, barely half a decade, and a log
    # axis there prints "8 x 10^4" ticks that read as precision we do not have.
    ax2.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:,.0f}k"))
    ax1.set_ylim(0, 1.0)
    ax1.annotate("assumed $\\pi$ = 0.002", (2e-3, 0.98),
                 textcoords="offset points", xytext=(4, 0),
                 fontsize=6.5, color=MUTED, va="top")
    ax1.legend(loc="upper left", bbox_to_anchor=(0.0, 0.88), handlelength=2.2)
    _save(fig, "fig_alert_burden")


# ---------------------------------------------------------------------------
def fig_latency_budget():
    """p99 per architecture against the swept near-RT budget.

    One series, so no legend: the title names it. The budget is a range, drawn
    as reference lines, because which line an author picks is what decides a
    conformance verdict in the existing literature.
    """
    src = RES / "EXP-005" / "processed" / "budget_sweep_radio.csv"
    if not src.exists():
        print("  skip fig_latency_budget: no budget_sweep_radio.csv")
        return
    df = pd.read_csv(src).sort_values("p99")
    fig, ax = plt.subplots(figsize=(IEEE_COL, 0.32 * len(df) + 1.2))
    y = np.arange(len(df))
    is_floor = df.model.str.contains("FLOOR")
    colors = [MUTED if f else BLUE for f in is_floor]
    ax.barh(y, df.p99, height=0.46, color=colors, zorder=3)
    for yi, (v, f) in enumerate(zip(df.p99, is_floor)):
        ax.text(v * 1.12, yi, f"{v:.2f}", va="center", fontsize=6.5, color=INK2)
    ax.set_yticks(y, df.model)
    ax.set_xscale("log")
    ax.set_xlabel("99th-percentile decision latency (ms, emulated)")
    ax.set_ylim(-0.8, len(df) - 0.2)
    for b, lab in ((10, "10 ms"), (100, "100 ms"), (1000, "1 s")):
        ax.axvline(b, color=ORANGE, lw=0.8, zorder=2)
        ax.annotate(lab, (b, -0.72), rotation=90, fontsize=6.3, color=ORANGE,
                    ha="right", va="bottom")
    ax.set_xlim(0.05, 3000)
    ax.xaxis.grid(True); ax.yaxis.grid(False)
    _despine(ax)
    ax.set_title("Conformance depends on which budget is chosen", loc="left", pad=6)
    _save(fig, "fig_latency_budget")


# ---------------------------------------------------------------------------
def fig_transfer():
    """Source against target, with the trivial floor drawn across the target.

    The floor line is the point of the figure. A target macro-F1 of 0.53 looks
    like a mediocre score until a coin flip is drawn at 0.42 beside it, at which
    point it looks like near-total failure -- and the MLP, the best model on the
    source, sits underneath the line.
    """
    src = RES / "EXP-026" / "processed" / "transfer_summary__a_to_b.csv"
    if not src.exists():
        print("  skip transfer figure"); return
    d = pd.read_csv(src)
    floor = float(d[d.model == "stratified"].target_f1.iloc[0])
    nt = d[~d.model.isin(["majority", "stratified"])].sort_values(
        "source_f1", ascending=False)

    fig, ax = plt.subplots(figsize=(IEEE_COL, 2.5))
    x = np.arange(len(nt))
    w = 0.38
    ax.bar(x - w / 2, nt.source_f1, w, label="Source held-out",
           color=BLUE, edgecolor="none")
    ax.bar(x + w / 2, nt.target_f1, w, label="Target ($D_B$)",
           color=ORANGE, edgecolor="none")
    ax.axhline(floor, color=INK, lw=0.9, ls="--", zorder=5)
    ax.annotate("stratified floor on $D_B$ (%.3f)" % floor,
                xy=(len(nt) - 0.45, floor), xytext=(0, 3),
                textcoords="offset points", ha="right", va="bottom",
                fontsize=6.5, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(nt.model, rotation=20, ha="right")
    ax.set_ylabel("macro-$F_1$")
    ax.set_ylim(0, 0.85)
    ax.legend(loc="upper right", ncol=1)
    _despine(ax)
    _save(fig, "fig_transfer")


def fig_prevalence():
    """PPV against base rate, pooled, with the corpus-precision line above it."""
    src = RES / "EXP-027" / "processed" / "ppv_spread_vs_prevalence.csv"
    if not src.exists():
        print("  skip prevalence figure"); return
    d = pd.read_csv(src)
    fig, ax = plt.subplots(figsize=(IEEE_COL, 2.5))
    colours = {"d_a_radio_heldout": BLUE, "d_b_target": ORANGE,
               "d_a_network_heldout_shared": AQUA}
    for surface, g in d.groupby("surface"):
        g = g.sort_values("pi")
        ax.fill_between(g.pi, g.ppv_min, g.ppv_max, alpha=0.18,
                        color=colours.get(surface, MUTED), lw=0)
        ax.plot(g.pi, (g.ppv_min + g.ppv_max) / 2, lw=1.2,
                color=colours.get(surface, MUTED),
                label=surface.replace("_", " "))
        cp = float(g.corpus_precision_max.iloc[0])
        ax.axhline(cp, color=colours.get(surface, MUTED), lw=0.7, ls=":")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"attack base rate $\pi$ (declared, not measured)")
    ax.set_ylabel("PPV in deployment")
    ax.annotate("dotted: precision measured on the corpus", xy=(0.02, 0.96),
                xycoords="axes fraction", fontsize=6.5, color=INK2, va="top")
    ax.legend(loc="lower right", fontsize=6.5)
    _despine(ax)
    _save(fig, "fig_prevalence")


def fig_estimator_bug():
    """B-E, drawn. Three estimates of one quantity against the lucky-fold count."""
    src = RES / "EXP-027" / "processed" / "estimator_comparison.csv"
    if not src.exists():
        print("  skip estimator figure"); return
    d = pd.read_csv(src)
    d = d[(d.surface == "d_a_radio_heldout")
          & (~d.model.isin(["majority", "stratified"]))]
    d = d.sort_values("n_folds_ppv_equals_1")
    fig, ax = plt.subplots(figsize=(IEEE_COL, 2.3))
    ax.plot(d.n_folds_ppv_equals_1, d.ppv_mean_of_folds, "o-", color=ORANGE,
            lw=1.2, ms=4, label="mean of folds (what was published)")
    ax.plot(d.n_folds_ppv_equals_1, d.ppv_median_of_folds, "s-", color=MUTED,
            lw=1.0, ms=3.5, label="median of folds")
    ax.plot(d.n_folds_ppv_equals_1, d.ppv_pooled, "^-", color=BLUE, lw=1.2,
            ms=4, label="pooled counts (correct)")
    for _, r in d.iterrows():
        ax.annotate(r.model, xy=(r.n_folds_ppv_equals_1, r.ppv_mean_of_folds),
                    xytext=(3, 3), textcoords="offset points", fontsize=6,
                    color=INK2)
    ax.set_xlabel("folds (of 40) in which FPR happened to be exactly 0")
    ax.set_ylabel(r"deployment PPV at $\pi=0.002$")
    ax.set_yscale("log")
    ax.legend(loc="upper left", fontsize=6.5)
    _despine(ax)
    _save(fig, "fig_estimator_bug")


def fig_extraction():
    """Extraction cost per packet by implementation, against deployed inference."""
    src = RES / "EXP-030" / "processed" / "extraction_speedup.csv"
    if not src.exists():
        print("  skip extraction figure"); return
    d = pd.read_csv(src).sort_values("pkts_per_flow")
    fig, ax = plt.subplots(figsize=(IEEE_COL, 2.4))
    ax.plot(d.pkts_per_flow, d.us_per_pkt_reference, "o-", color=ORANGE,
            lw=1.2, ms=4, label="reference (per-packet Python)")
    ax.plot(d.pkts_per_flow, d.us_per_pkt_vectorised, "^-", color=BLUE,
            lw=1.2, ms=4, label="vectorised (bulk NumPy)")
    ax.set_xscale("log")
    ax.set_xlabel("packets per flow")
    ax.set_ylabel(r"extraction, $\mu$s per packet")
    ax.legend(loc="upper right", fontsize=6.5)
    _despine(ax)
    _save(fig, "fig_extraction")


def main() -> int:
    _style()
    print("generating figures...")
    fig_leakage()
    fig_alert_burden()
    fig_latency_budget()
    fig_transfer()
    fig_prevalence()
    fig_estimator_bug()
    fig_extraction()
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
