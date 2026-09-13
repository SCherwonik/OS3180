"""33_pooled_model.py -- one equation for every powertrain, MY2024.

Extends the stage-19 combustion model to battery-electric vehicles so the
deck can use ONE equation throughout. The DV becomes miles per gasoline-
gallon-equivalent of energy: EPA unadjusted 2-cycle combined MPG for
combustion rows and MPGe (miles per 33.7 kWh) for BEV rows -- the same
column in the FE file, same test, same energy basis.

BEVs have no ENG_RATED_HP in the compliance FE file. Rated horsepower is
joined from the EPA MY2024 Test Car List (external/epa_24_testcar_2025-05
.xlsx) through a tiered key: (carline name, test weight) -> carline name ->
(year-agnostic test group, test weight) -> test group. The same procedure
applied to combustion rows, where HP is already known, is reported as the
validation of the key.

Specifications compared (all OLS, HC1 robust SEs):
  A  combustion only, 4 IVs                    (stage 19, reproduced)
  B  pooled, powertrain as one 3-level factor  (gas/diesel | hybrid | BEV)
  C  pooled, single merged "electrified" dummy (hybrid or BEV)
  D  pooled, ordinal electrification 0/1/2
  E  B + BEV x slope interactions               (do the elasticities differ?)

Outputs:
  outputs/my2024_pooled.csv     modeling table incl. HP source tier
  outputs/pooled_model.json     every spec, VIFs, outliers, join stats
  reports/33_pooled_model.md
"""

import hashlib
import io
import json
import os
import re

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
REPORTS = os.path.join(HERE, "reports")
TESTCAR = os.path.join(HERE, "external", "epa_24_testcar_2025-05.xlsx")

P = "src_my24fe_"
KEY = [P + "Carline Mfr Code", P + "CARLINE_CODE", P + "MODEL_TYPE_INDEX"]
COLS = {
    "fe": P + "UNRD_UNADJ_MT_COMB_FE",
    "wt": P + "CAFE Base Level Inertia Weight",
    "hp": P + "ENG_RATED_HP",
    "fp": "src_my24fp_EPA_CALC_ROUNDED_AREA",
    "hy": P + "HYBRID_YN",
    "name": P + "CARLINE_NAME",
    "mfr": P + "Carline Mfr Name",
    "tg": P + "Basic Engine Testgroup",
}


def hc1_ols(X, y, names):
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    n, k = X.shape
    meat = (X * (resid ** 2)[:, None]).T @ X
    cov = (n / (n - k)) * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(cov))
    t = beta / se
    p = 2 * (1 - stats.t.cdf(np.abs(t), n - k))
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot
    adj = 1 - (1 - r2) * (n - 1) / (n - k)
    f_stat = (r2 / (k - 1)) / ((1 - r2) / (n - k))
    f_p = 1 - stats.f.cdf(f_stat, k - 1, n - k)
    hat = np.einsum("ij,jk,ik->i", X, XtX_inv, X)
    s = np.sqrt(ss_res / (n - k))
    return {
        "coef": dict(zip(names, np.round(beta, 4))),
        "se": dict(zip(names, np.round(se, 4))),
        "t": dict(zip(names, np.round(t, 2))),
        "p": dict(zip(names, [float(f"{v:.2e}") for v in p])),
        "r2": round(r2, 4), "adj_r2": round(adj, 4),
        "f": round(float(f_stat), 1), "f_p": float(f"{f_p:.2e}"),
        "n": int(n), "k": int(k), "sse": ss_res, "s": float(s),
        "resid": resid, "fitted": X @ beta, "hat": hat,
    }


