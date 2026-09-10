# Data Source Manifest

Every raw input to this project, with origin, retrieval method, and checksum.
Regenerate checksums with `python -c` md5 over the files listed; if a hash
differs, the file changed and downstream outputs are not comparable.

## User-provided source files (in project root)

These five files were downloaded manually before the project started and are
the inputs to `01_inspect.py` / `02_crosswalk.py` / `03_merge.py`.

| File | Origin | Coverage / grain | MD5 |
|---|---|---|---|
| `Data by Manufacturer.csv` | EPA Automotive Trends Report, "Explore the Data" Tableau export (detailed by-manufacturer table): https://www.epa.gov/automotive-trends/explore-automotive-trends-data | MY1975–"Prelim. 2025", aggregate: manufacturer x year x reg class x vehicle type | `8be1c2823eee5a7c054b0d7ff771fe80` |
| `Data by Vehicle Type.csv` | Same EPA Trends viewer (by-vehicle-type table; verified strict subset of the file above) | MY1975–"Prelim. 2025", aggregate | `f46fc4fee60626b38a927ae47fc16e0c` |
| `model-year-2024-fuel-economy-and-technology-data.csv` | EPA Automotive Trends data downloads (MY2024 fuel economy and technology data): https://www.epa.gov/automotive-trends | MY2024 only, vehicle-configuration grain, includes production volumes | `ca6558bf81f79f271276b589ecde45d9` |
| `model-year-2024-footprint-data.csv` | EPA Automotive Trends data downloads (MY2024 footprint data), same page | MY2024 only, footprint-configuration grain, includes production volumes | `36a00a64b59cfd78882952eda6d356e5` |
| `vehicles.csv` | fueleconomy.gov bulk download: https://www.fueleconomy.gov/feg/download.shtml | MY1984–2027, configuration grain, NO production volumes | `7babf9548dfaad26e9253b67bb20f223` |

The two Tableau exports were diagnosed in `reports/01_schema_inventory.md`:
neither is the Summary table (no CO2 columns), and the by-vehicle-type file is
the Manufacturer='All' slice of the by-manufacturer file. Exact export dates
unknown (user download); contents pin the vintage: Trends data through
preliminary MY2025, vehicles.csv through MY2027.

## External series (in external/, fetched 2026-08-13 by 06 stage)

