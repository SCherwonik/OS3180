# COURSE_TIEINS.md — Where the Semester's Material Lives in This Project

Mapping of the Stats 1 course material (Weeks 1–6 + Chapters 9–11) to the
artifacts we built, with the figure/slide/report where each concept
appears and a suggested spoken line. Use during the briefing to
name-drop course vocabulary at the moment we used it.

## Week 1 — Descriptive Statistics

| Course concept | Where we used it | Spoken tie-in |
|---|---|---|
| Population vs. sample | The MY2024 compliance data is a **census, not a sample**: every model type legally filed (n = 1,025) | "Our 'sample' is actually the population of filed 2024 model types — which is why the 10:1 rule is cleared 205-fold" |
| Mean / median / mode | Descriptive table, deck slide 4 (min/median/max of DV and IVs); medians used throughout the powertrain charts | "Medians, not means, for the cost charts — trim-count skew makes means lie" |
| Variance, SD, **coefficient of variation** | fig21/fig36: cross-sectional SD of manufacturer MPG; **CV of gas (0.20) vs electricity (0.14) prices** drives the price-shock slide | "Gasoline's price CV is 0.20, electricity's 0.14 — variability, exactly as defined in Week 1, is the whole argument" |
| Percentiles / quartiles | IQR bands in powertrain cost tables; event-study percentile ranks (1979 = 100th, 2008 = 52nd) | "The 1979 shock sits at the 100th percentile of placebo windows" |
| Scatterplots, histograms, ECDF-style displays | fig9, fig31 (scatter); fig23 (histograms); fig17 (ECDFs) | — |

## Week 2 — Probability

| Course concept | Where we used it | Spoken tie-in |
|---|---|---|
| Relative-frequency probability | Production shares as probabilities throughout EPA Trends | — |
| **Conditional probability** | The Model Y spike decomposition: **P(BEV given Car SUV class) = 35.7% in 2023** vs P(BEV) = 7.2% overall | "The spike is a conditional probability story: BEV share conditional on class is five times the marginal share" |
| Storytelling with data (explicit course topic) | The whole 9-beat deck arc; claim-based titles; BLUF slide | "We structured the brief as beginning-middle-end per the Week 2 storytelling material" |

## Week 3 — Discrete Distributions

| Course concept | Where we used it | Spoken tie-in |
|---|---|---|
| **Poisson distribution** | fig20: fatalities modeled as Poisson counts with a log-VMT exposure offset (stage 10 GLM) | "Traffic deaths are counts, so we used the Week 3 Poisson — with an exposure offset for miles driven" |
| Expected value & variance of a discrete RV | Overdispersion test: Poisson requires variance = mean; ours had **dispersion φ = 115**, so quasi-Poisson scaling | "The Poisson's defining property — variance equals mean — failed by a factor of 115, which is itself the finding that forced robust scaling" |

## Week 4 — Continuous Distributions

| Course concept | Where we used it |
|---|---|
| PDFs / areas as probability | ECDF comparisons (fig17), KS statistics on distribution shapes (D = 0.211 offered-vs-bought; D = 0.833 bunching) |
| Distribution shift formalized | Wasserstein distance 3.06 MPG between offered and bought distributions |

## Week 5 — Sampling, Estimation, Confidence Intervals

| Course concept | Where we used it | Spoken tie-in |
|---|---|---|
| Point estimates + **confidence intervals** | Every coefficient table; fig29's whiskers; bootstrap CIs on S-curve parameters (fig18); the slope-CI band on the fig42 projection | "Filled marker = the CI excludes zero — one of six does" |
| **Z-scores + Empirical Rule** | fig20: the 2021 fatality excess is **z = 6.0** even after dispersion scaling | "Week 5's empirical rule says 99.7% of outcomes live within three sigma; this sits at six" |
| Central Limit Theorem | Grain lesson, figs 38 vs 39: aggregating configurations to yearly medians collapses the noise (R² 0.06 → 0.88) | "Same data, coarser sampling unit, tighter distribution — the CLT's logic on display" |
| Margin of error honesty | fig42/45 caveats: the CI band carries fit uncertainty only; scenario uncertainty dominates | — |

## Week 6 — Hypothesis Testing

| Course concept | Where we used it | Spoken tie-in |
|---|---|---|
| H0 / Ha formulation | Deck slide 3: expected signs stated before fitting = four directional alternatives | "Signs were our alternative hypotheses, committed before estimation" |
| Test statistics, p-values, rejection at α = 0.05 | Every model table (t up to 43.0); Chow F-tests at the changepoints; KS, Brown–Forsythe | — |
| **Type II error / power** | Insurance injury effects: all negative, none significant — presented as "consistent but **underpowered**", an explicit beta discussion | "We reported a possible Type II error rather than claiming a null result" |
| One- vs two-tailed | Two-tailed throughout (conservative given directional priors) | — |

## Chapters 9–11 — Two-Sample Inference and ANOVA

| Course concept | Where we used it | Spoken tie-in |
|---|---|---|
| Two-sample comparisons | Freeze-era vs footprint-era CAFE gap distributions (two-sample KS, p ≈ 5e-54, fig23); tight-vs-recent variance windows | — |
| **F-statistic** | The regression's global **F(4, 1020) = 1,401** is the ANOVA decomposition of the model: between-model vs residual variation | "The F on the results slide is Chapter 10's machinery — explained variation over unexplained, exactly SST vs SSE" |
| **ANOVA via dummy variables** | Insurance model's size/body-group dummies and the class breakouts are regression's equivalent of one-way ANOVA treatments (regression with factor dummies ≡ ANOVA) | "Our class dummies are a one-way ANOVA in regression clothing" |
| Variance-equality testing (ANOVA's assumption toolkit) | **Brown–Forsythe** W = on the manufacturer re-divergence (p = 0.042, validation E) | "Levene-family test, from the ANOVA toolkit, on whether the field really re-diverged" |
| Multiple comparisons awareness | fig29 shows six simultaneous tests; only one survives — noted without hiding the other five | "With six tests at α = .05 you expect ~0.3 false positives; our one hit is at p = 0.003, robust to any Bonferroni-style correction" |

## Rubric lines, already covered

- Background → slides 2, 9 - Data sources + descriptives → slide 4 +
  DATA_SOURCES.md - BLUF → title + close - Hypothesis w/ DV & IVs →
  slide 3 - Statistical analysis + significance → slides 6–8 -
  Results/conclusions/call-to-action → slides 16, 18 - Limitations →
  slide 17 - "Model coefficients, R², standard error" displays → slide 7
  table - Pre-attentive attributes/Gestalt → consistent entity colors,
  claim titles, one-highlight-per-chart design system.

## Three cheap deck tweaks if desired (not yet applied)

1. Slide 3: add explicit "H0: βi = 0 / Ha: βi < 0 (hybrid: > 0)" notation.
2. Slide 8 notes: say "F is the ANOVA decomposition" aloud.
3. Backup fig20 (if re-added): cite the Empirical Rule when saying z = 6.
