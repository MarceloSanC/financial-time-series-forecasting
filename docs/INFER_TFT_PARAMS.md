# Inferencia TFT - Parametros

Este documento centraliza os parametros do `src.main_infer_tft`.

## Minimo Para Rodar

| Parametro | Tipo | Obrigatorio | Exemplo | Impacto |
|---|---|---|---|---|
| `--asset` | `str` | Sim* | `--asset AAPL` | Define ativo alvo |
| `--model-path` | `str` | Sim* | `--model-path data/models/AAPL/runs/20260302_010101_B` | Seleciona artefato do modelo |
| `--start` | `str yyyymmdd` | Nao | `--start 20260101` | Inicio do periodo explicito |
| `--end` | `str yyyymmdd` | Nao | `--end 20260228` | Fim do periodo explicito |

\* Pode ser fornecido via `--config-json`.

## Parametros Opcionais

| Parametro | Tipo | Default | Exemplo | Impacto |
|---|---|---:|---|---|
| `--overwrite` | flag | `False` | `--overwrite` | Regrava inferencias no periodo |
| `--batch-size` | `int` | `64` | `--batch-size 128` | Controle de throughput/memoria |
| `--config-json` | `str` | - | `--config-json config/infer_tft_aapl.json` | Carrega configuracao por arquivo |
| `--dataset-dir` | `str` | de `data_paths.yaml` | `--dataset-dir /mnt/dataset_tft` | Override do repositorio dataset_tft |
| `--inference-dir` | `str` | de `data_paths.yaml` | `--inference-dir /mnt/inference_tft` | Override do repositorio de inferencia |
| `--auto-refresh` | flag | `False` | `--auto-refresh` | Habilita refresh incremental automatico quando faltar cobertura no dataset_tft |

## Regras De Precedencia

- `defaults` <- `JSON` <- `CLI`
- Parametros passados por CLI sempre sobrescrevem JSON.

## JSON De Exemplo

`config/infer_tft_aapl.json`:

```json
{
  "asset": "AAPL",
  "model_path": "data/models/AAPL/runs/20260302_010101_B",
  "start": "20260101",
  "end": "20260228",
  "overwrite": false,
  "batch_size": 64,
  "auto_refresh": false
}
```

Execucao:

```bash
python -m src.main_infer_tft --config-json config/infer_tft_aapl.json
```

## Validacoes Aplicadas Pela Pipeline

- `asset` do modelo deve ser igual ao `asset` solicitado.
- O `dataset_tft` deve conter as colunas requeridas pelo modelo.
- O periodo solicitado deve ter contexto suficiente para `max_encoder_length`.
- Sem `--start`: precisa existir historico no repositorio de inferencia.
- Modo padrao (fail-fast): se `end` estiver fora da cobertura do `dataset_tft`, a inferencia falha com mensagem orientativa para rodar fetch/build manualmente.
- Com `--auto-refresh`: se `end` estiver fora da cobertura do `dataset_tft`, a pipeline tenta refresh incremental dos dados.
- A inferencia exige `dataset_parameters` no artefato e reconstrucao via `TimeSeriesDataSet.from_parameters` (sem fallback legado).

## Erros Comuns

`No inference history found for asset. Provide an explicit start/end period.`
- Ocorre quando voce roda sem `--start` e ainda nao existe inferencia para o ativo.

`Requested period is outside dataset_tft coverage after refresh`
- Ocorre quando mesmo apos refresh nao ha dados suficientes para cobrir o periodo.

`Insufficient historical context for requested start date and model context window`
- Ocorre quando o inicio pedido nao tem linhas anteriores suficientes para o contexto do modelo.

`[INFER_DATASET_SPEC_INVALID_TYPE]`
- Ocorre quando `dataset_parameters.pkl` existe, mas nao contem um `dict`.

`[INFER_DATASET_SPEC_MISSING]`
- Ocorre quando o artefato nao possui `dataset_parameters` para reconstruir o `TimeSeriesDataSet`.

`[INFER_DATASET_SPEC_INCOMPATIBLE]`
- Ocorre quando `dataset_parameters` estao incompletos/invalidos ou incompativeis com a versao atual da lib.
