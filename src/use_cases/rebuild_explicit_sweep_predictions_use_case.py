from __future__ import annotations

import logging

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.adapters.local_tft_inference_model_loader import LocalTFTInferenceModelLoader
from src.adapters.parquet_tft_dataset_repository import ParquetTFTDatasetRepository
from src.adapters.pytorch_forecasting_tft_inference_engine import (
    PytorchForecastingTFTInferenceEngine,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RebuildExplicitSweepPredictionsResult:
    predictions_path: Path
    failures_path: Path
    total_runs: int
    successful_runs: int
    failed_runs: int
    total_rows: int


class RebuildExplicitSweepPredictionsUseCase:
    def __init__(
        self,
        *,
        dataset_repository: ParquetTFTDatasetRepository,
        model_loader: LocalTFTInferenceModelLoader | None = None,
        inference_engine: PytorchForecastingTFTInferenceEngine | None = None,
    ) -> None:
        self.dataset_repository = dataset_repository
        self.model_loader = model_loader or LocalTFTInferenceModelLoader()
        self.inference_engine = inference_engine or PytorchForecastingTFTInferenceEngine()

    @staticmethod
    def _parse_yyyymmdd(value: str) -> datetime:
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=UTC)

    @staticmethod
    def _resolve_fold_split_map(analysis_config: dict[str, Any]) -> dict[str, dict[str, str]]:
        walk_forward = analysis_config.get("walk_forward", {})
        fold_map: dict[str, dict[str, str]] = {}
        if isinstance(walk_forward, dict) and isinstance(walk_forward.get("folds"), list):
            required = {"train_start", "train_end", "val_start", "val_end", "test_start", "test_end"}
            for idx, fold in enumerate(walk_forward.get("folds", []), start=1):
                if not isinstance(fold, dict):
                    continue
                name = str(fold.get("name") or f"fold_{idx}").strip() or f"fold_{idx}"
                split_cfg = {k: str(fold[k]) for k in required if fold.get(k) is not None}
                if required.issubset(set(split_cfg.keys())):
                    fold_map[name] = split_cfg
        if fold_map:
            return fold_map

        split_config = analysis_config.get("split_config")
        required = {"train_start", "train_end", "val_start", "val_end", "test_start", "test_end"}
        if isinstance(split_config, dict) and required.issubset(set(split_config.keys())):
            return {"default": {k: str(split_config[k]) for k in required}}
        return {}

    @staticmethod
    def _apply_scalers(df: pd.DataFrame, scalers: dict) -> pd.DataFrame:
        if not scalers:
            return df
        out = df.copy()
        protected_columns = {"time_idx", "timestamp", "asset_id", "target_return"}
        for col, scaler in scalers.items():
            if col in protected_columns:
                continue
            if col not in out.columns or scaler is None:
                continue
            values = pd.to_numeric(out[col], errors="coerce")
            arr = np.array(values.to_numpy(dtype="float64"), copy=True)
            mask = np.isfinite(arr)
            if mask.any():
                arr[mask] = scaler.transform(arr[mask].reshape(-1, 1)).reshape(-1)
            out[col] = arr
        return out

    @staticmethod
    def _extract_seed(run_label: str) -> int | None:
        marker = "|seed="
        if marker not in run_label:
            return None
        rest = run_label.split(marker, 1)[1]
        token = rest.split("|", 1)[0].strip()
        try:
            return int(token)
        except Exception:
            return None

    @staticmethod
    def _to_utc_timestamp(value: Any) -> pd.Timestamp:
        ts = pd.Timestamp(value)
        if ts.tzinfo is None:
            return ts.tz_localize("UTC")
        return ts.tz_convert("UTC")

    def execute(
        self,
        *,
        sweep_dir: Path,
        asset: str,
        analysis_config: dict[str, Any],
        overwrite: bool = False,
    ) -> RebuildExplicitSweepPredictionsResult:
        analysis_dir = sweep_dir / "explicit_analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        predictions_path = analysis_dir / "predictions_long.parquet"
        failures_path = analysis_dir / "prediction_rebuild_failures.csv"
        if predictions_path.exists() and not overwrite:
            existing = pd.read_parquet(predictions_path)
            return RebuildExplicitSweepPredictionsResult(
                predictions_path=predictions_path,
                failures_path=failures_path,
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                total_rows=int(len(existing)),
            )

        run_df = pd.read_csv(sweep_dir / "sweep_runs.csv")
        run_df = run_df[run_df["status"] == "ok"].copy()
        if run_df.empty:
            pd.DataFrame().to_parquet(predictions_path, index=False)
            pd.DataFrame().to_csv(failures_path, index=False)
            return RebuildExplicitSweepPredictionsResult(
                predictions_path=predictions_path,
                failures_path=failures_path,
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                total_rows=0,
            )

        dataset_df = self.dataset_repository.load(asset).copy()
        dataset_df["timestamp"] = pd.to_datetime(dataset_df["timestamp"], utc=True, errors="raise")
        dataset_df = dataset_df.sort_values("timestamp").reset_index(drop=True)

        fold_split_map = self._resolve_fold_split_map(analysis_config)
        true_target_by_ts = {
            pd.Timestamp(ts).to_pydatetime(): float(v)
            for ts, v in zip(dataset_df["timestamp"].tolist(), dataset_df["target_return"].tolist())
        }

        prediction_rows: list[dict[str, Any]] = []
        failure_rows: list[dict[str, Any]] = []

        for row in run_df.itertuples(index=False):
            fold_name = str(getattr(row, "fold_name"))
            run_label = str(getattr(row, "run_label"))
            config_signature = str(getattr(row, "config_signature"))
            version = str(getattr(row, "version"))
            split_cfg = fold_split_map.get(fold_name)
            if split_cfg is None:
                failure_rows.append(
                    {
                        "fold_name": fold_name,
                        "run_label": run_label,
                        "version": version,
                        "reason": "missing_fold_split_config",
                    }
                )
                continue

            model_dir = sweep_dir / "folds" / fold_name / "models" / version
            try:
                model_bundle = self.model_loader.load(model_dir)
                max_encoder_length = int(model_bundle.training_config.get("max_encoder_length", 0))
                max_prediction_length = int(model_bundle.training_config.get("max_prediction_length", 1))
                if max_encoder_length < 1 or max_prediction_length < 1:
                    raise ValueError("invalid_encoder_or_prediction_length")

                test_start = self._parse_yyyymmdd(split_cfg["test_start"])
                test_end = self._parse_yyyymmdd(split_cfg["test_end"])

                target_mask = (dataset_df["timestamp"] >= pd.Timestamp(test_start)) & (
                    dataset_df["timestamp"] <= pd.Timestamp(test_end)
                )
                target_idx = dataset_df.index[target_mask].tolist()
                if not target_idx:
                    raise ValueError("no_rows_inside_test_period")
                first_target_idx = int(target_idx[0])
                last_target_idx = int(target_idx[-1])
                if first_target_idx < max_encoder_length:
                    raise ValueError("insufficient_context_window")

                inference_slice = dataset_df.iloc[
                    first_target_idx - max_encoder_length : last_target_idx + 1
                ].copy()
                inference_slice = self._apply_scalers(inference_slice, model_bundle.scalers)
                required_cols = {
                    "timestamp",
                    "time_idx",
                    "asset_id",
                    "target_return",
                    *model_bundle.feature_cols,
                }
                missing = [c for c in required_cols if c not in inference_slice.columns]
                if missing:
                    raise ValueError(f"missing_columns:{sorted(missing)}")

                records = self.inference_engine.infer(
                    model=model_bundle.model,
                    dataset_df=inference_slice,
                    asset_id=asset,
                    model_version=model_bundle.version,
                    model_path=str(model_bundle.model_dir),
                    feature_set_name=model_bundle.feature_set_name,
                    features_used_csv=",".join(model_bundle.feature_cols),
                    feature_cols=model_bundle.feature_cols,
                    dataset_parameters=model_bundle.dataset_parameters,
                    max_encoder_length=max_encoder_length,
                    max_prediction_length=max_prediction_length,
                    batch_size=256,
                    run_id=f"rebuild_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
                )
                records = [
                    r
                    for r in records
                    if self._to_utc_timestamp(r.timestamp) >= pd.Timestamp(test_start)
                    and self._to_utc_timestamp(r.timestamp) <= pd.Timestamp(test_end)
                ]

                seed = self._extract_seed(run_label)
                for rec in records:
                    y_true = true_target_by_ts.get(pd.Timestamp(rec.timestamp).to_pydatetime())
                    if y_true is None:
                        continue
                    err = float(y_true) - float(rec.prediction)
                    prediction_rows.append(
                        {
                            "fold_name": fold_name,
                            "run_label": run_label,
                            "seed": seed,
                            "config_signature": config_signature,
                            "version": version,
                            "timestamp": self._to_utc_timestamp(rec.timestamp),
                            "y_true": float(y_true),
                            "y_pred": float(rec.prediction),
                            "error": float(err),
                            "squared_error": float(err * err),
                            "abs_error": float(abs(err)),
                        }
                    )
            except Exception as exc:
                failure_rows.append(
                    {
                        "fold_name": fold_name,
                        "run_label": run_label,
                        "version": version,
                        "reason": str(exc),
                    }
                )
                logger.warning(
                    "Failed to rebuild predictions for run",
                    extra={"fold_name": fold_name, "run_label": run_label, "version": version},
                )

        pred_df = pd.DataFrame(prediction_rows)
        if not pred_df.empty:
            pred_df = pred_df.sort_values(["fold_name", "config_signature", "seed", "timestamp"]).reset_index(
                drop=True
            )
        pred_df.to_parquet(predictions_path, index=False)
        pd.DataFrame(failure_rows).to_csv(failures_path, index=False)
        return RebuildExplicitSweepPredictionsResult(
            predictions_path=predictions_path,
            failures_path=failures_path,
            total_runs=int(len(run_df)),
            successful_runs=int(run_df["run_label"].nunique() - len({f["run_label"] for f in failure_rows})),
            failed_runs=int(len({f["run_label"] for f in failure_rows})),
            total_rows=int(len(pred_df)),
        )
