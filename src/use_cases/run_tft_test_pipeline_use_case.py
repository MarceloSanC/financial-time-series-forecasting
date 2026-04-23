from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.domain.services.test_run_planners import (
    build_explicit_run_specs,
    run_specs_to_experiments,
)
from src.main_generate_sweep_artifacts import generate_for_sweep
from src.use_cases.run_tft_model_analysis_use_case import RunTFTModelAnalysisUseCase
from src.use_cases.run_tft_optuna_search_use_case import RunTFTOptunaSearchUseCase
from src.use_cases.test_pipeline_common import (
    TEST_TYPE_EXPLICIT_CONFIGS,
    TEST_TYPE_OFAT,
    TEST_TYPE_OPTUNA,
    validate_required_type_fields,
)


@dataclass(frozen=True)
class RunTFTTestPipelineResult:
    test_type: str
    output_dir: str
    artifacts_generated: int
    payload: dict[str, Any]


class RunTFTTestPipelineUseCase:
    def __init__(self, *, train_runner: Any) -> None:
        self.train_runner = train_runner

    def execute(
        self,
        *,
        asset: str,
        models_asset_dir: Path,
        config: dict[str, Any],
    ) -> RunTFTTestPipelineResult:
        test_type = str(config.get("test_type") or "").strip().lower()
        validate_required_type_fields(config=config, test_type=test_type)

        common_context = {
            "test_type": test_type,
            "schema_version": str(config.get("schema_version") or "1.0"),
        }

        if test_type == TEST_TYPE_OFAT:
            use_case = RunTFTModelAnalysisUseCase(
                train_runner=self.train_runner,
                base_training_config=dict(config["training_config"]),
                param_ranges=dict(config["param_ranges"]),
                replica_seeds=list(config.get("replica_seeds") or [7, 42, 123]),
                split_config=dict(config.get("split_config") or {}),
                compute_confidence_interval=bool(config.get("compute_confidence_interval", False)),
                walk_forward_config=dict(config.get("walk_forward") or {}),
                generate_comparison_plots=bool(config.get("generate_comparison_plots", True)),
            )
            analysis_config = dict(config)
            analysis_config.update(common_context)
            result = use_case.execute(
                asset=asset,
                models_asset_dir=models_asset_dir,
                features=config.get("features"),
                continue_on_error=bool(config.get("continue_on_error", False)),
                merge_tests=bool(config.get("merge_tests", False)),
                max_runs=config.get("max_runs"),
                output_subdir=config.get("output_subdir"),
                analysis_config=analysis_config,
            )
            artifacts = generate_for_sweep(Path(result.sweep_dir))
            return RunTFTTestPipelineResult(
                test_type=test_type,
                output_dir=result.sweep_dir,
                artifacts_generated=len(artifacts),
                payload={
                    "runs_ok": result.runs_ok,
                    "runs_failed": result.runs_failed,
                    "top_5_runs": result.top_5_runs,
                },
            )

        if test_type == TEST_TYPE_EXPLICIT_CONFIGS:
            run_specs = build_explicit_run_specs(
                base_config=dict(config["training_config"]),
                explicit_configs=list(config.get("explicit_configs") or []),
            )
            experiments = run_specs_to_experiments(run_specs)
            use_case = RunTFTModelAnalysisUseCase(
                train_runner=self.train_runner,
                base_training_config=dict(config["training_config"]),
                param_ranges={},
                replica_seeds=list(config.get("replica_seeds") or [7, 42, 123]),
                split_config=dict(config.get("split_config") or {}),
                compute_confidence_interval=bool(config.get("compute_confidence_interval", False)),
                walk_forward_config=dict(config.get("walk_forward") or {}),
                generate_comparison_plots=bool(config.get("generate_comparison_plots", True)),
            )
            analysis_config = dict(config)
            analysis_config.update(common_context)
            result = use_case.execute(
                asset=asset,
                models_asset_dir=models_asset_dir,
                features=config.get("features"),
                continue_on_error=bool(config.get("continue_on_error", False)),
                merge_tests=bool(config.get("merge_tests", False)),
                max_runs=config.get("max_runs"),
                output_subdir=config.get("output_subdir"),
                analysis_config=analysis_config,
                explicit_experiments=experiments,
            )
            artifacts = generate_for_sweep(Path(result.sweep_dir))
            return RunTFTTestPipelineResult(
                test_type=test_type,
                output_dir=result.sweep_dir,
                artifacts_generated=len(artifacts),
                payload={
                    "runs_ok": result.runs_ok,
                    "runs_failed": result.runs_failed,
                    "top_5_runs": result.top_5_runs,
                },
            )

        if test_type == TEST_TYPE_OPTUNA:
            use_case = RunTFTOptunaSearchUseCase(
                train_runner=self.train_runner,
                base_training_config=dict(config["training_config"]),
                split_config=dict(config.get("split_config") or {}),
                walk_forward_config=dict(config.get("walk_forward") or {}),
                replica_seeds=list(config.get("replica_seeds") or [7, 42, 123]),
                continue_on_error=bool(config.get("continue_on_error", True)),
                merge_tests=bool(config.get("merge_tests", False)),
                objective_metric=str(config.get("objective_metric", "robust_score")),
                objective_lambda=float(config.get("objective_lambda", 1.0)),
            )
            result = use_case.execute(
                asset=asset,
                models_asset_dir=models_asset_dir,
                features=config.get("features"),
                search_space=dict(config["search_space"]),
                n_trials=int(config["n_trials"]),
                top_k=int(config["top_k"]),
                output_subdir=str(config.get("output_subdir") or "optuna_tft_search"),
                study_name=str(config["study_name"]),
                timeout_seconds=config.get("timeout_seconds"),
                sampler_seed=config.get("sampler_seed"),
            )
            return RunTFTTestPipelineResult(
                test_type=test_type,
                output_dir=result.output_dir,
                artifacts_generated=0,
                payload={
                    "best_value": result.best_value,
                    "best_params": result.best_params,
                    "top_k": len(result.top_k_configs),
                },
            )

        raise ValueError(f"Unsupported test_type='{test_type}'")
