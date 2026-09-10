"""20_charts_final.py -- figures for the final presentation model.

Reads outputs/final_model.json. Writes charts/fig31_predicted_vs_actual.png.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

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
    with open(os.path.join(HERE, "outputs", "final_model.json"),
              encoding="utf-8") as f:
        R = json.load(f)
    act = np.exp(np.array(R["actual"]))     # back to MPG for readability
    fit = np.exp(np.array(R["fitted"]))
    r2 = R["main"]["r2"]

    fig, ax = plt.subplots(figsize=(9.5, 8))
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    lim = (8, 65)
    ax.plot(lim, lim, color=INK2, lw=1.2)
    ax.scatter(fit, act, s=16, c=S1, alpha=0.45, edgecolors=SURFACE,
               linewidths=0.5)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Predicted MPG (from weight, horsepower, footprint, hybrid)")
    ax.set_ylabel("Actual MPG (EPA 2-cycle combined)")
    ax.text(11, 58, f"R² = {r2}\nn = {R['main']['n']:,} model types\n"
            "4 predictors, all p < 0.001", fontsize=12, color=INK,
            fontweight="bold")
    ax.text(44, 39, "45° line:\nperfect prediction", fontsize=9.5,
            color=INK2)
    ax.set_title("One dot per MY2024 combustion model type; predictions from "
                 "the log-log OLS fit", loc="left", fontsize=10.5, color=INK2,
                 pad=8)
    fig.suptitle("Four numbers predict a vehicle's fuel economy within a few MPG",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.012, "EPA MY2024 compliance data (files 3+4 joined). "
             "ln(MPG) ~ ln(weight) + ln(HP) + footprint + hybrid, HC1 SEs. "
             "Combustion only; EVs measure MPGe.", fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))
    fig.savefig(os.path.join(CHARTS, "fig31_predicted_vs_actual.png"), dpi=150)
    print("wrote fig31")


if __name__ == "__main__":
    main()
