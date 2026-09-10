"""07_charts_extended.py -- extended figure set: external context + untapped
in-house stories.

Reads outputs/analysis_clean.csv, outputs/context_annual.csv,
outputs/my2024_config.csv. Writes charts/fig5..fig12.

Same design rules as 05_charts.py. Entity colors stay consistent with the
first figure set: Sedan/Wagon blue, Car SUV orange, Truck SUV aqua,
Pickup yellow.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S2, S3, S4, S5, S6 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE, STAGN = "#898781", "#e1e0d9", "#c3c2b7", "#f0efec"

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


def draw_series(ax, x, y, color, lw=2.0, prelim_x=None):
    """Line with an optional dashed final segment for a preliminary year."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if prelim_x is not None and prelim_x in x:
        cut = x < prelim_x
        ax.plot(x[cut], y[cut], color=color, lw=lw, solid_capstyle="round")
        ax.plot(x[~cut | (x == x[cut].max())][-2:] if False else x[x >= x[cut].max()],
                y[x >= x[cut].max()], color=color, lw=lw, ls=(0, (3, 2)))
        ax.plot(x[-1], y[-1], "o", mfc=SURFACE, mec=color, mew=1.6, ms=6)
    else:
        ax.plot(x, y, color=color, lw=lw, solid_capstyle="round")


def legend(ax, handles, labels, **kw):
    lg = ax.legend(handles, labels, frameon=False, fontsize=9.5, **kw)
    for t in lg.get_texts():
        t.set_color(INK2)


def line_handle(c, ls="-"):
    return plt.Line2D([], [], color=c, lw=2, ls=ls)


def footnote(fig, text):
    fig.text(0.01, 0.012, text, fontsize=8.5, color=MUTED)


def save(fig, name):
    fig.savefig(os.path.join(CHARTS, name), dpi=150)
    plt.close(fig)


