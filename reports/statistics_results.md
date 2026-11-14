# Statistical Analysis (Stage 4)

Unit of analysis: one video headline. Sentiment = VADER compound score of the title.
Significance level: alpha = 0.05. Pairwise p-values are Holm-adjusted (6 comparisons).
`P(A > B)` = chance that a random headline from A scores higher than one from B (50% = no difference).

## 1. Descriptive statistics (full snapshot)

| channel   |    n |   mean |   median |   std |   ci95_low |   ci95_high |
|:----------|-----:|-------:|---------:|------:|-----------:|------------:|
| CBS News  | 2000 | -0.097 |        0 | 0.385 |     -0.114 |      -0.08  |
| CNN       | 2000 | -0.061 |        0 | 0.362 |     -0.077 |      -0.045 |
| Fox News  | 2000 | -0.16  |        0 | 0.388 |     -0.177 |      -0.143 |
| MSNBC     | 2000 | -0.046 |        0 | 0.393 |     -0.064 |      -0.029 |

## 2. Do channels differ in sentiment score? (full snapshot)

**Kruskal-Wallis:** H = 98.30, p = <0.0001, epsilon-squared = 0.0123 (n = 8,000).
- Significant at 0.05: **yes**. Channel explains about 1.23% of the rank variation in scores.

| A        | B        |   mean_A - mean_B | P(A > B)   |   cliffs_delta |   cohens_d | p_raw   | p_holm   | significant   | effect_size   |
|:---------|:---------|------------------:|:-----------|---------------:|-----------:|:--------|:---------|:--------------|:--------------|
| CBS News | CNN      |            -0.037 | 47.8%      |         -0.045 |     -0.098 | 0.0116  | 0.0231   | yes           | negligible    |
| CBS News | Fox News |             0.063 | 54.7%      |          0.094 |      0.163 | <0.0001 | <0.0001  | yes           | negligible    |
| CBS News | MSNBC    |            -0.051 | 46.6%      |         -0.068 |     -0.13  | 0.0001  | 0.0004   | yes           | negligible    |
| CNN      | Fox News |             0.099 | 57.1%      |          0.142 |      0.265 | <0.0001 | <0.0001  | yes           | negligible    |
| CNN      | MSNBC    |            -0.014 | 48.7%      |         -0.026 |     -0.038 | 0.1462  | 0.1462   | no            | negligible    |
| Fox News | MSNBC    |            -0.114 | 42.0%      |         -0.16  |     -0.291 | <0.0001 | <0.0001  | yes           | small         |

## 3. Do channels differ in the positive / neutral / negative mix?

**Chi-square test of independence:** chi2 = 92.7, df = 6, p = <0.0001, Cramer's V = 0.076.
- Significant: **yes**. Cramer's V of 0.08 is negligible (rule of thumb: 0.1 small, 0.3 medium, 0.5 large).

**Pairwise difference in negative-headline share** (percentage points, Wald 95% CI, Holm-adjusted):

| A        | B        |   neg_A_% |   neg_B_% |   diff_pp |   ci_low |   ci_high | p_raw   | p_holm   | significant   |
|:---------|:---------|----------:|----------:|----------:|---------:|----------:|:--------|:---------|:--------------|
| CBS News | CNN      |      38.6 |      34.1 |       4.5 |      1.5 |       7.5 | 0.0031  | 0.0074   | yes           |
| CBS News | Fox News |      38.6 |      44.6 |      -6   |     -9.1 |      -3   | 0.0001  | 0.0004   | yes           |
| CBS News | MSNBC    |      38.6 |      34   |       4.6 |      1.6 |       7.6 | 0.0025  | 0.0074   | yes           |
| CNN      | Fox News |      34.1 |      44.6 |     -10.5 |    -13.6 |      -7.5 | <0.0001 | <0.0001  | yes           |
| CNN      | MSNBC    |      34.1 |      34   |       0.1 |     -2.8 |       3   | 0.9468  | 0.9468   | no            |
| Fox News | MSNBC    |      44.6 |      34   |      10.6 |      7.6 |      13.7 | <0.0001 | <0.0001  | yes           |

## 4. Robustness checks

### 4a. Time-matched window: 2026-10-16 to 2026-11-11 (5,361 videos)

**Kruskal-Wallis:** H = 67.06, p = <0.0001, epsilon-squared = 0.0125 (n = 5,361).

