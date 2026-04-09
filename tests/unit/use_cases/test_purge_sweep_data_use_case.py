from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.use_cases.purge_sweep_data_use_case import PurgeSweepDataUseCase


class _FakeRefreshResult:
    outputs = {"gold_dummy": "data/analytics/gold/gold_dummy.parquet"}


class _FakeRefreshUseCase:
    called = 0

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        self.kwargs = kwargs

    def execute(self) -> _FakeRefreshResult:
        _FakeRefreshUseCase.called += 1
        return _FakeRefreshResult()


class _FakeQualityResult:
    def __init__(self, passed: bool = True) -> None:
        self.passed = passed
        self.checks = [{"check": "dummy", "passed": passed, "detail": "ok" if passed else "fail"}]


class _FakeQualityUseCase:
    called = 0

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        self.kwargs = kwargs

    def execute(self) -> _FakeQualityResult:
        _FakeQualityUseCase.called += 1
        return _FakeQualityResult(passed=True)


def _write_table(silver_root: Path, table: str, df: pd.DataFrame) -> Path:
    out = silver_root / table / "part.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return out


def test_purge_sweep_data_use_case_removes_silver_and_models_and_validates_zero(tmp_path: Path) -> None:
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"
    models_sweeps = tmp_path / "models" / "AAPL" / "sweeps"
    models_sweeps.mkdir(parents=True, exist_ok=True)

    _write_table(
        silver,
        "dim_run",
        pd.DataFrame(
            [
                {"run_id": "r1", "parent_sweep_id": "0_2_4_demo", "asset": "AAPL"},
                {"run_id": "r2", "parent_sweep_id": "0_2_3_demo", "asset": "AAPL"},
            ]
        ),
    )
    _write_table(
        silver,
        "fact_oos_predictions",
        pd.DataFrame(
            [
                {"run_id": "r1", "parent_sweep_id": "0_2_4_demo", "prediction": 0.1},
                {"run_id": "r2", "parent_sweep_id": "0_2_3_demo", "prediction": 0.2},
            ]
        ),
    )
    _write_table(
        silver,
        "fact_model_artifacts",
        pd.DataFrame(
            [
                {"run_id": "r1", "checkpoint_path_final": "a"},
                {"run_id": "r2", "checkpoint_path_final": "b"},
            ]
        ),
    )

    (models_sweeps / "0_2_4_demo_a").mkdir(parents=True, exist_ok=True)
    (models_sweeps / "0_2_3_demo_b").mkdir(parents=True, exist_ok=True)

    use_case = PurgeSweepDataUseCase(
        analytics_silver_dir=silver,
        analytics_gold_dir=gold,
        models_sweeps_dir=models_sweeps,
        refresh_use_case_factory=_FakeRefreshUseCase,
        quality_use_case_factory=_FakeQualityUseCase,
    )

    result = use_case.execute(sweep_prefix="0_2_4_")

    assert result.run_ids_found == 1
    assert result.silver_files_rewritten >= 2
    assert result.validation_zero_passed is True
    assert result.quality_passed is True
    assert _FakeRefreshUseCase.called == 1
    assert _FakeQualityUseCase.called == 1

    dim_after = pd.read_parquet(silver / "dim_run" / "part.parquet")
    assert set(dim_after["run_id"].astype(str)) == {"r2"}

    oos_after = pd.read_parquet(silver / "fact_oos_predictions" / "part.parquet")
    assert set(oos_after["run_id"].astype(str)) == {"r2"}

    assert not (models_sweeps / "0_2_4_demo_a").exists()
    assert (models_sweeps / "0_2_3_demo_b").exists()


def test_purge_sweep_data_use_case_also_removes_parent_sweep_rows_without_run_id_match(tmp_path: Path) -> None:
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"
    models_sweeps = tmp_path / "models" / "AAPL" / "sweeps"
    models_sweeps.mkdir(parents=True, exist_ok=True)

    _write_table(
        silver,
        "dim_run",
        pd.DataFrame(
            [
                {"run_id": "r1", "parent_sweep_id": "0_2_3_demo", "asset": "AAPL"},
            ]
        ),
    )
    _write_table(
        silver,
        "fact_config",
        pd.DataFrame(
            [
                {"parent_sweep_id": "0_2_4_demo", "config_signature": "x"},
                {"parent_sweep_id": "0_2_3_demo", "config_signature": "y"},
            ]
        ),
    )

    use_case = PurgeSweepDataUseCase(
        analytics_silver_dir=silver,
        analytics_gold_dir=gold,
        models_sweeps_dir=models_sweeps,
        refresh_use_case_factory=_FakeRefreshUseCase,
        quality_use_case_factory=_FakeQualityUseCase,
    )
    result = use_case.execute(sweep_prefix="0_2_4_")

    assert result.validation_zero_passed is True
    cfg_after = pd.read_parquet(silver / "fact_config" / "part.parquet")
    assert set(cfg_after["parent_sweep_id"].astype(str)) == {"0_2_3_demo"}

def test_purge_sweep_data_use_case_fails_zero_validation_when_model_path_still_matches_prefix(tmp_path: Path) -> None:
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"
    models_sweeps = tmp_path / "models" / "AAPL" / "sweeps"
    models_sweeps.mkdir(parents=True, exist_ok=True)

    _write_table(
        silver,
        "dim_run",
        pd.DataFrame(
            [{"run_id": "r1", "parent_sweep_id": "0_2_4_demo", "asset": "AAPL"}],
        ),
    )

    # This file is not a directory, so purge of model directories won't remove it.
    # Validation must detect it as remaining residue by sweep prefix.
    (models_sweeps / "0_2_4_demo_note.txt").write_text("leftover", encoding="utf-8")

    use_case = PurgeSweepDataUseCase(
        analytics_silver_dir=silver,
        analytics_gold_dir=gold,
        models_sweeps_dir=models_sweeps,
        refresh_use_case_factory=_FakeRefreshUseCase,
        quality_use_case_factory=_FakeQualityUseCase,
    )

    result = use_case.execute(sweep_prefix="0_2_4_")

    assert result.validation_zero_passed is False
    assert result.model_paths_remaining
    assert "model_residue=" in result.validation_zero_detail


def test_purge_sweep_data_use_case_fails_when_prefix_not_found_anywhere(tmp_path: Path) -> None:
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"
    models_sweeps = tmp_path / "models" / "AAPL" / "sweeps"
    models_sweeps.mkdir(parents=True, exist_ok=True)

    _FakeRefreshUseCase.called = 0
    _FakeQualityUseCase.called = 0

    _write_table(
        silver,
        "dim_run",
        pd.DataFrame(
            [
                {"run_id": "r1", "parent_sweep_id": "0_2_3_demo", "asset": "AAPL"},
            ]
        ),
    )

    use_case = PurgeSweepDataUseCase(
        analytics_silver_dir=silver,
        analytics_gold_dir=gold,
        models_sweeps_dir=models_sweeps,
        refresh_use_case_factory=_FakeRefreshUseCase,
        quality_use_case_factory=_FakeQualityUseCase,
    )

    try:
        use_case.execute(sweep_prefix="0_2_4_")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "No sweep data found" in str(exc)

    assert _FakeRefreshUseCase.called == 0
    assert _FakeQualityUseCase.called == 0
