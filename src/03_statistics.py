"""
Stage 4 - Statistical analysis
------------------------------
Input:   data/processed/videos_clean.csv
Output:  reports/statistics_results.md, figures/08_mean_ci.png

Questions answered:
  1. Do channels differ in headline sentiment score?  (Kruskal-Wallis + pairwise tests)
  2. Do channels differ in the mix of positive / neutral / negative headlines?  (chi-square)
  3. Are the differences big enough to matter?  (effect sizes)
  4. Do the results survive robustness checks?  (time-matched window, day-level test)

Run from the project root:   python src/04_statistics.py
"""

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
ORDER = ["CBS News", "CNN", "Fox News", "MSNBC"]
CHANNEL_COLORS = {"Fox News": "#5975a4", "CNN": "#b55d60", "MSNBC": "#5f9e6e", "CBS News": "#666666"}
ALPHA = 0.05
OUT = []


def say(text=""):
    print(text)
    OUT.append(text)


def holm(pvalues):
    """Holm-Bonferroni adjusted p-values (controls the chance of any false positive)."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    adjusted = np.empty(m)
    running_max = 0.0
    for rank, i in enumerate(np.argsort(p)):
        running_max = max(running_max, (m - rank) * p[i])
        adjusted[i] = min(1.0, running_max)
    return adjusted


def size_label(delta):
    """Rule-of-thumb labels for Cliff's delta (Romano et al., 2006)."""
    d = abs(delta)
    return "negligible" if d < 0.147 else "small" if d < 0.33 else "medium" if d < 0.474 else "large"


def epsilon_squared(h, n):
    """Effect size for Kruskal-Wallis: share of rank variation explained by group."""
    return h / (n - 1)


def kruskal_block(data, group_col, groups, value_col="sentiment_score"):
    samples = [data.loc[data[group_col] == g, value_col].values for g in groups]
    h, p = stats.kruskal(*samples)
    n = sum(len(s) for s in samples)
    return h, p, epsilon_squared(h, n), n


def pairwise_mwu(data, groups, group_col="channel", value_col="sentiment_score"):
    """Mann-Whitney U for every pair of groups, with Holm correction and effect sizes."""
    rows = []
    for a, b in combinations(groups, 2):
        x = data.loc[data[group_col] == a, value_col].values
        y = data.loc[data[group_col] == b, value_col].values
        u, p = stats.mannwhitneyu(x, y, alternative="two-sided")
        ps = u / (len(x) * len(y))            # probability a random A video scores higher than a random B video
        delta = 2 * ps - 1                    # Cliff's delta (rank-biserial correlation)
        pooled_sd = np.sqrt(((len(x) - 1) * x.var(ddof=1) + (len(y) - 1) * y.var(ddof=1)) / (len(x) + len(y) - 2))
        rows.append({"A": a, "B": b, "n_A": len(x), "n_B": len(y),
                     "mean_A - mean_B": x.mean() - y.mean(),
                     "P(A > B)": ps, "cliffs_delta": delta,
                     "cohens_d": (x.mean() - y.mean()) / pooled_sd, "p_raw": p})
    res = pd.DataFrame(rows)
    res["p_holm"] = holm(res["p_raw"])
    res["significant"] = np.where(res["p_holm"] < ALPHA, "yes", "no")
    res["effect_size"] = res["cliffs_delta"].apply(size_label)
    return res


def fmt_p(p):
    return "<0.0001" if p < 1e-4 else f"{p:.4f}"


def show_pairs(res):
    t = res.copy()
    for c in ["mean_A - mean_B", "cohens_d", "cliffs_delta"]:
        t[c] = t[c].round(3)
    t["P(A > B)"] = (t["P(A > B)"] * 100).round(1).astype(str) + "%"
    t["p_raw"] = t["p_raw"].apply(fmt_p)
    t["p_holm"] = t["p_holm"].apply(fmt_p)
    say(t[["A", "B", "mean_A - mean_B", "P(A > B)", "cliffs_delta", "cohens_d",
           "p_raw", "p_holm", "significant", "effect_size"]].to_markdown(index=False))


