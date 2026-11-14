"""
Stage 3 - Build the SQLite database and run the analytical queries
------------------------------------------------------------------
Input:   data/processed/videos_clean.csv  (from Stage 1)
         sql/schema.sql, sql/queries.sql
Output:  data/news.db
         reports/sql_results.md

Run from the project root:   python src/03_build_database.py
"""

from pathlib import Path
import re
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "processed" / "videos_clean.csv"
DB_PATH = ROOT / "data" / "news.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
QUERIES_PATH = ROOT / "sql" / "queries.sql"
REPORT_PATH = ROOT / "reports" / "sql_results.md"

TOPICS = ["trump", "obama", "clinton", "democrats", "republicans", "liberals", "conservatives"]
MAX_ROWS_IN_REPORT = 12


def build_database(df: pd.DataFrame) -> sqlite3.Connection:
    if DB_PATH.exists():
        DB_PATH.unlink()                       # rebuild from scratch every time
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute("PRAGMA foreign_keys = ON")

    # Store timestamps as plain UTC text so SQLite date functions work
    df = df.copy()
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")

    # channels: one row per channel
    channels = (df[["channel", "channel_youtube_id"]].drop_duplicates()
                .sort_values("channel").reset_index(drop=True))
    channels["channel_id"] = channels.index + 1
    conn.executemany(
        "INSERT INTO channels (channel_id, channel_name, youtube_channel_id) VALUES (?, ?, ?)",
        channels[["channel_id", "channel", "channel_youtube_id"]].itertuples(index=False, name=None))

    df = df.merge(channels[["channel", "channel_id"]], on="channel", how="left")

    # videos
    conn.executemany(
        "INSERT INTO videos (video_id, channel_id, title, published_at, title_length, "
        "duplicate_title, is_topic_relevant) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(r.youtube_id, int(r.channel_id), r.title, r.published_at, int(r.title_length),
          int(r.duplicate_title), int(r.relevant)) for r in df.itertuples()])

    # sentiment_scores (VADER compound score is stored exactly as it was)
    conn.executemany(
        "INSERT INTO sentiment_scores (video_id, compound, label) VALUES (?, ?, ?)",
        df[["youtube_id", "sentiment_score", "sentiment_label"]].itertuples(index=False, name=None))

    # video_topics: one row per (video, topic) match
    topic_rows = [(r.youtube_id, t) for r in df.itertuples() for t in TOPICS if getattr(r, t)]
    conn.executemany("INSERT INTO video_topics (video_id, topic) VALUES (?, ?)", topic_rows)

    conn.commit()
    return conn


def check_database(conn: sqlite3.Connection, df: pd.DataFrame) -> list:
    """Fail loudly if the database does not match the CSV."""
    lines = []
    for table in ("channels", "videos", "sentiment_scores", "video_topics"):
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        lines.append(f"- `{table}`: {n:,} rows")
    assert conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0] == len(df)
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == [], "Foreign key violations"
    lines.append("- Foreign key check: no violations")

    # Cross-check SQL against pandas using exact counts (rounded percentages can differ
    # at a .x5 boundary, e.g. 38.55% rounds differently in SQLite and pandas)
    sql_neg = dict(conn.execute(
        "SELECT c.channel_name, SUM(s.label = 'negative') "
        "FROM videos v JOIN channels c USING (channel_id) JOIN sentiment_scores s USING (video_id) "
        "GROUP BY c.channel_name").fetchall())
    pd_neg = df["sentiment_label"].eq("negative").groupby(df["channel"]).sum().astype(int).to_dict()
    assert sql_neg == pd_neg, f"SQL and pandas disagree: {sql_neg} vs {pd_neg}"
    lines.append("- Negative video counts per channel in SQL match pandas exactly")
    return lines


def run_queries(conn: sqlite3.Connection) -> list:
    text = QUERIES_PATH.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^-- Q(\d+): (.*)$", text)   # [preamble, num, title, body, num, title, body, ...]
    out = []
    for i in range(1, len(parts), 3):
        num, title, body = parts[i], parts[i + 1], parts[i + 2]
        skills = re.search(r"(?m)^-- Skills: (.*)$", body)
        sql = "\n".join(l for l in body.splitlines() if not l.startswith("-- ")).strip()
        result = pd.read_sql_query(sql, conn)
        out.append(f"\n## Q{num}: {title}\n")
        if skills:
            out.append(f"*Skills: {skills.group(1)}*\n")
        out.append("```sql\n" + sql + "\n```\n")
        shown = result.head(MAX_ROWS_IN_REPORT)
        out.append(shown.to_markdown(index=False))
        if len(result) > MAX_ROWS_IN_REPORT:
            out.append(f"\n*(showing {MAX_ROWS_IN_REPORT} of {len(result)} rows)*")
        print(f"Q{num}: {title} -> {len(result)} rows")
    return out


def main() -> None:
    df = pd.read_csv(CSV_PATH)
    conn = build_database(df)
    report = ["# SQL Results (Stage 3)\n", "## Database check\n"]
    report += check_database(conn, df)
    report += run_queries(conn)
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    conn.close()
    print(f"\nDatabase: {DB_PATH.relative_to(ROOT)}   Report: {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
