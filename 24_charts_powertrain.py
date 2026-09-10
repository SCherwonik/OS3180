"""24_charts_powertrain.py -- figures for the BEV/Hybrid/Gasoline comparison.

Reads outputs/powertrain_trends.csv.
Writes charts/fig33_cost_trends.png, fig34_label_efficiency.png,
fig35_bev_range.png.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S2, S3, S5 = "#2a78d6", "#eb6834", "#1baf7a", "#e87ba4"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE, WASH = "#898781", "#e1e0d9", "#c3c2b7", "#f0efec"
COLORS = {"BEV": S1, "Gasoline": S2, "Hybrid": S3}
FCEV = S5

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
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)
    ax.margins(x=0.02)


def footnote(fig, text):
    fig.text(0.01, 0.012, text, fontsize=8.5, color=MUTED)


def save(fig, name):
    fig.savefig(os.path.join(CHARTS, name), dpi=150)
    plt.close(fig)


def series(t, grp, col, y0=2011, y1=2026):
    g = t[(t.group == grp) & t.year.between(y0, y1)].sort_values("year")
    return g.year, g[col]


def fig33(t):
    fig, ax = plt.subplots(figsize=(11, 6.4))
    style_ax(ax)
    for grp, c in COLORS.items():
        x, y = series(t, grp, "median_cost_per_mile")
        ax.plot(x, y, color=c, lw=2)
        last = y.iloc[-1]
        ax.text(x.iloc[-1] + 0.25, last, grp, color=c, fontweight="bold",
                fontsize=10.5, va="center")
    ax.set_ylim(0, 0.20)
    ax.set_yticks([0, 0.05, 0.10, 0.15, 0.20])
    ax.set_yticklabels(["$0.00", "$0.05", "$0.10", "$0.15", "$0.20"])
    ax.annotate("2024, per 15,000 miles:\nBEV $1,007 | Hybrid $2,069 | "
                "Gasoline $2,463", xy=(2024, 0.067), xytext=(2013.5, 0.032),
                fontsize=10.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("gap narrows: electricity prices climb\nwhile gas cars improve",
                xy=(2023, 0.062), xytext=(2017.5, 0.095), fontsize=9.5,
                color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Median energy cost per mile at each model year's national "
                 "prices (catalog configurations)", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("Driving on electrons costs half as much, and has for a decade",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "fueleconomy.gov catalog + BLS prices via FRED. Energy only: "
                  "no purchase price, depreciation, or DC-fast premiums. "
                  "PHEV/diesel excluded (reports/23_powertrain.md).")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig33_cost_trends.png")


def fig34(t):
    fig, ax = plt.subplots(figsize=(11, 6.4))
    style_ax(ax)
    for grp, c in COLORS.items():
        x, y = series(t, grp, "median_comb08")
        ax.plot(x, y, color=c, lw=2)
        label = "BEV (MPGe)" if grp == "BEV" else grp + " (MPG)"
        ax.text(x.iloc[-1] + 0.25, y.iloc[-1], label, color=c,
                fontweight="bold", fontsize=10.5, va="center")
    xf, yf = series(t, "FCEV", "median_comb08", y0=2014)
    ax.plot(xf, yf, "o-", color=FCEV, lw=1.8, ms=4)
    ax.text(xf.iloc[-1] + 0.25, yf.iloc[-1], "FCEV (MPGe)", color=FCEV,
            fontweight="bold", fontsize=10.5, va="center")
    ax.set_ylim(0, 130)
    ax.annotate("2018-2020 plateau near 110:\ncatalog was small efficient "
                "sedans\n(~25 configs)", xy=(2019, 110.5),
                xytext=(2011.5, 85), fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("electric trucks and SUVs arrive:\nmedian MPGe falls to 87\n"
                "(266 configs)", xy=(2024, 87.5), xytext=(2019.5, 55),
                fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Median window-sticker combined efficiency by powertrain. "
                 "MPGe is an energy-equivalence unit (33.7 kWh = 1 gal), not "
                 "MPG.", loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The SUV-ification of the EV: median efficiency peaked in 2018",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "fueleconomy.gov catalog, unweighted configuration medians. "
                  "Hybrid MPG falls after 2020 for the same reason: hybrids "
                  "spread into trucks and SUVs. Composition, not regression.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig34_label_efficiency.png")


def fig35(t):
    b = t[(t.group == "BEV") & t.median_range_mi.notna()].sort_values("year")
    h = t[(t.group == "FCEV") & t.median_range_mi.notna()].sort_values("year")
    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.plot(b.year, b.median_range_mi, "o-", color=S1, lw=2, ms=4)
    ax.plot(h.year, h.median_range_mi, "o-", color=FCEV, lw=1.8, ms=4)
    ax.text(h.year.iloc[-1] + 0.3, h.median_range_mi.iloc[-1],
            "FCEV median", color=FCEV, fontweight="bold", fontsize=10,
            va="center")
    for yr, lbl in [(2012, "2012: 82 mi"), (2018, "2018: 213 mi"),
                    (2024, "2024: 283 mi")]:
        r = b[b.year == yr]
        if len(r):
            ax.annotate(lbl, xy=(yr, r.median_range_mi.iloc[0]),
                        xytext=(yr - 2.6, r.median_range_mi.iloc[0] + 26),
                        fontsize=10, color=INK2,
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_ylim(0, 360)
    ax.set_title("Median EPA-rated range of BEV and FCEV configurations "
                 "offered each model year", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("BEV range tripled in twelve years; hydrogen started high "
                 "and stayed there", x=0.01, ha="left", fontsize=15,
                 fontweight="bold")
    footnote(fig, "fueleconomy.gov catalog rated range. Gasoline/hybrid "
                  "driving range is not computable from this catalog (no "
                  "tank-capacity field).")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig35_bev_range.png")


def fig36():
    s = pd.read_csv(os.path.join(HERE, "outputs",
                                 "powertrain_sensitivity.csv"))
    order = ["Gasoline", "Hybrid", "BEV"]
    s = s.set_index("group").loc[order]

    fig, ax = plt.subplots(figsize=(11, 5.6))
    style_ax(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    for i, g in enumerate(order):
        lo, hi = s.loc[g, "annual_low"], s.loc[g, "annual_high"]
        ax.barh(i, hi - lo, left=lo, height=0.5, color=COLORS[g], alpha=0.85)
        ax.text(hi + 40, i, f"\\${lo:,.0f} to \\${hi:,.0f}\n"
                f"(swing \\${hi-lo:,.0f})",
                va="center", fontsize=10, color=INK2)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=11)
    ax.set_xlim(0, 3600)
    ax.set_xlabel("Annual energy cost at 15,000 miles, across observed "
                  "2011-2026 national prices")
    ax.set_title("Bar spans each group's annual cost from its energy's "
                 "cheapest to costliest observed year; 2024 median vehicle "
                 "efficiency held fixed", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("Price-shock exposure: the BEV's worst year beats gasoline's best",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Sensitivity of cost/mile to price = 1/efficiency. Gas "
                  "\\$2.14 to \\$4.09/gal (CV 0.20); electricity \\$0.130 to "
                  "\\$0.194/kWh (CV 0.14). Isolates the price channel only.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.90))
    save(fig, "fig36_price_sensitivity.png")


def main():
    os.makedirs(CHARTS, exist_ok=True)
    t = pd.read_csv(os.path.join(HERE, "outputs", "powertrain_trends.csv"))
    fig33(t)
    fig34(t)
    fig35(t)
    fig36()
    print("wrote fig33-fig36")


if __name__ == "__main__":
    main()
