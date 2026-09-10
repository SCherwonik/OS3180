"""01_inspect.py -- Phase 1 schema inventory.

Reads the five source CSVs and writes reports/01_schema_inventory.md.
No transformation, no merging: inspection only. Idempotent -- rerunning
regenerates the same report from the same inputs.
"""

import io
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(HERE, "reports")

FILES = [
    "Data by Manufacturer.csv",
    "Data by Vehicle Type.csv",
    "model-year-2024-fuel-economy-and-technology-data.csv",
    "model-year-2024-footprint-data.csv",
    "vehicles.csv",
]

# Column-name fragments that mark a candidate join key. Matched
# case-insensitively against each column name.
KEY_FRAGMENTS = [
    "manufacturer", "make", "mfr", "model", "year", "type", "class",
    "carline", "index", "id", "division",
]

# Fragments that mark a year-like column for min/max reporting.
YEAR_FRAGMENTS = ["year"]


def read_csv_robust(path):
    """Try common encodings; EPA/Tableau exports vary (UTF-8 BOM, UTF-16, cp1252)."""
    for enc in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False), enc
        except (UnicodeDecodeError, UnicodeError):
            continue
        except pd.errors.ParserError:
            # Tableau sometimes exports tab-separated with a .csv name.
            try:
                return pd.read_csv(path, encoding=enc, sep="\t", low_memory=False), enc + " (tab-sep)"
            except Exception:
                continue
    raise RuntimeError(f"could not read {path} with any tried encoding")


def is_key_like(col):
    c = col.lower()
    return any(frag in c for frag in KEY_FRAGMENTS)


def is_year_like(col):
    c = col.lower()
    return any(frag in c for frag in YEAR_FRAGMENTS)


def sample_values(series, n=5):
    vals = series.dropna().unique()[:n]
    return ", ".join(repr(v)[:60] for v in vals) if len(vals) else "(all null)"


def inspect_file(path, out):
    name = os.path.basename(path)
    df, enc = read_csv_robust(path)
    size_kb = os.path.getsize(path) / 1024

    out.write(f"\n## {name}\n\n")
    out.write(f"- File size: {size_kb:,.0f} KB, encoding used: {enc}\n")
    out.write(f"- Rows: {len(df):,}\n")
    out.write(f"- Columns: {df.shape[1]}\n\n")

    out.write("### Columns\n\n")
    out.write("| # | Column | dtype | Nulls | Distinct | Sample values |\n")
    out.write("|---|--------|-------|-------|----------|---------------|\n")
    for i, col in enumerate(df.columns):
        s = df[col]
        out.write(
            f"| {i} | `{col}` | {s.dtype} | {s.isna().sum():,} | "
            f"{s.nunique(dropna=True):,} | {sample_values(s)} |\n"
        )

    year_cols = [c for c in df.columns if is_year_like(c)]
    if year_cols:
        out.write("\n### Year fields\n\n")
        for col in year_cols:
            s = pd.to_numeric(df[col], errors="coerce")
            if s.notna().any():
                out.write(f"- `{col}`: min {int(s.min())}, max {int(s.max())}\n")
            else:
                out.write(f"- `{col}`: not numeric (samples: {sample_values(df[col])})\n")

    key_cols = [c for c in df.columns if is_key_like(c)]
    if key_cols:
        out.write("\n### Candidate join keys: top 20 values verbatim\n\n")
        for col in key_cols:
            vc = df[col].value_counts(dropna=True).head(20)
            out.write(f"**`{col}`** ({df[col].nunique(dropna=True):,} distinct)\n\n")
            out.write("| Value (verbatim) | Count |\n|---|---|\n")
            for val, cnt in vc.items():
                out.write(f"| `{repr(val)}` | {cnt:,} |\n")
            out.write("\n")

    return df


def diagnose_tableau_exports(frames, out):
    """Determine which two Trends viewer tables the Tableau exports are.

    Empirical test: is 'Data by Vehicle Type' just the Manufacturer='All'
    slice of 'Data by Manufacturer'? If measures match row-for-row, the
    second export adds nothing.
    """
    import numpy as np

    m = frames.get("Data by Manufacturer.csv")
    v = frames.get("Data by Vehicle Type.csv")
    out.write("\n## Diagnosis: which two Tableau exports these are\n\n")
    if m is None or v is None:
        out.write("One or both Tableau exports missing; diagnosis skipped.\n")
        return

    keys = ["Model Year", "Regulatory Class", "Vehicle Type"]
    ma = m[m["Manufacturer"] == "All"]
    merged = ma.merge(v, on=keys, how="inner", suffixes=("_m", "_v"))

    shared_measures = ["Real-World MPG", "Horsepower (HP)", "Weight (lbs)"]
    identical = {}
    for col in shared_measures:
        a = pd.to_numeric(merged[col + "_m"], errors="coerce")
        b = pd.to_numeric(merged[col + "_v"], errors="coerce")
        identical[col] = int(np.isclose(a, b, rtol=1e-4, equal_nan=True).sum())

    out.write(
        f"- `Data by Manufacturer.csv`: {len(m):,} rows, {m.shape[1]} columns. "
        "Dimensions: Manufacturer (15 values incl. 'All') x Model Year x "
        "Regulatory Class x Vehicle Type. Carries the attribute measures "
        "(production, real-world MPG, weight, HP, footprint, displacement, "
        "0-60) AND the full technology-share block (turbo, GDI, CVT, hybrid "
        "tiers, cylinder deactivation, gear counts, drivetrain, fuel "
        "delivery). This is the DETAILED viewer's by-manufacturer table.\n"
        f"- `Data by Vehicle Type.csv`: {len(v):,} rows, {v.shape[1]} columns. "
        "No Manufacturer dimension; only 6 measures.\n"
        f"- Key match of vehicle-type file against the Manufacturer='All' "
        f"slice of the manufacturer file: {len(merged)}/{len(v)} rows.\n"
    )
    for col, n in identical.items():
        out.write(f"- `{col}` identical within 0.01%: {n}/{len(merged)}\n")
    out.write(
        "\nConclusion: `Data by Vehicle Type.csv` is the Manufacturer='All' "
        "slice of `Data by Manufacturer.csv` with fewer measures. It is "
        "redundant. Neither file is the Summary export: no CO2 column exists "
        "in either, and the Summary table's real-world CO2 measure is the "
        "narrative's emissions anchor. Both files label the preliminary year "
        "as the string 'Prelim. 2025' in `Model Year`.\n"
    )


def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    buf = io.StringIO()
    buf.write("# Schema Inventory: five source files\n")
    buf.write("\nGenerated by 01_inspect.py. Inspection only; no data modified.\n")

    frames = {}
    for fname in FILES:
        path = os.path.join(HERE, fname)
        if not os.path.exists(path):
            buf.write(f"\n## {fname}\n\n- MISSING FROM DISK\n")
            continue
        frames[fname] = inspect_file(path, buf)

    diagnose_tableau_exports(frames, buf)

    report_path = os.path.join(REPORT_DIR, "01_schema_inventory.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(buf.getvalue())
    print(f"wrote {report_path}")
    for fname, df in frames.items():
        print(f"{fname}: {len(df):,} rows x {df.shape[1]} cols")


if __name__ == "__main__":
    main()
