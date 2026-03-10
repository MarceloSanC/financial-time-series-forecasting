from __future__ import annotations

import argparse
import logging

from src.use_cases.refresh_analytics_store_use_case import RefreshAnalyticsStoreUseCase
from src.use_cases.validate_analytics_quality_use_case import ValidateAnalyticsQualityUseCase
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
    if args.fail_on_quality and not quality_result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