def vif(X, names):
    out = {}
    for j in range(1, X.shape[1]):
        others = np.delete(X, j, axis=1)
        b, *_ = np.linalg.lstsq(others, X[:, j], rcond=None)
        r = X[:, j] - others @ b
        r2 = 1 - (r @ r) / (((X[:, j] - X[:, j].mean()) ** 2).sum())
        out[names[j]] = round(1 / (1 - r2), 1)
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def testcar_hp(d, tc, wtcol):
    """Tiered join of Test Car List rated HP onto FE rows. Returns hp, tier."""
    tc = tc[tc["Rated Horsepower"] > 20].copy()
    tc["tg11"] = tc["Actual Tested Testgroup"].astype(str).str[1:]
    tc["nm"] = tc["Represented Test Veh Model"].map(norm)
    tc["etw"] = tc["Equivalent Test Weight (lbs.)"]
    d = d.copy()
    d["tg11"] = d[COLS["tg"]].astype(str).str[1:]
    d["nm"] = d[COLS["name"]].map(norm)
    d["etw"] = d[wtcol]
    tiers = [("name+wt", ["nm", "etw"]), ("name", ["nm"]),
             ("tg+wt", ["tg11", "etw"]), ("tg", ["tg11"])]
    hp = pd.Series(np.nan, index=d.index)
    tier = pd.Series("none", index=d.index)
    for label, keys in tiers:
        g = tc.groupby(keys)["Rated Horsepower"].median().rename("hp_tc")
        cand = d[keys].merge(g, left_on=keys, right_index=True, how="left")["hp_tc"]
        cand.index = d.index
        fill = hp.isna() & cand.notna()
        hp[fill] = cand[fill]
        tier[fill] = label
    return hp, tier


def design(d, spec):
    base = [np.ones(len(d)), np.log(d.wt), np.log(d.hp), d.fp]
    names = ["const", "ln_weight", "ln_hp", "footprint_sqft"]
    if spec == "A":
        return np.column_stack(base + [d.hybrid]), names + ["hybrid"]
    if spec == "B":
        return np.column_stack(base + [d.hybrid, d.bev]), names + ["hybrid", "bev"]
    if spec == "C":
        return (np.column_stack(base + [((d.hybrid + d.bev) > 0).astype(float)]),
                names + ["electrified"])
    if spec == "D":
        return (np.column_stack(base + [d.hybrid + 2 * d.bev]),
                names + ["electrification_0_1_2"])
    if spec == "E":
        return (np.column_stack(base + [d.hybrid, d.bev, d.bev * np.log(d.wt),
                                        d.bev * np.log(d.hp), d.bev * d.fp]),
                names + ["hybrid", "bev", "bev_x_ln_weight", "bev_x_ln_hp",
                         "bev_x_footprint"])
    if spec == "F":  # B without footprint: the final presentation equation
        return (np.column_stack(base[:3] + [d.hybrid, d.bev]),
                names[:3] + ["hybrid", "bev"])
    raise ValueError(spec)


def strip(m):
    return {k: v for k, v in m.items()
            if k not in ("resid", "fitted", "hat", "sse")}


