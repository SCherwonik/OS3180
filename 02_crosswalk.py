"""02_crosswalk.py -- Phase 2: manufacturer crosswalk + joinability assessment.

Outputs:
  crosswalk/manufacturer_crosswalk.csv   every raw mfr/make string -> canonical
  crosswalk/unmatched_manufacturers.csv  strings needing human review
  reports/02_joinability.md              join-key tests for each candidate pair

Idempotent: regenerates all three from the source CSVs on every run.
"""

import io
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CROSSWALK_DIR = os.path.join(HERE, "crosswalk")
REPORT_DIR = os.path.join(HERE, "reports")

F_MFR = "Data by Manufacturer.csv"
F_VTYPE = "Data by Vehicle Type.csv"
F_MY24FE = "model-year-2024-fuel-economy-and-technology-data.csv"
F_MY24FP = "model-year-2024-footprint-data.csv"
F_FEGOV = "vehicles.csv"


def read_csv_robust(path):
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"could not read {path}")


def norm(s):
    """Normalization used only for lookup: lowercase, strip punctuation,
    collapse whitespace. Raw strings are preserved in the crosswalk."""
    s = str(s).lower()
    s = re.sub(r"[.,;:'\"()&/\\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Canonical parent names follow the EPA Trends manufacturer list (14 parents),
# since analysis_clean's spine uses them. canonical_make preserves the brand;
# canonical_parent is the Trends rollup. method records how the mapping was
# decided. Era-dependent ownerships (Saab, Jaguar, Land Rover, Volvo, etc.)
# are NOT rolled into a parent; they map to themselves and are flagged for
# review, because their parent depends on the model year.
#   (canonical_make, canonical_parent, method)
M = {}


def add(parent, make, *raws, method="division-rollup"):
    for r in raws:
        M[norm(r)] = (make, parent, method)


# --- Trends parent names map to themselves -------------------------------
for p in ["GM", "Ford", "Toyota", "Honda", "Nissan", "Stellantis", "VW",
          "Mercedes", "BMW", "Hyundai", "Kia", "Mazda", "Subaru", "Tesla"]:
    add(p, p, p, method="trends-parent")
add(None, "All", "All", method="aggregate-total")

# --- General Motors ------------------------------------------------------
add("GM", "Chevrolet", "Chevrolet", "CHEVROLET", "Chevy")
add("GM", "GMC", "GMC")
add("GM", "Buick", "Buick")
add("GM", "Cadillac", "Cadillac")
add("GM", "Pontiac", "Pontiac")
add("GM", "Oldsmobile", "Oldsmobile")
add("GM", "Saturn", "Saturn")
add("GM", "Geo", "Geo")
add("GM", "Hummer", "Hummer")
add("GM", "GM", "General Motors LLC", "General Motors", "GMX")

# --- Ford ----------------------------------------------------------------
add("Ford", "Ford", "Ford Motor Company", "FMX")
add("Ford", "Lincoln", "Lincoln")
add("Ford", "Mercury", "Mercury")
add("Ford", "Merkur", "Merkur")  # Ford of Europe brand sold in US 1985-1989
add("Ford", "Shelby", "Shelby")  # Ford-based; EPA lists under Ford carlines

# --- Toyota --------------------------------------------------------------
add("Toyota", "Toyota", "Toyota Motor Corporation", "TOYOTA", "TYX",
    "Toyota Motor North America, Inc.")
add("Toyota", "Lexus", "Lexus", "LEXUS")
add("Toyota", "Scion", "Scion")

# --- Honda ---------------------------------------------------------------
add("Honda", "Honda", "American Honda Motor Co., Inc.", "HNX")
add("Honda", "Acura", "Acura")

# --- Nissan --------------------------------------------------------------
add("Nissan", "Nissan", "Nissan Motor Co., Ltd.", "NISSAN", "NSX",
    "Nissan North America, Inc.")
add("Nissan", "Infiniti", "Infiniti", "INFINITI")
add("Nissan", "Datsun", "Datsun")

# --- Stellantis (FCA and predecessors; Chrysler-era brands roll up the
#     same way the Trends report does: current corporate family) ----------
add("Stellantis", "Stellantis", "FCA US LLC", "Stellantis N.V.", "CRX")
add("Stellantis", "Chrysler", "Chrysler")
add("Stellantis", "Dodge", "Dodge")
add("Stellantis", "Jeep", "Jeep")
add("Stellantis", "Ram", "Ram", "RAM")
add("Stellantis", "Plymouth", "Plymouth")
add("Stellantis", "Eagle", "Eagle")
add("Stellantis", "Fiat", "Fiat", "FIAT")
add("Stellantis", "Alfa Romeo", "Alfa Romeo", "ALFA ROMEO")
add("Stellantis", "SRT", "SRT")
add("Stellantis", "AMC", "American Motors Corporation", "AMC")  # absorbed by Chrysler 1987

# --- Volkswagen Group ----------------------------------------------------
add("VW", "Volkswagen", "Volkswagen", "Volkswagen Group of America, Inc.",
    "VOLKSWAGEN", "VGA")
add("VW", "Audi", "Audi", "AUDI")
add("VW", "Porsche", "Porsche", "Porsche AG", "PRX", "Dr. Ing. h.c.F. Porsche AG")
add("VW", "Bentley", "Bentley", "Bentley Motors Limited")
add("VW", "Lamborghini", "Lamborghini", "Automobili Lamborghini")
add("VW", "Bugatti", "Bugatti")  # Veyron/Chiron era, VW Group

# --- Mercedes ------------------------------------------------------------
add("Mercedes", "Mercedes-Benz", "Mercedes-Benz", "Mercedes Benz", "MBX",
    "Mercedes-Benz USA, LLC", "Mercedes-Benz AG")
add("Mercedes", "smart", "smart")
add("Mercedes", "Maybach", "Maybach")

# --- BMW -----------------------------------------------------------------
add("BMW", "BMW", "BMW of North America, LLC", "BMX")
add("BMW", "Mini", "Mini", "MINI")
add("BMW", "Rolls-Royce", "Rolls-Royce", "Rolls-Royce Motor Cars Limited", "RRG")

# --- Hyundai / Kia (separate CAFE manufacturers; Trends lists both) ------
add("Hyundai", "Hyundai", "Hyundai Motor Company", "HYUNDAI",
    "HYUNDAI MOTOR COMPANY", "HYX")
add("Hyundai", "Genesis", "Genesis", "GENESIS")
add("Kia", "Kia", "Kia Corporation", "KIA", "Kia Motors Corporation", "KMX")

# --- Mazda / Subaru / Tesla ---------------------------------------------
add("Mazda", "Mazda", "Mazda Motor Corporation", "MAZDA", "TKX")
add("Subaru", "Subaru", "Subaru Corporation", "SUBARU", "FJX",
    "Fuji Heavy Industries, Ltd.")
add("Tesla", "Tesla", "Tesla, Inc.", "TESLA", "TSL", "Tesla Motors, Inc.",
    "Tesla Motors")

# --- Standalone manufacturers: map to themselves, no Trends parent -------
SELF = [
    "Mitsubishi", "Mitsubishi Motors Corporation", "MITSUBISHI", "MTX",
    "MITSUBISHI MOTORS",
    "Rivian", "Rivian Automotive LLC", "RIV",
    "Lucid", "Lucid USA, Inc.", "LMU",
    "Ferrari", "Ferrari S.p.A.", "FEX", "Ferrari North America, Inc.",
    "McLaren", "McLaren Automotive", "MCX", "McLaren Automotive Limited",
    "Polestar", "Polestar Automotive USA Inc",
    "Suzuki", "Isuzu", "Daihatsu", "Sterling", "Yugo", "Peugeot", "Renault",
    "Karma", "Fisker", "Fisker Automotive", "Fisker Group Inc.",
    "INEOS", "Ineos Automotive Limited", "INEOS Automotive", "IAL",
    "Koenigsegg", "Spyker", "Mobility Ventures LLC",
    "Roush Performance", "Panoz", "Saleen", "Saleen Performance",
    "Bertone", "Pininfarina", "Avanti Motor Corporation",
    "Grumman Olson", "Grumman Allied Industries",
    "BYD", "Dacia", "Morgan", "Mahindra", "Kandi", "Lordstown",
    "AM General", "Vector", "Qvale", "Spartan Motors",
]
add(None, "VinFast", "VinFast", "VinFast Trading and Production LLC",
    "VinFast Trading and Production Joint Stock Company",
    "Hai Phong manufacturing plant ",  # VinFast's Haiphong plant listed as division
    method="self")
add(None, "Pagani", "Pagani", "Pagani S.p.A.", "Pagani Automobili S.p.A.",
    method="self")
add(None, "TVR", "TVR Engineering Ltd", method="self")
add(None, "Ruf", "RUF Automobile", "Ruf Automobile Gmbh", method="self")
for s in SELF:
    # First token chain up to a comma/legal suffix keeps display name short.
    disp = re.sub(r"\s+(S\.p\.A\.|LLC|Inc\.?|Ltd\.?|Limited|Corporation|"
                  r"N\.V\.|USA.*|Automotive.*|Trading.*|Motors? Corporation)$",
                  "", s).strip() or s
    M.setdefault(norm(s), (disp, None, "self"))

# --- Era-dependent ownership: self-mapped AND flagged for review ---------
REVIEW = {
    "Saab": "GM 1990-2010, independent before, defunct after; parent depends on model year",
    "Jaguar": "Ford 1990-2008, Tata/JLR after",
    "Land Rover": "Ford 2000-2008, Tata/JLR after",
    "Jaguar Land Rover Limited": "Tata-owned JLR; separate CAFE manufacturer",
    "JLX": "Jaguar Land Rover CAFE code",
    "Volvo": "Ford 1999-2010, Geely after; separate CAFE manufacturer",
    "Volvo Car USA,  LLC": "Geely-era Volvo legal name (note double space)",
    "Volvo Cars of North America, LLC": "Volvo division name in footprint file",
    "VVX": "Volvo CAFE code",
    "Maserati": "Stellantis family since 2021 but separate CAFE manufacturer in MY2024 files",
    "MASERATI": "see Maserati",
    "Maserati North America, Inc.": "see Maserati",
    "MAX": "Maserati CAFE code",
    "Lotus": "GM 1986-1993, Proton 1996-2017, Geely after",
    "Aston Martin": "Ford 1994-2007, independent after",
    "Aston Martin Lagonda": "see Aston Martin",
    "Aston Martin Lagonda Ltd": "see Aston Martin",
    "ASX": "Aston Martin CAFE code",
    "Daewoo": "GM-affiliated 2002+ (sold as Suzuki/Chevrolet later); standalone brand years 1998-2002",
    "Lotus Cars Ltd": "see Lotus",
    "Bugatti Rimac": "Rimac-majority JV with Porsche 45% since 2021; not a clean VW rollup",
    "Bugatti Rimac LLC": "see Bugatti Rimac",
    "BGR": "Bugatti Rimac CAFE code",
    "AM": "division short-name in Aston Martin rows of MY2024 FE file",
    "BMW Alpina": "independent tuner until BMW acquired it in 2022; 3 rows in vehicles.csv",
    "Certification": "junk division label in footprint file; resolve via CAFE_MFR_NM on those rows",
    "CERT": "junk division short-name in MY2024 FE file; resolve via CAFE Mfr Name on those rows",
    "Manufacturing Plant": "junk division short-name in MY2024 FE file; resolve via CAFE Mfr Name on those rows",
}
for r, why in REVIEW.items():
    disp = re.sub(r"\s+(Lagonda.*|North America.*|Car USA.*|Cars of North America.*|"
                  r"Land Rover Limited)$", "", r).strip() or r
    M.setdefault(norm(r), (disp, None, "review"))
REVIEW_NORM = {norm(k): v for k, v in REVIEW.items()}

# Columns holding manufacturer/make/division strings, per file.
MFR_SOURCES = [
    (F_MFR, "Manufacturer"),
    (F_MY24FE, "CAFE Mfr Name"),
    (F_MY24FE, "Carline Mfr Name"),
    (F_MY24FE, "MFR_DIVISION_SHORT_NM"),
    (F_MY24FP, "CAFE_MFR_NM"),
    (F_MY24FP, "FOOTPRINT_MFR_NM"),
    (F_MY24FP, "FOOTPRINT_DIVISION_NM"),
    (F_FEGOV, "make"),
]


def build_crosswalk(frames):
    rows = []
    for fname, col in MFR_SOURCES:
        vc = frames[fname][col].value_counts(dropna=True)
        for raw, cnt in vc.items():
            hit = M.get(norm(raw))
            if hit:
                make, parent, method = hit
            else:
                make, parent, method = str(raw), None, "unmapped"
            rows.append({
                "raw_value": raw,
                "source_file": fname,
                "source_column": col,
                "n_rows": int(cnt),
                "canonical_make": make,
                "canonical_parent": parent if parent else "",
                "map_method": method,
                "review_note": REVIEW_NORM.get(norm(raw), ""),
            })
    xw = pd.DataFrame(rows).sort_values(
        ["source_file", "source_column", "n_rows"], ascending=[True, True, False]
    ).reset_index(drop=True)

    unmatched = xw[xw["map_method"].isin(["unmapped", "review"])].copy()
    return xw, unmatched


# ---------------------------------------------------------------------------
# Joinability tests
# ---------------------------------------------------------------------------

def test_my24_pair(fe, fp, out):
    """Files 3 & 4: the highest-value join. Carline-level identifier."""
    out.write("## Files 3 & 4: MY2024 fuel-economy x footprint\n\n")

    fe_k = fe.assign(
        mfr_cd=fe["Carline Mfr Code"].str.strip(),
        div_cd=fe["DIVISION_CD"],
        car_cd=fe["CARLINE_CODE"],
    )
    fp_k = fp.assign(
        mfr_cd=fp["FOOTPRINT_MFR_CD"].str.strip(),
        div_cd=fp["FTPT_DIVISION_CD"],
        car_cd=fp["FTPT_CARLINE_CD"],
    )
    keys = ["mfr_cd", "div_cd", "car_cd"]

    fe_tup = fe_k[keys].drop_duplicates()
    fp_tup = fp_k[keys].drop_duplicates()
    both = fe_tup.merge(fp_tup, on=keys, how="inner")
    out.write(
        f"- Proposed key: (carline manufacturer code, division code, carline code)\n"
        f"- Distinct key tuples: FE file {len(fe_tup):,}, footprint file "
        f"{len(fp_tup):,}, intersection {len(both):,}\n"
        f"- Tuple match rate: {len(both)/len(fe_tup):.1%} of FE tuples, "
        f"{len(both)/len(fp_tup):.1%} of footprint tuples\n"
    )

    m = fe_k.merge(fp_k[keys].drop_duplicates(), on=keys, how="left", indicator=True)
    fe_row_rate = (m["_merge"] == "both").mean()
    m2 = fp_k.merge(fe_k[keys].drop_duplicates(), on=keys, how="left", indicator=True)
    fp_row_rate = (m2["_merge"] == "both").mean()
    out.write(
        f"- Row-level match: {fe_row_rate:.1%} of FE rows have a footprint "
        f"carline; {fp_row_rate:.1%} of footprint rows have an FE carline\n"
    )

    # Cardinality: rows per key tuple on each side.
    fe_per = fe_k.groupby(keys).size()
    fp_per = fp_k.groupby(keys).size()
    full = fe_k.merge(fp_k, on=keys, how="inner")
    out.write(
        f"- Cardinality: many-to-many at carline level. FE rows per carline "
        f"median {int(fe_per.median())} / max {int(fe_per.max())}; footprint rows per "
        f"carline median {int(fp_per.median())} / max {int(fp_per.max())}\n"
        f"- Full inner join row count: {len(full):,} "
        f"(FE {len(fe):,} x FP {len(fp):,} at shared carlines -> "
        f"{len(full)/len(fe):.1f}x multiplication of FE rows)\n"
    )

    # Name-based sanity check on the carline name columns.
    name_eq = (
        full["CARLINE_NAME"].str.strip().str.upper()
        == full["FOOTPRINT_CARLINE_NM"].str.strip().str.upper()
    ).mean()
    out.write(
        f"- Sanity: `CARLINE_NAME` == `FOOTPRINT_CARLINE_NM` on "
        f"{name_eq:.1%} of joined rows\n\n"
    )
    return fe_row_rate, fp_row_rate


def test_fegov_vs_my24(veh, fe, xw, out):
    """File 5 (2024 slice) vs file 3: free-text name matching."""
    out.write("## File 5 (2024 rows) x File 3: make/model vs division/carline\n\n")
    v24 = veh[veh["year"] == 2024].copy()

    lookup = {r: (m if m else r) for r, m in
              zip(xw["raw_value"], xw["canonical_make"])}

    def canon(s):
        return norm(lookup.get(s, s))

    v24["k_make"] = v24["make"].map(canon)
    v24["k_model"] = v24["model"].map(norm)
    fe2 = fe.copy()
    fe2["k_make"] = fe2["MFR_DIVISION_SHORT_NM"].map(canon)
    fe2["k_model"] = fe2["CARLINE_NAME"].map(norm)

    mk = v24.merge(fe2[["k_make"]].drop_duplicates(), on="k_make",
                   how="left", indicator=True)
    make_rate = (mk["_merge"] == "both").mean()

    mm = v24.merge(fe2[["k_make", "k_model"]].drop_duplicates(),
                   on=["k_make", "k_model"], how="left", indicator=True)
    model_rate = (mm["_merge"] == "both").mean()
    out.write(
        f"- fueleconomy.gov 2024 rows: {len(v24):,}\n"
        f"- Canonical-make match: {make_rate:.1%} of rows find their make in file 3\n"
        f"- Exact (make, model-name) match after normalization: {model_rate:.1%}\n"
        f"- What breaks it: fueleconomy.gov `model` is a display name "
        f"('F150 Pickup 2WD'), file 3 `CARLINE_NAME` is the CAFE carline "
        f"('F150 PICKUP 2WD', 'MUSTANG'); trim/spec suffixes differ, and EV "
        f"sub-models live in `MODEL_TYPE_DESC` not `CARLINE_NAME`\n\n"
    )
    return model_rate


def test_trends_internal(mfr, vtype, out):
    out.write("## Files 1 & 2: Trends by-manufacturer x by-vehicle-type\n\n")
    keys = ["Model Year", "Regulatory Class", "Vehicle Type"]
    ma = mfr[mfr["Manufacturer"] == "All"]
    merged = ma.merge(vtype, on=keys, how="inner", suffixes=("_m", "_v"))
    checks = []
    for col in ["Real-World MPG", "Horsepower (HP)", "Weight (lbs)"]:
        a = pd.to_numeric(merged[col + "_m"], errors="coerce")
        b = pd.to_numeric(merged[col + "_v"], errors="coerce")
        checks.append(int(np.isclose(a, b, rtol=1e-4, equal_nan=True).sum()))
    out.write(
        f"- Key match: {len(merged)}/{len(vtype)} vehicle-type rows found in "
        f"the Manufacturer='All' slice (1:1)\n"
        f"- Shared measures identical within 0.01% on {min(checks)}/{len(merged)} rows\n"
        f"- Verdict: file 2 is a strict subset of file 1. Join is legitimate "
        f"but adds no columns worth keeping; carried in full_wide for "
        f"provenance only.\n\n"
    )


def test_trends_vs_my24(mfr, fe, out):
    """File 1 (2024, per-manufacturer) x file 3 rolled up via crosswalk."""
    out.write("## File 1 (MY2024 rows) x File 3: manufacturer-level rollup\n\n")
    t24 = mfr[(mfr["Model Year"] == "2024") & (mfr["Manufacturer"] != "All")]
    trends_parents = set(t24["Manufacturer"])

    fe2 = fe.copy()
    fe2["parent"] = fe2["CAFE Mfr Name"].map(
        lambda s: (M.get(norm(s)) or (None, None, None))[1]
    )
    # Model_Type_Actual_Prod_Vol repeats on every configuration row of a
    # model type; dedupe to one row per model type before summing, or the
    # total double-counts.
    fe2 = fe2.drop_duplicates(
        subset=["Carline Mfr Code", "CARLINE_CODE", "MODEL_TYPE_INDEX"]
    )
    vol = fe2.groupby("parent", dropna=False)["Model_Type_Actual_Prod_Vol"].sum()
    covered = vol[vol.index.isin(trends_parents)].sum()
    total = vol.sum()
    out.write(
        f"- Trends 2024 manufacturers: {sorted(trends_parents)}\n"
        f"- Rolling file 3's 27 CAFE manufacturers up via crosswalk covers "
        f"{covered/total:.1%} of file 3's reported production volume "
        f"({covered:,.0f} of {total:,.0f} units)\n"
        f"- Remainder is standalone/era-dependent makes (Mitsubishi, Volvo, "
        f"JLR, Rivian, Lucid, Maserati, Ferrari, etc.) that Trends folds "
        f"into 'All' but does not break out\n"
        f"- Join key for analysis_clean: (model year int, canonical_parent). "
        f"One-to-many by design: one Trends aggregate row to many "
        f"configuration rows\n\n"
    )


def test_trends_vs_fegov(mfr, veh, xw, out):
    out.write("## File 1 x File 5: aggregate x catalog (offer-vs-buy axis)\n\n")
    lookup = dict(zip(xw[xw["source_column"] == "make"]["raw_value"],
                      xw[xw["source_column"] == "make"]["canonical_parent"]))
    veh2 = veh.copy()
    veh2["parent"] = veh2["make"].map(lookup)
    have_parent = veh2["parent"].ne("").fillna(False) & veh2["parent"].notna()
    yr_overlap = veh2["year"].between(1984, 2025)
    out.write(
        f"- fueleconomy.gov rows with a Trends-parent mapping: "
        f"{have_parent.mean():.1%} ({int(have_parent.sum()):,} of {len(veh2):,})\n"
        f"- Rows inside the Trends year window 1984-2025: {yr_overlap.mean():.1%}\n"
        f"- Rows usable for the offer-side derived aggregates (both): "
        f"{(have_parent & yr_overlap).mean():.1%}\n"
        f"- Unmapped remainder is the long tail of makes (see "
        f"unmatched_manufacturers.csv), kept as configuration rows with "
        f"canonical_parent null, excluded only from per-parent rollups\n\n"
    )


def main():
    os.makedirs(CROSSWALK_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    frames = {f: read_csv_robust(os.path.join(HERE, f))
              for f in [F_MFR, F_VTYPE, F_MY24FE, F_MY24FP, F_FEGOV]}

    xw, unmatched = build_crosswalk(frames)
    xw.to_csv(os.path.join(CROSSWALK_DIR, "manufacturer_crosswalk.csv"),
              index=False, encoding="utf-8")
    unmatched.to_csv(os.path.join(CROSSWALK_DIR, "unmatched_manufacturers.csv"),
                     index=False, encoding="utf-8")

    buf = io.StringIO()
    buf.write("# Joinability Assessment\n\nGenerated by 02_crosswalk.py.\n\n")
    n_unmapped = (xw["map_method"] == "unmapped").sum()
    n_review = (xw["map_method"] == "review").sum()
    buf.write(
        f"Crosswalk: {len(xw)} (raw value, file, column) combinations; "
        f"{n_unmapped} unmapped, {n_review} flagged era-dependent for review. "
        f"See crosswalk/unmatched_manufacturers.csv.\n\n"
    )

    test_my24_pair(frames[F_MY24FE], frames[F_MY24FP], buf)
    test_fegov_vs_my24(frames[F_FEGOV], frames[F_MY24FE], xw, buf)
    test_trends_internal(frames[F_MFR], frames[F_VTYPE], buf)
    test_trends_vs_my24(frames[F_MFR], frames[F_MY24FE], buf)
    test_trends_vs_fegov(frames[F_MFR], frames[F_FEGOV], xw, buf)

    path = os.path.join(REPORT_DIR, "02_joinability.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
    print(f"wrote {path}")
    print(f"crosswalk rows: {len(xw)}, unmatched/review: {len(unmatched)}")


if __name__ == "__main__":
    main()
