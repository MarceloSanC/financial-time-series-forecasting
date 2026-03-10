from __future__ import annotations

from src.utils.asset_periods import (
    resolve_data_period,
    resolve_training_range,
    resolve_training_split,
)


def test_resolve_data_period_prefers_data_period() -> None:
    asset_cfg = {
        "symbol": "AAPL",
        "start_date": "2015-01-01",
        "end_date": "2016-01-01",
        "data_period": {
            "start_date": "2010-01-01",
            "end_date": "2025-12-31",
        },
    }
    start, end = resolve_data_period(asset_cfg)
    assert start.year == 2010
    assert end.year == 2025


def test_resolve_data_period_requires_data_period() -> None:
    asset_cfg = {
        "symbol": "AAPL",
        "start_date": "2012-01-01",
        "end_date": "2013-01-01",
    }
    try:
        resolve_data_period(asset_cfg)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "data_period.start_date/end_date" in str(exc)


def test_resolve_training_split_from_asset_config() -> None:
    asset_cfg = {
        "symbol": "AAPL",
        "training_period": {
            "train_start": "2010-01-01",
            "train_end": "2020-12-31",
            "val_start": "2021-01-01",
            "val_end": "2022-12-31",
            "test_start": "2023-01-01",
            "test_end": "2025-12-31",
        },
    }
    split = resolve_training_split(asset_cfg)
    assert split is not None
    assert split["train_start"] == "20100101"
    assert split["test_end"] == "20251231"


def test_resolve_training_range_optional() -> None:
    asset_cfg = {
        "symbol": "AAPL",
        "training_period": {
            "start_date": "2010-01-01",
            "end_date": "2025-12-31",
        },
    }
    training_range = resolve_training_range(asset_cfg)
    assert training_range == ("20100101", "20251231")