Downloaded via `curl` from FRED's CSV endpoint
(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>`), monthly
frequency, annualized by `06_external.py`. FRED re-publishes revisions;
re-downloading later can change recent values, which is why the hashes below
pin the vintage used.

| File | FRED series | Underlying source | Series page | MD5 |
|---|---|---|---|---|
| `external/fred_gas_price.csv` | `APU000074714` | BLS average price, unleaded regular gasoline, $/gal, 1976+ | https://fred.stlouisfed.org/series/APU000074714 | `6c7d5edbd5cf2602cf73b55c0bc4f30f` |
| `external/fred_cpi_all.csv` | `CPIAUCSL` | BLS CPI-U all items, 1947+ | https://fred.stlouisfed.org/series/CPIAUCSL | `f312f433824ad8556645ae22337c871f` |
| `external/fred_cpi_newveh.csv` | `CUUR0000SETA01` | BLS CPI new vehicles (hedonic quality-adjusted), 1947+ | https://fred.stlouisfed.org/series/CUUR0000SETA01 | `93add16404ef86232f3f08cf3e96e02a` |
| `external/fred_vmt.csv` | `TRFVOLUSM227NFWA` | FHWA vehicle miles traveled, millions, monthly, 1970+ | https://fred.stlouisfed.org/series/TRFVOLUSM227NFWA | `ab36e06d25b7ffd3f966001d53159f00` |

## Safety, sales, and events additions (2026-08-14, 08 stage)

| File | Origin | Notes | MD5 |
|---|---|---|---|
| `external/bts_table_2_17_safety.xlsx` | BTS National Transportation Statistics Table 2-17: https://www.bts.gov/content/motor-vehicle-safety-data | Fatalities, VMT, fatality rate per 100M VMT (FARS/FHWA-based), 1960–2024; 5-year steps before 1990. Retrieved through the user's browser: bts.gov and nhtsa.gov return 403 to command-line clients, which is also why the NHTSA FARS API was abandoned. | `244e088d8a1d62be331e692b1ef75e2e` |
| `external/fred_DAUTOSAAR.csv` | BEA via FRED, https://fred.stlouisfed.org/series/DAUTOSAAR | Domestic auto retail sales, millions SAAR, monthly, 1967+ | `524fae2a793164abed07289eaff9f306` |
| `external/fred_FAUTOSAAR.csv` | https://fred.stlouisfed.org/series/FAUTOSAAR | Foreign autos, same | `14b8850fbd91658cff95cbca3fb79d15` |
| `external/fred_DLTRUCKSSAAR.csv` | https://fred.stlouisfed.org/series/DLTRUCKSSAAR | Domestic light trucks, same | `499c939c3b98f15cbf3e2c28e78ce854` |
| `external/fred_FLTRUCKSSAAR.csv` | https://fred.stlouisfed.org/series/FLTRUCKSSAAR | Foreign light trucks, same | `d075be7775e6d5aa1570b9e927b0fb86` |
| `external/events_timeline.csv` | Curated in `08_extra_context.py` (regenerated each run) | 13 documented regulation/scandal/market events, one source citation per row. Annotation layer, not measurements. | `468f794ad4fa46a37de6594adb5ee3de` |

## Finance, energy, and fleet additions (2026-08-14, 14 stage)

| File | Origin | Notes | MD5 (first 16) |
|---|---|---|---|
| `external/fred_autoloan48.csv` | Fed G.19 via FRED: https://fred.stlouisfed.org/series/TERMCBAUTO48NS | 48-month new-car loan rate, %, QUARTERLY (annualized with min 3 obs/yr), 1972+ | `a1079fcbda86bc46` |
| `external/fred_electricity.csv` | BLS via FRED: https://fred.stlouisfed.org/series/APU000072610 | Electricity $/kWh, US city average, monthly, 1978+ | `b4b7c7c5f1999f34` |
| `external/bts_table_1_26_fleet_age.xlsx` | BTS NTS Table 1-26a: https://www.bts.gov/content/average-age-automobiles-and-trucks-operation-united-states | Average age of light vehicles in operation, 1995+; retrieved via user's browser (bts.gov 403s CLI clients); sheet also carries a second NHTS table the parser deliberately stops before | `fe275f317c4167cf` |
| `external/events_timeline.csv` | curated in 08_extra_context.py | now 16 events: added chicken tax (Proclamation 3564, 1963) and the 55 mph limit imposition (Pub. L. 93-239) and repeal (Pub. L. 104-59) | `bbe74ad34af9e3fd` |

Second embedded reference table: Census Bureau Table HH-4 average persons per
household (5-year sampling, hardcoded in `14_more_context.py` with source
link). Derived columns (cost-per-mile, parity ratio) documented in
`reports/14_more_sources.md`.

## Teammate dataset (2026-09-08, 16 stage)

| File | Origin | Notes |
|---|---|---|
| `Phil Data/Insurance Project Dataset - 2026.09.01.xlsx` | Compiled by teammate Phil. IIHS/HLDI insurance losses by make and model: https://www.iihs.org/research-areas/auto-insurance/insurance-losses-by-make-and-model | 11,313 vehicle-window rows, six relative loss measures, 2015-2017 through 2022-2024 windows. Automation scores (1-3) were generated with Grok and shipped WITHOUT citations (the workbook's supporting-links section is empty); automated audit in reports/16_insurance_prep.md, human-verification worksheet at outputs/automation_score_audit_sample.csv. Loss values are relative deviations from the all-vehicle average per IIHS methodology. |

## Embedded reference table (not a file)

CAFE passenger-car standards, MY1978–2010, hardcoded in `06_external.py`
(`CAFE_CAR_STANDARD`). Source: NHTSA published standard levels,
https://www.nhtsa.gov/laws-regulations/corporate-average-fuel-economy.
Single national values per year, including the 1986–1988 relaxation to 26.0.
Post-2010 standards are footprint-based per-fleet and deliberately not
represented by a single number.

## Pipeline (rerun order)

1. `01_inspect.py` -> `reports/01_schema_inventory.md`
2. `02_crosswalk.py` -> `crosswalk/*.csv`, `reports/02_joinability.md`
3. `03_merge.py` -> `outputs/full_wide.csv`, `outputs/analysis_clean.csv`, `outputs/my2024_config.csv`, `outputs/catalog_fegov.csv`, `reports/03_merge_report.md`
4. `04_filter_core.py` -> `outputs/analysis_core.csv`, `reports/04_core_filter.md`
5. `06_external.py` -> `outputs/context_annual.csv`, `reports/06_external_sources.md`
6. `08_extra_context.py` -> `outputs/context_extra.csv`, `external/events_timeline.csv`, `reports/08_extra_sources.md`
7. `10_stats.py` -> `outputs/stats_results.json`, `reports/10_statistics.md`
8. `12_validation.py` -> `outputs/validation_results.json`, `reports/12_validation.md`
9. `14_more_context.py` -> `outputs/context_finance.csv`, `reports/14_more_sources.md`
10. `16_insurance_prep.py` -> `outputs/insurance_clean.csv`, `outputs/automation_score_audit_sample.csv`, `reports/16_insurance_prep.md`
11. `17_insurance_model.py` -> `outputs/insurance_model.json`, `reports/17_insurance_model.md`
12. `19_final_model.py` -> `outputs/final_model.json`, `reports/19_final_model.md`
12b. `21_fetch_mympg.py` -> `external/mympg_cache.jsonl` (fueleconomy.gov My MPG API; resumable); `22_mympg_analysis.py` consumes it
12c. `23_powertrain_compare.py` -> `outputs/powertrain_trends.csv`, `outputs/powertrain_sensitivity.csv`, `reports/23_powertrain.md`; `24_charts_powertrain.py` -> fig33-fig36
12d. `25_atp_data.py` -> `outputs/atp_july2026.csv`, `reports/25_atp.md` (KBB/Cox July 2026 ATP report + EV Market Monitor, fetched 2026-09-08 via coxautoinc.com wp-json API; article-text snapshots in `external/cox_kbb_atp_july2026.txt` and `external/cox_ev_monitor_july2026.txt`); `26_charts_atp.py` -> fig37
12e. `external/carapi_sample_datafeed.zip` -- CarAPI vehicle data feed, FREE SAMPLE, downloaded 2026-09-10 from https://carapi.app/sample-opendatafeed (linked from https://carapi.app/features/vehicle-csv-download/). 17,573 US trims, model years 2015-2020, trim-level MSRP + dealer invoice + specs. Evaluation sample; current-year data is paid. Processed by `28_msrp.py` -> `outputs/msrp_2015_2020.csv`, `reports/28_msrp.md`, fig41. EPA Fuel Economy Guide datafiles were checked first (26data.zip, 162 columns) and confirmed to carry NO price field.
12f. `external/msrp_model_level.csv` -- SCAFFOLD, NOT DATA (for CURRENT 2026 models, which the CarAPI sample does not cover): 22 representative models (8 BEV, 2 FCEV, 5 hybrid, 7 gasoline) with blank msrp/destination-fee/source-url/date columns for manual fill from manufacturer sites. No per-model MSRP exists in any public bulk dataset consulted (EPA, fueleconomy.gov, NHTSA vPIC); prices must be hand-entered with a citation per row before any analysis touches this file.
13. `05_charts.py`, `07_charts_extended.py`, `09_charts_extra.py`, `11_charts_stats.py`, `13_charts_validation.py`, `15_charts_more.py`, `18_charts_insurance.py`, `20_charts_final.py` -> `charts/fig1..fig31`

Narrative index: see `STORY.md` for the full story log, figure inventory, deck
order, ideas backlog, and caveats canon.

Every stage is idempotent; identical inputs reproduce identical outputs
(verified by md5 across repeated runs during the build).
