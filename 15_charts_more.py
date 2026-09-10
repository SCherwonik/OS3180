"""15_charts_more.py -- credit trap, EV parity, household irony, fleet age.

Reads outputs/context_finance.csv + outputs/analysis_clean.csv.
Writes charts/fig25..fig28.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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


def fig25(f, ac):
    trk = (ac[(ac.manufacturer == "All") & (ac.vehicle_type == "All Truck")
              & (~ac.is_preliminary)][["model_year", "production_share"]]
           .rename(columns={"model_year": "year"}))
    m = trk.merge(f[["year", "autoloan_48mo_rate_pct"]], on="year").dropna()

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 5.8))
    for a in (a1, a2):
        style_ax(a)
    # Left: the seduction. Two lines, indexed so one axis is honest.
    idx_rate = m.autoloan_48mo_rate_pct / m.autoloan_48mo_rate_pct.iloc[0] * 100
    idx_trk = m.production_share / m.production_share.iloc[0] * 100
    a1.plot(m.year, idx_rate, color=S2, lw=2)
    a1.plot(m.year, idx_trk, color=S3, lw=2)
    a1.text(1990, 45, "loan rate\n(indexed 1972=100)", color=S2,
            fontweight="bold", fontsize=10)
    a1.text(1995, 210, "truck share\n(indexed)", color=S3,
            fontweight="bold", fontsize=10)
    a1.set_title("The seduction: rates fell for four decades,\ntruck share "
                 "rose. Levels r² = 0.568, p = 3e-10", loc="left",
                 fontsize=10.5, color=INK2)
    # Right: the audit.
    dm = m.set_index("year").diff().dropna()
    a2.grid(axis="x", visible=True)
    a2.scatter(dm.autoloan_48mo_rate_pct, dm.production_share, s=36,
               c=S1, edgecolors=SURFACE, linewidths=0.8)
    a2.set_xlabel("Change in loan rate (pp, year over year)")
    a2.set_ylabel("Change in truck share")
    a2.set_title("The audit: year-over-year changes.\nDifferenced r² = 0.045, "
                 "p = 0.145 -- not significant", loc="left", fontsize=10.5,
                 color=INK2)
    fig.suptitle("Revision #7, the cheap-credit story: same trap as gas prices, "
                 "caught by the same test", x=0.01, ha="left", fontsize=14.5,
                 fontweight="bold")
    footnote(fig, "Fed G.19 via FRED TERMCBAUTO48NS (48-mo new-car loans) vs EPA "
                  "Trends truck production share, 1972-2024. The textbook "
                  "spurious-levels regression fig19 went looking for.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.90))
    save(fig, "fig25_credit_trap.png")


def fig26(f):
    d = f.dropna(subset=["gas_cost_per_mile", "ev_cost_per_mile"])
    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.plot(d.year, d.gas_cost_per_mile, color=S2, lw=2)
    ax.plot(d.year, d.ev_cost_per_mile, color=S1, lw=2)
    ax.set_ylim(0, 0.20)
    ax.set_yticks([0, 0.05, 0.10, 0.15, 0.20])
    ax.set_yticklabels(["$0.00", "$0.05", "$0.10", "$0.15", "$0.20"])
    last = d.iloc[-1]
    ax.text(last.year + 0.3, last.gas_cost_per_mile, "gasoline\n(fleet avg)",
            color=S2, fontweight="bold", fontsize=10.5, va="center")
    ax.text(last.year + 0.3, last.ev_cost_per_mile, "electricity\n(catalog EV avg)",
            color=S1, fontweight="bold", fontsize=10.5, va="center")
    r12 = d[d.year == 2012].iloc[0]
    r24 = d[d.year == 2024].iloc[0]
    ax.annotate(f"2012: EV miles {r12.gas_over_ev_cost_ratio:.1f}x cheaper",
                xy=(2012, r12.ev_cost_per_mile), xytext=(2012.3, 0.115),
                fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate(f"2024: advantage down to {r24.gas_over_ev_cost_ratio:.2f}x\n"
                "(electricity prices up, gas cars more efficient)",
                xy=(2024, r24.ev_cost_per_mile), xytext=(2013.5, 0.021),
                fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Energy cost per mile, nominal dollars: gasoline price over "
                 "real-world MPG, vs electricity price times EV consumption",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("EV miles are still cheaper, but the advantage is quietly shrinking",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "BLS gas & electricity prices via FRED; EPA fleet MPG; catalog "
                  "EV kWh/100mi from fueleconomy.gov. Energy only -- excludes "
                  "purchase price, depreciation, and DC-fast-charging premiums.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig26_ev_parity.png")


def fig27(f, ac):
    aa = ac[(ac.manufacturer == "All") & (ac.regulatory_class == "All")
            & (ac.vehicle_type == "All") & (~ac.is_preliminary)]
    hh = f.dropna(subset=["household_avg_size"])

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.2), sharex=True)
    for a in (a1, a2):
        style_ax(a)
    a1.plot(hh.year, hh.household_avg_size, "o-", color=S1, lw=1.8, ms=6)
    a1.set_ylim(2.3, 3.1)
    a1.set_title("Average persons per household (Census, 5-year sampling)",
                 loc="left", fontsize=11, pad=6)
    a1.annotate("-15% people", xy=(2024, 2.51), xytext=(2013, 2.85),
                fontsize=11, color=S1, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    a2.plot(aa.model_year, aa.weight_lbs, color=S2, lw=2)
    a2.set_title("Average vehicle weight, production-weighted (EPA Trends)",
                 loc="left", fontsize=11, pad=6)
    a2.annotate("+35% pounds since 1981", xy=(2024, 4354), xytext=(2004, 3500),
                fontsize=11, color=S2, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    fig.suptitle("Households shrank while their vehicles grew",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Census Table HH-4 (persons per household); EPA Trends "
                  "production-weighted weight. Correlation is not causation; "
                  "the juxtaposition is the point.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    save(fig, "fig27_household_irony.png")


def fig28(f, ac):
    d = f.dropna(subset=["fleet_avg_age_years"])
    fig, ax = plt.subplots(figsize=(11, 6.0))
    style_ax(ax)
    ax.plot(d.year, d.fleet_avg_age_years, color=S1, lw=2)
    ax.set_ylim(0, 14)
    ax.annotate("1995: 8.4 years", xy=(1995, 8.4), xytext=(1997, 5.6),
                fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("2024: 12.6 years", xy=(2024, 12.6), xytext=(2013, 13.4),
                fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.text(1996.5, 2.1,
            "Why it matters for every adoption chart in this deck:\n"
            "production share is not road share. At a 12.6-year average age,\n"
            "the median vehicle on the road today was built around 2013 --\n"
            "before GDI, turbo, and CVT hit their S-curve midpoints (fig18).\n"
            "The street lags the factory by roughly a decade.",
            fontsize=10, color=INK2)
    ax.set_title("Average age of light vehicles in operation (BTS Table 1-26a)",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The fleet is the oldest it has ever been, so the road lags the factory",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "BTS National Transportation Statistics Table 1-26a, all light "
                  "vehicles. Retrieved via user's browser (bts.gov blocks CLI).")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig28_fleet_age.png")


def main():
    os.makedirs(CHARTS, exist_ok=True)
    f = pd.read_csv(os.path.join(HERE, "outputs", "context_finance.csv"))
    ac = pd.read_csv(os.path.join(HERE, "outputs", "analysis_clean.csv"))
    fig25(f, ac)
    fig26(f)
    fig27(f, ac)
    fig28(f, ac)
    print("wrote fig25-fig28")


if __name__ == "__main__":
    main()
