# STORY.md — Master Narrative & Idea Log

The running record of every story thread, figure, statistical finding, decision,
and discarded idea in this project. Companion files: `DATA_SOURCES.md` (raw
input provenance with checksums) and the numbered reports in `reports/`.
Updated as the project evolves; this version reflects the state after the
statistics build (figs 1–21).

---

## 1. Project premise

A data-storytelling project about US light-duty vehicles, 1975–present, built
for a graduate probability & statistics course. The founding narrative: the gap
between what automakers **offer** (the catalog of configurations) and what
Americans actually **buy** (production-weighted reality), told through fuel
economy, size, power, and technology across five decades.

The structural constraint that shaped everything: no public file has
vehicle-level records *with* production volumes *across all years*. We have
production-weighted aggregates for 50 years (EPA Trends), production-weighted
vehicle detail for one year (MY2024 compliance files), and vehicle detail
without volumes for 40 years (fueleconomy.gov). The pipeline never fabricates
a bridge between those grains; every cross-grain comparison happens through
derived aggregates or is explicitly labeled.

## 2. Data foundation (details in DATA_SOURCES.md)

- **EPA Automotive Trends detailed by-manufacturer export** — the spine of
  `analysis_clean.csv`. 1975–preliminary 2025, production-weighted, 14 parent
  manufacturers + 'All', with the full technology-share block. Phase-1 finding:
  the second Tableau export ("Data by Vehicle Type") is a strict subset of this
  file, and neither is the Summary table (no CO2 anywhere — accepted, CO2 ruled
  out of scope).
- **MY2024 fuel-economy/technology + footprint files** — configuration grain,
  production volumes, joined 100% at carline level into `my2024_config.csv`.
- **fueleconomy.gov vehicles.csv** — the offer-side catalog, 1984–2027,
  50,242 configurations, no volumes. Canonicalized via the manufacturer
  crosswalk (85% of rows mappable to a Trends parent).
- **External context**: FRED (gas price, CPI, new-vehicle CPI, VMT, BEA
  car/light-truck sales split), BTS Table 2-17 (FARS fatalities & rates),
  NHTSA CAFE standards (hardcoded, documented), curated events timeline.

Standing data rules: no imputation, nulls stay null, every drop logged,
preliminary 2025 flagged never dropped, `'-'` means "not applicable/not yet"
not zero, and the three MPG definitions (real-world / CAFE 2-cycle /
window-sticker) never share an axis unlabeled.

## 3. The figure-by-figure story inventory

### Act I — The 50-year arc (core set, `05_charts.py`)

**fig1_three_acts** — *"Fuel economy stalled for 17 years while horsepower
doubled."* Four stacked panels (real-world MPG, HP, weight, 0–60) with the
1987–2004 stagnation band shaded. Key numbers: 13.1 MPG (1975) → 22.0 peak
(1987) → 19.3 trough (2004) → 27.2 (2024); HP 137→258; weight back to 4,354
lbs; 0–60 from 13.4s to 7.5s. The engineering gains of Act II went into power
and size, not economy. This is the deck's spine.

**fig2_sedan_inversion** — *"81% of production to 24%."* Stacked area of body
types. Sedan/Wagon 80.6% (1975) → 23.7% (2024); Truck SUV 1.7% → 49.6%.
Explains most of fig1's Act II.

**fig3_ev_gap** — *"Automakers offer EVs three times faster than Americans buy
them."* The literal offer/buy gap in 2024: 266 EV configurations = 21% of the
catalog offered, but 7.2% of production bought. Offered share derived from
vehicles.csv; bought share from Trends. Both are shares, so the axis is legal.

**fig4_tech_scurves** — *"GDI hit 56% in sixteen years; turbo took
twenty-eight to reach 44%."* Six adoption curves: carburetors 96%→extinct,
GDI, turbo, CVT, HEV, BEV. Production-weighted truth, not press releases.
(Statistical formalization later in fig18.)

### Act II — Context and causes (extended set, `07_charts_extended.py`)

**fig5_gas_vs_mix** — *"Expensive gas kept sedans alive; cheap gas buried
them."* Real gas price (2024$) above the sedan/truck shares. 1980's $4.74 and
2008's $4.76 peaks both coincide with sedan holds; the cheap-gas 2010s with
the truck breakaway. NOTE: fig19 later audits this narrative and finds the
annual-grain correlation is essentially zero — the deck should present both,
seduction then audit. That pairing is deliberate and is the course's
methodological centerpiece.

