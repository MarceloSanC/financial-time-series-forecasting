from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path

import pandas as pd

from src.domain.time.utc import require_tz_aware, to_utc
from src.entities.tft_inference_record import TFTInferenceRecord
from src.infrastructure.schemas.tft_inference_parquet_schema import (
    TFT_INFERENCE_COLUMNS,
    TFT_INFERENCE_DTYPES,
)
from src.interfaces.tft_inference_repository import TFTInferenceRepository

logger = logging.getLogger(__name__)


class ParquetTFTInferenceRepository(TFTInferenceRepository):
    """
    Parquet repository for TFT inference outputs.

    Storage layout:
      data/processed/inference_tft/AAPL/inference_tft_AAPL.parquet
    """

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        if self.output_dir.exists() and not self.output_dir.is_dir():
            raise NotADirectoryError(
                f"Inference output_dir is not a directory: {self.output_dir.resolve()}"
            )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalize_symbol(asset_id: str) -> str:
        return asset_id.split(".")[0].upper()

    def _asset_dir(self, asset_id: str) -> Path:
        symbol = self._normalize_symbol(asset_id)
        return self.output_dir / symbol

    def _filepath(self, asset_id: str) -> Path:
        symbol = self._normalize_symbol(asset_id)
        return self._asset_dir(symbol) / f"inference_tft_{symbol}.parquet"

    def _load_df(self, asset_id: str) -> pd.DataFrame:
        path = self._filepath(asset_id)
        if not path.exists():
            return pd.DataFrame(columns=TFT_INFERENCE_COLUMNS)
        df = pd.read_parquet(path)
        if df.empty:
            return pd.DataFrame(columns=TFT_INFERENCE_COLUMNS)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
        missing = set(TFT_INFERENCE_COLUMNS) - set(df.columns)
        for col in missing:
            df[col] = pd.NA
        return df[TFT_INFERENCE_COLUMNS]

    def get_latest_timestamp(self, asset_id: str) -> datetime | None:
        df = self._load_df(asset_id)
        if df.empty:
            return None
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce").dropna()
        if ts.empty:
            return None
        return ts.max().to_pydatetime()

    def list_inference_timestamps(
        self,
        asset_id: str,
        start_date: datetime,
        end_date: datetime,
        *,
        model_version: str | None = None,
        feature_set_name: str | None = None,
    ) -> set[datetime]:
        require_tz_aware(start_date, "start_date")
        require_tz_aware(end_date, "end_date")
        start_utc = to_utc(start_date)
        end_utc = to_utc(end_date)
        if start_utc > end_utc:
            raise ValueError("start_date must be <= end_date")

        df = self._load_df(asset_id)
        if df.empty:
            return set()

        if model_version is not None and "model_version" in df.columns:
            df = df[df["model_version"] == model_version]
        if feature_set_name is not None and "feature_set_name" in df.columns:
            df = df[df["feature_set_name"] == feature_set_name]

        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        mask = (ts >= pd.Timestamp(start_utc)) & (ts <= pd.Timestamp(end_utc))
        selected = ts.loc[mask].dropna()
        return {t.to_pydatetime() for t in selected}

    def upsert_records(self, asset_id: str, records: list[TFTInferenceRecord]) -> int:
        if not records:
            return 0

        symbol = self._normalize_symbol(asset_id)
        if any(self._normalize_symbol(r.asset_id) != symbol for r in records):
            raise ValueError("All inference records must share the same asset_id.")

        rows: list[dict] = []
        created_at = datetime.now(timezone.utc)
        for r in records:
            require_tz_aware(r.timestamp, "timestamp")
            rows.append(
                {
                    "asset_id": symbol,
                    "timestamp": to_utc(r.timestamp),
                    "model_version": r.model_version,
                    "model_path": r.model_path,
                    "feature_set_name": r.feature_set_name,
                    "features_used_csv": r.features_used_csv,
                    "prediction": float(r.prediction),
                    "quantile_p10": (
                        float(r.quantile_p10) if r.quantile_p10 is not None else None
                    ),
                    "quantile_p50": (
                        float(r.quantile_p50) if r.quantile_p50 is not None else None
                    ),
                    "quantile_p90": (
                        float(r.quantile_p90) if r.quantile_p90 is not None else None
                    ),
                    "inference_run_id": r.inference_run_id,
                    "created_at": created_at,
                }
            )

        df_new = pd.DataFrame(rows)
        df_new["timestamp"] = pd.to_datetime(df_new["timestamp"], utc=True, errors="raise")
        df_new["created_at"] = pd.to_datetime(df_new["created_at"], utc=True, errors="raise")
        for col, dtype in TFT_INFERENCE_DTYPES.items():
            if col in df_new.columns:
                df_new[col] = df_new[col].astype(dtype)

        df_old = self._load_df(asset_id)
        df = pd.concat([df_old, df_new], ignore_index=True)
        df = df.drop_duplicates(
            subset=["asset_id", "timestamp", "model_version"],
            keep="last",
        )
        df = df.sort_values(["timestamp", "model_version"]).reset_index(drop=True)

        path = self._filepath(asset_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)

        logger.info(
            "TFT inference rows persisted",
            extra={
                "asset_id": symbol,
                "saved_rows": len(df_new),
                "total_rows": len(df),
                "path": str(path.resolve()),
            },
        )
        return len(df_new)
