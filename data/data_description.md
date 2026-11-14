# Data

The data files are **not committed** to this repository. They come from the YouTube Data API v3, and YouTube's developer policies (as far as I understand them) require stored API data to be refreshed or deleted within 30 days. Check the current policy before publishing any API data.

## What the pipeline expects

`data/raw/videos.csv` (8,000 rows, one per video; collected 12 Nov 2026, latest 2,000 uploads per channel)

| Column | Meaning |
|---|---|
| youtube_id | Video ID (unique) |
| title | Video title (the text that is scored) |
| description | Video description (not used in the analysis) |
| published_at | Upload time (UTC) |
| channel_youtube_id, channel | Channel ID and name (CBS News, CNN, Fox News, MSNBC) |
| relevant | True if the title mentions at least one tracked topic |
| obama, clinton, trump, democrats, republicans, liberals, conservatives | True if the title mentions that topic |

`data/raw/sentiments.csv` (8,000 rows)

| Column | Meaning |
|---|---|
| youtube_id | Video ID |
| sentiment | Not usable (a bug in the original code stored the analyzer object here) |
| sentiment_score | VADER compound score of the title, from -1 to 1 |

## Created by the pipeline
`data/processed/videos_clean.csv` (Stage 1) and `data/news.db` (Stage 3).
