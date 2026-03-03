from __future__ import annotations

TFT_INFERENCE_COLUMNS = [
    "asset_id",
    "timestamp",
    "model_version",
    "model_path",
    "feature_set_name",
    "features_used_csv",
    "prediction",
    "quantile_p10",
    "quantile_p50",
    "quantile_p90",
    "inference_run_id",
    "created_at",
]

TFT_INFERENCE_DTYPES = {
    "asset_id": "string",
    "model_version": "string",
    "model_path": "string",
    "feature_set_name": "string",
    "features_used_csv": "string",
    "prediction": "float64",
    "quantile_p10": "float64",
    "quantile_p50": "float64",
    "quantile_p90": "float64",
    "inference_run_id": "string",
}
