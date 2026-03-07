# src/infrastructure/schemas/model_artifact_schema.py

MODEL_METADATA_FIELDS = {
    "model_type",
    "asset_id",
    "created_at",
    "training_window",
    "features_used",
    "scaler_type",
    "version",
}

TFT_TRAINING_DEFAULTS = {
    "max_encoder_length": 60,
    "max_prediction_length": 1,
    "batch_size": 64,
    "max_epochs": 20,
    "learning_rate": 5e-4,
    "hidden_size": 32,
    "attention_head_size": 2,
    "dropout": 0.1,
    "hidden_continuous_size": 8,
    "seed": 42,
    "early_stopping_patience": 5,
    "early_stopping_min_delta": 0.0,
    "warmup_policy": "strict_fail",
    "min_samples_train": 1,
    "min_samples_val": 1,
    "min_samples_test": 1,
    "quality_gate_max_nan_ratio_per_feature": 1.0,
    "quality_gate_min_temporal_coverage_days": 1,
    "quality_gate_require_unique_timestamps": True,
    "quality_gate_require_monotonic_timestamps": True,
}

TFT_TRAINING_LIMITS = {
    "max_encoder_length": {"min": 2},
    "max_prediction_length": {"min": 1},
    "batch_size": {"min": 1},
    "max_epochs": {"min": 1},
    "learning_rate": {"min_exclusive": 0.0},
    "hidden_size": {"min": 1},
    "attention_head_size": {"min": 1},
    "dropout": {"min": 0.0, "max": 1.0},
    "hidden_continuous_size": {"min": 1},
    "early_stopping_patience": {"min": 0},
    "early_stopping_min_delta": {"min": 0.0},
    "min_samples_train": {"min": 1},
    "min_samples_val": {"min": 1},
    "min_samples_test": {"min": 1},
    "quality_gate_max_nan_ratio_per_feature": {"min": 0.0, "max": 1.0},
    "quality_gate_min_temporal_coverage_days": {"min": 1},
}

TFT_WARMUP_POLICIES = {"strict_fail", "drop_leading"}

TFT_SPLIT_DEFAULTS = {
    "train_start": "20100101",
    "train_end": "20221231",
    "val_start": "20230101",
    "val_end": "20241231",
    "test_start": "20250101",
    "test_end": "20251231",
}


def validate_tft_training_config(config: dict) -> None:
    if "max_prediction_length" in config and "max_encoder_length" in config:
        if int(config["max_prediction_length"]) > int(config["max_encoder_length"]):
            raise ValueError(
                "Invalid config: max_prediction_length must be <= max_encoder_length"
            )

    for key, rule in TFT_TRAINING_LIMITS.items():
        if key not in config or config[key] is None:
            continue

        value = config[key]
        if "min" in rule and value < rule["min"]:
            raise ValueError(f"Invalid config: {key} must be >= {rule['min']}")
        if "max" in rule and value > rule["max"]:
            raise ValueError(f"Invalid config: {key} must be <= {rule['max']}")
        if "min_exclusive" in rule and value <= rule["min_exclusive"]:
            raise ValueError(
                f"Invalid config: {key} must be > {rule['min_exclusive']}"
            )

    if "quality_gate_require_unique_timestamps" in config and not isinstance(
        config["quality_gate_require_unique_timestamps"], bool
    ):
        raise ValueError(
            "Invalid config: quality_gate_require_unique_timestamps must be boolean"
        )
    if "quality_gate_require_monotonic_timestamps" in config and not isinstance(
        config["quality_gate_require_monotonic_timestamps"], bool
    ):
        raise ValueError(
            "Invalid config: quality_gate_require_monotonic_timestamps must be boolean"
        )

    warmup_policy = str(config.get("warmup_policy", "strict_fail")).strip().lower()
    if warmup_policy not in TFT_WARMUP_POLICIES:
        raise ValueError(
            f"Invalid config: warmup_policy must be one of {sorted(TFT_WARMUP_POLICIES)}"
        )
