"""05_charts.py -- presentation figure set for the offer-vs-buy narrative.

Reads outputs/analysis_clean.csv, writes charts/fig1..fig4 as PNG.

Design rules applied (dataviz method): one axis per plot (small multiples,
never dual axes), fixed categorical slot order (validated palette), thin
marks, solid hairline grid, direct labels for identity, preliminary 2025
drawn dashed with an open marker and footnoted.

Idempotent: same inputs -> same PNGs.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

# Validated categorical palette, light mode, fixed slot order.
S1, S2, S3, S4, S5, S6 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
STAGN = "#f0efec"  # neutral wash for the 1987-2004 stagnation band

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "grid.linestyle": "-",
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": INK,
    "axes.labelcolor": INK2,
    "axes.titlecolor": INK,
    "font.size": 11,
})


def style_ax(ax, ybaseline=True):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_visible(ybaseline)
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)
    ax.margins(x=0.01)


def split_prelim(df, ycol):
    """Return (final-years series, dashed bridge into the preliminary year)."""
    fin = df[~df.is_preliminary].dropna(subset=[ycol])
    pre = df[df.is_preliminary].dropna(subset=[ycol])
    if pre.empty:
        return fin, None
    bridge = pd.concat([fin[fin.model_year == fin.model_year.max()], pre])
    return fin, bridge


def draw_series(ax, df, ycol, color, lw=2.0):
    fin, bridge = split_prelim(df, ycol)
    ax.plot(fin.model_year, fin[ycol], color=color, lw=lw, solid_capstyle="round")
    if bridge is not None:
        ax.plot(bridge.model_year, bridge[ycol], color=color, lw=lw, ls=(0, (3, 2)))
        ax.plot(bridge.model_year.iloc[-1], bridge[ycol].iloc[-1], "o",
                mfc=SURFACE, mec=color, mew=1.6, ms=6)


def footnote(fig, extra=""):
    fig.text(0.01, 0.012,
             "Source: EPA Automotive Trends Report (production-weighted). "
             "Dashed segment / open marker: preliminary 2025." + extra,
             fontsize=8.5, color=MUTED)


def fig1(aa):
    panels = [
        ("real_world_mpg", "Real-world fuel economy (MPG)"),
        ("horsepower_hp", "Horsepower"),
        ("weight_lbs", "Weight (lbs)"),
        ("accel_0_60_s", "0–60 mph (seconds, lower = quicker)"),
    ]
    fig, axes = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
    for ax, (col, title) in zip(axes, panels):
        style_ax(ax)
        ax.axvspan(1987, 2004, color=STAGN, zorder=0)
        draw_series(ax, aa, col, S1)
        ax.set_title(title, loc="left", fontsize=11.5, pad=6)
    a0 = axes[0]
    a0.annotate("1987 peak: 22.0", xy=(1987, 22.0), xytext=(1980.5, 25.5),
                fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    a0.annotate("2004 trough: 19.3", xy=(2004, 19.3), xytext=(2004.5, 14.5),
                fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    a0.annotate("2024: 27.2", xy=(2024, 27.2), xytext=(2015.5, 29.5),
                fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    axes[1].text(1995.5, 240, "17-year detour:\nefficiency spent on\npower and weight",
                 fontsize=9.5, color=INK2, ha="center", va="top")
    axes[3].invert_yaxis()  # quicker (smaller) reads as "up"
    fig.suptitle("Fuel economy stalled for 17 years while horsepower doubled",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.945, "US light-duty fleet averages, model years 1975–2025",
             fontsize=10.5, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    fig.savefig(os.path.join(CHARTS, "fig1_three_acts.png"), dpi=150)
    plt.close(fig)


def fig2(ac):
    order = ["Sedan/Wagon", "Car SUV", "Truck SUV", "Pickup", "Minivan/Van"]
    colors = [S1, S2, S3, S4, S5]
    sub = ac[(ac.manufacturer == "All") & (ac.vehicle_type.isin(order))]
    wide = (sub.pivot_table(index="model_year", columns="vehicle_type",
                            values="production_share")[order].fillna(0.0))
    prelim_years = set(ac.loc[ac.is_preliminary, "model_year"])

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.grid(visible=False)
    ax.stackplot(wide.index, [wide[c] for c in order], colors=colors,
                 labels=order, linewidth=1.5, edgecolor=SURFACE)
    if prelim_years:
        ax.axvline(2024, color=SURFACE, lw=1.5)
        ax.axvline(2024, color=MUTED, lw=0.8, ls=(0, (3, 2)))
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    # Direct labels for the three big segments at their vertical centers, 2024.
    y0 = 0
    centers = {}
    for c in order:
        centers[c] = y0 + wide.loc[2024, c] / 2
        y0 += wide.loc[2024, c]
    for c, lab in [("Sedan/Wagon", "Sedan/Wagon 24%"),
                   ("Truck SUV", "Truck SUV 50%"),
                   ("Pickup", "Pickup 14%")]:
        ax.text(2023.2, centers[c], lab, ha="right", va="center",
                fontsize=10.5, color=SURFACE, fontweight="bold")
    ax.text(1976, 0.42, "Sedan/Wagon 81%", fontsize=10.5, color=SURFACE,
            fontweight="bold")
    leg = ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.08), ncol=5,
                    frameon=False, fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(INK2)
    ax.set_title("Production share by body type, US light-duty vehicles",
                 loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("The sedan inversion: 81% of production to 24%",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig)
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig2_sedan_inversion.png"), dpi=150)
    plt.close(fig)


def fig3(aa):
    d = aa[aa.model_year >= 2008].copy()
    d["offered"] = d.catalog_n_ev_configurations / d.catalog_n_configurations
    d["bought"] = d.share_powertrain_battery_electric_vehicle_bev

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    draw_series(ax, d, "offered", S1)
    draw_series(ax, d, "bought", S2)
    ax.set_ylim(0, 0.24)
    ax.set_yticks([0, 0.05, 0.10, 0.15, 0.20])
    ax.set_yticklabels(["0%", "5%", "10%", "15%", "20%"])
    lo = d.dropna(subset=["offered"]).iloc[-1]
    lb = d.dropna(subset=["bought"]).iloc[-1]
    ax.text(lo.model_year + 0.3, lo.offered, "EV share of\ncatalog offered",
            color=S1, fontsize=10.5, va="center", fontweight="bold")
    ax.text(lb.model_year + 0.3, lb.bought, "EV share of\nproduction bought",
            color=S2, fontsize=10.5, va="center", fontweight="bold")
    # 2024 gap bracket
    o24 = d.loc[d.model_year == 2024, "offered"].iloc[0]
    b24 = d.loc[d.model_year == 2024, "bought"].iloc[0]
    ax.annotate("", xy=(2024, o24), xytext=(2024, b24),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1.0))
    ax.text(2023.4, (o24 + b24) / 2, "2024: offered 21%,\nbought 7%",
            ha="right", va="center", fontsize=10, color=INK2)
    handles = [plt.Line2D([], [], color=c, lw=2) for c in (S1, S2)]
    leg = ax.legend(handles, ["EV share of catalog offered",
                              "EV share of production bought"],
                    loc="upper left", frameon=False, fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(INK2)
    ax.set_title("Battery-electric share of fueleconomy.gov catalog vs "
                 "production-weighted BEV share", loc="left", fontsize=10.5,
                 color=INK2, pad=8)
    fig.suptitle("Automakers offer EVs three times faster than Americans buy them",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, " Catalog share derived from fueleconomy.gov vehicles.csv.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig3_ev_gap.png"), dpi=150)
    plt.close(fig)


def fig4(aa):
    series = [
        ("share_fuel_delivery_carbureted", "Carburetor", S1),
        ("share_turbocharged_engine_of_gasoline_ice_vehicles", "Turbo", S2),
        ("share_fuel_delivery_gasoline_direct_injection_gdi", "GDI", S3),
        ("share_transmission_cvt_non_hybrid", "CVT", S4),
        ("share_powertrain_gasoline_strong_hybrid_hev", "Hybrid (HEV)", S5),
        ("share_powertrain_battery_electric_vehicle_bev", "BEV", S6),
    ]
    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ends = []
    for col, label, color in series:
        d = aa.dropna(subset=[col])
        draw_series(ax, d, col, color)
        ends.append((label, color, d.model_year.max(), d[col].iloc[-1]))
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    # Direct end labels, nudged apart where endpoints crowd.
    ends.sort(key=lambda e: e[3])
    ys = []
    for label, color, x, y in ends:
        yy = y
        while any(abs(yy - p) < 0.05 for p in ys):
            yy += 0.05
        ys.append(yy)
        ax.text(x + 0.4, yy, label, color=color, fontsize=10.5,
                va="center", fontweight="bold")
    ax.annotate("carburetors: 96% → extinct", xy=(1975.4, 0.957),
                xytext=(1979, 0.87), fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    handles = [plt.Line2D([], [], color=c, lw=2) for _, _, c in
               [(s[0], s[1], s[2]) for s in series]]
    leg = ax.legend(handles, [s[1] for s in series], loc="upper left",
                    bbox_to_anchor=(0.0, -0.08), ncol=6, frameon=False,
                    fontsize=9.5)
    for t in leg.get_texts():
        t.set_color(INK2)
    ax.set_title("Production share of engine and drivetrain technologies, "
                 "1975–2025", loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("Technology S-curves: GDI hit 56% in sixteen years; "
                 "turbo took twenty-eight to reach 44%",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig)
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig4_tech_scurves.png"), dpi=150)
    plt.close(fig)


def main():
    os.makedirs(CHARTS, exist_ok=True)
    ac = pd.read_csv(os.path.join(HERE, "outputs", "analysis_clean.csv"))
    aa = ac[(ac.manufacturer == "All") & (ac.regulatory_class == "All")
            & (ac.vehicle_type == "All")].sort_values("model_year")
    fig1(aa)
    fig2(ac)
    fig3(aa)
    fig4(aa)
    for f in sorted(os.listdir(CHARTS)):
        print("wrote charts/" + f)


if __name__ == "__main__":
    main()
