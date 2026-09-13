"""34_charts_pooled.py -- charts for the pooled (all-powertrain) equation.

Reads outputs/my2024_pooled.csv and outputs/pooled_model.json (stage 33).

  fig49_weight_vs_mpgeq.png     weight vs MPG-equivalent, three powertrains
  fig50_hp_vs_mpgeq.png         horsepower vs MPG-equivalent, same
  fig51_pooled_pred_vs_actual   predicted vs actual with the 95% prediction
                                band and the largest studentized residuals
                                labelled
  fig52_merged_dummy_fails.png  why one "electrified" dummy cannot work:
                                residuals by powertrain, spec C vs spec F
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
CHARTS = os.path.join(HERE, "charts")

S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUT, GRID, BASELINE, WASH = "#898781", "#e1e0d9", "#c3c2b7", "#f0efec"
PT = [("gas_diesel", INK2, "Gasoline / diesel"), ("hybrid", S3, "Hybrid"),
      ("bev", S1, "Battery-electric (MPGe)")]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "xtick.color": MUT, "ytick.color": MUT,
    "text.color": INK, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "font.size": 11,
})


def clean_ax(ax):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)


def scatter(d, xcol, xlabel, headline, sub, fname, logx=False):
    fig, ax = plt.subplots(figsize=(11, 6.6))
    clean_ax(ax)
    for key, c, lab in PT:
        s = d[d.powertrain == key]
        ax.scatter(s[xcol], s.fe, s=22, c=c, alpha=0.55, edgecolors=SURFACE,
                   linewidths=0.6, label=f"{lab} (n = {len(s):,})")
    if logx:
        ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_yticks([10, 20, 30, 50, 80, 120, 180])
    ax.set_yticklabels(["10", "20", "30", "50", "80", "120", "180"])
    lg = ax.legend(frameon=False, fontsize=10, loc="upper right")
    for t in lg.get_texts():
        t.set_color(INK2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Unadjusted 2-cycle combined MPG or MPGe (log scale)")
    ax.set_title(sub, loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle(headline, x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.012, "EPA MY2024 compliance FE file, one dot per model "
             "type; BEV horsepower from the EPA MY2024 Test Car List "
             "(reports/33_pooled_model.md).", fontsize=8.5, color=MUT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, fname), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(CHARTS, exist_ok=True)
    d = pd.read_csv(os.path.join(OUT, "my2024_pooled.csv"))
    j = json.load(open(os.path.join(OUT, "pooled_model.json"), encoding="utf-8"))
    F = j["specs"]["F"]
    ew, eh = -F["coef"]["ln_weight"], -F["coef"]["ln_hp"]

    scatter(d, "wt", "CAFE inertia weight (lbs)",
            f"Heavier is thirstier for every powertrain: 10% more weight costs {ew*10:.1f}% of MPG",
            f"Three parallel bands, one slope: the pooled weight elasticity is -{ew:.3f} with power and powertrain held fixed",
            "fig49_weight_vs_mpgeq.png")
    scatter(d, "hp", "Rated horsepower (log scale)",
            f"Power costs economy: 10% more horsepower costs {eh*10:.1f}% of MPG",
            f"Log-log axes turn the power law into a line; pooled HP elasticity -{eh:.3f}",
            "fig50_hp_vs_mpgeq.png", logx=True)

    # ---- predicted vs actual with 95% band and outliers -------------------
    fitted = np.exp(np.array(j["fitted_F"]))
    actual = np.exp(np.array(j["actual_F"]))
    pt = np.array(j["powertrain_F"])
    band = j["prediction_band_F"]["band95_factor"]
    fig, ax = plt.subplots(figsize=(11, 6.6))
    clean_ax(ax)
    lim = np.array([9, 220])
    ax.fill_between(lim, lim / band, lim * band, color="#dbe8f8", alpha=0.6,
                    zorder=0, label=f"95% prediction band (x/÷ {band:.2f})")
    ax.plot(lim, lim, color=BASELINE, lw=1.2, zorder=1)
    for key, c, lab in PT:
        m = pt == key
        ax.scatter(fitted[m], actual[m], s=20, c=c, alpha=0.55,
                   edgecolors=SURFACE, linewidths=0.6, label=lab, zorder=2)
    slots_neg = [0.62, 0.55, 0.62, 0.55, 0.62]
    slots_pos = [0.42, 0.36, 0.42, 0.36, 0.42]
    ni = pi = 0
    for o in j["outliers_F"][:5]:
        name = o["carline"].replace("&quot;", '"')
        if o["studentized_resid"] < 0:
            xt, yt = o["predicted"] * slots_neg[ni], o["actual"] * 0.74
            ni += 1
        else:
            xt, yt = o["predicted"] * slots_pos[pi], o["actual"] * 0.90
            pi += 1
        ax.annotate(name, xy=(o["predicted"], o["actual"]), xytext=(xt, yt),
                    fontsize=8.5, color=INK2, ha="center",
                    arrowprops=dict(arrowstyle="-", color=MUT, lw=0.7))
    ax.set_xscale("log")
    ax.set_yscale("log")
    for a in (ax.xaxis, ax.yaxis):
        a.set_major_formatter(matplotlib.ticker.ScalarFormatter())
        a.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xticks([10, 20, 30, 50, 80, 120, 180])
    ax.set_yticks([10, 20, 30, 50, 80, 120, 180])
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_xlabel("Predicted MPG or MPGe from the four-variable equation")
    ax.set_ylabel("Actual (EPA unadjusted 2-cycle combined)")
    lg = ax.legend(frameon=False, fontsize=10, loc="upper left")
    for t in lg.get_texts():
        t.set_color(INK2)
    ax.set_title(f"One dot per MY2024 model type (n = {F['n']:,}); "
                 f"{j['prediction_band_F']['share_inside_95']:.0%} of dots fall "
                 "inside the band; the five largest studentized residuals are named",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle(f"What R² = {F['r2']:.3f} looks like: four numbers predict "
                 "economy for gas, hybrid, and electric alike",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.012, "Band = predicted x/÷ exp(1.96 s), s = residual SD in "
             "logs; leverage ignored. reports/33_pooled_model.md.",
             fontsize=8.5, color=MUT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig51_pooled_pred_vs_actual.png"), dpi=150)
    plt.close(fig)

    # ---- why a merged dummy fails ---------------------------------------
    C, Fm = j["specs"]["C"]["mean_resid_by_powertrain"], F["mean_resid_by_powertrain"]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    clean_ax(ax)
    ax.grid(axis="x", visible=False)
    keys = [k for k, _, _ in PT]
    labs = [lab for _, _, lab in PT]
    x = np.arange(3)
    ax.bar(x - 0.18, [100 * (np.exp(C[k]) - 1) for k in keys], 0.36, color=S2,
           label=f"one merged 'electrified' dummy (spec C, R² = {j['specs']['C']['r2']:.2f})")
    ax.bar(x + 0.18, [100 * (np.exp(Fm[k]) - 1) for k in keys], 0.36, color=S1,
           label=f"hybrid and BEV as separate levels (final, R² = {F['r2']:.3f})")
    ax.axhline(0, color=BASELINE, lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labs)
    ax.set_ylabel("Mean actual-vs-predicted gap by powertrain (%)")
    for i, k in enumerate(keys):
        v = 100 * (np.exp(C[k]) - 1)
        ax.text(i - 0.18, v + (3 if v >= 0 else -9), f"{v:+.0f}%", ha="center",
                fontsize=10, color=S2, fontweight="bold")
        ax.text(i + 0.18, 3, "0%", ha="center", fontsize=10, color=S1,
                fontweight="bold")
    ax.text(0.62, 48, "Blue bars are zero by construction:\nseparate hybrid "
            "and BEV levels leave no\nsystematic gap in any group. One merged\n"
            "dummy leaves both.", fontsize=10.5, color=INK2, ha="center")
    lg = ax.legend(frameon=False, fontsize=10, loc="upper left")
    for t in lg.get_texts():
        t.set_color(INK2)
    hyb = 100 * (np.exp(F["coef"]["hybrid"]) - 1)
    bev = 100 * (np.exp(F["coef"]["bev"]) - 1)
    ax.set_title(f"A hybrid is +{hyb:.0f}% at equal weight and power; a BEV is "
                 f"+{bev:.0f}%. One average premium mis-prices both",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("Why hybrids and BEVs cannot share one dummy: the premiums "
                 "differ eighteen-fold", x=0.01, ha="left", fontsize=15,
                 fontweight="bold")
    fig.text(0.01, 0.012, "Mean residual by group, exponentiated to percent; "
             "reports/33_pooled_model.md specs C and F.", fontsize=8.5, color=MUT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig52_merged_dummy_fails.png"), dpi=150)
    plt.close(fig)
    print("wrote fig49-fig52")


if __name__ == "__main__":
    main()
