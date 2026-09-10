"""28_msrp.py -- model-level MSRP data (CarAPI sample feed, 2015-2020).

Source: CarAPI vehicle data feed FREE SAMPLE, downloaded 2026-09-10 from
https://carapi.app/sample-opendatafeed (linked from
https://carapi.app/features/vehicle-csv-download/), archived at
external/carapi_sample_datafeed.zip. 17,573 US trims, model years
2015-2020, with trim-level MSRP and dealer invoice. The sample is the
freely distributed evaluation feed; current-year data is paid, which is
why 2021+ MSRPs remain the hand-fill scaffold
(external/msrp_model_level.csv).

This stage classifies each trim's powertrain by joining to the
fueleconomy.gov catalog on (make, model, year) with prefix-tolerant name
matching, then writes:

  outputs/msrp_2015_2020.csv   trim rows + powertrain group
  reports/28_msrp.md           coverage, join rate, median MSRP by group
  charts/fig41_msrp_by_powertrain.png

Caveats carried everywhere: 2015-2020 era (pre-dates the mainstream EV
wave); MSRP is the asking price, not the transaction price (fig37 covers
ATP); Tesla model names normalized ('3' -> 'Model 3').
"""

import io
import os
import re
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
REPORTS = os.path.join(HERE, "reports")
CHARTS = os.path.join(HERE, "charts")
ZIP = os.path.join(HERE, "external", "carapi_sample_datafeed.zip")

S1, S2, S3, S5 = "#2a78d6", "#eb6834", "#1baf7a", "#e87ba4"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE = "#898781", "#e1e0d9", "#c3c2b7"
COLORS = {"BEV": S1, "Gasoline": S2, "Hybrid": S3, "FCEV": S5}

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "font.size": 11,
})


