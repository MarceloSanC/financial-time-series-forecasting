from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.use_cases.run_tft_test_pipeline_use_case import RunTFTTestPipelineUseCase


@dataclass
class _AnalysisResult:
    sweep_dir: str
    runs_ok: int
    runs_failed: int
    top_5_runs: list[dict[str, Any]]


@dataclass
class _OptunaResult:
    output_dir: str
    best_value: float
    best_params: dict[str, Any]
    top_k_configs: list[dict[str, Any]]


class _DummyTrainRunner:
    def run(self, **_: Any) -> tuple[str, dict[str, Any]]:
        return "v1", {"split_metrics": {"val": {"rmse": 1.0, "mae": 1.0}, "test": {"rmse": 1.0, "mae": 1.0}}}


def test_dispatch_ofat(monkeypatch, tmp_path: Path) -> None:
    class _DummyAnalysisUseCase:
        def __init__(self, **_: Any) -> None:
            pass

        def execute(self, **_: Any) -> _AnalysisResult:
            return _AnalysisResult(
                sweep_dir=str(tmp_path / "sweeps" / "ofat_1"),
                runs_ok=10,
                runs_failed=0,
                top_5_runs=[{"run_label": "x"}],
            )

    monkeypatch.setattr(
        "src.use_cases.run_tft_test_pipeline_use_case.RunTFTModelAnalysisUseCase",
        _DummyAnalysisUseCase,
    )
    monkeypatch.setattr(
        "src.use_cases.run_tft_test_pipeline_use_case.generate_for_sweep",
        lambda _: ["a.png", "b.png"],
    )

    uc = RunTFTTestPipelineUseCase(train_runner=_DummyTrainRunner())
    result = uc.execute(
        asset="AAPL",
        models_asset_dir=tmp_path,
        config={
            "test_type": "ofat",
            "training_config": {"max_encoder_length": 10, "max_prediction_length": 1},
            "param_ranges": {"max_encoder_length": [10, 20]},
            "replica_seeds": [7],
            "split_config": {},
            "walk_forward": {"enabled": False, "folds": []},
        },
    )

    assert result.test_type == "ofat"
    assert result.artifacts_generated == 2
    assert result.payload["runs_ok"] == 10


def test_dispatch_optuna(monkeypatch, tmp_path: Path) -> None:
    class _DummyOptunaUseCase:
        def __init__(self, **_: Any) -> None:
            pass

        def execute(self, **_: Any) -> _OptunaResult:
            return _OptunaResult(
                output_dir=str(tmp_path / "optuna" / "s1"),
                best_value=0.123,
                best_params={"a": 1},
                top_k_configs=[{"rank": 1}],
            )

    monkeypatch.setattr(
        "src.use_cases.run_tft_test_pipeline_use_case.RunTFTOptunaSearchUseCase",
        _DummyOptunaUseCase,
    )

    uc = RunTFTTestPipelineUseCase(train_runner=_DummyTrainRunner())
    result = uc.execute(
        asset="AAPL",
        models_asset_dir=tmp_path,
        config={
            "test_type": "optuna",
            "training_config": {"max_encoder_length": 10, "max_prediction_length": 1},
            "search_space": {"max_encoder_length": {"type": "int", "low": 2, "high": 10}},
            "n_trials": 2,
            "top_k": 1,
            "study_name": "s1",
            "replica_seeds": [7],
            "split_config": {},
            "walk_forward": {"enabled": False, "folds": []},
        },
    )

    assert result.test_type == "optuna"
    assert result.payload["best_value"] == 0.123
