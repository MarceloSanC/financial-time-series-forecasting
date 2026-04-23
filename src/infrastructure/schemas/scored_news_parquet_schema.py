from __future__ import annotations

SCORED_NEWS_PARQUET_COLUMNS: list[str] = [
    "asset_id",
    "article_id",
    "published_at",
    "sentiment_score",
    "confidence",
    "model_name",
]

# pandas dtypes for stable parquet writing
# NOTE: published_at handled separately as datetime64[ns, UTC]
SCORED_NEWS_PARQUET_DTYPES: dict[str, str] = {
    "asset_id": "string",
    "article_id": "string",
    "sentiment_score": "float64",
    "confidence": "Float64",
    "model_name": "string",
}
