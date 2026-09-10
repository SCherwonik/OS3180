"""14_more_context.py -- credit, energy-parity, fleet-age, household-size.

Inputs:
  external/fred_autoloan48.csv     TERMCBAUTO48NS, 48-mo new-car loan rate,
                                   %, monthly, 1972+ (Fed G.19 via FRED)
  external/fred_electricity.csv    APU000072610, electricity $/kWh, US city
                                   average, monthly, 1978+ (BLS via FRED)
  external/bts_table_1_26_fleet_age.xlsx  BTS NTS Table 1-26a, average age of
                                   light vehicles in operation, 1995+
                                   (retrieved via browser; bts.gov blocks CLI)
  outputs/catalog_fegov.csv        EV energy consumption (combE, kWh/100mi)
  outputs/analysis_clean.csv       real-world MPG; truck share
  outputs/context_annual.csv       nominal gas price

Household size is a small hardcoded table from Census Bureau Table HH-4
(average population per household, CPS-based), 5-year sampling.

Outputs:
  outputs/context_finance.csv   year-keyed: loan rate, electricity price,
                                gas & EV cost per mile, parity ratio,
                                fleet age, household size
  reports/14_more_sources.md    sources, units, and the credit-story audit
                                (levels + differenced regression vs truck
                                share, same honesty test as fig19)
"""

import io
import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(HERE, "external")
OUT = os.path.join(HERE, "outputs")
REPORTS = os.path.join(HERE, "reports")

# Census Bureau, Table HH-4 "Households by Size" (average population per
# household), selected years. Sparse on purpose; charted as markers only.
HOUSEHOLD_SIZE = {
    1975: 2.94, 1980: 2.76, 1985: 2.69, 1990: 2.63, 1995: 2.65,
    2000: 2.62, 2005: 2.57, 2010: 2.59, 2015: 2.54, 2020: 2.53, 2024: 2.51,
}


def annual_mean(fname, col, min_obs=6):
    """min_obs=3 for the loan series: G.19 reports it quarterly."""
    df = pd.read_csv(os.path.join(EXT, fname))
    df.columns = ["date", col]
    df["date"] = pd.to_datetime(df["date"])
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df["year"] = df["date"].dt.year
    counts = df.dropna(subset=[col]).groupby("year")[col].count()
    means = df.groupby("year")[col].mean()
    return means.loc[counts[counts >= min_obs].index]


def fleet_age():
    df = pd.read_excel(os.path.join(EXT, "bts_table_1_26_fleet_age.xlsx"),
                       sheet_name="1-26", header=None)
    # Table 1-26a is the first contiguous numeric-year block; a second NHTS
    # table ("average age of household vehicles") sits below it -- stop at
    # the first non-numeric year cell.
    rows = []
    for i in range(2, len(df)):
        y = pd.to_numeric(pd.Series([df.iloc[i, 0]]), errors="coerce").iloc[0]
        if pd.isna(y):
            break
        rows.append((int(y), pd.to_numeric(pd.Series([df.iloc[i, 3]]),
                                           errors="coerce").iloc[0]))
    s = pd.Series({y: v for y, v in rows}).dropna()
    return s.rename("fleet_avg_age_years")


