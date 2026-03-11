from __future__ import annotations

import pandas as pd

from src.use_cases.validate_analytics_quality_use_case import (
    ValidateAnalyticsQualityUseCase,
)


def _write_table(base, table_name: str, rows: list[dict], parts: dict[str, str] | None = None) -> None:
    table_dir = base / table_name
    if parts:
        for k, v in parts.items():
            table_dir = table_dir / f"{k}={v}"
    table_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(table_dir / f"{table_name}.parquet", index=False)


def _seed_minimal_valid_silver(silver) -> None:
    _write_table(
        silver,
        "dim_run",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "execution_id": None,
                "asset": "AAPL",
                "feature_set_name": "B",
                "feature_set_hash": "fh",
                "feature_list_ordered_json": "[]",
                "config_signature": "cfg1",
                "split_fingerprint": "sp1",
                "model_version": "v1",
                "checkpoint_path_final": "/tmp/final.pt",
                "checkpoint_path_best": "/tmp/best.ckpt",
                "git_commit": "abc",
                "pipeline_version": "0.1",
                "library_versions_json": "{}",
                "hardware_info_json": "{}",
                "status": "ok",
                "duration_total_seconds": 1.0,
                "eta_recorded_seconds": 0.0,
                "retries": 0,
                "created_at_utc": "2026-01-01T00:00:00+00:00",
            }
        ],
        {"asset": "AAPL", "sweep_id": "__none__"},
    )
    _write_table(
        silver,
        "fact_run_snapshot",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "parent_sweep_id": None,
                "dataset_start_utc": "2026-01-01T00:00:00+00:00",
                "dataset_end_utc": "2026-01-10T00:00:00+00:00",
                "train_start_utc": "2026-01-01T00:00:00+00:00",
                "train_end_utc": "2026-01-06T00:00:00+00:00",
                "val_start_utc": "2026-01-07T00:00:00+00:00",
                "val_end_utc": "2026-01-08T00:00:00+00:00",
                "test_start_utc": "2026-01-09T00:00:00+00:00",
                "test_end_utc": "2026-01-10T00:00:00+00:00",
                "warmup_policy": "strict_fail",
                "required_warmup_count": 0,
                "warmup_applied": "false",
                "effective_train_start_utc": "2026-01-01T00:00:00+00:00",
                "n_samples_train": 6,
                "n_samples_val": 2,
                "n_samples_test": 2,
                "dataset_fingerprint": "dfp",
                "split_fingerprint": "sfp",
            }
        ],
        {"asset": "AAPL", "sweep_id": "__none__"},
    )
    _write_table(
        silver,
        "fact_split_metrics",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "parent_sweep_id": None,
                "split": "test",
                "rmse": 0.1,
                "mae": 0.1,
                "mape": 0.0,
                "smape": 0.0,
                "directional_accuracy": 0.5,
                "n_samples": 2,
            }
        ],
        {"asset": "AAPL", "sweep_id": "__none__"},
    )
    _write_table(
        silver,
        "fact_config",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "parent_sweep_id": None,
                "prediction_mode": "quantile",
                "loss_name": "QuantileLoss",
                "quantile_levels_json": "[0.1,0.5,0.9]",
                "max_encoder_length": 3,
                "max_prediction_length": 1,
                "batch_size": 8,
                "max_epochs": 2,
                "learning_rate": 0.001,
                "hidden_size": 8,
                "attention_head_size": 2,
                "dropout": 0.1,
                "hidden_continuous_size": 4,
                "early_stopping_patience": 2,
                "early_stopping_min_delta": 0.0,
                "scaler_type": "none",
                "training_config_json": "{}",
                "dataset_parameters_json": "{}",
                "search_space_json": "{}",
                "objective_name": "val_loss",
                "objective_direction": "minimize",
            }
        ],
        {"asset": "AAPL", "sweep_id": "__none__"},
    )
    _write_table(
        silver,
        "fact_epoch_metrics",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "parent_sweep_id": None,
                "fold": "none",
                "epoch": 0,
                "train_loss": 0.8,
                "val_loss": 0.9,
            }
        ],
        {"asset": "AAPL", "sweep_id": "__none__", "fold": "none"},
    )
    _write_table(
        silver,
        "fact_oos_predictions",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "feature_set_name": "B",
                "config_signature": "cfg1",
                "split": "test",
                "fold": "none",
                "seed": 0,
                "horizon": 1,
                "timestamp_utc": "2026-01-09T00:00:00+00:00",
                "target_timestamp_utc": "2026-01-09T00:00:00+00:00",
                "y_true": 0.1,
                "y_pred": 0.2,
                "error": 0.1,
                "abs_error": 0.1,
                "sq_error": 0.01,
                "quantile_p10": 0.1,
                "quantile_p50": 0.2,
                "quantile_p90": 0.3,
                "year": 2026,
            }
        ],
        {"asset": "AAPL", "feature_set_name": "B", "year": "2026"},
    )
    _write_table(
        silver,
        "fact_model_artifacts",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "model_version": "v1",
                "checkpoint_path_final": "/tmp/final.pt",
                "checkpoint_path_best": "/tmp/best.ckpt",
                "config_path": "/tmp/config.json",
                "scaler_path": None,
                "encoder_path": None,
                "feature_importance_json": "[]",
                "attention_summary_json": "{\"available\": false}",
                "logs_ref_json": "{}",
            }
        ],
        {"asset": "AAPL"},
    )
    _write_table(
        silver,
        "bridge_run_features",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "feature_order": 0,
                "feature_name": "close",
            }
        ],
        {"run_id": "r1"},
    )


def test_validate_analytics_quality_passes_on_valid_dataset(tmp_path) -> None:
    silver = tmp_path / "silver"
    _seed_minimal_valid_silver(silver)

    result = ValidateAnalyticsQualityUseCase(analytics_silver_dir=silver).execute()
    assert result.passed is True
    assert len(result.checks) > 0
    assert all(bool(item["passed"]) for item in result.checks)


def test_validate_analytics_quality_fails_when_quantile_contract_is_broken(tmp_path) -> None:
    silver = tmp_path / "silver"
    _seed_minimal_valid_silver(silver)

    # Break quantile contract for official run
    _write_table(
        silver,
        "fact_oos_predictions",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "feature_set_name": "B",
                "config_signature": "cfg1",
                "split": "test",
                "fold": "none",
                "seed": 0,
                "horizon": 1,
                "timestamp_utc": "2026-01-10T00:00:00+00:00",
                "target_timestamp_utc": "2026-01-10T00:00:00+00:00",
                "y_true": 0.1,
                "y_pred": 0.2,
                "error": 0.1,
                "abs_error": 0.1,
                "sq_error": 0.01,
                "quantile_p10": None,
                "quantile_p50": 0.2,
                "quantile_p90": 0.3,
                "year": 2026,
            }
        ],
        {"asset": "AAPL", "feature_set_name": "B", "year": "2026"},
    )

    result = ValidateAnalyticsQualityUseCase(analytics_silver_dir=silver).execute()
    assert result.passed is False
    assert any(
        (item["check"] == "official_contract_quantile_attention" and not bool(item["passed"]))
        for item in result.checks
    )