| A        | B        |   mean_A - mean_B | P(A > B)   |   cliffs_delta |   cohens_d | p_raw   | p_holm   | significant   | effect_size   |
|:---------|:---------|------------------:|:-----------|---------------:|-----------:|:--------|:---------|:--------------|:--------------|
| CBS News | CNN      |            -0.017 | 49.0%      |         -0.019 |     -0.048 | 0.4613  | 1.0000   | no            | negligible    |
| CBS News | Fox News |             0.088 | 56.4%      |          0.128 |      0.231 | <0.0001 | <0.0001  | yes           | negligible    |
| CBS News | MSNBC    |            -0.01  | 49.2%      |         -0.016 |     -0.025 | 0.5217  | 1.0000   | no            | negligible    |
| CNN      | Fox News |             0.106 | 57.4%      |          0.147 |      0.279 | <0.0001 | <0.0001  | yes           | small         |
| CNN      | MSNBC    |             0.008 | 50.2%      |          0.003 |      0.02  | 0.8641  | 1.0000   | no            | negligible    |
| Fox News | MSNBC    |            -0.098 | 43.1%      |         -0.138 |     -0.25  | <0.0001 | <0.0001  | yes           | negligible    |

### 4b. Excluding the 94 videos whose title appears more than once

**Kruskal-Wallis:** H = 98.09, p = <0.0001, epsilon-squared = 0.0124 (n = 7,906).

### 4c. Day-level test (27 days, daily mean per channel)

Headlines posted on the same day share news events, so they are not fully independent. Here each *day* is one observation.

**Friedman test:** chi2 = 23.00, p = <0.0001, Kendall's W = 0.284 (0 = channels rank randomly each day, 1 = same ranking every day).

Number of days on which each channel had the **lowest** daily mean score:

|             |   CBS News |   CNN |   Fox News |   MSNBC |
|:------------|-----------:|------:|-----------:|--------:|
| days_lowest |          6 |     3 |         16 |       2 |

## 5. Trump headlines only (the test from the original notebook, re-run on this snapshot)

**Kruskal-Wallis:** H = 9.52, p = 0.0231, epsilon-squared = 0.0052 (n = 1,842).

| A        | B        |   mean_A - mean_B | P(A > B)   |   cliffs_delta |   cohens_d |   p_raw |   p_holm | significant   | effect_size   |
|:---------|:---------|------------------:|:-----------|---------------:|-----------:|--------:|---------:|:--------------|:--------------|
| CBS News | CNN      |            -0.019 | 49.4%      |         -0.012 |     -0.054 |  0.7663 |   1      | no            | negligible    |
| CBS News | Fox News |             0.037 | 53.4%      |          0.068 |      0.101 |  0.1019 |   0.3057 | no            | negligible    |
| CBS News | MSNBC    |             0.049 | 53.8%      |          0.077 |      0.13  |  0.0323 |   0.1613 | no            | negligible    |
| CNN      | Fox News |             0.056 | 54.1%      |          0.083 |      0.154 |  0.0459 |   0.1837 | no            | negligible    |
| CNN      | MSNBC    |             0.068 | 54.6%      |          0.092 |      0.181 |  0.01   |   0.0599 | no            | negligible    |
| Fox News | MSNBC    |             0.011 | 50.6%      |          0.011 |      0.03  |  0.7623 |   1      | no            | negligible    |

## 6. Topic headlines vs other headlines, within each channel

| channel   |   n_topic |   n_other |   mean_topic |   mean_other | P(topic > other)   |   cliffs_delta | p_raw   | p_holm   | significant   | effect_size   |
|:----------|----------:|----------:|-------------:|-------------:|:-------------------|---------------:|:--------|:---------|:--------------|:--------------|
| CBS News  |       508 |      1492 |       -0.02  |       -0.123 | 57.5%              |          0.15  | <0.0001 | <0.0001  | yes           | small         |
| CNN       |       461 |      1539 |       -0.02  |       -0.073 | 53.7%              |          0.075 | 0.0107  | 0.0107   | yes           | negligible    |
| Fox News  |       445 |      1555 |       -0.091 |       -0.18  | 56.2%              |          0.123 | <0.0001 | 0.0001   | yes           | negligible    |
| MSNBC     |       857 |      1143 |       -0.084 |       -0.018 | 45.7%              |         -0.086 | 0.0006  | 0.0013   | yes           | negligible    |

## 7. Do channels differ in how often headlines mention a tracked topic?

Share of headlines mentioning at least one tracked topic. MSNBC is compared with the other three channels combined (Wald 95% CI for the difference in percentage points).

| dataset             |   chi2 | p       |   cramers_v |   MSNBC_% |   others_% |   diff_pp |   ci_low |   ci_high |
|:--------------------|-------:|:--------|------------:|----------:|-----------:|----------:|---------:|----------:|
| Full snapshot       |  279.6 | <0.0001 |       0.187 |      42.8 |       23.6 |      19.3 |     16.9 |      21.7 |
| Time-matched window |  180.6 | <0.0001 |       0.184 |      43.1 |       25.7 |      17.3 |     14.7 |      20   |

Topic coverage % by channel in the time-matched window:

|           |   CBS News |   CNN |   Fox News |   MSNBC |
|:----------|-----------:|------:|-----------:|--------:|
| topic_pct |       30.7 |  25.3 |       23.8 |    43.1 |