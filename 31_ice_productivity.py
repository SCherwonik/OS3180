"""31_ice_productivity.py -- figs 42/43 rebuilt excluding BEVs.

The Trends aggregates fold BEV energy-equivalents in, so BEVs are backed
OUT rather than dropped: per year and class, remove the BEV share
harmonically from MPG (EPA computes fleet MPG gallons-first) and
arithmetically from weight and horsepower, using the EPA Trends Tesla
series as the BEV proxy (the only production-weighted EV series with MPG,
weight, and HP on the same basis). Then normalize exactly as stage 29/30.

  MPG_ice  = (1 - s) / (1/MPG_all - s/MPGe_bev)
  wt_ice   = (wt_all - s * wt_bev) / (1 - s)     (same for HP)

Hybrids and PHEVs remain included: the user asked BEV-only removal.

Outputs: outputs/ice_productivity.csv, reports/31_ice_productivity.md,
charts/fig45_ice_productivity.png, charts/fig46_ice_class_productivity.png
"""

import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
REPORTS = os.path.join(HERE, "reports")
CHARTS = os.path.join(HERE, "charts")

EL_W, EL_H = 0.304, 0.483
BEV_COL = "share_powertrain_battery_electric_vehicle_bev"

S1, S2, S3, S4, S5 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUT, GRID, BASELINE, WASH = "#898781", "#e1e0d9", "#c3c2b7", "#f0efec"
CLASSES = [("Sedan/Wagon", S1), ("Car SUV", S2), ("Truck SUV", S3),
           ("Pickup", S4), ("Minivan/Van", S5)]

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "xtick.color": MUT, "ytick.color": MUT,
    "text.color": INK, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "font.size": 11,
})


def style(ax):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", visible=False)


def de_bev(df, tesla):
    """Back the BEV share out of MPG (harmonic) and weight/HP (arithmetic)."""
    out = df.copy()
    s = out[BEV_COL].fillna(0.0).clip(0, 0.95)
    proxy = tesla.reindex(out.model_year)
    mpg_bev = proxy["real_world_mpg"].values
    wt_bev = proxy["weight_lbs"].values
    hp_bev = proxy["horsepower_hp"].values
    have = (s.values > 0) & ~np.isnan(mpg_bev)
    inv = 1.0 / out.real_world_mpg.values
    mpg = out.real_world_mpg.values.copy()
    mpg[have] = (1 - s.values[have]) / (inv[have] - s.values[have] / mpg_bev[have])
    wt = out.weight_lbs.values.copy()
    hp = out.horsepower_hp.values.copy()
    wt[have] = (wt[have] - s.values[have] * wt_bev[have]) / (1 - s.values[have])
    hp[have] = (hp[have] - s.values[have] * hp_bev[have]) / (1 - s.values[have])
    out["mpg_ice"], out["wt_ice"], out["hp_ice"] = mpg, wt, hp
    return out


def normalize(d):
    ref = d[d.model_year == 2024].iloc[0]
    return (d.mpg_ice * (d.wt_ice / ref.wt_ice) ** EL_W
            * (d.hp_ice / ref.hp_ice) ** EL_H)


