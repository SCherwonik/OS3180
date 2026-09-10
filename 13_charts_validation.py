"""13_charts_validation.py -- figures for the validation checks.

Reads outputs/validation_results.json. Writes charts/fig22..fig24.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE, WASH = "#898781", "#e1e0d9", "#c3c2b7", "#f0efec"

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


def fig22(V):
    a = V["A_ton_mpg"]
    t = np.array(a["years"], dtype=float)
    y = np.array(a["ton_mpg"])
    breaks, beta = a["breaks"], np.array(a["beta"])
    X = np.column_stack([np.ones_like(t), t]
                        + [np.clip(t - b, 0, None) for b in breaks])
    yhat = X @ beta

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.axvspan(1987, 2004, color=WASH, zorder=0)
    ax.plot(t, y, "o", ms=3.5, color=S1)
    ax.plot(t, yhat, color=S2, lw=2.2)
    trough = [s for s in a["segment_slopes"] if s["from"] == 1983][0]
    ax.annotate("MPG's trough era, 1987-2004:\nton-MPG still climbs "
                f"{trough['slope_per_year']:+.2f}/yr\n(CAGR "
                f"+{a['cagr_1987_2004_pct']}%/yr while raw MPG fell "
                f"{abs(a['mpg_change_1987_2004_pct'])}%)",
                xy=(1996, 42.5), xytext=(1986, 55), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("2018+: electrification bends\nthe curve upward "
                f"({a['segment_slopes'][-1]['slope_per_year']:+.1f}/yr)",
                xy=(2019.5, 56), xytext=(2006, 62), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Ton-MPG (weight-normalized efficiency), fleet average, with "
                 f"its own BIC changepoints at {a['breaks']}", loc="left",
                 fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("Validation A: the engine never stalled, only the allocation did",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Same changepoint machinery as fig16, applied to ton-miles per "
                  "gallon. The shaded MPG stagnation band contains no negative "
                  "ton-MPG segment.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig22_allocation_proof.png")


def fig23(V):
    b = V["B_bunching"]
    gf = np.array(b["gaps_freeze"])
    gp = np.array(b["gaps_post"])
    bins = np.arange(-6, 21, 1.0)

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.8), sharex=True)
    for a in (a1, a2):
        style_ax(a)
    a1.hist(gf, bins=bins, color=S1, edgecolor=SURFACE, linewidth=1.2)
    a1.axvline(0, color=INK2, lw=1.4)
    a1.axvspan(0, 3, color=WASH, zorder=0)
    a1.set_title(f"Freeze era 1990-2007 (n={b['freeze_n']}): "
                 f"{b['freeze_share_in_0_3_band']:.0%} of manufacturer-years "
                 f"sit 0-3 MPG above the standard; median gap "
                 f"{b['freeze_median_gap']}", loc="left", fontsize=10.5, pad=6)
    a2.hist(gp, bins=bins, color=S3, edgecolor=SURFACE, linewidth=1.2)
    a2.axvline(0, color=INK2, lw=1.4)
    a2.axvspan(0, 3, color=WASH, zorder=0)
    a2.set_title(f"Footprint era 2012-2019 (n={b['post_n']}): only "
                 f"{b['post_share_in_0_3_band']:.0%} in that band; median gap "
                 f"{b['post_median_gap']} MPG", loc="left", fontsize=10.5, pad=6)
    a2.set_xlabel("Manufacturer car-fleet 2-cycle MPG minus the 27.5 standard")
    fig.suptitle("Validation B: manufacturers parked just above the frozen standard",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, f"KS test on the two gap distributions: D = {b['ks_D']}, "
                  f"p = {b['ks_p']:.0e}. Approximation caveat: true CAFE "
                  "compliance uses harmonic-mean fleet math and credits.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    save(fig, "fig23_bunching.png")


def fig24(V):
    c = V["C_event_study"]
    pl = np.array(list(c["placebo_values"].values()))
    s79 = c["shocks"]["1979"]["deviation"]
    s08 = c["shocks"]["2008"]["deviation"]

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.hist(pl, bins=18, color=BASELINE, edgecolor=SURFACE, linewidth=1.2)
    ax.axvline(s79, color=S2, lw=2.2)
    ax.axvline(s08, color=S1, lw=2.2)
    ax.annotate(f"1979 oil shock: {s79:+.3f}\n100th percentile --\n"
                "the strongest sedan hold\nin the whole record",
                xy=(s79, 1.0), xytext=(0.028, 3.6), fontsize=10,
                color=S2, fontweight="bold", ha="right",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate(f"2008 spike: {s08:+.3f}\n52nd percentile --\n"
                "indistinguishable from noise",
                xy=(s08, 4.6), xytext=(-0.062, 4.9), fontsize=10,
                color=S1, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_xlabel("4-year mean sedan-share deviation from prior local trend")
    ax.set_ylabel("Placebo windows")
    ax.set_title(f"Gray: {c['placebo_n']} placebo windows (every non-shock start "
                 "year). Colored lines: the two gas-shock windows.", loc="left",
                 fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("Validation C: 1979 was a real episode; the 2008 'sedan rebound' wasn't",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Deviation = mean over 4 post years of (sedan production share - "
                  "linear trend from prior 6 years). Windows within 3 years of a "
                  "shock excluded from placebos. Data: EPA Trends.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig24_event_study.png")


def main():
    os.makedirs(CHARTS, exist_ok=True)
    with open(os.path.join(HERE, "outputs", "validation_results.json"),
              encoding="utf-8") as f:
        V = json.load(f)
    fig22(V)
    fig23(V)
    fig24(V)
    print("wrote fig22-fig24")


if __name__ == "__main__":
    main()
