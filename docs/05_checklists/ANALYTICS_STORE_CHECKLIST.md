---
title: Analytics Store Checklist
scope: Tracking de implementacao da analytics store em 3 niveis (run-level, epoch-level, timestamp-level) com schemas, contratos e quality gates. Para definicoes canonicas, ver 01_architecture/ANALYTICS_STORE_ARCHITECTURE.md e 02_data/DATA_CONTRACTS.md.
update_when:
  - nova tabela silver/gold for adicionada
  - status de implementacao (checkbox) for atualizado
  - novo campo obrigatorio for adicionado a tabela existente
canonical_for: [analytics_store_checklist, analytics_store_implementation_tracking]
---

# Analytics Store Checklist (DuckDB + Parquet)

Objetivo: coletar dados suficientes para analises futuras sem retraining, em 3 niveis:
- run-level
- epoch-level
- timestamp-level (OOS alinhado)

Legenda de prioridade para implementacao:
- `P0` = indispensavel para defensabilidade academica (v0 obrigatorio)
- `P1` = muito recomendavel (v0 alvo, pode fechar logo apos P0)
- `P2` = pos-v0 (nao bloqueia analises robustas sem retrain)

---

## Decisoes Fechadas (Contrato v0)

- [x] `run_id` = `sha256(asset|feature_set_hash|trial_number|fold|seed|model_version|config_signature|split_signature|pipeline_version)` em JSON canonico.
- [x] `partial_failed` = treino concluiu, mas faltou pelo menos 1 artefato obrigatorio (ex.: sem `fact_oos_predictions` ou sem `fact_epoch_metrics`).
- [x] `schema_version` = coluna obrigatoria em toda `dim_*`/`fact_*`, iniciando em `1`.
- [x] `feature_set_hash` = `sha256("|".join(features_ordered))`.
- [x] `dataset_fingerprint` = `sha256(asset, timestamp_min, timestamp_max, row_count, close_sum, volume_sum, parquet_file_hash)`.
- [x] `split_fingerprint` = `sha256` das listas de timestamps ordenadas por split (`train|val|test`).
- [x] `config_signature` = `sha256(training_config canonico sem campos volateis)`.
- [x] `fact_oos_predictions` grao/PK logica = `run_id + split + horizon + timestamp + target_timestamp`.
- [x] Particionamento Parquet:
- [x] `dim_run`, `fact_config`, `fact_run_snapshot` => `asset/sweep_id`.
- [x] `fact_epoch_metrics` => `asset/sweep_id/fold`.
- [x] `fact_oos_predictions` => `asset/feature_set_name/year`.
- [x] Campos obrigatorios = ids, chaves temporais, metricas core, status, quantis, attention.
- [x] Campos opcionais = hardware detalhado, logs extensos.
- [x] Tipos canonicos: `timestamps` em UTC ISO8601; metricas `float64`; contagens `int64`; ids/status/chaves `string`.
- [x] Nulabilidade: `run_id` nunca nulo; `execution_id` nulo permitido em P0.
- [x] Alinhamento OOS = join por `asset + split + horizon + target_timestamp`; descartar pares incompletos para testes pareados.
- [x] Update policy: `dim_run` upsert por `run_id`; tabelas fato append-only por padrao; upsert apenas em reprocessamento explicito.
- [x] Retencao/backup: Silver Parquet com retencao total em v0; DuckDB reconstruivel com backup diario opcional.
- [x] Escopo Gold P1: `gold_runs_long`, `gold_oos_consolidated`, `vw_runs_latest`, `vw_fold_seed_metrics`, `vw_oos_aligned_pairs`.

---

## Stage 0 - Contrato e Escopo (obrigatorio antes de implementar)

