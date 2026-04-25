---
title: Data Flow
scope: Fluxo end-to-end de dados (raw -> processed -> silver -> gold) com paths concretos, sequencia operacional e responsabilidades por camada. Nao cobre schema (ver ANALYTICS_STORE_ARCHITECTURE) nem CLI (ver 06_runbooks/).
update_when:
  - nova camada de dados for introduzida (alem de raw/processed/silver/gold)
  - paths de armazenamento mudarem
  - sequencia operacional canonica mudar
  - politica de particionamento for revisada
canonical_for: [data_flow, raw_processed_silver_gold, partitioning_policy]
---

# Data Flow

## Proposito
Documentar o fluxo end-to-end de dados do projeto, da ingestao bruta ate a
materializacao das tabelas analiticas usadas para decisao. Nao cobre detalhes
de schema (ver `ANALYTICS_STORE_ARCHITECTURE.md`) nem operacao CLI
(ver `06_runbooks/`).

## Conceitos-chave
- **Camada raw:** dados brutos exatamente como recebidos da fonte externa
  (yfinance, finnhub, alpha vantage). Imutavel apos ingestao.
- **Camada processed:** dados intermediarios derivados (sentimento por noticia,
  indicadores tecnicos, dataset_tft), separados por responsabilidade.
- **Camada silver (analytics):** fatos atomicos rastreaveis por `run_id`
  (predicoes OOS, metricas por epoca, configs de treino).
- **Camada gold (analytics):** tabelas agregadas prontas para decisao
  (leaderboards, DM/MCS, calibracao, robustez), reconstruiveis sem retrain.

## Decisoes e escolhas
- **Parquet como source of truth em silver.** *Why:* tipos preservados,
  particionamento eficiente, leitura por coluna, compatibilidade com PyArrow/DuckDB.
- **DuckDB como camada derivada reconstruivel, nao persistida em git.** *Why:*
  evita estado mutavel comitado; sempre derivavel dos Parquets.
- **Particionamento `asset/feature_set/year` em `fact_oos_predictions`.** *Why:*
  consultas analiticas filtram quase sempre por essas chaves; reduz I/O.
- **Append-only por padrao em fatos.** *Why:* preserva historico para auditoria;
  reprocessamento e operacao explicita, nao silenciosa.

## Sequencia operacional canonica

```
yfinance/finnhub/alpha_vantage    (fontes externas)
        |
        v
data/raw/{candles, news, fundamentals}/{asset}/    (camada raw, imutavel)
        |
        v
data/processed/{scored_news, sentiment_daily, technical_indicators,
                fundamentals, dataset_tft}/{asset}/    (camada processed)
        |
        v
src.main_train_tft / src.main_tft_optuna_sweep    (treino)
        |
        v
data/models/{asset}/{model_version}/    (checkpoints + config + metadata)
        |
        v
data/analytics/silver/{dim_run, fact_*}/asset={asset}/    (fatos atomicos)
        |
        v
src.main_refresh_analytics_store    (materializacao)
        |
        v
data/analytics/gold/{gold_*}.parquet    (tabelas de decisao)
```

## Fonte da verdade (codigo)
- `src/use_cases/fetch_candles_use_case.py`, `fetch_news_use_case.py`,
  `fetch_fundamentals_use_case.py` — ingestao raw
- `src/use_cases/build_tft_dataset_use_case.py` — consolidacao processed
- `src/use_cases/train_tft_model_use_case.py` — emissao silver via treino
- `src/use_cases/refresh_analytics_store_use_case.py` — materializacao gold
- `src/adapters/parquet_*_repository.py` — implementacao concreta de cada camada

## Documentos relacionados
- `01_architecture/ANALYTICS_STORE_ARCHITECTURE.md` — camadas silver/gold em detalhe
- `02_data/DATA_SOURCES.md` — fontes externas e contratos de ingestao
- `02_data/DATA_CONTRACTS.md` — chaves, fingerprints, schema_version
- `06_runbooks/RUN_PIPELINE_QUICKSTART.md` — sequencia operacional CLI
