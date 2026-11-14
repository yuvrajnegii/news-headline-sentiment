-- Analytical queries. Each block starts with "-- Q<number>: title".
-- Run by src/03_build_database.py, which writes the results to reports/sql_results.md

-- Q1: Which channel has the highest percentage of negative headlines?
-- Skills: JOIN, GROUP BY, CASE WHEN, RANK() window function
SELECT c.channel_name,
       COUNT(*) AS videos,
       SUM(CASE WHEN s.label = 'negative' THEN 1 ELSE 0 END) AS negative_videos,
       ROUND(100.0 * SUM(CASE WHEN s.label = 'negative' THEN 1 ELSE 0 END) / COUNT(*), 1) AS negative_pct,
       RANK() OVER (ORDER BY 1.0 * SUM(CASE WHEN s.label = 'negative' THEN 1 ELSE 0 END) / COUNT(*) DESC) AS rank_most_negative
FROM videos v
JOIN channels c USING (channel_id)
JOIN sentiment_scores s USING (video_id)
GROUP BY c.channel_name
ORDER BY negative_pct DESC;

-- Q2: How does the positive / neutral / negative split vary by channel?
-- Skills: GROUP BY, CASE WHEN, aggregate ratio
SELECT c.channel_name,
       ROUND(100.0 * SUM(s.label = 'positive') / COUNT(*), 1) AS positive_pct,
       ROUND(100.0 * SUM(s.label = 'neutral')  / COUNT(*), 1) AS neutral_pct,
       ROUND(100.0 * SUM(s.label = 'negative') / COUNT(*), 1) AS negative_pct,
       ROUND(1.0 * SUM(s.label = 'positive') / SUM(s.label = 'negative'), 2) AS positive_to_negative_ratio
FROM videos v
JOIN channels c USING (channel_id)
JOIN sentiment_scores s USING (video_id)
GROUP BY c.channel_name
ORDER BY positive_pct DESC;

-- Q3: Average, minimum, maximum and spread of the compound score per channel
-- Skills: aggregate functions (SQLite has no STDDEV, so population SD is computed by hand)
SELECT c.channel_name,
       COUNT(*) AS videos,
       ROUND(AVG(s.compound), 3) AS mean_score,
       ROUND(MIN(s.compound), 3) AS min_score,
       ROUND(MAX(s.compound), 3) AS max_score,
       ROUND(SQRT(AVG(s.compound * s.compound) - AVG(s.compound) * AVG(s.compound)), 3) AS std_dev
FROM videos v
JOIN channels c USING (channel_id)
JOIN sentiment_scores s USING (video_id)
GROUP BY c.channel_name
ORDER BY mean_score;

-- Q4: How much data does each channel have, and over what period?
-- Skills: MIN/MAX, date arithmetic with julianday
SELECT c.channel_name,
       COUNT(*) AS videos,
       MIN(v.published_at) AS first_video,
       MAX(v.published_at) AS last_video,
       ROUND(julianday(MAX(v.published_at)) - julianday(MIN(v.published_at)), 1) AS days_covered,
       ROUND(COUNT(*) / (julianday(MAX(v.published_at)) - julianday(MIN(v.published_at))), 1) AS videos_per_day
FROM videos v
JOIN channels c USING (channel_id)
GROUP BY c.channel_name
ORDER BY days_covered;

-- Q5: What share of each channel's headlines mention a tracked political topic?
-- Skills: JOIN, GROUP BY, aggregate on a flag column
SELECT c.channel_name,
       COUNT(*) AS videos,
       SUM(v.is_topic_relevant) AS topic_videos,
       ROUND(100.0 * SUM(v.is_topic_relevant) / COUNT(*), 2) AS topic_pct
FROM videos v
JOIN channels c USING (channel_id)
GROUP BY c.channel_name
ORDER BY topic_pct DESC;

-- Q6: Average sentiment by channel and topic (only groups with at least 30 videos)
-- Skills: 3-table JOIN, GROUP BY two columns, HAVING to avoid tiny groups
SELECT c.channel_name,
       t.topic,
       COUNT(*) AS videos,
       ROUND(AVG(s.compound), 3) AS mean_score
FROM video_topics t
JOIN videos v USING (video_id)
JOIN channels c USING (channel_id)
JOIN sentiment_scores s USING (video_id)
GROUP BY c.channel_name, t.topic
HAVING COUNT(*) >= 30
ORDER BY t.topic, mean_score;

-- Q7: Are topic headlines more or less negative than other headlines, per channel?
-- Skills: CASE WHEN used to build a group label, GROUP BY
SELECT c.channel_name,
       CASE WHEN v.is_topic_relevant = 1 THEN 'topic' ELSE 'other' END AS headline_group,
       COUNT(*) AS videos,
       ROUND(AVG(s.compound), 3) AS mean_score,
       ROUND(100.0 * SUM(s.label = 'negative') / COUNT(*), 1) AS negative_pct
