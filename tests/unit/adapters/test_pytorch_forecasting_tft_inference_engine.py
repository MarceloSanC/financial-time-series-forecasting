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
        if mode == "quantiles":
            return np.tile(np.array([[[0.1, 0.2, 0.3]]]), (n, 1, 1))
        if mode == "raw":
            return np.tile(np.array([[[0.1, 0.2, 0.3]]]), (n, 1, 1))
        return np.arange(1, n + 1, dtype=float).reshape(-1, 1)


class _FakeModelInvalidQuantiles(_FakeModel):
    def predict(self, loader, mode="prediction", **kwargs):
        n = sum(len(x["decoder_time_idx"]) for x, _ in loader)
        if mode == "quantiles":
            # Invalid layout for quantiles parser; should trigger raw fallback.
            return np.arange(1, n + 1, dtype=float).reshape(-1, 1)
        if mode == "raw":
            return np.tile(np.array([[[0.1, 0.2, 0.3]]]), (n, 1, 1))
        return super().predict(loader, mode=mode, **kwargs)


class _FakeModelEmptyQuantilesAndRaw(_FakeModel):
    def predict(self, loader, mode="prediction", **kwargs):
        n = sum(len(x["decoder_time_idx"]) for x, _ in loader)
        if mode == "quantiles":
            return []
        if mode == "raw":
            return []
        return np.arange(1, n + 1, dtype=float).reshape(-1, 1)

    def __call__(self, x):
        n = len(x["decoder_time_idx"])
        pred = np.tile(np.array([[[0.1, 0.2, 0.3]]], dtype=float), (n, 1, 1))

        class _Out:
            prediction = pred

        return _Out()

    def to_quantiles(self, out):
        return out.prediction

    def eval(self):
        return self

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


def test_extract_quantiles_accepts_2d_prediction_layout() -> None:
    engine = PytorchForecastingTFTInferenceEngine()
    raw = np.array([[0.1, 0.2, 0.3], [0.11, 0.21, 0.31]], dtype=float)
    q10, q50, q90 = engine._extract_quantiles(raw, _FakeModel())
    assert q10 is not None and q50 is not None and q90 is not None
    assert q10.shape == (2,)
    assert q50.shape == (2,)
    assert q90.shape == (2,)


def test_extract_quantiles_accepts_4d_prediction_layout() -> None:
    engine = PytorchForecastingTFTInferenceEngine()
    raw = np.array([[[[0.1, 0.2, 0.3]]], [[[0.11, 0.21, 0.31]]]], dtype=float)
    q10, q50, q90 = engine._extract_quantiles(raw, _FakeModel())
    assert q10 is not None and q50 is not None and q90 is not None
    assert q10.shape == (2,)


def test_extract_quantiles_from_quantile_mode_accepts_2d_layout() -> None:
    engine = PytorchForecastingTFTInferenceEngine()
    raw = np.array([[0.1, 0.2, 0.3], [0.11, 0.21, 0.31]], dtype=float)
    q10, q50, q90 = engine._extract_quantiles_from_quantile_mode(
        raw,
        quantile_levels=[0.1, 0.5, 0.9],
    )
    assert q10 is not None and q50 is not None and q90 is not None
    assert q10.shape == (2,)


def test_engine_falls_back_to_raw_when_quantiles_mode_layout_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_pf_module(monkeypatch, fail_from_parameters=False)
    engine = PytorchForecastingTFTInferenceEngine()
    records = engine.infer(
        model=_FakeModelInvalidQuantiles(),
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


def test_engine_falls_back_to_forward_when_quantiles_and_raw_are_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_pf_module(monkeypatch, fail_from_parameters=False)
    engine = PytorchForecastingTFTInferenceEngine()
    records = engine.infer(
        model=_FakeModelEmptyQuantilesAndRaw(),
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


def test_to_numpy_prefers_output_when_prediction_is_empty() -> None:
    class _Obj:
        prediction = np.asarray([])
        output = np.array([[[0.1, 0.2, 0.3]]], dtype=float)

    arr = PytorchForecastingTFTInferenceEngine._to_numpy(_Obj())
    assert arr.shape == (1, 1, 3)


def _install_fake_pf_module_with_encoder_lengths(
    monkeypatch: pytest.MonkeyPatch,
    *,
    encoder_lengths: list[int],
    decoder_time_idx: list[int],
    capture: dict | None = None,
) -> None:
    fake_pf = types.ModuleType("pytorch_forecasting")

    class _FakeDataset:
        def __init__(self, df: pd.DataFrame, **kwargs):
            self.df = df.copy()

        @classmethod
        def from_parameters(cls, params, df: pd.DataFrame, predict=True, stop_randomization=True):
            if capture is not None:
                capture["predict"] = bool(predict)
            return cls(df)

        def to_dataloader(self, train, batch_size, num_workers):
            dec = np.asarray(decoder_time_idx, dtype=int).reshape(-1, 1)
            enc = np.asarray(encoder_lengths, dtype=int).reshape(-1)
            return [({"decoder_time_idx": dec, "encoder_lengths": enc}, None)]

    fake_pf.TimeSeriesDataSet = _FakeDataset
    monkeypatch.setitem(sys.modules, "pytorch_forecasting", fake_pf)


def test_engine_rolling_inference_sets_target_and_decision_timestamps(monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict = {}
    _install_fake_pf_module_with_encoder_lengths(
        monkeypatch,
        encoder_lengths=[2, 2, 2, 2],
        decoder_time_idx=[2, 3, 4, 5],
        capture=capture,
    )
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

    assert capture.get("predict") is False
    assert len(records) == 4
    assert all(r.horizon == 1 for r in records)
    assert all(r.target_timestamp is not None for r in records)
    assert all(r.decision_timestamp is not None for r in records)
    assert records[0].decision_timestamp < records[0].target_timestamp


def test_engine_skips_samples_without_full_encoder_context(monkeypatch: pytest.MonkeyPatch) -> None:
    # First sample has encoder_length=1 (< max_encoder_length=2) and must be skipped.
    _install_fake_pf_module_with_encoder_lengths(
        monkeypatch,
        encoder_lengths=[1, 2, 2],
        decoder_time_idx=[2, 3, 4],
    )
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

    assert len(records) == 2
    assert records[0].target_timestamp == pd.Timestamp("2026-01-04", tz="UTC").to_pydatetime()