- [x] `[P0]` Definir `run_id` como identidade logica deterministica.
- [ ] `[P2]` Definir `execution_id` como identidade fisica por execucao (UUID).
- [ ] `[P2]` Definir relacao oficial `execution_id -> run_id` (many-to-one).
- [x] `[P0]` Definir status canonicos de execucao: `ok`, `failed`, `partial_failed`.
- [x] `[P1]` Definir `schema_version` por tabela.
- [x] `[P0]` Definir Parquet (`silver`) como source of truth.
- [x] `[P0]` Definir DuckDB como camada derivada/reconstruivel.
- [x] `[P0]` Definir contrato de `feature_set_name`.
- [x] `[P0]` Definir contrato da lista de features com ordem preservada.
- [x] `[P0]` Definir contrato de `feature_set_hash` (hash da lista ordenada de features).
- [x] `[P0]` Definir contrato de `prediction_mode` por run: `point` ou `quantile`.
- [x] `[P0]` Definir politica default: `prediction_mode=quantile` (point permitido apenas por override explicito).
- [x] `[P0]` Definir quantis e attention como campos obrigatorios para analise comparativa oficial.

---

## Stage 1 - Coleta Run-Level (identidade, config, snapshot, falhas)

### 1.1 Identidade e rastreabilidade do experimento

- [x] `[P0]` Salvar `run_id`, `parent_sweep_id`, `trial_number`, `fold`, `seed`, `asset`.
- [x] `[P0]` Salvar `feature_set_name` e lista exata de features usadas (ordem preservada).
- [x] `[P0]` Salvar `feature_set_hash` por run para rastreabilidade de combinacao exata de features.
- [x] `[P0]` Salvar `model_version`.
- [x] `[P1]` Salvar `checkpoint_path_final` e `checkpoint_path_best`.
- [x] `[P1]` Salvar `git_commit`, `pipeline_version`, `created_at_utc`.
- [x] `[P1]` Salvar versao das libs: torch, lightning, pytorch-forecasting, pandas e dependencias criticas.
- [x] `[P1]` Salvar hardware: CPU/GPU, nome da placa, memoria.

### 1.2 Snapshot de dados e splits

- [x] `[P0]` Salvar intervalo temporal total do dataset usado.
- [x] `[P0]` Salvar `train_start/end`, `val_start/end`, `test_start/end` efetivos.
- [x] `[P0]` Salvar politica de warmup (`strict_fail`/`drop_leading`) e datas ajustadas.
- [x] `[P0]` Salvar numero de amostras por split e por fold.
- [x] `[P0]` Salvar hash/fingerprint do dataset.
- [x] `[P0]` Salvar hash/fingerprint dos splits.
- [x] `[P1]` Salvar lista de timestamps por split ou referencia reproduzivel.

### 1.3 Configuracao completa de treino

- [x] `[P0]` Salvar hiperparametros finais do modelo.
- [x] `[P0]` Salvar search space (quando Optuna).
- [x] `[P0]` Salvar objetivo de otimizacao e funcao de score.
- [x] `[P0]` Salvar early stopping params, batch size, max epochs, learning rate.
- [x] `[P1]` Salvar parametros de normalizacao/scalers.
- [x] `[P0]` Salvar `dataset_parameters` completos do TimeSeriesDataSet.
- [x] `[P0]` Salvar `config_json` completo serializado.
- [x] `[P0]` Salvar `prediction_mode` e loss usada no treino.
- [x] `[P0]` Salvar lista de quantis treinados (ex.: `[0.1, 0.5, 0.9]`) quando `prediction_mode=quantile`.
- [x] `[P0]` Garantir que configs default de treino/sweep publiquem `prediction_mode=quantile`.

### 1.4 Metadados de execucao e falhas

- [x] `[P0]` Salvar status por run (`ok`, `failed`, `partial_failed`).
- [x] `[P0]` Salvar traceback/erro resumido quando falha.
- [x] `[P1]` Salvar `cmdline`/`entrypoint`.
- [x] `[P2]` Salvar `stdout/stderr` truncados.
- [x] `[P1]` Salvar duracao total de execucao.
- [x] `[P2]` Salvar ETA estimado registrado (quando houver).
- [x] `[P2]` Salvar numero de tentativas/retries.

