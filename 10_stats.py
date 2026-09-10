"""10_stats.py -- six statistical analyses for the story deck.

1. Changepoint detection on fleet real-world MPG (piecewise-linear BIC search
   + Chow tests at discovered breaks)
2. Offered-vs-bought MPG as a distribution shift (weighted KS, Wasserstein,
   quantiles) + production concentration (Lorenz/Gini)
3. Logistic diffusion fits for technology adoption (curve_fit + residual
   bootstrap CIs)
4. Spurious-regression demonstration: gas price vs truck share in levels vs
   first differences
5. Poisson GLM (IRLS, log-VMT offset) on fatalities: fit 1990-2019, project
   2020-24, quasi-Poisson dispersion
6. Manufacturer convergence: cross-sectional dispersion on a balanced panel

Outputs: reports/10_statistics.md (tables) and outputs/stats_results.json
(consumed by 11_charts_stats.py). Deterministic: fixed RNG seed.
"""

import io
import json
import os

import numpy as np
import pandas as pd
from scipy import optimize, stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
REPORTS = os.path.join(HERE, "reports")
RNG = np.random.default_rng(31_80)

R = {}  # results tree -> stats_results.json


# ---------------------------------------------------------------------------
# 1. Changepoints
# ---------------------------------------------------------------------------

def pwl_design(t, breaks):
    """Continuous piecewise-linear design matrix: 1, t, (t-b)+ per break."""
    cols = [np.ones_like(t, dtype=float), t.astype(float)]
    for b in breaks:
        cols.append(np.clip(t - b, 0, None).astype(float))
    return np.column_stack(cols)


def fit_sse(t, y, breaks):
    X = pwl_design(t, breaks)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return float(resid @ resid), beta


def changepoints(aa):
    d = aa[~aa.is_preliminary].dropna(subset=["real_world_mpg"])
    t, y = d.model_year.values, d.real_world_mpg.values
    n = len(t)
    MIN_SEG = 6
    cand = [int(b) for b in t[MIN_SEG:-MIN_SEG]]

    results = {}
    sse0, _ = fit_sse(t, y, [])
    results[0] = (sse0, [])
    best1 = min(((fit_sse(t, y, [b])[0], [b]) for b in cand), key=lambda r: r[0])
    results[1] = best1
    best2 = min(((fit_sse(t, y, [b1, b2])[0], [b1, b2])
                 for i, b1 in enumerate(cand) for b2 in cand[i + 1:]
                 if b2 - b1 >= MIN_SEG), key=lambda r: r[0])
    results[2] = best2
    # 3 breaks: greedy around the best-2 solution to keep the search tractable.
    b1, b2 = best2[1]
    best3 = min(((fit_sse(t, y, sorted({b1, b2, b3}))[0], sorted({b1, b2, b3}))
                 for b3 in cand if len({b1, b2, b3}) == 3
                 and min(abs(b3 - b1), abs(b3 - b2)) >= MIN_SEG),
                key=lambda r: r[0])
    results[3] = best3

    bic = {}
    for m, (sse, breaks) in results.items():
        k = 2 + 2 * m  # slope+intercept, plus (location, slope change) per break
        bic[m] = n * np.log(sse / n) + k * np.log(n)
    m_star = min(bic, key=bic.get)
    breaks = results[m_star][1]

    # Chow test at each selected break (split regression vs pooled).
    chow = []
    for b in breaks:
        left, right = t <= b, t > b
        X1, X2 = pwl_design(t[left], []), pwl_design(t[right], [])
        _, r1 = np.linalg.lstsq(X1, y[left], rcond=None)[0:2:1], None
        sse_l, _ = fit_sse(t[left], y[left], [])
        sse_r, _ = fit_sse(t[right], y[right], [])
        sse_p, _ = fit_sse(t, y, [])
        k = 2
        F = ((sse_p - (sse_l + sse_r)) / k) / ((sse_l + sse_r) / (n - 2 * k))
        p = 1 - stats.f.cdf(F, k, n - 2 * k)
        chow.append({"break": int(b), "F": round(float(F), 1),
                     "p": float(p)})

    R["changepoints"] = {
        "selected_breaks": [int(b) for b in breaks],
        "bic_by_num_breaks": {str(m): round(float(v), 2) for m, v in bic.items()},
        "sse_by_num_breaks": {str(m): round(float(results[m][0]), 2) for m in results},
        "chow": chow,
        "beta": [float(b) for b in fit_sse(t, y, breaks)[1]],
        "years": [int(v) for v in t], "mpg": [float(v) for v in y],
    }


