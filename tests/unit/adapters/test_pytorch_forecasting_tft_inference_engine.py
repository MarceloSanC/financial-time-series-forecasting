from __future__ import annotations

import sys
import types

import numpy as np
import pandas as pd
import pytest

from src.adapters.pytorch_forecasting_tft_inference_engine import (
    PytorchForecastingTFTInferenceEngine,
)


class _FakeModel:
    class _Loss:
        quantiles = [0.1, 0.5, 0.9]

    loss = _Loss()

    def predict(self, loader, mode="prediction", **kwargs):
        n = sum(len(x["decoder_time_idx"]) for x, _ in loader)
        if mode == "raw":
            return np.tile(np.array([[[0.1, 0.2, 0.3]]]), (n, 1, 1))
        return np.arange(1, n + 1, dtype=float).reshape(-1, 1)


def _install_fake_pf_module(monkeypatch: pytest.MonkeyPatch, *, fail_from_parameters: bool) -> None:
    fake_pf = types.ModuleType("pytorch_forecasting")

    class _FakeDataset:
        def __init__(self, df: pd.DataFrame, **kwargs):
            self.df = df.copy()

        @classmethod
        def from_parameters(cls, params, df: pd.DataFrame, predict=True, stop_randomization=True):
            if fail_from_parameters:
                raise RuntimeError("invalid params")
            return cls(df)

        def to_dataloader(self, train, batch_size, num_workers):
            tids = self.df["time_idx"].to_numpy()
            decoder = tids[tids >= 2].reshape(-1, 1)
            return [({"decoder_time_idx": decoder}, None)]

    fake_pf.TimeSeriesDataSet = _FakeDataset
    monkeypatch.setitem(sys.modules, "pytorch_forecasting", fake_pf)


def _sample_df() -> pd.DataFrame:
    rows = []
    for i in range(6):
        rows.append(
            {
                "asset_id": "AAPL",
                "timestamp": pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(days=i),
                "time_idx": i,
                "target_return": 0.01 * i,
                "close": 100.0 + i,
                "day_of_week": i % 7,
                "month": 1,
            }
        )
    return pd.DataFrame(rows)


def test_engine_strict_mode_requires_dataset_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_pf_module(monkeypatch, fail_from_parameters=False)
    engine = PytorchForecastingTFTInferenceEngine()

    with pytest.raises(ValueError, match="INFER_DATASET_SPEC_MISSING"):
        engine.infer(
            model=_FakeModel(),
            dataset_df=_sample_df(),
            asset_id="AAPL",
            model_version="20260303_120000_B",
            model_path="/tmp/model",
            feature_set_name="BASELINE_FEATURES",
            features_used_csv="close",
            feature_cols=["close"],
            dataset_parameters={},
            max_encoder_length=2,
            max_prediction_length=1,
            batch_size=8,
            run_id="run_1",
        )


def test_engine_uses_from_parameters_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_pf_module(monkeypatch, fail_from_parameters=False)
    engine = PytorchForecastingTFTInferenceEngine()
    records = engine.infer(
        model=_FakeModel(),
        dataset_df=_sample_df(),
        asset_id="AAPL",
        model_version="20260303_120000_B",
        model_path="/tmp/model",
        feature_set_name="BASELINE_FEATURES",
        features_used_csv="close",
        feature_cols=["close"],
        dataset_parameters={"time_idx": "time_idx"},
        max_encoder_length=2,
        max_prediction_length=1,
        batch_size=8,
        run_id="run_1",
    )
    assert len(records) == 4
    assert records[0].quantile_p10 is not None


def test_engine_raises_incompatible_when_from_parameters_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_pf_module(monkeypatch, fail_from_parameters=True)
    engine = PytorchForecastingTFTInferenceEngine()
    with pytest.raises(ValueError, match="INFER_DATASET_SPEC_INCOMPATIBLE"):
        engine.infer(
            model=_FakeModel(),
            dataset_df=_sample_df(),
            asset_id="AAPL",
            model_version="20260303_120000_B",
            model_path="/tmp/model",
            feature_set_name="BASELINE_FEATURES",
            features_used_csv="close",
            feature_cols=["close"],
            dataset_parameters={"time_idx": "time_idx"},
            max_encoder_length=2,
            max_prediction_length=1,
            batch_size=8,
            run_id="run_1",
        )