---

## Stage 2 - Coleta Epoch-Level

- [x] `[P0]` Salvar `train_loss`, `val_loss` por epoca.
- [x] `[P0]` Salvar `best_epoch`.
- [x] `[P0]` Salvar `stopped_epoch`.
- [x] `[P0]` Salvar `early_stop_reason`.
- [x] `[P1]` Salvar tempo por epoca.
- [x] `[P1]` Salvar tempo total de treino.
- [x] `[P1]` Salvar curva de convergencia reproduzivel.

---

## Stage 3 - Coleta Timestamp-Level (OOS essencial)

- [x] `[P0]` Salvar por timestamp: `y_true`, `y_pred`.
- [x] `[P0]` Salvar por timestamp: `error`, `abs_error`, `sq_error`.
- [x] `[P0]` Salvar identificadores por linha: `run_id`, `fold`, `seed`, `config_id/signature`, `feature_set`, `asset`.
- [x] `[P0]` Salvar `horizon` e `target_timestamp` para multi-horizonte.
- [x] `[P0]` Salvar quantis TFT (`p10`, `p50`, `p90` ou lista configurada) como obrigatorios no OOS.
- [x] `[P0]` Garantir alinhamento temporal OOS entre modelos para DM/MCS.
- [x] `[P0]` Politica default de coleta timestamp-level: persistir apenas `val/test` (split `train` opcional via `evaluate_train_split=true` para diagnostico in-sample).

---

## Stage 4 - Artefatos e Estruturas Analiticas Pre-Prontas

### 4.1 Artefatos de modelo

- [x] `[P1]` Salvar checkpoint e config serializada.
- [x] `[P1]` Salvar scalers/encoders versionados.
- [x] `[P0]` Salvar feature importance/attention.
- [x] `[P0]` Politica de performance v0: `compute_feature_importance=false` por padrao em sweeps optuna; habilitar em rerun dedicado/top-k para reduzir latencia pos-treino sem perder analise final.
- [x] `[P0]` Fluxo recomendado de interpretabilidade: executar sweeps com `compute_feature_importance=false` e depois rerodar apenas `top3` por `feature_set` via `explicit_configs` com `compute_feature_importance=true`.
- [x] `[P2]` Salvar historico de treino e referencias de logs estruturados.

### 4.2 Estruturas para analise posterior

- [x] `[P0]` Disponibilizar tabela longa de runs (`config x fold x seed`).
- [x] `[P2]` Disponibilizar tabela de ranking por config.
- [x] `[P2]` Disponibilizar tabela de impacto por grupo de feature set (agregado por fold/seed e metrica).
- [x] `[P2]` Disponibilizar tabela de consistencia top-k.
- [x] `[P2]` Disponibilizar tabela de IC95 por metrica/config.
- [x] `[P1]` Disponibilizar tabela consolidada de predições OOS.

---

## Stage 5 - Qualidade de Dados e Validacoes

- [x] `[P0]` Validar unicidade e consistencia de `run_id` e `execution_id` (quando existir).
- [x] `[P0]` Validar integridade referencial entre fatos e dimensoes.
- [x] `[P0]` Validar ausencia de NaN em metricas obrigatorias.
- [x] `[P0]` Validar consistencia temporal dos timestamps.
- [x] `[P0]` Validar cardinalidade esperada (`config x fold x seed`).
- [x] `[P0]` Validar minimos por split (`n_samples >= contexto`).
- [x] `[P0]` Validar contratos obrigatorios de quantis/attention para runs oficiais.
- [ ] `[P2]` Publicar relatorio automatico de qualidade por ingestao em `gold`.
- [x] `[P1]` Suportar `fail-on-quality` para CI/CD.

---

## Stage 6 - CI/CD e Operacao Escalavel

