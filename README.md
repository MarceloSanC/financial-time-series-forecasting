# Financial Time Series Forecasting

End-to-end machine learning project for financial time series forecasting with:
- data ingestion (market/news/fundamentals),
- feature engineering (technical, sentiment, derived features),
- TFT model training and inference,
- analytics storage for reproducible model evaluation without retraining.

The project is structured with Clean Architecture (adapters, interfaces, use cases, domain services), with emphasis on traceability, reproducibility, and academic-grade evaluation.

## Project Scope
- **Primary goal**: generate robust, reproducible evidence for model comparison and decision support in financial assets.
- **Model family**: Temporal Fusion Transformer (TFT), including quantile outputs for uncertainty-aware analysis.
- **Data stack**: Parquet + DuckDB for analytics persistence and interactive querying.

## Main Capabilities
- Historical data pipelines:
  - candles (market OHLCV),
  - news ingestion,
  - FinBERT sentiment scoring,
  - daily sentiment aggregation,
  - technical indicators,
  - fundamentals.
- Dataset builder for TFT (`dataset_tft`).
- Training pipeline with split/warmup validation and quality gates.
- Inference pipeline with feature compatibility checks and quantile support.
- Analytics Store (silver/gold) for run/epoch/OOS artifacts and statistical post-analysis.

## High-Level Architecture
```
src/
  adapters/         # external integrations and IO adapters
  interfaces/       # ports
  use_cases/        # application orchestration
  domain/           # business rules/services
  entities/         # core entities
  infrastructure/   # schemas and storage contracts
```

For the full structure, see `docs/PROJECT_STRUCTURE.md`.

## Repository Structure
```
config/             # runtime and source configuration
data/               # raw, processed, analytics outputs
docs/               # checklists, runbooks, guides
src/                # source code
tests/              # unit/integration tests
```

## Environment Setup
### Requirements
- Python 3.12+
- GNU Make
- Git

### Quick start
```bash
git clone git@github.com:MarceloSanC/financial-time-series-forecasting.git
cd financial-time-series-forecasting
python -m venv .venv
source .venv/bin/activate
make install
```

## Configuration
Main configuration files:
- `config/data_sources.yaml` (providers, assets, periods, source-specific settings)
- `config/data_paths.yaml` (local storage layout)

Set API keys via environment variables / `.env` (never commit secrets).

## Running Pipelines
### Core data steps (example asset: AAPL)
```bash
make run-candles ASSET=AAPL
make run-news-raw ASSET=AAPL
make run-sentiment ASSET=AAPL
make run-sentiment-feat ASSET=AAPL
make run-indicators ASSET=AAPL
python -m src.main_fundamentals --asset AAPL
python -m src.main_dataset_tft --asset AAPL --overwrite
```

### Training
```bash
python -m src.main_train_tft --asset AAPL --features BASELINE_FEATURES,TECHNICAL_FEATURES
```

### Inference
```bash
python -m src.main_infer_tft --asset AAPL --model-path <MODEL_VERSION> --start 20250101 --end 20250228
```

### Analytics refresh + validation
```bash
python -m src.main_refresh_analytics_store --fail-on-quality
```

## Quality and CI
- Local quality gate:
```bash
make ci-local
```
- CI workflows are defined in `.github/workflows/ci.yml`.

## Documentation Index
- `docs/RUNNING_PIPELINE.md`
- `docs/RUNNING_TESTS.md`
- `docs/RUNNING_TFT_INFERENCE.md`
- `docs/ANALYTICS_STORE_CHECKLIST.md`
- `docs/PREDICTIONS_AND_METRICS_CHECKLIST.md`
- `docs/FEATURES_SET_CHECKLIST.md`

## Academic Context
This repository supports TCC research focused on:
- financial forecasting with structured feature sets,
- uncertainty-aware predictions (quantiles),
- reproducible model comparison across folds/seeds/configurations.

## Author
Marcelo Santos  
UFSC - Engenharia Mecatrônica
