"""11_charts_stats.py -- figures for the six statistical analyses.

Reads outputs/stats_results.json (produced by 10_stats.py).
Writes charts/fig16..fig21.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S2, S3, S4, S5, S6 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE, WASH = "#898781", "#e1e0d9", "#c3c2b7", "#f0efec"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

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
    ax.margins(x=0.02)


def footnote(fig, text):
    fig.text(0.01, 0.012, text, fontsize=8.5, color=MUTED)


def save(fig, name):
    fig.savefig(os.path.join(CHARTS, name), dpi=150)
    plt.close(fig)


def fig16(R):
    c = R["changepoints"]
    t = np.array(c["years"], dtype=float)
    y = np.array(c["mpg"])
    breaks, beta = c["selected_breaks"], np.array(c["beta"])
    X = np.column_stack([np.ones_like(t), t]
                        + [np.clip(t - b, 0, None) for b in breaks])
    yhat = X @ beta

    fig, ax = plt.subplots(figsize=(11, 6.4))
    style_ax(ax)
    ax.plot(t, y, color=BASELINE, lw=1.4)
    ax.plot(t, y, "o", ms=3.5, color=S1)
    ax.plot(t, yhat, color=S2, lw=2.2)
    for b, ch in zip(breaks, c["chow"]):
        ax.axvline(b, color=MUTED, lw=1.0)
        ax.text(b + 0.3, y.min() + 0.4,
                f"{b}\nChow F={ch['F']}\np={ch['p']:.0e}",
                fontsize=9, color=INK2, va="bottom")
    ax.text(1977, 26.5, "piecewise-linear fit,\nbreaks chosen by BIC",
            color=S2, fontsize=10, fontweight="bold")
    bic2, bic3 = c["bic_by_num_breaks"]["2"], c["bic_by_num_breaks"]["3"]
    ax.set_title("Fleet real-world MPG with BIC-selected structural breaks. "
                 f"BIC: 2 breaks {bic2}, 3 breaks {bic3} (narrow win for 3).",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The algorithm found the eras on its own: breaks at "
                 f"{', '.join(str(b) for b in breaks)}",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Exhaustive SSE search over break locations (min segment 6 yrs), "
                  "continuous piecewise-linear model, order by BIC; Chow tests at "
                  "selected breaks. Data: EPA Trends, final years only.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig16_changepoints.png")


def fig17(R):
    d = R["distribution"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5.8))
    for a in (a1, a2):
        style_ax(a)

    grid = np.array(d["grid"])
    a1.plot(grid, d["F_offered"], color=S1, lw=2)
    a1.plot(grid, d["F_bought"], color=S2, lw=2)
    a1.text(12.5, 0.55, "offered\n(each model type\ncounted once)", color=S1,
            fontsize=9.5, fontweight="bold")
    a1.text(33.5, 0.45, "bought\n(production-\nweighted)", color=S2,
            fontsize=9.5, fontweight="bold")
    a1.set_xlabel("5-cycle adjusted combined MPG")
    a1.set_title(f"ECDFs: KS D = {d['ks_D']}, Wasserstein = "
                 f"{d['wasserstein_mpg']} MPG.\nMedians: offered "
                 f"{d['quantiles']['0.5']['offered']}, bought "
                 f"{d['quantiles']['0.5']['bought']}", loc="left",
                 fontsize=10, color=INK2)

    x = np.array(d["lorenz_cum_carlines"])
    yv = np.array(d["lorenz_cum_volume"])
    a2.plot([0, 1], [0, 1], color=BASELINE, lw=1.2)
    a2.plot(x, yv, color=S1, lw=2)
    a2.fill_between(x, yv, x, color=WASH)
    a2.text(0.42, 0.87, f"Gini = {d['gini_carline_volume']}", color=INK,
            fontsize=12, fontweight="bold")
    a2.text(0.35, 0.55, f"{d['carlines_for_80pct']} of {d['n_carlines']} "
            f"carlines\n= 80% of production", color=INK2, fontsize=9.5)
    a2.set_xlabel("Cumulative share of carlines (largest first)")
    a2.set_title("Lorenz curve of MY2024 production volume", loc="left",
                 fontsize=10, color=INK2)

    fig.suptitle("Buyers don't sample the catalog: a 3.5-MPG shift and a long tail nobody buys",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "MY2024 combustion model types, EPA compliance data. Weighted "
                  "ECDF/quantiles; Gini over carline production volumes.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.90))
    save(fig, "fig17_distribution_shift.png")


def fig18(R):
    techs = [("Turbo", S2), ("GDI", S3), ("CVT", S4),
             ("Hybrid (HEV)", S5), ("BEV", S6)]
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), sharex=True)
    axes = axes.ravel()
    for ax, (name, c) in zip(axes, techs):
        style_ax(ax)
        f = R["diffusion"][name]
        t = np.array(f["years"], dtype=float)
        y = np.array(f["share"])
        ax.plot(t, y, "o", ms=3, color=c)
        tt = np.linspace(1975, 2040, 200)
        fit = f["L"] / (1 + np.exp(-f["k"] * (tt - f["t0"])))
        obs = tt <= t.max()
        ax.plot(tt[obs], fit[obs], color=c, lw=2)
        ax.plot(tt[~obs], fit[~obs], color=c, lw=2, ls=(0, (3, 2)), alpha=0.6)
        ax.set_ylim(0, 1)
        ax.set_title(f"{name}", loc="left", fontsize=11, pad=4)
        ax.text(0.03, 0.83, f"k = {f['k']}\n10%→90%: {f['takeover_years_10_90']} yrs"
                + (f"\nmidpoint {f['t0']:.0f}" if f.get("t0") else ""),
                transform=ax.transAxes, fontsize=9, color=INK2)
    ax = axes[5]
    style_ax(ax)
    ax.grid(visible=False)
    ax.set_axis_off()
    ax.text(0.02, 0.85, "Same curve, different clocks:",
            fontsize=11, fontweight="bold", color=INK)
    ax.text(0.02, 0.70,
            "GDI took over 2.1x faster than turbo\n"
            "(k = 0.61 vs 0.29).\n\n"
            "BEV is the honest ambiguity: the fit\n"
            "put its ceiling at L = 0.10, i.e. the\n"
            "data so far cannot distinguish 'early\n"
            "S-curve' from 'low plateau'. Its k and\n"
            "L carry the widest bootstrap CIs;\n"
            "believe the dashes least.\n\n"
            "HEV is the slow burner: fitted\n"
            "midpoint 2036, still climbing.",
            fontsize=9.5, color=INK2, va="top")
    fig.suptitle("Every technology is the same S-curve with a different rate constant",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Logistic fits L/(1+exp(-k(t-t0))) by nonlinear least squares; "
                  "ceiling L estimated, not assumed. Dashed = extrapolation beyond "
                  "data. CIs in reports/10_statistics.md.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    save(fig, "fig18_diffusion_fits.png")


def fig19(R):
    s = R["spurious"]
    g = np.array(s["gas"])
    tr = np.array(s["truck"])
    yrs = np.array(s["years"])

    fig, ax = plt.subplots(figsize=(11, 6.4))
    style_ax(ax)
    ax.grid(axis="x", visible=True)
    sc = ax.scatter(g, tr, c=yrs, cmap=matplotlib.colors.LinearSegmentedColormap
                    .from_list("seq", SEQ), s=42, edgecolors=SURFACE,
                    linewidths=0.8)
    cb = fig.colorbar(sc, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("year", color=INK2)
    cb.ax.tick_params(color=MUTED, labelcolor=MUTED)
    cb.outline.set_visible(False)
    lv = s["levels"]
    ax.text(0.02, 0.95,
            f"levels: r² = {lv['r2']} (r = -0.08), p = {lv['p']:.2f}\n"
            f"first differences: r² = {s['diffs']['r2']}, p = {s['diffs']['p']:.2f}",
            transform=ax.transAxes, fontsize=10.5, color=INK, va="top",
            bbox=dict(facecolor=WASH, edgecolor="none", pad=6))
    ax.set_xlabel("Real gasoline price (2024 $/gal)")
    ax.set_ylabel("Truck share of production")
    ax.set_title("Each dot is a year, colored by time. The vertical drift is the "
                 "trend; the horizontal scatter is the price. They barely touch.",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The correlation that wasn't: gas prices explain almost none of the truck takeover",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "1976-2024 annual. The overlay chart (fig5) invites a causal read; "
                  "the scatter shows secular trend, not price response. Lesson: "
                  "eyeballed co-movement is not association.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig19_correlation_that_wasnt.png")


def fig20(R):
    g = R["fatality_glm"]
    yrs = np.array(g["years"])
    rate = np.array(g["rate"])
    fitted = np.array(g["fitted_rate"])

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.plot(yrs, rate, "o-", ms=4, lw=1.6, color=S1)
    ax.plot(yrs, fitted, color=INK2, lw=1.8, ls=(0, (5, 2)))
    ax.axvspan(2019.5, 2024.5, color=WASH, zorder=0)
    p21 = g["predictions_2020s"]["2021"]
    ax.annotate(f"2021: {p21['observed']:,} deaths observed,\n"
                f"{p21['expected']:,} expected from trend\n"
                f"(+{p21['excess']:,} excess, z = {p21['z']})",
                xy=(2021, rate[list(yrs).index(2021)]),
                xytext=(2004.5, 1.62), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.text(1997, 1.28, "quasi-Poisson trend, fit 1990-2019\n"
            f"({g['annual_trend_pct']}% per year, dispersion φ = "
            f"{g['dispersion_phi']})", fontsize=9.5, color=INK2)
    ax.set_ylim(0.9, 2.2)
    ax.set_title("Deaths per 100M vehicle-miles: observed vs pre-2020 GLM trend "
                 "(log-VMT offset)", loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The pandemic-era fatality reversal is statistically real, not noise",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Poisson GLM via IRLS, exposure offset log(VMT/100M), "
                  "quasi-Poisson SE scaling. Data: BTS Table 2-17. Even at "
                  "dispersion 115, the 2021 excess is six standard errors out.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig20_fatality_glm.png")


def fig21(R):
    v = R["convergence"]
    yrs = np.array(v["years"])
    sd = np.array(v["sd"])

    fig, ax = plt.subplots(figsize=(11, 6.0))
    style_ax(ax)
    ax.plot(yrs, sd, color=S1, lw=2)
    ax.set_ylim(0, 7)
    ax.annotate(f"1977 peak: SD {v['sd_max']} MPG\n(fuel-crisis scramble, "
                "manufacturers far apart)", xy=(v["sd_max_year"], v["sd_max"]),
                xytext=(1984, 6.3), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("early 1990s-2008: tightest field,\nSD under 2 MPG",
                xy=(1991, 1.81), xytext=(1994.5, 0.8), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate(f"2024: SD back to {v['sd_2024']} MPG\n(hybrid-heavy vs "
                "truck-heavy strategies\npull the field apart again)",
                xy=(2024, v["sd_2024"]), xytext=(2007, 4.6), fontsize=10,
                color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Cross-sectional SD of real-world MPG across the 8 manufacturers "
                 "present all 50 years (Ford, GM, Honda, Mazda, Nissan, "
                 "Stellantis, Toyota, VW)", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("The field converged for two decades, then electrification split it again",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Balanced panel avoids composition effects from entrants "
                  "(Tesla, Hyundai/Kia excluded by construction). Data: EPA Trends.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig21_convergence.png")


def main():
    os.makedirs(CHARTS, exist_ok=True)
    with open(os.path.join(HERE, "outputs", "stats_results.json"),
              encoding="utf-8") as f:
        R = json.load(f)
    fig16(R)
    fig17(R)
    fig18(R)
    fig19(R)
    fig20(R)
    fig21(R)
    print("wrote fig16-fig21")


if __name__ == "__main__":
    main()