def norm(s):
    s = str(s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\b([a-z]) (\d{2,4})\b", r"\1\2", s)
    return s


def cat_group(r):
    if r.fuelType1 == "Hydrogen":
        return "FCEV"
    if r.fuelType1 == "Electricity":
        return "BEV"
    if isinstance(r.atvType, str) and r.atvType == "Plug-in Hybrid":
        return "PHEV"
    if isinstance(r.atvType, str) and r.atvType == "Hybrid":
        return "Hybrid"
    if r.fuelType1 == "Diesel":
        return "Diesel"
    if isinstance(r.fuelType1, str) and "Gasoline" in r.fuelType1:
        return "Gasoline"
    return "Other"


def main():
    os.makedirs(CHARTS, exist_ok=True)
    z = zipfile.ZipFile(ZIP)
    t = pd.read_csv(io.BytesIO(z.read("trims-sample.csv")))
    t = t[t["Trim MSRP"] > 0].copy()
    t["make"] = t["Make Name"]
    # Tesla names its models '3', 'S', 'X', 'Y' in this feed.
    t["model"] = np.where(t.make == "Tesla", "Model " + t["Model Name"].astype(str),
                          t["Model Name"].astype(str))
    t["k_make"] = t.make.map(norm)
    t["k_model"] = t.model.map(norm)

    cat = pd.read_csv(os.path.join(OUT, "catalog_fegov.csv"), low_memory=False)
    cat = cat[cat.year.between(2015, 2020)].copy()
    cat["grp"] = cat.apply(cat_group, axis=1)
    cat["k_make"] = cat["canonical_make"].map(norm)
    cat["k_model"] = cat["baseModel"].map(norm)

    # (make, model) -> dominant powertrain group per year; prefix-tolerant.
    by_make = {}
    for (mk, md, yr), g in cat.groupby(["k_make", "k_model", "year"]):
        by_make.setdefault(mk, {}).setdefault(md, {})[yr] = g.grp.mode().iloc[0]

    def classify(mk, md, yr):
        models = by_make.get(mk)
        if not models:
            return None
        cands = []
        for cm in models:
            if cm == md or cm.startswith(md + " ") or md.startswith(cm + " ") \
               or cm == md.split()[0] or md == cm.split()[0]:
                cands.append(cm)
        if md in models:
            cands = [md]
        if not cands:
            return None
        cm = max(cands, key=len)
        years = models[cm]
        if yr in years:
            return years[yr]
        return pd.Series(list(years.values())).mode().iloc[0]

    t["group"] = [classify(r.k_make, r.k_model, r["Model Year"])
                  for _, r in t.iterrows()]
    matched = t.group.notna().mean()
    d = t[t.group.notna()].copy()
    d.to_csv(os.path.join(OUT, "msrp_2015_2020.csv"), index=False,
             encoding="utf-8")

    core = d[d.group.isin(["BEV", "Hybrid", "Gasoline", "FCEV"])]
    med = core.groupby(["Model Year", "group"])["Trim MSRP"].median().unstack()
    cnt = core.groupby(["Model Year", "group"]).size().unstack()

    b = io.StringIO()
    b.write("# Model-Level MSRP, 2015-2020 (CarAPI sample feed)\n\n"
            "Generated by 28_msrp.py. Source and archive noted in the "
            "script header and DATA_SOURCES.md.\n")
    b.write(f"\n## Coverage\n\n- {len(t):,} trims with MSRP; powertrain "
            f"classified for {matched:.1%} via fueleconomy.gov catalog join "
            "(prefix-tolerant make/model match); unmatched rows dropped "
            "from group analysis but kept in no file (they lack a "
            "powertrain label).\n"
            f"- Kept for the four-group comparison: {len(core):,} trims.\n")
    b.write("\n## Median trim MSRP by powertrain\n\n")
    b.write(med.round(0).to_string() + "\n\n### Trim counts\n\n"
            + cnt.to_string())
    b.write("\n\n## Caveats\n\n"
            "- 2015-2020: the early-EV era. BEV medians here reflect "
            "Bolt/Leaf/Tesla-S/X pricing, not today's market; the 2026 "
            "acquisition-cost picture is fig37 (KBB ATP).\n"
            "- MSRP is the asking price; transactions (fig37) include "
            "incentives and mix.\n"
            "- Trim-level medians: luxury brands list many trims, so these "
            "are catalog medians, not sales-weighted prices.\n"
            "- Sample feed is free for evaluation; cite as 'CarAPI vehicle "
            "data feed, free sample, accessed 2026-09-10'.\n")
    with open(os.path.join(REPORTS, "28_msrp.md"), "w", encoding="utf-8") as f:
        f.write(b.getvalue())

    fig, ax = plt.subplots(figsize=(11, 6.4))
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", visible=False)
    ends = []
    for grp, c in COLORS.items():
        if grp not in med.columns:
            continue
        s = med[grp].dropna()
        marker = "o-" if grp == "FCEV" else "-"
        ax.plot(s.index, s.values, marker, color=c, lw=2, ms=5)
        ends.append((grp, c, s.index[-1], s.values[-1]))
    ends.sort(key=lambda e: e[3])
    used = []
    for grp, c, x, y in ends:
        yy = y
        while any(abs(yy - u) < 2800 for u in used):
            yy += 2800
        used.append(yy)
        ax.text(x + 0.08, yy, grp, color=c, fontweight="bold",
                fontsize=10.5, va="center")
    ax.annotate("BEV median swings on 11-31 trims/yr:\nBolt/Leaf years vs "
                "Tesla-heavy years", xy=(2017, 58490), xytext=(2015.1, 66000),
                fontsize=9.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_ylim(0, 80000)
    ax.set_yticks(range(0, 80001, 20000))
    ax.set_yticklabels(["\\$0", "\\$20k", "\\$40k", "\\$60k", "\\$80k"])
    ax.set_title("Median trim-level MSRP by powertrain (catalog medians, not "
                 "sales-weighted)", loc="left", fontsize=10.5, color=INK2,
                 pad=8)
    fig.suptitle("Sticker prices 2015-2020: the era when electric meant expensive",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.012, "CarAPI sample data feed (17.5k US trims, MSRP + "
             "invoice), powertrain via fueleconomy.gov join. FCEV = Toyota "
             "Mirai only. Compare fig37 for 2026 transaction prices.",
             fontsize=8.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(os.path.join(CHARTS, "fig41_msrp_by_powertrain.png"), dpi=150)

    print(f"match rate {matched:.1%} | core rows {len(core):,}")
    print(med.round(0).to_string())


if __name__ == "__main__":
    main()
