from __future__ import annotations

from src.infrastructure.schemas.feature_registry import (
    FEATURE_REGISTRY,
    feature_registry_hash,
    get_feature_spec,
    list_feature_specs,
)
from src.infrastructure.schemas.tft_dataset_parquet_schema import (
    BASELINE_FEATURES,
    FUNDAMENTAL_DERIVED_FEATURES,
    FUNDAMENTAL_FEATURES,
    MOMENTUM_LIQUIDITY_FEATURES,
    REGIME_FEATURES,
    SENTIMENT_DYNAMICS_FEATURES,
    SENTIMENT_FEATURES,
    TECHNICAL_FEATURES,
    VOLATILITY_ROBUST_FEATURES,
)


def test_registry_covers_all_current_dataset_features() -> None:
    expected = set(
        BASELINE_FEATURES
        + TECHNICAL_FEATURES
        + SENTIMENT_FEATURES
        + FUNDAMENTAL_FEATURES
        + FUNDAMENTAL_DERIVED_FEATURES
        + MOMENTUM_LIQUIDITY_FEATURES
        + VOLATILITY_ROBUST_FEATURES
        + REGIME_FEATURES
        + SENTIMENT_DYNAMICS_FEATURES
    )
    assert set(FEATURE_REGISTRY.keys()) == expected


def test_all_specs_have_required_contract_fields() -> None:
    for spec in FEATURE_REGISTRY.values():
        assert spec.name
        assert spec.group in {"baseline", "technical", "sentiment", "fundamental", "derived"}
        assert isinstance(spec.source_cols, tuple)
        assert spec.formula_desc
        assert spec.anti_leakage_tag
        assert isinstance(spec.warmup_count, int)
        assert spec.warmup_count >= 0
        assert spec.dtype


def test_helpers_return_consistent_results() -> None:
    ema = get_feature_spec("ema_200")
    assert ema.group == "technical"
    assert ema.warmup_count == 200

    technical = list_feature_specs(group="technical")
    assert any(s.name == "ema_200" for s in technical)

    h1 = feature_registry_hash()
    h2 = feature_registry_hash()
    assert h1 == h2
    assert len(h1) == 64
