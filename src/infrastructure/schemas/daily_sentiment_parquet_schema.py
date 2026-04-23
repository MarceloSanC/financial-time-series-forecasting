from __future__ import annotations

DAILY_SENTIMENT_PARQUET_COLUMNS: list[str] = [
    "asset_id",
    "day",
    "sentiment_score",
    "n_articles",
    "sentiment_std",
]

# pandas dtypes for stable parquet writing
# NOTE: day handled separately as datetime64[ns, UTC]
DAILY_SENTIMENT_PARQUET_DTYPES: dict[str, str] = {
    "asset_id": "string",
    "sentiment_score": "float64",
    "n_articles": "int64",
    "sentiment_std": "Float64",
}
