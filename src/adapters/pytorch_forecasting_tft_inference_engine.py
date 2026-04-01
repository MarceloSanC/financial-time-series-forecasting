from __future__ import annotations

import logging
import warnings

from contextlib import contextmanager
from typing import Any

import numpy as np
import pandas as pd
import torch

from src.entities.tft_inference_record import TFTInferenceRecord
from src.interfaces.tft_inference_engine import TFTInferenceEngine

logger = logging.getLogger(__name__)


class PytorchForecastingTFTInferenceEngine(TFTInferenceEngine):
    @staticmethod
    def _safe_shape_and_size(value: Any) -> tuple[tuple[int, ...] | None, int | None]:
        try:
            arr = np.asarray(value)
            return tuple(arr.shape), int(arr.size)
        except Exception:
            return None, None

    @staticmethod
    def _describe_predict_object(obj: Any) -> dict[str, Any]:
        desc: dict[str, Any] = {"type": type(obj).__name__}
        if isinstance(obj, dict):
            desc["dict_keys"] = sorted([str(k) for k in obj.keys()])
        if isinstance(obj, (list, tuple)):
            desc["sequence_len"] = len(obj)
            if len(obj) > 0:
                desc["sequence_first_type"] = type(obj[0]).__name__
        for field in ("prediction", "output"):
            present = False
            value: Any | None = None
            if hasattr(obj, field):
                present = True
                value = getattr(obj, field)
            elif isinstance(obj, dict) and field in obj:
                present = True
                value = obj[field]
            desc[f"{field}_present"] = present
            if present:
                shape, size = PytorchForecastingTFTInferenceEngine._safe_shape_and_size(value)
                desc[f"{field}_shape"] = shape
                desc[f"{field}_size"] = size

        shape, size = PytorchForecastingTFTInferenceEngine._safe_shape_and_size(obj)
        desc["asarray_shape"] = shape
        desc["asarray_size"] = size
        return desc

    @staticmethod
    def _is_effectively_empty(value: Any) -> bool:
        if value is None:
            return True
        if hasattr(value, "numel"):
            try:
                return int(value.numel()) == 0
            except Exception:
                pass
        try:
            arr = np.asarray(value)
            return arr.size == 0
        except Exception:
            return False

    @staticmethod
    @contextmanager
    def _suppress_lightning_predict_logs():
        noisy_loggers = [
            "lightning",
            "lightning.pytorch",
            "lightning.pytorch.utilities.rank_zero",
            "lightning.pytorch.accelerators.cuda",
            "pytorch_lightning",
            "pytorch_lightning.utilities.rank_zero",
        ]
        previous_levels: dict[str, int] = {}
        try:
            for name in noisy_loggers:
                lg = logging.getLogger(name)
                previous_levels[name] = lg.level
                lg.setLevel(logging.ERROR)
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=r".*predict_dataloader.*does not have many workers.*",
                    category=UserWarning,
                )
                yield
        finally:
            for name in noisy_loggers:
                logging.getLogger(name).setLevel(previous_levels.get(name, logging.NOTSET))

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
                predict=False,
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

        def _build_loader():
            return inference_ds.to_dataloader(
                train=False,
                batch_size=max(1, int(batch_size)),
                # Keep single-process loading for deterministic/reliable multi-pass predict
                # (prediction + quantiles/raw) across environments.
                num_workers=0,
            )

        decoder_time_idx: list[int] = []
        encoder_lengths: list[int] = []
        loader_for_index = _build_loader()
        for x, _ in iter(loader_for_index):
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

            enc = x.get("encoder_lengths")
            if enc is None:
                encoder_lengths.extend([int(max_encoder_length)] * int(len(arr)))
            else:
                if hasattr(enc, "detach"):
                    enc = enc.detach().cpu().numpy()
                else:
                    enc = np.asarray(enc)
                encoder_lengths.extend([int(v) for v in np.asarray(enc).reshape(-1).tolist()])

        predict_kwargs = {
            "trainer_kwargs": {
                "logger": False,
                "enable_progress_bar": False,
                "enable_model_summary": False,
                "accelerator": "gpu" if torch.cuda.is_available() else "cpu",
                "devices": 1,
            }
        }
        with self._suppress_lightning_predict_logs():
            prediction_loader = _build_loader()
            try:
                preds_obj = model.predict(prediction_loader, mode="prediction", **predict_kwargs)
            except TypeError:
                preds_obj = model.predict(prediction_loader, mode="prediction")

        pred_point = self._to_1d_first_step(self._to_numpy(preds_obj))
        if len(pred_point) != len(decoder_time_idx):
            raise RuntimeError(
                "Inference outputs mismatch sample count: "
                f"preds={len(pred_point)} samples={len(decoder_time_idx)}."
            )
        if len(encoder_lengths) != len(decoder_time_idx):
            raise RuntimeError(
                "Inference outputs mismatch encoder/context sample count: "
                f"encoder_lengths={len(encoder_lengths)} samples={len(decoder_time_idx)}."
            )

        q10: np.ndarray | None = None
        q50: np.ndarray | None = None
        q90: np.ndarray | None = None
        quantile_levels = getattr(getattr(model, "loss", None), "quantiles", None)
        quantile_levels = (
            [float(q) for q in quantile_levels]
            if isinstance(quantile_levels, (list, tuple)) and quantile_levels
            else [0.1, 0.5, 0.9]
        )
        try:
            with self._suppress_lightning_predict_logs():
                quant_obj = None
                quant_np = None
                try:
                    quant_loader = _build_loader()
                    quant_obj = model.predict(
                        quant_loader,
                        mode="quantiles",
                        mode_kwargs={"quantiles": quantile_levels},
                        **predict_kwargs,
                    )
                except Exception:
                    quant_obj = None

                if quant_obj is not None:
                    quant_np = self._to_numpy(quant_obj)
                    q10, q50, q90 = self._extract_quantiles_from_quantile_mode(
                        quant_np,
                        quantile_levels=quantile_levels,
                    )
                # If quantiles mode returns an unsupported/empty layout, fallback to raw extraction.
                if q10 is None or q50 is None or q90 is None:
                    raw_loader = _build_loader()
                    try:
                        raw_obj = model.predict(raw_loader, mode="raw", **predict_kwargs)
                    except TypeError:
                        raw_obj = model.predict(raw_loader, mode="raw")
                    raw_np = self._to_numpy(raw_obj)
                    q10, q50, q90 = self._extract_quantiles(raw_np, model)
                # Final fallback: direct forward + to_quantiles(out), robust for
                # environments where predict(mode=quantiles/raw) returns empty lists.
                if q10 is None or q50 is None or q90 is None:
                    q10, q50, q90 = self._extract_quantiles_via_forward(
                        model=model,
                        build_loader=_build_loader,
                        quantile_levels=quantile_levels,
                    )
                if q10 is not None and q50 is not None and q90 is not None:
                    if not (len(q10) == len(q50) == len(q90) == len(decoder_time_idx)):
                        raise RuntimeError(
                            "Quantile outputs mismatch sample count: "
                            f"q10={len(q10)} q50={len(q50)} q90={len(q90)} "
                            f"samples={len(decoder_time_idx)}."
                        )
                if q10 is None or q50 is None or q90 is None:
                    raw_shape = None
                    if "raw_np" in locals():
                        raw_shape = tuple(raw_np.shape) if hasattr(raw_np, "shape") else None
                    quant_shape = None
                    if quant_np is not None and hasattr(quant_np, "shape"):
                        quant_shape = tuple(quant_np.shape)
                    loss_q = getattr(getattr(model, "loss", None), "quantiles", None)
                    logger.warning(
                        "Quantile extraction returned empty values during inference",
                        extra={
                            "asset_id": asset_id,
                            "model_version": model_version,
                            "model_path": model_path,
                            "raw_prediction_shape": raw_shape,
                            "quantiles_prediction_shape": quant_shape,
                            "loss_quantiles": list(loss_q) if isinstance(loss_q, (list, tuple)) else None,
                            "quantiles_object_debug": self._describe_predict_object(quant_obj)
                            if quant_obj is not None
                            else None,
                            "raw_object_debug": self._describe_predict_object(raw_obj)
                            if "raw_obj" in locals()
                            else None,
                            "forward_quantiles_fallback_tried": True,
                        },
                    )
        except Exception as exc:
            logger.warning(
                "Quantile extraction failed during inference",
                extra={
                    "asset_id": asset_id,
                    "model_version": model_version,
                    "model_path": model_path,
                    "error": str(exc),
                },
            )
            q10, q50, q90 = None, None, None

        timestamp_by_time_idx = {
            int(ti): pd.Timestamp(ts).to_pydatetime()
            for ti, ts in zip(df["time_idx"].tolist(), df["timestamp"].tolist())
        }

        records: list[TFTInferenceRecord] = []
        for i, time_idx in enumerate(decoder_time_idx):
            if int(encoder_lengths[i]) < int(max_encoder_length):
                continue
            target_ts = timestamp_by_time_idx.get(int(time_idx))
            if target_ts is None:
                continue
            decision_ts = timestamp_by_time_idx.get(int(time_idx) - 1)
            if decision_ts is None:
                continue
            records.append(
                TFTInferenceRecord(
                    asset_id=asset_id,
                    timestamp=target_ts,
                    target_timestamp=target_ts,
                    decision_timestamp=decision_ts,
                    horizon=1,
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
        if hasattr(x, "prediction") and hasattr(x, "output"):
            pred = getattr(x, "prediction")
            out = getattr(x, "output")
            if not PytorchForecastingTFTInferenceEngine._is_effectively_empty(pred):
                return PytorchForecastingTFTInferenceEngine._to_numpy(pred)
            return PytorchForecastingTFTInferenceEngine._to_numpy(out)
        if hasattr(x, "prediction"):
            return PytorchForecastingTFTInferenceEngine._to_numpy(getattr(x, "prediction"))
        if hasattr(x, "output"):
            return PytorchForecastingTFTInferenceEngine._to_numpy(getattr(x, "output"))
        if isinstance(x, dict):
            if "prediction" in x and "output" in x:
                pred = x["prediction"]
                out = x["output"]
                if not PytorchForecastingTFTInferenceEngine._is_effectively_empty(pred):
                    return PytorchForecastingTFTInferenceEngine._to_numpy(pred)
                return PytorchForecastingTFTInferenceEngine._to_numpy(out)
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
        quantiles = getattr(getattr(model, "loss", None), "quantiles", None)
        if not isinstance(quantiles, (list, tuple)):
            return None, None, None

        q_levels = [float(q) for q in quantiles]
        if not q_levels:
            return None, None, None

        arr = np.asarray(raw_pred)
        if arr.ndim == 4 and arr.shape[2] == 1:
            arr = arr[:, :, 0, :]
        elif arr.ndim == 2 and arr.shape[1] == len(q_levels):
            arr = arr[:, np.newaxis, :]

        if arr.ndim != 3 or arr.shape[0] == 0 or arr.shape[2] != len(q_levels):
            return None, None, None

        def nearest(q: float) -> int:
            return int(np.argmin(np.abs(np.asarray(q_levels, dtype=float) - q)))

        idx10 = nearest(0.1)
        idx50 = nearest(0.5)
        idx90 = nearest(0.9)
        return (
            arr[:, 0, idx10].reshape(-1),
            arr[:, 0, idx50].reshape(-1),
            arr[:, 0, idx90].reshape(-1),
        )

    @staticmethod
    def _extract_quantiles_from_quantile_mode(
        quant_pred: Any,
        *,
        quantile_levels: list[float],
    ) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
        arr = PytorchForecastingTFTInferenceEngine._to_numpy(quant_pred)
        arr = np.asarray(arr)
        if arr.ndim == 2 and arr.shape[1] == len(quantile_levels):
            arr = arr[:, np.newaxis, :]
        if arr.ndim == 4 and arr.shape[2] == 1:
            arr = arr[:, :, 0, :]
        if arr.ndim != 3 or arr.shape[2] != len(quantile_levels) or arr.shape[0] == 0:
            return None, None, None

        def nearest(q: float) -> int:
            return int(np.argmin(np.abs(np.asarray(quantile_levels, dtype=float) - q)))

        idx10 = nearest(0.1)
        idx50 = nearest(0.5)
        idx90 = nearest(0.9)
        return (
            arr[:, 0, idx10].reshape(-1),
            arr[:, 0, idx50].reshape(-1),
            arr[:, 0, idx90].reshape(-1),
        )

    def _extract_quantiles_via_forward(
        self,
        *,
        model: Any,
        build_loader: Any,
        quantile_levels: list[float],
    ) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
        rows: list[np.ndarray] = []
        try:
            model.eval()
            model_device = None
            if hasattr(model, "parameters"):
                try:
                    model_device = next(model.parameters()).device
                except Exception:
                    model_device = None
            with torch.no_grad():
                loader = build_loader()
                for batch in loader:
                    x, _ = batch
                    if model_device is not None:
                        moved: dict[str, Any] = {}
                        for k, v in x.items():
                            if hasattr(v, "to"):
                                moved[k] = v.to(model_device)
                            else:
                                moved[k] = v
                        x = moved
                    out = model(x)
                    q = model.to_quantiles(out)
                    q_np = self._to_numpy(q)
                    q_np = np.asarray(q_np)
                    if q_np.ndim == 2 and q_np.shape[1] == len(quantile_levels):
                        q_np = q_np[:, np.newaxis, :]
                    if q_np.ndim == 4 and q_np.shape[2] == 1:
                        q_np = q_np[:, :, 0, :]
                    if q_np.ndim != 3:
                        continue
                    rows.append(q_np)
        except Exception:
            return None, None, None

        if not rows:
            return None, None, None
        arr = np.concatenate(rows, axis=0)
        if arr.ndim != 3 or arr.shape[2] != len(quantile_levels) or arr.shape[0] == 0:
            return None, None, None

        def nearest(q: float) -> int:
            return int(np.argmin(np.abs(np.asarray(quantile_levels, dtype=float) - q)))

        idx10 = nearest(0.1)
        idx50 = nearest(0.5)
        idx90 = nearest(0.9)
        return (
            arr[:, 0, idx10].reshape(-1),
            arr[:, 0, idx50].reshape(-1),
            arr[:, 0, idx90].reshape(-1),
        )