### 6.1 CI por estagios

- [x] `[P1]` Rodar `lint + type + unit` em todo PR.
- [x] `[P1]` Rodar testes de integracao de escrita Parquet + refresh DuckDB.
- [x] `[P1]` Rodar contract-tests de schema.
- [x] `[P1]` Rodar quality gate com dataset sintetico.

### 6.2 CD e operacao

- [ ] `[P2]` Gerar artefatos `gold` em toda execucao relevante.
- [ ] `[P2]` Versionar SQLs analiticos em pacote estavel.
- [ ] `[P2]` Definir rollback (rebuild DuckDB a partir de Parquet).
- [ ] `[P2]` Definir backup e retencao de Parquet + DuckDB.
- [ ] `[P2]` Garantir `.duckdb` e Parquet volumosos fora do Git.
- [ ] `[P2]` Definir ownership tecnico (schema, ingestao, qualidade, operacao).
- [ ] `[P2]` Documentar runbook de troubleshooting.

---

## Definition of Done (Sem Retraining para Analises Planejadas)

- [x] `[P0]` Todos os dados de run-level, epoch-level e timestamp-level estao persistidos.
  1. Execute um treino real: `python -m src.main_train_tft --asset AAPL --features BASELINE_FEATURES,TECHNICAL_FEATURES`.
  2. Valide existencia de parquet com linhas em `dim_run`, `fact_config`, `fact_run_snapshot`, `fact_split_metrics`, `fact_epoch_metrics`, `fact_oos_predictions`, `fact_model_artifacts`, `bridge_run_features`.
  3. Aceite: todas as tabelas acima possuem ao menos 1 `run_id` do treino executado.
- [x] `[P0]` Configuracao, dataset snapshot e artefatos permitem reproducao auditavel.
  1. No `run_id` do treino, valide preenchimento de: `training_config_json`, `dataset_parameters_json`, `dataset_fingerprint`, `split_fingerprint`, `feature_set_hash`, `model_version`, `checkpoint_path_best/final`.
  2. Rode inferencia com o mesmo modelo: `python -m src.main_infer_tft --asset AAPL --model-path <MODEL_DIR> --start 20260101 --end 20260228`.
  3. Aceite: inferencia executa sem erro de contrato de dataset/feature e gera previsoes para o mesmo `asset`.
- [x] `[P0]` OOS alinhado permite DM/MCS e comparacoes pareadas sem retrain.
  1. Garanta pelo menos 2 `run_id` com mesmo `asset/split/horizon`.
  2. Execute refresh: `python -m src.main_refresh_analytics_store --fail-on-quality`.
  3. Valide no `gold_oos_consolidated.parquet` que existe intersecao por `asset + split + horizon + target_timestamp`.
  4. Aceite: para cada par de modelos comparados, existem pares completos (sem faltantes) apos alinhamento temporal.
- [x] `[P1]` Tabelas pre-prontas para ranking, robustez, consistencia e IC95 estao disponiveis.
  1. Execute refresh: `python -m src.main_refresh_analytics_store`.
  2. Valide existencia dos arquivos: `gold_ranking_by_config.parquet`, `gold_consistency_topk.parquet`, `gold_ic95_by_config_metric.parquet`, `gold_runs_long.parquet`, `gold_oos_consolidated.parquet`.
  3. Aceite: todos os arquivos existem e possuem pelo menos 1 linha.
- [x] `[P1]` Pipeline validado em CI com qualidade controlada e rastreabilidade completa.
  1. Local: `source .venv/bin/activate && make ci-local`.
  2. Remoto: abrir PR e confirmar jobs verdes em `.github/workflows/ci.yml` (`lint-type-unit` e `analytics-contract-and-quality`).
  3. Aceite: CI verde no PR e sem falha no `--fail-on-quality`.

---

## Referencia de Estruturas de Schema (Engenharia de Dados)

### Silver (fonte canonica em Parquet)

