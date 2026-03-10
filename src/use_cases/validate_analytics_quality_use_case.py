from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AnalyticsQualityResult:
    passed: bool
    checks: list[dict[str, object]]


class ValidateAnalyticsQualityUseCase:
    def __init__(
        self,
        *,
        analytics_silver_dir: str | Path,
        min_samples_train: int = 1,
        min_samples_val: int = 1,
        min_samples_test: int = 1,
    ) -> None:
        self.analytics_silver_dir = Path(analytics_silver_dir)
        self.min_samples_train = int(min_samples_train)
        self.min_samples_val = int(min_samples_val)
        self.min_samples_test = int(min_samples_test)

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
    def _record(checks: list[dict[str, object]], name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    def execute(self) -> AnalyticsQualityResult:
        checks: list[dict[str, object]] = []

        dim_run = self._load_partitioned_table(self.analytics_silver_dir, "dim_run")
        fact_run_snapshot = self._load_partitioned_table(self.analytics_silver_dir, "fact_run_snapshot")
        fact_config = self._load_partitioned_table(self.analytics_silver_dir, "fact_config")
        fact_split_metrics = self._load_partitioned_table(self.analytics_silver_dir, "fact_split_metrics")
        fact_epoch_metrics = self._load_partitioned_table(self.analytics_silver_dir, "fact_epoch_metrics")
        fact_oos_predictions = self._load_partitioned_table(self.analytics_silver_dir, "fact_oos_predictions")
        fact_model_artifacts = self._load_partitioned_table(self.analytics_silver_dir, "fact_model_artifacts")
        fact_failures = self._load_partitioned_table(self.analytics_silver_dir, "fact_failures")
        bridge_run_features = self._load_partitioned_table(self.analytics_silver_dir, "bridge_run_features")
        fact_split_timestamps_ref = self._load_partitioned_table(
            self.analytics_silver_dir, "fact_split_timestamps_ref"
        )

        required_tables = {
            "dim_run": dim_run,
            "fact_run_snapshot": fact_run_snapshot,
            "fact_config": fact_config,
            "fact_split_metrics": fact_split_metrics,
            "fact_epoch_metrics": fact_epoch_metrics,
            "fact_oos_predictions": fact_oos_predictions,
            "fact_model_artifacts": fact_model_artifacts,
            "bridge_run_features": bridge_run_features,
        }
        missing_required_tables = [name for name, df in required_tables.items() if df.empty]
        self._record(
            checks,
            "required_tables_presence",
            len(missing_required_tables) == 0,
            "ok" if not missing_required_tables else ", ".join(missing_required_tables),
        )

        # P0: run_id/execution_id consistency.
        if dim_run.empty:
            self._record(checks, "run_id_execution_consistency", False, "dim_run is empty")
        else:
            run_id_null = int(dim_run["run_id"].isna().sum()) if "run_id" in dim_run else len(dim_run)
            dup_run_id = int(dim_run["run_id"].duplicated().sum()) if "run_id" in dim_run else len(dim_run)
            non_null_exec = (
                dim_run["execution_id"].dropna().astype(str).str.strip()
                if "execution_id" in dim_run.columns
                else pd.Series(dtype=str)
            )
            dup_exec_id = int(non_null_exec.duplicated().sum()) if not non_null_exec.empty else 0
            ok = run_id_null == 0 and dup_run_id == 0 and dup_exec_id == 0
            self._record(
                checks,
                "run_id_execution_consistency",
                ok,
                f"run_id_null={run_id_null}, duplicate_run_id={dup_run_id}, duplicate_execution_id={dup_exec_id}",
            )

        # P0: referential integrity facts -> dim_run
        fact_tables = {
            "fact_run_snapshot": fact_run_snapshot,
            "fact_config": fact_config,
            "fact_split_metrics": fact_split_metrics,
            "fact_epoch_metrics": fact_epoch_metrics,
            "fact_oos_predictions": fact_oos_predictions,
            "fact_model_artifacts": fact_model_artifacts,
            "fact_failures": fact_failures,
            "bridge_run_features": bridge_run_features,
            "fact_split_timestamps_ref": fact_split_timestamps_ref,
        }
        dim_ids = set(dim_run["run_id"].dropna().astype(str).tolist()) if "run_id" in dim_run.columns else set()
        missing_refs: list[str] = []
        for table_name, df in fact_tables.items():
            if df.empty or "run_id" not in df.columns:
                continue
            ids = set(df["run_id"].dropna().astype(str).tolist())
            missing = ids - dim_ids
            if missing:
                missing_refs.append(f"{table_name}:{len(missing)}")
        self._record(
            checks,
            "referential_integrity",
            len(missing_refs) == 0,
            "ok" if not missing_refs else ", ".join(missing_refs),
        )

        # P0: no NaN in required metrics
        nan_issues: list[str] = []
        for df, cols, label in [
            (fact_split_metrics, ["rmse", "mae", "directional_accuracy", "n_samples"], "fact_split_metrics"),
            (fact_epoch_metrics, ["train_loss", "val_loss"], "fact_epoch_metrics"),
        ]:
            if df.empty:
                continue
            for col in cols:
                if col not in df.columns:
                    nan_issues.append(f"{label}.{col}:missing")
                    continue
                values = pd.to_numeric(df[col], errors="coerce")
                n_bad = int(values.isna().sum())
                if n_bad > 0:
                    nan_issues.append(f"{label}.{col}:nan={n_bad}")
        self._record(checks, "required_metrics_nan", len(nan_issues) == 0, "ok" if not nan_issues else ", ".join(nan_issues))

        # P0: temporal consistency
        temporal_issues: list[str] = []
        if not fact_oos_predictions.empty:
            if "timestamp_utc" not in fact_oos_predictions.columns or "target_timestamp_utc" not in fact_oos_predictions.columns:
                temporal_issues.append("fact_oos_predictions missing timestamp columns")
            else:
                ts = pd.to_datetime(fact_oos_predictions["timestamp_utc"], utc=True, errors="coerce")
                tgt = pd.to_datetime(fact_oos_predictions["target_timestamp_utc"], utc=True, errors="coerce")
                bad_parse = int(ts.isna().sum() + tgt.isna().sum())
                if bad_parse > 0:
                    temporal_issues.append(f"timestamp_parse_errors={bad_parse}")
                bad_order = int((tgt < ts).sum())
                if bad_order > 0:
                    temporal_issues.append(f"target_before_timestamp={bad_order}")

                keys = [c for c in ["run_id", "split", "horizon"] if c in fact_oos_predictions.columns]
                if keys:
                    tmp = fact_oos_predictions.copy()
                    tmp["_ts"] = ts
                    for _, g in tmp.groupby(keys, dropna=False):
                        sorted_ts = g["_ts"].dropna().sort_values()
                        if not sorted_ts.is_monotonic_increasing:
                            temporal_issues.append("non_monotonic_timestamps_in_group")
                            break
        self._record(
            checks,
            "temporal_consistency",
            len(temporal_issues) == 0,
            "ok" if not temporal_issues else ", ".join(temporal_issues),
        )

        # P0: expected cardinality config x fold x seed
        cardinality_ok = True
        cardinality_detail = "ok"
        if not dim_run.empty:
            key_cols = [c for c in ["asset", "feature_set_name", "config_signature", "fold", "seed"] if c in dim_run.columns]
            if len(key_cols) >= 3:
                dup = int(dim_run.duplicated(subset=key_cols).sum())
                cardinality_ok = dup == 0
                cardinality_detail = f"duplicate_groups={dup}"
        self._record(checks, "cardinality_config_fold_seed", cardinality_ok, cardinality_detail)

        # P0: minimum split samples
        split_min_ok = True
        split_min_detail = "ok"
        if not fact_run_snapshot.empty:
            checks_df = fact_run_snapshot.copy()
            missing_cols = [
                c
                for c in ["n_samples_train", "n_samples_val", "n_samples_test"]
                if c not in checks_df.columns
            ]
            if missing_cols:
                split_min_ok = False
                split_min_detail = f"missing_columns={missing_cols}"
            else:
                bad_train = int((pd.to_numeric(checks_df["n_samples_train"], errors="coerce") < self.min_samples_train).sum())
                bad_val = int((pd.to_numeric(checks_df["n_samples_val"], errors="coerce") < self.min_samples_val).sum())
                bad_test = int((pd.to_numeric(checks_df["n_samples_test"], errors="coerce") < self.min_samples_test).sum())
                split_min_ok = (bad_train + bad_val + bad_test) == 0
                split_min_detail = f"below_min_train={bad_train}, below_min_val={bad_val}, below_min_test={bad_test}"
        self._record(checks, "min_samples_by_split", split_min_ok, split_min_detail)

        # P0: official runs quantile/attention contract
        contract_ok = True
        contract_issues: list[str] = []
        if not dim_run.empty:
            official_runs = set(
                dim_run.loc[dim_run["status"].astype(str).str.lower() == "ok", "run_id"].astype(str).tolist()
            ) if "status" in dim_run.columns else set()
            if official_runs:
                if fact_oos_predictions.empty:
                    contract_ok = False
                    contract_issues.append("missing_fact_oos_predictions")
                else:
                    oos_off = fact_oos_predictions[fact_oos_predictions["run_id"].astype(str).isin(official_runs)]
                    for q in ["quantile_p10", "quantile_p50", "quantile_p90"]:
                        if q not in oos_off.columns:
                            contract_ok = False
                            contract_issues.append(f"missing_{q}")
                        else:
                            nulls = int(pd.to_numeric(oos_off[q], errors="coerce").isna().sum())
                            if nulls > 0:
                                contract_ok = False
                                contract_issues.append(f"{q}_nan={nulls}")

                if fact_model_artifacts.empty:
                    contract_ok = False
                    contract_issues.append("missing_fact_model_artifacts")
                else:
                    mar = fact_model_artifacts[fact_model_artifacts["run_id"].astype(str).isin(official_runs)]
                    missing_mar = len(official_runs - set(mar["run_id"].astype(str).tolist()))
                    if missing_mar > 0:
                        contract_ok = False
                        contract_issues.append(f"missing_model_artifacts={missing_mar}")
                    for c in ["feature_importance_json", "attention_summary_json"]:
                        if c not in mar.columns:
                            contract_ok = False
                            contract_issues.append(f"missing_{c}")
                        else:
                            empty = int(mar[c].fillna("").astype(str).str.strip().eq("").sum())
                            if empty > 0:
                                contract_ok = False
                                contract_issues.append(f"empty_{c}={empty}")

        self._record(
            checks,
            "official_contract_quantile_attention",
            contract_ok,
            "ok" if not contract_issues else ", ".join(contract_issues),
        )

        passed = all(bool(item["passed"]) for item in checks)
        return AnalyticsQualityResult(passed=passed, checks=checks)
