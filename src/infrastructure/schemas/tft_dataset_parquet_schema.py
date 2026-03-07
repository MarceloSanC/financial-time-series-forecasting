from __future__ import annotations

from typing import Dict, List

TFT_DATASET_BASE_COLUMNS: List[str] = [
    "asset_id",
    "timestamp",
    "time_idx",
    "day_of_week",
    "month",
    "target_return",
]

TFT_DATASET_DTYPES: Dict[str, str] = {
    "asset_id": "string",
    "time_idx": "int64",
    "day_of_week": "int64",
    "month": "int64",
    "target_return": "float64",
}

BASELINE_FEATURES: List[str] = [
    "open",
    "high",
    "low",
    "close",
    "volume",
]

TECHNICAL_FEATURES: List[str] = [
    "volatility_20d",
    "rsi_14",
    "candle_body",
    "macd_signal",
    "ema_100",
    "macd",
    "ema_10",
    "ema_200",
    "ema_50",
    "candle_range",
]

SENTIMENT_FEATURES: List[str] = [
    "sentiment_score",
    "news_volume",
    "sentiment_std",
    "has_news",
]

FUNDAMENTAL_FEATURES: List[str] = [
    "revenue",
    "net_income",
    "operating_cash_flow",
    "total_shareholder_equity",
    "total_liabilities",
]

FUNDAMENTAL_DERIVED_FEATURES: List[str] = [
    "net_margin",
    "leverage_ratio",
    "cashflow_efficiency",
    "revenue_yoy_growth",
    "net_income_yoy_growth",
]

MOMENTUM_LIQUIDITY_FEATURES: List[str] = [
    "log_return_1d",
    "log_return_5d",
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
]

VOLATILITY_ROBUST_FEATURES: List[str] = [
    "volatility_parkinson",
    "volatility_garman_klass",
    "downside_semivolatility",
    "vol_of_vol",
]

REGIME_FEATURES: List[str] = [
    "volatility_regime",
    "trend_regime",
    "stress_tail_return_flag",
]

SENTIMENT_DYNAMICS_FEATURES: List[str] = [
    "sentiment_lag_1",
    "sentiment_lag_3",
    "sentiment_lag_5",
    "sentiment_ema",
    "sentiment_surprise",
    "sentiment_x_volatility",
    "sentiment_x_volume",
]

DEFAULT_TFT_FEATURES: List[str] = [
    *BASELINE_FEATURES
]
