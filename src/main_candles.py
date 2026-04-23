# src/main_candles.py
import argparse
import logging

from pathlib import Path

import yaml

from src.adapters.parquet_candle_repository import ParquetCandleRepository
from src.adapters.yfinance_candle_fetcher import YFinanceCandleFetcher
from src.domain.services.data_quality_profiles import get_profile
from src.domain.services.data_quality_reporter import DataQualityReporter
from src.use_cases.fetch_candles_use_case import FetchCandlesUseCase
from src.utils.asset_periods import resolve_data_period
from src.utils.logging_config import setup_logging
from src.utils.path_resolver import load_data_paths

logger = logging.getLogger(__name__)


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "data_sources.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    setup_logging(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, help="Ex: AAPL")
    args = parser.parse_args()

    asset_id = args.asset
    symbol = asset_id.split(".")[0].upper()

    config = load_config()
    asset_config = next(
        (a for a in config["assets"] if a["symbol"] == asset_id), None
    )
    if not asset_config:
        raise ValueError(
            f"Ativo {asset_id} não encontrado em config/data_sources.yaml"
        )

    # ---------- Paths (ORQUESTRADOR decide estrutura) ----------
    paths = load_data_paths()

    # base: data/raw/market/candles
    candles_base_dir = paths["raw_candles"]
    candles_base_dir.mkdir(parents=True, exist_ok=True)

    # ---------- Adapters ----------
    fetcher = YFinanceCandleFetcher()

    repository = ParquetCandleRepository(
        output_dir=candles_base_dir
    )

    use_case = FetchCandlesUseCase(fetcher, repository)

    # ---------- Execute ----------
    start, end = resolve_data_period(asset_config)

    logger.info(
        "Starting candles pipeline",
        extra={
            "asset": asset_id,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
    )

    fetched, existing = use_case.execute(asset_id, start, end)
    new_rows = max(fetched - existing, 0)

    # Data quality report (snapshot)
    candles_path = candles_base_dir / symbol / f"candles_{symbol}_1d.parquet"
    if candles_path.exists():
        profile = get_profile("candles")
        reports_dir = candles_path.parent / "reports"
        if fetched > 0 or not DataQualityReporter.report_exists(reports_dir, profile.prefix):
            DataQualityReporter.report_from_parquet(candles_path, **profile.to_kwargs())

    if fetched == 0:
        logger.info(
            "Candles pipeline skipped (no new data)",
            extra={"asset": asset_id, "start": start.isoformat(), "end": end.isoformat()},
        )
    else:
        logger.info(
            "Pipeline de candles finalizado",
            extra={
                "asset": asset_id,
                "fetched": fetched,
                "existing_rows": existing,
                "new_rows": new_rows,
            },
        )


if __name__ == "__main__":
    main()
