#!/usr/bin/env python3
"""Data figures for the manuscript. Every value is read from results/.

Camera-ready rules (revision of 2026-09-25):
  * one IEEE column (3.5 in) wide, included at \\columnwidth, so text prints at
    its set size: 8 pt labels, 7 pt ticks and legends, sans-serif to match the
    IEEE Access caption face;
  * white background, closed axes with inward ticks, 0.6 pt frame, no titles
    inside the image (the caption carries the title);
  * at most three hues per chart (Okabe-Ito blue, vermillion, green), and every
    series also differs by marker or line style so it survives greyscale print;
  * where six detectors would need six hues, they are drawn as grey min-max
    extent with two named models on top;
  * vector PDF for LaTeX and a 600 dpi PNG for checking.

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
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from revision_stats import ci  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
P = RES / "EXP-052" / "processed"
OUT = ROOT / "figures" / "generated"
COL = 3.5
NAME = {"logreg": "LR", "tree": "DT", "rf": "RF", "xgboost": "XGB", "hgb": "HGB",
        "mlp": "MLP", "stratified": "Strat.", "majority": "Maj.", "nn1": "1-NN"}
NT = ["logreg", "tree", "rf", "xgboost", "hgb", "mlp"]
PI = 0.002
LAMBDA_B = 240_000.0
UE_HOUR = 225            # 16 s windows per benign UE-hour

# Okabe-Ito, colour-vision safe; greys for context
BLUE, VERM, GREEN = "#0072B2", "#D55E00", "#009E73"
INK, INK2, GREY, LIGHT = "#1a1a1a", "#4d4d4d", "#9a9a9a", "#e3e3e3"


def style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "mathtext.fontset": "stixsans", "patch.linewidth": 0.5,
        "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "legend.fontsize": 7,
        "axes.linewidth": 0.6, "axes.edgecolor": INK, "axes.labelcolor": INK,
        "text.color": INK, "xtick.color": INK, "ytick.color": INK,
        "xtick.direction": "in", "ytick.direction": "in",
        "xtick.top": True, "ytick.right": True,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "xtick.minor.size": 1.6, "ytick.minor.size": 1.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.minor.width": 0.5, "ytick.minor.width": 0.5,
        "axes.grid": False, "grid.color": LIGHT, "grid.linewidth": 0.5,
        "lines.linewidth": 1.0, "lines.markersize": 4,
        "legend.frameon": True, "legend.edgecolor": "#b0b0b0",
        "legend.fancybox": False, "legend.framealpha": 1.0,
        "legend.borderpad": 0.35, "legend.handlelength": 1.6,
        "legend.handletextpad": 0.4, "legend.columnspacing": 1.0,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "savefig.bbox": "tight",
        "savefig.pad_inches": 0.015, "savefig.dpi": 600,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", metadata={"CreationDate": None}
                    if ext == "pdf" else None)
    plt.close(fig)
    print("  wrote", name)


def ppv(t, f, pi=PI):
    t, f = np.asarray(t, float), np.asarray(f, float)
    den = t * pi + f * (1 - pi)
    return np.where(den > 0, t * pi / np.where(den > 0, den, 1), np.nan)


def panel_tag(ax, s, x=0.02, y=0.97, **kw):
    ax.text(x, y, s, transform=ax.transAxes, va="top", ha="left", fontsize=7.5,
            **kw)


# ---------------------------------------------------------------------------
def fig_leakage():
    """Dot plot: macro-F1 under three protocols, one row per detector."""
    L = pd.read_csv(P / "leakage_stats.csv").set_index("model")
    nn = pd.read_csv(P / "leakage_nn1.csv").set_index("model")
    L = pd.concat([L, nn])
    order = NT + ["nn1", "stratified", "majority"]
    L = L.loc[order]
    y = np.arange(len(L))[::-1].astype(float)
    y[-2:] -= 0.35                      # set the trivial floors apart
    y[order.index("nn1")] -= 0.2
    fig, ax = plt.subplots(figsize=(COL, 2.55))
    for yi, (_, r) in zip(y, L.iterrows()):
        v = [r["random"], r["group_disjoint"], r["stratified_group"]]
        ax.plot([min(v), max(v)], [yi, yi], color=GREY, lw=0.8, zorder=1)
    for col, lab, c, mk, fc in (("random", "Random split", VERM, "o", VERM),
                                ("group_disjoint", "Run-disjoint", BLUE, "s", BLUE),
                                ("stratified_group", "Category-stratified run-disjoint",
                                 GREEN, "^", "white")):
        ax.plot(L[col], y, ls="none", marker=mk, ms=4.2, mfc=fc, mec=c, mew=0.9,
                label=lab, zorder=3)
    ax.set_yticks(y, [NAME[m] for m in L.index])
    ax.tick_params(axis="y", which="both", right=False, left=False)
    ax.axhline(y[order.index("nn1")] + 0.6, color=LIGHT, lw=0.6)
    ax.axhline(y[-2] + 0.62, color=LIGHT, lw=0.6)
    ax.set_xlabel("Macro-$F_1$, $\\mathcal{D}_A$ radio layer")
    ax.set_xlim(0.40, 1.0)
    ax.set_ylim(y[-1] - 0.6, y[0] + 0.6)
    ax.xaxis.grid(True, zorder=0)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3,
              frameon=False, handletextpad=0.2, columnspacing=0.8, fontsize=6.8)
    save(fig, "fig_rev_leakage")


def fig_benign():
    """False positive rate on each benign radio session held out alone."""
    B = pd.read_csv(P / "drift_v3_benign.csv").sort_values("day").reset_index(drop=True)
    x = np.arange(len(B)).astype(float)
    x[-1] += 0.8                               # the 47-day gap in the schedule
    fig, ax = plt.subplots(figsize=(COL, 2.05))
    ax.vlines(x, B.fpr_min, B.fpr_max, color=INK2, lw=1.0, zorder=2)
    ax.plot(x, B.fpr_min, ls="none", marker="_", ms=5, color=INK2, zorder=2)
    ax.plot(x, B.fpr_max, ls="none", marker="_", ms=5, color=INK2, zorder=2)
    late = B.day > 30
    ax.plot(x[~late], B.fpr_mean[~late], ls="none", marker="o", ms=4.6,
            mfc=BLUE, mec=BLUE, label="first week (days 0 to 6)", zorder=3)
    ax.plot(x[late], B.fpr_mean[late], ls="none", marker="D", ms=4.2, mfc=VERM,
            mec=VERM, label="attack period (day 53)", zorder=3)
    ax.axvline((x[-2] + x[-1]) / 2, color=GREY, lw=0.6, ls=(0, (3, 2)))
    ax.text((x[-2] + x[-1]) / 2, 0.5, "47-day gap", rotation=90, ha="right",
            va="center", fontsize=6.5, color=INK2)
    ax.set_xticks(x, [f"{int(s)}" for s in B.session])
    ax.set_xlabel("Held-out benign session (ordered by capture day)")
    ax.set_ylabel("False positive rate")
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlim(x[0] - 0.6, x[-1] + 0.6)
    ax.tick_params(axis="x", top=False)
    ax.yaxis.grid(True, zorder=0)
    ax.tick_params(axis="y", right=False)
    sec = ax.secondary_yaxis("right", functions=(lambda v: v * UE_HOUR,
                                                 lambda v: v / UE_HOUR))
    sec.set_ylabel("False alerts per benign UE-hour")
    sec.set_yticks([0, 50, 100, 150, 200])
    ax.legend(loc="upper left", fontsize=6.5, handletextpad=0.2)
    save(fig, "fig_rev_benign")


def _per_seed_ba(runs: pd.DataFrame, dom: str) -> pd.DataFrame:
    r = runs[runs.domain == dom]
    return r.pivot_table(index="split_seed", columns="model", values="balanced_accuracy")


def _clean_target_ba() -> pd.DataFrame:
    """Per-seed balanced accuracy on D_B without the benign copies (EXP-056),
    computed exactly as analysis/revision_stats.py does for Table tab:transfer."""
    g = pd.read_csv(RES / "EXP-056/a_to_b__shared/raw/tau_counts_by_group.csv",
                    low_memory=False, dtype={"group": str})
    g = g[(g.domain == "target") & np.isclose(g.tau, 0.5)
          & ~g.group.str.endswith("|c")]
    s = g.groupby(["model", "split_seed"])[["tp", "fp", "tn", "fn"]].sum()
    ba = (s.tp / (s.tp + s.fn) + s.tn / (s.tn + s.fp)) / 2
    return ba.unstack("model")


def fig_transfer():
    """Dumbbells: held-out source against target balanced accuracy."""
    T = pd.read_csv(P / "transfer_stats.csv").query("direction == 'a_to_b'").set_index("model")
    ratio = float(T.n_ratio_nb.iloc[0])
    runs = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/runs.csv")
    src, tgt = _per_seed_ba(runs, "source_heldout"), _per_seed_ba(runs, "target")
    clean = _clean_target_ba()
    runs_c = pd.read_csv(RES / "EXP-058/a_to_c__shared/raw/runs.csv")
    src_c, tgt_c = _per_seed_ba(runs_c, "source_heldout"), _per_seed_ba(runs_c, "target")
    ratio_c = float(pd.read_csv(P / "third_transfer.csv").query(
        "direction == 'a_to_c'").n_ratio_nb.iloc[0])
    ref = pd.read_csv(P / "target_reference.csv")
    ref_b = ref[(ref.feature_set == "shared18") & (ref.protocol == "random")].set_index("model").ba_clean
    ref3 = pd.read_csv(P / "third_reference.csv")
    ref_c = ref3[(ref3.feature_set == "shared18") & (ref3.protocol == "random")].set_index("model").ba

    ref_b_all = ref[(ref.feature_set == "shared18") & (ref.protocol == "random")].set_index("model").ba
    panels = (("$\\mathcal{D}_B$, all flows", src, tgt, ratio, ref_b_all),
              ("$\\mathcal{D}_B$, consistent labels", src.loc[clean.index], clean,
               ratio, ref_b),
              ("$\\mathcal{D}_C$ (third corpus)", src_c, tgt_c, ratio_c, ref_c))
    fig, axes = plt.subplots(1, 3, figsize=(COL, 2.05), sharey=True)
    y = np.arange(len(NT))[::-1]
    for ax, (lab, S, Tg, rt, rf) in zip(axes, panels):
        ax.axvline(0.5, color=GREY, lw=0.6, ls=(0, (3, 2)), zorder=0)
        for yi, m in zip(y, NT):
            s, t = S[m].mean(), Tg[m].mean()
            c = ci(Tg[m].to_numpy() - 0.5, rt)
            ax.plot([s, t], [yi, yi], color=GREY, lw=1.0, zorder=1)
            ax.plot([c["nb_lo"] + 0.5, c["nb_hi"] + 0.5], [yi, yi], color=VERM,
                    lw=2.2, alpha=0.35, solid_capstyle="butt", zorder=2)
            ax.plot(s, yi, "o", ms=4.2, mfc="white", mec=BLUE, mew=1.0, zorder=3)
            ax.plot(t, yi, "o", ms=4.2, mfc=VERM, mec=VERM, zorder=3)
            if rf is not None and m in rf.index:
                ax.plot(rf[m], yi, marker="|", ms=7, mew=1.3, color=INK, zorder=3)
        ax.set_xlim(0.38, 1.02)
        ax.set_xticks([0.5, 0.75, 1.0], ["0.5", "0.75", "1"])
        ax.set_title(lab, fontsize=6.8, pad=3)
        ax.tick_params(axis="y", left=False, right=False)
        ax.xaxis.grid(True, zorder=0)
    axes[0].set_yticks(y, [NAME[m] for m in NT])
    axes[1].set_xlabel("Balanced accuracy")
    h = [plt.Line2D([], [], ls="none", marker="o", mfc="white", mec=BLUE, mew=1.0,
                    ms=4.2, label="held-out $\\mathcal{D}_A$"),
         plt.Line2D([], [], ls="none", marker="o", mfc=VERM, mec=VERM, ms=4.2,
                    label="target (95% corrected interval)"),
         plt.Line2D([], [], ls="none", marker="|", color=INK, ms=7, mew=1.3,
                    label="in-target reference")]
    fig.legend(handles=h, loc="lower center", bbox_to_anchor=(0.53, 0.96), ncol=3,
               frameon=False, fontsize=6.5, handletextpad=0.15, columnspacing=0.7)
    fig.subplots_adjust(wspace=0.10)
    save(fig, "fig_rev_transfer")


def fig_shift():
    """Per-feature Wasserstein distance between D_A and D_B, source quantiles."""
    F = pd.read_csv(RES / "EXP-045/processed/feature_shift.csv").sort_values(
        "w1_source_quantile")
    y = np.arange(len(F))
    fig, ax = plt.subplots(figsize=(COL, 2.6))
    rob = F.robust.to_numpy()
    ax.hlines(y, 0, F.w1_source_quantile, color=LIGHT, lw=1.6, zorder=1)
    ax.plot(F.w1_source_quantile[rob], y[rob], "o", ms=4.4, mfc=BLUE, mec=BLUE,
            label="exporter-robust subset", zorder=3)
    ax.plot(F.w1_source_quantile[~rob], y[~rob], "o", ms=4.4, mfc="white",
            mec=INK2, mew=0.9, label="segmentation-dependent", zorder=3)
    for val, lab, ls in ((F.w1_source_quantile[rob].mean(), "mean, robust", "-"),
                         (F.w1_source_quantile[~rob].mean(), "mean, other", (0, (3, 2)))):
        ax.axvline(val, color=INK2, lw=0.7, ls=ls, zorder=0, label=lab)
    ax.set_yticks(y, F.feature.str.replace("_", "\\_", regex=False).map(
        lambda s: f"$\\mathtt{{{s}}}$"))
    ax.tick_params(axis="y", left=False, right=False, labelsize=6.3)
    ax.set_xlabel("$W_1$ between $\\mathcal{D}_A$ and $\\mathcal{D}_B$ (source quantiles)")
    ax.set_xlim(0, 0.65)
    ax.set_ylim(-0.7, len(F) - 0.3)
    ax.xaxis.grid(True, zorder=0)
    ax.legend(loc="lower right", fontsize=6.5, handletextpad=0.2)
    save(fig, "fig_rev_shift")


def _pooled_by_tau(counts):
    g = counts.groupby(["model", "tau"])[["tp", "fp", "tn", "fn"]].sum().reset_index()
    g["tpr"] = g.tp / (g.tp + g.fn)
    g["fpr"] = g.fp / (g.fp + g.tn)
    g["ppv"] = ppv(g.tpr.to_numpy(), g.fpr.to_numpy())
    return g


def fig_threshold():
    radio = _pooled_by_tau(pd.read_csv(RES / "EXP-046/raw/tau_counts_radio.csv"))
    net = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/tau_counts.csv")
    tgt = _pooled_by_tau(net[net.domain == "target"])
    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.1), sharey=True)
    for ax, g, lab in ((axes[0], radio, "(a) $\\mathcal{D}_A$ radio windows"),
                       (axes[1], tgt, "(b) $\\mathcal{D}_B$ flows (transfer)")):
        g = g[g.model.isin(NT) & (g.tpr >= 0.10)]
        band = g.groupby("tau").ppv.agg(["min", "max"]).reset_index()
        ax.fill_between(band.tau, band["min"], band["max"], color=LIGHT, lw=0,
                        label="six detectors, range")
        for m, c, mk, ls in (("logreg", BLUE, "o", "-"), ("rf", VERM, "s", "--")):
            s = g[g.model == m].sort_values("tau")
            ax.plot(s.tau, s.ppv, color=c, marker=mk, ms=2.6, lw=1.0, ls=ls,
                    markevery=max(1, len(s) // 10), label=NAME[m], zorder=3)
        ax.axhline(0.1, color=INK2, lw=0.6, ls=":")
        ax.set_yscale("log")
        ax.set_ylim(1e-3, 0.5)
        ax.set_xlim(0, 1)
        ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        ax.set_xlabel("Decision threshold $\\tau$")
        panel_tag(ax, lab)
    axes[0].set_ylabel("Operational PPV at $\\pi = 0.002$")
    axes[1].text(0.98, 0.1, "$\\rho = 0.1$", transform=axes[1].get_yaxis_transform(),
                 ha="right", va="bottom", fontsize=6.5, color=INK2)
    h, lab = axes[0].get_legend_handles_labels()
    fig.subplots_adjust(wspace=0.08, top=0.87)
    fig.legend(h, lab, loc="lower center", bbox_to_anchor=(0.53, 0.875), ncol=3,
               frameon=False)
    save(fig, "fig_rev_threshold")


def fig_prevalence():
    A = pd.read_csv(P / "pooled_radio_tau05.csv").set_index("model").loc[NT]
    pis = np.logspace(-4, np.log10(0.5), 80)
    fig, ax = plt.subplots(figsize=(COL, 2.1))
    ax.axhspan(A.corpus_precision.min(), A.corpus_precision.max(), color=VERM,
               alpha=0.55, lw=0, label="corpus precision, six detectors")
    for i, (_, r) in enumerate(A.iterrows()):
        ax.plot(pis, ppv(r.tpr, r.fpr, pis), color=BLUE, lw=0.8, alpha=0.85,
                label="operational PPV, six detectors" if i == 0 else None)
    ax.axvline(PI, color=INK2, lw=0.6, ls=(0, (3, 2)))
    ax.text(PI * 1.15, 0.2, "$\\pi = 0.002$", fontsize=6.5, color=INK2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Declared attack prevalence $\\pi$")
    ax.set_ylabel("Precision")
    ax.set_ylim(1e-4, 1.6)
    ax.set_xlim(1e-4, 0.5)
    ax.legend(loc="lower right", fontsize=6.5)
    save(fig, "fig_rev_prevalence")


def _alert_grid(counts, amax, rho, rmin=0.5):
    g = _pooled_by_tau(counts)
    g = g[g.model.isin(NT) & (g.tpr >= rmin)].copy()
    g["fa_h"] = g.fpr * LAMBDA_B
    out = np.zeros((len(rho), len(amax)), int)
    for i, r in enumerate(rho):
        for j, a in enumerate(amax):
            ok = g[(g.ppv >= r) & (g.fa_h <= a)]
            out[i, j] = ok.model.nunique()
    return out


def fig_sensitivity():
    """How many architectures meet each term of Eq. (7) as the bounds move."""
    bg = pd.read_csv(RES / "EXP-056/a_to_b__shared/raw/tau_counts_by_group.csv",
                     low_memory=False, dtype={"group": str})
    clean = bg[(bg.domain == "target") & ~bg.group.str.endswith("|c")]
    clean = clean.groupby(["model", "split_seed", "tau"])[["tp", "fp", "tn", "fn"]].sum().reset_index()
    net = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/tau_counts.csv")
    allf = net[net.domain == "target"]
    amax = np.logspace(1, 6, 21)                  # 10 .. 1e6 false alerts per hour
    rho = np.logspace(-3, 0, 19)                  # 0.001 .. 1
    Gc = _alert_grid(clean, amax, rho)
    Ga = _alert_grid(allf, amax, rho)
    print("   all-flows grid never exceeds the clean grid:", bool((Ga <= Gc).all()))
    pred = pd.read_csv(P / "predicate.csv").set_index("model").loc[NT]

    fig = plt.figure(figsize=(COL, 2.45))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.35, 1], height_ratios=[0.06, 1],
                          wspace=0.45, hspace=0.12)
    ax = fig.add_subplot(gs[1, 0])
    cax = fig.add_subplot(gs[0, 0])
    cmap = ListedColormap(["#ffffff", "#deebf7", "#9ecae1", "#6baed6", "#3182bd",
                           "#08519c", "#08306b"])
    norm = BoundaryNorm(np.arange(-0.5, 7.5), cmap.N)
    ex = [np.log10(amax[0]), np.log10(amax[-1]), np.log10(rho[0]), np.log10(rho[-1])]
    im = ax.imshow(Gc, origin="lower", aspect="auto", cmap=cmap, norm=norm,
                   extent=ex, interpolation="nearest")
    ax.contour(np.log10(amax), np.log10(rho), (Ga > 0).astype(float), levels=[0.5],
               colors=[VERM], linewidths=0.9, linestyles="--")
    ax.plot([], [], color=VERM, lw=0.9, ls="--", label="all flows: $\geq$1 passes")
    ax.legend(loc="upper right", fontsize=6, handlelength=1.4, borderpad=0.25)
    ax.plot(np.log10(200), np.log10(0.1), marker="*", ms=7, mfc="white", mec=INK,
            mew=0.8)
    ax.annotate("stated bounds", xy=(np.log10(200), np.log10(0.1)),
                xytext=(np.log10(200) + 0.25, np.log10(0.1) + 0.35), fontsize=6.3,
                arrowprops=dict(arrowstyle="-", lw=0.5, color=INK))
    ax.set_xticks([1, 2, 3, 4, 5, 6], ["$10$", "$10^2$", "$10^3$", "$10^4$",
                                       "$10^5$", "$10^6$"])
    ax.set_yticks([-3, -2, -1, 0], ["0.001", "0.01", "0.1", "1"])
    ax.set_xlabel("$A_{\\max}$, false alerts per hour")
    ax.set_ylabel("Minimum PPV $\\rho$")
    panel_tag(ax, "(a)", y=0.10)
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=range(7))
    cax.xaxis.set_ticks_position("top")
    cax.xaxis.set_label_position("top")
    cb.ax.tick_params(labelsize=6, length=1.5, direction="out", top=True,
                      bottom=False)
    cb.outline.set_linewidth(0.5)
    cb.set_label("architectures meeting the alert term ($r_{\\min} = 0.5$)",
                 fontsize=6.5, labelpad=2)

    ax2 = fig.add_subplot(gs[1, 1])
    d = np.linspace(0, 0.6, 601)
    n = [(pred.dBA_upper <= v).sum() for v in d]
    ax2.step(d, n, where="post", color=BLUE, lw=1.1)
    ax2.axvline(0.10, color=INK2, lw=0.6, ls=(0, (3, 2)))
    ax2.text(0.115, 5.4, "$\\delta = 0.10$", fontsize=6.3, color=INK2)
    ax2.set_xlim(0, 0.6); ax2.set_ylim(-0.3, 6.5)
    ax2.set_yticks(range(0, 7))
    ax2.set_xlabel("$\\delta$, bound on $\\overline{\\Delta}_{\\mathrm{BA}}$")
    ax2.set_ylabel("Architectures meeting\nthe generalization term", fontsize=7)
    ax2.yaxis.grid(True, zorder=0)
    panel_tag(ax2, "(b)")
    save(fig, "fig_rev_sensitivity")
    return Gc, Ga, amax, rho


def fig_reliability():
    B = pd.read_csv(RES / "EXP-041/a_to_b__shared/raw/reliability_bins.csv")
    fig, axes = plt.subplots(1, 2, figsize=(COL, 1.9), sharey=True)
    for ax, m in zip(axes, ("logreg", "xgboost")):
        ax.plot([0, 1], [0, 1], color=GREY, lw=0.6, ls=":")
        for dom, c, mk, ls, lab in (("source_heldout", BLUE, "o", "-",
                                     "held-out $\\mathcal{D}_A$"),
                                    ("target", VERM, "s", "--", "$\\mathcal{D}_B$")):
            g = B[(B.model == m) & (B.domain == dom)].sort_values("mean_score")
            # pool every seed's equal-mass bins, then re-bin the pooled points
            # into 15 groups of equal total count, weighted by bin size
            cum = g.n.cumsum() / g.n.sum()
            grp = np.minimum((cum * 15).astype(int), 14)
            w = g.groupby(grp.to_numpy()).apply(lambda d: pd.Series({
                "s": np.average(d.mean_score, weights=d.n),
                "f": np.average(d.attack_freq, weights=d.n)}), include_groups=False)
            ax.plot(w.s, w.f, color=c, marker=mk, ms=2.8, lw=1.0, ls=ls, label=lab)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        ax.set_yticks([0, 0.5, 1], ["0", "0.5", "1"])
        ax.set_xlabel("Mean score $\\hat{p}$")
        panel_tag(ax, NAME[m])
    axes[0].set_ylabel("Observed attack frequency")
    axes[1].legend(loc="lower right", fontsize=6.3)
    fig.subplots_adjust(wspace=0.08)
    save(fig, "fig_rev_reliability")


def fig_latency():
    """Per-call latency quantiles on one host (EXP-043), radio layer."""
    L = pd.read_csv(RES / "EXP-043/raw/latency_stages.csv")
    R = L[L.layer == "radio"]
    floor = float(L[(L.layer == "platform")].p99.iloc[0])
    agg = R[R.stage == "window_aggregation"].iloc[0]
    impl = (("sk_dataframe", "scikit-learn, DataFrame", GREY, "o"),
            ("sk_array", "scikit-learn, array, 1 thread", BLUE, "s"),
            ("onnx", "ONNX Runtime, 1 thread", VERM, "D"))
    fig, ax = plt.subplots(figsize=(COL, 2.55))
    rows = NT + ["agg"]
    ypos = {m: len(rows) - 1 - i for i, m in enumerate(rows)}
    off = {"sk_dataframe": 0.24, "sk_array": 0.0, "onnx": -0.24}
    for st, lab, c, mk in impl:
        first = True
        for m in NT:
            r = R[(R.model == m) & (R.stage == st)]
            if r.empty:
                continue
            r = r.iloc[0]
            yy = ypos[m] + off[st]
            ax.plot([r.p50, r.p99], [yy, yy], color=c, lw=1.1, zorder=2)
            ax.plot(r.p95, yy, marker="|", ms=4, mew=0.9, color=c, zorder=3)
            ax.plot(r.p50, yy, marker=mk, ms=3.3, mfc="white", mec=c, mew=0.9, zorder=3)
            ax.plot(r.p99, yy, marker=mk, ms=3.3, mfc=c, mec=c, zorder=3, ls="none",
                    label=lab if first else None)
            first = False
    y = ypos["agg"]
    ax.plot([agg.p50, agg.p99], [y, y], color=INK, lw=1.1)
    ax.plot(agg.p50, y, "^", ms=3.3, mfc="white", mec=INK, mew=0.9)
    ax.plot(agg.p99, y, "^", ms=3.3, mfc=INK, mec=INK)
    ax.axvspan(10, 1e3, color=LIGHT, lw=0, zorder=0)
    ax.axvline(10, color=INK2, lw=0.7)
    ax.text(12, len(rows) + 0.45, "smallest budget\nin the range,\n$B = 10$ ms",
            fontsize=6.2, va="top", color=INK2)
    ax.axvline(floor, color=GREY, lw=0.6, ls=":")
    ax.text(floor * 1.15, -0.62, "no-op", fontsize=6, color=INK2, va="bottom")
    ax.set_xscale("log")
    ax.set_xlim(5e-4, 300)
    ax.set_ylim(-0.7, len(rows) + 0.55)
    ax.set_yticks([ypos[m] for m in rows], [NAME.get(m, m) for m in NT]
                  + ["window\naggregation"])
    ax.tick_params(axis="y", left=False, right=False)
    ax.set_xlabel("Per-call latency (ms), $p_{50}$ (open) to $p_{99}$ (filled)")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.0), fontsize=6.2,
              handletextpad=0.2, borderpad=0.3)
    ax.text(0.02, 0.985, "timed: $t_{\\mathrm{feat}} + t_{\\mathrm{inf}}$, one host\n"
            "not timed: $t_{\\mathrm{ind}}$, $t_{\\mathrm{act}}$, $t_q$ (no RIC)",
            transform=ax.transAxes, va="top", fontsize=6.2, color=INK2,
            bbox=dict(fc="white", ec="none", pad=0.5))
    save(fig, "fig_rev_latency")


def fig_latency_cdf():
    """Empirical CDF of per-call latency from EXP-060, a repeat of the radio part
    of EXP-043 that kept every one of the 20,000 timed calls per stage.

    (a) the radio decision path the deployability test uses (window
        aggregation + ONNX Runtime), one line per architecture;
    (b) one architecture (RF) under the three implementations of Table XXI.
    The y axis is logit-scaled so that p50, p95 and p99 are all readable.
    """
    S = np.load(RES / "EXP-060/raw/latency_samples.npz")

    def ecdf(x):
        x = np.sort(np.asarray(x, float))
        f = (np.arange(1, len(x) + 1) - 0.5) / len(x)
        return x, f

    fig, axes = plt.subplots(1, 2, figsize=(COL, 2.3), sharey=True)
    ax = axes[0]
    for i, m in enumerate(NT):
        k = f"radio__{m}__e2e_aggregate_plus_onnx"
        if k not in S:
            continue
        x, f = ecdf(S[k])
        ax.plot(x, f, color=BLUE if m in ("rf",) else GREY, lw=1.0 if m == "rf" else 0.8,
                label="RF" if m == "rf" else ("other five" if i == 0 else None), zorder=3 if m == "rf" else 2)
    ax.set_title("(a) aggregation + ONNX Runtime", fontsize=6.8, pad=3)
    ax.legend(loc="lower right", bbox_to_anchor=(0.77, 0.03), fontsize=6.2, handlelength=1.2, borderpad=0.25)

    ax = axes[1]
    for st, lab, c, ls in (("sk_dataframe", "DataFrame", GREY, "-"),
                           ("sk_array", "NumPy array", BLUE, "--"),
                           ("onnx", "ONNX", VERM, "-")):
        k = f"radio__rf__{st}"
        if k in S:
            x, f = ecdf(S[k])
            ax.plot(x, f, color=c, ls=ls, lw=1.0, label=lab)
    ax.set_title("(b) RF, three implementations", fontsize=6.8, pad=3)
    ax.legend(loc="center", bbox_to_anchor=(0.47, 0.42), fontsize=6.2, handlelength=1.6, borderpad=0.25)

    for ax in axes:
        ax.set_xscale("log")
        ax.set_yscale("logit")
        ax.set_ylim(0.2, 0.9995)
        ax.set_xlim(8e-3, 100)
        for q, lab in ((0.5, "$p_{50}$"), (0.95, "$p_{95}$"), (0.99, "$p_{99}$")):
            ax.axhline(q, color=LIGHT, lw=0.6, zorder=0)
        ax.axvspan(10, 200, color=LIGHT, lw=0, zorder=0)
        ax.axvline(10, color=INK2, lw=0.7, zorder=1)
        ax.set_xlabel("Per-call latency (ms)")
        ax.set_xticks([0.01, 0.1, 1, 10], ["0.01", "0.1", "1", "10"])
    axes[0].set_yticks([0.5, 0.95, 0.99, 0.999], ["0.5", "0.95", "0.99", "0.999"])
    axes[0].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axes[0].set_ylabel("Cumulative probability")
    axes[0].text(12, 0.25, "$B = 10$ ms", fontsize=6.2, color=INK2, rotation=90,
                 va="bottom", ha="left")
    fig.subplots_adjust(wspace=0.08)
    save(fig, "fig_rev_latency")


def main() -> int:
    style()
    lat = (fig_latency_cdf if (RES / "EXP-060/raw/latency_samples.npz").exists()
           else fig_latency)
    for fn in (fig_leakage, fig_benign, fig_transfer, fig_shift, fig_threshold,
               fig_prevalence, fig_sensitivity, fig_reliability, lat):
        fn()
    return 0


if __name__ == "__main__":
    sys.exit(main())
