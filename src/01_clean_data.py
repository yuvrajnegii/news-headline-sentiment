"""
Stage 1 - Data cleaning and validation
--------------------------------------
Input  (never modified):  data/raw/videos.csv, data/raw/sentiments.csv
Output:                   data/processed/videos_clean.csv
                          reports/data_quality_report.md

What this script does:
  1. Loads the two raw files and checks they match (same 8,000 video IDs).
  2. Merges them into one table (all original video columns are kept).
  3. Adds sentiment_label (positive / neutral / negative) using the
     standard VADER cut-offs on the EXISTING compound score.
  4. Flags (does NOT delete) videos whose title appears more than once.
  5. Verifies the "about 28%" topic-coverage result and writes a report.

Run from the project root:   python src/01_clean_data.py
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_VIDEOS = ROOT / "data" / "raw" / "videos.csv"
RAW_SENTIMENTS = ROOT / "data" / "raw" / "sentiments.csv"
OUT_CSV = ROOT / "data" / "processed" / "videos_clean.csv"
OUT_REPORT = ROOT / "reports" / "data_quality_report.md"

# Standard VADER thresholds (from the VADER documentation):
#   compound >=  0.05 -> positive
#   compound <= -0.05 -> negative
#   otherwise         -> neutral
POS_CUTOFF = 0.05
NEG_CUTOFF = -0.05


def label_sentiment(score: float) -> str:
    if score >= POS_CUTOFF:
        return "positive"
    if score <= NEG_CUTOFF:
        return "negative"
    return "neutral"


def main() -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = []  # report lines

    def log(text: str = "") -> None:
        print(text)
        lines.append(text)

    # ---- 1. Load -------------------------------------------------------
    videos = pd.read_csv(RAW_VIDEOS)
    sentiments = pd.read_csv(RAW_SENTIMENTS)
    log("# Data Quality Report (Stage 1)\n")
    log(f"- Raw videos file: {len(videos):,} rows, {videos.shape[1]} columns")
    log(f"- Raw sentiments file: {len(sentiments):,} rows, {sentiments.shape[1]} columns")

    # ---- 2. Integrity checks (fail loudly if something is wrong) -------
    assert videos["youtube_id"].is_unique, "Duplicate youtube_id in videos.csv"
    assert sentiments["youtube_id"].is_unique, "Duplicate youtube_id in sentiments.csv"
    assert set(videos["youtube_id"]) == set(sentiments["youtube_id"]), \
        "Video IDs in the two files do not match"
    log("- Duplicate youtube_id: 0 in both files; both files contain exactly the same IDs")

    missing = videos.isna().sum()
    missing = missing[missing > 0]
    log(f"- Columns with missing values in videos.csv: {len(missing)}")
    log(f"- Empty or very short titles (< 3 chars): "
        f"{(videos['title'].str.strip().str.len() < 3).sum()}")

    # The 'sentiment' column written by the old code holds the text
    # '<nltk...SentimentIntensityAnalyzer object ...>' (a bug), so it carries
    # no information. We keep only the score. The raw file is untouched.
    junk = sentiments["sentiment"].astype(str).str.contains("SentimentIntensityAnalyzer").all()
    log(f"- Old 'sentiment' column is the analyzer object text in every row: {junk} "
        f"(not carried into the clean file; raw file is unchanged)")

    # ---- 3. Merge ------------------------------------------------------
    df = videos.merge(
        sentiments[["youtube_id", "sentiment_score"]],
        on="youtube_id",
        how="left",
        validate="one_to_one",
    )
    assert len(df) == len(videos) and df["sentiment_score"].notna().all()
    assert df["sentiment_score"].between(-1, 1).all(), "Score outside [-1, 1]"

    # ---- 4. New columns (original columns are not changed) -------------
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True)
    df["published_date"] = df["published_at"].dt.date
    df["sentiment_label"] = df["sentiment_score"].apply(label_sentiment)
    df["title_length"] = df["title"].str.len()
    df["duplicate_title"] = df.duplicated(subset="title", keep=False)

    n_dup_rows = int(df["duplicate_title"].sum())
    n_dup_titles = df.loc[df["duplicate_title"], "title"].nunique()
    same_channel = (
        df[df["duplicate_title"]].groupby("title")["channel"].nunique().eq(1).sum()
    )
    log(f"- Videos sharing a title with another video: {n_dup_rows} rows "
        f"({n_dup_titles} distinct titles; {same_channel} of them repeat within one channel). "
        f"Flagged in `duplicate_title`, not removed (they are different videos).")

    # ---- 5. Distribution tables ---------------------------------------
    log("\n## Videos per channel and date window\n")
    window = df.groupby("channel")["published_at"].agg(["min", "max"])
    window["days_covered"] = (window["max"] - window["min"]).dt.days
    window["videos"] = df.groupby("channel").size()
    log(window.to_markdown())

    log("\n## Sentiment label counts per channel (all videos)\n")
    counts = pd.crosstab(df["channel"], df["sentiment_label"])
    counts = counts[["positive", "neutral", "negative"]]
    log(counts.to_markdown())
    log("\n## Sentiment label share per channel (%)\n")
    log((pd.crosstab(df["channel"], df["sentiment_label"], normalize="index")[
        ["positive", "neutral", "negative"]] * 100).round(1).to_markdown())

    overall_neutral = (df["sentiment_label"] == "neutral").mean() * 100
    log(f"\nOverall neutral share: {overall_neutral:.1f}% "
        f"(dropping neutrals would discard this share of the data)")

    # ---- 6. Verify the topic-coverage ("28%") result -------------------
    n_rel = int(df["relevant"].sum())
    log("\n## Topic coverage check (the '28%' result)\n")
    log(f"- Videos whose title mentions at least one tracked topic: "
        f"{n_rel:,} of {len(df):,} = {100 * n_rel / len(df):.2f}%\n")
    cov = df.groupby("channel")["relevant"].agg(relevant="sum", total="size")
    cov["pct_relevant"] = (100 * cov["relevant"] / cov["total"]).round(2)
    log(cov.to_markdown())

    # ---- 7. Optional: confirm scores match VADER on titles -------------
    try:
        from nltk.sentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        recomputed = df["title"].apply(lambda t: sia.polarity_scores(t)["compound"])
        diff = (recomputed - df["sentiment_score"]).abs()
        log("\n## VADER reproducibility check\n")
        log(f"- Max difference between stored score and recomputed score: {diff.max():.6f}")
        log(f"- Rows that differ by more than 0.0001: {(diff > 1e-4).sum()}")
    except Exception as exc:  # nltk missing or lexicon not downloaded
        log(f"\n(VADER reproducibility check skipped: {type(exc).__name__})")

    # ---- 8. Save -------------------------------------------------------
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    log(f"\nSaved {len(df):,} rows x {df.shape[1]} columns to {OUT_CSV.relative_to(ROOT)}")
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
