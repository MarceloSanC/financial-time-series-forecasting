from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.adapters.parquet_analytics_run_repository import ParquetAnalyticsRunRepository
from src.infrastructure.schemas.analytics_store_schema import ANALYTICS_SCHEMA_VERSION
from src.utils.logging_config import setup_logging
from src.utils.path_policy import to_project_relative
from src.utils.path_resolver import load_data_paths

logger = logging.getLogger(__name__)


def _load_partitioned_table(base_dir: Path, table_name: str) -> pd.DataFrame:
    table_dir = base_dir / table_name
    if not table_dir.exists():
        return pd.DataFrame()
    files = sorted(table_dir.rglob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(fp) for fp in files], ignore_index=True)


def _safe_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _try_load_feature_importance(version_dir: Path) -> list[dict[str, Any]]:
    json_fp = version_dir / "analysis" / "feature_importance.json"
    if json_fp.exists():
        try:
            data = json.loads(json_fp.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [dict(item) for item in data if isinstance(item, dict)]
        except Exception:
            pass

    csv_fp = version_dir / "analysis" / "feature_importance.csv"
    if csv_fp.exists():
        try:
            df = pd.read_csv(csv_fp)
            return df.to_dict(orient="records")
        except Exception:
            pass

    return []


def _resolve_version_dir(row: dict[str, Any]) -> Path | None:
    final_path = row.get("checkpoint_path_final")
    if isinstance(final_path, str) and final_path.strip():
        fp = Path(final_path)
        if fp.name == "model_state.pt":
            return fp.parent
        return fp

    best_path = row.get("checkpoint_path_best")
    if isinstance(best_path, str) and best_path.strip():
        bp = Path(best_path)
        # .../<version>/checkpoints/best.ckpt -> <version>
        if bp.name == "best.ckpt" and bp.parent.name == "checkpoints":
            return bp.parent.parent
        return bp.parent

    return None


def _build_row(dim_row: dict[str, Any]) -> dict[str, Any] | None:
    run_id = str(dim_row.get("run_id") or "").strip()
    asset = str(dim_row.get("asset") or "").strip()
    model_version = str(dim_row.get("model_version") or "").strip()
    if not run_id or not asset or not model_version:
        return None

    version_dir = _resolve_version_dir(dim_row)
    if version_dir is None:
        return None

    checkpoint_final = version_dir / "model_state.pt"
    config_path = version_dir / "config.json"
    checkpoint_best = version_dir / "checkpoints" / "best.ckpt"
    scaler_path = version_dir / "scalers.pkl"
    encoder_path = version_dir / "dataset_parameters.pkl"
    history_path = version_dir / "history.csv"
    metrics_path = version_dir / "metrics.json"
    split_metrics_path = version_dir / "split_metrics.json"
    metadata_path = version_dir / "metadata.json"
    loss_curve_path = version_dir / "plots" / "loss_curve.png"

    # Contract-required fields must exist.
    if not checkpoint_final.exists() or not config_path.exists():
        return None

    fi_payload = _try_load_feature_importance(version_dir)
    attention_summary = {
        "available": False,
        "source": "backfill_model_artifacts",
        "reason": "attention tensors are not exported by trainer yet",
    }
    logs_refs = {
        "history_csv": to_project_relative(history_path) if history_path.exists() else None,
        "metrics_json": to_project_relative(metrics_path) if metrics_path.exists() else None,
        "split_metrics_json": to_project_relative(split_metrics_path) if split_metrics_path.exists() else None,
        "metadata_json": to_project_relative(metadata_path) if metadata_path.exists() else None,
        "loss_curve_png": to_project_relative(loss_curve_path) if loss_curve_path.exists() else None,
    }

    return {
        "schema_version": ANALYTICS_SCHEMA_VERSION,
        "run_id": run_id,
        "asset": asset,
        "model_version": model_version,
        "checkpoint_path_final": to_project_relative(checkpoint_final),
        "checkpoint_path_best": to_project_relative(checkpoint_best) if checkpoint_best.exists() else None,
        "config_path": to_project_relative(config_path),
        "scaler_path": to_project_relative(scaler_path) if scaler_path.exists() else None,
        "encoder_path": to_project_relative(encoder_path) if encoder_path.exists() else None,
        "feature_importance_json": _safe_json_dumps(fi_payload),
        "attention_summary_json": _safe_json_dumps(attention_summary),
        "logs_ref_json": _safe_json_dumps(logs_refs),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill missing fact_model_artifacts rows from saved model directories.")
    parser.add_argument("--asset", default=None, help="Filter by asset (e.g. AAPL).")
    parser.add_argument("--run-id", action="append", default=[], help="Specific run_id(s) to backfill. Can be repeated.")
    parser.add_argument("--dry-run", action="store_true", help="Only show rows that would be inserted.")
    return parser.parse_args()


def main() -> None:
    setup_logging(logging.INFO)
    args = parse_args()
    paths = load_data_paths()
    silver_dir = Path(paths["analytics_silver"])

    dim_run = _load_partitioned_table(silver_dir, "dim_run")
    fact_model_artifacts = _load_partitioned_table(silver_dir, "fact_model_artifacts")

    if dim_run.empty:
        logger.info("No dim_run rows found; nothing to backfill.")
        return

    if args.asset:
        dim_run = dim_run[dim_run.get("asset", pd.Series(dtype=str)).astype(str) == str(args.asset)].copy()

    if "status" in dim_run.columns:
        dim_run = dim_run[dim_run["status"].astype(str).str.lower() == "ok"].copy()

    if args.run_id:
        wanted = {str(r).strip() for r in args.run_id if str(r).strip()}
        dim_run = dim_run[dim_run["run_id"].astype(str).isin(wanted)].copy()

    if dim_run.empty:
        logger.info("No candidate runs after filters.")
        return

    existing = set()
    if not fact_model_artifacts.empty and "run_id" in fact_model_artifacts.columns:
        existing = set(fact_model_artifacts["run_id"].dropna().astype(str).tolist())

    candidates = dim_run[~dim_run["run_id"].astype(str).isin(existing)].copy()
    candidates = candidates.drop_duplicates(subset=["run_id"]) if not candidates.empty else candidates

    rows_to_insert: list[dict[str, Any]] = []
    skipped: list[tuple[str, str]] = []
    for _, r in candidates.iterrows():
        run_id = str(r.get("run_id"))
        row = _build_row(r.to_dict())
        if row is None:
            skipped.append((run_id, "missing_required_artifacts_or_paths"))
            continue
        rows_to_insert.append(row)

    logger.info(
        "Backfill fact_model_artifacts scan completed",
        extra={
            "asset": args.asset,
            "candidates": int(len(candidates)),
            "to_insert": int(len(rows_to_insert)),
            "skipped": int(len(skipped)),
            "dry_run": bool(args.dry_run),
        },
    )

    if skipped:
        for run_id, reason in skipped[:20]:
            logger.warning("Skipped run during model_artifacts backfill", extra={"run_id": run_id, "reason": reason})

    if args.dry_run:
        if rows_to_insert:
            preview_cols = ["run_id", "asset", "model_version", "checkpoint_path_best", "checkpoint_path_final"]
            preview = pd.DataFrame(rows_to_insert)[preview_cols]
            logger.info("Backfill dry-run preview", extra={"rows": preview.to_dict(orient="records")[:20]})
        return

    repo = ParquetAnalyticsRunRepository(output_dir=silver_dir)
    for row in rows_to_insert:
        repo.append_fact_model_artifacts(row)

    logger.info("Backfill fact_model_artifacts completed", extra={"inserted_rows": int(len(rows_to_insert))})


if __name__ == "__main__":
    main()
