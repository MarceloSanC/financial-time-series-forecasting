from __future__ import annotations

import argparse
import logging

from pathlib import Path

from src.use_cases.generate_prediction_analysis_plots_use_case import (
    GeneratePredictionAnalysisPlotsUseCase,
)
from src.utils.logging_config import setup_logging
from src.utils.path_resolver import load_data_paths

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate prediction analysis plots (section 9.2/9.3) from analytics silver/gold tables."
    )
    parser.add_argument("--asset", required=False, default=None, help="Optional asset filter (example: AAPL).")
    parser.add_argument(
        "--output-dir",
        required=False,
        default=None,
        help="Optional output directory (default: data/analytics/reports/prediction_analysis_plots[/asset=<ASSET>]).",
    )
    parser.add_argument("--top-n-configs", type=int, default=12, help="Top N configs to include in comparative figures.")
    parser.add_argument("--top-k-features", type=int, default=10, help="Top K features for feature importance/contribution figures.")
    parser.add_argument("--max-timeseries-points", type=int, default=120, help="Max points in OOS timeseries examples.")
    return parser.parse_args()


def _default_output_dir(*, asset: str | None) -> Path:
    base = Path("data/analytics/reports/prediction_analysis_plots")
    if asset:
        return base / f"asset={asset.upper()}"
    return base


def main() -> None:
    setup_logging(logging.INFO)
    args = parse_args()
    paths = load_data_paths()

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir(asset=args.asset)

    result = GeneratePredictionAnalysisPlotsUseCase(
        analytics_gold_dir=paths["analytics_gold"],
        analytics_silver_dir=paths["analytics_silver"],
        output_dir=output_dir,
    ).execute(
        asset=args.asset,
        top_n_configs=args.top_n_configs,
        top_k_features=args.top_k_features,
        max_timeseries_points=args.max_timeseries_points,
    )
    logger.info(
        "Prediction analysis plots generated",
        extra={"output_dir": result.output_dir, "outputs": result.outputs},
    )


if __name__ == "__main__":
    main()
