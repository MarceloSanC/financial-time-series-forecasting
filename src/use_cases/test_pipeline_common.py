from __future__ import annotations

from typing import Any

TEST_TYPE_OFAT = "ofat"
TEST_TYPE_OPTUNA = "optuna"
TEST_TYPE_EXPLICIT_CONFIGS = "explicit_configs"
SUPPORTED_TEST_TYPES = {TEST_TYPE_OFAT, TEST_TYPE_OPTUNA, TEST_TYPE_EXPLICIT_CONFIGS}


def ensure_expected_test_type(*, file_config: dict[str, Any], expected_test_type: str) -> None:
    cfg_type = str(file_config.get("test_type") or expected_test_type).strip().lower()
    if cfg_type not in SUPPORTED_TEST_TYPES:
        raise ValueError(
            f"Unsupported test_type='{cfg_type}'. Supported: {sorted(SUPPORTED_TEST_TYPES)}"
        )
    if cfg_type != expected_test_type:
        raise ValueError(
            f"Config test_type='{cfg_type}' is incompatible with this entrypoint. "
            f"Expected test_type='{expected_test_type}'."
        )


def apply_common_test_fields(
    *,
    effective: dict[str, Any],
    file_config: dict[str, Any],
) -> dict[str, Any]:
    out = dict(effective)
    if isinstance(file_config.get("features"), str):
        out["features"] = file_config["features"].strip() or None
    if isinstance(file_config.get("feature_sets"), list):
        out["feature_sets"] = [str(v).strip() for v in file_config["feature_sets"] if str(v).strip()]
    if isinstance(file_config.get("continue_on_error"), bool):
        out["continue_on_error"] = file_config["continue_on_error"]
    if isinstance(file_config.get("merge_tests"), bool):
        out["merge_tests"] = file_config["merge_tests"]
    if isinstance(file_config.get("output_subdir"), str):
        out["output_subdir"] = file_config["output_subdir"]
    if isinstance(file_config.get("replica_seeds"), list):
        out["replica_seeds"] = [int(v) for v in file_config["replica_seeds"]]
    if isinstance(file_config.get("walk_forward"), dict):
        out["walk_forward"] = dict(file_config["walk_forward"])
    if isinstance(file_config.get("training_config"), dict):
        merged_training = dict(out.get("training_config", {}))
        merged_training.update(file_config["training_config"])
        out["training_config"] = merged_training
    if isinstance(file_config.get("split_config"), dict):
        merged_split = dict(out.get("split_config", {}))
        merged_split.update(file_config["split_config"])
        out["split_config"] = merged_split
    return out


def validate_required_type_fields(*, config: dict[str, Any], test_type: str) -> None:
    if test_type == TEST_TYPE_OFAT:
        if not isinstance(config.get("param_ranges"), dict) or not config.get("param_ranges"):
            raise ValueError("OFAT config requires non-empty 'param_ranges'.")
        return
    if test_type == TEST_TYPE_OPTUNA:
        if not isinstance(config.get("search_space"), dict) or not config.get("search_space"):
            raise ValueError("Optuna config requires non-empty 'search_space'.")
        if int(config.get("n_trials", 0)) <= 0:
            raise ValueError("Optuna config requires 'n_trials' > 0.")
        if int(config.get("top_k", 0)) <= 0:
            raise ValueError("Optuna config requires 'top_k' > 0.")
        if not str(config.get("study_name") or "").strip():
            raise ValueError("Optuna config requires non-empty 'study_name'.")
        return
    if test_type == TEST_TYPE_EXPLICIT_CONFIGS:
        explicit = config.get("explicit_configs")
        if not isinstance(explicit, list) or not explicit:
            raise ValueError("Explicit-configs test requires non-empty 'explicit_configs' list.")
        for idx, item in enumerate(explicit):
            if not isinstance(item, dict):
                raise ValueError(f"explicit_configs[{idx}] must be an object.")
            if not isinstance(item.get("training_config"), dict) or not item.get("training_config"):
                raise ValueError(
                    f"explicit_configs[{idx}] requires non-empty 'training_config'."
                )
        return
    raise ValueError(f"Unknown test_type='{test_type}'.")


def validate_train_runner_contract(train_runner: Any) -> None:
    run_fn = getattr(train_runner, "run", None)
    if run_fn is None or not callable(run_fn):
        raise ValueError(
            "Invalid train_runner: expected a callable 'run' method with signature compatible "
            "with run(asset, features, config, split_config, models_asset_dir)."
        )


def validate_split_metrics_payload(
    *,
    metadata: dict[str, Any] | None,
    required_splits: tuple[str, ...] = ("val", "test"),
    required_metrics: tuple[str, ...] = ("rmse", "mae"),
    optional_numeric_metrics: tuple[str, ...] = ("directional_accuracy",),
) -> tuple[bool, str | None]:
    if not isinstance(metadata, dict):
        return False, "metadata is not an object"
    split_metrics = metadata.get("split_metrics")
    if not isinstance(split_metrics, dict):
        return False, "metadata missing split_metrics"
    for split_name in required_splits:
        metrics = split_metrics.get(split_name)
        if not isinstance(metrics, dict):
            return False, f"metadata missing split_metrics.{split_name}"
        for metric_name in required_metrics:
            value = metrics.get(metric_name)
            try:
                float(value)
            except Exception:
                return False, f"invalid split_metrics.{split_name}.{metric_name}"
        for metric_name in optional_numeric_metrics:
            if metric_name in metrics and metrics.get(metric_name) is not None:
                try:
                    float(metrics.get(metric_name))
                except Exception:
                    return False, f"invalid split_metrics.{split_name}.{metric_name}"
    return True, None