**fig6_standard_vs_achieved** — *"When the standard froze, so did progress:
22 years at 27.5 MPG."* CAFE passenger-car standard (step line, 1978–2010)
vs achieved 2-cycle car MPG — same test basis, so directly comparable. The
achieved line sits pinned to the frozen standard through 2007, then climbs
when footprint-based rules arrive (2011+). The causal frame for fig1's Act II.

**fig7_lab_vs_road** — *"The lab test drifted from the road: compliance MPG
runs 31% hot."* The ratio of 2-cycle to real-world MPG: +17% (1975) → +31%
(2024). The one chart where two MPG definitions meet on purpose; the ratio is
the story.

**fig8_manufacturer_race** — *"The 8-MPG spread: Honda has led for most of 50
years."* All 13 ICE-era manufacturers in gray, Honda/Toyota/GM highlighted.
2024: Honda 31.0, Stellantis 22.8. Tesla excluded and labeled why (117
MPGe-basis, different quantity).

**fig9_footprint_vs_mpg_2024** — *"Bigger footprint, lower economy, and the
volume sits in trucks."* Production-weighted carline scatter from
my2024_config. Build note: BEV rows leak through the FE_UNIT filter carrying
MPGe under an "MPG" label; the fix filters on combustion drive source. That
data trap is documented for the methods slide.

**fig10_trim_collapse** — *"The menu shrank: half the trims per model since
1984."* Configurations per base model 8.7 → 4.1. Offer-side texture.

**fig11_footprint_creep** — *"Everything got physically bigger, and pickups
most of all."* Footprint by body type since 2008 (when EPA began collecting
it); pickups ~66 sq ft.

**fig12_suv_reclassification** — *"Most SUVs are trucks on paper, and the
truck rulebook is easier."* Truck-classed share of SUV production: 91% (1990)
→ 72% (2010, crossover era) → 82% (2024). The regulatory-arbitrage story
behind fig2's green wedge.

### Act III — Independent witnesses (`09_charts_extra.py`)

**fig13_safety_dividend** — *"Cars got heavier, faster, and 3x safer per
mile."* Deaths per 100M VMT: 3.35 (1975) → 1.11 (2010) → ~1.2–1.4 (2021–24
reversal). The counterweight to fig1: the same decades that gave us bloat
gave us the safety dividend. Reversal cause deliberately not asserted.
(Statistical treatment in fig20.)

**fig14_sales_vs_production** — *"The truck takeover is real in both the
factory and the showroom."* EPA model-year production share vs BEA
calendar-year sales share of light trucks: two agencies, different
populations, same inversion. Credibility slide.

**fig15_scandal_overlay** — *"Where the scandals landed on the curves."*
Hyundai/Kia (Nov 2012 EPA-forced mileage restatement) and VW (Sept 2015
diesel notice of violation) marked on real-world MPG curves. Honest finding:
the Trends lines barely flinch, because the scandals hit *window labels and
lab conduct*, not this EPA-verified series. VW's post-2015 sag and EV-driven
2025 rebound is visible. Events documented in `external/events_timeline.csv`
(13 dated regulation/scandal/market events, one citation each).

### Act IV — The statistics homage (`10_stats.py` + `11_charts_stats.py`)

Full tables in `reports/10_statistics.md`; machine-readable results in
`outputs/stats_results.json`.

**fig16_changepoints** — *"The algorithm found the eras on its own: breaks at
1983, 2003, 2013."* Continuous piecewise-linear model, exhaustive SSE search
over break locations, order selected by BIC (3 breaks beats 2 narrowly:
−49.58 vs −48.14). Chow tests: 1983 F=13.7 (p≈2e−5), 2003 F=6.1 (p≈4e−3),
2013 F=3.5 (p≈0.04). The eyeballed eras of fig1 get mathematical legitimacy,
plus a bonus fourth act: the algorithm says the modern climb steepened around
2013.

**fig17_distribution_shift** — *"Buyers don't sample the catalog: a 3.5-MPG
shift and a long tail nobody buys."* Offered (each MY2024 model type once) vs
bought (production-weighted) MPG distributions: KS D = 0.211, Wasserstein =
3.06 MPG, medians 22.2 vs 25.7 — buyers systematically choose more efficient
than the catalog average. Companion Lorenz curve: Gini = 0.731; 176 of 768
carlines (23%) carry 80% of production. The founding offer-vs-buy thesis,
formalized.

