# SHORTSTORY.md — The MPG Prediction Deck (22 core + 12 backup)

The focused companion to STORY.md. One relationship, one equation, one
deck: predicting a vehicle's fuel economy from its physical design, for
gasoline, hybrid, and electric vehicles alike, and what that prediction
unlocks for reading fifty years of fleet history and projecting the next
twenty. Deck file: `MPG Prediction Deck.pptx` (34 slides). Builder:
`deck_build3.js` (pptxgenjs); QA: python-pptx structural check + PowerPoint
COM PNG export, every core slide inspected.

---

## 0. Terminology, stated once and correctly

**MPG is the DEPENDENT variable** (the response, y — the thing we predict);
for battery-electric vehicles it is MPGe, miles per 33.7 kWh, the same EPA
test on the same energy basis. **Weight, horsepower, and powertrain
(hybrid flag, battery-electric flag) are the INDEPENDENT variables** (the
predictors, x). The assignment requires one dependent variable and at least
three independent variables; this model has one and four.

## 1. The equation (the deck's center)

    ln(MPG) = 9.26 − 0.453·ln(weight) − 0.369·ln(HP) + 0.224·hybrid + 1.708·electric + ε

- **DV**: ln of EPA unadjusted 2-cycle combined MPG (MPGe for BEVs), one
  row per MY2024 model type: 775 gasoline/diesel + 250 hybrid + 260 BEV =
  **n = 1,285**.
- **IVs**: ln(CAFE inertia weight, lbs), ln(rated horsepower), hybrid 0/1,
  battery-electric 0/1 (gasoline/diesel is the reference level; powertrain
  is one categorical variable with three levels).
- **Fit**: OLS with HC1 heteroskedasticity-robust standard errors.
- **R² = 0.955** (adjusted 0.954), F(4, 1280) = 6,732, every predictor
  p < 0.001 with the pre-stated sign, 256 observations per parameter
  (10:1 rule cleared 25×). VIFs ≤ 1.9.
- **Coefficient table** (from `outputs/pooled_model.json`, spec F):

  | term | coef | HC1 SE | t |
  |---|---|---|---|
  | intercept | 9.258 | 0.201 | 46.0 |
  | ln(weight) | −0.453 | 0.029 | −15.4 |
  | ln(HP) | −0.369 | 0.015 | −24.6 |
  | hybrid | +0.224 | 0.011 | 21.0 |
  | battery-electric | +1.708 | 0.014 | 117.7 |

Why log-log: coefficients read as **elasticities** — 10% more weight costs
4.5% of MPG; 10% more horsepower costs 3.7%; a hybrid buys +25% at the same
weight and power; a BEV buys +452% (in MPG-equivalent).

Prediction band: residual SD in logs s = 0.135, a typical miss of ~14%;
the 95% band is predicted ×/÷ 1.30 and holds 94% of model types.

### How BEVs got into the equation (stage 33)

- The MY2024 FE file leaves `ENG_RATED_HP` blank for every BEV. Rated HP
  was joined from the **EPA MY2024 Test Car List**
  (`external/epa_24_testcar_2025-05.xlsx`): 96.3% of BEV model types
  matched; the same key reproduces the filed HP within 10% for 86.5% of
  combustion rows (where HP is known), which is the validation.
- Two BEV rows had kWh/100 mi in the MPGe cell (Model S Plaid 21in, Q4 40
  e-tron); caught because an unadjusted value cannot sit below its own
  5-cycle label; recomputed as 3370.5 / cell. Logged in the report.
- Footprint, kept in the combustion-only model, drops out once BEVs are
  in (t = 0.1, p = 0.87; nested F = 0.03). Final equation has no footprint.
- **The merged-dummy question** (asked by the presenter): one
  "electrified" flag for hybrids + BEVs gives R² = 0.465 and flips the
  weight sign; mean residual −49% for hybrids, +93% for BEVs. Nested
  F(1, 1279) = 13,798 for splitting it. Slide 15 and fig52.
- **BEV-specific slopes** (backup): weight elasticity −1.05, HP ≈ 0
  (F(3, 1276) = 179). The common-slope equation is a fleet-wide
  compromise costing 1.3 points of R² (0.955 vs 0.968); chosen for one
  equation, one story.
