# Architecture

```mermaid
flowchart LR
    A["YouTube Data API v3<br/>collected 12 Nov 2026"] --> B[("Raw CSVs<br/>videos + VADER scores")]
    B --> C["01 Clean and validate"]
    C --> D[("videos_clean.csv")]
    D --> F["03 SQLite database<br/>+ 12 SQL queries"]
    D --> G["04 Statistics"]
    F --> H["05 Export tables"]
    G --> H
    H --> I["Power BI dashboard"]
    F --> J["Findings and<br/>recommendations"]
    G --> J
    I --> J
```

| Step | Script / file | Input | Output |
|---|---|---|---|
| Collection (legacy) | `legacy/my_code/youtube_api.py`, `language_api.py` | `channels.csv`, `topics.csv` | raw CSVs with VADER scores |
| Clean | `src/01_clean_data.py` | raw CSVs | `data/processed/videos_clean.csv`, `reports/data_quality_report.md` |
| SQL | `src/02_build_database.py`, `sql/*.sql` | `videos_clean.csv` | `data/news.db`, `reports/sql_results.md` (local) |
| Statistics | `src/03_statistics.py` | `videos_clean.csv` | `reports/statistics_results.md`, `figures/08_mean_ci.png` |
| Dashboard | `src/04_export_for_powerbi.py` | `news.db` | `powerbi/data/*.csv` for Power BI |
| Findings | `docs/findings.md` | SQL, statistics and dashboard results | written findings and recommendations |

Script numbers keep their original names (there is no `02`), so the run order is 01, 03, 04, 05.