def main():
    loan = annual_mean("fred_autoloan48.csv", "autoloan_48mo_rate_pct", min_obs=3)
    elec = annual_mean("fred_electricity.csv", "electricity_usd_kwh")
    age = fleet_age()

    ctx = pd.read_csv(os.path.join(OUT, "context_annual.csv"))
    ac = pd.read_csv(os.path.join(OUT, "analysis_clean.csv"))
    aa = ac[(ac.manufacturer == "All") & (ac.regulatory_class == "All")
            & (ac.vehicle_type == "All")][["model_year", "real_world_mpg"]]
    cat = pd.read_csv(os.path.join(OUT, "catalog_fegov.csv"), low_memory=False)

    # EV energy use: unweighted catalog mean of combE (kWh/100mi) per year.
    ev = cat[(cat.fuelType1 == "Electricity") & (cat.combE > 0)]
    ev_kwh100 = ev.groupby("year")["combE"].mean().rename("ev_kwh_per_100mi")

    f = (pd.DataFrame({"year": range(1972, 2027)})
         .merge(loan.reset_index(), on="year", how="left")
         .merge(elec.reset_index(), on="year", how="left")
         .merge(age.reset_index().rename(columns={"index": "year"}),
                on="year", how="left")
         .merge(ev_kwh100.reset_index(), on="year", how="left")
         .merge(ctx[["year", "gas_nominal_usd_gal"]], on="year", how="left")
         .merge(aa.rename(columns={"model_year": "year"}), on="year", how="left"))
    f["household_avg_size"] = f.year.map(HOUSEHOLD_SIZE)

    # Cost per mile, both in nominal dollars of the same year (ratio is
    # inflation-invariant). Gas: fleet real-world MPG. EV: catalog mean
    # consumption. Fuel/energy only -- no depreciation, insurance, purchase.
    f["gas_cost_per_mile"] = f.gas_nominal_usd_gal / f.real_world_mpg
    f["ev_cost_per_mile"] = f.electricity_usd_kwh * f.ev_kwh_per_100mi / 100.0
    f["gas_over_ev_cost_ratio"] = f.gas_cost_per_mile / f.ev_cost_per_mile

    f.to_csv(os.path.join(OUT, "context_finance.csv"), index=False,
             encoding="utf-8")

    # Credit-story audit: loan rate vs truck share, held to the fig19 standard.
    trk = (ac[(ac.manufacturer == "All") & (ac.vehicle_type == "All Truck")
              & (~ac.is_preliminary)][["model_year", "production_share"]]
           .rename(columns={"model_year": "year", "production_share": "truck"}))
    m = trk.merge(loan.reset_index(), on="year").dropna().sort_values("year")
    lv = stats.linregress(m.autoloan_48mo_rate_pct, m.truck)
    dm = m.set_index("year").diff().dropna()
    df_ = stats.linregress(dm.autoloan_48mo_rate_pct, dm.truck)

    b = io.StringIO()
    b.write(
        "# More Context Sources: credit, energy parity, fleet age, households\n\n"
        "Generated by 14_more_context.py. One row per year in "
        "outputs/context_finance.csv.\n\n"
        "| Column | Source | Units / notes |\n|---|---|---|\n"
        "| `autoloan_48mo_rate_pct` | Fed G.19 via FRED TERMCBAUTO48NS: "
        "https://fred.stlouisfed.org/series/TERMCBAUTO48NS | %, 48-month new-car "
        "loans, annual mean of monthly, 1972+ |\n"
        "| `electricity_usd_kwh` | BLS via FRED APU000072610: "
        "https://fred.stlouisfed.org/series/APU000072610 | $/kWh, US city "
        "average, 1978+ |\n"
        "| `fleet_avg_age_years` | BTS NTS Table 1-26a: "
        "https://www.bts.gov/content/average-age-automobiles-and-trucks-"
        "operation-united-states | years, all light vehicles in operation, "
        "1995+; retrieved via user's browser (bts.gov blocks CLI) |\n"
        "| `household_avg_size` | Census Bureau Table HH-4 (hardcoded, "
        "5-year sampling): https://www.census.gov/data/tables/time-series/"
        "demo/families/households.html | persons per household |\n"
        "| `ev_kwh_per_100mi` | derived from catalog_fegov.csv (`combE`, "
        "EVs only, unweighted catalog mean) | kWh/100mi |\n"
        "| `gas_cost_per_mile` | derived: nominal gas $/gal / fleet real-world "
        "MPG | $/mile, fuel only |\n"
        "| `ev_cost_per_mile` | derived: $/kWh x kWh/mile | $/mile, energy "
        "only; excludes purchase price, depreciation, home-vs-DC charging "
        "mix |\n"
        "| `gas_over_ev_cost_ratio` | derived | >1 means driving on "
        "electricity is cheaper per mile |\n\n"
        "## Credit-story audit (the fig19 honesty standard)\n\n"
        "Loan rate vs truck share of production, 1972-2024:\n\n"
        "| Specification | slope | R^2 | p |\n|---|---|---|---|\n"
        f"| Levels | {lv.slope:.4f} | {lv.rvalue**2:.3f} | {lv.pvalue:.1e} |\n"
        f"| First differences | {df_.slope:.4f} | {df_.rvalue**2:.3f} | "
        f"{df_.pvalue:.2f} |\n\n"
    )
    audit = ("Same verdict as gas prices: the levels relationship is the "
             "secular-trend illusion (rates fell for four decades while truck "
             "share rose for five), and the differenced relationship is "
             "indistinguishable from noise. The credit story joins the "
             "gas-price story in the 'seductive overlay, no annual "
             "association' bin. Present as revision #7, not as a cause.\n"
             if df_.pvalue > 0.05 else
             "Unlike gas prices, the differenced relationship IS significant: "
             "year-to-year rate changes co-move with truck-share changes. "
             "The credit story survives the audit that killed the gas story.\n")
    b.write(audit)
    with open(os.path.join(REPORTS, "14_more_sources.md"), "w",
              encoding="utf-8") as fo:
        fo.write(b.getvalue())

    print("context_finance.csv written")
    print("loan levels R2:", round(lv.rvalue**2, 3), "p:", f"{lv.pvalue:.1e}")
    print("loan diffs R2:", round(df_.rvalue**2, 3), "p:", round(df_.pvalue, 3))
    r = f.dropna(subset=["gas_over_ev_cost_ratio"])
    for y in (2012, 2020, 2024):
        row = r[r.year == y]
        if len(row):
            row = row.iloc[0]
            print(y, "| gas c/mi", round(row.gas_cost_per_mile, 3),
                  "| ev c/mi", round(row.ev_cost_per_mile, 3),
                  "| ratio", round(row.gas_over_ev_cost_ratio, 2))
    print("fleet age 1995:", age.get(1995), "-> 2023:", age.get(2023),
          "2024:", age.get(2024))


if __name__ == "__main__":
    main()