FROM videos v
JOIN channels c USING (channel_id)
JOIN sentiment_scores s USING (video_id)
GROUP BY c.channel_name, headline_group
ORDER BY c.channel_name, headline_group;

-- Q8: Time-matched comparison (only whole days when all four channels have data)
-- Skills: CTEs, subquery logic, CROSS JOIN, date functions
WITH span AS (
    SELECT channel_id, MIN(published_at) AS first_ts, MAX(published_at) AS last_ts
    FROM videos
    GROUP BY channel_id
),
bounds AS (
    SELECT date(MAX(first_ts), '+1 day') AS start_day,   -- first full day every channel has
           date(MIN(last_ts))            AS end_day      -- exclusive: the last day is partial
    FROM span
)
SELECT c.channel_name,
       COUNT(*) AS videos,
       ROUND(AVG(s.compound), 3) AS mean_score,
       ROUND(100.0 * SUM(s.label = 'negative') / COUNT(*), 1) AS negative_pct
FROM videos v
JOIN channels c USING (channel_id)
JOIN sentiment_scores s USING (video_id)
CROSS JOIN bounds b
WHERE date(v.published_at) >= b.start_day AND date(v.published_at) < b.end_day
GROUP BY c.channel_name
ORDER BY mean_score;

-- Q9: The 3 most negative headlines of each channel
-- Skills: ROW_NUMBER() window function with PARTITION BY, subquery
SELECT channel_name, compound, title
FROM (
    SELECT c.channel_name, s.compound, v.title,
           ROW_NUMBER() OVER (PARTITION BY c.channel_name ORDER BY s.compound ASC) AS rn
    FROM videos v
    JOIN channels c USING (channel_id)
    JOIN sentiment_scores s USING (video_id)
)
WHERE rn <= 3
ORDER BY channel_name, rn;

-- Q10: Which channels are below the overall average sentiment, and by how much?
-- Skills: scalar subquery, comparison to a global value
SELECT c.channel_name,
       ROUND(AVG(s.compound), 3) AS channel_mean,
       ROUND((SELECT AVG(compound) FROM sentiment_scores), 3) AS overall_mean,
       ROUND(AVG(s.compound) - (SELECT AVG(compound) FROM sentiment_scores), 3) AS difference,
       CASE WHEN AVG(s.compound) < (SELECT AVG(compound) FROM sentiment_scores)
            THEN 'below overall' ELSE 'above overall' END AS position
FROM videos v
JOIN channels c USING (channel_id)
JOIN sentiment_scores s USING (video_id)
GROUP BY c.channel_name
ORDER BY difference;

-- Q11: 7-day rolling average sentiment per channel (latest days first, time-matched window)
-- Skills: CTEs, SUM() OVER with a ROWS frame, PARTITION BY
WITH span AS (
    SELECT channel_id, MIN(published_at) AS first_ts, MAX(published_at) AS last_ts
    FROM videos GROUP BY channel_id
),
bounds AS (
    SELECT date(MAX(first_ts), '+1 day') AS start_day, date(MIN(last_ts)) AS end_day FROM span
),
daily AS (
    SELECT c.channel_name, date(v.published_at) AS day,
           SUM(s.compound) AS score_sum, COUNT(*) AS n
    FROM videos v
    JOIN channels c USING (channel_id)
    JOIN sentiment_scores s USING (video_id)
    CROSS JOIN bounds b
    WHERE date(v.published_at) >= b.start_day AND date(v.published_at) < b.end_day
    GROUP BY c.channel_name, date(v.published_at)
),
rolling AS (
    SELECT channel_name, day,
           SUM(score_sum) OVER w AS sum7,
           SUM(n)         OVER w AS n7,
           COUNT(*)       OVER w AS days_in_window
    FROM daily
    WINDOW w AS (PARTITION BY channel_name ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
)
SELECT day, channel_name, ROUND(sum7 / n7, 3) AS rolling_7day_mean, n7 AS videos_in_window
FROM rolling
WHERE days_in_window = 7
ORDER BY day DESC, channel_name;

-- Q12: Which headlines appear more than once? (data quality check)
-- Skills: GROUP BY, HAVING, GROUP_CONCAT
SELECT v.title,
       COUNT(*) AS times_posted,
       COUNT(DISTINCT v.channel_id) AS channels,
       GROUP_CONCAT(DISTINCT c.channel_name) AS channel_names
FROM videos v
JOIN channels c USING (channel_id)
GROUP BY v.title
HAVING COUNT(*) > 1
ORDER BY times_posted DESC, v.title;
