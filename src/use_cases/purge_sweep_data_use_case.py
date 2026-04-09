from __future__ import annotations

from dataclasses import dataclass
import logging
import shutil
from pathlib import Path
from typing import Callable

import pandas as pd

from src.use_cases.refresh_analytics_store_use_case import RefreshAnalyticsStoreUseCase
from src.use_cases.validate_analytics_quality_use_case import ValidateAnalyticsQualityUseCase


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PurgeSweepDataResult:
    sweep_prefix: str
    run_ids_found: int
    silver_files_scanned: int
    silver_files_rewritten: int
    silver_rows_removed_total: int
    silver_rows_removed_by_table: dict[str, int]
    model_dirs_removed: list[str]
    model_paths_remaining: list[str]
    refresh_outputs: dict[str, str]
    quality_passed: bool
    quality_failed_checks: list[dict[str, object]]
    validation_zero_passed: bool
    validation_zero_detail: str


class PurgeSweepDataUseCase:
    def __init__(
        self,
        *,
        analytics_silver_dir: str | Path,
        analytics_gold_dir: str | Path,
        models_sweeps_dir: str | Path,
        refresh_use_case_factory: Callable[..., RefreshAnalyticsStoreUseCase] = RefreshAnalyticsStoreUseCase,
        quality_use_case_factory: Callable[..., ValidateAnalyticsQualityUseCase] = ValidateAnalyticsQualityUseCase,
    ) -> None:
        self.analytics_silver_dir = Path(analytics_silver_dir)
        self.analytics_gold_dir = Path(analytics_gold_dir)
        self.models_sweeps_dir = Path(models_sweeps_dir)
        self.refresh_use_case_factory = refresh_use_case_factory
        self.quality_use_case_factory = quality_use_case_factory

    @staticmethod
    def _iter_parquet_files(base_dir: Path) -> list[Path]:
        if not base_dir.exists():
            return []
        return sorted(base_dir.rglob("*.parquet"))

    def _collect_run_ids(self, *, sweep_prefix: str) -> set[str]:
        dim_dir = self.analytics_silver_dir / "dim_run"
        run_ids: set[str] = set()
        for fp in self._iter_parquet_files(dim_dir):
            df = pd.read_parquet(fp)
            if "run_id" not in df.columns or "parent_sweep_id" not in df.columns:
                continue
            mask = df["parent_sweep_id"].astype(str).str.startswith(sweep_prefix)
            if mask.any():
                run_ids.update(df.loc[mask, "run_id"].astype(str).tolist())
        return run_ids

    def _has_sweep_prefix_in_silver(self, *, sweep_prefix: str) -> bool:
        for fp in self._iter_parquet_files(self.analytics_silver_dir):
            df = pd.read_parquet(fp)
            if df.empty or "parent_sweep_id" not in df.columns:
                continue
            if bool(df["parent_sweep_id"].astype(str).str.startswith(sweep_prefix).any()):
                return True
        return False

    def _list_sweep_paths(self, *, sweep_prefix: str) -> list[str]:
        if not self.models_sweeps_dir.exists():
            return []
        return [str(p) for p in sorted(self.models_sweeps_dir.glob(f"{sweep_prefix}*"))]

    def _purge_silver(
        self, *, sweep_prefix: str, run_ids: set[str]
    ) -> tuple[int, int, int, dict[str, int]]:
        files = self._iter_parquet_files(self.analytics_silver_dir)
        files_scanned = len(files)
        files_rewritten = 0
        rows_removed_total = 0
        removed_by_table: dict[str, int] = {}

        for fp in files:
            df = pd.read_parquet(fp)
            if df.empty:
                continue

            mask = pd.Series(False, index=df.index)
            if run_ids and "run_id" in df.columns:
                mask |= df["run_id"].astype(str).isin(run_ids)
            if "parent_sweep_id" in df.columns:
                mask |= df["parent_sweep_id"].astype(str).str.startswith(sweep_prefix)

            removed = int(mask.sum())
            if removed <= 0:
                continue

            out = df.loc[~mask].copy()
            out.to_parquet(fp, index=False)
            files_rewritten += 1
            rows_removed_total += removed

            rel = fp.relative_to(self.analytics_silver_dir)
            table = rel.parts[0] if rel.parts else "unknown"
            removed_by_table[table] = int(removed_by_table.get(table, 0) + removed)

        return files_scanned, files_rewritten, rows_removed_total, removed_by_table

    def _purge_model_dirs(self, *, sweep_prefix: str) -> list[str]:
        removed: list[str] = []
        if not self.models_sweeps_dir.exists():
            return removed
        for d in sorted(self.models_sweeps_dir.glob(f"{sweep_prefix}*")):
            if d.is_dir():
                shutil.rmtree(d)
                removed.append(str(d))
        return removed

    def _validate_zero_residue(self, *, sweep_prefix: str, run_ids: set[str]) -> tuple[bool, str]:
        residues: list[str] = []
        for fp in self._iter_parquet_files(self.analytics_silver_dir):
            df = pd.read_parquet(fp)
            if df.empty:
                continue

            prefix_hits = 0
            run_hits = 0
            if "parent_sweep_id" in df.columns:
                prefix_hits = int(df["parent_sweep_id"].astype(str).str.startswith(sweep_prefix).sum())
            if run_ids and "run_id" in df.columns:
                run_hits = int(df["run_id"].astype(str).isin(run_ids).sum())
            if prefix_hits > 0 or run_hits > 0:
                rel = str(fp.relative_to(self.analytics_silver_dir))
                residues.append(f"{rel}:prefix_hits={prefix_hits},run_id_hits={run_hits}")

        if residues:
            return False, "; ".join(residues[:30])
        return True, "ok"

    def _validate_models_zero(self, *, sweep_prefix: str) -> tuple[bool, list[str], str]:
        if not self.models_sweeps_dir.exists():
            return True, [], "ok"

        remaining_paths = [str(p) for p in sorted(self.models_sweeps_dir.glob(f"{sweep_prefix}*"))]
        if not remaining_paths:
            return True, [], "ok"

        preview = ", ".join(remaining_paths[:30])
        return False, remaining_paths, f"model_paths_remaining={len(remaining_paths)} ({preview})"

    def execute(
        self,
        *,
        sweep_prefix: str,
        min_samples_train: int = 1,
        min_samples_val: int = 1,
        min_samples_test: int = 1,
    ) -> PurgeSweepDataResult:
        prefix = str(sweep_prefix).strip()
        if not prefix:
            raise ValueError("sweep_prefix must not be empty")

        logger.info(
            "Purge sweep started",
            extra={
                "sweep_prefix": prefix,
                "analytics_silver_dir": str(self.analytics_silver_dir),
                "analytics_gold_dir": str(self.analytics_gold_dir),
                "models_sweeps_dir": str(self.models_sweeps_dir),
            },
        )

        run_ids = self._collect_run_ids(sweep_prefix=prefix)
        has_prefix_in_silver = self._has_sweep_prefix_in_silver(sweep_prefix=prefix)
        matched_paths = self._list_sweep_paths(sweep_prefix=prefix)
        logger.info(
            "Purge sweep discovery",
            extra={
                "sweep_prefix": prefix,
                "run_ids_found": len(run_ids),
                "has_prefix_in_silver": has_prefix_in_silver,
                "matched_model_paths": len(matched_paths),
            },
        )
        if not has_prefix_in_silver and not matched_paths:
            raise ValueError(
                f"No sweep data found for prefix '{prefix}' in analytics silver or model sweeps directory"
            )

        files_scanned, files_rewritten, rows_removed_total, removed_by_table = self._purge_silver(
            sweep_prefix=prefix,
            run_ids=run_ids,
        )
        logger.info(
            "Purge sweep silver completed",
            extra={
                "sweep_prefix": prefix,
                "files_scanned": files_scanned,
                "files_rewritten": files_rewritten,
                "rows_removed_total": rows_removed_total,
                "rows_removed_by_table": removed_by_table,
            },
        )

        removed_dirs = self._purge_model_dirs(sweep_prefix=prefix)
        logger.info(
            "Purge sweep model directories completed",
            extra={
                "sweep_prefix": prefix,
                "model_dirs_removed": len(removed_dirs),
            },
        )

        logger.info("Purge sweep refresh started", extra={"sweep_prefix": prefix})
        refresh_result = self.refresh_use_case_factory(
            analytics_silver_dir=self.analytics_silver_dir,
            analytics_gold_dir=self.analytics_gold_dir,
        ).execute()
        logger.info(
            "Purge sweep refresh completed",
            extra={
                "sweep_prefix": prefix,
                "refresh_outputs": list(refresh_result.outputs.keys()),
            },
        )

        logger.info("Purge sweep quality validation started", extra={"sweep_prefix": prefix})
        quality_result = self.quality_use_case_factory(
            analytics_silver_dir=self.analytics_silver_dir,
            analytics_gold_dir=self.analytics_gold_dir,
            min_samples_train=min_samples_train,
            min_samples_val=min_samples_val,
            min_samples_test=min_samples_test,
        ).execute()

        failed_checks = [c for c in quality_result.checks if not bool(c.get("passed"))]
        logger.info(
            "Purge sweep quality validation completed",
            extra={
                "sweep_prefix": prefix,
                "quality_passed": bool(quality_result.passed),
                "failed_checks_count": len(failed_checks),
            },
        )

        zero_ok_silver, zero_detail_silver = self._validate_zero_residue(sweep_prefix=prefix, run_ids=run_ids)
        zero_ok_models, model_paths_remaining, zero_detail_models = self._validate_models_zero(sweep_prefix=prefix)

        zero_ok = bool(zero_ok_silver and zero_ok_models)
        if zero_ok:
            zero_detail = "ok"
        else:
            details = []
            if not zero_ok_silver:
                details.append(f"silver_residue=({zero_detail_silver})")
            if not zero_ok_models:
                details.append(f"model_residue=({zero_detail_models})")
            zero_detail = "; ".join(details)

        logger.info(
            "Purge sweep final validation",
            extra={
                "sweep_prefix": prefix,
                "validation_zero_passed": zero_ok,
                "validation_zero_detail": zero_detail,
                "quality_passed": bool(quality_result.passed),
            },
        )

        return PurgeSweepDataResult(
            sweep_prefix=prefix,
            run_ids_found=len(run_ids),
            silver_files_scanned=files_scanned,
            silver_files_rewritten=files_rewritten,
            silver_rows_removed_total=rows_removed_total,
            silver_rows_removed_by_table=removed_by_table,
            model_dirs_removed=removed_dirs,
            model_paths_remaining=model_paths_remaining,
            refresh_outputs=dict(refresh_result.outputs),
            quality_passed=bool(quality_result.passed),
            quality_failed_checks=failed_checks,
            validation_zero_passed=zero_ok,
            validation_zero_detail=str(zero_detail),
        )
