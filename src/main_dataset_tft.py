from __future__ import annotations

import argparse
import logging

from pathlib import Path

import pandas as pd
import yaml

from dotenv import load_dotenv

from src.adapters.parquet_candle_repository import ParquetCandleRepository
from src.adapters.parquet_daily_sentiment_repository import (
    ParquetDailySentimentRepository,
)
from src.adapters.parquet_fundamental_repository import ParquetFundamentalRepository
from src.adapters.parquet_technical_indicator_repository import (
    ParquetTechnicalIndicatorRepository,
)
from src.adapters.parquet_tft_dataset_repository import ParquetTFTDatasetRepository
from src.domain.services.data_quality_profiles import get_profile
from src.domain.services.data_quality_reporter import DataQualityReporter
from src.domain.services.dataset_quality_gate import (
    DatasetQualityGate,
    DatasetQualityGateConfig,
)
from src.domain.time.trading_calendar import trading_policy_from_asset_config
from src.infrastructure.schemas.feature_validation_schema import FEATURE_WARMUP_BARS
from src.use_cases.build_tft_dataset_use_case import BuildTFTDatasetUseCase
from src.utils.asset_periods import resolve_data_period
from src.utils.logging_config import setup_logging
from src.utils.path_resolver import load_data_paths

logger = logging.getLogger(__name__)
load_dotenv()


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "data_sources.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_quality_gate_config() -> DatasetQualityGateConfig:
    cfg_path = Path(__file__).parent.parent / "config" / "quality" / "dataset_quality.yaml"
    if not cfg_path.exists():
        return DatasetQualityGateConfig()
    with open(cfg_path, encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    section = payload.get("build_dataset_tft", {})
    if not isinstance(section, dict):
        section = {}
    return DatasetQualityGateConfig(
        max_nan_ratio_per_feature=float(section.get("max_nan_ratio_per_feature", 1.0)),
        min_temporal_coverage_days=int(section.get("min_temporal_coverage_days", 1)),
        require_unique_timestamps=bool(section.get("require_unique_timestamps", True)),
        require_monotonic_timestamps=bool(section.get("require_monotonic_timestamps", True)),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a daily TFT training dataset from processed pipelines"
    )
    parser.add_argument("--asset", required=True, help="Asset symbol (e.g. AAPL)")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing TFT dataset if it exists",
    )
    return parser.parse_args()


def _model_feature_columns(df: pd.DataFrame) -> list[str]:
    excluded = {"asset_id", "timestamp", "time_idx", "day_of_week", "month", "target_return"}
    return [c for c in df.columns if c not in excluded]


def _report_extra_sections(
    *,
    dataset_path: Path,
    quality_gate_config: DatasetQualityGateConfig,
) -> dict:
    try:
        df = pd.read_parquet(dataset_path)
    except Exception:
        return {}
    quality_gate_report = DatasetQualityGate.evaluate(
        df=df,
        feature_cols=_model_feature_columns(df),
        config=quality_gate_config,
        warmup_counts=FEATURE_WARMUP_BARS,
    )
    return {"quality_gate": quality_gate_report}