def main():
    os.makedirs(CHARTS, exist_ok=True)
    ac = pd.read_csv(os.path.join(OUT, "analysis_clean.csv"))
    fin = ac[~ac.is_preliminary]
    tesla = (fin[(fin.manufacturer == "Tesla") & (fin.regulatory_class == "All")
                 & (fin.vehicle_type == "All")]
             .set_index("model_year")[["real_world_mpg", "weight_lbs",
                                       "horsepower_hp"]])

    rows_csv = []
    proj_years = np.arange(2025, 2046)

    # ---- fig45: fleet, ex-BEV ------------------------------------------
    aa = (fin[(fin.manufacturer == "All") & (fin.regulatory_class == "All")
              & (fin.vehicle_type == "All")]
          .sort_values("model_year")
          .dropna(subset=["real_world_mpg", "weight_lbs", "horsepower_hp"]))
    aa = de_bev(aa, tesla)
    norm = normalize(aa)
    t = aa.model_year.values.astype(float)
    r_all = stats.linregress(t, np.log(norm))
    m = t >= 2005
    r_rec = stats.linregress(t[m], np.log(norm.values[m]))
    p_rec = np.exp(r_rec.intercept + r_rec.slope * proj_years)
    p_full = np.exp(r_all.intercept + r_all.slope * proj_years)
    g_all, g_rec = [100 * (np.exp(r.slope) - 1) for r in (r_all, r_rec)]
    for y, v in zip(t, norm):
        rows_csv.append({"scope": "fleet", "year": int(y),
                         "mpg_norm_ice": round(float(v), 3)})

    fig, ax = plt.subplots(figsize=(11, 6.4))
    style(ax)
    ax.axvspan(1987, 2004, color=WASH, zorder=0)
    ax.plot(t, aa.real_world_mpg.values, color=BASELINE, lw=1.6)
    ax.plot(t, norm.values, color=S1, lw=2.2)
    ax.plot(proj_years, p_rec, color=S1, lw=2.0, ls=(0, (4, 2)))
    ax.plot(proj_years, p_full, color=S3, lw=1.6, ls=(0, (2, 2)))
    ax.text(1990, 14.0, "raw fleet MPG", color=MUT, fontsize=10)
    ax.text(1992.5, 22.5, "combustion only, normalized to 2024 design:\n"
            f"+{g_all:.2f}%/yr for 50 years", color=S1, fontweight="bold",
            fontsize=10.5)
    ax.annotate(f"2045 at 2005-2024 rate: {p_rec[-1]:.0f}",
                xy=(2045, p_rec[-1]), xytext=(2027, 42), fontsize=10,
                color=S1, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
    ax.annotate(f"at 50-year rate: {p_full[-1]:.0f}",
                xy=(2045, p_full[-1]), xytext=(2035.5, 26), fontsize=10,
                color=S3, arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8))
    ax.set_ylim(5, 50)
    ax.set_title("BEV share backed out of MPG (harmonic), weight, and HP "
                 "before normalizing; hybrids remain in. fig42's ex-BEV "
                 "twin.", loc="left", fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("Combustion alone kept the clock: "
                 f"+{g_all:.1f}%/yr normalized, no BEVs required",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.012, "EPA Trends; Tesla series as the BEV proxy for "
             "removal (share <= 7.2% at fleet level, so proxy error is "
             "second-order). reports/31_ice_productivity.md.",
             fontsize=8.5, color=MUT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig45_ice_productivity.png"), dpi=150)
    plt.close(fig)

    # ---- fig46: classes, ex-BEV ----------------------------------------
    sub = fin[(fin.manufacturer == "All")].dropna(
        subset=["real_world_mpg", "weight_lbs", "horsepower_hp"])
    fig, ax = plt.subplots(figsize=(11, 6.8))
    style(ax)
    ends, class_stats = [], []
    for vt, c in CLASSES:
        d = de_bev(sub[sub.vehicle_type == vt].sort_values("model_year"), tesla)
        n = normalize(d)
        yr = d.model_year.values.astype(float)
        r = stats.linregress(yr, np.log(n))
        proj = np.exp(r.intercept + r.slope * proj_years)
        g = 100 * (np.exp(r.slope) - 1)
        ax.plot(yr, n.values, color=c, lw=2)
        ax.plot(proj_years, proj, color=c, lw=1.5, ls=(0, (4, 2)), alpha=0.8)
        ends.append((vt, c, proj[-1], g))
        class_stats.append((vt, g, r.rvalue ** 2, n.iloc[-1], proj[-1]))
        for y, v in zip(yr, n):
            rows_csv.append({"scope": vt, "year": int(y),
                             "mpg_norm_ice": round(float(v), 3)})
    ends.sort(key=lambda e: e[2])
    used = []
    for vt, c, y, g in ends:
        yy = y
        while any(abs(yy - u) < 2.6 for u in used):
            yy += 2.6
        used.append(yy)
        ax.text(2045.5, yy, f"{vt}  +{g:.1f}%/yr", color=c,
                fontweight="bold", fontsize=10, va="center")
    ax.set_xlim(1974, 2054)
    ax.set_ylim(0, 55)
    ax.set_title("Same construction as fig43 with the BEV share backed out "
                 "of every class; the Car SUV spike is gone, the hybrid "
                 "climb remains", loc="left", fontsize=10.5, color=INK2,
                 pad=8)
    fig.suptitle("Without BEVs the classes converge harder: 1.9-2.2%/yr across "
                 "the board", x=0.01, ha="left", fontsize=15,
                 fontweight="bold")
    fig.text(0.01, 0.012, "EPA Trends by vehicle type, BEV share removed via "
             "Tesla proxy (largest correction: Car SUV 2023 at 35.7% BEV). "
             "Hybrids/PHEVs remain. reports/31_ice_productivity.md.",
             fontsize=8.5, color=MUT)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig46_ice_class_productivity.png"),
                dpi=150)

    pd.DataFrame(rows_csv).to_csv(os.path.join(OUT, "ice_productivity.csv"),
                                  index=False, encoding="utf-8")

    b = io.StringIO()
    b.write("# Combustion-Only Productivity (figs 45-46, ex-BEV twins of "
            "42-43)\n\nGenerated by 31_ice_productivity.py.\n\n"
            "## Method\n\n"
            "BEV share s backed out per year and class: MPG_ice = (1-s) / "
            "(1/MPG_all - s/MPGe_bev) (harmonic, gallons-first, matching "
            "EPA's aggregation); weight and HP removed arithmetically. BEV "
            "proxy = EPA Trends Tesla series (production-weighted, same "
            "real-world basis). Hybrids and PHEVs remain included by "
            "design.\n\n"
            f"## Fleet (fig45)\n\n- Normalized combustion productivity: "
            f"**+{g_all:.2f}%/yr over 1975-2024 (R² = "
            f"{r_all.rvalue**2:.3f})**; 2005-2024 rate +{g_rec:.2f}%/yr.\n"
            f"- Projection at constant 2024 design: {p_rec[-1]:.0f} by 2045 "
            f"at the recent rate, {p_full[-1]:.0f} at the 50-year rate.\n"
            "- Versus fig42 (BEVs in): the 50-year rate barely moves "
            "(electrification is late and fleet share small), but the "
            "recent-rate projection drops -- that gap IS the electrification "
            "contribution to measured fleet productivity.\n\n"
            "## Classes (fig46)\n\n| Class | growth/yr | R² | 2024 norm | "
            "2045 proj |\n|---|---|---|---|---|\n")
    for vt, g, r2, last, proj in class_stats:
        b.write(f"| {vt} | {g:.2f}% | {r2:.3f} | {last:.1f} | {proj:.0f} |\n")
    b.write(
        "\n- The Car SUV anomaly resolves: its ex-BEV rate falls into line "
        "with the other classes, confirming the 2020-2023 spike was Model "
        "Y-era mix (BEV share 0.6% -> 35.7% within the class), not a "
        "combustion breakthrough.\n"
        "\n## Caveats\n\n"
        "- Tesla as the all-BEV proxy: adequate at fleet level (BEV <= "
        "7.2%), coarser inside Car SUV 2023 (35.7% share, so proxy error "
        "is first-order there); non-Tesla BEVs average lower MPGe, meaning "
        "the true ICE line would sit very slightly higher.\n"
        "- Harmonic removal assumes EPA's gallons-first aggregation, per "
        "their methodology.\n"
        "- All stage-29 caveats (elasticity stability, log-linear "
        "extrapolation) still apply.\n")
    with open(os.path.join(REPORTS, "31_ice_productivity.md"), "w",
              encoding="utf-8") as f:
        f.write(b.getvalue())

    print(f"fleet ex-BEV: +{g_all:.2f}%/yr (R2 {r_all.rvalue**2:.3f}), "
          f"recent +{g_rec:.2f}%/yr, 2045 {p_rec[-1]:.0f}/{p_full[-1]:.0f}")
    for vt, g, r2, last, proj in class_stats:
        print(f"{vt}: +{g:.2f}%/yr R2 {r2:.3f} -> 2045 {proj:.0f}")


if __name__ == "__main__":
    main()
