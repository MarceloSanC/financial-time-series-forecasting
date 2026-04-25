from __future__ import annotations

import pandas as pd

from src.domain.services.quantile_contract_analyzer import (
    QuantileBlockAThresholds,
    QuantileContractAnalyzer,
)


def test_analyze_and_evaluate_block_a_with_valid_quantiles() -> None:
    df = pd.DataFrame(
        [
            {"quantile_p10": -0.01, "quantile_p50": 0.00, "quantile_p90": 0.01},
            {"quantile_p10": -0.02, "quantile_p50": -0.01, "quantile_p90": 0.00},
        ]
    )
    metrics = QuantileContractAnalyzer.analyze(df)
    assert metrics.crossing_bruto_count == 0
    assert metrics.negative_interval_width_count == 0

    out = QuantileContractAnalyzer.evaluate_block_a(
        metrics,
        thresholds=QuantileBlockAThresholds(
            max_crossing_bruto_rate=0.001,
            max_negative_interval_width_count=0,
            max_crossing_post_guardrail_rate=0.0,
            require_post_guardrail=False,
        ),
    )
    assert out.passed is True


def test_evaluate_block_a_fails_on_crossing_rate_threshold() -> None:
    df = pd.DataFrame(
        [
            {"quantile_p10": 0.03, "quantile_p50": 0.02, "quantile_p90": 0.01},
            {"quantile_p10": -0.02, "quantile_p50": -0.01, "quantile_p90": 0.00},
        ]
    )
    metrics = QuantileContractAnalyzer.analyze(df)
    out = QuantileContractAnalyzer.evaluate_block_a(
        metrics,
        thresholds=QuantileBlockAThresholds(max_crossing_bruto_rate=0.10),
    )
    assert out.passed is False
    assert "crossing_bruto_rate=" in out.detail


def test_filter_scope_by_parent_sweep_split_and_horizon() -> None:
    oos = pd.DataFrame(
        [
            {"run_id": "r1", "split": "test", "horizon": 1, "quantile_p10": 0.0, "quantile_p50": 0.1, "quantile_p90": 0.2},
            {"run_id": "r1", "split": "val", "horizon": 1, "quantile_p10": 0.0, "quantile_p50": 0.1, "quantile_p90": 0.2},
            {"run_id": "r2", "split": "test", "horizon": 1, "quantile_p10": 0.0, "quantile_p50": 0.1, "quantile_p90": 0.2},
        ]
    )
    dim = pd.DataFrame(
        [
            {"run_id": "r1", "parent_sweep_id": "0_2_3_explicit"},
            {"run_id": "r2", "parent_sweep_id": "0_2_1_explicit"},
        ]
    )

    scoped = QuantileContractAnalyzer.filter_scope(
        fact_oos_predictions=oos,
        dim_run=dim,
        parent_sweep_prefixes=["0_2_3_"],
        splits=["test"],
        horizons=[1],
    )
    assert len(scoped) == 1
    assert set(scoped["run_id"].astype(str)) == {"r1"}
    assert set(scoped["split"].astype(str)) == {"test"}