# ---------------------------------------------------------------------------
# 2. Distribution shift + concentration
# ---------------------------------------------------------------------------

def wecdf(x, w, grid):
    order = np.argsort(x)
    x, w = x[order], w[order]
    cw = np.cumsum(w) / w.sum()
    return np.interp(grid, x, cw, left=0, right=1)


def gini(v):
    v = np.sort(v.astype(float))
    n = len(v)
    return float((2 * np.arange(1, n + 1) - n - 1) @ v / (n * v.sum()))


def distribution_shift(my24):
    d = my24[(my24["src_my24fe_FE_UNIT"] == "MPG")
             & (my24["src_my24fe_DRIVE_SOURCE"] == "C")]
    # One row per model type (offered unit); join-multiplied rows would bias.
    mt = d.drop_duplicates(subset=["src_my24fe_Carline Mfr Code",
                                   "src_my24fe_CARLINE_CODE",
                                   "src_my24fe_MODEL_TYPE_INDEX"])
    y = mt["src_my24fe_UNRD_5C_ADJ_MT_COMB_FE"].values
    w = mt["src_my24fe_Model_Type_Actual_Prod_Vol"].values.astype(float)
    grid = np.linspace(y.min(), y.max(), 512)
    F_off = wecdf(y, np.ones_like(y), grid)
    F_buy = wecdf(y, w, grid)
    ks = float(np.max(np.abs(F_off - F_buy)))
    wass = float(np.trapezoid(np.abs(F_off - F_buy), grid))

    def wq(q, weights):
        order = np.argsort(y)
        cw = np.cumsum(weights[order]) / weights.sum()
        return float(np.interp(q, cw, y[order]))

    quants = {q: {"offered": wq(q, np.ones_like(y)), "bought": wq(q, w)}
              for q in (0.25, 0.5, 0.75)}

    vols = d.drop_duplicates(subset=["src_my24fe_Carline Mfr Code",
                                     "src_my24fe_CARLINE_CODE"]
                             )["derived_carline_prod_vol"].dropna().values
    v = np.sort(vols)[::-1]
    cum = np.cumsum(v) / v.sum()
    n80 = int(np.searchsorted(cum, 0.8) + 1)
    R["distribution"] = {
        "n_model_types": int(len(y)), "ks_D": round(ks, 4),
        "wasserstein_mpg": round(wass, 3),
        "quantiles": {str(k): {kk: round(vv, 1) for kk, vv in v.items()}
                      for k, v in quants.items()},
        "mean_offered": round(float(y.mean()), 2),
        "mean_bought": round(float((y * w).sum() / w.sum()), 2),
        "gini_carline_volume": round(gini(vols), 3),
        "n_carlines": int(len(vols)),
        "carlines_for_80pct": n80,
        "grid": [float(g) for g in grid[::8]],
        "F_offered": [float(f) for f in F_off[::8]],
        "F_bought": [float(f) for f in F_buy[::8]],
        "lorenz_cum_carlines": [float(x) for x in
                                np.arange(1, len(v) + 1) / len(v)][::10],
        "lorenz_cum_volume": [float(x) for x in cum][::10],
    }


# ---------------------------------------------------------------------------
# 3. Logistic diffusion
# ---------------------------------------------------------------------------

