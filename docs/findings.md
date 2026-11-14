# Key Findings and Recommendations

**Project:** News Headline Sentiment & Coverage Analysis: Four YouTube News Channels
**Data:** 8,000 video titles (2,000 per channel: CBS News, CNN, Fox News, MSNBC), collected 12 Nov 2026.
**Method:** VADER compound score of each *title*, tested with Kruskal-Wallis, Mann-Whitney (Holm-adjusted), chi-square and a day-level Friedman test. Full results: `reports/statistics_results.md`.

> **Read this first.** These are headlines, not comments. A VADER score measures how *negative or positive the words* in a headline sound. It does not measure what a channel believes or what viewers think, and it cannot explain *why* any difference exists.

## Summary
The clearest difference between the channels is **what they cover, not how their headlines sound**: MSNBC titles mention the tracked political topics about 17 to 19 percentage points more often than the other three channels. In tone, Fox News headlines score slightly lower than the others, consistently across every check, but the gap is small. CBS, CNN and MSNBC are statistically indistinguishable once compared over the same dates.

## Findings

| # | Finding | Strength |
|---|---|---|
| F1 | MSNBC headlines mention tracked political topics far more often | Strong |
| F2 | Fox headlines have the lowest tone, but the effect is small | Strong that it exists; small in size |
| F3 | CBS, CNN and MSNBC do not differ in tone over the same dates | Moderate |
| F4 | Tone moves with the news cycle across all four channels | Descriptive only |
| F5 | Topic headlines differ in tone from other headlines, in opposite directions | Weak to moderate |
| F6 | No channel difference in tone for Trump headlines | Negative finding |
| F7 | VADER scores wording, so tone results need careful reading | Method limit |

### F1. MSNBC headlines mention tracked political topics far more often
- 42.9% of MSNBC titles mention at least one of the 7 tracked topics, against 22.3% to 25.4% for the others (full snapshot).
- Over the same dates (time-matched, 27 days), MSNBC is 43.1% and the others are 23.8% to 30.7%.
- Difference MSNBC vs the other three combined: **17.3 percentage points (95% CI 14.7 to 20.0)**, Cramer's V = 0.18 (small to medium).
- Trump accounts for 1,842 of the 2,271 topic headlines overall (81%), so this is mostly a "Trump in the title" finding.
- *Caveat:* a name in a title says what the video is about, not what the channel thinks of it.

### F2. Fox headlines have the lowest tone, but the effect is small
- Mean score: Fox -0.160 (full), -0.148 (time-matched), against -0.046 to -0.097 for the others.
- Negative share: Fox 44.6% vs 34.0% to 38.6%; the gaps are 6.0 to 10.6 percentage points and every 95% interval excludes zero.
- Significant after Holm correction in every Fox comparison, in both the full and time-matched data. Fox also had the lowest daily average on **16 of 27 days** (about 7 would be expected if the channels were equal).
- Effect size is small at most: Cliff's delta 0.09 to 0.16, Cohen's d 0.16 to 0.29. Channel explains about 1.2% of the variation in scores.
- *Caveat:* we did not test why. It could reflect the kinds of stories covered rather than anything about the channel's views.

### F3. CBS, CNN and MSNBC do not differ in tone over the same dates
- Time-matched, all three pairs are non-significant (adjusted p = 1.00), and CNN vs MSNBC negative share is 34.1% vs 34.0%.
- In the full snapshot CBS looked slightly more negative (-0.097) with significant but negligible differences. Those disappear when the dates are matched, which is consistent with CBS's longer, earlier window being the reason.
- *Caveat:* "not significant" means no difference was detected, not that none exists.

### F4. Tone moves with the news cycle
- In the 7-day trend, all four channels rise together in early November and fall again afterwards, while Fox stays lowest throughout.
- This is a visual pattern, not a tested result, and the data cannot say which events caused it.
- Headlines in this window include midterm election coverage (for example titles about "midterm election night" and "Sen.-elect"), so the early-November rise may reflect election news. This was not tested.

### F5. Topic headlines differ in tone from other headlines, in opposite directions
- CBS, CNN and Fox: topic headlines are *less* negative than the channel's other headlines (for example Fox -0.091 vs -0.180).
- MSNBC: the reverse (-0.084 for topic vs -0.018 for other).
- All four are significant after correction, but effects are negligible to small (Cliff's delta 0.08 to 0.15).
- *Caveat:* a possible explanation is that "other" headlines include crime and disaster stories. We have not tested this.

### F6. No channel difference in tone for Trump headlines
- Overall test p = 0.023, but no pairwise comparison survives correction (smallest adjusted p = 0.060) and all effects are negligible.
- The "MSNBC is more negative on Trump" result from the original notebook is **not supported** on this snapshot; the original used different data and a comparison chosen after seeing the results.

### F7. VADER scores wording, so tone results need careful reading
- 40% of headlines score within the neutral band, so neutrals are kept in all main analyses.
- The most negative headlines are driven by event words (riots, attack, death penalty). Some scores are misreadings: a headline about a teen accused of mowing down two friends scored +0.86 because of "best friends".

## Recommendations
*For a media-monitoring or content-analytics team, or as next steps for this project.*

1. **Compare channels only over matched dates.** The full-snapshot comparison produced CBS differences that vanished when dates were matched.
2. **Use a baseline, not a raw gap.** Treat Fox's small, stable offset as its baseline and flag *changes* relative to each channel's own 7-day average.
3. **Report coverage and tone together.** Topic coverage (F1) is the strongest signal here; tone alone would understate it.
4. **Validate VADER before relying on it.** Hand-label about 200 random headlines and report how often VADER agrees. This is the most valuable next step and has not been done yet.
5. **Annotate spikes with news events** before interpreting any movement in tone (F4).
6. **To discuss audiences, collect comments** (a possible extension), and treat commenters as a self-selected group, not the public.
7. **Keep dated snapshots** so future runs can measure change instead of overwriting results.

## What this analysis cannot tell you
- What viewers or the public think.
- Whether any channel is biased, or why its headlines differ.
- Anything about videos older than each channel's latest 2,000 (the data covers 27 to 69 days).
- Anything about comments, shorts versus long videos, or other channels.

## Interview summary (30 seconds)
"I analysed 8,000 headlines from four news channels. The biggest finding was about coverage: MSNBC mentions the tracked political topics far more often. Tone differences were small: Fox scored a little lower on VADER across all checks, and the other three were indistinguishable once I matched the dates. I used corrected tests and effect sizes, and I'm clear that VADER measures wording, not opinion."
