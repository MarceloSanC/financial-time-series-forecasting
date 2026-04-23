from __future__ import annotations

import pandas as pd

from src.domain.services.explicit_config_sweep_analysis_service import (
    ExplicitConfigSweepAnalysisService,
)


def _sample_run_df() -> pd.DataFrame:
    rows = []
    configs = ["top1_trial", "top2_trial", "top3_trial"]
    for fold in ["wf_1", "wf_2"]:
        for seed in [1, 2, 3]:
            for i, cfg in enumerate(configs):
                rows.append(
                    {
                        "fold_name": fold,
                        "run_label": f"{cfg}|seed={seed}|fold={fold}",
                        "status": "ok",
                        "config_signature": f"cfg_{i+1}",
                        "val_rmse": 0.01 + (i * 0.001) + (seed * 0.00001),
                        "val_mae": 0.008 + (i * 0.001) + (seed * 0.00001),
                        "val_da": 0.50 - (i * 0.01),
                        "test_rmse": 0.02 + (i * 0.001) + (seed * 0.00001),
                        "test_mae": 0.015 + (i * 0.001) + (seed * 0.00001),
                        "test_da": 0.52 - (i * 0.01),
                    }
                )
    return pd.DataFrame(rows)


def _sample_predictions_df() -> pd.DataFrame:
    rows = []
    timestamps = pd.date_range("2026-01-01", periods=20, freq="D", tz="UTC")
    for fold in ["wf_1", "wf_2"]:
        for ts in timestamps:
            for cfg, bias in [("top1_trial", 0.01), ("top2_trial", 0.02), ("top3_trial", 0.03)]:
                y_true = 0.05
                y_pred = y_true - bias
                err = y_true - y_pred
                rows.append(
                    {
                        "fold_name": fold,
                        "run_label": f"{cfg}|seed=1|fold={fold}",
                        "timestamp": ts,
                        "squared_error": err * err,
                    }
                )
    return pd.DataFrame(rows)


def test_build_run_level_tables_returns_expected_outputs() -> None:
    run_df = _sample_run_df()
    out = ExplicitConfigSweepAnalysisService.build_run_level_tables(run_df)
    assert not out.ranking_oos.empty
    assert not out.robustness.empty
    assert not out.generalization_gap.empty
    assert not out.consistency.empty
    assert not out.heatmap_test_rmse.empty
    assert not out.confidence_intervals.empty
    assert "mean_test_rmse" in out.ranking_oos.columns
    assert "top1_rate" in out.consistency.columns


def test_compute_dm_and_mcs_returns_non_empty_results() -> None:
    pred_df = _sample_predictions_df()
    dm_df, mcs_df, mcs_trace_df = ExplicitConfigSweepAnalysisService.compute_dm_and_mcs(
        pred_df,
        bootstrap_samples=80,
        block_len=3,
        random_seed=7,
    )
    assert not dm_df.empty
    assert not mcs_df.empty
    assert "selected_in_mcs_alpha_0_05" in mcs_df.columns
    # Trace can be empty if no elimination step is needed.
    assert isinstance(mcs_trace_df, pd.DataFrame)
