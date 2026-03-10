from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from src.utils.path_policy import to_project_relative


@dataclass(frozen=True)
class RefreshAnalyticsStoreResult:
    gold_dir: str
    outputs: dict[str, str]


class RefreshAnalyticsStoreUseCase:
    def __init__(self, *, analytics_silver_dir: str | Path, analytics_gold_dir: str | Path) -> None:
        self.analytics_silver_dir = Path(analytics_silver_dir)
        self.analytics_gold_dir = Path(analytics_gold_dir)
        self.analytics_gold_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load_partitioned_table(base_dir: Path, table_name: str) -> pd.DataFrame:
        table_dir = base_dir / table_name
        if not table_dir.exists():
            return pd.DataFrame()
        files = sorted(table_dir.rglob("*.parquet"))
        if not files:
            return pd.DataFrame()
        frames = [pd.read_parquet(fp) for fp in files]
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    @staticmethod
    def _safe_write(df: pd.DataFrame, path: Path) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
        return str(to_project_relative(path))

    @staticmethod
    def _base_join_runs_split_metrics(dim_run: pd.DataFrame, fact_split_metrics: pd.DataFrame) -> pd.DataFrame:
        if dim_run.empty or fact_split_metrics.empty:
            return pd.DataFrame()
        cols = [
            "run_id",
            "asset",
            "feature_set_name",
            "feature_set_hash",
            "config_signature",
            "model_version",
            "parent_sweep_id",
            "trial_number",
            "fold",
            "seed",
            "status",
            "created_at_utc",
        ]
        keep = [c for c in cols if c in dim_run.columns]
        dim_trim = dim_run[keep].copy()
        out = fact_split_metrics.merge(dim_trim, on="run_id", how="left")
        if "asset_x" in out.columns and "asset" not in out.columns:
            out["asset"] = out["asset_x"]
        if "asset_y" in out.columns and "asset" not in out.columns:
            out["asset"] = out["asset_y"]
        return out

    @staticmethod
    def _build_gold_runs_long(base: pd.DataFrame) -> pd.DataFrame:
        if base.empty:
            return pd.DataFrame()
        cols = [
            "run_id",
            "asset",
            "feature_set_name",
            "feature_set_hash",
            "config_signature",
            "model_version",
            "parent_sweep_id",
            "trial_number",
            "fold",
            "seed",
            "split",
            "rmse",
            "mae",
            "mape",
            "smape",
            "directional_accuracy",
            "n_samples",
            "status",
            "created_at_utc",
        ]
        keep = [c for c in cols if c in base.columns]
        return base[keep].copy()

    @staticmethod
    def _build_gold_ranking_by_config(base: pd.DataFrame) -> pd.DataFrame:
        if base.empty:
            return pd.DataFrame()
        df = base[base["split"] == "test"].copy()
        if df.empty:
            return pd.DataFrame()
        group_cols = ["asset", "feature_set_name", "config_signature"]
        agg = (
            df.groupby(group_cols, dropna=False)
            .agg(
                n_runs=("run_id", "count"),
                mean_test_rmse=("rmse", "mean"),
                std_test_rmse=("rmse", "std"),
                mean_test_mae=("mae", "mean"),
                std_test_mae=("mae", "std"),
                mean_test_da=("directional_accuracy", "mean"),
                std_test_da=("directional_accuracy", "std"),
            )
            .reset_index()
        )
        agg["rank_test_rmse"] = agg.groupby(["asset", "feature_set_name"])["mean_test_rmse"].rank(
            method="min", ascending=True
        )
        agg["rank_test_mae"] = agg.groupby(["asset", "feature_set_name"])["mean_test_mae"].rank(
            method="min", ascending=True
        )
        agg["rank_test_da"] = agg.groupby(["asset", "feature_set_name"])["mean_test_da"].rank(
            method="min", ascending=False
        )
        return agg.sort_values(["asset", "feature_set_name", "rank_test_rmse"]).reset_index(drop=True)

    @staticmethod
    def _build_gold_consistency_topk(base: pd.DataFrame) -> pd.DataFrame:
        if base.empty:
            return pd.DataFrame()
        df = base[base["split"] == "test"].copy()
        if df.empty or "fold" not in df.columns or "seed" not in df.columns:
            return pd.DataFrame()

        keys = ["asset", "feature_set_name", "fold", "seed"]
        ranked = df.sort_values(keys + ["rmse"]).copy()
        ranked["position"] = ranked.groupby(keys).cumcount() + 1

        all_counts = (
            ranked.groupby(["asset", "feature_set_name", "config_signature"], dropna=False)
            .size()
            .rename("total_groups")
            .reset_index()
        )
        top1 = (
            ranked[ranked["position"] <= 1]
            .groupby(["asset", "feature_set_name", "config_signature"], dropna=False)
            .size()
            .rename("top1_hits")
            .reset_index()
        )
        top3 = (
            ranked[ranked["position"] <= 3]
            .groupby(["asset", "feature_set_name", "config_signature"], dropna=False)
            .size()
            .rename("top3_hits")
            .reset_index()
        )
        top5 = (
            ranked[ranked["position"] <= 5]
            .groupby(["asset", "feature_set_name", "config_signature"], dropna=False)
            .size()
            .rename("top5_hits")
            .reset_index()
        )
        out = all_counts.merge(top1, on=["asset", "feature_set_name", "config_signature"], how="left")
        out = out.merge(top3, on=["asset", "feature_set_name", "config_signature"], how="left")
        out = out.merge(top5, on=["asset", "feature_set_name", "config_signature"], how="left")
        for c in ["top1_hits", "top3_hits", "top5_hits"]:
            out[c] = out[c].fillna(0).astype(int)
        out["top1_pct"] = out["top1_hits"] / out["total_groups"]
        out["top3_pct"] = out["top3_hits"] / out["total_groups"]
        out["top5_pct"] = out["top5_hits"] / out["total_groups"]
        return out.sort_values(["asset", "feature_set_name", "top1_pct"], ascending=[True, True, False]).reset_index(drop=True)

    @staticmethod
    def _build_gold_ic95(base: pd.DataFrame) -> pd.DataFrame:
        if base.empty:
            return pd.DataFrame()
        df = base[base["split"] == "test"].copy()
        if df.empty:
            return pd.DataFrame()
        metrics = [("rmse", "test_rmse"), ("mae", "test_mae"), ("directional_accuracy", "test_da")]
        rows: list[dict[str, object]] = []
        for metric_col, metric_name in metrics:
            grouped = (
                df.groupby(["asset", "feature_set_name", "config_signature"], dropna=False)[metric_col]
                .agg(["count", "mean", "std"])
                .reset_index()
            )
            grouped["std"] = grouped["std"].fillna(0.0)
            grouped["se"] = grouped["std"] / np.sqrt(grouped["count"].clip(lower=1))
            grouped["ci95_low"] = grouped["mean"] - (1.96 * grouped["se"])
            grouped["ci95_high"] = grouped["mean"] + (1.96 * grouped["se"])
            for _, row in grouped.iterrows():
                rows.append(
                    {
                        "asset": row["asset"],
                        "feature_set_name": row["feature_set_name"],
                        "config_signature": row["config_signature"],
                        "metric": metric_name,
                        "n": int(row["count"]),
                        "mean": float(row["mean"]),
                        "std": float(row["std"]),
                        "se": float(row["se"]),
                        "ci95_low": float(row["ci95_low"]),
                        "ci95_high": float(row["ci95_high"]),
                    }
                )
        return pd.DataFrame(rows)

    @staticmethod
    def _build_gold_feature_set_impact(base: pd.DataFrame) -> pd.DataFrame:
        if base.empty:
            return pd.DataFrame()
        df = base.copy()
        metric_cols = ["rmse", "mae", "directional_accuracy"]
        out_rows: list[dict[str, object]] = []
        group_cols = ["asset", "feature_set_name", "split"]
        for metric_col in metric_cols:
            grouped = (
                df.groupby(group_cols, dropna=False)[metric_col]
                .agg(["count", "mean", "std"])
                .reset_index()
            )
            for _, row in grouped.iterrows():
                out_rows.append(
                    {
                        "asset": row["asset"],
                        "feature_set_name": row["feature_set_name"],
                        "split": row["split"],
                        "metric": metric_col,
                        "n_runs": int(row["count"]),
                        "mean_value": float(row["mean"]),
                        "std_value": float(row["std"]) if pd.notna(row["std"]) else 0.0,
                    }
                )
        return pd.DataFrame(out_rows)

    @staticmethod
    def _build_gold_oos_consolidated(dim_run: pd.DataFrame, fact_oos_predictions: pd.DataFrame) -> pd.DataFrame:
        if fact_oos_predictions.empty:
            return pd.DataFrame()
        if dim_run.empty:
            return fact_oos_predictions.copy()
        cols = [
            "run_id",
            "model_version",
            "feature_set_hash",
            "parent_sweep_id",
            "trial_number",
            "status",
        ]
        keep = [c for c in cols if c in dim_run.columns]
        dim_trim = dim_run[keep].copy()
        return fact_oos_predictions.merge(dim_trim, on="run_id", how="left")

    def execute(self) -> RefreshAnalyticsStoreResult:
        dim_run = self._load_partitioned_table(self.analytics_silver_dir, "dim_run")
        fact_split_metrics = self._load_partitioned_table(self.analytics_silver_dir, "fact_split_metrics")
        fact_oos_predictions = self._load_partitioned_table(self.analytics_silver_dir, "fact_oos_predictions")

        base = self._base_join_runs_split_metrics(dim_run, fact_split_metrics)

        outputs: dict[str, str] = {}
        outputs["gold_runs_long"] = self._safe_write(
            self._build_gold_runs_long(base),
            self.analytics_gold_dir / "gold_runs_long.parquet",
        )
        outputs["gold_ranking_by_config"] = self._safe_write(
            self._build_gold_ranking_by_config(base),
            self.analytics_gold_dir / "gold_ranking_by_config.parquet",
        )
        outputs["gold_consistency_topk"] = self._safe_write(
            self._build_gold_consistency_topk(base),
            self.analytics_gold_dir / "gold_consistency_topk.parquet",
        )
        outputs["gold_ic95_by_config_metric"] = self._safe_write(
            self._build_gold_ic95(base),
            self.analytics_gold_dir / "gold_ic95_by_config_metric.parquet",
        )
        outputs["gold_feature_set_impact"] = self._safe_write(
            self._build_gold_feature_set_impact(base),
            self.analytics_gold_dir / "gold_feature_set_impact.parquet",
        )
        outputs["gold_oos_consolidated"] = self._safe_write(
            self._build_gold_oos_consolidated(dim_run, fact_oos_predictions),
            self.analytics_gold_dir / "gold_oos_consolidated.parquet",
        )

        return RefreshAnalyticsStoreResult(
            gold_dir=str(to_project_relative(self.analytics_gold_dir)),
            outputs=outputs,
        )
