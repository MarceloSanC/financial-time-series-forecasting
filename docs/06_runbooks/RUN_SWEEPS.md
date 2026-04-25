# Rodando Analise de Modelo (Sweeps)

Este guia documenta o uso do pipeline de analise de hiperparametros via:

- `python -m src.main_tft_param_sweep`

Ele executa treinos OFAT (one-factor-at-a-time), consolida resultados e gera relatorios/plots.

## 1) Pre-requisitos

1. Dataset TFT do ativo ja gerado:
- `data/processed/dataset_tft/{ASSET}/dataset_tft_{ASSET}.parquet`

2. Ambiente com dependencias de treino e plots:
- `pytorch_forecasting`, `lightning`, `matplotlib`, etc.

3. Arquivo de configuracao JSON para o sweep:
- por padrao: `config/sweeps/ofat/model_analysis.default.json`
- recomendado: criar arquivos em `config/sweeps/ofat/*.json`

## 2) Estrutura minima do JSON

Exemplo:

```json
{
  "test_type": "ofat",
  "output_subdir": "0_0_sweep_all_params_robust_vs_baseline",
  "features": "BASELINE_FEATURES",
  "replica_seeds": [7, 11, 13, 42, 123],
  "walk_forward": {
    "enabled": true,
    "folds": [
      {
        "name": "wf_1",
        "train_start": "20100101",
        "train_end": "20161231",
        "val_start": "20170101",
        "val_end": "20181231",
        "test_start": "20190101",
        "test_end": "20201231"
      }
    ]
  },
  "training_config": {
    "max_encoder_length": 120,
    "max_prediction_length": 1,
    "batch_size": 64,
    "max_epochs": 20,
    "learning_rate": 0.0005,
    "hidden_size": 32,
    "attention_head_size": 2,
    "dropout": 0.1,
    "hidden_continuous_size": 8,
    "seed": 42,
    "early_stopping_patience": 5,
    "early_stopping_min_delta": 0.0
  },
  "split_config": {
    "train_start": "20100101",
    "train_end": "20221231",
    "val_start": "20230101",
    "val_end": "20241231",
    "test_start": "20250101",
    "test_end": "20251231"
  },
  "param_ranges": {
    "max_encoder_length": [120, 150, 180, 210]
  }
}
```

Regra de validacao por tipo:
- `main_tft_param_sweep` exige `test_type: "ofat"`
- `main_tft_optuna_sweep` exige `test_type: "optuna"`

## 3) Execucao basica

```bash
python -m src.main_tft_param_sweep --asset AAPL --config-json config/sweeps/ofat/SEU_SWEEP.json
```

Comportamento:

1. Treina as variacoes OFAT por fold e seed.
2. Salva `sweep_runs.csv/json`.
3. Gera relatorios agregados (`config_ranking`, `param_impact`, `summary`).
4. Gera artefatos automaticamente (relatorios + plots) via `main_generate_sweep_artifacts`.

## 4) Regerar apenas artefatos (sem treinar)

Use quando os modelos/runs ja existem e voce quer recomputar relatorios/plots:

```bash
python -m src.main_generate_sweep_artifacts --sweep-dir data/models/AAPL/sweeps/SEU_SWEEP
```

### 4.1) Reconstruir previsoes por timestamp para `explicit_configs` (sem retreino)

Necessario para testes estatisticos de comparacao preditiva (ex.: DM/MCS).

```bash
python -m src.main_rebuild_explicit_sweep_predictions \
  --sweep-dir data/models/AAPL/sweeps/SEU_SWEEP_EXPLICIT \
  --overwrite
```

## 5) Merge incremental de testes (`--merge-tests`)

Use para adicionar novos runs ao mesmo sweep sem perder historico:

```bash
python -m src.main_tft_param_sweep --asset AAPL --config-json config/sweeps/ofat/SEU_SWEEP.json --output-subdir SEU_SWEEP --merge-tests
```

### Regras de seguranca do merge

Para evitar inconsistencias, ao usar `--merge-tests`:

1. Apenas estes campos podem mudar:
- `param_ranges`
- `walk_forward.folds`
- `replica_seeds`

2. Restricoes:
- `param_ranges`: valores antigos nao podem ser removidos (somente manter/adicionar).
- `folds`: folds antigos nao podem ser removidos nem alterados (somente manter/adicionar novos folds).
- `replica_seeds`: seeds antigas nao podem ser removidas (somente manter/adicionar).

3. Qualquer outra mudanca de configuracao bloqueia a execucao com erro.

## 5.1) Merge para `explicit_configs` e `optuna` (runner unificado)

No entrypoint unificado (`main_tft_test_pipeline`), `merge_tests` tambem funciona para:

- `test_type: "explicit_configs"`
- `test_type: "optuna"`

Comportamento:

1. Reaproveita runs existentes apenas quando os artefatos obrigatorios existem e estao validos.
2. Valida `metadata/split_metrics` e tenta carregar `model_state.pt` para detectar corrupcao.
3. Se detectar artefato faltando/corrompido, reexecuta somente o run afetado.

Exemplo:

```bash
python -m src.main_tft_test_pipeline --asset AAPL --config-json config/seu_teste.json --merge-tests
```

## 6) Principais artefatos gerados

No diretorio:
- `data/models/{ASSET}/sweeps/{output_subdir}/`

Arquivos principais:

- `analysis_config.json`: configuracao efetiva do sweep
- `sweep_runs.csv`: base principal de runs (coracao da analise de performance)
- `summary.json`: resumo executivo
- `config_ranking.csv`: ranking por configuracao
- `param_impact_detail.csv`: impacto por run
- `param_impact_summary.csv`: impacto agregado por parametro
- `drift_ks_psi_by_fold.csv`: drift por fold
- `drift_ks_psi_overall_summary.json`: resumo global de drift