- Outliers (studentized residuals): VF 8 Plus (−5.1), Fiat 500e (−4.4),
  Lucid Air variants (+3.5 to +4.2), Ioniq 5 Robotaxi (−3.7). All real
  vehicles; all kept.

Sources: `33_pooled_model.py`, `reports/33_pooled_model.md`,
`outputs/pooled_model.json`, `outputs/my2024_pooled.csv`;
`34_charts_pooled.py` -> fig49 (weight), fig50 (HP), fig51 (predicted vs
actual with band), fig52 (merged dummy fails). Combustion-only model
(stage 19, R² 0.846) remains as backup spec A.

## 2. The adjacent elements (why anyone cares)

Money is the through-line: consumers do not buy MPG, they buy annual cost.

- **Energy cost per mile** (fig33): gasoline $0.164/mi vs BEV $0.067 —
  $2,463 vs $1,007 per 15k-mile year at 2024 prices.
- **Price-shock exposure** (fig36): observed 2011–2026 prices swing a
  gasoline driver's annual bill by $1,394; a BEV driver's by $370.
- **Acquisition cost** (fig37, KBB July 2026): industry ATP $49,855; EV
  premium $6,477 → energy savings ($1,456/yr) repay it in ~4.5 years.
- **The 50-year backdrop** (fig1): MPG 13.1 → 22.0 → 19.3 → 27.2; the
  1987–2004 trough is where efficiency gains were spent on weight and
  power — precisely the tradeoffs the equation prices.
- **The sales mix** (fig2): sedans 81% → 24% of production; Truck SUV 50%.
- **EVs** (fig3): 21% of the 2024 catalog, 7.2% of production; 2023
  Car SUV BEV share 35.7% (Model Y), 2024 sedan-class share halves.
- **Technology S-curves** (fig18): logistic diffusion, GDI 2.1× faster
  than turbo; the BEV ceiling carries the widest CI.

## 3. Design-normalized productivity (stages 29–31)

MPG_norm(t) = fleet MPG × (wt_t/wt₂₀₂₄)^0.453 × (hp_t/hp₂₀₂₄)^0.369 —
each year's technology expressed at 2024's production-weighted fleet
weight and power, using the deck's own (pooled) elasticities. Worked
example, 1987: 22.0 × 0.872 × 0.748 = 14.3.

- The 1987–2004 trough **vanishes**: 10.0 → 14.3 → 17.4 → 27.2, monotone.
- **+1.79%/yr for 50 years, R² = 0.980**; +2.19%/yr since 2005.
- Projection at constant 2024 design: ~35 by 2035, **38–43 by 2045**.
- Per class (fig43): 1.8–2.4%/yr everywhere, R² 0.92–0.98; Car SUV
  fastest (2.41%), Pickup slowest (1.84%). The 2023 Car SUV spike is the
  Model Y (annotated on the chart); 2024 dip = credit hangover; 2024 final.
- Backup: combustion-only series (stage 31, combustion-only elasticities
  0.304/0.483): +1.86%/yr, 39 by 2045 — same clock without electrics.
- Two R² values in the deck: 0.955 (cross-section, 1,285 vehicles) and
  0.980 (50-year trend line, 50 points) are different regressions. Said
  on slide 18.

## 4. The 34 slides (9-part structure)

