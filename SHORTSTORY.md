# SHORTSTORY.md — The MPG Prediction Deck (14 slides)

The focused companion to STORY.md. One relationship, one equation, one
deck: predicting a vehicle's fuel economy from its physical design, and
what that prediction unlocks for understanding consumer cost, buying
patterns, and fuel-economy trends. Deck file: `MPG Prediction Deck.pptx`.

---

## 0. Terminology, stated once and correctly

**MPG is the DEPENDENT variable** (the response, y — the thing we
predict). Weight, horsepower, footprint, and hybrid status are the
**INDEPENDENT variables** (the predictors, x). The assignment requires one
dependent variable and at least three independent variables; this model
has one and four.

## 1. The equation (the deck's center)

    ln(MPG) = 8.78 − 0.304·ln(weight) − 0.483·ln(HP) − 0.0022·footprint + 0.207·hybrid

- **DV**: ln of EPA unadjusted 2-cycle combined MPG, one row per MY2024
  combustion model type (a single consistent test basis; EVs excluded
  because MPGe is a different physical quantity, modeled separately).
- **IVs**: ln(CAFE inertia weight, lbs), ln(rated horsepower), footprint
  (sq ft), hybrid indicator.
- **Fit**: OLS with HC1 heteroskedasticity-robust standard errors.
- **R² = 0.846** (adjusted 0.845), F(4, 1020) = 1,401, every predictor
  p < 0.001, n = 1,025 → 205 observations per parameter (10:1 rule
  cleared 20×). VIFs ≤ 3.4 (mild collinearity, no destabilization).

Why log-log: coefficients read as **elasticities** — a 10% increase in
horsepower costs 4.8% in fuel economy; 10% more weight costs 3.0%; a
hybrid powertrain buys ~23% at the same weight, power, and size.

Derivation story (slide 7): physics motivates the form (fuel burn scales
multiplicatively with mass and power demand), the log transform makes the
multiplicative relationship linear, OLS estimates it, robust errors guard
against heteroskedasticity across vehicle classes.

Sources: `19_final_model.py`, `reports/19_final_model.md`,
`outputs/final_model.json`. Data: EPA MY2024 compliance files (fuel
economy + footprint), joined 100% at carline level (`my2024_config.csv`).

## 2. The adjacent elements (why anyone cares)

Money is the through-line: consumers do not buy MPG, they buy annual cost.

- **Energy cost per mile** (fig33): gasoline $0.164/mi vs BEV $0.067 —
  $2,463 vs $1,007 per 15k-mile year at 2024 prices.
- **Price-shock exposure** (fig36): observed 2011–2026 prices swing a
  gasoline driver's annual bill by $1,394; a BEV driver's by $370.
- **Acquisition cost** (fig37, KBB July 2026): industry ATP $49,855; EV
  premium $6,477 → energy savings alone repay it in ~4.5 years.
- **Historical stickers** (fig41, CarAPI 2015–2020): the era when
  electric meant expensive (BEV median to $60k while hybrids sat at
  $24–39k).
- **The 50-year backdrop** (fig1): MPG 13.1 → 22.0 → 19.3 → 27.2; the
  1987–2004 trough is where efficiency gains were spent on weight and
  power — precisely the tradeoffs the equation prices (fig22: ton-MPG
  never stalled, +0.25/yr through the trough).
- **Lab vs road honesty** (fig7): the model's DV is the 2-cycle lab
  value, which runs ~31% above real-world by 2024 — predictions are of
  the consistent lab measure, not window stickers.

## 3. Robustness (slide 11)

| Spec | R² | Notes |
|---|---|---|
| Main log-log, MY2024 | 0.846 | the headline |
| Linear DV | 0.804 | conclusions unchanged |
| Drop footprint | ~0.846 | collinear term costs nothing |
| Catalog model, 2000+ | 0.777 | n = 30,659, different dataset & DV basis |
| Catalog model, 2020+ | 0.710 | displacement variance compressed by downsizing |
| BEV MPGe physics, MY2024 | 0.708 | n = 153; weight elasticity −0.97 |

The relationship is not an artifact of one year, one dataset, or one
specification.

## 4. The 14 slides

| # | Slide | Content | Visual |
|---|---|---|---|
| 1 | Title (dark) | "Predicting MPG" + BLUF: four numbers explain 85% | big stat |
| 2 | Why MPG matters | fuel cost callouts: $2,463 vs $1,007/yr; $49,855 ATP | stat callouts |
| 3 | 50 years of MPG | the three-acts arc | fig1 |
| 4 | Question & hypothesis | DV/IV definitions, expected signs | table |
| 5 | Data | EPA MY2024 compliance files, n = 1,025, descriptives | table |
| 6 | The raw relationship | size vs economy, volume-weighted | fig9 |
| 7 | Deriving the model | equation, why log-log, OLS + HC1 | equation |
| 8 | Results | coefficients, R² = 0.846, F, VIF | table + callout |
| 9 | The proof | predicted vs actual | fig31 |
| 10 | What it means | elasticities; the allocation story | fig22 |
| 11 | Robustness | six specs, eras, BEV companion | table |
| 12 | MPG → money | payback math, price-shock insurance | fig36 or fig37 |
| 13 | Limitations | cross-sectional; lab-vs-road; EVs separate | fig7 |
| 14 | Conclusion (dark) | predict MPG → trends → consumer behavior | recap stats |

Timing for 20 minutes: ~85 s/slide; spend 8 minutes on slides 7–10 (the
equation block), keep 2–3 for questions off slide 14.

## 5. The forward thesis (slide 14 talk track)

Once MPG is predictable from design, fleet MPG becomes predictable from
the *mix* of designs sold — so shifts in consumer buying (toward trucks,
toward hybrids, toward EVs) translate mechanically into national fuel
economy and fuel spending. The prediction equation is the hinge between
engineering choices and consumer outcomes: fig2/fig14 (the truck
takeover), fig33/fig36/fig37 (the cost stack), and fig18 (technology
S-curves) are all downstream stories of the same relationship.
