# Legacy code

The original collection and scoring code, kept unchanged for reference.

It fetched the latest 2,000 uploads per channel from the YouTube Data API v3 and scored each video title with NLTK VADER (compound score). It is **not used by the analysis pipeline in `src/`**, which starts from the collected CSVs.

## Files
| File | Purpose |
|---|---|
| `my_code/youtube_api.py` | Downloads video metadata for each channel from the YouTube Data API |
| `my_code/language_api.py` | Scores each title with VADER |
| `my_code/utils.py` | Topic matching (the `relevant` flag) and merging of channel files |
| `my_code/plotting.py` | The original charts |
| `Project.ipynb` | The original analysis (its outputs come from an earlier collection, so its numbers differ from the reported results) |
| `channels.csv`, `topics.csv` | Inputs read by the code: the 4 channels and the topic word lists |
| `sentimentalanalysis.py` | If present: the script that created `channels.csv` (the file name is misleading) |

## Known issues
- The `sentiment` column in the scored output stores an analyzer object instead of a label. The analysis uses only `sentiment_score`.
- Pagination can repeat pages for a channel with fewer videos than the requested limit.
- `plotting.py` uses a seaborn function that no longer exists, and the notebook uses a pandas display option that newer versions reject.

## Running it
To run the collection code you need your own YouTube API key in a file named `google-api-key.txt` (not included).
