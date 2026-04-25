# Data Contracts

## Purpose
Consolidar os contratos de dados obrigatorios para reproducibilidade e
comparabilidade entre runs, sem substituir checklists de acompanhamento.

## Contract Layers

### Layer 1: Parquet schemas (raw/processed)
- Candles: `src/infrastructure/schemas/candle_parquet_schema.py`
- News raw: `src/infrastructure/schemas/news_parquet_schema.py`
- Scored news: `src/infrastructure/schemas/scored_news_parquet_schema.py`
- Daily sentiment: `src/infrastructure/schemas/daily_sentiment_parquet_schema.py`
- Technical indicators: `src/infrastructure/schemas/technical_indicator_parquet_schema.py`
- Fundamentals: `src/infrastructure/schemas/fundamental_parquet_schema.py`
- Dataset TFT: `src/infrastructure/schemas/tft_dataset_parquet_schema.py`
- Inference: `src/infrastructure/schemas/tft_inference_parquet_schema.py`

### Layer 2: Feature contract
- Canonical registry: `src/infrastructure/schemas/feature_registry.py`
- Validation schema: `src/infrastructure/schemas/feature_validation_schema.py`
- Core contract: `FeatureSpec(name, group, source_cols, formula_desc, anti_leakage_tag, warmup_count, dtype, null_policy)`

### Layer 3: Analytics store contract (silver/gold)
- Canonical schema map: `src/infrastructure/schemas/analytics_store_schema.py`
- Required invariants (P0):
  - deterministic `run_id`
  - `schema_version` per table
  - `feature_set_hash` from ordered list
  - `dataset_fingerprint` and `split_fingerprint`
  - OOS key uniqueness by (`run_id`,`split`,`horizon`,`timestamp`,`target_timestamp`)
  - quantile ordering (`p10 <= p50 <= p90`)
  - exact temporal alignment for paired tests by `target_timestamp`

## Canonical Identifiers
- `run_id`: logical deterministic experiment id
- `parent_sweep_id`: cohort boundary for scoped decisions
- `feature_set_name`: semantic group label
- `feature_set_hash`: hash of ordered feature list
- `model_version`: persisted model artifact version
- `split_signature` / `split_fingerprint`: comparability signature across runs

## Temporal and Causality Contracts
- Split chronology must be non-overlapping (`train < val < test`)
- Feature engineering must be causal (no future leakage)
- Fundamental joins must be as-of by reported date
- Sentiment aggregation must respect publication cutoff
- Paired DM/MCS/win-rate comparisons must use explicit intersection by
  `asset + split + horizon + target_timestamp`

## Source of Truth in Code
- Build dataset: `src/use_cases/build_tft_dataset_use_case.py`
- Train: `src/use_cases/train_tft_model_use_case.py`
- Infer: `src/use_cases/run_tft_inference_use_case.py`
- Refresh analytics: `src/use_cases/refresh_analytics_store_use_case.py`
- Validate quality: `src/use_cases/validate_analytics_quality_use_case.py`

## Validation
- Unit tests:
  - `tests/unit/infrastructure/schemas/test_feature_registry.py`
  - `tests/unit/infrastructure/schemas/test_feature_validation_schema.py`
  - `tests/unit/infrastructure/schemas/test_analytics_store_schema.py`
- Operational gate:
  - `python -m src.main_refresh_analytics_store --fail-on-quality`

## Checklist Cross-Reference
- Tracking and phased completion:
  - `docs/05_checklists/CHECKLISTS.md`
  - `docs/05_checklists/ANALYTICS_STORE_CHECKLIST.md`
