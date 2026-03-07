from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.entities.tft_inference_record import TFTInferenceRecord
from src.interfaces.tft_inference_model_loader import LoadedTFTInferenceModel
from src.use_cases.run_tft_inference_use_case import RunTFTInferenceUseCase


class _FakeDatasetRepo:
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()

    def load(self, asset_id: str) -> pd.DataFrame:
        return self.df.copy()


class _FakeInferenceRepo:
    def __init__(self) -> None:
        self.rows: list[TFTInferenceRecord] = []

    def get_latest_timestamp(self, asset_id: str):
        if not self.rows:
            return None
        return max(r.timestamp for r in self.rows)

    def list_inference_timestamps(
        self,
        asset_id: str,
        start_date: datetime,
        end_date: datetime,
        *,
        model_version: str | None = None,
        feature_set_name: str | None = None,
    ):
        out = []
        for r in self.rows:
            if not (start_date <= r.timestamp <= end_date):
                continue
            if model_version is not None and r.model_version != model_version:
                continue
            if feature_set_name is not None and r.feature_set_name != feature_set_name:
                continue
            out.append(r.timestamp)
        return set(out)

    def upsert_records(self, asset_id: str, records: list[TFTInferenceRecord]) -> int:
        self.rows.extend(records)
        return len(records)


class _FakeModelLoader:
    def __init__(self, asset_id: str = "AAPL") -> None:
        self.asset_id = asset_id

    def load(self, model_dir: str | Path) -> LoadedTFTInferenceModel:
        return LoadedTFTInferenceModel(
            asset_id=self.asset_id,
            version="20260302_010101_B",
            model_dir=Path(model_dir),
            model=object(),
            feature_cols=["close"],
            feature_set_name="BASELINE_FEATURES",
            feature_tokens=["BASELINE_FEATURES"],
            training_config={"max_encoder_length": 3, "max_prediction_length": 1},
            scalers={},
        )


class _FakeEngine:
    def infer(
        self,
        *,
        model: Any,
        dataset_df: pd.DataFrame,
        asset_id: str,
        model_version: str,
        model_path: str,
        feature_set_name: str,
        features_used_csv: str,
        feature_cols: list[str],
        dataset_parameters: dict | None,
        max_encoder_length: int,
        max_prediction_length: int,
        batch_size: int,
        run_id: str,
    ) -> list[TFTInferenceRecord]:
        out: list[TFTInferenceRecord] = []
        for _, row in dataset_df.iterrows():
            ts = pd.Timestamp(row["timestamp"]).to_pydatetime()
            out.append(
                TFTInferenceRecord(
                    asset_id=asset_id,
                    timestamp=ts,
                    model_version=model_version,
                    model_path=model_path,
                    feature_set_name=feature_set_name,
                    features_used_csv=features_used_csv,
                    prediction=float(row["target_return"]),
                    quantile_p10=-0.1,
                    quantile_p50=0.0,
                    quantile_p90=0.1,
                    inference_run_id=run_id,
                )
            )
        return out


def _dataset(start: datetime, rows: int = 12) -> pd.DataFrame:
    data = []
    for i in range(rows):
        ts = start + timedelta(days=i)
        data.append(
            {
                "timestamp": ts,
                "time_idx": i,
                "asset_id": "AAPL",
                "target_return": 0.001 * i,
                "close": 100.0 + i,
                "day_of_week": i % 7,
                "month": 1,
            }
        )
    return pd.DataFrame(data)


def test_use_case_skips_existing_when_not_overwrite() -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    dataset_repo = _FakeDatasetRepo(_dataset(start))
    inference_repo = _FakeInferenceRepo()
    loader = _FakeModelLoader(asset_id="AAPL")
    engine = _FakeEngine()

    existing_ts = start + timedelta(days=6)
    inference_repo.rows.append(
        TFTInferenceRecord(
            asset_id="AAPL",
            timestamp=existing_ts,
            model_version="20260302_010101_B",
            model_path="/tmp/model",
            feature_set_name="BASELINE_FEATURES",
            features_used_csv="close",
            prediction=0.0,
        )
    )

    use_case = RunTFTInferenceUseCase(
        dataset_repository=dataset_repo,
        inference_repository=inference_repo,
        model_loader=loader,
        inference_engine=engine,
    )

    result = use_case.execute(
        asset_id="AAPL",
        model_path="/tmp/model",
        start_date=start + timedelta(days=5),
        end_date=start + timedelta(days=7),
        overwrite=False,
    )

    assert result.inferred >= 3
    assert result.skipped_existing >= 1
    assert result.attempted_upserts >= 2


