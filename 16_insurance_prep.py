"""16_insurance_prep.py -- clean Phil's IIHS dataset, audit the Grok-derived
automation scores, and join catalog attributes.

Inputs:
  Phil Data/Insurance Project Dataset - 2026.09.01.xlsx
  outputs/catalog_fegov.csv   (fueleconomy.gov catalog with canonical makes)

Outputs:
  outputs/insurance_clean.csv                  regression-ready rows
  outputs/automation_score_audit_sample.csv    30-vehicle human-verification
                                               worksheet (blank verdict column)
  reports/16_insurance_prep.md                 cleaning log, join rates, and
                                               the automated score audit

Audit design: the automation scores were generated with Grok and shipped with
no citations, so this stage runs the checks that CAN be automated
(duplicate-key conflicts, window-invariance, EV plausibility) and emits a
random sample worksheet for the checks that require a human against
manufacturer equipment lists. No scores are altered.
"""

import io
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PHIL = os.path.join(HERE, "Phil Data",
                    "Insurance Project Dataset - 2026.09.01.xlsx")
OUT = os.path.join(HERE, "outputs")
REPORTS = os.path.join(HERE, "reports")
RNG = np.random.default_rng(31_82)

LOSS_COLS = ["collision", "property_damage", "comprehensive",
             "personal_injury", "medical_payment", "bodily_injury"]

# Tokens stripped from IIHS vehicle names before matching the catalog.
STRIP_TOKENS = {
    "2dr", "4dr", "2wd", "4wd", "awd", "fwd", "rwd", "convertible",
    "hybrid", "electric", "plug", "in", "plug-in", "phev", "ev",
    "with", "w", "eyesight", "active", "safety", "sensing",
}


