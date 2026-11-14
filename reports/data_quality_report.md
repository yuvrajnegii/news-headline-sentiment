# Data Quality Report (Stage 1)

- Raw videos file: 8,000 rows, 14 columns
- Raw sentiments file: 8,000 rows, 3 columns
- Duplicate youtube_id: 0 in both files; both files contain exactly the same IDs
- Columns with missing values in videos.csv: 0
- Empty or very short titles (< 3 chars): 0
- Old 'sentiment' column is the analyzer object text in every row: True (not carried into the clean file; raw file is unchanged)
- Videos sharing a title with another video: 94 rows (47 distinct titles; 45 of them repeat within one channel). Flagged in `duplicate_title`, not removed (they are different videos).

## Videos per channel and date window

| channel   | min                       | max                       |   days_covered |   videos |
|:----------|:--------------------------|:--------------------------|---------------:|---------:|
| CBS News  | 2026-09-03 18:03:34+00:00 | 2026-11-12 05:01:19+00:00 |             69 |     2000 |
| CNN       | 2026-09-28 19:09:27+00:00 | 2026-11-12 10:28:41+00:00 |             44 |     2000 |
| Fox News  | 2026-10-07 01:30:36+00:00 | 2026-11-12 10:00:14+00:00 |             36 |     2000 |
| MSNBC     | 2026-10-15 15:19:54+00:00 | 2026-11-12 10:00:26+00:00 |             27 |     2000 |

## Sentiment label counts per channel (all videos)

| channel   |   positive |   neutral |   negative |
|:----------|-----------:|----------:|-----------:|
| CBS News  |        461 |       768 |        771 |
| CNN       |        442 |       877 |        681 |
| Fox News  |        342 |       766 |        892 |
| MSNBC     |        534 |       787 |        679 |

## Sentiment label share per channel (%)

| channel   |   positive |   neutral |   negative |
|:----------|-----------:|----------:|-----------:|
| CBS News  |       23   |      38.4 |       38.6 |
| CNN       |       22.1 |      43.8 |       34.1 |
| Fox News  |       17.1 |      38.3 |       44.6 |
| MSNBC     |       26.7 |      39.4 |       34   |

Overall neutral share: 40.0% (dropping neutrals would discard this share of the data)

## Topic coverage check (the '28%' result)

- Videos whose title mentions at least one tracked topic: 2,271 of 8,000 = 28.39%

| channel   |   relevant |   total |   pct_relevant |
|:----------|-----------:|--------:|---------------:|
| CBS News  |        508 |    2000 |          25.4  |
| CNN       |        461 |    2000 |          23.05 |
| Fox News  |        445 |    2000 |          22.25 |
| MSNBC     |        857 |    2000 |          42.85 |

## VADER reproducibility check

- Max difference between stored score and recomputed score: 0.000000
- Rows that differ by more than 0.0001: 0

Saved 8,000 rows x 19 columns to data\processed\videos_clean.csv