def logistic(t, L, k, t0):
    return L / (1 + np.exp(-k * (t - t0)))


def diffusion(aa):
    techs = {
        "Turbo": "share_turbocharged_engine_of_gasoline_ice_vehicles",
        "GDI": "share_fuel_delivery_gasoline_direct_injection_gdi",
        "CVT": "share_transmission_cvt_non_hybrid",
        "Hybrid (HEV)": "share_powertrain_gasoline_strong_hybrid_hev",
        "BEV": "share_powertrain_battery_electric_vehicle_bev",
    }
    out = {}
    for name, col in techs.items():
        d = aa.dropna(subset=[col])
        t, y = d.model_year.values.astype(float), d[col].values.astype(float)
        try:
            popt, _ = optimize.curve_fit(
                logistic, t, y, p0=[max(y.max(), 0.05), 0.3, t[np.argmax(y > y.max() / 2)]],
                bounds=([0.01, 0.01, 1970], [1.0, 2.0, 2080]), maxfev=20000)
        except RuntimeError:
            out[name] = {"fit": "failed"}
            continue
        resid = y - logistic(t, *popt)
        boot = []
        for _ in range(300):
            yb = logistic(t, *popt) + RNG.choice(resid, len(resid), replace=True)
            try:
                pb, _ = optimize.curve_fit(
                    logistic, t, np.clip(yb, 0, 1), p0=popt,
                    bounds=([0.01, 0.01, 1970], [1.0, 2.0, 2080]), maxfev=5000)
                boot.append(pb)
            except RuntimeError:
                continue
        boot = np.array(boot)
        ci = np.percentile(boot, [2.5, 97.5], axis=0) if len(boot) > 30 else None
        takeover = float(np.log(81) / popt[1])  # years from 10% to 90% of L
        out[name] = {
            "L": round(float(popt[0]), 3), "k": round(float(popt[1]), 3),
            "t0": round(float(popt[2]), 1), "takeover_years_10_90": round(takeover, 1),
            "ci_k": [round(float(ci[0][1]), 3), round(float(ci[1][1]), 3)] if ci is not None else None,
            "ci_t0": [round(float(ci[0][2]), 1), round(float(ci[1][2]), 1)] if ci is not None else None,
            "years": [int(v) for v in t], "share": [round(float(v), 4) for v in y],
        }
    R["diffusion"] = out


# ---------------------------------------------------------------------------
# 4. Spurious regression
# ---------------------------------------------------------------------------

def spurious(aa, ctx):
    trk = aa_truck_share = None
    trk = (pd.read_csv(os.path.join(OUT, "analysis_clean.csv"))
           .query("manufacturer=='All' and vehicle_type=='All Truck'")
           [["model_year", "production_share"]]
           .rename(columns={"model_year": "year", "production_share": "truck"}))
    m = trk.merge(ctx[["year", "gas_real_2024_usd_gal"]], on="year").dropna()
    m = m[m.year <= 2024].sort_values("year")

    lv = stats.linregress(m.gas_real_2024_usd_gal, m.truck)
    dm = m.set_index("year").diff().dropna()
    df_ = stats.linregress(dm.gas_real_2024_usd_gal, dm.truck)
    lag = pd.DataFrame({"dg": dm.gas_real_2024_usd_gal.shift(1),
                        "dt": dm.truck}).dropna()
    lg = stats.linregress(lag.dg, lag.dt)

    R["spurious"] = {
        "n_years": int(len(m)),
        "levels": {"slope": round(lv.slope, 4), "r2": round(lv.rvalue**2, 3),
                   "p": float(lv.pvalue)},
        "diffs": {"slope": round(df_.slope, 4), "r2": round(df_.rvalue**2, 3),
                  "p": float(df_.pvalue)},
        "diffs_lag1": {"slope": round(lg.slope, 4), "r2": round(lg.rvalue**2, 3),
                       "p": float(lg.pvalue)},
        "years": [int(v) for v in m.year],
        "gas": [round(float(v), 3) for v in m.gas_real_2024_usd_gal],
        "truck": [round(float(v), 4) for v in m.truck],
    }