**fig18_diffusion_fits** — *"Every technology is the same S-curve with a
different rate constant."* Logistic fits (ceiling L estimated, not assumed):
GDI k=0.61 (7.2-year 10%→90% run) vs turbo k=0.29 (15.3 years) — 2.1× faster.
HEV is the slow burner (fitted midpoint 2036). The honest ambiguity is BEV:
the fit put its ceiling at L=0.10, meaning the data cannot yet distinguish
"early S-curve" from "low plateau" — the widest bootstrap CIs in the table,
and the deck should say "believe the dashes least."

**fig19_correlation_that_wasnt** — *"Gas prices explain almost none of the
truck takeover."* The planned lesson was the classic spurious-regression trap;
the data delivered a sharper one. Levels r² = 0.007 (r = −0.08, p = 0.57);
first differences r² = 0.003 (p = 0.70). Truck share rose monotonically while
real gas price oscillated, so fig5's visual co-movement is secular trend plus
episodes, not an annual elasticity. Year-colored scatter shows the vertical
drift (time) dominating the horizontal axis (price). Lessons: eyeballed
co-movement ≠ association; a monotone trend can't correlate strongly with a
mean-reverting series in levels; identifying a price effect needs micro data.
**Deck beat: show fig5, let it persuade, then show fig19.**

**fig20_fatality_glm** — *"The pandemic-era fatality reversal is statistically
real, not noise."* Poisson GLM via hand-rolled IRLS, exposure offset
log(VMT/100M), fit 1990–2019 (trend −2.08%/yr), quasi-Poisson dispersion
φ = 115 scaling all SEs. Out-of-sample 2021: 43,230 observed vs 31,101
expected = +12,129 excess deaths, z = 6.0. Even with brutal overdispersion
scaling, six standard errors. Textbook GLM with a conclusion that matters.

**fig21_convergence** — *"The field converged for two decades, then
electrification split it again."* Cross-sectional SD of real-world MPG on the
balanced 8-manufacturer panel (avoids entrant composition effects): 6.14 peak
(1977) → under 2 from the early 1990s through 2008 → back to 3.2 (2024) as
hybrid-heavy manufacturers (Honda, Toyota) pull away from truck-heavy ones
(Ford, GM, Stellantis). Original hypothesis was monotone convergence; the
data said convergence-then-divergence, and the divergence is the more
interesting half.

### Act V — Validation: stress-testing our own claims (`12_validation.py` + `13_charts_validation.py`)

Eight checks (A–H) that treat the deck's own claims as hypotheses. Full
tables in `reports/12_validation.md`; results in
`outputs/validation_results.json`. Three earned figures:

**fig22_allocation_proof** — *"The engine never stalled, only the allocation
did."* Validation A, the deck's central claim tested. The fig16 changepoint
machinery applied to ton-MPG (weight-normalized efficiency): through the
1987–2004 MPG trough, ton-MPG climbs +0.25/yr (CAGR +0.65%/yr) while raw MPG
fell 12%. No negative segment anywhere. Verdict: **CONFIRMED** — engineering
efficiency improved every year of the "stagnation"; the gains were spent on
weight and power. Bonus: its own breakpoints (1983, 2005, 2018) show
electrification bending the curve to +3.2/yr after 2018.

**fig23_bunching** — *"Manufacturers parked just above the frozen standard."*
Validation B. Freeze era (1990–2007): 44% of manufacturer car-fleet years sat
within 0–3 MPG above the 27.5 standard, median gap 0.72 MPG. Footprint era
(2012–2019): 6% in that band, median gap 8.87 MPG. KS D = 0.833, p ≈ 5e−54.
Verdict: **CONFIRMED** — the standard was binding; fig6's causal framing
survives. (Caveat on the slide: true CAFE compliance uses harmonic-mean fleet
math and credits; this is the approximation.)

**fig24_event_study** — *"1979 was a real episode; the 2008 'sedan rebound'
wasn't."* Validation C. Sedan-share deviation from local trend, 4-year
windows, vs 31 placebo windows: the 1979 shock scores at the 100th percentile
(+0.054, the strongest sedan hold in the record); the 2008 spike scores at
the **52nd percentile — indistinguishable from noise**. Half of fig5's
episode narrative survives, half doesn't.

