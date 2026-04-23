from __future__ import annotations

from src.utils.feature_token_parser import (
    normalize_feature_tokens,
    parse_feature_tokens,
)


def test_parse_feature_tokens_splits_csv_and_plus() -> None:
    parsed = parse_feature_tokens("BASELINE_FEATURES+SENTIMENT_FEATURES,close")
    assert parsed == ["BASELINE_FEATURES", "SENTIMENT_FEATURES", "close"]


def test_parse_feature_tokens_deduplicates_preserving_order() -> None:
    parsed = parse_feature_tokens("B+S,B,close+S")
    assert parsed == ["B", "S", "close"]


def test_normalize_feature_tokens_splits_list_entries_with_plus() -> None:
    parsed = normalize_feature_tokens(["BASELINE_FEATURES+TECHNICAL_FEATURES", "SENTIMENT_FEATURES"])
    assert parsed == ["BASELINE_FEATURES", "TECHNICAL_FEATURES", "SENTIMENT_FEATURES"]
