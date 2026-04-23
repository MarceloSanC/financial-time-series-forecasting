from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DatasetQualityGateConfig:
    max_nan_ratio_per_feature: float = 1.0
    min_temporal_coverage_days: int = 1
    require_unique_timestamps: bool = True
    require_monotonic_timestamps: bool = True


class DatasetQualityGate:
    @staticmethod
    def evaluate(
        *,
        df: pd.DataFrame,
        feature_cols: list[str],
        config: DatasetQualityGateConfig,
        warmup_counts: dict[str, int] | None = None,
    ) -> dict:
        report: dict = {
            "config": {
                "max_nan_ratio_per_feature": float(config.max_nan_ratio_per_feature),
                "min_temporal_coverage_days": int(config.min_temporal_coverage_days),
                "require_unique_timestamps": bool(config.require_unique_timestamps),
                "require_monotonic_timestamps": bool(config.require_monotonic_timestamps),
            },
            "checks": {},
            "passed": True,
        }

        if "timestamp" not in df.columns:
            report["checks"]["timestamp_presence"] = {"passed": False}
            report["passed"] = False
            return report

        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        timestamp_parse_ok = bool(ts.notna().all())
        report["checks"]["timestamp_parse"] = {
            "passed": timestamp_parse_ok,
            "invalid_rows": int(ts.isna().sum()),
        }
        if not timestamp_parse_ok:
            report["passed"] = False
            return report

        if config.require_unique_timestamps:
            dup_count = int(ts.duplicated().sum())
            unique_ok = dup_count == 0
            report["checks"]["timestamp_unique"] = {
                "enabled": True,
                "passed": unique_ok,
                "duplicate_count": dup_count,
            }
            report["passed"] = report["passed"] and unique_ok
        else:
            report["checks"]["timestamp_unique"] = {"enabled": False, "passed": True}

        if config.require_monotonic_timestamps:
            mono_ok = bool(ts.is_monotonic_increasing)
            report["checks"]["timestamp_monotonic"] = {
                "enabled": True,
                "passed": mono_ok,
            }
            report["passed"] = report["passed"] and mono_ok
        else:
            report["checks"]["timestamp_monotonic"] = {"enabled": False, "passed": True}

        coverage_days = int((ts.max() - ts.min()).days) + 1
        coverage_ok = coverage_days >= int(config.min_temporal_coverage_days)
        report["checks"]["temporal_coverage"] = {
            "passed": coverage_ok,
            "coverage_days": coverage_days,
            "min_required": int(config.min_temporal_coverage_days),
        }
        report["passed"] = report["passed"] and coverage_ok

        effective_features = [c for c in feature_cols if c in df.columns]
        warmup_counts = warmup_counts or {}
        failing_features: dict[str, float] = {}
        features_not_evaluated: list[str] = []
        applied_warmup_rows: dict[str, int] = {}
        if effective_features:
            max_allowed = float(config.max_nan_ratio_per_feature)
            for col in effective_features:
                warmup = max(0, int(warmup_counts.get(col, 0)))
                series = df[col]
                effective_series = series.iloc[warmup:] if warmup > 0 else series
                applied_warmup_rows[col] = warmup
                if effective_series.empty:
                    features_not_evaluated.append(col)
                    continue
                ratio = float(effective_series.isna().mean())
                if ratio > max_allowed:
                    failing_features[str(col)] = ratio
            failing_features = dict(
                sorted(
                    failing_features.items(),
                    key=lambda kv: kv[1],
                    reverse=True,
                )
            )
        nan_ok = len(failing_features) == 0
        report["checks"]["nan_ratio"] = {
            "passed": nan_ok,
            "max_allowed": float(config.max_nan_ratio_per_feature),
            "feature_count_evaluated": len(effective_features),
            "failing_features": failing_features,
            "features_not_evaluated": features_not_evaluated,
            "applied_warmup_rows": applied_warmup_rows,
        }
        report["passed"] = report["passed"] and nan_ok
        return report

    @staticmethod
    def validate(
        *,
        df: pd.DataFrame,
        feature_cols: list[str],
        config: DatasetQualityGateConfig,
        context: str,
        warmup_counts: dict[str, int] | None = None,
    ) -> None:
        report = DatasetQualityGate.evaluate(
            df=df,
            feature_cols=feature_cols,
            config=config,
            warmup_counts=warmup_counts,
        )
        if report.get("passed", False):
            return

        checks = report.get("checks", {})
        if checks.get("timestamp_presence", {}).get("passed") is False:
            raise ValueError(f"{context} quality gate failed: missing required column `timestamp`.")
        if checks.get("timestamp_parse", {}).get("passed") is False:
            invalid_rows = checks.get("timestamp_parse", {}).get("invalid_rows", 0)
            raise ValueError(
                f"{context} quality gate failed: invalid timestamp parsing (invalid_rows={invalid_rows})."
            )
        if checks.get("timestamp_unique", {}).get("enabled") and not checks.get(
            "timestamp_unique", {}
        ).get("passed", True):
            dup_count = checks.get("timestamp_unique", {}).get("duplicate_count", 0)
            raise ValueError(
                f"{context} quality gate failed: duplicate timestamp rows detected (count={dup_count})."
            )
        if checks.get("timestamp_monotonic", {}).get("enabled") and not checks.get(
            "timestamp_monotonic", {}
        ).get("passed", True):
            raise ValueError(f"{context} quality gate failed: timestamps are not monotonic increasing.")
        if not checks.get("temporal_coverage", {}).get("passed", True):
            coverage_days = checks.get("temporal_coverage", {}).get("coverage_days", 0)
            min_required = checks.get("temporal_coverage", {}).get("min_required", 0)
            raise ValueError(
                f"{context} quality gate failed: temporal coverage below minimum "
                f"(coverage_days={coverage_days}, min_required={min_required})."
            )
        if not checks.get("nan_ratio", {}).get("passed", True):
            max_allowed = checks.get("nan_ratio", {}).get("max_allowed", 1.0)
            failing_features = checks.get("nan_ratio", {}).get("failing_features", {})
            details = ", ".join(
                f"{col}={float(ratio):.3f}" for col, ratio in failing_features.items()
            )
            raise ValueError(
                f"{context} quality gate failed: feature NaN ratio above threshold "
                f"(max={float(max_allowed):.3f}). failing={details}"
            )