Report-only checks: **D** — logistic beats Gompertz on AIC for all five
technologies (fig18's premise stands), but Durbin–Watson flags serial
correlation on the slow diffusers (HEV 0.48, CVT 0.93), so those bootstrap
CIs are lower bounds on uncertainty. **E** — the fig21 re-divergence is
significant, barely: Brown–Forsythe p = 0.042. **F** — fig16's breaks: 1983
[1982–1984] and 2003 [2001–2003] are tight and replicate within cars-only
(1983, 2006, 2018) and trucks-only (1983, 2004); the 2013 fleet break has a
sloppy CI [2010–2018] and should be demoted from "fourth act" to "suggestive."
**G** — Hyundai step −0.77 (CI −2.92 to +1.38, p = 0.50), Kia −2.00 (CI −4.32
to +0.32, p = 0.12): no statistically detectable level shift after the 2012
restatement, confirming fig15's "labels, not this series" (Kia's
negative-leaning CI is worth a spoken aside). **H** — sales and production
truck shares: differenced cross-correlation peaks at lag −1 (0.59), i.e. the
showroom leads the factory's model-year accounting by about a year, exactly
what the calendar-vs-model-year offset predicts.

### Act VI — Money, energy, and time (`14_more_context.py` + `15_charts_more.py`)

**fig25_credit_trap** — *"Revision #7: the cheap-credit story."* Auto-loan
rates (Fed G.19, 1972+) vs truck share: levels r² = 0.568 (p = 3e−10) — the
spectacular spurious-levels regression fig19 originally went looking for —
collapsing to r² = 0.045, p = 0.145 in first differences. Two-panel design:
the seduction (indexed overlay), then the audit (differenced scatter). The
deck now has the trap demonstrated for real, and the credit story joins gas
prices in the "seductive overlay, no annual association" bin.

**fig26_ev_parity** — *"EV miles are still cheaper, but the advantage is
quietly shrinking."* Energy cost per mile: gas price / fleet real-world MPG
vs electricity price × catalog EV consumption. The EV operating advantage was
2.9× in 2012 and is 1.85× in 2024 — electricity prices rose while gas cars
got more efficient. Pairs with fig3/fig18's adoption question: the economic
tailwind behind EV adoption is weakening, not strengthening. Scope honesty on
the slide: energy only; excludes purchase price, depreciation, DC-fast
premiums.

**fig27_household_irony** — *"Households shrank while their vehicles grew."*
Census persons-per-household (2.94 → 2.51, −15%) over average vehicle weight
(+35% since 1981). Two panels, shared clock; the footnote says the correlation
is not causation — the juxtaposition is the point.

**fig28_fleet_age** — *"The road lags the factory."* BTS average light-vehicle
age: 8.4 years (1995) → 12.6 (2024). The reframing insight for every adoption
chart in the deck: at a 12.6-year average age, the median vehicle in traffic
was built around 2013 — before GDI, turbo, and CVT hit their fitted S-curve
midpoints. Production share is not road share; the street runs about a decade
behind our fig4/fig18 curves.

Timeline additions: the 1963 "chicken tax" (25% light-truck tariff — the
structural reason truck production is domestic and profitable; context for
figs 2, 12, 14) and the 55 mph national speed limit (1974 imposed, 1995
repealed; context for fig13). `external/events_timeline.csv` now holds 16
events.

### Act VII — The insurance regression (`16_insurance_prep.py` + `17_insurance_model.py`)

Phil's IIHS/HLDI dataset (Phil Data/Insurance Project Dataset -
2026.09.01.xlsx) turned the project into the assignment's required shape: one
row per vehicle × 3-year loss window (11,313 rows), DV = relative collision
loss, IVs = automation score + size + body group + year + joined catalog MPG
and EV flag. 10:1 rule cleared ~1,000×.

**The Grok audit** (reports/16_insurance_prep.md): the automation scores are
AI-generated with an empty supporting-links section, so stage 16 runs four
automated checks — zero duplicate-key conflicts; 540 of 2,369 vehicles change
score across windows (so scores are not purely nameplate-constant); zero
era-adjusted EV anomalies (the first pass flagged 2013-2017 Leaf/Volt-era EVs
until the check was made era-aware — itself a lesson in anachronistic
validation); zero Tesla anomalies — and emits
outputs/automation_score_audit_sample.csv, a 30-vehicle worksheet with blank
verified-score/source/agree columns for human verification. Catalog join hit
92.2% after trim-suffix handling ('civic si hatchback' → 'civic').

**The models** (reports/17_insurance_model.md): OLS, cluster-robust SEs by
vehicle. Robust finding: score-3 automation carries **+0.24 collision loss
vs Basic (p = 0.003)** with all controls held — the sensor-repair penalty is
real. The injury benefit is direction-only: every injury coefficient is
negative but none clears 0.05 once clustered (p = 0.07-0.26); the raw-means
sign flip is mostly absorbed by size/body/year controls. Deck framing:
"automation demonstrably raises repair losses; the injury offset is
consistent but underpowered here" — which also feeds the revisions thread
(the raw gradient looked like a two-sided finding until the controls and
clustering arrived).

