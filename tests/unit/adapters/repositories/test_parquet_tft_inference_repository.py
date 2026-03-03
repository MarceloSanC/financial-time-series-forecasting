from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.adapters.parquet_tft_inference_repository import ParquetTFTInferenceRepository
from src.entities.tft_inference_record import TFTInferenceRecord


def _dt_utc(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


def _record(*, model_version: str, model_path: str) -> TFTInferenceRecord:
    return TFTInferenceRecord(
        asset_id="AAPL",
        timestamp=_dt_utc(2026, 3, 1),
        model_version=model_version,
        model_path=model_path,
        feature_set_name="BASELINE_FEATURES",
        features_used_csv="close",
        prediction=0.01,
        inference_run_id="run_1",
    )


def test_upsert_rejects_model_version_collision_with_different_model_path(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    repo = ParquetTFTInferenceRepository(output_dir=tmp_path)

    repo.upsert_records(
        "AAPL",
        [_record(model_version="20260303_104320_B", model_path="/tmp/model_a")],
    )

    with pytest.raises(ValueError, match="Invariant violation"):
        repo.upsert_records(
            "AAPL",
            [_record(model_version="20260303_104320_B", model_path="/tmp/model_b")],
        )