def norm(s):
    s = str(s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # 'f-150' normalizes to 'f 150' but the catalog writes 'f150'; collapse
    # letter-space-number model codes.
    s = re.sub(r"\b([a-z]) (\d{2,4})\b", r"\1\2", s)
    return s


def base_model(vehicle, make):
    v = norm(vehicle)
    m = norm(make)
    if v.startswith(m):
        v = v[len(m):].strip()
    toks = [t for t in v.split() if t not in STRIP_TOKENS]
    return " ".join(toks)


def load_phil():
    d = pd.read_excel(PHIL, sheet_name="(IIHS) - Combined Dataset", header=3)
    d.columns = ["year_range", "start_year", "end_year", "make", "body_style",
                 "vehicle_size", "vehicle"] + LOSS_COLS + ["automation_score"]
    n0 = len(d)
    d = d.dropna(subset=["vehicle", "year_range"])
    coerce_log = [("rows with empty vehicle/year dropped", n0 - len(d))]
    for c in LOSS_COLS + ["automation_score", "start_year", "end_year"]:
        before = d[c].notna().sum()
        d[c] = pd.to_numeric(d[c], errors="coerce")
        bad = int(before - d[c].notna().sum())
        if bad:
            coerce_log.append((f"`{c}`: non-numeric -> null", bad))
    lut = pd.read_excel(PHIL, sheet_name="Automation Lookup Table")
    lut.columns = [c.strip() for c in lut.columns][:len(lut.columns)]
    return d.reset_index(drop=True), lut, coerce_log


def audit_scores(d, lut):
    """Automated checks on the Grok-derived scores."""
    a = {}
    # 1. Duplicate lookup keys with conflicting scores.
    g = lut.groupby("LookupKey")["AutomationScore"].nunique()
    conflicts = g[g > 1]
    a["lookup_rows"] = int(len(lut))
    a["duplicate_keys"] = int((lut.groupby("LookupKey").size() > 1).sum())
    a["conflicting_keys"] = conflicts.index.tolist()

    # 2. Window-invariance: does any vehicle's score change across year
    #    windows? A constant score despite ADAS going standard mid-period
    #    means the score describes the nameplate, not the model year.
    per_v = d.groupby("vehicle")["automation_score"].nunique()
    a["vehicles_total"] = int(per_v.size)
    a["vehicles_score_varies"] = int((per_v > 1).sum())
    a["varying_examples"] = per_v[per_v > 1].index.tolist()[:10]

    # 3. EV plausibility. Standard ADAS on EVs is a ~2019+ fact, not an
    #    always fact (2013-2017 Leaf/Volt/Spark EV shipped without it), so
    #    only recent windows can flag a suspect label.
    ev_mask = d.vehicle.str.contains("electric|EV\\b|Tesla|Leaf|Bolt|Ioniq 5|"
                                     "ID.4|Polestar|Rivian|Lucid|Mach-E",
                                     case=False, regex=True)
    ev1 = d[ev_mask & (d.automation_score == 1) & (d.end_year >= 2021)]
    a["ev_rows"] = int(ev_mask.sum())
    a["ev_scored_basic"] = sorted(ev1.vehicle.unique().tolist())

    # 4. Tesla check: Autopilot has been standard since 2019; Teslas below 3
    #    in recent windows are suspect in the other direction.
    tesla = d[d.vehicle.str.contains("Tesla", case=False) & (d.end_year >= 2020)]
    a["tesla_recent_rows"] = int(len(tesla))
    a["tesla_below_3"] = sorted(
        tesla[tesla.automation_score < 3].vehicle.unique().tolist())
    return a


def audit_sample(d):
    """30-vehicle worksheet for human verification against equipment lists."""
    uniq = (d.sort_values("end_year")
            .groupby("vehicle").last().reset_index()
            [["vehicle", "make", "body_style", "vehicle_size", "year_range",
              "automation_score"]])
    take = uniq.iloc[RNG.choice(len(uniq), size=30, replace=False)].copy()
    take = take.sort_values(["make", "vehicle"]).reset_index(drop=True)
    take["verified_score_1_2_3"] = ""
    take["verification_source"] = ""
    take["agrees_y_n"] = ""
    take.to_csv(os.path.join(OUT, "automation_score_audit_sample.csv"),
                index=False, encoding="utf-8")
    return len(take)


def join_catalog(d):
    cat = pd.read_csv(os.path.join(OUT, "catalog_fegov.csv"), low_memory=False)
    cat["k_make"] = cat["canonical_make"].map(norm)
    cat["k_model"] = cat["baseModel"].map(norm)
    cat["is_ev"] = (cat["fuelType1"] == "Electricity").astype(int)

    d = d.copy()
    d["k_make"] = d["make"].map(norm)
    d["k_model"] = d.apply(lambda r: base_model(r.vehicle, r.make), axis=1)

    # Catalog attributes averaged over the IIHS window years per (make,
    # model). Two indexes -- baseModel and the raw model column -- and a
    # progressive-shortening fallback ('civic si hatchback' -> 'civic si'
    # -> 'civic') for IIHS trim suffixes the catalog doesn't carry.
    idx = {}
    cat["k_model2"] = cat["model"].map(norm)
    for key_col in ("k_model", "k_model2"):
        for (mk, md), g in cat.groupby(["k_make", key_col]):
            idx.setdefault((mk, md), []).append(g)

    def lookup(mk, md):
        toks = md.split()
        while toks:
            hit = idx.get((mk, " ".join(toks)))
            if hit:
                return pd.concat(hit)
            toks = toks[:-1]
        return None

    rows = []
    for i, r in d.iterrows():
        g = lookup(r.k_make, r.k_model)
        if g is None:
            rows.append((np.nan, np.nan, np.nan, np.nan, False))
            continue
        w = g[(g.year >= r.start_year) & (g.year <= r.end_year)]
        if not len(w):
            w = g  # fall back to all years of that model
        rows.append((w.comb08.mean(), w.displ.mean(), w.cylinders.mean(),
                     int(w.is_ev.max()), True))
    extra = pd.DataFrame(rows, columns=["cat_comb08_mpg", "cat_displacement_l",
                                        "cat_cylinders", "cat_is_ev",
                                        "cat_matched"], index=d.index)
    return pd.concat([d, extra], axis=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    d, lut, coerce_log = load_phil()
    a = audit_scores(d, lut)
    n_sample = audit_sample(d)
    d = join_catalog(d)
    d.to_csv(os.path.join(OUT, "insurance_clean.csv"), index=False,
             encoding="utf-8")

    match_rate = d.cat_matched.mean()
    b = io.StringIO()
    b.write("# Insurance Data Prep and Automation-Score Audit\n\n"
            "Generated by 16_insurance_prep.py from Phil's workbook "
            "(Insurance Project Dataset - 2026.09.01.xlsx).\n")
    b.write(f"\n## Cleaning\n\n- Rows kept: {len(d):,}\n")
    for msg, n in coerce_log:
        b.write(f"- {msg}: {n:,}\n")
    b.write("- IIHS loss values are relative deviations from the all-vehicle "
            "average for the window (-0.30 = 30% better than average), per "
            "the IIHS/HLDI losses-by-make-and-model publication.\n")

    b.write("\n## Automated audit of the Grok-derived automation scores\n\n")
    b.write("The workbook's 'Automation Score Supporting Links' section "
            "contains zero links; scores are uncited AI output. Automated "
            "checks:\n\n")
    b.write(f"1. **Lookup consistency.** {a['lookup_rows']} lookup rows, "
            f"{a['duplicate_keys']} duplicated keys, "
            f"{len(a['conflicting_keys'])} with conflicting scores"
            + (f": {a['conflicting_keys']}" if a["conflicting_keys"] else "")
            + ".\n")
    b.write(f"2. **Window-invariance.** {a['vehicles_score_varies']} of "
            f"{a['vehicles_total']} vehicles ever change score across year "
            "windows. A score that never varies describes the nameplate's "
            "current equipment, not the model years being rated: a 2015-2017 "
            "window scored by 2024 equipment overstates early-window "
            "automation. This is the audit's main structural finding and "
            "belongs on the limitations slide.\n" if a["vehicles_score_varies"] == 0
            else f"2. **Window-invariance.** {a['vehicles_score_varies']} of "
            f"{a['vehicles_total']} vehicles change score across windows "
            f"(examples: {a['varying_examples']}).\n")
    b.write(f"3. **EV plausibility.** {a['ev_rows']:,} EV-pattern rows; "
            f"EVs scored 'Basic': {a['ev_scored_basic'] or 'none'}. Every "
            "US-market EV ships standard ADAS, so any entry here is a "
            "suspect label.\n")
    b.write(f"4. **Tesla check.** {a['tesla_recent_rows']} Tesla rows with "
            f"windows ending 2020+; scored below 3: "
            f"{a['tesla_below_3'] or 'none'}.\n")
    b.write(f"\n**Human-verification worksheet**: "
            f"outputs/automation_score_audit_sample.csv ({n_sample} randomly "
            "sampled vehicles, seeded) with blank columns for the verified "
            "score, the source consulted, and agree/disagree. Verify against "
            "manufacturer equipment pages or IIHS ratings pages and report "
            "the agreement rate on the data-sources slide.\n")

    b.write(f"\n## Catalog join\n\n- Match rate: {match_rate:.1%} of rows "
            "matched a fueleconomy.gov (make, base model); attributes "
            "(`cat_comb08_mpg`, `cat_displacement_l`, `cat_cylinders`, "
            "`cat_is_ev`) averaged over the window years.\n"
            "- Matching tries the full trim string, then progressively drops "
            "trailing tokens ('civic si hatchback' -> 'civic si' -> 'civic'), "
            "so a trim can inherit its base model's attributes; that is the "
            "price of the match rate and is acceptable for MPG/displacement "
            "controls, not for anything trim-specific.\n"
            "- Unmatched rows keep null attributes and stay in the file; the "
            "model stage decides handling.\n")

    with open(os.path.join(REPORTS, "16_insurance_prep.md"), "w",
              encoding="utf-8") as f:
        f.write(b.getvalue())

    print(f"rows {len(d):,} | catalog match {match_rate:.1%}")
    print("score varies across windows:", a["vehicles_score_varies"],
          "of", a["vehicles_total"])
    print("lookup conflicts:", len(a["conflicting_keys"]))
    print("EVs scored basic:", len(a["ev_scored_basic"]),
          "| Teslas below 3:", len(a["tesla_below_3"]))


if __name__ == "__main__":
    main()