def main():
    df = pd.read_csv(ROOT / "data" / "processed" / "videos_clean.csv")
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)

    say("# Statistical Analysis (Stage 4)\n")
    say("Unit of analysis: one video headline. Sentiment = VADER compound score of the title.")
    say(f"Significance level: alpha = {ALPHA}. Pairwise p-values are Holm-adjusted (6 comparisons).")
    say("`P(A > B)` = chance that a random headline from A scores higher than one from B (50% = no difference).\n")

    # ------------------------------------------------------------------ 1. descriptive
    say("## 1. Descriptive statistics (full snapshot)\n")
    g = df.groupby("channel")["sentiment_score"]
    desc = pd.DataFrame({"n": g.count(), "mean": g.mean(), "median": g.median(), "std": g.std()}).loc[ORDER]
    desc["se"] = desc["std"] / np.sqrt(desc["n"])
    desc["ci95_low"] = desc["mean"] - 1.96 * desc["se"]
    desc["ci95_high"] = desc["mean"] + 1.96 * desc["se"]
    say(desc.drop(columns="se").round(3).to_markdown())

    # ------------------------------------------------------------------ 2. scores
    say("\n## 2. Do channels differ in sentiment score? (full snapshot)\n")
    h, p, e2, n = kruskal_block(df, "channel", ORDER)
    say(f"**Kruskal-Wallis:** H = {h:.2f}, p = {fmt_p(p)}, epsilon-squared = {e2:.4f} (n = {n:,}).")
    say(f"- Significant at 0.05: **{'yes' if p < ALPHA else 'no'}**. "
        f"Channel explains about {100 * e2:.2f}% of the rank variation in scores.\n")
    full_pairs = pairwise_mwu(df, ORDER)
    show_pairs(full_pairs)

    # ------------------------------------------------------------------ 3. label mix
    say("\n## 3. Do channels differ in the positive / neutral / negative mix?\n")
    table = pd.crosstab(df["channel"], df["sentiment_label"]).loc[ORDER, ["positive", "neutral", "negative"]]
    chi2, p_chi, dof, _ = stats.chi2_contingency(table)
    v = np.sqrt(chi2 / (table.values.sum() * (min(table.shape) - 1)))
    say(f"**Chi-square test of independence:** chi2 = {chi2:.1f}, df = {dof}, p = {fmt_p(p_chi)}, "
        f"Cramer's V = {v:.3f}.")
    say(f"- Significant: **{'yes' if p_chi < ALPHA else 'no'}**. "
        f"Cramer's V of {v:.2f} is {'negligible' if v < 0.1 else 'small' if v < 0.3 else 'medium'} "
        f"(rule of thumb: 0.1 small, 0.3 medium, 0.5 large).\n")

    say("**Pairwise difference in negative-headline share** (percentage points, Wald 95% CI, Holm-adjusted):\n")
    neg = df["sentiment_label"].eq("negative").groupby(df["channel"]).agg(["sum", "count"])
    rows = []
    for a, b in combinations(ORDER, 2):
        na, ta = neg.loc[a, "sum"], neg.loc[a, "count"]
        nb, tb = neg.loc[b, "sum"], neg.loc[b, "count"]
        pa, pb = na / ta, nb / tb
        se = np.sqrt(pa * (1 - pa) / ta + pb * (1 - pb) / tb)
        _, pv, _, _ = stats.chi2_contingency([[na, ta - na], [nb, tb - nb]], correction=False)
        rows.append({"A": a, "B": b, "neg_A_%": 100 * pa, "neg_B_%": 100 * pb,
                     "diff_pp": 100 * (pa - pb), "ci_low": 100 * (pa - pb - 1.96 * se),
                     "ci_high": 100 * (pa - pb + 1.96 * se), "p_raw": pv})
    neg_pairs = pd.DataFrame(rows)
    neg_pairs["p_holm"] = holm(neg_pairs["p_raw"])
    neg_pairs["significant"] = np.where(neg_pairs["p_holm"] < ALPHA, "yes", "no")
    t = neg_pairs.copy()
    for c in ["neg_A_%", "neg_B_%", "diff_pp", "ci_low", "ci_high"]:
        t[c] = t[c].round(1)
    t["p_raw"] = t["p_raw"].apply(fmt_p)
    t["p_holm"] = t["p_holm"].apply(fmt_p)
    say(t.to_markdown(index=False))

    # ------------------------------------------------------------------ 4. robustness
    say("\n## 4. Robustness checks\n")

    # 4a time-matched window
    start = df.groupby("channel")["published_at"].min().max().normalize() + pd.Timedelta(days=1)
    end = df.groupby("channel")["published_at"].max().min().normalize()
    win = df[(df["published_at"] >= start) & (df["published_at"] < end)].copy()
    win["day"] = win["published_at"].dt.normalize()
    say(f"### 4a. Time-matched window: {start.date()} to {(end - pd.Timedelta(days=1)).date()} "
        f"({len(win):,} videos)\n")
    h2, p2, e2b, n2 = kruskal_block(win, "channel", ORDER)
    say(f"**Kruskal-Wallis:** H = {h2:.2f}, p = {fmt_p(p2)}, epsilon-squared = {e2b:.4f} (n = {n2:,}).\n")
    tm_pairs = pairwise_mwu(win, ORDER)
    show_pairs(tm_pairs)

    # 4b without repeated titles
    nodup = df[~df["duplicate_title"]]
    h3, p3, e2c, n3 = kruskal_block(nodup, "channel", ORDER)
    say(f"\n### 4b. Excluding the {len(df) - len(nodup)} videos whose title appears more than once\n")
    say(f"**Kruskal-Wallis:** H = {h3:.2f}, p = {fmt_p(p3)}, epsilon-squared = {e2c:.4f} (n = {n3:,}).\n")

    # 4c day-level test (handles the fact that headlines on the same day are not independent)
    daily = win.pivot_table(index="day", columns="channel", values="sentiment_score", aggfunc="mean")[ORDER]
    chi_f, p_f = stats.friedmanchisquare(*[daily[c] for c in ORDER])
    kendall_w = chi_f / (len(daily) * (len(ORDER) - 1))
    lowest = daily.idxmin(axis=1).value_counts().reindex(ORDER).fillna(0).astype(int)
    say(f"### 4c. Day-level test ({len(daily)} days, daily mean per channel)\n")
    say("Headlines posted on the same day share news events, so they are not fully independent. "
        "Here each *day* is one observation.\n")
    say(f"**Friedman test:** chi2 = {chi_f:.2f}, p = {fmt_p(p_f)}, Kendall's W = {kendall_w:.3f} "
        f"(0 = channels rank randomly each day, 1 = same ranking every day).\n")
    say("Number of days on which each channel had the **lowest** daily mean score:\n")
    say(lowest.rename("days_lowest").to_frame().T.to_markdown())

    # ------------------------------------------------------------------ 5. Trump headlines
    say("\n## 5. Trump headlines only (the test from the original notebook, re-run on this snapshot)\n")
    trump = df[df["trump"]]
    h4, p4, e2d, n4 = kruskal_block(trump, "channel", ORDER)
    say(f"**Kruskal-Wallis:** H = {h4:.2f}, p = {fmt_p(p4)}, epsilon-squared = {e2d:.4f} (n = {n4:,}).\n")
    trump_pairs = pairwise_mwu(trump, ORDER)
    show_pairs(trump_pairs)

    # ------------------------------------------------------------------ 6. topic vs other
    say("\n## 6. Topic headlines vs other headlines, within each channel\n")
    rows = []
    for ch in ORDER:
        sub = df[df["channel"] == ch]
        x = sub.loc[sub["relevant"], "sentiment_score"].values
        y = sub.loc[~sub["relevant"], "sentiment_score"].values
        u, pv = stats.mannwhitneyu(x, y, alternative="two-sided")
        rows.append({"channel": ch, "n_topic": len(x), "n_other": len(y),
                     "mean_topic": x.mean(), "mean_other": y.mean(),
                     "P(topic > other)": u / (len(x) * len(y)), "cliffs_delta": 2 * u / (len(x) * len(y)) - 1,
                     "p_raw": pv})
    to = pd.DataFrame(rows)
    to["p_holm"] = holm(to["p_raw"])
    to["significant"] = np.where(to["p_holm"] < ALPHA, "yes", "no")
    to["effect_size"] = to["cliffs_delta"].apply(size_label)
    t = to.copy()
    for c in ["mean_topic", "mean_other", "cliffs_delta"]:
        t[c] = t[c].round(3)
    t["P(topic > other)"] = (t["P(topic > other)"] * 100).round(1).astype(str) + "%"
    t["p_raw"] = t["p_raw"].apply(fmt_p)
    t["p_holm"] = t["p_holm"].apply(fmt_p)
    say(t.to_markdown(index=False))

    # ------------------------------------------------------------------ 7. topic coverage
    say("\n## 7. Do channels differ in how often headlines mention a tracked topic?\n")
    say("Share of headlines mentioning at least one tracked topic. MSNBC is compared with the other three channels "
        "combined (Wald 95% CI for the difference in percentage points).\n")
    rows = []
    for name, data in (("Full snapshot", df), ("Time-matched window", win)):
        table_t = pd.crosstab(data["channel"], data["relevant"])
        chi_t, p_t, _, _ = stats.chi2_contingency(table_t)
        v_t = np.sqrt(chi_t / table_t.values.sum())          # Cramer's V for a 4 x 2 table
        is_ms = data["channel"] == "MSNBC"
        pa, pb = data.loc[is_ms, "relevant"].mean(), data.loc[~is_ms, "relevant"].mean()
        se = np.sqrt(pa * (1 - pa) / is_ms.sum() + pb * (1 - pb) / (~is_ms).sum())
        rows.append({"dataset": name, "chi2": round(chi_t, 1), "p": fmt_p(p_t), "cramers_v": round(v_t, 3),
                     "MSNBC_%": round(100 * pa, 1), "others_%": round(100 * pb, 1),
                     "diff_pp": round(100 * (pa - pb), 1),
                     "ci_low": round(100 * (pa - pb - 1.96 * se), 1),
                     "ci_high": round(100 * (pa - pb + 1.96 * se), 1)})
    say(pd.DataFrame(rows).to_markdown(index=False))
    cov_tm = (win.groupby("channel")["relevant"].mean() * 100).round(1).loc[ORDER]
    say("\nTopic coverage % by channel in the time-matched window:\n")
    say(cov_tm.rename("topic_pct").to_frame().T.to_markdown())

    # ------------------------------------------------------------------ figure
    tm_desc = win.groupby("channel")["sentiment_score"].agg(["mean", "std", "count"]).loc[ORDER]
    tm_desc["ci"] = 1.96 * tm_desc["std"] / np.sqrt(tm_desc["count"])
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(ORDER))
    ax.errorbar(x - 0.1, desc["mean"], yerr=1.96 * desc["se"], fmt="o", capsize=4, color="black",
                label="Full snapshot")
    ax.errorbar(x + 0.1, tm_desc["mean"], yerr=tm_desc["ci"], fmt="s", capsize=4, color="#d95f02",
                label="Time-matched window")
    ax.axhline(0, color="grey", lw=0.8, ls="--")
    ax.set_xticks(x)
    ax.set_xticklabels(ORDER)
    ax.set_ylabel("Mean VADER score (95% CI)")
    ax.set_title("Average headline sentiment by channel")
    ax.legend(loc="lower right")
    fig.savefig(ROOT / "figures" / "08_mean_ci.png", dpi=150, bbox_inches="tight")

    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "statistics_results.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\nSaved reports/statistics_results.md and figures/08_mean_ci.png")


if __name__ == "__main__":
    main()