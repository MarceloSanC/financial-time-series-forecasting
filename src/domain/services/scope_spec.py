from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

ScopeMode = Literal["global_health", "cohort_decision"]


@dataclass(frozen=True)
class ScopeSpec:
    """Domain contract for analytics scope selection."""

    scope_mode: ScopeMode
    parent_sweep_prefixes: tuple[str, ...] = ()
    splits: tuple[str, ...] = ()
    horizons: tuple[int, ...] = ()

    @staticmethod
    def _normalize_str_values(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
        if not values:
            return ()
        cleaned = [str(v).strip() for v in values if str(v).strip()]
        return tuple(dict.fromkeys(cleaned))

    @staticmethod
    def _normalize_int_values(values: tuple[int, ...] | list[int] | None) -> tuple[int, ...]:
        if not values:
            return ()
        cleaned = [int(v) for v in values]
        return tuple(dict.fromkeys(cleaned))

    @classmethod
    def create(
        cls,
        *,
        scope_mode: ScopeMode,
        parent_sweep_prefixes: tuple[str, ...] | list[str] | None = None,
        splits: tuple[str, ...] | list[str] | None = None,
        horizons: tuple[int, ...] | list[int] | None = None,
    ) -> ScopeSpec:
        return cls(
            scope_mode=scope_mode,
            parent_sweep_prefixes=cls._normalize_str_values(parent_sweep_prefixes),
            splits=cls._normalize_str_values(splits),
            horizons=cls._normalize_int_values(horizons),
        )

    def has_cohort_filters(self) -> bool:
        return bool(self.parent_sweep_prefixes or self.splits or self.horizons)


def validate_scope_spec(
    scope_spec: ScopeSpec,
    *,
    ignore_restrictive_filters_on_global_health: bool = True,
) -> ScopeSpec:
    """
    Validate and normalize scope semantics.

    Rules:
    - cohort_decision without cohort filters is invalid.
    - global_health ignores restrictive filters by default.
    """

    if scope_spec.scope_mode == "cohort_decision" and not scope_spec.has_cohort_filters():
        raise ValueError(
            "scope_mode=cohort_decision requires at least one cohort filter "
            "(parent_sweep_prefixes, splits, or horizons)."
        )

    if (
        scope_spec.scope_mode == "global_health"
        and ignore_restrictive_filters_on_global_health
        and scope_spec.has_cohort_filters()
    ):
        return ScopeSpec.create(scope_mode="global_health")

    return scope_spec


def filter_dataframe_by_scope(
    df: pd.DataFrame,
    *,
    scope_spec: ScopeSpec,
    parent_sweep_col: str = "parent_sweep_id",
    split_col: str = "split",
    horizon_col: str = "horizon",
) -> pd.DataFrame:
    """Apply scope filters to a dataframe using canonical sweep/split/horizon columns."""
    if df.empty:
        return df.copy()

    scoped = df.copy()

    if scope_spec.parent_sweep_prefixes:
        if parent_sweep_col not in scoped.columns:
            return scoped.iloc[0:0].copy()
        sweep_values = scoped[parent_sweep_col].astype(str)
        mask = sweep_values.apply(
            lambda value: any(value.startswith(prefix) for prefix in scope_spec.parent_sweep_prefixes)
        )
        scoped = scoped[mask].copy()

    if scope_spec.splits:
        if split_col not in scoped.columns:
            return scoped.iloc[0:0].copy()
        scoped = scoped[scoped[split_col].astype(str).isin(set(scope_spec.splits))].copy()

    if scope_spec.horizons:
        if horizon_col not in scoped.columns:
            return scoped.iloc[0:0].copy()
        horizon_values = pd.to_numeric(scoped[horizon_col], errors="coerce")
        scoped = scoped[horizon_values.isin(set(scope_spec.horizons))].copy()

    return scoped

