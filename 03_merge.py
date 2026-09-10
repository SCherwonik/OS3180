"""03_merge.py -- Phase 3: build outputs; Phase 4: merge report.

Outputs:
  outputs/full_wide.csv       every source row, outer logic, source-prefixed
  outputs/analysis_clean.csv  Trends by-manufacturer spine + offer-side aggregates
  outputs/my2024_config.csv   files 3+4 joined at carline level
  outputs/catalog_fegov.csv   vehicles.csv + canonical manufacturer columns
  reports/03_merge_report.md  spine rationale, data dictionary, row accounting,
                              fuel-economy definition warnings

Idempotent: every run regenerates all five from the source CSVs and the
crosswalk produced by 02_crosswalk.py.
"""

import io
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "outputs")
REPORT_DIR = os.path.join(HERE, "reports")

F_MFR = "Data by Manufacturer.csv"
F_VTYPE = "Data by Vehicle Type.csv"
F_MY24FE = "model-year-2024-fuel-economy-and-technology-data.csv"
F_MY24FP = "model-year-2024-footprint-data.csv"
F_FEGOV = "vehicles.csv"

STAGES = []          # (stage, rows, note) -> row-accounting table
COERCIONS = []       # (file, action, count) -> coercion log


def log_stage(stage, rows, note=""):
    STAGES.append((stage, rows, note))


def read_csv_robust(path):
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"could not read {path}")