def test_use_case_requires_explicit_period_without_history() -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    dataset_repo = _FakeDatasetRepo(_dataset(start))
    inference_repo = _FakeInferenceRepo()
    loader = _FakeModelLoader(asset_id="AAPL")
    engine = _FakeEngine()

    use_case = RunTFTInferenceUseCase(
        dataset_repository=dataset_repo,
        inference_repository=inference_repo,
        model_loader=loader,
        inference_engine=engine,
    )

    with pytest.raises(ValueError, match="No inference history found"):
        use_case.execute(
            asset_id="AAPL",
            model_path="/tmp/model",
            start_date=None,
            end_date=None,
        )


def test_use_case_triggers_refresh_when_end_exceeds_dataset() -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    dataset_repo = _FakeDatasetRepo(_dataset(start, rows=8))
    inference_repo = _FakeInferenceRepo()
    loader = _FakeModelLoader(asset_id="AAPL")
    engine = _FakeEngine()

    called = {"value": False}

    def _refresh(asset_id: str, refresh_start: datetime, refresh_end: datetime, rebuild_start: datetime):
        called["value"] = True
        dataset_repo.df = _dataset(start, rows=12)

    use_case = RunTFTInferenceUseCase(
        dataset_repository=dataset_repo,
        inference_repository=inference_repo,
        model_loader=loader,
        inference_engine=engine,
        refresh_dataset_fn=_refresh,
    )

    result = use_case.execute(
        asset_id="AAPL",
        model_path="/tmp/model",
        start_date=start + timedelta(days=5),
        end_date=start + timedelta(days=9),
    )

    assert called["value"] is True
    assert result.refreshed_dataset is True
    assert result.attempted_upserts > 0


def test_use_case_fail_fast_when_end_exceeds_dataset_and_auto_refresh_disabled() -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    dataset_repo = _FakeDatasetRepo(_dataset(start, rows=8))
    inference_repo = _FakeInferenceRepo()
    loader = _FakeModelLoader(asset_id="AAPL")
    engine = _FakeEngine()

    use_case = RunTFTInferenceUseCase(
        dataset_repository=dataset_repo,
        inference_repository=inference_repo,
        model_loader=loader,
        inference_engine=engine,
        refresh_dataset_fn=None,
    )

    with pytest.raises(ValueError, match="auto-refresh is disabled"):
        use_case.execute(
            asset_id="AAPL",
            model_path="/tmp/model",
            start_date=start + timedelta(days=5),
            end_date=start + timedelta(days=9),
        )


def test_inference_fails_with_clear_diagnostic_when_model_feature_is_missing() -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    df = _dataset(start).drop(columns=["close"])
    dataset_repo = _FakeDatasetRepo(df)
    inference_repo = _FakeInferenceRepo()
    loader = _FakeModelLoader(asset_id="AAPL")
    engine = _FakeEngine()
    use_case = RunTFTInferenceUseCase(
        dataset_repository=dataset_repo,
        inference_repository=inference_repo,
        model_loader=loader,
        inference_engine=engine,
    )

    with pytest.raises(ValueError, match="missing_model_features=.*close"):
        use_case.execute(
            asset_id="AAPL",
            model_path="/tmp/model",
            start_date=start + timedelta(days=5),
            end_date=start + timedelta(days=7),
        )


def test_inference_logs_excess_dataset_features_but_runs(caplog) -> None:
    caplog.set_level(logging.INFO)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    df = _dataset(start)
    df["open"] = df["close"] - 1.0  # feature implemented but unused by model
    dataset_repo = _FakeDatasetRepo(df)
    inference_repo = _FakeInferenceRepo()
    loader = _FakeModelLoader(asset_id="AAPL")
    engine = _FakeEngine()
    use_case = RunTFTInferenceUseCase(
        dataset_repository=dataset_repo,
        inference_repository=inference_repo,
        model_loader=loader,
        inference_engine=engine,
    )

    result = use_case.execute(
        asset_id="AAPL",
        model_path="/tmp/model",
        start_date=start + timedelta(days=5),
        end_date=start + timedelta(days=7),
    )

    assert result.attempted_upserts > 0
    assert any("extra model feature columns not used" in r.message for r in caplog.records)
