"""27_charts_range.py -- BEV range regressions (three windows, two grains)
and the hydrogen FCEV profile. Three separate figures.

  fig38_range_fits.png    config-level range ~ year, windows 2000/2010/2020
  fig39_median_fits.png   median-range-per-year ~ year, same windows
  fig40_fcev.png          hydrogen FCEV range and catalog breadth

Reads outputs/catalog_fegov.csv.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S2, S3, S5 = "#2a78d6", "#eb6834", "#1baf7a", "#e87ba4"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE = "#898781", "#e1e0d9", "#c3c2b7"
WIN_COLORS = {2000: S1, 2010: S3, 2020: S2}

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "font.size": 11,
})


def style_ax(ax):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", visible=False)


def footnote(fig, text):
    fig.text(0.01, 0.012, text, fontsize=8.5, color=MUTED)


def save(fig, name):
    fig.savefig(os.path.join(CHARTS, name), dpi=150)
    plt.close(fig)


def load():
    v = pd.read_csv(os.path.join(HERE, "outputs", "catalog_fegov.csv"),
                    low_memory=False)
    bev = v[(v.fuelType1 == "Electricity") & (v["range"] > 0) & (v.year >= 2000)]
    fcev = v[(v.fuelType1 == "Hydrogen") & (v["range"] > 0)]
    return bev, fcev


def fig38(bev):
    fig, ax = plt.subplots(figsize=(11, 6.6))
    style_ax(ax)
    jitter = (np.random.default_rng(3).random(len(bev)) - 0.5) * 0.6
    ax.scatter(bev.year + jitter, bev["range"], s=10, c=BASELINE,
               edgecolors="none")
    lines = []
    for y0, c in WIN_COLORS.items():
        d = bev[bev.year >= y0]
        r = stats.linregress(d.year, d["range"])
        xs = np.array([y0, 2027])
        ax.plot(xs, r.intercept + r.slope * xs, color=c, lw=2.4)
        lines.append(f"from {y0}: R² = {r.rvalue**2:.3f}, "
                     f"{r.slope:+.1f} mi/yr, n = {len(d):,}")
    for i, (txt, c) in enumerate(zip(lines, WIN_COLORS.values())):
        ax.text(2000.5, 500 - 28 * i, txt, fontsize=11, color=c,
                fontweight="bold")
    ax.set_ylim(0, 530)
    ax.set_ylabel("EPA-rated range (miles)")
    ax.set_title("One dot per BEV catalog configuration; each line is an OLS "
                 "fit of range on year over its window", loc="left",
                 fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("BEV range on year, configuration level: R² collapses as the "
                 "window shortens", x=0.01, ha="left", fontsize=15,
                 fontweight="bold")
    footnote(fig, "fueleconomy.gov catalog. Within-year spread (city cars to "
                  "500-mile sedans) dominates the trend at this grain; "
                  "compare fig39. Horizontal jitter for visibility.")
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    save(fig, "fig38_range_fits.png")


def fig39(bev):
    med = bev.groupby("year")["range"].median().reset_index()
    fig, ax = plt.subplots(figsize=(11, 6.6))
    style_ax(ax)
    ax.plot(med.year, med["range"], "o", ms=6, color=INK2)
    lines = []
    for y0, c in WIN_COLORS.items():
        d = med[med.year >= y0]
        r = stats.linregress(d.year, d["range"])
        xs = np.array([y0, 2027])
        ax.plot(xs, r.intercept + r.slope * xs, color=c, lw=2.4)
        lines.append(f"from {y0}: R² = {r.rvalue**2:.3f}, "
                     f"{r.slope:+.1f} mi/yr, {len(d)} yearly medians")
    for i, (txt, c) in enumerate(zip(lines, WIN_COLORS.values())):
        ax.text(2000.5, 420 - 24 * i, txt, fontsize=11, color=c,
                fontweight="bold")
    ax.set_ylim(0, 450)
    ax.set_ylabel("Median EPA-rated BEV range (miles)")
    ax.set_title("One dot per model year (median across configurations); "
                 "same three windows as fig38", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("The same data at median grain: R² above 0.80 in every window",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "fueleconomy.gov catalog. Aggregating to yearly medians "
                  "removes the within-year mix, so the trend dominates: the "
                  "R² gap between fig38 and fig39 is grain, not physics.")
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    save(fig, "fig39_median_fits.png")


def fig40(bev, fcev):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.4), sharex=True,
                                 height_ratios=[2, 1])
    for a in (a1, a2):
        style_ax(a)
    fmed = fcev.groupby("year")["range"].median()
    bmed = bev.groupby("year")["range"].median()
    a1.plot(bmed.index, bmed.values, color=S1, lw=2)
    a1.plot(fmed.index, fmed.values, "o-", color=S5, lw=2, ms=5)
    a1.set_xlim(2010, 2027)
    a1.set_ylim(0, 450)
    a1.text(2011, 300, "Hydrogen FCEV median", color=S5, fontweight="bold",
            fontsize=10.5)
    a1.text(2013.5, 90, "BEV median", color=S1, fontweight="bold",
            fontsize=10.5)
    a1.set_title("Median EPA-rated range (miles)", loc="left", fontsize=11,
                 pad=6)
    counts = fcev.groupby("year").size()
    a2.bar(counts.index, counts.values, color=S5, width=0.7)
    a2.set_title("Hydrogen configurations offered per year (three nameplates "
                 "ever: Mirai, Nexo/Tucson FC, Clarity FC)", loc="left",
                 fontsize=11, pad=6)
    a2.set_ylim(0, 8)
    fig.suptitle("Hydrogen never had a range problem; it had a catalog problem",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "fueleconomy.gov catalog. FCEV median 65 MPGe, 357-mi "
                  "range; 3 nameplates vs 266 BEV configs in 2024. No public "
                  "retail H2 price series -> no cost-per-mile computed.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    save(fig, "fig40_fcev.png")


def main():
    os.makedirs(CHARTS, exist_ok=True)
    bev, fcev = load()
    fig38(bev)
    fig39(bev)
    fig40(bev, fcev)
    print("wrote fig38, fig39, fig40")


if __name__ == "__main__":
    main()