Estrutura por fold:

- `folds/{fold_name}/sweep_runs.csv`
- `folds/{fold_name}/config_ranking.csv`
- `folds/{fold_name}/param_impact_*.csv`
- `folds/{fold_name}/plots/*.png`
- `folds/{fold_name}/models/{version}/...`

Artefatos adicionais para `test_type: explicit_configs`:

- `explicit_analysis/predictions_long.parquet`
- `explicit_analysis/prediction_rebuild_failures.csv`
- `explicit_analysis/ec_ranking_oos.csv`
- `explicit_analysis/ec_robustness.csv`
- `explicit_analysis/ec_generalization_gap.csv`
- `explicit_analysis/ec_consistency_topk.csv`
- `explicit_analysis/ec_heatmap_test_rmse_config_fold.csv`
- `explicit_analysis/ec_confidence_intervals.csv`
- `explicit_analysis/ec_dm_pairwise.csv`
- `explicit_analysis/ec_mcs_result.csv`
- `explicit_analysis/ec_mcs_trace.csv`
- `explicit_analysis/plots/ec_*.png`

## 7) Leitura rapida dos resultados

1. Parametro com melhor impacto medio:
- veja `param_impact_summary.csv`
- menor `avg_delta_rmse_vs_baseline` e mais estavel

2. Melhor configuracao robusta:
- veja `config_ranking.csv`
- criterio principal: menor `robust_score` (`mean_val_rmse + std_val_rmse`)

3. Estabilidade temporal:
- compare resultados por fold (`folds/*/config_ranking.csv`)
- use `drift_ks_psi_by_fold.csv` para contexto de regime

## 8) Observacoes praticas

1. `sweep_runs.csv` e a base principal para ranking/impacto, mas:
- `all_models_ranked.csv` depende dos artefatos em `models/`
- drift depende de dataset + split (nao so de `sweep_runs.csv`)

2. Se um sweep falhar parcialmente:
- use `--continue-on-error` para seguir
- depois regenere artefatos com `main_generate_sweep_artifacts`

3. Para comparacao justa entre sweeps:
- compare apenas intersecao de folds/seeds/params iguais


## 9) HPO com Optuna (top-k para sweep)

Use quando quiser buscar hiperparametros com estrategia bayesiana e depois
rodar somente os melhores na pipeline de sweep tradicional.

Comando:

```bash
python -m src.main_tft_optuna_sweep --asset AAPL --config-json config/sweeps/optuna/default_tft_optuna_sweep.json
```

Artefatos gerados em:
- `data/models/{ASSET}/optuna/{output_subdir}/...`

Arquivos principais:
- `optuna_summary.json`
- `optuna_best_trial.json`
- `optuna_top_k_configs.json`
- `optuna_trials.csv`
- `optuna_trials.json`
- `optuna_study.db`

Fluxo recomendado:
1. Executar Optuna para obter top-k configuracoes (`optuna_top_k_configs.json`).
2. Levar as configuracoes para um sweep dedicado e gerar relatorios/plots finais.

## 10) Runner unificado por `test_type`

Novo entrypoint:

```bash
python -m src.main_tft_test_pipeline --asset AAPL --config-json config/test_pipeline.default.json
```

Campos obrigatorios:
- comuns: `schema_version`, `test_type`, `training_config`, `split_config`
- `test_type: "ofat"`: exige `param_ranges`
- `test_type: "optuna"`: exige `search_space`, `n_trials`, `top_k`, `study_name`
- `test_type: "explicit_configs"`: exige `explicit_configs` com `training_config` por item

## 11) Purge completo de um sweep (silver + models + refresh + validacao)

Use quando precisar apagar completamente os dados de um sweep (ex.: rerun limpo com mesmo prefixo).

Comando:

```bash
python -m src.main_purge_sweep_data \
  --asset AAPL \
  --sweep-prefix 0_2_4_ \
  --fail-on-quality
```

Regras de seguranca da CLI:
- `--sweep-prefix` e obrigatorio.
- `--sweep-prefix` nao pode ser vazio/whitespace.
- Se o prefixo nao existir no `silver` (coluna `parent_sweep_id`) e nem em `data/models/<ASSET>/sweeps/<prefix>*`, o comando aborta antes de purge/refresh/quality.

O que o pipeline faz:

1. Resolve `run_id` do prefixo em `dim_run`.
2. Remove, em todas as tabelas `silver`, linhas com:
- `parent_sweep_id` iniciando com o prefixo, e/ou
- `run_id` pertencente ao sweep.
3. Remove diretorios de modelos em:
- `data/models/<ASSET>/sweeps/<prefix>*`
4. Executa refresh do gold (`RefreshAnalyticsStoreUseCase`).
5. Executa quality validation (`ValidateAnalyticsQualityUseCase`).
6. Valida residuo zero no silver e ausencia de caminhos remanescentes em models para o sweep purgado.

Codigos de saida:

- `0`: purge + refresh + validacao de residuo concluido.
- `1`: quality gate falhou com `--fail-on-quality`.
- `2`: validacao de residuo zero falhou (ainda ha linhas/caminhos do sweep).
- `3`: sweep prefix nao encontrado (aborta sem executar purge/refresh/quality).

Observacoes:

- O comando nao remove arquivos de configuracao em `config/sweeps/*`.
- Para rerun limpo do mesmo sweep, execute esse purge antes de iniciar o novo treino.
- Logs de progresso foram enriquecidos por etapa para facilitar monitoramento:
  - inicio do comando (paths/asset/prefixo),
  - discovery,
  - purge silver,
  - purge models,
  - refresh,
  - quality,
  - validacao final e tempo total.
