-- Schema for the news headline sentiment database (SQLite)
-- One row per channel, per video, per sentiment score, and per (video, topic) match.

PRAGMA foreign_keys = ON;

CREATE TABLE channels (
    channel_id          INTEGER PRIMARY KEY,
    channel_name        TEXT NOT NULL UNIQUE,
    youtube_channel_id  TEXT NOT NULL UNIQUE
);

CREATE TABLE videos (
    video_id            TEXT PRIMARY KEY,                 -- the YouTube video ID
    channel_id          INTEGER NOT NULL REFERENCES channels(channel_id),
    title               TEXT NOT NULL,
    published_at        TEXT NOT NULL,                    -- UTC, 'YYYY-MM-DD HH:MM:SS'
    title_length        INTEGER NOT NULL,
    duplicate_title     INTEGER NOT NULL CHECK (duplicate_title IN (0, 1)),
    is_topic_relevant   INTEGER NOT NULL CHECK (is_topic_relevant IN (0, 1))
);

CREATE TABLE sentiment_scores (
    video_id   TEXT PRIMARY KEY REFERENCES videos(video_id),
    compound   REAL NOT NULL CHECK (compound BETWEEN -1 AND 1),   -- VADER score (unchanged)
    label      TEXT NOT NULL CHECK (label IN ('positive', 'neutral', 'negative'))
);

-- A video can match several topics, so topics live in their own table
CREATE TABLE video_topics (
    video_id   TEXT NOT NULL REFERENCES videos(video_id),
    topic      TEXT NOT NULL,
    PRIMARY KEY (video_id, topic)
);

CREATE INDEX idx_videos_channel   ON videos(channel_id);
CREATE INDEX idx_videos_published ON videos(published_at);
CREATE INDEX idx_topics_topic     ON video_topics(topic);
