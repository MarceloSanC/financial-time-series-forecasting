# Executando Inferencia TFT

Este guia cobre a etapa 10 da pipeline: inferencia com modelo TFT treinado em dados novos.

## Objetivo

- Executar previsoes por ativo usando artefatos de treino ja salvos.
- Persistir previsoes em `data/processed/inference_tft/{ASSET}/`.
- Suportar execucao por periodo explicito ou incremental desde a ultima inferencia.

## Pre-requisitos

- Dataset TFT existente para o ativo:
  - `data/processed/dataset_tft/{ASSET}/dataset_tft_{ASSET}.parquet`
- Modelo treinado existente (diretorio de versao):
  - `data/models/{ASSET}/{VERSION}/`
- Chaves de API no ambiente (somente quando precisar refresh de dados):
  - `ALPHAVANTAGE_API_KEY`

## Execucao Minima

```bash
python -m src.main_infer_tft \
  --asset AAPL \
  --model-path data/models/AAPL/20260302_010101_B \
  --start 20260101 \
  --end 20260228
```

Para manter paridade treino/inferencia, a inferencia exige `dataset_parameters` do artefato
e reconstrucao via `TimeSeriesDataSet.from_parameters` (sem fallback legado).

## Comportamento De Janela Temporal

### 1) Periodo explicito (`--start/--end`)

- Inferencia somente no intervalo informado.
- Sem `--overwrite`, timestamps ja existentes no repositorio de inferencia sao ignorados.
- Com `--overwrite`, o intervalo e recalculado e regravado.

### 2) Periodo implicito (sem `--start`)

- O pipeline tenta iniciar em `ultimo_timestamp_inferencia + 1 dia`.
- Se nao existir historico de inferencia para o ativo, o processo falha e exige periodo explicito.

## Cobertura De Dados E Refresh Incremental

Antes de inferir, a pipeline valida:

- Se `dataset_tft` cobre o periodo solicitado.
- Se existe historico suficiente para o `max_encoder_length` do modelo.

Modo padrao (`fail-fast`):

- Se o `end` solicitado estiver alem do `dataset_tft`, a inferencia falha com orientacao para rodar fetch/build manualmente.

Modo opcional (`--auto-refresh`):

- Se o `end` solicitado estiver alem do `dataset_tft`, a pipeline roda refresh incremental:

1. candles
2. news raw
3. scored news (FinBERT)
4. sentiment daily
5. technical indicators
6. fundamentals
7. rebuild do dataset_tft ate o `end` solicitado

## Saidas

Repositorio de inferencia:

- `data/processed/inference_tft/{ASSET}/inference_tft_{ASSET}.parquet`

Colunas persistidas:

- `asset_id`
- `timestamp`
- `model_version`
- `model_path`
- `feature_set_name`
- `features_used_csv`
- `prediction`
- `quantile_p10`
- `quantile_p50`
- `quantile_p90`
- `inference_run_id`
- `created_at`

## Invariante De Versao De Modelo

- `model_version` deve seguir o padrao `YYYYMMDD_HHMMSS_<TAG>`.
- O nome do diretorio do modelo deve ser exatamente igual ao `metadata.json.version`.
- O repositorio de inferencia rejeita gravacao quando o mesmo `model_version` aparece com `model_path` diferente.

## Exemplos Uteis

Inferencia sem sobrescrever resultados ja calculados:

```bash
python -m src.main_infer_tft \
  --asset AAPL \
  --model-path data/models/AAPL/20260302_010101_B \
  --start 20260101 \
  --end 20260228
```

Inferencia com overwrite:

```bash
python -m src.main_infer_tft \
  --asset AAPL \
  --model-path data/models/AAPL/20260302_010101_B \
  --start 20260101 \
  --end 20260228 \
  --overwrite
```

Inferencia via JSON:

```bash
python -m src.main_infer_tft --config-json config/infer_tft_aapl.json
```

Consulte os parametros completos em `docs/INFER_TFT_PARAMS.md`.
