from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

import src.main_purge_sweep_data as main_purge

from src.use_cases.purge_sweep_data_use_case import PurgeSweepDataResult


class _FakePurgeUseCase:
    last_init_kwargs = None
    last_execute_kwargs = None

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        _FakePurgeUseCase.last_init_kwargs = kwargs

    def execute(self, **kwargs) -> PurgeSweepDataResult:  # noqa: ANN003
        _FakePurgeUseCase.last_execute_kwargs = kwargs
        return PurgeSweepDataResult(
            sweep_prefix="0_2_4_",
            run_ids_found=10,
            silver_files_scanned=20,
            silver_files_rewritten=5,
            silver_rows_removed_total=100,
            silver_rows_removed_by_table={"dim_run": 10},
            model_dirs_removed=["x"],
            model_paths_remaining=[],
            refresh_outputs={"gold": "ok"},
            quality_passed=True,
            quality_failed_checks=[],
            validation_zero_passed=True,
            validation_zero_detail="ok",
        )


def test_main_purge_passes_args_to_use_case(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(main_purge, "setup_logging", lambda *_a, **_k: None)
    monkeypatch.setattr(
        main_purge,
        "parse_args",
        lambda: Namespace(
            asset="AAPL",
            sweep_prefix="0_2_4_",
            min_samples_train=2,
            min_samples_val=3,
            min_samples_test=4,
            fail_on_quality=True,
        ),
    )
    monkeypatch.setattr(
        main_purge,
        "load_data_paths",
        lambda: {
            "analytics_silver": str(tmp_path / "silver"),
            "analytics_gold": str(tmp_path / "gold"),
            "models": str(tmp_path / "models"),
        },
    )
    monkeypatch.setattr(main_purge, "PurgeSweepDataUseCase", _FakePurgeUseCase)

    main_purge.main()

    assert _FakePurgeUseCase.last_init_kwargs is not None
    assert _FakePurgeUseCase.last_execute_kwargs is not None
    assert _FakePurgeUseCase.last_execute_kwargs == {
        "sweep_prefix": "0_2_4_",
        "min_samples_train": 2,
        "min_samples_val": 3,
        "min_samples_test": 4,
    }


def test_main_purge_fails_when_zero_residue_validation_fails(monkeypatch, tmp_path: Path) -> None:
    class _BadZeroUseCase(_FakePurgeUseCase):
        def execute(self, **kwargs) -> PurgeSweepDataResult:  # noqa: ANN003
            return PurgeSweepDataResult(
                sweep_prefix="0_2_4_",
                run_ids_found=10,
                silver_files_scanned=20,
                silver_files_rewritten=5,
                silver_rows_removed_total=100,
                silver_rows_removed_by_table={"dim_run": 10},
                model_dirs_removed=["x"],
                model_paths_remaining=[],
                refresh_outputs={"gold": "ok"},
                quality_passed=True,
                quality_failed_checks=[],
                validation_zero_passed=False,
                validation_zero_detail="residue",
            )

    monkeypatch.setattr(main_purge, "setup_logging", lambda *_a, **_k: None)
    monkeypatch.setattr(
        main_purge,
        "parse_args",
        lambda: Namespace(
            asset="AAPL",
            sweep_prefix="0_2_4_",
            min_samples_train=1,
            min_samples_val=1,
            min_samples_test=1,
            fail_on_quality=False,
        ),
    )
    monkeypatch.setattr(
        main_purge,
        "load_data_paths",
        lambda: {
            "analytics_silver": str(tmp_path / "silver"),
            "analytics_gold": str(tmp_path / "gold"),
            "models": str(tmp_path / "models"),
        },
    )
    monkeypatch.setattr(main_purge, "PurgeSweepDataUseCase", _BadZeroUseCase)

    with pytest.raises(SystemExit) as exc:
        main_purge.main()
    assert exc.value.code == 2


def test_main_purge_fails_on_quality_when_requested(monkeypatch, tmp_path: Path) -> None:
    class _BadQualityUseCase(_FakePurgeUseCase):
        def execute(self, **kwargs) -> PurgeSweepDataResult:  # noqa: ANN003
            return PurgeSweepDataResult(
                sweep_prefix="0_2_4_",
                run_ids_found=10,
                silver_files_scanned=20,
                silver_files_rewritten=5,
                silver_rows_removed_total=100,
                silver_rows_removed_by_table={"dim_run": 10},
                model_dirs_removed=["x"],
                model_paths_remaining=[],
                refresh_outputs={"gold": "ok"},
                quality_passed=False,
                quality_failed_checks=[{"check": "x", "passed": False, "detail": "bad"}],
                validation_zero_passed=True,
                validation_zero_detail="ok",
            )

    monkeypatch.setattr(main_purge, "setup_logging", lambda *_a, **_k: None)
    monkeypatch.setattr(
        main_purge,
        "parse_args",
        lambda: Namespace(
            asset="AAPL",
            sweep_prefix="0_2_4_",
            min_samples_train=1,
            min_samples_val=1,
            min_samples_test=1,
            fail_on_quality=True,
        ),
    )
    monkeypatch.setattr(
        main_purge,
        "load_data_paths",
        lambda: {
            "analytics_silver": str(tmp_path / "silver"),
            "analytics_gold": str(tmp_path / "gold"),
            "models": str(tmp_path / "models"),
        },
    )
    monkeypatch.setattr(main_purge, "PurgeSweepDataUseCase", _BadQualityUseCase)

    with pytest.raises(SystemExit) as exc:
        main_purge.main()
    assert exc.value.code == 1


def test_parse_args_rejects_blank_sweep_prefix(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "main_purge_sweep_data.py",
            "--asset", "AAPL",
            "--sweep-prefix", "   ",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        main_purge.parse_args()
    assert exc.value.code == 2



def test_main_purge_exits_with_code_3_when_prefix_not_found(monkeypatch, tmp_path: Path) -> None:
    class _MissingSweepUseCase(_FakePurgeUseCase):
        def execute(self, **kwargs):  # noqa: ANN003
            raise ValueError("No sweep data found for prefix '0_2_9_'")

    monkeypatch.setattr(main_purge, "setup_logging", lambda *_a, **_k: None)
    monkeypatch.setattr(
        main_purge,
        "parse_args",
        lambda: Namespace(
            asset="AAPL",
            sweep_prefix="0_2_9_",
            min_samples_train=1,
            min_samples_val=1,
            min_samples_test=1,
            fail_on_quality=False,
        ),
    )
    monkeypatch.setattr(
        main_purge,
        "load_data_paths",
        lambda: {
            "analytics_silver": str(tmp_path / "silver"),
            "analytics_gold": str(tmp_path / "gold"),
            "models": str(tmp_path / "models"),
        },
    )
    monkeypatch.setattr(main_purge, "PurgeSweepDataUseCase", _MissingSweepUseCase)

    with pytest.raises(SystemExit) as exc:
        main_purge.main()
    assert exc.value.code == 3
