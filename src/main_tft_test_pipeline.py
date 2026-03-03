from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from src.adapters.cli_tft_train_runner import CLITFTTrainRunner
from src.infrastructure.schemas.model_artifact_schema import TFT_SPLIT_DEFAULTS, TFT_TRAINING_DEFAULTS
from src.use_cases.run_tft_test_pipeline_use_case import RunTFTTestPipelineUseCase
from src.use_cases.test_pipeline_common import (
    TEST_TYPE_EXPLICIT_CONFIGS,
    TEST_TYPE_OFAT,
    TEST_TYPE_OPTUNA,
    apply_common_test_fields,
    validate_required_type_fields,
)
from src.utils.logging_config import setup_logging
from src.utils.path_resolver import load_data_paths

logger = logging.getLogger(__name__)
DEFAULT_TEST_CONFIG_PATH = Path("config/test_pipeline.default.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unified TFT test pipeline runner by test_type.")
    parser.add_argument("--asset", required=True, help="Asset symbol. Example: AAPL")
    parser.add_argument(
        "--config-json",
        type=str,
        default=str(DEFAULT_TEST_CONFIG_PATH),
        help="Path to unified test config JSON with test_type.",
    )
    parser.add_argument(
        "--merge-tests",
        action="store_true",
        help="Enable merge/resume mode when supported by selected test_type.",
    )
    return parser.parse_args()


def _load_json_config(path: str) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists() or not config_path.is_file():
        raise ValueError(f"Config JSON not found: {config_path}")
    try:
        content = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file: {config_path}") from exc
    if not isinstance(content, dict):
        raise ValueError("Config JSON root must be an object")
    return content


def _default_for_test_type(test_type: str) -> dict[str, Any]:
    common = {
        "schema_version": "1.0",
        "test_type": test_type,
        "features": None,
        "feature_sets": [],
        "continue_on_error": True,
        "output_subdir": None,
        "replica_seeds": [7, 42, 123],
        "walk_forward": {"enabled": False, "folds": []},
        "training_config": dict(TFT_TRAINING_DEFAULTS),
        "split_config": dict(TFT_SPLIT_DEFAULTS),
    }
    if test_type == TEST_TYPE_OFAT:
        common.update(
            {
                "merge_tests": False,
                "max_runs": None,
                "compute_confidence_interval": False,
                "generate_comparison_plots": True,
                "param_ranges": {},
            }
        )
    elif test_type == TEST_TYPE_OPTUNA:
        common.update(
            {
                "merge_tests": False,
                "study_name": "tft_optuna",
                "n_trials": 30,
                "top_k": 5,
                "timeout_seconds": None,
                "sampler_seed": 42,
                "objective_metric": "robust_score",
                "objective_lambda": 1.0,
                "search_space": {},
            }
        )
    elif test_type == TEST_TYPE_EXPLICIT_CONFIGS:
        common.update(
            {
                "merge_tests": False,
                "max_runs": None,
                "compute_confidence_interval": False,
                "generate_comparison_plots": True,
                "explicit_configs": [],
            }
        )
    return common


def _resolve_effective_config(file_config: dict[str, Any]) -> dict[str, Any]:
    test_type = str(file_config.get("test_type") or "").strip().lower()
    if not test_type:
        raise ValueError("Unified config requires 'test_type'.")
    effective = _default_for_test_type(test_type)
    effective = apply_common_test_fields(effective=effective, file_config=file_config)
    for key in [
        "schema_version",
        "merge_tests",
        "max_runs",
        "compute_confidence_interval",
        "generate_comparison_plots",
        "study_name",
        "n_trials",
        "top_k",
        "timeout_seconds",
        "sampler_seed",
        "objective_metric",
        "objective_lambda",
        "param_ranges",
        "search_space",
        "explicit_configs",
    ]:
        if key in file_config:
            effective[key] = file_config[key]
    validate_required_type_fields(config=effective, test_type=test_type)
    return effective


def main() -> None:
    setup_logging(logging.INFO)
    args = parse_args()
    asset = args.asset.strip().upper()
    file_config = _load_json_config(args.config_json)
    effective_cfg = _resolve_effective_config(file_config)
    if args.merge_tests:
        effective_cfg["merge_tests"] = True

    paths = load_data_paths()
    models_asset_dir = Path(paths["models"]) / asset

    use_case = RunTFTTestPipelineUseCase(train_runner=CLITFTTrainRunner())
    result = use_case.execute(
        asset=asset,
        models_asset_dir=models_asset_dir,
        config=effective_cfg,
    )
    logger.info(
        "Unified test pipeline finished",
        extra={
            "asset": asset,
            "test_type": result.test_type,
            "output_dir": result.output_dir,
            "artifacts_generated": result.artifacts_generated,
            "payload": result.payload,
        },
    )


if __name__ == "__main__":
    main()