def norm(s):
    s = str(s).lower()
    s = re.sub(r"[.,;:'\"()&/\\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------------------------------------------------------------------------
# Trends cleaning
# ---------------------------------------------------------------------------

def parse_measure(series, fname, col):
    """'-' -> NaN; '4.4%' -> 0.044; plain numbers pass through.
    Every coercion is counted, nothing else is touched."""
    s = series.astype(str).str.strip()
    n_dash = int(s.isin(["-", ""]).sum())
    pct_mask = s.str.endswith("%", na=False)
    n_pct = int(pct_mask.sum())
    s = s.replace({"-": None, "": None})
    out = pd.Series(np.nan, index=s.index, dtype=float)
    out[pct_mask] = pd.to_numeric(s[pct_mask].str.rstrip("%"), errors="coerce") / 100.0
    rest = ~pct_mask & s.notna()
    out[rest] = pd.to_numeric(s[rest].str.replace(",", ""), errors="coerce")
    if n_dash:
        COERCIONS.append((fname, f"`{col}`: '-' treated as null", n_dash))
    if n_pct:
        COERCIONS.append((fname, f"`{col}`: percent string / 100 -> fraction", n_pct))
    return out


def clean_trends(df, fname):
    out = df.copy()
    prelim = out["Model Year"].eq("Prelim. 2025")
    out["model_year"] = out["Model Year"].replace({"Prelim. 2025": "2025"}).astype(int)
    out["is_preliminary"] = prelim
    COERCIONS.append((fname, "`Model Year` 'Prelim. 2025' -> 2025 + is_preliminary flag",
                      int(prelim.sum())))
    dims = {"Manufacturer", "Model Year", "Regulatory Class", "Vehicle Type",
            "model_year", "is_preliminary"}
    for col in out.columns:
        if col not in dims:
            out[col] = parse_measure(out[col], fname, col)
    return out


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    xw = pd.read_csv(os.path.join(HERE, "crosswalk", "manufacturer_crosswalk.csv"))
    make_map = {
        r.raw_value: (r.canonical_make, r.canonical_parent if pd.notna(r.canonical_parent) else None)
        for r in xw[xw.source_column == "make"].itertuples()
    }
    div_map = {
        r.raw_value: (r.canonical_make, r.canonical_parent if pd.notna(r.canonical_parent) else None)
        for r in xw[xw.source_column == "MFR_DIVISION_SHORT_NM"].itertuples()
    }

    trends_mfr = read_csv_robust(os.path.join(HERE, F_MFR))
    trends_vt = read_csv_robust(os.path.join(HERE, F_VTYPE))
    fe = read_csv_robust(os.path.join(HERE, F_MY24FE))
    fp = read_csv_robust(os.path.join(HERE, F_MY24FP))
    veh = read_csv_robust(os.path.join(HERE, F_FEGOV))
    for name, df in [(F_MFR, trends_mfr), (F_VTYPE, trends_vt), (F_MY24FE, fe),
                     (F_MY24FP, fp), (F_FEGOV, veh)]:
        log_stage(f"input: {name}", len(df))

    tm = clean_trends(trends_mfr, F_MFR)
    tv = clean_trends(trends_vt, F_VTYPE)

    # ---- catalog_fegov.csv ------------------------------------------------
    cat = veh.copy()
    cat["canonical_make"] = cat["make"].map(lambda s: make_map.get(s, (s, None))[0])
    cat["canonical_parent"] = cat["make"].map(lambda s: make_map.get(s, (s, None))[1])
    cat = cat.sort_values(["year", "make", "model", "id"]).reset_index(drop=True)
    cat.to_csv(os.path.join(OUT_DIR, "catalog_fegov.csv"), index=False, encoding="utf-8")
    log_stage("output: catalog_fegov.csv", len(cat),
              "vehicles.csv + canonical make/parent; no rows dropped")

    # ---- my2024_config.csv ------------------------------------------------
    fe_k = fe.add_prefix("src_my24fe_")
    fp_k = fp.add_prefix("src_my24fp_")
    fe_k["_mfr"] = fe["Carline Mfr Code"].str.strip()
    fe_k["_div"] = fe["DIVISION_CD"]
    fe_k["_car"] = fe["CARLINE_CODE"]
    fp_k["_mfr"] = fp["FOOTPRINT_MFR_CD"].str.strip()
    fp_k["_div"] = fp["FTPT_DIVISION_CD"]
    fp_k["_car"] = fp["FTPT_CARLINE_CD"]
    keys = ["_mfr", "_div", "_car"]

    my24 = fe_k.merge(fp_k, on=keys, how="outer", indicator=True)
    assert (my24["_merge"] == "both").all(), "carline join no longer 100%"
    my24 = my24.drop(columns=["_merge"])
    log_stage("join: my24fe x my24fp on (mfr cd, div cd, carline cd)", len(my24),
              f"outer==inner, 100% both sides; {len(my24)/len(fe):.1f}x FE rows "
              "(model-type x footprint-config within carline)")

    # Carline production volume, deduped to one row per model type first,
    # because Model_Type_Actual_Prod_Vol repeats on every configuration row.
    mt = fe.drop_duplicates(subset=["Carline Mfr Code", "CARLINE_CODE", "MODEL_TYPE_INDEX"])
    carline_vol = (
        mt.assign(_mfr=mt["Carline Mfr Code"].str.strip(),
                  _div=mt["DIVISION_CD"], _car=mt["CARLINE_CODE"])
        .groupby(keys)["Model_Type_Actual_Prod_Vol"].sum()
        .rename("derived_carline_prod_vol")
    )
    my24 = my24.merge(carline_vol, on=keys, how="left")
    my24 = my24.sort_values(
        ["_mfr", "_div", "_car", "src_my24fe_MODEL_TYPE_INDEX",
         "src_my24fp_FOOTPRINT_INDEX"]).drop(columns=keys).reset_index(drop=True)
    my24.to_csv(os.path.join(OUT_DIR, "my2024_config.csv"), index=False, encoding="utf-8")
    log_stage("output: my2024_config.csv", len(my24))

    # ---- analysis_clean.csv ----------------------------------------------
    RENAMES = {
        "Production (000)": "production_thousands",
        "Production Share": "production_share",
        "2-Cycle MPG": "cafe_2cycle_mpg",
        "Real-World MPG": "real_world_mpg",
        "Real-World MPG_City": "real_world_mpg_city",
        "Real-World MPG_Hwy": "real_world_mpg_hwy",
        "Weight (lbs)": "weight_lbs",
        "Footprint (sq. ft.)": "footprint_sqft",
        "Engine Displacement": "engine_displacement_cid",
        "Horsepower (HP)": "horsepower_hp",
        "Acceleration (0-60 time in seconds)": "accel_0_60_s",
        "HP/Engine Displacement": "hp_per_cid",
        "HP/Weight (lbs)": "hp_per_lb",
        "Ton-MPG (Real-World)": "ton_mpg_real_world",
        # Averages, not shares; kept out of the mechanical share_ renaming.
        "Average Number of Gears in Gasoline ICE non-Hybrids": "avg_gears_gasoline_ice_nonhybrid",
        "Cylinders in Gasoline ICE Vehicles": "avg_cylinders_gasoline_ice",
    }
    ac = tm.rename(columns=RENAMES)
    # Remaining share/tech columns: snake_case them mechanically; the mapping
    # is emitted into the data dictionary below.
    auto_renames = {}
    for col in ac.columns:
        if col in ("Manufacturer", "Regulatory Class", "Vehicle Type",
                   "Model Year", "model_year", "is_preliminary") or col in RENAMES.values():
            continue
        new = re.sub(r"[^0-9a-zA-Z]+", "_", col).strip("_").lower()
        auto_renames[col] = "share_" + new
    ac = ac.rename(columns=auto_renames)
    ac = ac.rename(columns={"Manufacturer": "manufacturer",
                            "Regulatory Class": "regulatory_class",
                            "Vehicle Type": "vehicle_type"})
    ac = ac.drop(columns=["Model Year"])  # replaced by model_year int; recorded in dictionary

    # Offer-side derived aggregates from the catalog, attached only to the
    # Regulatory Class='All' x Vehicle Type='All' rows so the grain of the
    # derived numbers matches the grain of the row they sit on.
    gas = cat[cat["fuelType1"] != "Electricity"]
    per_parent = cat[cat["canonical_parent"].notna()].groupby(
        ["year", "canonical_parent"]).agg(
        catalog_n_configurations=("id", "size"),
        catalog_n_models=("baseModel", "nunique"),
        catalog_n_ev_configurations=("fuelType1", lambda s: int((s == "Electricity").sum())),
    ).reset_index()
    gas_mpg = gas[gas["canonical_parent"].notna()].groupby(
        ["year", "canonical_parent"])["comb08"].mean().rename(
        "catalog_mean_label_comb_mpg_gas").reset_index()
    per_parent = per_parent.merge(gas_mpg, on=["year", "canonical_parent"], how="left")

    industry = cat.groupby("year").agg(
        catalog_n_configurations=("id", "size"),
        catalog_n_models=("baseModel", "nunique"),
        catalog_n_ev_configurations=("fuelType1", lambda s: int((s == "Electricity").sum())),
    ).reset_index()
    industry = industry.merge(
        gas.groupby("year")["comb08"].mean().rename(
            "catalog_mean_label_comb_mpg_gas").reset_index(),
        on="year", how="left")

    allall = (ac["regulatory_class"] == "All") & (ac["vehicle_type"] == "All")
    named = ac[allall & (ac["manufacturer"] != "All")].merge(
        per_parent, left_on=["model_year", "manufacturer"],
        right_on=["year", "canonical_parent"], how="left").drop(
        columns=["year", "canonical_parent"])
    tot = ac[allall & (ac["manufacturer"] == "All")].merge(
        industry, left_on="model_year", right_on="year", how="left").drop(columns=["year"])
    rest = ac[~allall]
    ac = pd.concat([named, tot, rest], ignore_index=True).sort_values(
        ["model_year", "manufacturer", "regulatory_class", "vehicle_type"]
    ).reset_index(drop=True)

    front = ["model_year", "is_preliminary", "manufacturer", "regulatory_class",
             "vehicle_type"]
    ac = ac[front + [c for c in ac.columns if c not in front]]
    ac.to_csv(os.path.join(OUT_DIR, "analysis_clean.csv"), index=False, encoding="utf-8")
    log_stage("output: analysis_clean.csv", len(ac),
              "= input rows of Data by Manufacturer.csv; nothing dropped")

    # ---- full_wide.csv ----------------------------------------------------
    # Aggregate blocks: stacked, never joined to configuration rows.
    a_blk = trends_mfr.add_prefix("src_trends_mfr_")
    a_blk.insert(0, "grain", "aggregate")
    a_blk.insert(1, "source_files", F_MFR)
    a_blk.insert(2, "has_production_volume", True)
    a_blk.insert(3, "canonical_parent",
                 trends_mfr["Manufacturer"].where(trends_mfr["Manufacturer"] != "All"))

    b_blk = trends_vt.add_prefix("src_trends_vtype_")
    b_blk.insert(0, "grain", "aggregate")
    b_blk.insert(1, "source_files", F_VTYPE)
    b_blk.insert(2, "has_production_volume", False)  # share only, no absolute volume
    b_blk.insert(3, "canonical_parent", np.nan)

    # Configuration block: vehicles.csv outer-joined to the my24 carline join
    # on normalized (canonical make, model name). User accepted the 78.5%
    # exact-match rate; my24_matched flags which rows actually linked.
    veh_k = veh.add_prefix("src_fegov_")
    veh_k["canonical_make"] = veh["make"].map(lambda s: make_map.get(s, (s, None))[0])
    veh_k["canonical_parent"] = veh["make"].map(lambda s: make_map.get(s, (s, None))[1])
    veh_k["_k_make"] = veh_k["canonical_make"].map(norm)
    veh_k["_k_model"] = veh["model"].map(norm)
    veh_k["_is2024"] = veh["year"] == 2024

    my24_k = my24.copy()
    my24_k["_k_make"] = my24_k["src_my24fe_MFR_DIVISION_SHORT_NM"].map(
        lambda s: norm(div_map.get(s, (s, None))[0]))
    my24_k["_k_model"] = my24_k["src_my24fe_CARLINE_NAME"].map(norm)

    v24 = veh_k[veh_k["_is2024"]]
    vrest = veh_k[~veh_k["_is2024"]]
    cfg24 = v24.merge(my24_k, on=["_k_make", "_k_model"], how="outer", indicator=True)
    cfg24["my24_matched"] = cfg24["_merge"] == "both"
    n_veh_only = int((cfg24["_merge"] == "left_only").sum())
    n_my24_only = int((cfg24["_merge"] == "right_only").sum())
    log_stage("join: fegov 2024 x my24 carlines on (canonical make, model name)",
              len(cfg24),
              f"outer; {n_veh_only} fegov-2024 rows unmatched, {n_my24_only} my24 "
              "rows unmatched, rest matched (multiplied where many-to-many)")
    cfg24 = cfg24.drop(columns=["_merge"])
    # For my24-only rows the canonical columns come from the my24 side.
    only = cfg24["src_fegov_id"].isna()
    cfg24.loc[only, "canonical_make"] = cfg24.loc[only, "src_my24fe_MFR_DIVISION_SHORT_NM"].map(
        lambda s: div_map.get(s, (str(s), None))[0] if pd.notna(s) else np.nan)
    cfg24.loc[only, "canonical_parent"] = cfg24.loc[only, "src_my24fe_MFR_DIVISION_SHORT_NM"].map(
        lambda s: div_map.get(s, (str(s), None))[1] if pd.notna(s) else np.nan)

    c_blk = pd.concat([cfg24, vrest], ignore_index=True)
    c_blk["grain"] = "configuration"
    has_my24 = c_blk["src_my24fe_MODEL_YEAR"].notna()
    has_veh = c_blk["src_fegov_id"].notna()
    c_blk["my24_matched"] = c_blk["my24_matched"].fillna(False)
    c_blk["has_production_volume"] = has_my24
    c_blk["source_files"] = np.select(
        [has_veh & has_my24, has_veh],
        [f"{F_FEGOV}+{F_MY24FE}+{F_MY24FP}", F_FEGOV],
        default=f"{F_MY24FE}+{F_MY24FP}")
    c_blk = c_blk.drop(columns=["_k_make", "_k_model", "_is2024"])
    c_blk = c_blk.sort_values(
        ["src_fegov_year", "canonical_make", "src_fegov_model", "src_fegov_id"],
        na_position="last").reset_index(drop=True)

    full = pd.concat([a_blk, b_blk, c_blk], ignore_index=True)
    meta = ["grain", "source_files", "has_production_volume", "my24_matched",
            "canonical_make", "canonical_parent", "derived_carline_prod_vol"]
    full = full[[c for c in meta if c in full.columns]
                + [c for c in full.columns if c not in meta]]
    full.to_csv(os.path.join(OUT_DIR, "full_wide.csv"), index=False, encoding="utf-8")
    log_stage("output: full_wide.csv", len(full),
              f"{len(a_blk)} + {len(b_blk)} aggregate rows stacked above "
              f"{len(c_blk)} configuration rows; {full.shape[1]} columns")

    write_report(ac, my24, full, cat, RENAMES, auto_renames)
    for s in STAGES:
        print(s)


# ---------------------------------------------------------------------------
# Phase 4 report
# ---------------------------------------------------------------------------

def write_report(ac, my24, full, cat, renames, auto_renames):
    b = io.StringIO()
    b.write("# Merge Report\n\nGenerated by 03_merge.py.\n\n")

    b.write("## Spine choices\n\n")
    b.write(
        "**analysis_clean.csv** -- spine is `Data by Manufacturer.csv` (the "
        "Trends detailed by-manufacturer export), one row per model year x "
        "manufacturer x regulatory class x vehicle type, all 5,661 rows kept. "
        "It is the only source with production-weighted measures across "
        "1975-2025, which is the half of the offer-vs-buy narrative that "
        "cannot be rebuilt from any other file. The offer side arrives as "
        "derived aggregates (configuration counts, model counts, unweighted "
        "gas-only mean label MPG) computed from vehicles.csv and attached "
        "only to the Regulatory Class='All' x Vehicle Type='All' rows, so a "
        "derived number never sits on a row whose grain it does not match. "
        "Tradeoff accepted: no per-vehicle drilldown here; that lives in "
        "my2024_config.csv and full_wide.csv.\n\n"
        "**full_wide.csv** -- configuration spine (vehicles.csv, all 50,242 "
        "rows) outer-joined to the MY2024 carline join for year-2024 rows; "
        "the two Trends aggregate exports are stacked above it as "
        "`grain='aggregate'` rows, never joined, because a join from a "
        "configuration row to a year x manufacturer aggregate row would "
        "manufacture a relationship the data does not contain.\n\n"
        "**my2024_config.csv** -- files 3 and 4 joined on (carline "
        "manufacturer code, division code, carline code): 100% of carline "
        "tuples on both sides, carline names agree verbatim on every joined "
        "row. Many-to-many by design: model-type rows x footprint-config "
        "rows within each carline, 5,571 rows from 1,978 x 2,085.\n\n"
    )

    b.write("## Prefix map (deviation from the prompt's names)\n\n")
    b.write(
        "The prompt proposed `src_summary_`/`src_detailed_`, but Phase 1 "
        "showed neither export is the Summary table. Prefixes follow what "
        "the files actually are:\n\n"
        "| Prefix | File |\n|---|---|\n"
        "| `src_trends_mfr_` | Data by Manufacturer.csv (Trends detailed viewer) |\n"
        "| `src_trends_vtype_` | Data by Vehicle Type.csv (redundant 'All' slice) |\n"
        "| `src_my24fe_` | model-year-2024-fuel-economy-and-technology-data.csv |\n"
        "| `src_my24fp_` | model-year-2024-footprint-data.csv |\n"
        "| `src_fegov_` | vehicles.csv |\n\n"
    )

    b.write("## Row accounting\n\n| Stage | Rows | Note |\n|---|---|---|\n")
    for stage, rows, note in STAGES:
        b.write(f"| {stage} | {rows:,} | {note} |\n")
    b.write(
        "\nNo source row was dropped anywhere in the pipeline. The only row-"
        "count changes are join multiplications, itemized above.\n\n"
    )

    b.write("## Coercions (nothing silent)\n\n| File | Action | Count |\n|---|---|---|\n")
    for fname, action, count in COERCIONS:
        b.write(f"| {fname} | {action} | {count:,} |\n")
    b.write(
        "\n'-' in the Trends exports means the measure does not apply or the "
        "technology did not exist yet (e.g. GDI share before 2007). It is "
        "stored as null, NOT zero, per the no-imputation rule; treat "
        "pre-introduction nulls as 'no adoption measured' when plotting.\n\n"
    )

    b.write("## Data dictionary: analysis_clean.csv\n\n")
    b.write("| Column | Source | Original name | Units / definition |\n|---|---|---|---|\n")
    dims = [
        ("model_year", "Trends mfr", "Model Year", "integer year; 'Prelim. 2025' -> 2025"),
        ("is_preliminary", "derived", "", "True on Trends 'Prelim. 2025' rows"),
        ("manufacturer", "Trends mfr", "Manufacturer", "Trends parent name (14 + 'All'); already canonical"),
        ("regulatory_class", "Trends mfr", "Regulatory Class", "All / Car / Truck (CAFE regulatory class)"),
        ("vehicle_type", "Trends mfr", "Vehicle Type", "8 Trends body-type buckets"),
    ]
    units = {
        "production_thousands": "units of 1,000 vehicles produced for US sale",
        "production_share": "fraction 0-1 of that year's total production",
        "cafe_2cycle_mpg": "MPG, unadjusted 2-cycle lab test (CAFE-style); NOT comparable to real-world or label MPG",
        "real_world_mpg": "MPG, EPA Trends estimated real-world (adjusted), production-weighted",
        "real_world_mpg_city": "MPG, real-world city",
        "real_world_mpg_hwy": "MPG, real-world highway",
        "weight_lbs": "inertia weight, pounds",
        "footprint_sqft": "square feet; null before MY2008 (not collected)",
        "engine_displacement_cid": "cubic inches (292.7 in 1975 -> 159.8 in 2024)",
        "horsepower_hp": "rated horsepower",
        "accel_0_60_s": "seconds, 0-60 mph, estimated",
        "hp_per_cid": "HP per cubic inch",
        "hp_per_lb": "HP per pound",
        "ton_mpg_real_world": "ton-miles per gallon (weight-normalized efficiency)",
        "avg_gears_gasoline_ice_nonhybrid": "average transmission gear count, gasoline ICE non-hybrids (an average, not a share)",
        "avg_cylinders_gasoline_ice": "average cylinder count, gasoline ICE vehicles (an average, not a share)",
    }
    for col, src, orig, defn in dims:
        b.write(f"| `{col}` | {src} | `{orig}` | {defn} |\n")
    for orig, new in renames.items():
        if new in units:
            b.write(f"| `{new}` | Trends mfr | `{orig}` | {units[new]} |\n")
    b.write(
        f"| `share_*` ({len(auto_renames)} columns) | Trends mfr | see mapping below | fraction 0-1 "
        "of production with that technology/attribute; percent strings divided "
        "by 100; null = not applicable/not yet existing |\n"
        "| `catalog_n_configurations` | derived from vehicles.csv | | count of "
        "fueleconomy.gov configurations offered that year by that manufacturer's "
        "brands; only on regulatory_class='All' & vehicle_type='All' rows; null "
        "before 1984 (no catalog coverage) |\n"
        "| `catalog_n_models` | derived | | distinct `baseModel` count, same scope |\n"
        "| `catalog_n_ev_configurations` | derived | | configurations with "
        "fuelType1='Electricity', same scope |\n"
        "| `catalog_mean_label_comb_mpg_gas` | derived | | UNWEIGHTED mean of "
        "`comb08` window-sticker combined MPG over non-electric configurations; "
        "measures what was offered, not what was bought; do not plot against "
        "real_world_mpg without labeling both definitions |\n\n"
    )
    b.write("`share_*` original-name mapping:\n\n| New | Original |\n|---|---|\n")
    for orig, new in sorted(auto_renames.items(), key=lambda kv: kv[1]):
        b.write(f"| `{new}` | `{orig}` |\n")
    b.write(
        "\nMissingness argument (columns over the 20% rule): every `share_*` "
        "column exceeds 20% null because most technologies did not exist for "
        "most of 1975-2025 (turbo share is null before its first measured "
        "year, BEV share before 2011, etc.). They stay because technology "
        "adoption is a core axis of the narrative and the nulls are "
        "informative (pre-introduction), not data quality failures. The four "
        "`catalog_*` columns are populated only on the All/All grain rows "
        "(13.5% of rows) by design, stated above. `footprint_sqft` is null "
        "before 2008 because EPA did not collect footprint before the "
        "attribute-based standards. `accel_0_60_s` and `production_share` "
        "carry sparse '-' markers in early manufacturer slices.\n\n"
    )

    b.write("## Data dictionary: my2024_config.csv and full_wide.csv\n\n")
    b.write(
        "Both keep every source column under its original name behind a "
        "source prefix (table above); per-column dtypes, null counts, and "
        "definitions are in reports/01_schema_inventory.md. Columns added by "
        "the pipeline:\n\n"
        "| Column | File(s) | Definition |\n|---|---|---|\n"
        "| `derived_carline_prod_vol` | both | carline total production, summed "
        "after deduping to one row per model type (raw `Model_Type_Actual_"
        "Prod_Vol` repeats per configuration row and double-counts if summed "
        "naively) |\n"
        "| `grain` | full_wide | 'aggregate' (Trends rows) or 'configuration' |\n"
        "| `source_files` | full_wide | which source file(s) produced the row |\n"
        "| `has_production_volume` | full_wide | True where a real volume field "
        "exists (Trends mfr rows, my24-joined rows); the vtype block carries "
        "shares only |\n"
        "| `my24_matched` | full_wide | True where a fegov 2024 row linked to a "
        "MY2024 carline by normalized (canonical make, model name); user-"
        "accepted 78.5% exact-match rate, filter on this flag |\n"
        "| `canonical_make` / `canonical_parent` | all | from crosswalk/"
        "manufacturer_crosswalk.csv; raw strings remain in the prefixed "
        "source columns |\n\n"
    )

    b.write("## Three incompatible fuel-economy definitions\n\n")
    b.write(
        "This file set carries three different meanings of 'MPG'. They "
        "differ by 20-30% for the same vehicle and MUST NOT share an axis "
        "without explicit adjustment and labeling.\n\n"
        "1. **EPA Trends estimated real-world** -- `real_world_mpg*` in "
        "analysis_clean, `src_trends_mfr_Real-World MPG*` in full_wide. "
        "Adjusted to reflect actual driving conditions, production-weighted, "
        "methodologically consistent across all 51 years. Lowest of the three.\n"
        "2. **Compliance / CAFE 2-cycle** -- `cafe_2cycle_mpg` in "
        "analysis_clean; in my2024_config: `src_my24fe_UNRD_UNADJ_MT_*`, "
        "`src_my24fe_EPA CAFE MT Calc*`, `src_my24fe_AMFA_*`, "
        "`src_my24fe_BASE_LEVEL_*FE*`. Unadjusted lab values used for "
        "regulatory accounting; roughly 25% higher than real-world. The "
        "footprint file's `MFR_TARGET_FE_VALUE`/`EPA_TARGET_FE_VALUE` are "
        "regulatory TARGETS derived from footprint, not measured economy at "
        "all.\n"
        "3. **fueleconomy.gov window-sticker labels** -- `city08`/`highway08`/"
        "`comb08` (and `catalog_mean_label_comb_mpg_gas` derived from them), "
        "plus `src_my24fe_MFR_*_FE_LABEL` and `src_my24fe_RND_5C_ADJ_MT_*` in "
        "the MY2024 file. Consumer-facing 5-cycle values. For EVs, `comb08` "
        "holds MPGe (a different physical quantity); the derived catalog mean "
        "excludes electric configurations for this reason.\n\n"
    )

    b.write("## The 2008 test-procedure break\n\n")
    b.write(
        "EPA changed label methodology for MY2008 from 2-cycle-derived "
        "values to 5-cycle. fueleconomy.gov retroactively restated older "
        "vehicles' label values with an approximation formula, so `city08/"
        "highway08/comb08` are roughly continuous across 2008 but pre-2008 "
        "values are estimates of what the 5-cycle label would have said. "
        "Trends `real_world_mpg` applies one adjusted methodology across all "
        "years and is the safest series to plot across the break. "
        "`cafe_2cycle_mpg` never changed definition (still the unadjusted "
        "2-cycle test) and also crosses the break cleanly, but measures the "
        "lab test, not reality. Columns that cross 2008: everything in "
        "analysis_clean. Columns that cannot cross it: none here (the MY2024 "
        "files are single-year).\n\n"
    )

    b.write("## Joins decided against, and limitations\n\n")
    b.write(
        "- **No configuration-to-aggregate join.** A vehicles.csv row cannot "
        "be assigned its share of a Trends production aggregate without "
        "inventing weights; the two grains coexist in full_wide, linked only "
        "by `canonical_parent` and year for grouping.\n"
        "- **No production imputation onto vehicles.csv.** Rows lacking "
        "volume keep `has_production_volume=False`.\n"
        "- **Fuzzy name matching declined.** The fegov-2024 x MY2024 attach "
        "uses exact normalized-name equality (78.5% of fegov 2024 rows; "
        "user-accepted). Fuzzy matching was declined: small payoff (one year "
        "of 44), real false-match risk. Unmatched rows are flagged, not "
        "dropped.\n"
        "- **`Data by Vehicle Type.csv` is redundant** (verified strict "
        "subset of the by-manufacturer export's 'All' slice). Kept in "
        "full_wide for provenance; contributes nothing to analysis_clean.\n"
        "- **No Trends Summary export in the file set**, so no CO2 series "
        "anywhere; user confirmed CO2 is out of scope for the narrative.\n"
        "- **Era-dependent manufacturers** (Saab, Jaguar, Land Rover, Volvo, "
        "Maserati, Lotus, Aston Martin, Bugatti Rimac, Daewoo) are not "
        "rolled into parents; see crosswalk/unmatched_manufacturers.csv for "
        "the review list. 44 long-tail coachbuilder/importer strings "
        "(203 vehicles.csv rows of 50,242) remain unmapped with null parent.\n"
        "- **vehicles.csv years 2026-2027** exist in the catalog but have no "
        "Trends counterpart; they appear in full_wide and catalog_fegov with "
        "no aggregate context.\n"
    )

    path = os.path.join(REPORT_DIR, "03_merge_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(b.getvalue())
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