def main() -> None:
    setup_logging(logging.INFO)

    args = parse_args()
    asset_id = args.asset.strip().upper()
    overwrite = args.overwrite

    config = load_config()
    quality_gate_config = load_quality_gate_config()
    asset_cfg = next(
        (a for a in config.get("assets", []) if str(a.get("symbol", "")).upper() == asset_id),
        None,
    )
    if not asset_cfg:
        raise RuntimeError(f"Asset not found in config/data_sources.yaml: {asset_id}")

    start_date, end_date = resolve_data_period(asset_cfg)
    trading_day_policy = trading_policy_from_asset_config(asset_cfg)

    paths = load_data_paths()

    raw_candles_base_dir = paths["raw_candles"]
    raw_candles_asset_dir = raw_candles_base_dir / asset_id
    if not raw_candles_asset_dir.exists():
        raise FileNotFoundError(
            f"No candle directory found for asset {asset_id}\n"
            f"Expected path: {raw_candles_asset_dir.resolve()}\n"
            "Run main_candles.py first."
        )

    indicators_asset_dir = paths["processed_technical_indicators"] / asset_id
    if not indicators_asset_dir.exists():
        raise FileNotFoundError(
            f"No technical indicators found for asset {asset_id}\n"
            f"Expected path: {indicators_asset_dir.resolve()}\n"
            "Run main_technical_indicators.py first."
        )

    processed_sentiment_daily_dir = paths["processed_sentiment_daily"]
    processed_fundamentals_dir = paths["processed_fundamentals"]
    dataset_tft_dir = paths["dataset_tft"]

    logger.info(
        "Starting TFT dataset build",
        extra={
            "asset": asset_id,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "candles_dir": str(raw_candles_asset_dir.resolve()),
            "indicators_dir": str(indicators_asset_dir.resolve()),
            "sentiment_daily_dir": str(processed_sentiment_daily_dir.resolve()),
            "fundamentals_dir": str(processed_fundamentals_dir.resolve()),
            "dataset_dir": str(dataset_tft_dir.resolve()),
            "overwrite": overwrite,
            "open_hour": trading_day_policy.open_hour.isoformat(),
            "close_hour": trading_day_policy.close_hour.isoformat(),
            "weekends": trading_day_policy.weekends,
            "quality_gate_max_nan_ratio_per_feature": quality_gate_config.max_nan_ratio_per_feature,
            "quality_gate_min_temporal_coverage_days": quality_gate_config.min_temporal_coverage_days,
            "quality_gate_require_unique_timestamps": quality_gate_config.require_unique_timestamps,
            "quality_gate_require_monotonic_timestamps": quality_gate_config.require_monotonic_timestamps,
        },
    )

    candle_repository = ParquetCandleRepository(output_dir=raw_candles_base_dir)
    indicator_repository = ParquetTechnicalIndicatorRepository(
        output_dir=indicators_asset_dir
    )
    daily_sentiment_repository = ParquetDailySentimentRepository(
        output_dir=processed_sentiment_daily_dir
    )
    fundamental_repository = ParquetFundamentalRepository(
        output_dir=processed_fundamentals_dir
    )
    tft_dataset_repository = ParquetTFTDatasetRepository(output_dir=dataset_tft_dir)

    dataset_path = dataset_tft_dir / asset_id / f"dataset_tft_{asset_id}.parquet"
    if dataset_path.exists() and not overwrite:
        logger.info(
            "TFT dataset skipped (already exists). Use --overwrite to rebuild.",
            extra={"asset": asset_id, "path": str(dataset_path.resolve())},
        )
        profile = get_profile("dataset_tft")
        if not DataQualityReporter.report_exists(dataset_path.parent / "reports", profile.prefix):
            DataQualityReporter.report_from_parquet(
                dataset_path,
                **profile.to_kwargs(),
                extra_sections=_report_extra_sections(
                    dataset_path=dataset_path,
                    quality_gate_config=quality_gate_config,
                ),
            )
        return

    use_case = BuildTFTDatasetUseCase(
        candle_repository=candle_repository,
        indicator_repository=indicator_repository,
        daily_sentiment_repository=daily_sentiment_repository,
        fundamental_repository=fundamental_repository,
        tft_dataset_repository=tft_dataset_repository,
        trading_day_policy=trading_day_policy,
        quality_gate_config=quality_gate_config,
    )

    result = use_case.execute(
        asset_id=asset_id,
        start_date=start_date,
        end_date=end_date,
    )
    if dataset_path.exists():
        profile = get_profile("dataset_tft")
        DataQualityReporter.report_from_parquet(
            dataset_path,
            **profile.to_kwargs(),
            extra_sections=_report_extra_sections(
                dataset_path=dataset_path,
                quality_gate_config=quality_gate_config,
            ),
        )

    logger.info(
        "TFT dataset completed",
        extra={
            "asset": result.asset_id,
            "rows": result.rows,
            "start": result.start.isoformat(),
            "end": result.end.isoformat(),
            "nulls": result.nulls,
        },
    )


if __name__ == "__main__":
    main()