| # | Section | Slide title | Visual |
|---|---|---|---|
| 1 | — | Predicting MPG (title) | dark |
| 2 | 1 Fuel costs + research question | Fuel is a four-figure annual bill, and MPG sets it | stats |
| 3 | 2 Data understanding: trends | Fifty years of fleet MPG: it rose, stalled for 17 years, then rose again | fig1 |
| 4 | 2 classes | The sales mix inverted: sedans fell from 81% of production to 24% | fig2 |
| 5 | 2 buyers | Why buyers care: MPG is a cash-flow forecast | fig36 |
| 6 | 2 EVs | EVs: offered faster than bought, and sensitive to the tax credit | fig3 |
| 7 | 2 future trends | Efficiency technology arrives on S-curves; the EV curve is the youngest | fig18 |
| 8 | 3 X/Y: the data | Two EPA datasets: the 50-year fleet record, and 1,285 model types for 2024 | fields table |
| 9 | 3 X/Y: hypotheses | One dependent variable, four independent variables, five hypotheses | H₀/Hₐ table |
| 10 | 3 X/Y: weight | Heavier is thirstier for every powertrain: 10% more weight costs 4.5% of MPG | fig49 |
| 11 | 3 X/Y: horsepower | Power costs economy: 10% more horsepower costs 3.7% of MPG | fig50 |
| 12 | 4 OLS: equation | The equation: multiplicative physics, estimated as a straight line in logs | equation |
| 13 | 4 OLS: results | Results: all four predictors reject H₀ and together explain 95.5% of MPG | table + t/F/VIF callouts |
| 14 | 4 OLS: fit | What R² = 0.955 looks like: 94% of vehicles land inside a ±30% band | fig51 |
| 15 | 4 OLS: powertrain | Hybrids and electrics cannot share one flag: their premiums differ eighteen-fold | fig52 |
| 16 | 5 Normalization: why | The exchange rate: what mass, power, and powertrain cost or buy in MPG | stats + fig22 |
| 17 | 5 Normalization: how | How we normalized: the equation re-prices every year at 2024's design | 3 steps + worked example |
| 18 | 6 Normalization → future | Hold the design constant and efficiency never stalled: +1.8%/yr for 50 years, 38–43 by 2045 | fig42 |
| 19 | 6 by class | Every class of vehicle improves on the same clock: 1.8–2.4% a year, normalized | fig43 |
| 20 | 7 Final: limitations | Limitations, stated plainly | fig7 |
| 21 | 7 Final: close | Predict the vehicle, predict the wallet, predict the fleet | dark |
| 22 | 8 Data links | Every dataset, where it came from, and what it fed | table |
| 23 | 9 Backup | Acronyms and terms | table |
| 24 | 9 Backup | The relationship survives every specification we tried | specs table |
| 25 | 9 Backup | Electrics obey their own physics: weight elasticity −1.05, HP ≈ 0 | table |
| 26 | 9 Backup | Footprint was tested and dropped: size travels with weight | fig9 |
| 27 | 9 Backup | Combustion alone kept the same clock: +1.9%/yr with electrics removed | fig45 |
| 28 | 9 Backup | The 2023 Car SUV spike was the Model Y, and it vanishes without electrics | fig46 |
| 29 | 9 Backup | The three eras were found by algorithm, not by eye | fig16 |
| 30 | 9 Backup | We audited our own story: gas prices explain almost none of the mix shift | fig19 |
| 31 | 9 Backup | Buyers systematically choose better MPG than the catalog median | fig17 |
| 32 | 9 Backup | Sticker history: the era when electric meant expensive | fig41 |
| 33 | 9 Backup | Driving on electrons has cost half as much for a decade | fig33 |
| 34 | 9 Backup | Electrics ride the same productivity clock | fig44 |

Consistency rule (from the presenter's review): BEVs are IN every core
slide — the equation, the scatters, the fit, the normalization (fig42/43
fold BEV MPGe in). Ex-BEV demonstrations live only in backup (27, 28).

Timing: 22 core slides in 25 minutes ≈ 65 s/slide. Slides 2–7 are
context and should run ~40 s each; spend the time on 12–18 (equation,
results, normalization). If short on time, slide 7 (S-curves) and slide
15 (merged dummy) are the first to cut; both survive as Q&A answers.
Grading note: read titles 2→21 aloud as a paragraph to test the
through-line.

## 5. Speaker notes

Every slide's notes are a narration voice track written to be read aloud,
followed by IF ASKED blocks with prepared answers: 2-cycle vs 5-cycle,
the two datasets, the join rates, why logs, HC1, what ε is, how F reaches
6,732, why the combustion-only R² is lower, studentized residuals, what
"the elasticities we estimated" means, why 2024 as the base year, what
the CI band is, whether the productivity line is just electrification,
whether one equation can serve both powertrains.

## 6. The forward thesis (close talk track)

Once MPG is predictable from design, fleet MPG becomes predictable from
the *mix* of designs sold — so shifts in consumer buying (toward trucks,
toward hybrids, toward EVs) translate mechanically into national fuel
economy and fuel spending. The prediction equation is the hinge between
engineering choices and consumer outcomes, and the normalization it
enables shows the engineering side has compounded at 1.8%/yr for fifty
years without a pause.
