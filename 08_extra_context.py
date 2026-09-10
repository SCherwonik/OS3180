"""08_extra_context.py -- safety data, sales split, and events timeline.

Inputs:
  external/bts_table_2_17_safety.xlsx  BTS NTS Table 2-17 (fatalities, VMT,
      fatality rate per 100M VMT; 5-year steps 1960-1985, annual 1990+).
      Retrieved via browser 2026-08-14; bts.gov blocks CLI clients.
  external/fred_DAUTOSAAR.csv / fred_FAUTOSAAR.csv   BEA retail unit sales,
      domestic/foreign autos, millions SAAR, monthly, 1967+
  external/fred_DLTRUCKSSAAR.csv / fred_FLTRUCKSSAAR.csv  same, light trucks

Outputs:
  outputs/context_extra.csv       year, fatalities, fatality rate, sales split
  external/events_timeline.csv    curated documented events (written here so
                                  a rerun regenerates it; sources per row)
  reports/08_extra_sources.md     source notes

Idempotent; no imputation. Sales are calendar-year means of monthly SAAR.
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(HERE, "external")
OUT = os.path.join(HERE, "outputs")
REPORTS = os.path.join(HERE, "reports")

# Documented events. type: regulation | scandal | market. Each row cites a
# public source. These annotate charts; they are not measurements.
EVENTS = [
    (1964, "1963-12-04", "'Chicken tax': 25% tariff on imported light trucks",
     "regulation", "Presidential Proclamation 3564"),
    (1973, "1973-10", "OPEC oil embargo begins", "market",
     "U.S. State Dept. Office of the Historian, Milestones 1969-1976"),
    (1974, "1974-01-02", "55 mph national speed limit imposed", "regulation",
     "Emergency Highway Energy Conservation Act, Pub. L. 93-239"),
    (1975, "1975-12-22", "Energy Policy and Conservation Act creates CAFE",
     "regulation", "Pub. L. 94-163"),
    (1979, "1979-01", "Iranian revolution; second oil shock", "market",
     "EIA petroleum chronology"),
    (1985, "1985", "Passenger-car CAFE standard reaches 27.5 MPG, then frozen",
     "regulation", "NHTSA CAFE standards table"),
    (2007, "2007-12-19", "Energy Independence and Security Act: 35 MPG by 2020",
     "regulation", "Pub. L. 110-140"),
    (2008, "2008", "EPA adopts 5-cycle fuel-economy labels", "regulation",
     "EPA 40 CFR Part 600 label rule"),
    (2010, "2010-12", "First mass-market plug-ins delivered (Leaf, Volt)",
     "market", "Nissan/GM December 2010 delivery announcements"),
    (2012, "2012-11-02", "EPA announces Hyundai/Kia fuel-economy restatement",
     "scandal", "EPA press release, Nov. 2, 2012"),
    (2013, "2013-08", "Ford lowers C-Max hybrid label from 47 to 43 MPG",
     "scandal", "EPA/Ford announcement, Aug. 2013"),
    (2014, "2014-06-12", "Ford relabels six 2013-14 models downward", "scandal",
     "Ford Motor Co. announcement, June 12, 2014"),
    (1995, "1995-11-28", "55 mph national speed limit repealed", "regulation",
     "National Highway System Designation Act, Pub. L. 104-59"),
    (2015, "2015-09-18", "EPA issues VW notice of violation (Dieselgate)",
     "scandal", "https://www.epa.gov/vw"),
    (2020, "2020-03", "COVID-19 production shutdowns", "market",
     "BEA/industry production records"),
    (2022, "2022-08-16", "Inflation Reduction Act revamps EV tax credits",
     "regulation", "Pub. L. 117-169"),
]


def parse_bts():
    df = pd.read_excel(os.path.join(EXT, "bts_table_2_17_safety.xlsx"),
                       sheet_name="2-17", header=None)
    years = pd.to_numeric(df.iloc[1, 1:], errors="coerce")
    rows = {}
    for idx, name in [(2, "fatalities"), (5, "bts_vmt_million_miles"),
                      (7, "fatality_rate_per_100m_vmt")]:
        vals = pd.to_numeric(df.iloc[idx, 1:], errors="coerce")
        rows[name] = pd.Series(vals.values, index=years.values)
    out = pd.DataFrame(rows)
    out = out[out.index.notna()]
    out.index = out.index.astype(int)
    out.index.name = "year"
    return out.dropna(how="all")


def annual_mean(fname, col):
    df = pd.read_csv(os.path.join(EXT, fname))
    df.columns = ["date", col]
    df["date"] = pd.to_datetime(df["date"])
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df["year"] = df["date"].dt.year
    counts = df.dropna(subset=[col]).groupby("year")[col].count()
    means = df.groupby("year")[col].mean()
    return means.loc[counts[counts >= 6].index]


def main():
    os.makedirs(OUT, exist_ok=True)
    bts = parse_bts()

    da = annual_mean("fred_DAUTOSAAR.csv", "da")
    fa = annual_mean("fred_FAUTOSAAR.csv", "fa")
    dl = annual_mean("fred_DLTRUCKSSAAR.csv", "dl")
    fl = annual_mean("fred_FLTRUCKSSAAR.csv", "fl")
    sales = pd.concat([da, fa, dl, fl], axis=1)
    sales["auto_sales_millions_saar"] = sales.da + sales.fa
    sales["lt_sales_millions_saar"] = sales.dl + sales.fl
    sales["lt_share_of_sales"] = sales.lt_sales_millions_saar / (
        sales.auto_sales_millions_saar + sales.lt_sales_millions_saar)
    sales = sales.drop(columns=["da", "fa", "dl", "fl"])
    sales.index.name = "year"

    ctx = bts.join(sales, how="outer").reset_index()
    ctx = ctx[ctx.year >= 1960]
    ctx.to_csv(os.path.join(OUT, "context_extra.csv"), index=False,
               encoding="utf-8")

    ev = pd.DataFrame(EVENTS, columns=["year", "date", "event", "type", "source"])
    ev.to_csv(os.path.join(EXT, "events_timeline.csv"), index=False,
              encoding="utf-8")

    with open(os.path.join(REPORTS, "08_extra_sources.md"), "w",
              encoding="utf-8") as f:
        f.write(
            "# Extra Context Sources\n\nGenerated by 08_extra_context.py.\n\n"
            "## outputs/context_extra.csv\n\n"
            "| Column | Source | Notes |\n|---|---|---|\n"
            "| `fatalities` | BTS NTS Table 2-17 (FARS-based) | 5-year steps "
            "1960-1985, annual 1990+; 30-day death definition |\n"
            "| `bts_vmt_million_miles` | same table (FHWA) | matches FRED VMT "
            "closely; kept separate for rate consistency |\n"
            "| `fatality_rate_per_100m_vmt` | same table, BTS-calculated | THE "
            "safety series; do not recompute from mixed sources |\n"
            "| `auto_sales_millions_saar` | BEA via FRED DAUTOSAAR+FAUTOSAAR | "
            "calendar-year mean of monthly SAAR, 1967+ |\n"
            "| `lt_sales_millions_saar` | BEA via FRED DLTRUCKSSAAR+FLTRUCKSSAAR "
            "| same |\n"
            "| `lt_share_of_sales` | derived | light-truck share of light-"
            "vehicle SALES; compare with production share but note sales != "
            "production and calendar != model year |\n\n"
            "## external/events_timeline.csv\n\n"
            "Curated documented events (regulation/scandal/market) with a "
            "source citation per row. Annotation layer only; not measurements. "
            "Regenerated by this script on every run.\n\n"
            "Retrieval note: bts.gov and nhtsa.gov block command-line clients "
            "(403). The BTS workbook was retrieved through the user's browser "
            "on 2026-08-14. The NHTSA FARS API was abandoned for this reason; "
            "BTS Table 2-17 carries the same FARS-based fatality series.\n"
        )

    print(f"context_extra.csv: {len(ctx)} years "
          f"({int(ctx.year.min())}-{int(ctx.year.max())})")
    for y in (1975, 1990, 2010, 2024):
        r = ctx[ctx.year == y]
        if len(r):
            r = r.iloc[0]
            print(y, "| fat rate", r.fatality_rate_per_100m_vmt,
                  "| lt sales share",
                  None if pd.isna(r.lt_share_of_sales) else round(r.lt_share_of_sales, 3))


if __name__ == "__main__":
    main()
