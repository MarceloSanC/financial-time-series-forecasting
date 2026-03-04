from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
import torch

from src.entities.tft_inference_record import TFTInferenceRecord
from src.interfaces.tft_inference_engine import TFTInferenceEngine

logger = logging.getLogger(__name__)


class PytorchForecastingTFTInferenceEngine(TFTInferenceEngine):
    @staticmethod
    def _prepare_dataframe_for_dataset(
        *,
        df: pd.DataFrame,
        dataset_parameters: dict[str, Any],
        asset_id: str,
        model_version: str,
        model_path: str,
    ) -> pd.DataFrame:
        prepared = df.copy()
        time_idx_col = str(dataset_parameters.get("time_idx") or "time_idx")
        if time_idx_col not in prepared.columns:
            raise ValueError(
                "[INFER_DATASET_SPEC_INCOMPATIBLE] dataset_parameters.time_idx column not found in data. "
                f"time_idx={time_idx_col} asset={asset_id} model_version={model_version} model_path={model_path}"
            )

        numeric_idx = pd.to_numeric(prepared[time_idx_col], errors="coerce")
        if numeric_idx.isna().any():
            bad = int(numeric_idx.isna().sum())
            raise ValueError(
                "[INFER_DATASET_SPEC_INCOMPATIBLE] time_idx contains non-numeric/null values after coercion. "
                f"time_idx={time_idx_col} invalid_rows={bad} asset={asset_id} "
                f"model_version={model_version} model_path={model_path}"
            )

        if not np.all(np.isclose(numeric_idx.to_numpy(dtype=float), np.round(numeric_idx.to_numpy(dtype=float)))):
            raise ValueError(
                "[INFER_DATASET_SPEC_INCOMPATIBLE] time_idx contains non-integer values. "
                f"time_idx={time_idx_col} asset={asset_id} model_version={model_version} model_path={model_path}"
            )

        prepared[time_idx_col] = numeric_idx.astype("int64")
        return prepared

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
        dataset_parameters: dict[str, Any] | None,
        max_encoder_length: int,
        max_prediction_length: int,
        batch_size: int,
        run_id: str,
    ) -> list[TFTInferenceRecord]:
        try:
            from pytorch_forecasting import TimeSeriesDataSet
        except Exception as exc:
            raise RuntimeError(
                "pytorch-forecasting is required for TFT inference."
            ) from exc

        df = dataset_df.copy().sort_values("time_idx").reset_index(drop=True)
        if len(df) < (max_encoder_length + max_prediction_length):
            raise ValueError(
                "Insufficient rows for inference with selected context window: "
                f"rows={len(df)}, required>={max_encoder_length + max_prediction_length}"
            )

        if not isinstance(dataset_parameters, dict) or not dataset_parameters:
            raise ValueError(
                "[INFER_DATASET_SPEC_MISSING] Model artifact is missing required "
                "dataset_parameters for inference dataset reconstruction via TimeSeriesDataSet.from_parameters. "
                f"asset={asset_id} model_version={model_version} model_path={model_path}"
            )
        prepared_df = self._prepare_dataframe_for_dataset(
            df=df,
            dataset_parameters=dataset_parameters,
            asset_id=asset_id,
            model_version=model_version,
            model_path=model_path,
        )
        try:
            inference_ds = TimeSeriesDataSet.from_parameters(
                dataset_parameters,
                prepared_df,
                predict=True,
                stop_randomization=True,
            )
        except Exception as exc:
            logger.exception(
                "Inference dataset reconstruction from parameters failed",
                extra={"asset_id": asset_id, "model_version": model_version},
            )
            raise ValueError(
                "[INFER_DATASET_SPEC_INCOMPATIBLE] Failed to rebuild TimeSeriesDataSet from "
                "artifact dataset_parameters. This can indicate invalid/incomplete parameters "
                "or incompatibility with current pytorch-forecasting version. "
                f"asset={asset_id} model_version={model_version} model_path={model_path}"
            ) from exc

        loader = inference_ds.to_dataloader(train=False, batch_size=max(1, int(batch_size)), num_workers=0)

        decoder_time_idx: list[int] = []
        for x, _ in iter(loader):
            if "decoder_time_idx" not in x:
                continue
            arr = x["decoder_time_idx"]
            if hasattr(arr, "detach"):
                arr = arr.detach().cpu().numpy()
            else:
                arr = np.asarray(arr)
            if arr.ndim > 1:
                arr = arr[:, 0]
            decoder_time_idx.extend([int(v) for v in arr.tolist()])

        predict_kwargs = {
            "trainer_kwargs": {
                "logger": False,
                "enable_progress_bar": False,
                "enable_model_summary": False,
                "accelerator": "gpu" if torch.cuda.is_available() else "cpu",
                "devices": 1,
            }
        }
        try:
            preds_obj = model.predict(loader, mode="prediction", **predict_kwargs)
        except TypeError:
            preds_obj = model.predict(loader, mode="prediction")

        pred_point = self._to_1d_first_step(self._to_numpy(preds_obj))
        if len(pred_point) != len(decoder_time_idx):
            raise RuntimeError(
                "Inference outputs mismatch sample count: "
                f"preds={len(pred_point)} samples={len(decoder_time_idx)}."
            )

        q10: np.ndarray | None = None
        q50: np.ndarray | None = None
        q90: np.ndarray | None = None
        try:
            try:
                raw_obj = model.predict(loader, mode="raw", **predict_kwargs)
            except TypeError:
                raw_obj = model.predict(loader, mode="raw")
            raw_np = self._to_numpy(raw_obj)
            q10, q50, q90 = self._extract_quantiles(raw_np, model)
        except Exception:
            q10, q50, q90 = None, None, None

        timestamp_by_time_idx = {
            int(ti): pd.Timestamp(ts).to_pydatetime()
            for ti, ts in zip(df["time_idx"].tolist(), df["timestamp"].tolist())
        }

        records: list[TFTInferenceRecord] = []
        for i, time_idx in enumerate(decoder_time_idx):
            ts = timestamp_by_time_idx.get(int(time_idx))
            if ts is None:
                continue
            records.append(
                TFTInferenceRecord(
                    asset_id=asset_id,
                    timestamp=ts,
                    model_version=model_version,
                    model_path=model_path,
                    feature_set_name=feature_set_name,
                    features_used_csv=features_used_csv,
                    prediction=float(pred_point[i]),
                    quantile_p10=float(q10[i]) if q10 is not None else None,
                    quantile_p50=float(q50[i]) if q50 is not None else None,
                    quantile_p90=float(q90[i]) if q90 is not None else None,
                    inference_run_id=run_id,
                )
            )
        return records

    @staticmethod
    def _to_numpy(x: Any) -> np.ndarray:
        if hasattr(x, "prediction"):
            return PytorchForecastingTFTInferenceEngine._to_numpy(getattr(x, "prediction"))
        if hasattr(x, "output"):
            return PytorchForecastingTFTInferenceEngine._to_numpy(getattr(x, "output"))
        if isinstance(x, dict):
            if "prediction" in x:
                return PytorchForecastingTFTInferenceEngine._to_numpy(x["prediction"])
            if "output" in x:
                return PytorchForecastingTFTInferenceEngine._to_numpy(x["output"])
        if hasattr(x, "detach"):
            return x.detach().cpu().numpy()
        if isinstance(x, (list, tuple)):
            parts = [PytorchForecastingTFTInferenceEngine._to_numpy(i) for i in x]
            if not parts:
                return np.asarray([])
            return np.concatenate(parts, axis=0)
        return np.asarray(x)

    @staticmethod
    def _to_1d_first_step(arr: np.ndarray) -> np.ndarray:
        if arr.ndim == 3:
            arr = arr[:, :, arr.shape[2] // 2]
        if arr.ndim > 1:
            arr = arr[:, 0]
        return arr.reshape(-1)

    @staticmethod
    def _extract_quantiles(
        raw_pred: np.ndarray, model: Any
    ) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
        if raw_pred.ndim != 3 or raw_pred.shape[0] == 0:
            return None, None, None

        quantiles = getattr(getattr(model, "loss", None), "quantiles", None)
        if not isinstance(quantiles, (list, tuple)) or len(quantiles) != raw_pred.shape[2]:
            return None, None, None

        def nearest(q: float) -> int:
            return int(np.argmin(np.abs(np.asarray(quantiles, dtype=float) - q)))

        idx10 = nearest(0.1)
        idx50 = nearest(0.5)
        idx90 = nearest(0.9)
        return (
            raw_pred[:, 0, idx10].reshape(-1),
            raw_pred[:, 0, idx50].reshape(-1),
            raw_pred[:, 0, idx90].reshape(-1),
        )
