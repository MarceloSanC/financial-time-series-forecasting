# Sweeps and Selection

## Proposito
Documentar as familias de sweeps (Optuna e explicit-config), a governanca de
escopo entre rodadas e a politica atual de selecao. Nao cobre comandos CLI
(ver `06_runbooks/RUN_SWEEPS.md`) nem o protocolo estatistico em si (ver
`04_evaluation/STATISTICAL_TESTS.md`).

> **Aviso importante:** a politica de selecao por desempenho OOS comparando
> conjuntos de features foi **abandonada** em 2026-04-23. Ver
> `00_overview/STRATEGIC_DIRECTION.md` §4 para o pivo metodologico atual
> (candidato unico all-features + analise de contribuicao).

## Conceitos-chave
- **Optuna sweep:** busca de hiperparametros via Bayesian optimization sobre
  `val_loss` (TPE sampler). Usado para Round 0 (exploratoria).
- **Explicit-config sweep:** rodada com lista pre-definida de configuracoes
  (top-k da Optuna), tipicamente para confirmar resultados ou variar seeds/folds.
- **`parent_sweep_id`:** identificador da rodada (ex.: `0_2_3_explicit_*`).
  Toda decisao estatistica deve declarar e filtrar por este campo.
- **Frozen set:** lista canonica e imutavel de candidatos selecionados antes
  da analise final. Persistido em CSV versionado.
- **Round 0 vs Round 1:** convencao de prefixo. `0_X_X` = exploratoria
  (HPO, sensibilidade); `1_X_X` = confirmatoria (candidato unico vs baselines).
- **Coorte (`scope_mode=cohort_decision`):** subset de runs comparaveis
  (mesmo sweep, mesmo split, mesmo horizonte). Comparacoes pareadas exigem
  intersecao temporal exata por `target_timestamp` dentro da coorte.

## Decisoes e escolhas
- **Round 0 e exploratoria, nao evidencia primaria.** *Why:* selecao de
  features por desempenho OOS e p-hacking mascarado. Round 0 sweeps servem
  apenas para identificar vizinhanca de hiperparametros. Ver
  `STRATEGIC_DIRECTION.md` §4.
- **Round 1 confirmatoria compara candidato unico vs baselines, nao
  feature sets entre si.** *Why:* alinha o teste com o claim defendido no TCC
  (calibracao probabilistica + contribuicao de familias).
- **Pre-registro versionado obrigatorio antes de Round 1.** *Why:* impede
  data snooping na escolha do candidato e da metrica primaria.
  Ver `07_reports/phase-gates/A_code_audit.md`.
- **Objetivo Optuna padrao: `robust_score = mean_val_rmse + lambda * std_val`.**
  *Why:* favorece configs com bom desempenho medio E baixa variancia entre
  seeds; reduz risco de escolher config instavel apenas por sorte.
- **Comparacoes estatisticas (DM/MCS/win-rate) restritas a coortes
  explicitas via `ScopeSpec`.** *Why:* misturar runs de sweeps diferentes
  invalida a estatistica; o ScopeSpec impede mistura silenciosa.

## Saidas tipicas por sweep
- `data/models/{asset}/{model_version}/` — checkpoint + config + metadata
- `data/analytics/silver/dim_run/asset={asset}/` — registro do run
- `data/analytics/silver/fact_oos_predictions/asset={asset}/...` — predicoes OOS
- `data/analytics/gold/gold_dm_pairwise_results.parquet` — DM por coorte
- `data/analytics/gold/gold_mcs_results.parquet` — MCS por coorte
- `data/analytics/selection/frozen_candidates_{prefixo}.csv` — frozen set

## Status atual (2026-04-24)
- Round 0 (`0_X_X`): concluida, ~6.900 runs em 12 feature sets.
  Reclassificada como exploratoria; nao gera evidencia primaria.
- Round 1 (`1_X_X`): nao iniciada. Bloqueada pelos gates da Fase A
  (ver `07_reports/phase-gates/A_code_audit.md`).
- Sweeps pre-`f7901a4` (commit 2026-04-03): tem quantis degenerados em
  85-98% dos runs por bug de fallback ja corrigido. RMSE/MAE permanecem
  validos; metricas probabilisticas invalidas. Ver `evidence_log.md` 2026-04-24.

## Fonte da verdade (codigo)
- `src/use_cases/run_tft_optuna_search_use_case.py` — Optuna search
- `src/domain/services/tft_sweep_experiment_builder.py` — geracao de configs
- `src/domain/services/explicit_config_sweep_analysis_service.py` — analise
  pos-sweep
- `src/domain/services/scope_spec.py` — governanca de coorte
- `config/sweeps/{optuna, explicit, ofat}/` — configs versionadas

## Documentos relacionados
- `00_overview/STRATEGIC_DIRECTION.md` §4 — pivo metodologico atual
- `00_overview/STRATEGIC_DIRECTION.md` §5 — roadmap das fases A-D
- `04_evaluation/STATISTICAL_TESTS.md` — DM/MCS/Holm e regras de alinhamento
- `06_runbooks/RUN_SWEEPS.md` — comandos CLI de execucao
- `07_reports/living-paper/evidence_log.md` (2026-04-24) — analise dos sweeps
  exploratorios e o que e/nao e valido concluir