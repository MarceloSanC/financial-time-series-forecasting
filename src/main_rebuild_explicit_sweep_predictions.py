from __future__ import annotations

import argparse
import json
import logging

from pathlib import Path

from src.adapters.parquet_tft_dataset_repository import ParquetTFTDatasetRepository
from src.use_cases.rebuild_explicit_sweep_predictions_use_case import (
    RebuildExplicitSweepPredictionsUseCase,
)
from src.utils.logging_config import setup_logging
from src.utils.path_resolver import load_data_paths

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild per-timestamp predictions for explicit-config sweeps without retraining."
    )
    parser.add_argument(
        "--sweep-dir",
        required=True,
        help="Sweep directory. Example: data/models/AAPL/sweeps/your_explicit_sweep",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing predictions_long.parquet",
    )
    return parser.parse_args()


def main() -> None:
    setup_logging(logging.INFO)
    args = parse_args()
    sweep_dir = Path(args.sweep_dir)
    analysis_cfg_path = sweep_dir / "analysis_config.json"
    if not analysis_cfg_path.exists():
        raise FileNotFoundError(f"analysis_config.json not found in sweep dir: {sweep_dir}")
    cfg = json.loads(analysis_cfg_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("analysis_config.json root must be an object")
    test_type = str(cfg.get("test_type") or "").strip().lower()
    if test_type != "explicit_configs":
        raise ValueError(
            f"Expected explicit_configs sweep, got test_type='{test_type}' in {analysis_cfg_path}"
        )

    asset = sweep_dir.parent.parent.name.upper()
    paths = load_data_paths()
    dataset_repo = ParquetTFTDatasetRepository(output_dir=Path(paths["dataset_tft"]))
    use_case = RebuildExplicitSweepPredictionsUseCase(dataset_repository=dataset_repo)
    result = use_case.execute(
        sweep_dir=sweep_dir,
        asset=asset,
        analysis_config=cfg,
        overwrite=bool(args.overwrite),
    )
    logger.info(
        "Explicit sweep prediction rebuild finished",
        extra={
            "sweep_dir": str(sweep_dir.resolve()),
            "predictions_path": str(result.predictions_path.resolve()),
            "failures_path": str(result.failures_path.resolve()),
            "total_runs": result.total_runs,
            "successful_runs": result.successful_runs,
            "failed_runs": result.failed_runs,
            "total_rows": result.total_rows,
        },
    )


if __name__ == "__main__":
    main()
