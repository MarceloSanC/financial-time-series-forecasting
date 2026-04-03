from __future__ import annotations

import pytest

from src.use_cases.test_pipeline_common import (
    TEST_TYPE_EXPLICIT_CONFIGS,
    TEST_TYPE_OFAT,
    TEST_TYPE_OPTUNA,
    apply_common_test_fields,
    validate_required_type_fields,
)


def test_validate_required_type_fields_ofat_requires_param_ranges() -> None:
    with pytest.raises(ValueError, match="param_ranges"):
        validate_required_type_fields(config={"test_type": TEST_TYPE_OFAT}, test_type=TEST_TYPE_OFAT)


def test_validate_required_type_fields_optuna_requires_search_space() -> None:
    with pytest.raises(ValueError, match="search_space"):
        validate_required_type_fields(
            config={"test_type": TEST_TYPE_OPTUNA, "n_trials": 10, "top_k": 3, "study_name": "s"},
            test_type=TEST_TYPE_OPTUNA,
        )


def test_validate_required_type_fields_explicit_requires_configs() -> None:
    with pytest.raises(ValueError, match="explicit_configs"):
        validate_required_type_fields(
            config={"test_type": TEST_TYPE_EXPLICIT_CONFIGS},
            test_type=TEST_TYPE_EXPLICIT_CONFIGS,
        )


def test_validate_required_type_fields_explicit_valid() -> None:
    validate_required_type_fields(
        config={
            "test_type": TEST_TYPE_EXPLICIT_CONFIGS,
            "explicit_configs": [{"training_config": {"max_encoder_length": 10}}],
        },
        test_type=TEST_TYPE_EXPLICIT_CONFIGS,
    )


def test_apply_common_test_fields_supports_resume_cleanup_flags() -> None:
    effective = {
        "merge_tests": False,
        "resume_policy": "keep_completed",
        "rewind_n": 1,
        "reconcile_orphans": True,
        "cleanup_failed_or_incomplete": True,
        "dry_run_cleanup": False,
        "training_config": {},
        "split_config": {},
    }
    file_config = {
        "merge_tests": True,
        "resume_policy": "rewind_last",
        "rewind_n": 2,
        "reconcile_orphans": False,
        "cleanup_failed_or_incomplete": False,
        "dry_run_cleanup": True,
    }
    out = apply_common_test_fields(effective=effective, file_config=file_config)
    assert out["merge_tests"] is True
    assert out["resume_policy"] == "rewind_last"
    assert out["rewind_n"] == 2
    assert out["reconcile_orphans"] is False
    assert out["cleanup_failed_or_incomplete"] is False
    assert out["dry_run_cleanup"] is True
