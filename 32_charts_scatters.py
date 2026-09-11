"""32_charts_scatters.py -- fig9's siblings: weight and horsepower vs MPG.

Same construction as fig9 (one dot per MY2024 carline, median across
configurations, dot area = production volume, passenger vehicles vs light
trucks): charts/fig47_weight_vs_mpg.png, charts/fig48_hp_vs_mpg.png.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S3 = "#2a78d6", "#1baf7a"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUT, GRID, BASELINE = "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "xtick.color": MUT, "ytick.color": MUT,
    "text.color": INK, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "font.size": 11,
})


def scatter(g, xcol, xlabel, headline, sub, fname, elast_note):
    fig, ax = plt.subplots(figsize=(11, 6.6))
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", visible=True)
    for cat, color, label in [("PV", S1, "Passenger vehicles"),
                              ("LT", S3, "Light trucks")]:
        s = g[g.cat == cat]
        ax.scatter(s[xcol], s.fe, s=8 + s.vol / 1200, c=color, alpha=0.55,
                   edgecolors=SURFACE, linewidths=0.8)
    lg = ax.legend([plt.Line2D([], [], marker="o", ls="", mfc=c, mec=SURFACE,
                               ms=9) for c in (S1, S3)],
                   ["Passenger vehicles", "Light trucks"], frameon=False,
                   fontsize=10, loc="upper right")
    for t in lg.get_texts():
        t.set_color(INK2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Unadjusted 2-cycle combined MPG")
    ax.set_title(sub, loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle(headline, x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.012, "EPA MY2024 FE & footprint files, carline medians; "
             "dot area = production volume; gasoline/diesel carlines only. "
             + elast_note, fontsize=8.5, color=MUT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, fname), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(CHARTS, exist_ok=True)
    m = pd.read_csv(os.path.join(HERE, "outputs", "my2024_config.csv"),
                    low_memory=False)
    d = m[(m["src_my24fe_FE_UNIT"] == "MPG")
          & (m["src_my24fe_DRIVE_SOURCE"] == "C")]
    g = d.groupby(["src_my24fe_Carline Mfr Code",
                   "src_my24fe_CARLINE_CODE"]).agg(
        fe=("src_my24fe_UNRD_UNADJ_MT_COMB_FE", "median"),
        wt=("src_my24fe_CAFE Base Level Inertia Weight", "median"),
        hp=("src_my24fe_ENG_RATED_HP", "median"),
        vol=("derived_carline_prod_vol", "first"),
        cat=("src_my24fe_Compliance Category", "first"),
    ).dropna(subset=["fe", "wt", "hp"])

    scatter(g, "wt", "CAFE inertia weight (lbs)",
            "Heavier is thirstier: every 10% of weight costs 3.0% of MPG",
            "One dot per carline, MY2024; the model's weight elasticity is "
            "-0.304 with power and size held fixed",
            "fig47_weight_vs_mpg.png",
            "Elasticity from the stage-19 log-log fit.")
    scatter(g, "hp", "Rated horsepower",
            "Power is the steepest lever: every 10% of HP costs 4.8% of MPG",
            "One dot per carline, MY2024; horsepower carries the largest "
            "elasticity in the model (-0.483)",
            "fig48_hp_vs_mpg.png",
            "Elasticity from the stage-19 log-log fit.")
    print(f"wrote fig47, fig48 (n = {len(g):,} carlines)")


if __name__ == "__main__":
    main()