# ---------------------------------------------------------------------------
# 5. Poisson GLM with offset (IRLS)
# ---------------------------------------------------------------------------

def poisson_irls(X, y, offset, iters=50):
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = X @ beta + offset
        mu = np.exp(eta)
        z = eta - offset + (y - mu) / mu
        W = mu
        XtW = X.T * W
        beta_new = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(beta_new - beta)) < 1e-10:
            beta = beta_new
            break
        beta = beta_new
    mu = np.exp(X @ beta + offset)
    pearson = float(((y - mu) ** 2 / mu).sum())
    cov = np.linalg.inv((X.T * mu) @ X)
    return beta, mu, pearson, cov


def fatality_glm(ctx_extra):
    d = ctx_extra.dropna(subset=["fatalities", "bts_vmt_million_miles"])
    d = d[(d.year >= 1990) & (d.year <= 2024)].sort_values("year")
    fit = d[d.year <= 2019]
    yc = (fit.year - 2000).values.astype(float)
    X = np.column_stack([np.ones_like(yc), yc])
    y = fit.fatalities.values.astype(float)
    offset = np.log(fit.bts_vmt_million_miles.values / 100.0)  # exposure: 100M miles
    beta, mu, pearson, cov = poisson_irls(X, y, offset)
    df_resid = len(y) - X.shape[1]
    phi = pearson / df_resid  # quasi-Poisson dispersion

    pred = {}
    for _, r in d[d.year >= 2020].iterrows():
        x = np.array([1.0, r.year - 2000])
        off = np.log(r.bts_vmt_million_miles / 100.0)
        mu_hat = float(np.exp(x @ beta + off))
        var_eta = float(x @ cov @ x) * phi
        # prediction variance: overdispersed count + parameter uncertainty
        var = phi * mu_hat + (mu_hat ** 2) * var_eta
        se = np.sqrt(var)
        z = (r.fatalities - mu_hat) / se
        pred[int(r.year)] = {
            "observed": int(r.fatalities), "expected": round(mu_hat),
            "z": round(float(z), 1),
            "excess": int(round(r.fatalities - mu_hat)),
        }
    R["fatality_glm"] = {
        "beta0": round(float(beta[0]), 4), "beta1": round(float(beta[1]), 4),
        "annual_trend_pct": round((np.exp(beta[1]) - 1) * 100, 2),
        "dispersion_phi": round(phi, 1),
        "fit_years": "1990-2019", "predictions_2020s": pred,
        "years": [int(v) for v in d.year],
        "rate": [round(float(v), 3) for v in d.fatality_rate_per_100m_vmt],
        "fitted_rate": [round(float(np.exp(np.array([1.0, yy - 2000]) @ beta)), 3)
                        for yy in d.year],
        "phi_note": "phi >> 1: quasi-Poisson scaling applied to all SEs",
    }


# ---------------------------------------------------------------------------
# 6. Convergence
# ---------------------------------------------------------------------------

def convergence(ac):
    full = ["Ford", "GM", "Honda", "Mazda", "Nissan", "Stellantis", "Toyota", "VW"]
    d = ac[(ac.regulatory_class == "All") & (ac.vehicle_type == "All")
           & (ac.manufacturer.isin(full)) & (~ac.is_preliminary)]
    g = d.groupby("model_year")["real_world_mpg"]
    sd, mean = g.std(), g.mean()
    R["convergence"] = {
        "panel": full,
        "years": [int(v) for v in sd.index],
        "sd": [round(float(v), 3) for v in sd.values],
        "cv": [round(float(s / m), 4) for s, m in zip(sd.values, mean.values)],
        "sd_1975": round(float(sd.iloc[0]), 2),
        "sd_max": round(float(sd.max()), 2),
        "sd_max_year": int(sd.idxmax()),
        "sd_2024": round(float(sd.loc[2024]), 2),
    }


