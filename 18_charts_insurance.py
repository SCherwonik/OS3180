"""18_charts_insurance.py -- figures for the insurance regression act.

Reads outputs/insurance_model.json + outputs/insurance_clean.csv.
Writes charts/fig29_coefficients.png, charts/fig30_raw_vs_controlled.png.
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE, WASH = "#898781", "#e1e0d9", "#c3c2b7", "#f0efec"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.edgecolor": BASELINE,
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "grid.linestyle": "-", "xtick.color": MUTED,
    "ytick.color": MUTED, "text.color": INK, "axes.labelcolor": INK2,
    "axes.titlecolor": INK, "font.size": 11,
})


def style_ax(ax, xgrid=True):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=xgrid)
    ax.tick_params(length=0)


def footnote(fig, text):
    fig.text(0.01, 0.012, text, fontsize=8.5, color=MUTED)


def save(fig, name):
    fig.savefig(os.path.join(CHARTS, name), dpi=150)
    plt.close(fig)


DV_LABELS = {
    "collision": ("Collision (repair)", S2),
    "personal_injury": ("Personal injury", S1),
    "bodily_injury": ("Bodily injury", S1),
}


def fig29(M):
    rows = []
    for dv in ("collision", "personal_injury", "bodily_injury"):
        for term, tl in (("score3", "Score 3 vs Basic"),
                         ("score2", "Score 2 vs Basic")):
            m = M[dv]
            rows.append({
                "label": f"{DV_LABELS[dv][0]}  --  {tl}",
                "coef": m["coef"][term], "se": m["se"][term],
                "p": m["p"][term], "color": DV_LABELS[dv][1],
            })
    rows = rows[::-1]  # top-to-bottom reading order

    fig, ax = plt.subplots(figsize=(11, 6.2))
    style_ax(ax)
    ax.axvline(0, color=INK2, lw=1.2)
    ys = np.arange(len(rows))
    for y, r in zip(ys, rows):
        lo, hi = r["coef"] - 1.96 * r["se"], r["coef"] + 1.96 * r["se"]
        sig = r["p"] < 0.05
        ax.plot([lo, hi], [y, y], color=r["color"], lw=2.2,
                alpha=1.0 if sig else 0.45)
        ax.plot(r["coef"], y, "o", ms=8, mfc=r["color"] if sig else SURFACE,
                mec=r["color"], mew=1.8)
        ax.text(hi + 0.012, y, f"p = {r['p']:.3f}", fontsize=9, color=INK2,
                va="center")
    ax.set_yticks(ys)
    ax.set_yticklabels([r["label"] for r in rows], fontsize=10)
    ax.set_xlabel("Coefficient: relative loss vs automation score 1 "
                  "(95% CI, cluster-robust)")
    ax.annotate("the one solid finding:\n+0.24 collision penalty",
                xy=(0.2445, 5), xytext=(0.30, 3.6), fontsize=10, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_title("Filled markers: p < 0.05. Hollow: not significant. Controls: "
                 "size, body group, window year, MPG, EV.", loc="left",
                 fontsize=10.5, color=INK2, pad=8)
    fig.suptitle("Automation and insurance losses: the repair penalty is real, "
                 "the injury benefit is a maybe",
                 x=0.01, ha="left", fontsize=15, fontweight="bold")
    footnote(fig, "IIHS/HLDI relative losses, 2015-2024 windows; OLS with SEs "
                  "clustered by vehicle (2,289 clusters). Automation scores are "
                  "audited AI labels (reports/16_insurance_prep.md).")
    fig.tight_layout(rect=(0, 0.04, 1, 0.90))
    save(fig, "fig29_coefficients.png")


def fig30(M, d):
    raw = d.groupby("automation_score")[["collision", "personal_injury"]].mean()

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 5.8))
    for a in (a1, a2):
        style_ax(a, xgrid=False)
        a.grid(axis="y", visible=True)
        a.axhline(0, color=INK2, lw=1.0)

    x = np.arange(3)
    w = 0.36
    a1.bar(x - w / 2, raw["collision"], w, color=S2, edgecolor=SURFACE)
    a1.bar(x + w / 2, raw["personal_injury"], w, color=S1, edgecolor=SURFACE)
    a1.set_xticks(x)
    a1.set_xticklabels(["Score 1\nBasic", "Score 2\nStandard", "Score 3"])
    a1.set_title("Raw means: a clean two-sided story.\nCollision worsens, "
                 "injury improves with automation", loc="left", fontsize=10.5,
                 color=INK2)

    terms = [("collision", "score3", S2), ("personal_injury", "score3", S1)]
    for i, (dv, term, c) in enumerate(terms):
        m = M[dv]
        coef, se, p = m["coef"][term], m["se"][term], m["p"][term]
        lo, hi = coef - 1.96 * se, coef + 1.96 * se
        sig = p < 0.05
        a2.plot([i, i], [lo, hi], color=c, lw=2.4, alpha=1.0 if sig else 0.45)
        a2.plot(i, coef, "o", ms=9, mfc=c if sig else SURFACE, mec=c, mew=1.8)
        a2.text(i + 0.07, coef, f"p = {p:.3f}", fontsize=9.5, color=INK2,
                va="center")
    a2.set_xlim(-0.5, 1.8)
    a2.set_xticks([0, 1])
    a2.set_xticklabels(["Collision\n(score 3 effect)", "Personal injury\n(score 3 effect)"])
    a2.set_title("With controls + clustering: only the\ncollision penalty "
                 "survives at p < 0.05", loc="left", fontsize=10.5, color=INK2)

    handles = [plt.Rectangle((0, 0), 1, 1, color=S2),
               plt.Rectangle((0, 0), 1, 1, color=S1)]
    lg = a1.legend(handles, ["Collision (repair)", "Personal injury"],
                   frameon=False, fontsize=9.5, loc="upper left")
    for t in lg.get_texts():
        t.set_color(INK2)

    fig.suptitle("Revision #8: the two-sided automation story, before and after "
                 "the controls arrive", x=0.01, ha="left", fontsize=14.5,
                 fontweight="bold")
    footnote(fig, "Left: unadjusted mean IIHS relative loss by score. Right: "
                  "score-3 coefficients with size/body/year/MPG/EV controls, "
                  "vehicle-clustered 95% CIs.")
    fig.tight_layout(rect=(0, 0.05, 1, 0.90))
    save(fig, "fig30_raw_vs_controlled.png")


def main():
    os.makedirs(CHARTS, exist_ok=True)
    with open(os.path.join(HERE, "outputs", "insurance_model.json"),
              encoding="utf-8") as f:
        M = json.load(f)
    d = pd.read_csv(os.path.join(HERE, "outputs", "insurance_clean.csv"),
                    low_memory=False)
    fig29(M)
    fig30(M, d)
    print("wrote fig29, fig30")


if __name__ == "__main__":
    main()
