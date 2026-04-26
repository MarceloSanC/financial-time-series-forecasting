---
title: Plot Interpretation Guide
scope: Criterios pass/fail e fonte de validacao para os 8 graficos canonicos da analise (heatmap por horizonte, boxplot por fold/seed, DM matrix, calibration curve, MPIW vs PICP, OOS timeseries, importancia global, contribuicoes locais).
update_when:
  - novo grafico canonico for adicionado a analise
  - criterio de aceite de grafico existente mudar
  - tabela gold de validacao for renomeada
canonical_for: [plot_interpretation, plot_acceptance_criteria, canonical_plots]
---

# Plot Interpretation Guide

Objetivo: padronizar leitura, criterio de aceite e fonte de validacao para cada
grafico usado em analise tecnica e defesa academica.

## 1) Heatmap metrics by horizon
- Mede: desempenho relativo por horizonte (`rmse`, `mae`, `da`, `mean_pinball`).
- Esperado: padrao consistente por horizonte com `n_oos > 0`.
- Alerta: celulas vazias, ranking instavel por falta de amostra.
- Validacao: `gold_prediction_metrics_by_config.parquet`.

## 2) Boxplot error by fold/seed
- Mede: robustez da distribuicao de erro OOS por replicacao.
- Esperado: variacao real entre folds/seeds, sem colapso em linha unica.
- Alerta: ausencia de variabilidade ou outliers sem rastreabilidade.
- Validacao: `gold_prediction_robustness_by_horizon.parquet`.

## 3) DM p-value matrix
- Mede: significancia estatistica pareada entre configuracoes por horizonte.
- Esperado: matriz quadrada com `pvalue_adj_holm` consistente.
- Alerta: comparacoes sem intersecao temporal ou sem ajuste multiplo.
- Validacao: `gold_dm_pairwise_results.parquet`.

## 4) Calibration curve
- Mede: cobertura observada vs nominal.
- Esperado: proximidade com diagonal de calibracao.
- Alerta: under-coverage sistematica (`coverage_error << 0`).
- Validacao: `gold_prediction_calibration.parquet`.

## 5) Interval width vs coverage
- Mede: trade-off entre sharpness (`MPIW`) e cobertura (`PICP`).
- Esperado: cobertura adequada sem explosao de largura.
- Alerta: `MPIW` alto com ganho pequeno de cobertura, ou `PICP` colapsado.
- Validacao: `gold_prediction_calibration.parquet`.

## 6) OOS time series examples
- Mede: aderencia temporal (`y_true`, `p50`, banda `p10-p90`) em janelas reais.
- Esperado: erro e incerteza coerentes com regime observado.
- Alerta: banda invertida, atrasos sistematicos, underreaction/overreaction extrema.
- Validacao: `fact_oos_predictions` + `gold_prediction_metrics_by_run_split_horizon`.

## 7) Global feature importance
- Mede: impacto medio global por feature no escopo analisado.
- Esperado: top-k plausivel e estavel entre replicacoes.
- Alerta: importancias quase identicas por artefato de agregacao.
- Validacao: `gold_feature_impact_by_horizon.parquet`.

## 8) Local feature contributions
- Mede: contribuicoes locais por caso (`timestamp`, `horizon`).
- Esperado: sinais e magnitudes rastreaveis com top-k coerente.
- Alerta: vazio no escopo, sinais inconsistentes, baixa estabilidade.
- Validacao: `fact_feature_contrib_local` + `gold_feature_contrib_local_summary.parquet`.

## Global Pass/Fail Gates
- `python -m src.main_refresh_analytics_store --fail-on-quality` sem falhas.
- Graficos gerados para o mesmo escopo (asset/coorte/split/horizon).
- Tabelas de suporte existentes e nao vazias para cada visualizacao.