BLUF candidate for the briefing: *Advanced automation is associated with a
24-point collision-loss penalty relative to basic vehicles, holding size,
body type, year, fuel economy, and powertrain constant; claimed injury
benefits do not reach significance in these data.*

**fig29_coefficients** — dot-and-whisker of all six automation terms across
the three DVs, cluster-robust 95% CIs, filled markers for p < 0.05. One
filled marker on the chart: the +0.24 collision penalty. The visual IS the
BLUF slide.

**fig30_raw_vs_controlled** — revision #8 rendered: left panel shows the
seductive raw-means story (collision worsens, injury improves, monotone in
score); right panel shows what survives controls and clustering (collision
p = 0.003, injury p = 0.262). The regression act's version of the fig5->fig19
pairing, and the eighth entry in the "statistics changed our minds" thread.

**Robustness spec** (reports/17_insurance_model.md): a single-window
2022-2024 cross-section (620 independent rows, 51:1 obs-per-parameter)
satisfies the strictest reading of the course's row-per-observation guidance
but cannot identify the automation contrast: only 4 score-1 vehicles remain
by 2022-2024 because nearly everything now ships standard ADAS (vs 5,886
score-1 rows across the panel's earlier windows). The collision coefficient
goes to p = 0.55 there -- unidentified, not refuted. This is the stated
justification for the panel-with-clustered-SEs primary spec, and a good
methods-slide beat: the design choice is driven by identification, not
convenience.

### Act VIII — The presentation model (`19_final_model.py` + `20_charts_final.py`)

Chosen as the briefing's centerpiece because the user wants a relationship
that demonstrably works: **ln(MPG) ~ ln(weight) + ln(HP) + footprint +
hybrid** on 1,025 independent MY2024 combustion model types.
**R² = 0.846** (adjusted 0.845), F = 1,401, every predictor p < 0.001,
205:1 observations per parameter, VIFs ≤ 3.4. Elasticities: 10% more HP
costs 4.8% MPG; 10% more weight costs 3.0%; a hybrid powertrain buys ~23%
at the same weight/power/size. Robustness: linear-DV and no-footprint specs
barely move anything (reports/19_final_model.md).

**fig31_predicted_vs_actual** — the proof slide: predicted vs actual MPG,
tight 45° cloud, R² printed on it.

Division of labor in the deck: this model is the *primary* regression (high
R², physical interpretation, clean cross-section); the insurance model
(Act VII) becomes the *secondary* analysis showing what real-world
behavioral data looks like (R² 0.25, one significant effect, careful
clustering) — the contrast between the two IS a teaching point.

### Act IX — BEV vs Hybrid vs Gasoline (`23_powertrain_compare.py` + `24_charts_powertrain.py`)

The user-chosen presentation direction: powertrain economics, vehicle-level,
with time trends. Table: outputs/powertrain_trends.csv (year x group medians);
report: reports/23_powertrain.md.

**fig33_cost_trends** — median energy cost per mile by group at each model
year's national prices, 2011-2026. 2024 medians per 15k miles: BEV $1,007,
Hybrid $2,069, Gasoline $2,463. Extends fig26's fleet pair to three groups.

**fig34_label_efficiency** — median window-sticker efficiency by group with
MPGe explicitly flagged as an energy-equivalence unit. The finding is
composition: BEV median MPGe peaked ~110 in the 2018-2020 sedan era and fell
to 87 as electric trucks/SUVs arrived; hybrid MPG fell post-2020 for the
same reason. The SUV-ification of fig2 invading both new powertrains.

**fig35_bev_range** — median rated BEV range: 82 mi (2012) -> 283 mi (2024).
Gas/hybrid range NOT computable (catalog has no tank size) -- stated, not
faked.

**fig36_price_sensitivity** — the user's sensitivity-analysis idea: hold 2024
median efficiency fixed, sweep each energy price across its observed
2011-2026 range. Annual swing at 15k miles: Gasoline $1,394, Hybrid $1,171,
BEV $370 -- and the BEV's worst-price year ($1,119) beats gasoline's best
($1,530). Gas CV 0.20 vs electricity CV 0.14: commodity vs regulated
utility. "BEVs are cheaper AND stabler" is the slide.

Data-honesty rulings recorded in the report: PHEVs excluded (utility-factor
assumptions), MSRP/vehicle price absent from all project datasets (not
fabricated), MPGe definitional flag mandatory on any shared axis, cost
figures are energy-only (no TCO).

### Act IX addendum — acquisition cost (`25_atp_data.py` + `26_charts_atp.py`)

The sticker-price gap closed with real data: Kelley Blue Book / Cox
Automotive July 2026 ATP report + EV Market Monitor, fetched via Cox's
WordPress REST API (the article pages themselves are a JS shell), text
snapshots archived in external/ for checkability.

**fig37_acquisition_cost** — what Americans actually paid, July 2026:
industry $49,855; EV average $56,126 (premium over ICE+ $6,477); Tesla
$53,891; segments from full-size pickup $66,980 down to compact car
$27,904. ATP = price paid (mix + incentives), not MSRP; both numbers
reported (MSRP average $51,621).

**The synthesis line for the deck** (reports/25_atp.md): EV costs ~$6,477
more to buy and ~$1,456/year less to fuel (fig33/fig36) -> energy savings
alone repay the purchase premium in ~4.5 years.

Recorded limitation: KBB publishes no hybrid-only ATP (ICE+ folds hybrids
in), so the three-way BEV/Hybrid/Gasoline price split cannot be completed
from public data; stated, not estimated. Era-restricted efficiency fits also
logged: combustion label-MPG model R² = 0.777 (2000+, n=30,659) vs 0.710
(2020+, n=7,890 -- displacement variance compressed by downsizing); clean
BEV MPGe physics fit R² = 0.708 (n=153, weight elasticity -0.97) after
fixing a drive-source filter leak that let PHEV gas-mode rows contaminate
the sample.

**figs 38–40, the range-grain trilogy** (`27_charts_range.py`, revised to
three separate figures at user request):

- **fig38** — config-level BEV range on year, three windows: from 2000
  R² = 0.339 (+11.9 mi/yr, n = 1,562); from 2010 R² = 0.301 (+12.8, 1,549);
  from 2020 R² = 0.058 (+8.5, 1,370). R² collapses as the window shortens
  because within-year spread dominates.
- **fig39** — identical data aggregated to yearly medians, same windows:
  R² = 0.809 / 0.883 / 0.881. The fig38-vs-fig39 pairing is a one-slide
  lesson: the R² gap is grain, not physics.
- **fig40** — the hydrogen profile: *"Hydrogen never had a range problem;
  it had a catalog problem."* FCEV median range above BEV's the whole
  decade (357 vs 283 in 2024), but three nameplates ever (Mirai,
  Nexo/Tucson FC, Clarity FC), peaking at 5 configs/yr vs 266 BEV configs
  in 2024.

FCEV is now a group in `powertrain_trends.csv` and appears on fig34
(efficiency, ~65 MPGe flat) and fig35 (range). Two recorded gaps: no public
retail hydrogen price series (AFDC's report has no fetchable H2 retail
data), so FCEV cost-per-mile stays null; and KBB publishes no FCEV ATP, so
fig37 cannot include hydrogen acquisition cost.

**fig41_msrp_by_powertrain** (`28_msrp.py`) — model-level MSRPs found: the
CarAPI free sample feed (17,573 US trims, 2015-2020, trim MSRP + dealer
invoice), archived in external/, powertrain-classified at 80.1% via
catalog join. Median stickers 2015-2020: Hybrid cheapest ($24k→$39k),
Gasoline steady ($35k→$40k), FCEV flat at ~$58.5k (Mirai only), BEV
volatile on 11-31 trims/yr (Bolt/Leaf years vs Tesla-heavy years,
$29k→$60k). "The era when electric meant expensive." Pairs with fig37
(2026 transaction prices) as before/after. EPA's Fuel Economy Guide
datafiles were checked and carry no price column; current-2026 MSRPs
remain the hand-fill scaffold.

**fig42_productivity_projection** (`29_productivity.py`) — the
design-normalized productivity series: fleet MPG re-expressed at constant
2024 weight/HP via the stage-19 elasticities. The 1987–2004 trough
vanishes; growth runs +1.94%/yr for 50 years (R² = 0.984); projected
~35 MPG-equivalent by 2035 and 40–44 by 2045 under the two documented
rates. Caveats in reports/29_productivity.md (elasticity stability, EV mix
folded in, no physics ceiling). Deck: backup slide 20; six backup slides
(15–20) added overall, claim-titled per the instructor's titles-tell-the-
story criterion — fig16, fig19, fig17, fig41, fig33, fig42.

**figs 43–44, productivity by class and powertrain**
(`30_class_productivity.py`) — fig42's normalization broken out. fig43:
every Trends class (Sedan/Wagon, Car SUV, Truck SUV, Pickup, Minivan/Van)
normalized to its own 2024 design grows a steady 2.0–2.6%/yr with
log-linear R² 0.93–0.99 — the productivity law is class-universal; classes
differ in level, not rate. Car SUV fastest (2.57%/yr, crossover
hybridization + Model Y classed there); pickups slowest (2.00%). No
'coupe' exists in Trends (two-doors fold into Sedan/Wagon; no two-door
weight/HP series exists anywhere in the project — stated, not faked).
fig44: the EV version via the only design-normalizable EV series (EPA
Trends Tesla rows, 2012–2024, BEV-model weight elasticity −0.975):
**+2.36%/yr — inside the same band as every combustion class.** One
productivity clock, two energy carriers.

## 4. Suggested deck order

1. fig1 (the arc) → fig16 (the algorithm agrees)
2. fig6 (the frozen standard) → fig5 (the gas-price story) → **fig19 (the
   audit of fig5)** — the methodological heart of the deck
3. fig2 (sedan inversion) → fig14 (two-source confirmation) → fig12 (the
   truck-rule incentive) → fig11 (size creep)
4. fig13 (safety dividend) → fig20 (the reversal is real)
5. fig4 (tech S-curves) → fig18 (fitted rate constants) → fig8 (who led) →
   fig21 (convergence-then-divergence)
6. fig17 (offer vs buy, formalized) → fig3 (the EV gap) → fig18's BEV panel
   as the open question that ends the talk
7. Texture/reserve: fig7 (lab vs road), fig10 (trim collapse), fig9 (2024
   scatter), fig15 (scandals)

## 4b. The revisions: where the statistics changed our minds

This is a deliberate narrative thread, not an embarrassment log. For a
probability & statistics course, the strongest thing the deck can show is a
claim we believed, the instrument that tested it, and the mind changed in
public. Every item below is a place where better statistical machinery
overturned or sharpened a conclusion we had already drawn — present them as
the story's spine, not its footnotes:

1. **"Cheap gas buried the sedan" → "the trend buried the sedan."** fig5's
   overlay persuaded us; fig19's scatter (levels r² = 0.007) showed the
   annual relationship barely exists; fig24's event study then rescued
   exactly half the claim: 1979 was a genuine episode (100th percentile),
   2008 was noise (52nd). The narrative got *more* accurate twice.
2. **"The stagnation era" → "the allocation era."** fig1 said progress
   stopped for 17 years. fig22 proved nothing stopped: ton-MPG rose every
   single year; the industry chose to spend the gains on 90 extra horsepower
   and 900 pounds. The revised claim is sharper and better supported than
   the original.
3. **"Three acts" → "three acts, maybe a fourth."** fig16's BIC narrowly
   preferred a 2013 break; validation F's bootstrap put a [2010–2018] CI on
   it. The 1983 and 2003 breaks survived every robustness check; 2013 gets
   demoted to "suggestive." Model selection giveth, uncertainty
   quantification taketh away.
4. **"Convergence" → "convergence, then divergence."** The planned fig21
   story was regulatory compression. The data showed the field re-spreading
   after 2010 (Brown–Forsythe p = 0.042) as electrification strategies
   diverged — a more interesting finding than the hypothesis.
5. **"BEV is the fastest S-curve" → "BEV is the widest confidence
   interval."** The logistic fit put BEV's ceiling at L = 0.10; the honest
   reading is that the data cannot yet distinguish an early takeoff from a
   low plateau. The slide now says "believe the dashes least."
6. **"The scandals dented the data" (reasonable prior) → "the scandals dented
   the labels, not the verified series."** fig15's eyeball claim, then
   validation G's interrupted time series: steps statistically
   indistinguishable from zero for both Hyundai and Kia.

Suggested framing slide for the course: *"Six times this deck changed its
mind. Each time, the correction came from a named method — a scatter, an
event study, a changepoint search, a bootstrap, a variance test, an
interrupted time series — not from a stronger opinion."*

## 5. Ideas built, declined, and still open

**Built**: everything above, plus the manufacturer crosswalk
(385 raw-string mappings), the 78.5% config-level attach (user-accepted with
`my24_matched` flag), the core complete-case view (`analysis_core.csv`, with
the preliminary-year production exemption), and the events timeline.

**Declined, with reasons** (keep for the limitations slide):
- IIHS crash ratings — no bulk public download, licensing risk in scraping.
- Insurance categories/rates — proprietary state filings; the public III
  series is national-aggregate, 1998+, joins on nothing useful.
- NHTS driver demographics — survey waves (1977…2022) don't align with an
  annual model-year spine; a separate project.
- NCAP crash-test ratings — bulk data exists but requires 35 years of
  free-text name matching (the 78.5% problem, compounded) plus a 2011 rating
  protocol break; mediocre effort-to-payoff. Revisit if a safety-deep-dive
  chapter is wanted.
- Fuzzy name matching to push the vehicles↔MY2024 attach past 80% — small
  payoff (one year of 44), real false-match risk.
- CO2 series — requires the Trends Summary export we don't have; user ruled
  CO2 out of the narrative.
- NHTSA FARS API — blocked (403) for CLI clients and the sandboxed browser;
  BTS Table 2-17 carries the same FARS-based series and was retrieved through
  the user's browser instead.

**Open threads worth considering later**:
- Quantile regression on my2024 (efficiency frontier vs median at given
  footprint) — "how good could a truck be?"
- Weighted least squares elasticity of MPG on footprint/weight/HP with VIF
  discussion (multicollinearity is severe and that's the teaching point).
- The 2013 changepoint deserves its own explanation slide (GDI+turbo+CVT all
  inflect near there; fig18's midpoints cluster 2012–2017).
- Re-export the Trends Summary table if CO2 ever re-enters scope.
- Dark-mode variants of the figure set for a dark deck template.

## 6. The caveats canon (recite before every chart decision)

1. Three MPG definitions — Trends real-world, CAFE 2-cycle, window-sticker —
   differ 20–30% for the same vehicle; never share an axis unlabeled (fig7 and
   fig6 are the two sanctioned meetings, ratio and same-basis respectively).
2. Preliminary 2025 is always dashed with an open marker, footnoted, and
   carries no production volumes (hence its exemption in analysis_core).
3. Calendar year ≠ model year; sales ≠ production. Cross-source overlays are
   approximate by design and say so.
4. The BLS new-vehicle CPI is hedonically quality-adjusted: its fall means
   price-per-quality-unit fell, not that stickers got cheaper. Kept out of
   charts for that reason.
5. `'-'` in Trends exports = not applicable / technology didn't exist yet;
   stored as null, never zero. Tech-share nulls are informative, not missing.
6. BEV rows can carry MPGe under an "MPG" unit label in the MY2024 file;
   filter on combustion drive source, not FE_UNIT alone.
7. Production volumes repeat per configuration row; dedupe to model type
   before summing (naive sums run ~40% hot).
8. FARS fatality counts pre-1990 are 5-year steps; the CRSS/GES redesign
   (2016) and vPIC reclassification (2020) break other columns of Table 2-17,
   though not the fatality series we use.

## 7. Pipeline map

| Stage | Script | Outputs |
|---|---|---|
| Inspect | `01_inspect.py` | `reports/01_schema_inventory.md` |
| Crosswalk + joinability | `02_crosswalk.py` | `crosswalk/*.csv`, `reports/02_joinability.md` |
| Merge | `03_merge.py` | `outputs/full_wide.csv`, `analysis_clean.csv`, `my2024_config.csv`, `catalog_fegov.csv`, `reports/03_merge_report.md` |
| Complete-case | `04_filter_core.py` | `outputs/analysis_core.csv`, `reports/04_core_filter.md` |
| Core charts | `05_charts.py` | fig1–fig4 |
| External context | `06_external.py` | `outputs/context_annual.csv`, `reports/06_external_sources.md` |
| Extended charts | `07_charts_extended.py` | fig5–fig12 |
| Safety/sales/events | `08_extra_context.py` | `outputs/context_extra.csv`, `external/events_timeline.csv`, `reports/08_extra_sources.md` |
| Extra charts | `09_charts_extra.py` | fig13–fig15 |
| Statistics | `10_stats.py` | `outputs/stats_results.json`, `reports/10_statistics.md` |
| Stats charts | `11_charts_stats.py` | fig16–fig21 |
| Validation | `12_validation.py` | `outputs/validation_results.json`, `reports/12_validation.md` |
| Validation charts | `13_charts_validation.py` | fig22–fig24 |
| Finance/energy/fleet | `14_more_context.py` | `outputs/context_finance.csv`, `reports/14_more_sources.md` |
| Finance charts | `15_charts_more.py` | fig25–fig28 |

Every stage is idempotent (verified by md5 across repeated runs). Rerun any
stage independently; rerun 01→11 to rebuild the world from the nine raw
inputs in `DATA_SOURCES.md`.
