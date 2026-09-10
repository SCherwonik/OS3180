# Claude Code Prompt: Merge EPA + fueleconomy.gov Vehicle Datasets

Paste everything below the line into Claude Code, with the five CSVs in the working directory.

---

## Context

I am building a data-storytelling project about US light-duty vehicles from 1975 to present. The narrative is about the gap between what automakers **offer** (the catalog of configurations) and what Americans actually **buy** (production-weighted reality), and how fuel economy, vehicle size, power, and technology have changed across five decades.

I have five source files. They come from three different EPA/DOE systems and they are at **different grains**, which is the central problem you need to solve carefully rather than paper over.

### The five files

1. **EPA Automotive Trends: Summary export** (Tableau export, model years 1975 to 2025)
   Aggregated. Dimensions are roughly model year, regulatory class, vehicle type, manufacturer. Measures are production-weighted real-world fuel economy, CO2, weight, horsepower, footprint, and similar attributes. Model year 2025 values are preliminary.

2. **EPA Automotive Trends: Detailed export** (Tableau export, model years 1975 to 2025)
   Aggregated. Organized around technology adoption shares (turbo, GDI, CVT, hybrid, cylinder deactivation, etc.) and/or GHG compliance categories. Also production-weighted.

3. **Model Year 2024 Fuel Economy and Technology Data** (`model-year-2024-fuel-economy-and-technology-data.csv`, ~443 KB)
   Vehicle-configuration level, 2024 only. Includes production volume per record.

4. **Model Year 2024 Footprint Data** (`model-year-2024-footprint-data.csv`, ~1.78 MB)
   Vehicle-configuration level, 2024 only. Wheelbase, track width, footprint. Includes production volume per record.

5. **fueleconomy.gov vehicles.csv** (the `vehicles.csv` bulk export, model years 1984 to 2026, ~48,000 rows)
   Vehicle-configuration level across four decades. **Has no production volume field.** Every row is one trim/engine/transmission combination regardless of whether it sold 400,000 units or 300.

### The structural constraint (read this before designing anything)

There is no public file that has vehicle-level records *with* production volumes *across all years*. You can have:

- production-weighted aggregates for 50 years (files 1 and 2), or
- production-weighted vehicle detail for one year (files 3 and 4), or
- vehicle detail without volumes for 40 years (file 5)

Do not fabricate a bridge between these. Do not impute production volumes onto file 5. If a join is not legitimate, say so in your report rather than forcing it.

## What I want you to do

### Phase 1: Inspect before you write any merge code

Do not guess at schemas. For each of the five files, print:

- exact filename, row count, column count
- full column list with inferred dtype
- for each column: null count, distinct count, and 5 sample values
- min/max of any year field
- for any column that looks like a join key (manufacturer, make, model, model year, vehicle type, class, carline, index/ID): the top 20 most frequent values verbatim, so I can see the exact casing and formatting

Then **tell me which two Tableau exports I actually have.** I may have accidentally exported two tables from the Detailed viewer instead of one Summary and one Detailed. Diagnose this from the columns and say so plainly if that is what happened.

Write this inspection to `reports/01_schema_inventory.md`.

### Phase 2: Assess joinability

For each candidate pair of files, report:

- the proposed join keys
- exact-match rate on those keys, as a percentage
- what breaks the match (casing, punctuation, "Chevrolet" vs "CHEVROLET" vs "Chevy", "Mercedes-Benz" vs "Mercedes Benz", division vs parent manufacturer, model year as string vs int)
- whether the join is one-to-one, one-to-many, or many-to-many, and the resulting row multiplication if applicable

Specifically test whether **files 3 and 4 (the two MY2024 files) join cleanly** on a shared vehicle identifier. This is the highest-value join in the set. Report the match rate and the identifier you used.

Build a **manufacturer crosswalk** as a standalone CSV (`crosswalk/manufacturer_crosswalk.csv`) mapping every raw manufacturer/make string found in any file to a single canonical name. Handle at minimum: case normalization, punctuation, division-to-parent rollup (e.g. Chevrolet/GMC/Buick/Cadillac under General Motors where the EPA files roll up that way, but keep the raw value in a separate column so nothing is lost). Do not silently drop unmatched values. Emit an `unmatched_manufacturers.csv` listing anything you could not confidently map, and leave it to me to review.

Write this to `reports/02_joinability.md`.

### Phase 3: Produce two outputs

**Output A: `outputs/full_wide.csv` (maximally complete)**

Keep as much as possible. Use outer joins throughout. Every source row should be represented even when its counterpart is missing. Requirements:

- Prefix or suffix every column with its source (`src_summary_`, `src_detailed_`, `src_my24fe_`, `src_my24fp_`, `src_fegov_`) so provenance is never ambiguous
- Add a `source_files` column listing which sources contributed to each row
- Add a `grain` column labeling each row as `aggregate` or `configuration`
- Add a `has_production_volume` boolean
- Preserve raw manufacturer/make strings alongside canonical ones
- Do not drop columns for being sparse. Sparse is fine here; that is the point of this output.

**Output B: `outputs/analysis_clean.csv` (trimmed and reliable)**

Only columns that are populated and comparable across the sources they claim to span. Drop anything that cannot be merged completely or that has ambiguous provenance. Requirements:

- One row per analysis unit at a grain you choose and justify
- No column with more than 20% missingness unless you explicitly argue for keeping it in the report
- Consistent units, documented
- Consistent canonical manufacturer names
- Model year as integer
- Flag preliminary data (model year 2025 from the Trends exports) with a `is_preliminary` boolean rather than dropping it

**You decide which file is the spine for each output, and justify the choice in writing.** Consider that the widest year coverage sits in file 5, the production weighting sits in files 1 through 4, and the deepest per-vehicle detail for a single year sits in files 3 and 4. There is no obviously correct answer; make a defensible call and explain the tradeoff.

### Phase 4: Documentation

Produce `reports/03_merge_report.md` containing:

- which file you chose as the spine for each output and why
- a data dictionary for both outputs: every column, its source file, its original name, units, and definition
- row counts at every stage of the pipeline (input, after each join, output) so shrinkage is traceable
- every record dropped and why, with counts
- **a dedicated section on the three incompatible fuel economy definitions in play**: EPA Trends "estimated real-world" values, EPA compliance/CAFE values, and fueleconomy.gov window-sticker values. State clearly which columns are which and warn that they must not be compared directly or plotted on a shared axis without adjustment.
- a note on the 2008 EPA test-procedure change and which columns cross that break
- known limitations and any join you decided against, with the reason

## Constraints and standards

- Python with pandas. Write a numbered, runnable pipeline (`01_inspect.py`, `02_crosswalk.py`, `03_merge.py`) rather than one monolithic script, so I can rerun stages independently.
- Every step idempotent. Re-running from scratch must reproduce identical outputs.
- Never silently coerce or drop. Every drop gets logged with a count and a reason.
- Do not fill missing values with zeros. Leave nulls as nulls.
- Do not rename columns without recording the mapping in the data dictionary.
- No imputation, no interpolation, no synthetic rows. If something is unknown, it stays unknown.
- If a merge you attempt produces a match rate below 80%, stop and report it to me instead of proceeding.
- Add brief inline comments explaining any non-obvious transformation, since this pipeline becomes a methods slide in a presentation.

## First response

Do not write the merge yet. Start with Phase 1 only, show me the schema inventory, tell me which two Tableau exports I have, and propose your spine choice with reasoning. I will confirm before you build anything.
