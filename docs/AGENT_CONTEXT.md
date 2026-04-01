# Agent Context (LLM-First)

Purpose: provide concise operational context for coding agents (Codex/Claude) to reduce ambiguity.

## Repository Context
- Project root: `financial-time-series-forecasting`
- Primary docs index: `docs/INDEX.md`
- Checklists source of truth: `docs/05_checklists/`

## Operational Commands (Canonical)
- Refresh analytics + quality:
  - `python -m src.main_refresh_analytics_store --fail-on-quality`
- Refresh analytics + scoped plots:
  - `python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL --plots-scope-csv data/analytics/selection/frozen_candidates_0_2_2.csv --plots-scope-sweep-prefixes 0_2_2_`
- Train model:
  - `python -m src.main_train_tft --asset AAPL --features BASELINE_FEATURES,TECHNICAL_FEATURES`
- Run inference:
  - `python -m src.main_infer_tft --asset AAPL --model-path <MODEL_VERSION> --start YYYYMMDD --end YYYYMMDD --overwrite`

## Non-Negotiable Data Rules
- Paired statistical comparison requires exact temporal intersection by `target_timestamp`.
- Quantile models must persist valid `p10 <= p50 <= p90`.
- Gold decision tables must be reproducible from persisted silver/gold only (no retrain).

## Editing Rules For Agents
- Do not duplicate metric definitions across multiple files.
- Prefer updating canonical docs and linking from other docs.
- When adding new artifact/report, update:
  1. `docs/05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md`
  2. `docs/INDEX.md`
  3. corresponding runbook in `docs/06_runbooks/`
