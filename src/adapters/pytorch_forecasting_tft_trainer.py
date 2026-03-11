from __future__ import annotations

import logging
import tempfile
import time
import warnings

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from tqdm.auto import tqdm

from src.interfaces.model_trainer import ModelTrainer, TrainingResult


@dataclass(frozen=True)
class TFTTrainingConfig:
    max_encoder_length: int = 60
    max_prediction_length: int = 1
    batch_size: int = 64
    max_epochs: int = 20
    learning_rate: float = 1e-3
    hidden_size: int = 16
    attention_head_size: int = 2
    dropout: float = 0.1
    hidden_continuous_size: int = 8
    seed: int = 42
    early_stopping_patience: int = 5
    early_stopping_min_delta: float = 0.0
    prediction_mode: str = "quantile"
    quantile_levels: tuple[float, ...] = (0.1, 0.5, 0.9)
    evaluate_train_split: bool = False
    compute_feature_importance: bool = False


class PytorchForecastingTFTTrainer(ModelTrainer):
    """
    Temporal Fusion Transformer trainer using pytorch-forecasting.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    @contextmanager
    def _suppress_lightning_predict_logs():
        """
        Silence noisy Lightning startup logs created by repeated internal
        Trainer instantiation during `model.predict(...)`, while keeping
        regular training logs intact.
        """
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
    def _resolve_config(config: dict) -> TFTTrainingConfig:
        merged = {**TFTTrainingConfig().__dict__, **(config or {})}
        allowed = set(TFTTrainingConfig().__dict__.keys())
        filtered = {k: v for k, v in merged.items() if k in allowed}

        raw_levels = filtered.get("quantile_levels", (0.1, 0.5, 0.9))
        if isinstance(raw_levels, (list, tuple)) and raw_levels:
            filtered["quantile_levels"] = tuple(float(x) for x in raw_levels)
        else:
            filtered["quantile_levels"] = (0.1, 0.5, 0.9)
        filtered["prediction_mode"] = str(filtered.get("prediction_mode", "quantile")).strip().lower()
        return TFTTrainingConfig(**filtered)

    def train(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        *,
        feature_cols: list[str],
        target_col: str,
        time_idx_col: str,
        group_col: str,
        known_real_cols: list[str],
        config: dict,
    ) -> TrainingResult:
        try:
            import torch

            from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
            from pytorch_forecasting.metrics import QuantileLoss
            try:
                from lightning.pytorch import Trainer, seed_everything
                from lightning.pytorch.callbacks import (
                    Callback,
                    EarlyStopping,
                    ModelCheckpoint,
                )
            except Exception:
                from pytorch_lightning import Trainer, seed_everything
                from pytorch_lightning.callbacks import (
                    Callback,
                    EarlyStopping,
                    ModelCheckpoint,
                )
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "pytorch-forecasting is required for TFT training. "
                "Install dependencies before running training."
            ) from exc

        cfg = self._resolve_config(config)
        seed_everything(cfg.seed, workers=True)

        train_df = train_df.copy().sort_values(time_idx_col).reset_index(drop=True)
        val_df = val_df.copy().sort_values(time_idx_col).reset_index(drop=True)
        test_df = test_df.copy().sort_values(time_idx_col).reset_index(drop=True)

        class HistoryCallback(Callback):
            def __init__(self) -> None:
                self.history: list[dict[str, float]] = []
                self._epoch_start_time: float | None = None
                self._epoch_durations: dict[int, float] = {}

            def on_train_epoch_start(self, trainer: Trainer, pl_module: Any) -> None:
                self._epoch_start_time = time.perf_counter()

            def on_train_epoch_end(self, trainer: Trainer, pl_module: Any) -> None:
                if self._epoch_start_time is None:
                    return
                epoch = int(getattr(trainer, "current_epoch", -1))
                self._epoch_durations[epoch] = float(time.perf_counter() - self._epoch_start_time)
                self._epoch_start_time = None

            def on_validation_epoch_end(self, trainer: Trainer, pl_module: Any) -> None:
                epoch = int(getattr(trainer, "current_epoch", -1))
                metrics: dict[str, float] = {"epoch": float(epoch)}
                for k, v in trainer.callback_metrics.items():
                    if k in {"train_loss", "val_loss"}:
                        try:
                            metrics[k] = float(v.detach().cpu().item())
                        except Exception:
                            pass
                if epoch in self._epoch_durations:
                    metrics["epoch_time_seconds"] = float(self._epoch_durations[epoch])

                try:
                    optimizers = getattr(trainer, "optimizers", [])
                    if optimizers and getattr(optimizers[0], "param_groups", None):
                        metrics["learning_rate"] = float(optimizers[0].param_groups[0].get("lr"))
                except Exception:
                    pass

                if "train_loss" in metrics and "val_loss" in metrics:
                    self.history.append(metrics)

        class EpochMetricsPrinter(Callback):
            def on_validation_epoch_end(self, trainer: Trainer, pl_module: Any) -> None:
                m = trainer.callback_metrics
                train_loss = m.get("train_loss")
                val_loss = m.get("val_loss")
                try:
                    train_loss_value = (
                        float(train_loss.detach().cpu().item())
                        if train_loss is not None
                        else float("nan")
                    )
                except Exception:
                    train_loss_value = float("nan")
                try:
                    val_loss_value = (
                        float(val_loss.detach().cpu().item())
                        if val_loss is not None
                        else float("nan")
                    )
                except Exception:
                    val_loss_value = float("nan")
                epoch = getattr(trainer, "current_epoch", -1)
                tqdm.write(
                    f"[epoch={epoch}] "
                    f"train_loss={train_loss_value:.6f} "
                    f"val_loss={val_loss_value:.6f}"
                )

        history_cb = HistoryCallback()
        metrics_printer_cb = EpochMetricsPrinter()

        training = TimeSeriesDataSet(
            train_df,
            time_idx=time_idx_col,
            target=target_col,
            group_ids=[group_col],
            max_encoder_length=cfg.max_encoder_length,
            max_prediction_length=cfg.max_prediction_length,
            time_varying_known_reals=known_real_cols,
            time_varying_unknown_reals=feature_cols,
        )
        validation = TimeSeriesDataSet.from_dataset(
            training, val_df, predict=False, stop_randomization=True
        )
        testing = TimeSeriesDataSet.from_dataset(
            training, test_df, predict=False, stop_randomization=True
        )

        train_dataloader = training.to_dataloader(train=True, batch_size=cfg.batch_size, num_workers=0)
        train_eval_dataloader = training.to_dataloader(
            train=False, batch_size=cfg.batch_size, num_workers=0
        )
        val_dataloader = validation.to_dataloader(train=False, batch_size=cfg.batch_size, num_workers=0)
        test_dataloader = testing.to_dataloader(train=False, batch_size=cfg.batch_size, num_workers=0)

        if cfg.prediction_mode == "point":
            try:
                from pytorch_forecasting.metrics import MAE
            except Exception as exc:
                raise RuntimeError(
                    "prediction_mode='point' requires MAE metric available in pytorch-forecasting."
                ) from exc
            loss_fn = MAE()
        else:
            loss_fn = QuantileLoss(quantiles=list(cfg.quantile_levels))

        model = TemporalFusionTransformer.from_dataset(
            training,
            learning_rate=cfg.learning_rate,
            hidden_size=cfg.hidden_size,
            attention_head_size=cfg.attention_head_size,
            dropout=cfg.dropout,
            hidden_continuous_size=cfg.hidden_continuous_size,
            loss=loss_fn,
        )

        checkpoint_dir = tempfile.mkdtemp(prefix="tft_ckpt_")
        checkpoint_cb = ModelCheckpoint(
            dirpath=checkpoint_dir,
            filename="best",
            monitor="val_loss",
            mode="min",
            save_top_k=1,
        )
        early_stopping_cb = EarlyStopping(
            monitor="val_loss",
            mode="min",
            patience=cfg.early_stopping_patience,
            min_delta=cfg.early_stopping_min_delta,
        )

        trainer = Trainer(
            max_epochs=cfg.max_epochs,
            enable_checkpointing=True,
            logger=False,
            callbacks=[history_cb, metrics_printer_cb, checkpoint_cb, early_stopping_cb],
        )
        trainer.fit(model, train_dataloader, val_dataloader)

        best_model = model
        best_checkpoint_path = checkpoint_cb.best_model_path or None
        if best_checkpoint_path:
            try:
                # PyTorch 2.6 defaults torch.load(..., weights_only=True), which
                # can fail for TFT checkpoints containing custom objects.
                try:
                    checkpoint = torch.load(
                        best_checkpoint_path,
                        map_location="cpu",
                        weights_only=False,
                    )
                except TypeError:
                    checkpoint = torch.load(best_checkpoint_path, map_location="cpu")

                state_dict = checkpoint.get("state_dict", checkpoint)
                best_model.load_state_dict(state_dict)
            except Exception:
                # Fallback for compatibility with mocked/unit environments.
                try:
                    best_model = TemporalFusionTransformer.load_from_checkpoint(best_checkpoint_path)
                except Exception as checkpoint_exc:
                    raise RuntimeError(
                        f"Failed to restore best checkpoint: {best_checkpoint_path}"
                    ) from checkpoint_exc

        predict_kwargs = {
            "trainer_kwargs": {
                "logger": False,
                "enable_progress_bar": False,
                "enable_model_summary": False,
            }
        }

        def _manual_forward_arrays(dataloader, split_name: str):
            pred_batches = []
            actual_batches = []
            for x, y in iter(dataloader):
                with torch.no_grad():
                    out = best_model(x)
                if isinstance(out, dict):
                    pred = out.get("prediction", out.get("output", out))
                elif hasattr(out, "prediction"):
                    pred = out.prediction
                elif hasattr(out, "output"):
                    pred = out.output
                else:
                    pred = out

                if not hasattr(pred, "detach"):
                    pred = torch.as_tensor(pred)
                if pred.ndim == 3:
                    pred = pred[:, :, pred.shape[2] // 2]
                if pred.ndim > 1:
                    pred = pred[:, 0]

                act = y[0]
                if act.ndim > 1:
                    act = act[:, 0]

                pred_batches.append(pred.detach().cpu())
                actual_batches.append(act.detach().cpu())

            if len(pred_batches) == 0:
                raise RuntimeError(
                    f"Manual forward produced no batches for split '{split_name}'."
                )

            preds_np = torch.cat(pred_batches, dim=0).numpy()
            actuals_np = torch.cat(actual_batches, dim=0).numpy()
            return preds_np, actuals_np

        def _extract_quantiles(raw_pred_np: np.ndarray) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
            quantiles = getattr(getattr(best_model, "loss", None), "quantiles", None)
            if not isinstance(quantiles, (list, tuple)):
                return None, None, None
            if raw_pred_np.ndim == 3:
                qmat = raw_pred_np[:, 0, :]
            elif raw_pred_np.ndim == 2:
                qmat = raw_pred_np
            else:
                return None, None, None
            if qmat.shape[1] != len(quantiles):
                return None, None, None

            q_arr = np.asarray([float(q) for q in quantiles], dtype=float)
            def _idx(target: float) -> int:
                return int(np.argmin(np.abs(q_arr - target)))

            return qmat[:, _idx(0.1)], qmat[:, _idx(0.5)], qmat[:, _idx(0.9)]

        def _predict_and_metrics(split_name: str, dataloader, *, collect_predictions: bool = False) -> tuple[dict[str, float], dict[str, list[float]] | None]:
            with self._suppress_lightning_predict_logs():
                try:
                    preds = best_model.predict(dataloader, mode="prediction", **predict_kwargs)
                except TypeError:
                    preds = best_model.predict(dataloader, mode="prediction")
            actuals = torch.cat([y[0] for _, y in iter(dataloader)], dim=0)


            def _to_numpy(x):
                # pytorch-forecasting Prediction/Output objects expose fields like
                # `.prediction` or `.output`; handle them before tuple/list fallback.
                if hasattr(x, "prediction"):
                    return _to_numpy(getattr(x, "prediction"))
                if hasattr(x, "output"):
                    return _to_numpy(getattr(x, "output"))
                if isinstance(x, dict):
                    if "prediction" in x:
                        return _to_numpy(x["prediction"])
                    if "output" in x:
                        return _to_numpy(x["output"])
                if hasattr(x, "detach"):
                    return x.detach().cpu().numpy()
                if isinstance(x, (list, tuple)):
                    parts = [_to_numpy(item) for item in x]
                    if len(parts) == 0:
                        raise RuntimeError(
                            f"Model predict returned empty output for split '{split_name}' evaluation."
                        )
                    return np.concatenate(parts, axis=0)
                return np.asarray(x)

            try:
                preds_np = _to_numpy(preds)
                actuals_np = _to_numpy(actuals)
            except RuntimeError as err:
                if "empty output" not in str(err):
                    raise
                preds_np, actuals_np = _manual_forward_arrays(dataloader, split_name)

            if preds_np.ndim > 1:
                preds_np = preds_np[:, 0]
            if actuals_np.ndim > 1:
                actuals_np = actuals_np[:, 0]
            if preds_np.shape[0] != actuals_np.shape[0]:
                raise RuntimeError(
                    "Model predict output length does not match target length "
                    f"(preds={preds_np.shape[0]}, actuals={actuals_np.shape[0]})."
                )

            q10_np: np.ndarray | None = None
            q50_np: np.ndarray | None = None
            q90_np: np.ndarray | None = None
            if collect_predictions and cfg.prediction_mode == "quantile":
                try:
                    with self._suppress_lightning_predict_logs():
                        try:
                            raw_preds = best_model.predict(dataloader, mode="raw", **predict_kwargs)
                        except TypeError:
                            raw_preds = best_model.predict(dataloader, mode="raw")
                    raw_np = _to_numpy(raw_preds)
                    q10_np, q50_np, q90_np = _extract_quantiles(raw_np)
                except Exception:
                    q10_np, q50_np, q90_np = None, None, None

            if q10_np is None:
                q10_np = preds_np.copy()
            if q50_np is None:
                q50_np = preds_np.copy()
            if q90_np is None:
                q90_np = preds_np.copy()

            direction_acc = float(np.mean(np.sign(preds_np) == np.sign(actuals_np)))
            metrics_out = {
                "rmse": float(np.sqrt(np.mean((preds_np - actuals_np) ** 2))),
                "mae": float(np.mean(np.abs(preds_np - actuals_np))),
                "directional_accuracy": direction_acc,
            }
            if not collect_predictions:
                return metrics_out, None

            details = {
                "y_true": actuals_np.astype(float).tolist(),
                "y_pred": preds_np.astype(float).tolist(),
                "quantile_p10": q10_np.astype(float).tolist(),
                "quantile_p50": q50_np.astype(float).tolist(),
                "quantile_p90": q90_np.astype(float).tolist(),
                "horizon": [1.0] * int(preds_np.shape[0]),
            }
            return metrics_out, details

        split_metrics: dict[str, dict[str, float]] = {}
        split_predictions: dict[str, dict[str, list[float]]] = {}
        eval_splits = [("val", val_dataloader), ("test", test_dataloader)]
        if bool(cfg.evaluate_train_split):
            eval_splits.insert(0, ("train", train_eval_dataloader))

        for split_name, loader in eval_splits:
            metrics_row, details_row = _predict_and_metrics(split_name, loader, collect_predictions=True)
            split_metrics[split_name] = metrics_row
            if details_row is not None:
                split_predictions[split_name] = details_row

        baseline_test = split_metrics["test"]
        feature_importance: list[dict[str, float | str]] = []
        if bool(cfg.compute_feature_importance):
            rng = np.random.default_rng(cfg.seed)
            for feature in feature_cols:
                if feature not in test_df.columns:
                    continue
                permuted_test = test_df.copy()
                permuted_test[feature] = rng.permutation(permuted_test[feature].to_numpy())
                permuted_dataset = TimeSeriesDataSet.from_dataset(
                    training, permuted_test, predict=True, stop_randomization=True
                )
                permuted_loader = permuted_dataset.to_dataloader(
                    train=False, batch_size=cfg.batch_size, num_workers=0
                )
                permuted_metrics, _ = _predict_and_metrics(
                    f"test_permuted_{feature}",
                    permuted_loader,
                    collect_predictions=False,
                )
                feature_importance.append(
                    {
                        "feature": feature,
                        "baseline_rmse": float(baseline_test["rmse"]),
                        "permuted_rmse": float(permuted_metrics["rmse"]),
                        "delta_rmse": float(permuted_metrics["rmse"] - baseline_test["rmse"]),
                        "baseline_mae": float(baseline_test["mae"]),
                        "permuted_mae": float(permuted_metrics["mae"]),
                        "delta_mae": float(permuted_metrics["mae"] - baseline_test["mae"]),
                    }
                )
            feature_importance.sort(key=lambda x: x["delta_rmse"], reverse=True)

        metrics = split_metrics["val"]

        history_out: list[dict[str, float]] = []
        if history_cb.history:
            best_idx = int(np.argmin([h.get("val_loss", np.inf) for h in history_cb.history]))
            best_epoch = int(history_cb.history[best_idx].get("epoch", best_idx))
            stopped_epoch = int(history_cb.history[-1].get("epoch", len(history_cb.history) - 1))
            early_stop_reason = "early_stopping" if (stopped_epoch + 1) < int(cfg.max_epochs) else "max_epochs"
            for h in history_cb.history:
                row = dict(h)
                row["best_epoch"] = float(best_epoch)
                row["stopped_epoch"] = float(stopped_epoch)
                row["early_stop_reason"] = early_stop_reason
                history_out.append(row)

        return TrainingResult(
            model=best_model,
            metrics=metrics,
            history=history_out,
            split_metrics=split_metrics,
            feature_importance=feature_importance,
            checkpoint_path=best_checkpoint_path,
            dataset_parameters=training.get_parameters(),
            split_predictions=split_predictions,
        )
