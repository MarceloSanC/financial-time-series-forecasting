from __future__ import annotations

import pandas as pd

from src.use_cases.refresh_analytics_store_use_case import RefreshAnalyticsStoreUseCase


def _write_table(base, table_name: str, rows: list[dict], parts: dict[str, str] | None = None) -> None:
    table_dir = base / table_name
    if parts:
        for k, v in parts.items():
            table_dir = table_dir / f"{k}={v}"
    table_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(table_dir / f"{table_name}.parquet", index=False)


def test_refresh_analytics_store_builds_gold_tables(tmp_path) -> None:
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"

    _write_table(
        silver,
        "dim_run",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "feature_set_name": "B",
                "feature_set_hash": "fh1",
                "config_signature": "cfg1",
                "model_version": "v1",
                "parent_sweep_id": "sw1",
                "trial_number": 1,
                "fold": "wf_1",
                "seed": 7,
                "status": "ok",
                "created_at_utc": "2026-01-01T00:00:00+00:00",
                "feature_list_ordered_json": "[]",
                "split_fingerprint": "sp1",
                "pipeline_version": "0.1",
                "checkpoint_path_final": "/tmp/final.pt",
                "checkpoint_path_best": "/tmp/best.ckpt",
                "git_commit": "abc",
                "library_versions_json": "{}",
                "hardware_info_json": "{}",
                "duration_total_seconds": 1.0,
                "eta_recorded_seconds": 0.0,
                "retries": 0,
            },
            {
                "schema_version": 1,
                "run_id": "r2",
                "asset": "AAPL",
                "feature_set_name": "B",
                "feature_set_hash": "fh1",
                "config_signature": "cfg1",
                "model_version": "v2",
                "parent_sweep_id": "sw1",
                "trial_number": 2,
                "fold": "wf_1",
                "seed": 42,
                "status": "ok",
                "created_at_utc": "2026-01-02T00:00:00+00:00",
                "feature_list_ordered_json": "[]",
                "split_fingerprint": "sp2",
                "pipeline_version": "0.1",
                "checkpoint_path_final": "/tmp/final.pt",
                "checkpoint_path_best": "/tmp/best.ckpt",
                "git_commit": "abc",
                "library_versions_json": "{}",
                "hardware_info_json": "{}",
                "duration_total_seconds": 1.0,
                "eta_recorded_seconds": 0.0,
                "retries": 0,
            },
        ],
        {"asset": "AAPL", "sweep_id": "sw1"},
    )

    _write_table(
        silver,
        "fact_split_metrics",
        [
            {
                "schema_version": 1,
                "run_id": "r1",
                "asset": "AAPL",
                "parent_sweep_id": "sw1",
                "split": "test",
                "rmse": 0.10,
                "mae": 0.09,
                "mape": 0.0,
                "smape": 0.0,
                "directional_accuracy": 0.55,
                "n_samples": 100,
            },
            {
                "schema_version": 1,
                "run_id": "r2",
                "asset": "AAPL",
                "parent_sweep_id": "sw1",
                "split": "test",
                "rmse": 0.12,
                "mae": 0.10,
                "mape": 0.0,
                "smape": 0.0,
                "directional_accuracy": 0.52,
                "n_samples": 100,
            },
        ],
        {"asset": "AAPL", "sweep_id": "sw1"},
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
                "fold": "wf_1",
                "seed": 7,
                "horizon": 1,
                "timestamp_utc": "2026-01-03T00:00:00+00:00",
                "target_timestamp_utc": "2026-01-03T00:00:00+00:00",
                "y_true": 0.1,
                "y_pred": 0.12,
                "error": 0.02,
                "abs_error": 0.02,
                "sq_error": 0.0004,
                "quantile_p10": 0.05,
                "quantile_p50": 0.12,
                "quantile_p90": 0.2,
                "year": 2026,
            }
        ],
        {"asset": "AAPL", "feature_set_name": "B", "year": "2026"},
    )

    use_case = RefreshAnalyticsStoreUseCase(
        analytics_silver_dir=silver,
        analytics_gold_dir=gold,
    )
    result = use_case.execute()

    assert "gold_runs_long" in result.outputs
    assert "gold_oos_consolidated" in result.outputs
    assert "gold_ranking_by_config" in result.outputs
    assert "gold_consistency_topk" in result.outputs
    assert "gold_ic95_by_config_metric" in result.outputs
    assert "gold_feature_set_impact" in result.outputs

    ranking = pd.read_parquet(gold / "gold_ranking_by_config.parquet")
    assert len(ranking) == 1
    assert ranking.iloc[0]["config_signature"] == "cfg1"

    oos = pd.read_parquet(gold / "gold_oos_consolidated.parquet")
    assert len(oos) == 1
    assert oos.iloc[0]["run_id"] == "r1"

    impact = pd.read_parquet(gold / "gold_feature_set_impact.parquet")
    assert not impact.empty
    assert "metric" in impact.columns