def main():
    m = pd.read_csv(os.path.join(OUT, "my2024_config.csv"), low_memory=False)
    tc = pd.read_excel(TESTCAR)
    md5 = hashlib.md5(open(TESTCAR, "rb").read()).hexdigest()

    # --- combustion rows, exactly as stage 19 -------------------------------
    cb = m[(m[P + "FE_UNIT"] == "MPG") & (m[P + "DRIVE_SOURCE"] == "C")]
    cb = cb.drop_duplicates(subset=KEY)
    cb_hp_tc, cb_tier = testcar_hp(
        cb, tc[tc["Test Fuel Type Description"] != "Electricity"], COLS["wt"])
    ok = cb_hp_tc.notna() & cb[COLS["hp"]].notna()
    rel = ((cb_hp_tc[ok] - cb.loc[ok, COLS["hp"]]).abs()
           / cb.loc[ok, COLS["hp"]])
    join_val = {
        "combustion_rows": int(len(cb)),
        "matched_share": round(float(cb_hp_tc.notna().mean()), 3),
        "within_5pct": round(float((rel <= 0.05).mean()), 3),
        "within_10pct": round(float((rel <= 0.10).mean()), 3),
        "median_rel_diff": round(float(rel.median()), 4),
        "tiers": cb_tier.value_counts().to_dict(),
    }
    cbm = cb[KEY + [COLS[c] for c in ("fe", "wt", "hp", "fp", "hy", "name", "mfr")]].copy()
    cbm.columns = ["mfr_code", "carline_code", "mt_index", "fe", "wt", "hp",
                   "fp", "hy", "name", "mfr"]
    cbm["powertrain"] = np.where(cbm.hy == "Y", "hybrid", "gas_diesel")
    cbm["hp_source"] = "FE file ENG_RATED_HP"

    # --- BEV rows -----------------------------------------------------------
    ev = m[(m[P + "FUEL_USAGE"] == "EL") & (m[P + "FE_UNIT"] == "MPG")
           & (m[P + "DRIVE_SOURCE"] == "E")].drop_duplicates(subset=KEY)
    # Unit check. An unadjusted 2-cycle value can never sit BELOW the same
    # row's 5-cycle label value (the label is the 2-cycle result adjusted
    # downward). Where it does, the MPGe cell is carrying kWh/100 mi, and by
    # definition MPGe = 3370.5 / (kWh per 100 mi) (33.705 kWh per gallon-
    # equivalent). The value is recomputed from the cell itself; EPA's paired
    # KW-HR/100Miles row is reported alongside as the cross-check. Logged.
    kwh = (m[(m[P + "FUEL_USAGE"] == "EL") & (m[P + "FE_UNIT"] == "KW-HR/100Miles")
             & (m[P + "DRIVE_SOURCE"] == "E")]
           .drop_duplicates(subset=KEY)
           .set_index(KEY)[COLS["fe"]].rename("kwh100"))
    ev = ev.merge(kwh, left_on=KEY, right_index=True, how="left").copy()
    label = pd.to_numeric(ev[P + "RND_5C_ADJ_MT_COMB_FE"], errors="coerce")
    bad = label.notna() & (ev[COLS["fe"]] < label)
    ev["mpge_fixed"] = 3370.5 / ev[COLS["fe"]]
    unit_fixes = [{"carline": str(r[COLS["name"]]), "mfr": str(r[COLS["mfr"]]),
                   "mpge_as_filed": round(float(r[COLS["fe"]]), 2),
                   "label_5cycle_mpge": float(r[P + "RND_5C_ADJ_MT_COMB_FE"]),
                   "paired_kwh_row_as_filed": round(float(r["kwh100"]), 2),
                   "mpge_recomputed": round(float(r["mpge_fixed"]), 1)}
                  for _, r in ev[bad].iterrows()]
    ev.loc[bad, COLS["fe"]] = ev.loc[bad, "mpge_fixed"]
    ev_hp, ev_tier = testcar_hp(
        ev, tc[tc["Test Fuel Type Description"] == "Electricity"], COLS["wt"])
    join_ev = {
        "bev_model_types": int(len(ev)),
        "matched": int(ev_hp.notna().sum()),
        "matched_share": round(float(ev_hp.notna().mean()), 3),
        "tiers": ev_tier.value_counts().to_dict(),
        "unmatched_carlines": sorted(
            ev.loc[ev_hp.isna(), COLS["name"]].unique().tolist()),
    }
    evm = ev[KEY + [COLS[c] for c in ("fe", "wt", "fp", "name", "mfr")]].copy()
    evm.columns = ["mfr_code", "carline_code", "mt_index", "fe", "wt", "fp",
                   "name", "mfr"]
    evm["hp"] = ev_hp.values
    evm["hy"] = "N"
    evm["powertrain"] = "bev"
    evm["hp_source"] = "Test Car List: " + ev_tier.values

    pooled = pd.concat([cbm, evm], ignore_index=True)
    pooled = pooled.dropna(subset=["fe", "wt", "hp", "fp"])
    pooled["hybrid"] = (pooled.powertrain == "hybrid").astype(float)
    pooled["bev"] = (pooled.powertrain == "bev").astype(float)
    pooled.to_csv(os.path.join(OUT, "my2024_pooled.csv"), index=False)
    y_all = np.log(pooled.fe.values)
    groups = pooled.powertrain.value_counts().to_dict()

    # --- specifications -----------------------------------------------------
    results, fits = {}, {}
    comb = pooled[pooled.bev == 0]
    for spec in "ABCDEF":
        d = comb if spec == "A" else pooled
        X, names = design(d, spec)
        y = np.log(d.fe.values)
        fit = hc1_ols(X, y, names)
        fits[spec] = (fit, d, names)
        results[spec] = strip(fit)
        results[spec]["vif"] = vif(X, names)
        # mean residual by powertrain: shows where a spec mis-prices a group
        results[spec]["mean_resid_by_powertrain"] = {
            g: round(float(fit["resid"][(d.powertrain == g).values].mean()), 4)
            for g in d.powertrain.unique()}

    # nested F: does B need BEV-specific slopes (E)?
    fb, fe_ = fits["B"][0], fits["E"][0]
    q = fe_["k"] - fb["k"]
    f_int = ((fb["sse"] - fe_["sse"]) / q) / (fe_["sse"] / (fe_["n"] - fe_["k"]))
    p_int = 1 - stats.f.cdf(f_int, q, fe_["n"] - fe_["k"])
    interaction_test = {"F": round(float(f_int), 2), "df": [q, fe_["n"] - fe_["k"]],
                        "p": float(f"{p_int:.2e}")}
    # implied BEV elasticities under E
    eb = fe_["coef"]
    bev_elast = {"ln_weight": round(eb["ln_weight"] + eb["bev_x_ln_weight"], 3),
                 "ln_hp": round(eb["ln_hp"] + eb["bev_x_ln_hp"], 3)}

    # nested F: B vs C (is the 3-level factor worth one extra parameter?)
    fc = fits["C"][0]
    f_bc = ((fc["sse"] - fb["sse"]) / 1) / (fb["sse"] / (fb["n"] - fb["k"]))
    p_bc = 1 - stats.f.cdf(f_bc, 1, fb["n"] - fb["k"])
    factor_test = {"F": round(float(f_bc), 1), "df": [1, fb["n"] - fb["k"]],
                   "p": float(f"{p_bc:.2e}")}

    # nested F: B vs F (does footprint earn its place once BEVs are in?)
    ff = fits["F"][0]
    f_bf = ((ff["sse"] - fb["sse"]) / 1) / (fb["sse"] / (fb["n"] - fb["k"]))
    p_bf = 1 - stats.f.cdf(f_bf, 1, fb["n"] - fb["k"])
    footprint_test = {"F": round(float(f_bf), 2), "df": [1, fb["n"] - fb["k"]],
                      "p": float(f"{p_bf:.3f}")}

    # outliers on F (the final equation): internally studentized residuals
    d = fits["F"][1]
    fb = ff
    r_stud = fb["resid"] / (fb["s"] * np.sqrt(1 - fb["hat"]))
    top = np.argsort(-np.abs(r_stud))[:8]
    outliers = [{
        "carline": str(d.iloc[i]["name"]), "mfr": str(d.iloc[i]["mfr"]),
        "powertrain": str(d.iloc[i].powertrain),
        "actual": round(float(d.iloc[i].fe), 1),
        "predicted": round(float(np.exp(fb["fitted"][i])), 1),
        "studentized_resid": round(float(r_stud[i]), 2),
        "hp": float(d.iloc[i].hp), "wt": float(d.iloc[i].wt),
    } for i in top]
    pred_band = {"s_log": round(fb["s"], 4),
                 "typical_miss_pct": round((np.exp(fb["s"]) - 1) * 100, 1),
                 "band95_factor": round(float(np.exp(1.96 * fb["s"])), 3),
                 "share_inside_95": round(float((np.abs(fb["resid"]) <= 1.96 * fb["s"]).mean()), 3)}

    payload = {
        "testcar_md5": md5, "join_validation_combustion": join_val,
        "join_bev": join_ev, "unit_fixes": unit_fixes,
        "groups": groups, "specs": results,
        "interaction_test_B_vs_E": interaction_test,
        "bev_own_elasticities_under_E": bev_elast,
        "factor_test_C_vs_B": factor_test,
        "footprint_test_F_vs_B": footprint_test,
        "final_spec": "F",
        "final_elasticities": {"weight": abs(float(results["F"]["coef"]["ln_weight"])),
                               "hp": abs(float(results["F"]["coef"]["ln_hp"]))},
        "outliers_F": outliers, "prediction_band_F": pred_band,
        "fitted_F": [round(float(x), 4) for x in fb["fitted"]],
        "actual_F": [round(float(x), 4) for x in np.log(d.fe.values)],
        "powertrain_F": d.powertrain.tolist(),
        "carline_F": d.name.tolist(),
    }
    with open(os.path.join(OUT, "pooled_model.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, default=float)

    # --- report -------------------------------------------------------------
    b = io.StringIO()
    b.write("# One Equation for Every Powertrain (MY2024)\n\n"
            "Generated by 33_pooled_model.py. Extends the stage-19 model to "
            "battery-electric vehicles.\n\n"
            "**DV:** ln(miles per gasoline-gallon-equivalent), unadjusted "
            "2-cycle combined -- MPG for combustion rows, MPGe (miles per "
            "33.7 kWh) for BEV rows. Same FE-file column, same test, same "
            "energy basis.\n\n")
    b.write("## Horsepower for BEVs: the Test Car List join\n\n"
            f"Source: EPA MY2024 Test Car List, `external/epa_24_testcar_"
            f"2025-05.xlsx` (md5 `{md5}`). The compliance FE file leaves "
            "ENG_RATED_HP blank for every BEV row; the Test Car List reports "
            "rated horsepower for every tested vehicle including electrics.\n\n"
            f"- BEV model types: {join_ev['bev_model_types']}; matched "
            f"{join_ev['matched']} ({join_ev['matched_share']:.1%}); tiers "
            f"{join_ev['tiers']}\n- Unmatched carlines (dropped, not imputed): "
            f"{', '.join(join_ev['unmatched_carlines'])}\n"
            f"- Validation on combustion rows (HP known from the FE file): "
            f"matched {join_val['matched_share']:.1%} of "
            f"{join_val['combustion_rows']:,}; joined HP within 5% of filed HP "
            f"for {join_val['within_5pct']:.1%}, within 10% for "
            f"{join_val['within_10pct']:.1%}; median relative difference "
            f"{join_val['median_rel_diff']}. Disagreements come from carline "
            "names that span several engines (the join returns the carline "
            "median); for BEVs the same limitation applies to multi-motor "
            "carlines.\n\n")
    b.write("## Unit check on BEV rows\n\n"
            "An unadjusted 2-cycle value cannot sit below the same row's "
            "5-cycle label value (the label is the 2-cycle result adjusted "
            "downward). BEV rows where the filed MPGe does: "
            f"{len(unit_fixes)}. In those rows the MPGe cell holds kWh/100 mi, "
            "so MPGe is recomputed from the cell as 3370.5 / (kWh/100 mi) "
            "(33.705 kWh per gallon-equivalent). No outside data, no "
            "imputation; EPA's paired kWh row is shown for comparison:\n\n"
            "| carline | mfr | MPGe as filed | 5-cycle label | paired kWh row | MPGe recomputed |\n|---|---|---|---|---|---|\n")
    for u in unit_fixes:
        b.write(f"| {u['carline']} | {u['mfr']} | {u['mpge_as_filed']} | "
                f"{u['label_5cycle_mpge']} | {u['paired_kwh_row_as_filed']} | "
                f"{u['mpge_recomputed']} |\n")
    b.write(f"\n## Sample\n\n{groups} -> n = {len(pooled):,} model types "
            f"(combustion rows identical to stage 19).\n\n")
    b.write("## Specifications\n\n| Spec | n | R^2 | adj R^2 | F | notes |\n"
            "|---|---|---|---|---|---|\n")
    labels = {"A": "combustion only, 4 IVs (stage 19)",
              "B": "pooled, powertrain factor (hybrid, BEV dummies)",
              "C": "pooled, one merged 'electrified' dummy",
              "D": "pooled, ordinal electrification 0/1/2",
              "E": "B + BEV x slope interactions",
              "F": "FINAL: B without footprint"}
    for sp in "ABCDEF":
        r = results[sp]
        b.write(f"| {sp} | {r['n']:,} | {r['r2']} | {r['adj_r2']} | {r['f']:,} "
                f"| {labels[sp]} |\n")
    for sp in "ABCDEF":
        r = results[sp]
        b.write(f"\n### Spec {sp}: {labels[sp]}\n\n| Term | coef | HC1 se | t | p | VIF |\n|---|---|---|---|---|---|\n")
        for nm in r["coef"]:
            b.write(f"| {nm} | {r['coef'][nm]} | {r['se'][nm]} | {r['t'][nm]} | "
                    f"{r['p'][nm]:.1e} | {r['vif'].get(nm, '')} |\n")
        b.write(f"\nMean residual by powertrain: {r['mean_resid_by_powertrain']}\n")
    rb = results["F"]["coef"]
    b.write("\n## Reading the final equation (spec F)\n\n"
            f"- Footprint drops out: in spec B its t = "
            f"{results['B']['t']['footprint_sqft']} (p = "
            f"{results['B']['p']['footprint_sqft']:.2f}); nested F"
            f"{footprint_test['df']} = {footprint_test['F']}, p = "
            f"{footprint_test['p']}. Size travels with weight; once the "
            "weight term is in, footprint adds nothing. Spec F is spec B "
            "without it.\n"
            f"- Weight elasticity {rb['ln_weight']}, HP elasticity {rb['ln_hp']}"
            f" (stage 19 combustion-only: {results['A']['coef']['ln_weight']}, "
            f"{results['A']['coef']['ln_hp']}).\n"
            f"- Hybrid premium exp({rb['hybrid']}) - 1 = "
            f"{(np.exp(rb['hybrid'])-1)*100:.0f}%; BEV premium exp({rb['bev']}) "
            f"- 1 = {(np.exp(rb['bev'])-1)*100:.0f}% at identical weight, "
            "power, footprint -- the energy-conversion advantage of an "
            "electric drivetrain over combustion.\n"
            f"- Factor vs merged dummy (C nested in B): F{factor_test['df']} = "
            f"{factor_test['F']}, p = {factor_test['p']:.1e}. Spec C's mean "
            f"residuals by group ({results['C']['mean_resid_by_powertrain']}) "
            "show why one merged dummy fails: it prices hybrids and BEVs at "
            "one average premium, over-predicting hybrids and under-"
            "predicting BEVs by a wide margin.\n"
            f"- Do BEVs obey different elasticities? B vs E: F{interaction_test['df']} = "
            f"{interaction_test['F']}, p = {interaction_test['p']:.1e}. BEV-own "
            f"elasticities under E: {bev_elast}. \n")
    b.write("\n## Outliers (spec F, internally studentized residuals)\n\n"
            "| carline | mfr | powertrain | actual | predicted | r_stud |\n|---|---|---|---|---|---|\n")
    for o in outliers:
        b.write(f"| {o['carline']} | {o['mfr']} | {o['powertrain']} | {o['actual']} | "
                f"{o['predicted']} | {o['studentized_resid']} |\n")
    b.write(f"\n## Prediction band (spec F)\n\nResidual SD in logs s = "
            f"{pred_band['s_log']} -> a typical miss of "
            f"{pred_band['typical_miss_pct']}%; the 95% band is predicted x/÷ "
            f"{pred_band['band95_factor']} and holds "
            f"{pred_band['share_inside_95']:.1%} of model types (leverage "
            "ignored; max h is tiny at n this size).\n")
    with open(os.path.join(REPORTS, "33_pooled_model.md"), "w", encoding="utf-8") as f:
        f.write(b.getvalue())
    for sp in "ABCDEF":
        r = results[sp]
        print(f"{sp}: n={r['n']} R2={r['r2']} coef={ {k: v for k, v in r['coef'].items() if k != 'const'} }")
    print("interaction B vs E:", interaction_test, "BEV own:", bev_elast)
    print("factor C vs B:", factor_test, "| footprint F vs B:", footprint_test)
    print("F table:", {k: (results['F']['coef'][k], results['F']['se'][k], results['F']['t'][k]) for k in results['F']['coef']}, "VIF", results["F"]["vif"])
    print("join BEV:", join_ev["matched_share"], "| validation:", join_val)
    print("unit fixes:", unit_fixes)
    print("outliers:", [(o["carline"], o["powertrain"], o["studentized_resid"]) for o in outliers])
    print("band:", pred_band)


if __name__ == "__main__":
    main()
