from __future__ import annotations

from src.infrastructure.schemas.feature_validation_schema import (
    FEATURE_ANTI_LEAKAGE_TAGS,
    FEATURE_WARMUP_BARS,
    IMPLEMENTED_FEATURES,
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


def test_catalog_covers_all_implemented_features_for_anti_leakage() -> None:
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
    assert set(IMPLEMENTED_FEATURES) == expected
    assert expected.issubset(set(FEATURE_ANTI_LEAKAGE_TAGS.keys()))


def test_warmup_declared_for_window_based_implemented_features() -> None:
    expected_warmup = {
        "volatility_20d",
        "rsi_14",
        "ema_10",
        "ema_50",
        "ema_100",
        "ema_200",
        "macd",
        "macd_signal",
        "log_return_5d",
        "log_return_1d",
        "log_return_21d",
        "momentum_5d",
        "momentum_21d",
        "momentum_63d",
        "reversal_1d",
        "reversal_5d",
        "drawdown_lookback",
        "amihud_illiquidity_proxy",
        "volume_zscore",
        "volume_spike_flag",
        "volatility_parkinson",
        "volatility_garman_klass",
        "downside_semivolatility",
        "vol_of_vol",
        "volatility_regime",
        "trend_regime",
        "stress_tail_return_flag",
        "sentiment_lag_1",
        "sentiment_lag_3",
        "sentiment_lag_5",
        "sentiment_ema",
        "sentiment_surprise",
        "sentiment_x_volatility",
        "revenue_yoy_growth",
        "net_income_yoy_growth",
    }
    assert expected_warmup.issubset(set(FEATURE_WARMUP_BARS.keys()))
    assert all(FEATURE_WARMUP_BARS[k] > 0 for k in expected_warmup)