def fig5(ac, ctx):
    """Real gas price above body-mix shares, shared time axis."""
    sub = ac[ac.manufacturer == "All"]
    sedan = sub[sub.vehicle_type == "Sedan/Wagon"].sort_values("model_year")
    truck = sub[(sub.vehicle_type == "All Truck")].sort_values("model_year")
    g = ctx.dropna(subset=["gas_real_2024_usd_gal"])
    g = g[g.year.between(1975, 2025)]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.6), sharex=True,
                                 height_ratios=[1, 1.4])
    for a in (a1, a2):
        style_ax(a)
    draw_series(a1, g.year, g.gas_real_2024_usd_gal, S2)
    a1.set_title("Retail gasoline, 2024 dollars per gallon (unleaded regular, from 1976)",
                 loc="left", fontsize=11, pad=6)
    a1.annotate("1980 oil shock: $4.74", xy=(1980, 4.74), xytext=(1984, 4.9),
                fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    a1.annotate("2008: $4.76", xy=(2008, 4.76), xytext=(2000.5, 4.9),
                fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))

    draw_series(a2, sedan.model_year, sedan.production_share, S1, prelim_x=2025)
    draw_series(a2, truck.model_year, truck.production_share, S3, prelim_x=2025)
    a2.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    a2.set_yticklabels(["0%", "20%", "40%", "60%", "80%"])
    a2.set_title("Production share", loc="left", fontsize=11, pad=6)
    a2.text(1978, 0.73, "Sedan/Wagon", color=S1, fontweight="bold", fontsize=10.5)
    a2.text(1978, 0.25, "Trucks (incl. Truck SUV)", color=S3, fontweight="bold",
            fontsize=10.5)
    a2.annotate("cheap-gas decade:\ntruck share takes off", xy=(2015, 0.55),
                xytext=(2003.5, 0.66), fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    legend(a2, [line_handle(S1), line_handle(S3)],
           ["Sedan/Wagon", "All Truck"], loc="upper left",
           bbox_to_anchor=(0.0, -0.12), ncol=2)
    fig.suptitle("Expensive gas kept sedans alive; cheap gas buried them",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Sources: EPA Automotive Trends (production-weighted); BLS via FRED "
                  "APU000074714, CPI-deflated to 2024$. Calendar-year prices vs "
                  "model-year shares: approximate alignment. Dashed: preliminary 2025.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    save(fig, "fig5_gas_vs_mix.png")


def fig6(ac, ctx):
    """CAFE car standard vs achieved car 2-cycle MPG, same test basis."""
    cars = ac[(ac.manufacturer == "All") & (ac.regulatory_class == "Car")
              & (ac.vehicle_type == "All Car")].sort_values("model_year")
    std = ctx.dropna(subset=["cafe_car_standard_mpg"])

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.axvspan(1985, 2007, color=STAGN, zorder=0)
    draw_series(ax, cars.model_year, cars.cafe_2cycle_mpg, S1, prelim_x=2025)
    ax.plot(std.year, std.cafe_car_standard_mpg, color=INK2, lw=1.6,
            drawstyle="steps-post")
    ax.text(1996, 28.6, "CAFE passenger-car standard\n(27.5 MPG, frozen 1985–2010)",
            fontsize=9.5, color=INK2, ha="center")
    ax.text(1994, 33.5, "Achieved (2-cycle test basis)", color=S1,
            fontweight="bold", fontsize=10.5)
    ax.annotate("standard resumes rising:\nfootprint-based rules, MY2011+",
                xy=(2011, 33), xytext=(2012.5, 26), fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_ylim(14, 48)
    legend(ax, [line_handle(S1), line_handle(INK2)],
           ["Achieved, cars (2-cycle)", "Passenger-car standard (1978–2010)"],
           loc="upper left")
    ax.set_title("Passenger-car fleet, unadjusted 2-cycle MPG vs the national "
                 "standard. Same test basis on both lines.", loc="left",
                 fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("When the standard froze, so did progress: 22 years at 27.5 MPG",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Sources: EPA Automotive Trends; NHTSA published CAFE standards. "
                  "Post-2010 standards are footprint-based per-fleet (no single value). "
                  "Dashed: preliminary 2025.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig6_standard_vs_achieved.png")


def fig7(ac):
    """Lab-over-road inflation ratio."""
    aa = ac[(ac.manufacturer == "All") & (ac.regulatory_class == "All")
            & (ac.vehicle_type == "All")].sort_values("model_year")
    ratio = aa.cafe_2cycle_mpg / aa.real_world_mpg

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    draw_series(ax, aa.model_year, ratio, S1, prelim_x=2025)
    ax.set_ylim(1.0, 1.4)
    ax.set_yticks([1.0, 1.1, 1.2, 1.3, 1.4])
    ax.set_yticklabels(["+0%", "+10%", "+20%", "+30%", "+40%"])
    ax.annotate("1975: lab 17% above real-world", xy=(1975, 1.174),
                xytext=(1977, 1.30), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("2024: +31%", xy=(2024, 1.309), xytext=(2015, 1.36),
                fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Unadjusted 2-cycle (CAFE-basis) MPG divided by EPA estimated "
                 "real-world MPG, fleet average", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("The lab test drifted from the road: compliance MPG runs 31% hot",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Source: EPA Automotive Trends. This chart compares the two MPG "
                  "definitions on purpose; the ratio, not the levels, is the story. "
                  "Dashed: preliminary 2025.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig7_lab_vs_road.png")


def fig8(ac):
    """Manufacturer race, highlight three, gray the rest, Tesla excluded."""
    mfg = ac[(ac.regulatory_class == "All") & (ac.vehicle_type == "All")
             & (~ac.manufacturer.isin(["All", "Tesla"]))]
    hi = {"Honda": S3, "Toyota": S1, "GM": S2}

    fig, ax = plt.subplots(figsize=(11, 6.6))
    style_ax(ax)
    for name, d in mfg.groupby("manufacturer"):
        d = d.sort_values("model_year")
        if name in hi:
            continue
        ax.plot(d.model_year, d.real_world_mpg, color=BASELINE, lw=1.1)
    for name, c in hi.items():
        d = mfg[mfg.manufacturer == name].sort_values("model_year")
        draw_series(ax, d.model_year, d.real_world_mpg, c, prelim_x=2025)
        last = d.iloc[-1]
        ax.text(last.model_year + 0.4, last.real_world_mpg, name, color=c,
                fontweight="bold", fontsize=10.5, va="center")
    ax.annotate("2024 spread: Honda 31.0,\nStellantis 22.8", xy=(2024, 22.8),
                xytext=(2010, 16.5), fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    legend(ax, [line_handle(c) for c in hi.values()] + [line_handle(BASELINE)],
           list(hi) + ["10 other manufacturers"], loc="upper left")
    ax.set_title("Real-world MPG by manufacturer (parent rollup). Tesla excluded: "
                 "its 117 MPGe-basis value is a different quantity.", loc="left",
                 fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The 8-MPG spread: Honda has led for most of 50 years",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Source: EPA Automotive Trends, production-weighted per manufacturer. "
                  "Dashed: preliminary 2025.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig8_manufacturer_race.png")


def fig9(my24):
    """MY2024: footprint vs unadjusted economy, per carline, volume-sized."""
    # FE_UNIT alone is not sufficient: some BEV rows carry MPGe values under
    # the MPG unit label. Combustion drive source is the reliable filter.
    d = my24[(my24["src_my24fe_FE_UNIT"] == "MPG")
             & (my24["src_my24fe_DRIVE_SOURCE"] == "C")].copy()
    g = d.groupby(["src_my24fe_Carline Mfr Code", "src_my24fe_CARLINE_CODE"]).agg(
        fp=("src_my24fp_EPA_CALC_ROUNDED_AREA", "median"),
        fe=("src_my24fe_UNRD_UNADJ_MT_COMB_FE", "median"),
        vol=("derived_carline_prod_vol", "first"),
        cat=("src_my24fe_Compliance Category", "first"),
    ).dropna()

    fig, ax = plt.subplots(figsize=(11, 6.6))
    style_ax(ax)
    ax.grid(axis="x", visible=True)
    for cat, color, label in [("PV", S1, "Passenger vehicles"),
                              ("LT", S3, "Light trucks")]:
        s = g[g.cat == cat]
        ax.scatter(s.fp, s.fe, s=8 + s.vol / 1200, c=color, alpha=0.55,
                   edgecolors=SURFACE, linewidths=0.8)
    legend(ax, [plt.Line2D([], [], marker="o", ls="", mfc=c, mec=SURFACE, ms=9)
                for c in (S1, S3)],
           ["Passenger vehicles", "Light trucks"], loc="upper right")
    ax.set_xlabel("Footprint (sq ft, EPA calculated)")
    ax.set_ylabel("Unadjusted 2-cycle combined MPG")
    ax.set_title("One dot per carline, MY2024; dot area = production volume. "
                 "Gasoline/diesel carlines only (MPG unit).", loc="left",
                 fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("Bigger footprint, lower economy, and the volume sits in trucks",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Source: EPA MY2024 FE & footprint files, joined at carline level. "
                  "Median across configurations within carline; EVs/PHEVs excluded "
                  "(different measurement unit).")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig9_footprint_vs_mpg_2024.png")


def fig10(ac):
    """Trim collapse: configurations per model in the catalog."""
    aa = ac[(ac.manufacturer == "All") & (ac.regulatory_class == "All")
            & (ac.vehicle_type == "All")].sort_values("model_year")
    d = aa.dropna(subset=["catalog_n_configurations", "catalog_n_models"])
    d = d[d.model_year <= 2025]
    ratio = d.catalog_n_configurations / d.catalog_n_models

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    draw_series(ax, d.model_year, ratio, S1, prelim_x=2025)
    ax.set_ylim(0, 10)
    ax.annotate("1984: 8.7 configurations\nper base model", xy=(1984, 8.7),
                xytext=(1988, 9.3), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("2024: 4.1", xy=(2024, 4.1), xytext=(2018, 6.3), fontsize=10,
                color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("fueleconomy.gov catalog: configurations offered per base model, "
                 "all makes", loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The menu shrank: half the trims per model since 1984",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Source: fueleconomy.gov vehicles.csv (catalog of offerings, "
                  "unweighted). Dashed: preliminary/partial 2025 catalog.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig10_trim_collapse.png")


def fig11(ac):
    """Footprint creep by body type since 2008."""
    order = [("Sedan/Wagon", S1), ("Car SUV", S2), ("Truck SUV", S3),
             ("Pickup", S4)]
    sub = ac[(ac.manufacturer == "All") & (ac.model_year >= 2008)]

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    for vt, c in order:
        d = sub[sub.vehicle_type == vt].sort_values("model_year").dropna(
            subset=["footprint_sqft"])
        draw_series(ax, d.model_year, d.footprint_sqft, c, prelim_x=2025)
        last = d.iloc[-1]
        ax.text(last.model_year + 0.25, last.footprint_sqft, vt, color=c,
                fontweight="bold", fontsize=10.5, va="center")
    legend(ax, [line_handle(c) for _, c in order], [vt for vt, _ in order],
           loc="upper left", bbox_to_anchor=(0.0, -0.1), ncol=4)
    ax.set_title("Average footprint (sq ft), production-weighted, by body type",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("Everything got physically bigger, and pickups most of all",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Source: EPA Automotive Trends. Footprint collected from MY2008 "
                  "(attribute-based standards). Dashed: preliminary 2025.")
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    save(fig, "fig11_footprint_creep.png")


def fig12(ac):
    """Share of SUVs regulated as trucks."""
    sub = ac[ac.manufacturer == "All"]
    cs = sub[sub.vehicle_type == "Car SUV"].set_index("model_year").production_share
    ts = sub[sub.vehicle_type == "Truck SUV"].set_index("model_year").production_share
    both = pd.concat([cs.rename("cs"), ts.rename("ts")], axis=1).dropna()
    both = both[(both.cs + both.ts) >= 0.02]  # ratio is noise when SUVs are ~0
    share = both.ts / (both.ts + both.cs)

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    draw_series(ax, share.index, share.values, S3, prelim_x=2025)
    ax.set_ylim(0.5, 1.0)
    ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_yticklabels(["50%", "60%", "70%", "80%", "90%", "100%"])
    ax.annotate("crossover era: car-classed\nSUVs gain ground", xy=(2010, 0.72),
                xytext=(1998, 0.62), fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.annotate("2024: 82% of SUV production\nregulated under truck rules",
                xy=(2024, 0.82), xytext=(2012, 0.9), fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Truck-classed share of SUV production (Truck SUV vs Car SUV, "
                 "EPA regulatory classes)", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("Most SUVs are trucks on paper, and the truck rulebook is easier",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "Source: EPA Automotive Trends. Years where SUVs total under 2% of "
                  "production omitted (ratio unstable). Dashed: preliminary 2025.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    save(fig, "fig12_suv_reclassification.png")


def main():
    os.makedirs(CHARTS, exist_ok=True)
    ac = pd.read_csv(os.path.join(HERE, "outputs", "analysis_clean.csv"))
    ctx = pd.read_csv(os.path.join(HERE, "outputs", "context_annual.csv"))
    my24 = pd.read_csv(os.path.join(HERE, "outputs", "my2024_config.csv"),
                       low_memory=False)
    fig5(ac, ctx)
    fig6(ac, ctx)
    fig7(ac)
    fig8(ac)
    fig9(my24)
    fig10(ac)
    fig11(ac)
    fig12(ac)
    for f in sorted(os.listdir(CHARTS)):
        print("wrote charts/" + f)


if __name__ == "__main__":
    main()