1. `dim_run`
- PK logica: `run_id`.
- Identidade fisica: `execution_id` (unico por tentativa).
- Campos: `parent_sweep_id`, `trial_number`, `fold`, `seed`, `asset`, `feature_set_name`,
  `model_version`, `checkpoint_path_final`, `checkpoint_path_best`, `git_commit`,
  `pipeline_version`, `created_at_utc`, `library_versions_json`, `hardware_info_json`,
  `status`, `duration_total_seconds`, `eta_recorded_seconds`, `retries`.

2. `fact_run_snapshot`
- FK: `run_id`.
- Campos: intervalo total do dataset, `train/val/test start/end` efetivos,
  politica e ajuste de warmup, `n_samples` por split/fold, `dataset_fingerprint`,
  `split_fingerprint`.

3. `fact_config`
- FK: `run_id`.
- Campos: hiperparametros finais, search space/objetivo (quando Optuna), early stopping,
  parametros de normalizacao/scalers, `dataset_parameters`, `config_json`,
  `prediction_mode`, `loss_name`, `quantile_levels` (quando aplicavel).

4. `fact_split_metrics`
- FK: `run_id`.
- Grao: `run_id + split`.
- Campos: RMSE, MAE, MAPE/sMAPE (quando aplicavel), DA, `n_samples`.

5. `fact_epoch_metrics`
- FK: `run_id`.
- Grao: `run_id + epoch`.
- Campos: `train_loss`, `val_loss`, `epoch_time_seconds`, `best_epoch`, `stopped_epoch`,
  `early_stop_reason`.

6. `fact_oos_predictions`
- FK: `run_id`.
- Grao: `run_id + split + horizon + timestamp + target_timestamp`.
- Campos: `y_true`, `y_pred`, `error`, `abs_error`, `sq_error`, `target_timestamp`.
- Quantis (`p10/p50/p90` ou lista configurada): obrigatorios.

7. `fact_model_artifacts` (`P0`)
- FK: `run_id`.
- Campos: paths de checkpoint/config/scalers/encoders, importance/attention (obrigatorios), referencias de logs.

8. `fact_failures` (`P0`)
- FK: `run_id` (nullable quando falha pre-run), `execution_id`.
- Campos: stage, erro resumido, traceback/hash, timestamp.
- Pos-v0 (`P2`): `cmdline`, `stdout/stderr` truncados.

9. `fact_inference_runs` (`P1`)
- FK: `run_id` (ou referencia consistente com `model_version`/`inference_run_id`).
- Campos: janela de inferencia, overwrite, batch, status, contadores
  (`inferred/skipped/upserts`), duracao.

10. `bridge_run_features` (`P0`)
- FK: `run_id`.
- Grao: `run_id + feature_order`.
- Campos: `feature_name`, `feature_order` (preserva ordem exata).

11. `fact_split_timestamps_ref` (`P1`)
- FK: `run_id`.
- Campos: `split`, referencia reproduzivel para timestamps (`artifact_path`/hash/lista compacta).

### Gold (camada analitica pronta para consumo)

- `gold_runs_long` (`config x fold x seed`) (`P1`).
- `gold_oos_consolidated` (`P1`).
- `gold_paired_oos_intersection_by_horizon` (`P0`): incluir `n_common`, `n_union`, `coverage_ratio`, `aligned_exact` por coorte comparavel (sweep/split_signature/split/horizon).
- `gold_ranking_by_config` (`P2`).
- `gold_consistency_topk` (`P2`).
- `gold_ic95_by_config_metric` (`P2`).

### Relacionamento principal

- `dim_run` e dimensao central.
- Todas as `fact_*` fazem join primario por `run_id`.
- `execution_id` separa tentativas fisicas de um mesmo `run_id`.
- `asset/feature_set/fold/seed/trial_number` devem ser materializados onde fizer sentido
  para consultas analiticas com menos joins.
