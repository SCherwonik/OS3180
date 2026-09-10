"""09_charts_extra.py -- safety dividend, sales-vs-production check, scandal
overlay. Reads outputs/context_extra.csv, outputs/analysis_clean.csv,
external/events_timeline.csv. Writes charts/fig13..fig15.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S2, S3, S4, S5 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE = "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "grid.linestyle": "-", "xtick.color": MUTED,
    "ytick.color": MUTED, "text.color": INK, "axes.labelcolor": INK2,
    "axes.titlecolor": INK, "font.size": 11,
})


def style_ax(ax):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)
    ax.margins(x=0.01)


def legend(ax, handles, labels, **kw):
    lg = ax.legend(handles, labels, frameon=False, fontsize=9.5, **kw)
    for t in lg.get_texts():
        t.set_color(INK2)


def lh(c, ls="-"):
    return plt.Line2D([], [], color=c, lw=2, ls=ls)


def footnote(fig, text):
    fig.text(0.01, 0.012, text, fontsize=8.5, color=MUTED)


def save(fig, name):
    fig.savefig(os.path.join(CHARTS, name), dpi=150)
    plt.close(fig)


def fig13(ctx):
    d = ctx.dropna(subset=["fatality_rate_per_100m_vmt"]).sort_values("year")
    d = d[d.year >= 1975]
    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.plot(d.year, d.fatality_rate_per_100m_vmt, color=S1, lw=2,
            marker="o", ms=4, mfc=S1, mec=S1)
    ax.set_ylim(0, 3.6)
    ax.annotate("1975: 3.35 deaths\nper 100M miles", xy=(1975, 3.35),
                xytext=(1978.5, 3.05), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("2010: 1.11 (record low era)", xy=(2010, 1.112),
                xytext=(1999, 0.55), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("2021-24: reversal to ~1.2-1.4\ndespite ever-safer vehicles",
                xy=(2022, 1.35), xytext=(2007.5, 2.15), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Motor-vehicle deaths per 100 million vehicle-miles "
                 "(FARS 30-day definition; 5-year steps before 1990)",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The safety dividend: cars got heavier, faster, and 3x safer per mile",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Source: BTS National Transportation Statistics Table 2-17 "
                  "(FARS/FHWA). Rate as published by BTS.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig13_safety_dividend.png")


def fig14(ctx, ac):
    prod = ac[(ac.manufacturer == "All") & (ac.vehicle_type == "All Truck")
              ].sort_values("model_year")
    sales = ctx.dropna(subset=["lt_share_of_sales"]).sort_values("year")

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.plot(prod.model_year, prod.production_share, color=S3, lw=2)
    ax.plot(sales.year, sales.lt_share_of_sales, color=S2, lw=2)
    ax.set_ylim(0, 0.9)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%"])
    ax.text(1996, 0.47, "share of SALES\n(BEA, calendar year)", color=S2,
            fontweight="bold", fontsize=10.5)
    ax.text(2002, 0.32, "share of PRODUCTION\n(EPA, model year)", color=S3,
            fontweight="bold", fontsize=10.5)
    legend(ax, [lh(S3), lh(S2)],
           ["Truck share of production (EPA Trends, model year)",
            "Light-truck share of sales (BEA, calendar year)"],
           loc="upper left")
    ax.set_title("Two independent sources, one inversion", loc="left",
                 fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The truck takeover is real in both the factory and the showroom",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Sources: EPA Trends (model-year production); BEA via FRED "
                  "(calendar-year sales, SAAR means). Different populations; "
                  "approximate alignment by design.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    save(fig, "fig14_sales_vs_production.png")


def fig15(ac, events):
    mfg = ac[(ac.regulatory_class == "All") & (ac.vehicle_type == "All")]
    lines = [("Hyundai", S1), ("Kia", S5), ("VW", S2)]

    fig, ax = plt.subplots(figsize=(11, 6.4))
    style_ax(ax)
    ends = []
    for name, c in lines:
        d = mfg[(mfg.manufacturer == name) & (mfg.model_year >= 2000)
                ].sort_values("model_year")
        fin = d[~d.is_preliminary]
        ax.plot(fin.model_year, fin.real_world_mpg, color=c, lw=2)
        bridge = d[d.model_year >= fin.model_year.max()]
        ax.plot(bridge.model_year, bridge.real_world_mpg, color=c, lw=2,
                ls=(0, (3, 2)))
        last = d.iloc[-1]
        ax.plot(last.model_year, last.real_world_mpg, "o", mfc=SURFACE,
                mec=c, mew=1.6, ms=6)
        ends.append((name, c, last.model_year, last.real_world_mpg))
    # End labels, nudged apart when endpoints crowd within 0.6 MPG.
    ends.sort(key=lambda e: e[3])
    ys = []
    for name, c, x, y in ends:
        yy = y
        while any(abs(yy - p) < 0.6 for p in ys):
            yy += 0.6
        ys.append(yy)
        ax.text(x + 0.3, yy, name, color=c, fontweight="bold",
                fontsize=10.5, va="center")
    for yr, label, ytext in [
        (2012.84, "Nov 2012: EPA forces Hyundai/Kia\nmileage restatement", 21.2),
        (2015.72, "Sept 2015: VW diesel\nnotice of violation", 32.3),
    ]:
        ax.axvline(yr, color=MUTED, lw=1.0)
        ax.text(yr + 0.15, ytext, label, fontsize=9, color=INK2, va="top")
    ax.set_ylim(19, 33)
    legend(ax, [lh(c) for _, c in lines], [n for n, _ in lines],
           loc="upper left")
    ax.set_title("Real-world MPG, manufacturers touched by reported-economy "
                 "scandals, 2000-2025", loc="left", fontsize=10.5, color=INK2,
                 pad=8)
    fig.suptitle("Where the scandals landed on the curves",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Sources: EPA Automotive Trends; event dates: EPA press releases "
                  "(external/events_timeline.csv). Scandals hit window labels, "
                  "not this EPA-verified series. Dashed: preliminary 2025.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    save(fig, "fig15_scandal_overlay.png")


def main():
    os.makedirs(CHARTS, exist_ok=True)
    ctx = pd.read_csv(os.path.join(HERE, "outputs", "context_extra.csv"))
    ac = pd.read_csv(os.path.join(HERE, "outputs", "analysis_clean.csv"))
    events = pd.read_csv(os.path.join(HERE, "external", "events_timeline.csv"))
    fig13(ctx)
    fig14(ctx, ac)
    fig15(ac, events)
    print("wrote fig13, fig14, fig15")


if __name__ == "__main__":
    main()
