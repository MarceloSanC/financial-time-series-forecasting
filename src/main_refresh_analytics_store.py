from __future__ import annotations

import argparse
import logging

from src.use_cases.generate_prediction_analysis_plots_use_case import (
    GeneratePredictionAnalysisPlotsUseCase,
)
from src.use_cases.refresh_analytics_store_use_case import RefreshAnalyticsStoreUseCase
from src.use_cases.validate_analytics_quality_use_case import (
    ValidateAnalyticsQualityUseCase,
)
from src.utils.logging_config import setup_logging
from src.utils.path_resolver import load_data_paths

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh analytics gold tables from analytics silver tables.")
    parser.add_argument(
        "--fail-on-quality",
        action="store_true",
        help="Fail process with non-zero exit code when analytics quality checks fail.",
    )
    parser.add_argument("--min-samples-train", type=int, default=1)
    parser.add_argument("--min-samples-val", type=int, default=1)
    parser.add_argument("--min-samples-test", type=int, default=1)
    parser.add_argument(
        "--skip-prediction-plots",
        action="store_true",
        help="Skip generation of section 9.2/9.3 prediction analysis plots after gold refresh.",
    )
    parser.add_argument(
        "--plots-asset",
        type=str,
        default=None,
        help="Optional asset filter for plot generation (example: AAPL).",
    )
    parser.add_argument(
        "--plots-output-dir",
        type=str,
        default=None,
        help=(
            "Optional output directory for prediction analysis plots. "
            "Default: data/analytics/reports/prediction_analysis_plots[/asset=<ASSET>]"
        ),
    )
    parser.add_argument(
        "--plots-scope-csv",
        type=str,
        default=None,
        help=(
            "Optional CSV path to scope plot generation to a frozen candidate set "
            "(supports columns run_id and/or feature_set_name+config_signature and/or config_label)."
        ),
    )
    parser.add_argument(
        "--plots-scope-sweep-prefixes",
        type=str,
        default=None,
        help=(
            "Optional comma-separated sweep id prefixes used to scope plot generation "
            "(example: 0_2_2_)."
        ),
    )
    return parser.parse_args()


def main() -> None:
    setup_logging(logging.INFO)
    args = parse_args()
    paths = load_data_paths()

    use_case = RefreshAnalyticsStoreUseCase(
        analytics_silver_dir=paths["analytics_silver"],
        analytics_gold_dir=paths["analytics_gold"],
    )
    result = use_case.execute()
    logger.info(
        "Analytics gold refresh completed",
        extra={
            "gold_dir": result.gold_dir,
            "outputs": result.outputs,
        },
    )

    quality_result = ValidateAnalyticsQualityUseCase(
        analytics_silver_dir=paths["analytics_silver"],
        analytics_gold_dir=paths["analytics_gold"],
        min_samples_train=args.min_samples_train,
        min_samples_val=args.min_samples_val,
        min_samples_test=args.min_samples_test,
    ).execute()
    failed_checks = [c for c in quality_result.checks if not bool(c["passed"])]
    logger.info(
        "Analytics quality validation completed",
        extra={
            "passed": quality_result.passed,
            "failed_checks": failed_checks,
            "total_checks": len(quality_result.checks),
        },
    )

    if not args.skip_prediction_plots:
        plots_output_dir = args.plots_output_dir
        if plots_output_dir is None:
            base = "data/analytics/reports/prediction_analysis_plots"
            plots_output_dir = (
                f"{base}/asset={args.plots_asset.upper()}"
                if args.plots_asset
                else base
            )
        scope_prefixes = None
        if args.plots_scope_sweep_prefixes:
            scope_prefixes = [
                part.strip()
                for part in str(args.plots_scope_sweep_prefixes).split(",")
                if part.strip()
            ]

        plots_result = GeneratePredictionAnalysisPlotsUseCase(
            analytics_silver_dir=paths["analytics_silver"],
            analytics_gold_dir=paths["analytics_gold"],
            output_dir=plots_output_dir,
        ).execute(
            asset=args.plots_asset,
            scope_csv_path=args.plots_scope_csv,
            scope_sweep_prefixes=scope_prefixes,
        )
        logger.info(
            "Prediction analysis plots generated",
            extra={
                "asset": args.plots_asset,
                "plots_scope_csv": args.plots_scope_csv,
                "plots_scope_sweep_prefixes": args.plots_scope_sweep_prefixes,
                "output_dir": plots_result.output_dir,
                "outputs": plots_result.outputs,
            },
        )

    if args.fail_on_quality and not quality_result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
