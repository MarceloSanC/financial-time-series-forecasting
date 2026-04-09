from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class QuantileBlockAThresholds:
    max_crossing_bruto_rate: float = 0.001
    max_negative_interval_width_count: int = 0
    max_crossing_post_guardrail_rate: float = 0.0
    require_post_guardrail: bool = False


@dataclass(frozen=True)
class QuantileContractMetrics:
    total_rows: int
    order_rows: int
    crossing_bruto_count: int
    crossing_bruto_rate: float
    negative_interval_width_count: int
    negative_interval_width_rate: float
    post_guardrail_rows: int
    crossing_post_guardrail_count: int | None
    crossing_post_guardrail_rate: float | None


@dataclass(frozen=True)
class QuantileBlockAEvaluation:
    passed: bool
    detail: str
    metrics: QuantileContractMetrics


class QuantileContractAnalyzer:
    """Compute reusable quantile contract metrics and Block A acceptance checks."""

    POST_GUARDRAIL_COLS = (
        "quantile_p10_post_guardrail",
        "quantile_p50_post_guardrail",
        "quantile_p90_post_guardrail",
    )

    @staticmethod
    def _normalize_list(values: list[str] | list[int] | None) -> list[str] | None:
        if not values:
            return None
        out = [str(v).strip() for v in values if str(v).strip()]
        return out or None

    @staticmethod
    def filter_scope(
        *,
        fact_oos_predictions: pd.DataFrame,
        dim_run: pd.DataFrame,
        parent_sweep_prefixes: list[str] | None = None,
        splits: list[str] | None = None,
        horizons: list[int] | None = None,
    ) -> pd.DataFrame:
        df = fact_oos_predictions.copy()
        if df.empty:
            return df

        split_filter = QuantileContractAnalyzer._normalize_list(splits)
        if split_filter is not None and "split" in df.columns:
            df = df[df["split"].astype(str).isin(split_filter)].copy()

        if horizons and "horizon" in df.columns:
            hset = {int(h) for h in horizons}
            hcol = pd.to_numeric(df["horizon"], errors="coerce")
            df = df[hcol.isin(hset)].copy()

        prefixes = QuantileContractAnalyzer._normalize_list(parent_sweep_prefixes)
        if prefixes is not None and "run_id" in df.columns and not dim_run.empty and "run_id" in dim_run.columns:
            meta = dim_run[[c for c in ["run_id", "parent_sweep_id"] if c in dim_run.columns]].drop_duplicates("run_id")
            scoped = df.merge(meta, on="run_id", how="left")
            ps = scoped.get("parent_sweep_id", pd.Series(index=scoped.index, dtype=object)).astype(str)
            mask = ps.apply(lambda v: any(v.startswith(p) for p in prefixes))
            df = scoped[mask].drop(columns=[c for c in ["parent_sweep_id"] if c in scoped.columns]).copy()

        return df

    @staticmethod
    def analyze(
        fact_oos_predictions: pd.DataFrame,
        *,
        post_guardrail_cols: tuple[str, str, str] | None = None,
    ) -> QuantileContractMetrics:
        if fact_oos_predictions.empty:
            return QuantileContractMetrics(
                total_rows=0,
                order_rows=0,
                crossing_bruto_count=0,
                crossing_bruto_rate=0.0,
                negative_interval_width_count=0,
                negative_interval_width_rate=0.0,
                post_guardrail_rows=0,
                crossing_post_guardrail_count=None,
                crossing_post_guardrail_rate=None,
            )

        df = fact_oos_predictions.copy()
        total_rows = int(len(df))

        q10 = pd.to_numeric(df.get("quantile_p10"), errors="coerce")
        q50 = pd.to_numeric(df.get("quantile_p50"), errors="coerce")
        q90 = pd.to_numeric(df.get("quantile_p90"), errors="coerce")

        order_mask = (~q10.isna()) & (~q50.isna()) & (~q90.isna())
        order_rows = int(order_mask.sum())
        bad_order = int((order_mask & ((q10 > q50) | (q50 > q90))).sum())
        crossing_bruto_rate = float(bad_order / order_rows) if order_rows > 0 else 0.0

        width_mask = (~q10.isna()) & (~q90.isna())
        bad_width = int((width_mask & ((q90 - q10) < 0.0)).sum())
        negative_width_rate = float(bad_width / int(width_mask.sum())) if int(width_mask.sum()) > 0 else 0.0

        pcols = post_guardrail_cols or QuantileContractAnalyzer.POST_GUARDRAIL_COLS
        pg_count: int | None = None
        pg_rate: float | None = None
        pg_rows = 0
        if set(pcols).issubset(set(df.columns)):
            p10 = pd.to_numeric(df[pcols[0]], errors="coerce")
            p50 = pd.to_numeric(df[pcols[1]], errors="coerce")
            p90 = pd.to_numeric(df[pcols[2]], errors="coerce")
            pg_mask = (~p10.isna()) & (~p50.isna()) & (~p90.isna())
            pg_rows = int(pg_mask.sum())
            pg_count = int((pg_mask & ((p10 > p50) | (p50 > p90))).sum())
            pg_rate = float(pg_count / pg_rows) if pg_rows > 0 else 0.0

        return QuantileContractMetrics(
            total_rows=total_rows,
            order_rows=order_rows,
            crossing_bruto_count=bad_order,
            crossing_bruto_rate=crossing_bruto_rate,
            negative_interval_width_count=bad_width,
            negative_interval_width_rate=negative_width_rate,
            post_guardrail_rows=pg_rows,
            crossing_post_guardrail_count=pg_count,
            crossing_post_guardrail_rate=pg_rate,
        )

    @staticmethod
    def evaluate_block_a(
        metrics: QuantileContractMetrics,
        *,
        thresholds: QuantileBlockAThresholds,
    ) -> QuantileBlockAEvaluation:
        issues: list[str] = []

        if metrics.crossing_bruto_rate > float(thresholds.max_crossing_bruto_rate):
            issues.append(
                f"crossing_bruto_rate={metrics.crossing_bruto_rate:.8f}>max={float(thresholds.max_crossing_bruto_rate):.8f}"
            )

        if metrics.negative_interval_width_count > int(thresholds.max_negative_interval_width_count):
            issues.append(
                f"negative_interval_width_count={metrics.negative_interval_width_count}>max={int(thresholds.max_negative_interval_width_count)}"
            )

        if metrics.crossing_post_guardrail_rate is None:
            if thresholds.require_post_guardrail:
                issues.append("missing_post_guardrail_quantiles")
        else:
            if metrics.crossing_post_guardrail_rate > float(thresholds.max_crossing_post_guardrail_rate):
                issues.append(
                    f"crossing_post_guardrail_rate={metrics.crossing_post_guardrail_rate:.8f}>max={float(thresholds.max_crossing_post_guardrail_rate):.8f}"
                )

        detail_parts = [
            f"total_rows={metrics.total_rows}",
            f"order_rows={metrics.order_rows}",
            f"crossing_bruto_count={metrics.crossing_bruto_count}",
            f"crossing_bruto_rate={metrics.crossing_bruto_rate:.8f}",
            f"negative_interval_width_count={metrics.negative_interval_width_count}",
            f"post_guardrail_rows={metrics.post_guardrail_rows}",
            (
                "crossing_post_guardrail_rate=NA"
                if metrics.crossing_post_guardrail_rate is None
                else f"crossing_post_guardrail_rate={metrics.crossing_post_guardrail_rate:.8f}"
            ),
        ]
        if issues:
            detail_parts.append("issues=" + "|".join(issues))

        return QuantileBlockAEvaluation(
            passed=len(issues) == 0,
            detail=", ".join(detail_parts),
            metrics=metrics,
        )
