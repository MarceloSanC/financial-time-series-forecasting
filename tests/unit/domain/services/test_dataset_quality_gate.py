from __future__ import annotations

import pandas as pd
import pytest

from src.domain.services.dataset_quality_gate import (
    DatasetQualityGate,
    DatasetQualityGateConfig,
)


def _base_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-03"], utc=True
            ),
            "f1": [1.0, 2.0, 3.0],
            "f2": [10.0, 11.0, 12.0],
        }
    )


def test_quality_gate_accepts_valid_dataframe() -> None:
    df = _base_df()
    DatasetQualityGate.validate(
        df=df,
        feature_cols=["f1", "f2"],
        config=DatasetQualityGateConfig(
            max_nan_ratio_per_feature=0.5,
            min_temporal_coverage_days=3,
            require_unique_timestamps=True,
            require_monotonic_timestamps=True,
        ),
        context="unit",
    )


def test_quality_gate_rejects_duplicate_timestamps() -> None:
    df = _base_df()
    df.loc[1, "timestamp"] = df.loc[0, "timestamp"]
    with pytest.raises(ValueError, match="duplicate timestamp"):
        DatasetQualityGate.validate(
            df=df,
            feature_cols=["f1"],
            config=DatasetQualityGateConfig(require_unique_timestamps=True),
            context="unit",
        )


def test_quality_gate_rejects_non_monotonic_timestamps() -> None:
    df = _base_df().iloc[[1, 0, 2]].reset_index(drop=True)
    with pytest.raises(ValueError, match="not monotonic increasing"):
        DatasetQualityGate.validate(
            df=df,
            feature_cols=["f1"],
            config=DatasetQualityGateConfig(require_monotonic_timestamps=True),
            context="unit",
        )


def test_quality_gate_rejects_low_temporal_coverage() -> None:
    df = _base_df()
    with pytest.raises(ValueError, match="temporal coverage below minimum"):
        DatasetQualityGate.validate(
            df=df,
            feature_cols=["f1"],
            config=DatasetQualityGateConfig(min_temporal_coverage_days=10),
            context="unit",
        )


def test_quality_gate_rejects_nan_ratio() -> None:
    df = _base_df()
    df["f1"] = [1.0, None, None]
    with pytest.raises(ValueError, match="NaN ratio above threshold"):
        DatasetQualityGate.validate(
            df=df,
            feature_cols=["f1"],
            config=DatasetQualityGateConfig(max_nan_ratio_per_feature=0.5),
            context="unit",
        )


def test_quality_gate_ignores_nan_inside_feature_warmup_window() -> None:
    df = _base_df()
    df["f1"] = [None, 2.0, 3.0]  # 1 leading NaN

    DatasetQualityGate.validate(
        df=df,
        feature_cols=["f1"],
        config=DatasetQualityGateConfig(max_nan_ratio_per_feature=0.0),
        context="unit",
        warmup_counts={"f1": 1},
    )


def test_quality_gate_still_rejects_nan_after_feature_warmup_window() -> None:
    df = _base_df()
    df["f1"] = [1.0, None, 3.0]  # NaN after warmup row

    with pytest.raises(ValueError, match="NaN ratio above threshold"):
        DatasetQualityGate.validate(
            df=df,
            feature_cols=["f1"],
            config=DatasetQualityGateConfig(max_nan_ratio_per_feature=0.0),
            context="unit",
            warmup_counts={"f1": 1},
        )