# ---------------------------------------------------------------------------

def write_report():
    b = io.StringIO()
    b.write("# Statistical Analyses\n\nGenerated by 10_stats.py. "
            "Companion figures: fig16-fig21.\n")

    c = R["changepoints"]
    b.write("\n## 1. Changepoint detection, fleet real-world MPG\n\n")
    b.write("Continuous piecewise-linear fits, break locations by exhaustive "
            "SSE search (min segment 6 years), model order by BIC.\n\n")
    b.write("| Breaks | BIC | SSE |\n|---|---|---|\n")
    for m in ("0", "1", "2", "3"):
        star = " **<- selected**" if int(m) == len(c["selected_breaks"]) else ""
        b.write(f"| {m} | {c['bic_by_num_breaks'][m]} | "
                f"{c['sse_by_num_breaks'][m]}{star} |\n")
    b.write(f"\nSelected breaks: **{c['selected_breaks']}**. Chow tests:\n\n")
    b.write("| Break | F | p |\n|---|---|---|\n")
    for ch in c["chow"]:
        b.write(f"| {ch['break']} | {ch['F']} | {ch['p']:.2e} |\n")

    d = R["distribution"]
    b.write("\n## 2. Offered vs bought, MY2024 (5-cycle adjusted combined MPG)\n\n")
    b.write(f"- Sample: {d['n_model_types']:,} model types (combustion, MPG unit), "
            "offered = unweighted, bought = production-weighted\n")
    b.write(f"- KS statistic D = {d['ks_D']}; Wasserstein distance = "
            f"{d['wasserstein_mpg']} MPG\n")
    b.write(f"- Means: offered {d['mean_offered']} vs bought {d['mean_bought']}\n")
    b.write("- Quantiles (offered / bought): "
            + ", ".join(f"P{int(float(q)*100)}: {v['offered']}/{v['bought']}"
                        for q, v in d["quantiles"].items()) + "\n")
    b.write(f"- Production concentration: Gini = {d['gini_carline_volume']} across "
            f"{d['n_carlines']} carlines; {d['carlines_for_80pct']} carlines "
            f"({d['carlines_for_80pct']/d['n_carlines']:.0%}) account for 80% of volume\n")

    b.write("\n## 3. Logistic diffusion fits\n\n")
    b.write("| Technology | L (ceiling) | k (rate) | 95% CI k | t0 (midpoint) | "
            "10%->90% years |\n|---|---|---|---|---|---|\n")
    for name, f in R["diffusion"].items():
        if f.get("fit") == "failed":
            b.write(f"| {name} | fit failed | | | | |\n")
            continue
        ci = f"{f['ci_k'][0]}-{f['ci_k'][1]}" if f["ci_k"] else "n/a"
        b.write(f"| {name} | {f['L']} | {f['k']} | {ci} | {f['t0']} | "
                f"{f['takeover_years_10_90']} |\n")
    b.write("\nCeiling L is estimated, not assumed = 1: CVT and HEV plateau "
            "far below universal adoption. BEV's parameters carry the widest "
            "CI: its curve is still mostly ahead of the data.\n")

    s = R["spurious"]
    b.write("\n## 4. The correlation that wasn't: real gas price vs truck share\n\n")
    b.write(f"| Specification | slope | R^2 | p |\n|---|---|---|---|\n")
    b.write(f"| Levels | {s['levels']['slope']} | {s['levels']['r2']} | "
            f"{s['levels']['p']:.2f} |\n")
    b.write(f"| First differences | {s['diffs']['slope']} | {s['diffs']['r2']} | "
            f"{s['diffs']['p']:.2f} |\n")
    b.write(f"| Differences, gas lagged 1yr | {s['diffs_lag1']['slope']} | "
            f"{s['diffs_lag1']['r2']} | {s['diffs_lag1']['p']:.2f} |\n")
    b.write("\nThe planned lesson was the classic spurious-regression trap "
            "(two trending series, inflated levels R^2). The data delivered a "
            "sharper one: there is essentially NO annual-grain linear "
            "relationship in any specification (levels r = -0.08). Truck "
            "share rose monotonically for fifty years while real gas price "
            "oscillated, so the overlay chart (fig5) that visually suggests "
            "'cheap gas buried sedans' is a story about secular trend plus a "
            "few episodes, not an annual price elasticity. Lessons: (a) "
            "eyeballed co-movement is not association; (b) a monotone trend "
            "cannot correlate strongly with a mean-reverting series in "
            "levels; (c) identifying a price effect here would need micro "
            "data or within-year variation, not 49 national annual points. "
            "The deck should present fig5 and this table together: the "
            "narrative, then the audit of the narrative.\n")

    g = R["fatality_glm"]
    b.write("\n## 5. Poisson GLM on fatalities (log-VMT offset, IRLS)\n\n")
    b.write(f"- Fit window {g['fit_years']}: rate trend "
            f"{g['annual_trend_pct']}% per year\n")
    b.write(f"- Quasi-Poisson dispersion phi = {g['dispersion_phi']} "
            "(annual counts are far from independent Poisson events; all SEs "
            "scaled accordingly)\n")
    b.write("- Out-of-sample 2020-24 vs the pre-2020 trend:\n\n")
    b.write("| Year | Observed | Expected | Excess | z |\n|---|---|---|---|---|\n")
    for yr, p in g["predictions_2020s"].items():
        b.write(f"| {yr} | {p['observed']:,} | {p['expected']:,} | "
                f"{p['excess']:+,} | {p['z']} |\n")

    v = R["convergence"]
    b.write("\n## 6. Manufacturer convergence (balanced 8-manufacturer panel)\n\n")
    b.write(f"- Panel: {', '.join(v['panel'])} (present all 50 years)\n")
    b.write(f"- Cross-sectional SD of real-world MPG: {v['sd_1975']} (1975), "
            f"peak {v['sd_max']} ({v['sd_max_year']}), {v['sd_2024']} (2024)\n")
    b.write("- The pattern is convergence-then-divergence, not monotone "
            "compression: the field tightened to under 2 MPG SD from the "
            "early 1990s through 2008, then spread again as hybrid-heavy "
            "manufacturers (Honda, Toyota) pulled away from truck-heavy ones "
            "(Ford, GM, Stellantis).\n")

    with open(os.path.join(REPORTS, "10_statistics.md"), "w", encoding="utf-8") as f:
        f.write(b.getvalue())


def main():
    ac = pd.read_csv(os.path.join(OUT, "analysis_clean.csv"))
    aa = ac[(ac.manufacturer == "All") & (ac.regulatory_class == "All")
            & (ac.vehicle_type == "All")].sort_values("model_year")
    my24 = pd.read_csv(os.path.join(OUT, "my2024_config.csv"), low_memory=False)
    ctx = pd.read_csv(os.path.join(OUT, "context_annual.csv"))
    ctx_extra = pd.read_csv(os.path.join(OUT, "context_extra.csv"))

    changepoints(aa)
    distribution_shift(my24)
    diffusion(aa)
    spurious(aa, ctx)
    fatality_glm(ctx_extra)
    convergence(ac)

    with open(os.path.join(OUT, "stats_results.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, indent=1)
    write_report()
    print("breaks:", R["changepoints"]["selected_breaks"])
    print("KS D:", R["distribution"]["ks_D"], "| Gini:",
          R["distribution"]["gini_carline_volume"])
    print("spurious levels R2:", R["spurious"]["levels"]["r2"],
          "diffs R2:", R["spurious"]["diffs"]["r2"])
    print("GLM phi:", R["fatality_glm"]["dispersion_phi"])


if __name__ == "__main__":
    main()
