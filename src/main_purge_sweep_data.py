from __future__ import annotations

import argparse
import logging

from pathlib import Path
from time import perf_counter

from src.use_cases.purge_sweep_data_use_case import PurgeSweepDataUseCase
from src.utils.logging_config import setup_logging
from src.utils.path_resolver import load_data_paths

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Purge all generated data for a sweep prefix (silver + model dirs), "
            "refresh gold, and validate zero residue."
        )
    )
    parser.add_argument("--asset", required=True, help="Asset id used in models sweep path (example: AAPL).")
    parser.add_argument(
        "--sweep-prefix",
        required=True,
        help="Sweep prefix to purge (example: 0_2_4_).",
    )
    parser.add_argument("--min-samples-train", type=int, default=1)
    parser.add_argument("--min-samples-val", type=int, default=1)
    parser.add_argument("--min-samples-test", type=int, default=1)
    parser.add_argument(
        "--fail-on-quality",
        action="store_true",
        help="Return non-zero exit code when post-purge quality checks fail.",
    )
    args = parser.parse_args()
    sweep_prefix = str(args.sweep_prefix).strip()
    if not sweep_prefix:
        parser.error("--sweep-prefix must be a non-empty value (example: 0_2_4_)")
    args.sweep_prefix = sweep_prefix
    return args


def main() -> None:
    setup_logging(logging.INFO)
    args = parse_args()
    t0 = perf_counter()
    paths = load_data_paths()

    models_sweeps_dir = Path(paths["models"]) / str(args.asset).upper() / "sweeps"
    logger.info(
        "Sweep purge command started",
        extra={
            "asset": str(args.asset).upper(),
            "sweep_prefix": args.sweep_prefix,
            "analytics_silver_dir": str(paths["analytics_silver"]),
            "analytics_gold_dir": str(paths["analytics_gold"]),
            "models_sweeps_dir": str(models_sweeps_dir),
            "fail_on_quality": bool(args.fail_on_quality),
        },
    )

    try:
        result = PurgeSweepDataUseCase(
            analytics_silver_dir=paths["analytics_silver"],
            analytics_gold_dir=paths["analytics_gold"],
            models_sweeps_dir=models_sweeps_dir,
        ).execute(
            sweep_prefix=args.sweep_prefix,
            min_samples_train=args.min_samples_train,
            min_samples_val=args.min_samples_val,
            min_samples_test=args.min_samples_test,
        )
    except ValueError as exc:
        logger.error("Sweep purge aborted", extra={"asset": str(args.asset).upper(), "sweep_prefix": args.sweep_prefix, "error": str(exc)})
        raise SystemExit(3) from exc

    logger.info(
        "Sweep purge completed",
        extra={
            "asset": str(args.asset).upper(),
            "sweep_prefix": result.sweep_prefix,
            "run_ids_found": result.run_ids_found,
            "silver_files_scanned": result.silver_files_scanned,
            "silver_files_rewritten": result.silver_files_rewritten,
            "silver_rows_removed_total": result.silver_rows_removed_total,
            "silver_rows_removed_by_table": result.silver_rows_removed_by_table,
            "model_dirs_removed": result.model_dirs_removed,
            "model_paths_remaining": result.model_paths_remaining,
            "refresh_outputs": result.refresh_outputs,
            "quality_passed": result.quality_passed,
            "quality_failed_checks": result.quality_failed_checks,
            "validation_zero_passed": result.validation_zero_passed,
            "validation_zero_detail": result.validation_zero_detail,
        },
    )

    if not result.validation_zero_passed:
        logger.error("Sweep purge failed zero-residue validation", extra={"sweep_prefix": result.sweep_prefix, "validation_zero_detail": result.validation_zero_detail})
        raise SystemExit(2)

    if args.fail_on_quality and not result.quality_passed:
        logger.error("Sweep purge failed quality gate", extra={"sweep_prefix": result.sweep_prefix, "failed_checks": result.quality_failed_checks})
        raise SystemExit(1)

    logger.info(
        "Sweep purge command finished successfully",
        extra={
            "asset": str(args.asset).upper(),
            "sweep_prefix": result.sweep_prefix,
            "elapsed_seconds": round(perf_counter() - t0, 3),
        },
    )


if __name__ == "__main__":
    main()
