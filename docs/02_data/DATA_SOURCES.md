---
title: Data Sources
scope: Fontes externas usadas no projeto (yfinance para candles, finnhub/alpha vantage para news, alpha vantage para fundamentals) e caminho canonico de ingestao de cada uma.
update_when:
  - nova fonte de dados externa for integrada
  - fonte existente for substituida ou descontinuada
  - politica de incremental/refetch mudar
  - chave de API ou autenticacao mudar
canonical_for: [data_sources, external_apis, ingestion_path, yfinance, finnhub, alpha_vantage]
---

# Data Sources

## Purpose
Definir as fontes de dados usadas no projeto e o caminho canonico de ingestao
de cada uma, com rastreabilidade para implementacao e validacao.

## Canonical Sources

### Market candles (OHLCV)
- Origem: `yfinance`
- Camada: `data/raw/market/candles/{ASSET}/`
- Contrato de schema: `src/infrastructure/schemas/candle_parquet_schema.py`
- Pipeline:
  - `src/main_candles.py`
  - `src/use_cases/fetch_candles_use_case.py`
  - `src/adapters/yfinance_candle_fetcher.py`
  - `src/adapters/parquet_candle_repository.py`

### News (raw)
- Origens: `Finnhub`, `Alpha Vantage`
- Camada: `data/raw/news/{ASSET}/`
- Contrato de schema: `src/infrastructure/schemas/news_parquet_schema.py`
- Pipeline:
  - `src/main_news_dataset.py`
  - `src/use_cases/fetch_news_use_case.py`
  - `src/adapters/finnhub_news_fetcher.py`
  - `src/adapters/alpha_vantage_news_fetcher.py`
  - `src/adapters/parquet_news_repository.py`

### Sentiment (processed)
- Origem: scoring FinBERT sobre news raw
- Camadas:
  - `data/processed/scored_news/{ASSET}/`
  - `data/processed/sentiment_daily/{ASSET}/`
- Contratos de schema:
  - `src/infrastructure/schemas/scored_news_parquet_schema.py`
  - `src/infrastructure/schemas/daily_sentiment_parquet_schema.py`
- Pipeline:
  - `src/main_sentiment.py`
  - `src/main_sentiment_features.py`
  - `src/use_cases/infer_sentiment_use_case.py`
  - `src/use_cases/sentiment_feature_engineering_use_case.py`

### Technical indicators (processed)
- Origem: calculo causal sobre OHLCV
- Camada: `data/processed/technical_indicators/{ASSET}/`
- Contratos de schema:
  - `src/infrastructure/schemas/technical_indicator_parquet_schema.py`
  - `src/infrastructure/schemas/technical_indicators_schema.py`
- Pipeline:
  - `src/main_technical_indicators.py`
  - `src/use_cases/technical_indicator_engineering_use_case.py`
  - `src/adapters/technical_indicator_calculator.py`

### Fundamentals (processed)
- Origem: Alpha Vantage fundamentals
- Camada: `data/processed/fundamental_indicators/{ASSET}/`
- Contrato de schema: `src/infrastructure/schemas/fundamental_parquet_schema.py`
- Pipeline:
  - `src/main_fundamentals.py`
  - `src/use_cases/fetch_fundamentals_use_case.py`

### TFT dataset (processed)
- Origem: uniao temporal de candles + technical + sentiment + fundamentals
- Camada: `data/processed/dataset_tft/{ASSET}/`
- Contratos de schema:
  - `src/infrastructure/schemas/tft_dataset_schema.py`
  - `src/infrastructure/schemas/tft_dataset_parquet_schema.py`
- Pipeline:
  - `src/main_dataset_tft.py`
  - `src/use_cases/build_tft_dataset_use_case.py`
  - `src/adapters/parquet_tft_dataset_repository.py`

### Inference outputs
- Camada: `data/processed/inference_tft/{ASSET}/`
- Contrato de schema: `src/infrastructure/schemas/tft_inference_parquet_schema.py`
- Pipeline:
  - `src/main_infer_tft.py`
  - `src/use_cases/run_tft_inference_use_case.py`
  - `src/adapters/parquet_tft_inference_repository.py`

### Analytics store (silver + gold)
- Silver (source of truth analitico): facts/dims em Parquet
- Gold (derivados para decisao): tabelas agregadas reconstruiveis
- Contrato de schema: `src/infrastructure/schemas/analytics_store_schema.py`
- Pipeline:
  - `src/main_refresh_analytics_store.py`
  - `src/use_cases/refresh_analytics_store_use_case.py`
  - `src/use_cases/validate_analytics_quality_use_case.py`
  - `src/adapters/parquet_analytics_run_repository.py`

## Operational Validation
- Runbook end-to-end: `docs/06_runbooks/RUN_DATASET.md`
- Quick smoke:
  - `python -m src.main_candles --asset AAPL`
  - `python -m src.main_dataset_tft --asset AAPL`
  - `python -m src.main_train_tft --asset AAPL`
  - `python -m src.main_infer_tft --asset AAPL --model-path <MODEL_VERSION> --start 20260101 --end 20260228`
- Quality gate:
  - `python -m src.main_refresh_analytics_store --fail-on-quality`

## Checklist Cross-Reference
- Tracking operacional: `docs/05_checklists/CHECKLISTS.md`
- Checklist de analytics: `docs/05_checklists/ANALYTICS_STORE_CHECKLIST.md`
