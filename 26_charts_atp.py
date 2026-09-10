"""26_charts_atp.py -- acquisition-cost figure from the KBB/Cox ATP table.

Reads outputs/atp_july2026.csv. Writes charts/fig37_acquisition_cost.png.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S2 = "#2a78d6", "#eb6834"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE = "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "font.size": 11,
})


def main():
    os.makedirs(CHARTS, exist_ok=True)
    df = pd.read_csv(os.path.join(HERE, "outputs", "atp_july2026.csv"))
    rows = df[df.kind.isin(["segment", "category", "brand"])].copy()
    rows = rows[rows.label != "Industry (all new vehicles)"]
    rows["short"] = rows.label.replace({
        "EV (battery electric)": "EV average",
        "ICE+ (non-EV, incl. hybrids)": "ICE+ average (incl. hybrids)",
    })
    rows = rows.sort_values("atp_usd")
    industry = int(df.loc[df.label.str.startswith("Industry"), "atp_usd"].iloc[0])

    fig, ax = plt.subplots(figsize=(11, 6.6))
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="y", visible=False)
    colors = {"segment": BASELINE, "brand": "#9ec5f4", "category": S1}
    for i, (_, r) in enumerate(rows.iterrows()):
        c = colors[r.kind]
        if r.short.startswith("ICE+"):
            c = S2
        ax.barh(i, r.atp_usd, height=0.6, color=c)
        ax.text(r.atp_usd + 600, i, f"\\${r.atp_usd:,}", va="center",
                fontsize=10, color=INK2)
    ax.axvline(industry, color=INK2, lw=1.4, ls=(0, (4, 2)))
    ax.text(industry + 500, len(rows) - 0.4,
            f"industry average \\${industry:,}", fontsize=9.5, color=INK2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows.short, fontsize=10.5)
    ax.set_xlim(0, 78000)
    ax.set_xlabel("Average transaction price, July 2026 (price actually paid)")
    ax.set_title("Blue: EV figures. Orange: the non-EV average (hybrids "
                 "included; KBB publishes no hybrid-only ATP). Gray: "
                 "conventional segments.", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("What Americans actually paid in July 2026: the EV premium is "
                 "\\$6,477", x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.012, "Source: Kelley Blue Book / Cox Automotive, July "
             "2026 ATP report and EV Market Monitor (snapshots in external/). "
             "ATP reflects sales mix and incentives, not MSRP.",
             fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig37_acquisition_cost.png"), dpi=150)
    print("wrote fig37")


if __name__ == "__main__":
    main()
