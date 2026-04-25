from __future__ import annotations

import pandas as pd
import pytest

from src.domain.services.scope_spec import (
    ScopeSpec,
    filter_dataframe_by_scope,
    validate_scope_spec,
)


def test_validate_scope_spec_cohort_decision_requires_filters() -> None:
    spec = ScopeSpec.create(scope_mode="cohort_decision")

    with pytest.raises(ValueError, match="cohort_decision requires at least one cohort filter"):
        validate_scope_spec(spec)


def test_validate_scope_spec_global_health_ignores_restrictive_filters_by_default() -> None:
    spec = ScopeSpec.create(
        scope_mode="global_health",
        parent_sweep_prefixes=["0_2_3_"],
        splits=["test"],
        horizons=[1],
    )

    validated = validate_scope_spec(spec)

    assert validated.scope_mode == "global_health"
    assert validated.parent_sweep_prefixes == ()
    assert validated.splits == ()
    assert validated.horizons == ()


def test_validate_scope_spec_global_health_can_keep_filters_when_requested() -> None:
    spec = ScopeSpec.create(
        scope_mode="global_health",
        parent_sweep_prefixes=["0_2_3_"],
        splits=["test"],
        horizons=[1],
    )

    validated = validate_scope_spec(
        spec,
        ignore_restrictive_filters_on_global_health=False,
    )

    assert validated == spec


def test_filter_dataframe_by_scope_applies_parent_sweep_split_and_horizon() -> None:
    df = pd.DataFrame(
        [
            {"run_id": "r1", "parent_sweep_id": "0_2_3_a", "split": "test", "horizon": 1},
            {"run_id": "r2", "parent_sweep_id": "0_2_3_a", "split": "val", "horizon": 1},
            {"run_id": "r3", "parent_sweep_id": "0_2_4_a", "split": "test", "horizon": 1},
            {"run_id": "r4", "parent_sweep_id": "0_2_3_a", "split": "test", "horizon": 7},
        ]
    )

    spec = ScopeSpec.create(
        scope_mode="cohort_decision",
        parent_sweep_prefixes=["0_2_3_"],
        splits=["test"],
        horizons=[1],
    )
    scoped = filter_dataframe_by_scope(df, scope_spec=spec)

    assert scoped["run_id"].tolist() == ["r1"]


def test_filter_dataframe_by_scope_returns_empty_when_required_column_is_missing() -> None:
    df = pd.DataFrame([{"run_id": "r1", "split": "test", "horizon": 1}])
    spec = ScopeSpec.create(scope_mode="cohort_decision", parent_sweep_prefixes=["0_2_3_"])

    scoped = filter_dataframe_by_scope(df, scope_spec=spec)

    assert scoped.empty

