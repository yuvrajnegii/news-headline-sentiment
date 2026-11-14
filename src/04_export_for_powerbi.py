"""
Stage 5 - Export clean tables for Power BI
------------------------------------------
Input:   data/news.db  (built by src/03_build_database.py)
Output:  powerbi/data/dim_channel.csv
         powerbi/data/fact_videos.csv
         powerbi/data/video_topics.csv
         powerbi/data/stat_pairwise.csv   (results of the Stage 4 tests, for the dashboard)

Run from the project root:   python src/05_export_for_powerbi.py
"""

import importlib.util
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "news.db"
OUT_DIR = ROOT / "powerbi" / "data"

ORDER = ["CBS News", "CNN", "Fox News", "MSNBC"]
COLORS = {"Fox News": "#5975a4", "CNN": "#b55d60", "MSNBC": "#5f9e6e", "CBS News": "#666666"}


def load_stage4_functions():
    """Re-use the tested statistics functions from src/04_statistics.py."""
    spec = importlib.util.spec_from_file_location("stats04", ROOT / "src" / "04_statistics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit("data/news.db not found. Run: python src/03_build_database.py")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # ---- dim_channel ---------------------------------------------------
    channels = pd.read_sql_query("SELECT channel_id, channel_name FROM channels", conn)
    channels["color_hex"] = channels["channel_name"].map(COLORS)
    channels["sort_order"] = channels["channel_name"].map({c: i + 1 for i, c in enumerate(ORDER)})
    channels = channels.sort_values("sort_order")

    # ---- fact_videos (one row per video) ---------------------------------
    fact = pd.read_sql_query(
        """
        SELECT v.video_id, v.channel_id, c.channel_name, v.title, v.published_at,
               date(v.published_at) AS published_date,
               s.compound AS sentiment_score, s.label AS sentiment_label,
               v.is_topic_relevant, v.duplicate_title
        FROM videos v
        JOIN channels c USING (channel_id)
        JOIN sentiment_scores s USING (video_id)
        """, conn)

    # Time-matched window flag (same rule as Stage 2 / Stage 4 / SQL Q8)
    ts = pd.to_datetime(fact["published_at"])
    first = ts.groupby(fact["channel_name"]).min().max().normalize() + pd.Timedelta(days=1)
    last = ts.groupby(fact["channel_name"]).max().min().normalize()
    fact["in_time_matched_window"] = ((ts >= first) & (ts < last)).astype(int)
    fact_out = fact.drop(columns=["channel_name"])      # channel name lives only in dim_channel

    # ---- video_topics ----------------------------------------------------
    topics = pd.read_sql_query("SELECT video_id, topic FROM video_topics", conn)

    # ---- stat_pairwise (Stage 4 results as a table) ----------------------
    s4 = load_stage4_functions()
    frames = []
    for name, data in (("Full snapshot", fact), ("Time-matched window", fact[fact["in_time_matched_window"] == 1])):
        res = s4.pairwise_mwu(data, ORDER, group_col="channel_name")
        res.insert(0, "dataset", name)
        frames.append(res)
    stats_df = pd.concat(frames, ignore_index=True)
    stats_df["comparison"] = stats_df["A"] + " vs " + stats_df["B"]
    stats_out = stats_df[["dataset", "comparison", "mean_A - mean_B", "P(A > B)", "cliffs_delta",
                          "p_holm", "significant", "effect_size"]].copy()
    stats_out.columns = ["dataset", "comparison", "mean_difference", "prob_A_higher",
                         "cliffs_delta", "p_holm", "significant", "effect_size"]
    stats_out = stats_out.round({"mean_difference": 4, "prob_A_higher": 4, "cliffs_delta": 4, "p_holm": 6})

    # ---- save ------------------------------------------------------------
    channels.to_csv(OUT_DIR / "dim_channel.csv", index=False, encoding="utf-8")
    fact_out.to_csv(OUT_DIR / "fact_videos.csv", index=False, encoding="utf-8")
    topics.to_csv(OUT_DIR / "video_topics.csv", index=False, encoding="utf-8")
    stats_out.to_csv(OUT_DIR / "stat_pairwise.csv", index=False, encoding="utf-8")

    # ---- checks printed for you -------------------------------------------
    print(f"dim_channel:   {len(channels)} rows")
    print(f"fact_videos:   {len(fact_out):,} rows  (time-matched window flag = 1 for "
          f"{int(fact_out['in_time_matched_window'].sum()):,} rows)")
    print(f"video_topics:  {len(topics):,} rows")
    print(f"stat_pairwise: {len(stats_out)} rows")
    print("\nPower BI check values:")
    print(f"  overall mean sentiment: {fact['sentiment_score'].mean():.3f}")
    print(f"  overall % positive / neutral / negative: "
          + " / ".join(f"{100 * (fact['sentiment_label'] == l).mean():.1f}" for l in ("positive", "neutral", "negative")))
    print("  negative % by channel:",
          (100 * fact["sentiment_label"].eq("negative").groupby(fact["channel_name"]).mean()).round(1).to_dict())
    conn.close()


if __name__ == "__main__":
    main()
