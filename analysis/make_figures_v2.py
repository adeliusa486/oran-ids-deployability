#!/usr/bin/env python3
"""Figures for the revised manuscript. Every value is read from results/.

Design rules (dataviz skill, validated palette): categorical hues in fixed slot
order (blue, orange, aqua); no chart carries more than three hues, because six
series fail the all-pairs colour-vision check, so the six detectors appear as a
grey min-max band with two named models drawn over it; one y-axis per panel; no
titles inside the image (the caption carries the title); every series has a
marker or line style as well as a colour, for greyscale print.

Usage:  python analysis/make_figures_v2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_figures import (AQUA, BLUE, GRID, INK, INK2, MUTED, ORANGE,  # noqa: E402
                          SURFACE, _despine, _style)

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
P = RES / "EXP-052" / "processed"
OUT = ROOT / "figures" / "generated"
COL = 3.5
NAME = {"logreg": "LR", "tree": "DT", "rf": "RF", "xgboost": "XGB", "hgb": "HGB",
        "mlp": "MLP", "stratified": "Strat.", "majority": "Maj."}
NT = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp"]
PI = 0.002


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print("  wrote", name)


def ppv(t, f, pi=PI):
    den = t * pi + f * (1 - pi)
    return np.where(den > 0, t * pi / np.where(den > 0, den, 1), np.nan)


def fig_leakage():
    L = pd.read_csv(P / "leakage_stats.csv")
    order = NT + ["stratified", "majority"]
    L = L.set_index("model").loc[order[::-1]]
    y = np.arange(len(L))
    h = 0.26
    fig, ax = plt.subplots(figsize=(COL, 3.3))
    for k, (col, lab, c) in enumerate((("random", "Random", ORANGE),
                                        ("group_disjoint", "Run-disjoint", BLUE),
                                        ("stratified_group", "Cat.-stratified", AQUA))):
        ax.barh(y + (1 - k) * (h + 0.02), L[col], height=h, color=c, label=lab,
                zorder=3)
    ax.set_yticks(y, [NAME[m] for m in L.index])
    ax.set_xlabel("Macro-$F_1$, radio layer")
    ax.set_xlim(0, 1.0)
    ax.xaxis.grid(True); ax.yaxis.grid(False)
    _despine(ax)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=7.5,
              handlelength=1.1, columnspacing=1.0)
    save(fig, "fig_rev_leakage")


def fig_transfer():
    T = pd.read_csv(P / "transfer_stats.csv").query("direction == 'a_to_b'")
    T = T.set_index("model").loc[NT + ["stratified", "majority"]]
    x = np.arange(len(T))
    w = 0.38
    fig, ax = plt.subplots(figsize=(COL, 2.4))
    ax.bar(x - w / 2 - 0.01, T.src_ba, w, color=BLUE, label="Held-out $\\mathcal{D}_A$",
           zorder=3)
    ax.bar(x + w / 2 + 0.01, T.tgt_ba, w, color=ORANGE, label="$\\mathcal{D}_B$",
           hatch="///", edgecolor=SURFACE, lw=0, zorder=3)
    ax.axhline(0.5, color=INK, lw=0.9, ls="--", zorder=4)
    ax.annotate("chance", xy=(len(T) - 0.5, 0.5), xytext=(0, 3),
                textcoords="offset points", ha="right", fontsize=7, color=INK)
    ax.set_xticks(x, [NAME[m] for m in T.index])
    ax.set_ylabel("Balanced accuracy")
    ax.set_ylim(0, 1.05)
    ax.yaxis.grid(True); ax.xaxis.grid(False)
    _despine(ax)
    ax.legend(loc="upper right", ncol=2, fontsize=7.5)
    save(fig, "fig_rev_transfer")


def _pooled_by_tau(counts):
    g = counts.groupby(["model", "tau"])[["tp", "fp", "tn", "fn"]].sum().reset_index()
    g["tpr"] = g.tp / (g.tp + g.fn)
    g["fpr"] = g.fp / (g.fp + g.tn)
    g["ppv"] = ppv(g.tpr.to_numpy(), g.fpr.to_numpy())
    return g[g.model.isin(NT) & (g.tpr >= 0.10)]


def fig_threshold():
    radio = _pooled_by_tau(pd.read_csv(RES / "EXP-046/raw/tau_counts_radio.csv"))
    net = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/tau_counts.csv")
    tgt = _pooled_by_tau(net[net.domain == "target"])
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.3), sharey=True)
    for ax, g, lab in ((axes[0], radio, "$\\mathcal{D}_A$ radio"),
                       (axes[1], tgt, "$\\mathcal{D}_B$ (transfer)")):
        band = g.groupby("tau").ppv.agg(["min", "max"]).reset_index()
        ax.fill_between(band.tau, band["min"], band["max"], color=MUTED,
                        alpha=0.30, lw=0, label="six detectors")
        for m, c, mk, ls in (("logreg", BLUE, "o", "-"), ("rf", ORANGE, "s", "--")):
            s = g[g.model == m].sort_values("tau")
            ax.plot(s.tau, s.ppv, color=c, marker=mk, ms=2.6, lw=1.2, ls=ls,
                    markevery=max(1, len(s) // 12), label=NAME[m], zorder=3)
        ax.axhline(0.05, color=INK2, lw=0.6, ls=":")
        ax.set_yscale("log")
        ax.set_xlabel("Threshold $\\tau$")
        ax.text(0.03, 0.97, lab, transform=ax.transAxes, va="top", fontsize=7.5)
        _despine(ax)
    axes[0].set_ylabel("Operational PPV at $\\pi=0.002$")
    axes[1].annotate("0.05", xy=(1.0, 0.05), xycoords=("axes fraction", "data"),
                     xytext=(-2, 2), textcoords="offset points", ha="right",
                     fontsize=6.5, color=INK2)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=3,
               fontsize=7, handlelength=1.6)
    fig.subplots_adjust(wspace=0.08, top=0.88)
    save(fig, "fig_rev_threshold")


def fig_prevalence():
    A = pd.read_csv(P / "pooled_radio_tau05.csv").set_index("model").loc[NT]
    pis = np.logspace(-4, np.log10(0.5), 60)
    vals = np.array([[ppv(r.tpr, r.fpr, p) for p in pis] for _, r in A.iterrows()])
    fig, ax = plt.subplots(figsize=(COL, 2.3))
    ax.fill_between(pis, vals.min(0), vals.max(0), color=BLUE, alpha=0.35, lw=0,
                    label="operational PPV, six detectors")
    ax.fill_between(pis, A.corpus_precision.min(), A.corpus_precision.max(),
                    color=ORANGE, alpha=0.45, lw=0, label="corpus precision")
    ax.axvline(PI, color=MUTED, lw=0.7)
    ax.annotate("$\\pi=0.002$", xy=(PI, 0.25), xytext=(3, 0),
                textcoords="offset points", fontsize=7, color=INK2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Declared attack prevalence $\\pi$")
    ax.set_ylabel("Precision")
    ax.set_ylim(1e-4, 1.5)
    _despine(ax)
    ax.legend(loc="lower right", fontsize=7)
    save(fig, "fig_rev_prevalence")


def fig_reliability():
    B = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/reliability_bins.csv")
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.95), sharey=True)
    for ax, m in zip(axes, ("logreg", "xgboost")):
        ax.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls=":")
        for dom, c, mk, lab in (("source_heldout", BLUE, "o", "held-out $\\mathcal{D}_A$"),
                                ("target", ORANGE, "s", "$\\mathcal{D}_B$")):
            g = B[(B.model == m) & (B.domain == dom)].sort_values("mean_score")
            # pool every seed's equal-mass bins, then re-bin the pooled points
            # into 15 groups of equal total count, weighted by bin size
            cum = g.n.cumsum() / g.n.sum()
            grp = np.minimum((cum * 15).astype(int), 14)
            w = g.groupby(grp.to_numpy()).apply(lambda d: pd.Series({
                "s": np.average(d.mean_score, weights=d.n),
                "f": np.average(d.attack_freq, weights=d.n)}), include_groups=False)
            ax.plot(w.s, w.f, color=c, marker=mk, ms=2.8, lw=1.1, label=lab)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        ax.set_xlabel("Mean score $\\hat{p}$")
        ax.text(0.03, 0.97, NAME[m], transform=ax.transAxes, va="top", fontsize=8)
        _despine(ax)
    axes[0].set_ylabel("Attack frequency")
    axes[1].legend(loc="lower right", fontsize=6.5)
    fig.subplots_adjust(wspace=0.08)
    save(fig, "fig_rev_reliability")


def main() -> int:
    _style()
    plt.rcParams.update({"font.size": 8, "axes.labelsize": 8,
                         "xtick.labelsize": 7.5, "ytick.labelsize": 7.5})
    for fn in (fig_leakage, fig_transfer, fig_threshold, fig_prevalence,
               fig_reliability):
        fn()
    return 0


if __name__ == "__main__":
    sys.exit(main())
