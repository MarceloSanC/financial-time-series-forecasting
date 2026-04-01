# Predictions and Metrics Checklist (Inference Output - Y)

Objetivo: definir, de forma canonica, os dados de saida do modelo (Y) necessarios para analise interpretavel, estimativa estatistica de retorno esperado e comparacao robusta entre modelos sem retraining.

## Escopo

Este documento cobre:
- saidas de inferencia/predicao do modelo (dados primarios)
- estrutura para metricas e testes estatisticos (dados derivados)
- suporte multi-horizonte (h+1, h+7, h+30)
- explicabilidade da previsao (global e local)

Nao cobre:
- features de entrada (X)
- setup/metadados de treino em detalhe (ver `ANALYTICS_STORE_CHECKLIST.md`)

---

## 0) Resultado Esperado Em Producao

- [x] Para cada inferencia, gerar retorno previsto para `h+1`, `h+7`, `h+30` (quando habilitados no run).
- [x] Para cada horizonte, salvar previsao probabilistica minima (`p10`, `p50`, `p90`).
- [ ] Fornecer grau de certeza calibrado (nao apenas score unico), baseado em intervalo + calibracao historica.
- [x] Fornecer explicabilidade global por feature (importancia media por periodo/run).
- [x] Fornecer explicabilidade local por inferencia (`timestamp`) com contribuicao por feature.

---

## 1) Predicoes Primarias (dados brutos do modelo)

### 1.0 Politica de horizontes (multi-horizonte)
- [x] Habilitar e padronizar horizontes de interesse: `h+1`, `h+7`, `h+30`.
- [x] Permitir configuracao explicita dos horizontes por experimento.
- [x] Registrar horizontes efetivamente usados em cada run.

### 1.1 Chaves de identificacao por linha de predicao
- [x] `run_id`
- [x] `model_version`
- [x] `asset`
- [x] `feature_set_name`
- [x] `fold`
- [x] `seed`
- [x] `split` (`train|val|test|inference`)
- [x] `config_id` (ou assinatura canonica da config)

### 1.2 Chaves temporais
- [x] `timestamp` (instante da observacao/entrada)
- [x] `horizon` (obrigatorio para multi-horizonte)
- [x] `target_timestamp` (timestamp alvo previsto)

### 1.3 Valores alvo/predicao
- [x] `y_true` (quando existir verdade-terreno)
- [x] `y_pred_point` (predicao pontual)
- [x] `y_pred_q10` (quando quantilico)
- [x] `y_pred_q50` (quando quantilico)
- [x] `y_pred_q90` (quando quantilico)
- [x] `quantile_levels` efetivamente usados no run

### 1.4 Integridade minima
- [x] Garantir 1 linha unica por (`run_id`,`split`,`horizon`,`timestamp`,`target_timestamp`).
- [x] Garantir `target_timestamp` monotono por (`run_id`,`split`,`horizon`).
- [x] Garantir tipos numericos consistentes (`float64`) em `y_true/y_pred*`.
- [x] Garantir cobertura completa para os horizontes obrigatorios (`1,7,30`) quando habilitados.

---

## 2) Derivados Minimos por Linha (timestamp-level)

- [x] `error = y_pred_point - y_true`
- [x] `abs_error = abs(error)`
- [x] `sq_error = error^2`
- [x] `pred_interval_low` (usar `quantile_p10`)
- [x] `pred_interval_high` (usar `quantile_p90`)
- [x] `pred_interval_width = pred_interval_high - pred_interval_low` (persistido por linha quando necessario; obrigatorio no gold)
- [x] `prob_up = P(y>0)` derivado dos quantis/distribuicao (ou aproximacao documentada)

Observacao: manter como principio P0 a persistencia dos dados primarios; derivados pesados podem ser materializados em gold.

---

## 3) Catalogo de Metricas por Nivel de Agregacao

### 3.1 Basicas por split/fold/seed/config
- [x] RMSE
- [x] MAE
- [x] MAPE (quando aplicavel)
- [x] sMAPE (quando aplicavel)
- [x] DA (Directional Accuracy)
- [x] Bias medio (`mean(y_pred - y_true)`)
- [x] Salvar metricas basicas por `horizon` (alem do agregado).

### 3.2 Probabilisticas (quantilicas)
- [x] Pinball loss por quantil (`q10`, `q50`, `q90`, ...)
- [x] Mean pinball loss
- [x] PICP (Prediction Interval Coverage Probability)
- [x] MPIW (Mean Prediction Interval Width)
- [x] Coverage error (`PICP - cobertura_nominal`)
- [x] Salvar metricas probabilisticas por `horizon`.

### 3.3 Grau de certeza (operacional)
- [x] `interval_width` medio por horizonte (proxy primaria de incerteza)
- [x] `prob_up` / `prob_down` por horizonte
- [x] `confidence` calibrada (derivada de cobertura historica + largura de intervalo)
- [x] Evitar score unico sem calibracao documentada

### 3.4 Risco previsto
- [x] VaR por alfa (`VaR_10`, `VaR_05`, ...)
- [x] ES (Expected Shortfall) aproximado
- [x] Expected move
- [x] Downside risk
- [ ] [P2] Risk-reward proxy

Definicoes matematicas (implementadas em `gold_prediction_risk`):
- `expected_move`: media de `abs(y_pred)` por (`run_id`,`split`,`horizon`).
- `downside_risk`: media de `max(-y_pred, 0)` por (`run_id`,`split`,`horizon`).
- `VaR_10`: media de `quantile_p10` por (`run_id`,`split`,`horizon`).
- `ES_10` aproximado: media de `1.125*q10 - 0.125*q50` (com clamp `ES_10 <= VaR_10`) por (`run_id`,`split`,`horizon`).
- `confidence_calibrated`: `(1 - |coverage_error|/coverage_nominal)_clip * 1/(1+pred_interval_width)` por (`run_id`,`split`,`horizon`).

### 3.5 Robustez e estabilidade
- [x] media por config
- [x] desvio padrao por config
- [x] IQR por config
- [x] IC95 por metrica/config
- [x] gap de generalizacao (`test - val`) por metrica
- [x] consistencia top-k por fold/seed
- [x] Repetir analises de robustez por `horizon` (h+1/h+7/h+30)

### 3.6 Comparacao estatistica entre modelos (OOS alinhado)
- [x] DM test (Diebold-Mariano)
- [x] MCS (Model Confidence Set)
- [x] win-rate pareado por timestamp

### 3.7 Explicabilidade de features (ligada a Y)
- [x] Importancia global por feature (periodo/run)
- [x] Contribuicao local por inferencia (`run_id`,`timestamp`,`horizon`,`feature`,`contribution`)
- [x] Estabilidade da explicacao local (top-k consistency entre seeds/janelas)

---

## 4) Estrategia de Tabelas (Reusar vs Criar)

### 4.1 Silver (P0: reusar o que ja existe)
- [x] Reusar `fact_oos_predictions` para predicoes, quantis, erros e chaves temporais.
- [x] Reusar `fact_config` para guardar `evaluation_horizons_json` e configuracao probabilistica.
- [x] Reusar `fact_model_artifacts` para importancia global (feature importance).
- [x] Criar `fact_inference_predictions` para unificar inferencia operacional com OOS em analytics (separado de `data/processed/inference_tft`).

### 4.2 Silver (P1: novos fatos apenas se necessario)
- [x] `fact_feature_contrib_local` (explicabilidade local por inferencia).
- [ ] `fact_prediction_distribution` (opcional; somente se formato de saida probabilistica exigir mais que q10/q50/q90).

### 4.3 Gold
- [x] `gold_prediction_metrics_by_run_split_horizon`
- [x] `gold_prediction_metrics_by_config`
- [x] `gold_prediction_metrics_by_horizon`
- [x] `gold_prediction_calibration`
- [x] `gold_prediction_risk`
- [x] `gold_prediction_generalization_gap`
- [x] `gold_prediction_robustness_by_horizon`
- [x] `gold_dm_pairwise_results`
- [x] `gold_mcs_results`
- [x] `gold_win_rate_pairwise_results`
- [x] `gold_paired_oos_intersection_by_horizon`
- [x] `gold_model_decision_final`
- [x] `gold_quality_run_sweep_summary`
- [x] `gold_feature_impact_by_horizon` (global)
- [x] `gold_feature_contrib_local_summary` (local)

---

## 5) Regras de Alinhamento OOS (criticas)

- [x] Comparacoes entre modelos devem usar exatamente o mesmo conjunto de `target_timestamp`.
- [x] Nao comparar metricas entre modelos com cobertura temporal diferente sem intersecao explicita.
- [x] Para DM/MCS, armazenar e usar perdas por timestamp no mesmo eixo temporal.
- [x] Executar alinhamento separadamente por `horizon` antes de agregar resultados.
- [x] Enforce tecnico antes de DM/MCS/win-rate: `inner join` por `asset+split+horizon+target_timestamp` (coorte comparavel).
- [x] Persistir diagnostico de alinhamento por coorte: `n_common`, `n_union`, `coverage_ratio`, `aligned_exact`.
- [x] Gate de comparacao pareada: falhar quando `n_common==0` ou cobertura abaixo do limiar definido.

---

## 6) Qualidade e Auditoria

- [x] Validar ausencia de duplicatas na chave temporal por run.
- [x] Validar nulos indevidos em `y_pred` e em `y_true` (quando split supervisionado).
- [x] Validar ranges impossiveis (ex.: `pred_interval_width < 0`).
- [x] Validar cardinalidade esperada por (`config x fold x seed x split`).
- [x] Validar tipos numericos nas colunas de predicao/erro.
- [x] Validar cobertura de horizontes esperados por run/split.
- [x] Validar ordem dos quantis `q10 <= q50 <= q90` quando disponiveis.
- [x] Validar `confidence_calibrated` por horizonte no gold (`gold_prediction_metrics_by_run_split_horizon`).
- [x] Validar contrato `n_oos` em `gold_prediction_metrics_by_config` (presenca, positividade e consistencia com `sum(n_samples)` do run-level).
- [x] Gerar relatorio automatico de qualidade para predicoes.

---

## 7) Definition of Done

- [x] Todas as predicoes primarias (Y) estao persistidas com chaves completas.
- [x] Grau de certeza e calibracao estao disponiveis por horizonte.
- [x] Analise de importancia global por feature esta disponivel por horizonte/split.
- [x] Contribuicao local por inferencia esta disponivel (ou explicitamente fora de escopo da release).
- [x] Todas as metricas de comparacao entre configs/feature sets sao reproduziveis sem retrain.
- [x] DM/MCS podem ser executados apenas com dados persistidos.

---

## 8) Prioridade para Rigor Academico (Proposta)

### P0 (obrigatorio para defesa robusta)
- [x] Metricas OOS basicas por split/fold/seed/config: RMSE, MAE, DA e Bias.
- [x] Calibracao probabilistica minima: Pinball por quantil, PICP e MPIW.
- [x] Comparacao pareada com alinhamento temporal estrito por `target_timestamp`:
- [x] DM test (com correcao small-sample).
- [x] MCS para selecao de conjunto de melhores modelos.
- [x] Robustez entre replicas:
- [x] media/desvio por config.
- [x] IC95 por metrica/config.
- [x] consistencia top-k por fold/seed.

### P1 (fortemente recomendado)
- [x] Analise por horizonte (h+1/h+7/h+30) para todas as metricas de P0.
- [x] Controle de comparacoes multiplas/data snooping (Holm-Bonferroni sobre DM pairwise).
- [x] Gap de generalizacao (`test - val`) por metrica e por horizonte.
- [ ] Explicabilidade local com validacao de estabilidade.

### P2 (complementar)
- [ ] Testes condicionais avancados (ex.: Giacomini-White, Clark-West quando aplicavel).
- [ ] Metricas de risco avancadas (VaR/ES completos com backtesting formal).
- [ ] Interpretabilidade avancada (attention export estruturado, SHAP/permutation em lote).

---

## 9) Outputs Obrigatorios De Analise (Graficos, Tabelas, Relatorios)

Objetivo: padronizar os artefatos que devem ser gerados para comparacao completa entre modelos,
com foco em rigor estatistico, reprodutibilidade e defesa academica.

### 9.1 Tabelas essenciais (P0)
- [x] `tbl_leaderboard_by_horizon`: RMSE, MAE, DA, Pinball, PICP, MPIW, `n_oos` por (`config`,`feature_set`,`horizon`) (materializado em `gold_prediction_metrics_by_config.parquet`).
  Definicao operacional de `n_oos`: soma de `n_samples` do nivel run (`gold_prediction_metrics_by_run_split_horizon`) para o mesmo (`asset`,`feature_set_name`,`config_signature`,`split`,`horizon`).
  Contrato de qualidade ativo: check `gold_metrics_by_config_n_oos_contract` valida coluna obrigatoria `n_oos`, `n_oos > 0` e consistencia com run-level (`sum(n_samples)`).
- [x] `tbl_paired_tests_by_horizon`: DM statistic, p-value, p-value ajustado (Holm), win-rate pareado e IC95 da diferenca de erro (materializado em `gold_quality_statistics_report.parquet`).
- [x] `tbl_final_decision`: melhor modelo por horizonte com regra explicita de selecao (metrica primaria + criterio estatistico) (materializado em `gold_model_decision_final.parquet`).
- [x] `tbl_robustness_fold_seed`: media, desvio, mediana e IQR por (`config`,`feature_set`,`horizon`).
- [x] `tbl_risk_summary`: expected_move, downside_risk, VaR10, ES por (`config`,`feature_set`,`horizon`) (materializado em `gold_prediction_risk.parquet`).

### 9.2 Graficos essenciais (P0)
- [x] `fig_heatmap_metrics_by_horizon`: heatmap modelo x horizonte para RMSE/MAE/DA/Pinball.
- [x] `fig_boxplot_error_by_fold_seed`: distribuicao de erro OOS por fold/seed para robustez.
- [x] `fig_dm_pvalue_matrix`: matriz de comparacao pareada com p-values ajustados por horizonte.
- [x] `fig_calibration_curve`: cobertura observada vs cobertura nominal (por horizonte).
- [x] `fig_interval_width_vs_coverage`: MPIW vs PICP para avaliar calibracao x sharpness.
- [x] `fig_oos_timeseries_examples`: `y_true` vs `p50` com banda `p10-p90` em janelas representativas.

### 9.3 Interpretabilidade visual (P1)
- [x] `fig_feature_importance_global`: top-k features por horizonte (agregado por run/config).
- [x] `fig_feature_contrib_local_cases`: contribuicao local para casos de maior erro e maior acerto.
- [x] `tbl_feature_explanation_stability`: estabilidade de top-k local entre seeds/janelas (materializado em `gold_feature_contrib_local_summary.parquet`).

### 9.4 Relatorios essenciais (P0)
- [x] `report_quality_and_completeness`: completude, duplicatas, alinhamento temporal, cobertura de horizontes e quantis (materializado em `gold_oos_quality_report.parquet`).
- [x] `report_statistical_comparison`: DM/MCS/win-rate/IC95 por horizonte com conclusao reproduzivel (materializado em `gold_quality_statistics_report.parquet`).
- [x] `report_model_selection`: ranking final e trade-offs (acuracia, calibracao, risco, robustez) (materializado em `gold_model_decision_final.parquet`).
- [x] `report_production_inference_monitoring`: qualidade de inferencias de producao (quantis validos, cobertura recente, drift de erro) (materializado em `gold_quality_run_sweep_summary.parquet`).

### 9.5 Escopo por fluxo (implementacao)
- [ ] Fluxo de testes/sweeps deve gerar todos os artefatos de 9.1, 9.2 e 9.4 automaticamente ao final da execucao.
- [ ] Fluxo de inferencia em producao deve gerar ao menos `report_production_inference_monitoring` e tabelas de qualidade/calibracao rolling.
- [ ] Todos os artefatos devem ser rastreaveis por `run_id`, `model_version`, `feature_set_name`, `config_signature` e `horizon`.

### 9.6 Definition of Done dos artefatos (P0)
- [ ] Comparacao final entre modelos pode ser feita apenas com dados persistidos (sem retrain).
- [ ] Todas as tabelas usam intersecao temporal explicita por `target_timestamp` nas comparacoes pareadas.
- [ ] Relatorio final apresenta vencedores por horizonte com evidencia estatistica (DM/MCS/win-rate/IC95).
- [ ] Relatorio final apresenta incerteza calibrada (PICP/MPIW/coverage error) e risco previsto (VaR/ES/expected_move).


---

## 10) Roteiro Pratico De Analise Final (Academico)

Objetivo: transformar os artefatos gerados em conclusao reproduzivel sobre melhor modelo por horizonte.

### 10.1 Execucao padrao
1. Rodar refresh + qualidade + graficos:
`python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL`
2. Confirmar `failed_checks=[]` no log.
3. Confirmar existencia dos artefatos em `data/analytics/gold` e `data/analytics/reports/prediction_analysis_plots/asset=AAPL`.

### 10.1.1 Execucao com escopo de analise (recomendado para defesa)
1. Escopo por candidatos congelados (mais reproduzivel):
`python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL --plots-scope-csv data/analytics/selection/frozen_candidates_0_2_2.csv`
2. Escopo por prefixo de sweep (suporte operacional):
`python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL --plots-scope-sweep-prefixes 0_2_2_`
3. Escopo combinado (intersecao):
`python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL --plots-scope-csv data/analytics/selection/frozen_candidates_0_2_2.csv --plots-scope-sweep-prefixes 0_2_2_`
4. O escopo afeta apenas a geracao dos graficos de analise (`--plots-*`); o refresh gold global continua sendo recalculado normalmente.

### 10.2 Ordem de leitura recomendada
1. Qualidade e completude:
`gold_oos_quality_report.parquet`
Validar: duplicatas=0, cobertura de horizontes esperados, quantis ordenados (`p10<=p50<=p90`), alinhamento temporal pareado habilitado.
2. Leaderboard por horizonte:
`gold_prediction_metrics_by_config.parquet`
Validar: RMSE/MAE/DA/Pinball/PICP/MPIW por `horizon` com `n_oos` suficiente e sem outliers de cardinalidade.
3. Comparacao estatistica:
`gold_quality_statistics_report.parquet`, `gold_dm_pairwise_results.parquet`, `gold_mcs_results.parquet`, `gold_win_rate_pairwise_results.parquet`
Validar: DM com ajuste Holm, MCS por horizonte, win-rate e IC95 consistentes.
4. Decisao final:
`gold_model_decision_final.parquet`
Validar: vencedor por horizonte com criterio explicito (acuracia + significancia estatistica + robustez).
5. Risco e calibracao:
`gold_prediction_risk.parquet`, `gold_prediction_calibration.parquet`
Validar: trade-off entre cobertura (PICP), largura (MPIW), VaR/ES e downside risk.
6. Interpretabilidade:
`gold_feature_impact_by_horizon.parquet`, `gold_feature_contrib_local_summary.parquet`
Validar: coerencia entre importancia global e casos locais (maior erro/acerto), estabilidade de top-k.

### 10.3 Leitura dos 8 graficos (9.2/9.3)
1. `fig_heatmap_metrics_by_horizon`:
Usar para triagem inicial de melhores configs por horizonte.
2. `fig_boxplot_error_by_fold_seed`:
Usar para robustez; preferir menor dispersao para desempenho equivalente.
3. `fig_dm_pvalue_matrix`:
Usar para filtrar diferencas nao significativas entre candidatos.
4. `fig_calibration_curve`:
Usar para verificar calibracao de incerteza (pontos proximos da diagonal).
5. `fig_interval_width_vs_coverage`:
Usar para escolher equilibrio calibracao vs sharpness (cobertura alta com intervalos menores).
6. `fig_oos_timeseries_examples`:
Usar para inspeção qualitativa de regime e estabilidade temporal da previsao.
7. `fig_feature_importance_global`:
Usar para contribuição media por feature e horizonte.
8. `fig_feature_contrib_local_cases`:
Usar para explicacao de previsoes especificas (maior erro e maior acerto).

### 10.4 Regra objetiva de decisao (recomendada)
1. Selecionar top-k por `horizon` via RMSE/MAE.
2. Remover modelos sem suporte estatistico (DM Holm p<0.05 contra benchmark/top).
3. Entre empatados, preferir melhor calibracao (menor `|coverage_error|`, menor MPIW).
4. Aplicar desempate por risco (menor downside/VaR/ES para mesma acuracia).
5. Registrar vencedor e runner-up por horizonte com justificativa textual curta e referencias das tabelas.

### 10.5 Evidencias minimas para defesa academica
- Tabela final por horizonte com metricas de erro + calibracao + risco + robustez.
- Resultado de DM/MCS/win-rate/IC95 por horizonte usando intersecao temporal explicita.
- Graficos 9.2/9.3 anexados ao relatorio com interpretacao objetiva.
- Decisao final rastreavel por `run_id`, `model_version`, `feature_set_name`, `config_signature`, `horizon`.

## 11) Checklist De Aceite Dos Graficos (Pass/Fail)

Objetivo: definir gates objetivos para considerar os artefatos visuais prontos para comparacao estatistica e defesa academica.

### 11.1 fig_heatmap_metrics_by_horizon
- [ ] Exibe todos os horizontes exigidos no experimento (`h+1`,`h+7`,`h+30`, quando aplicavel).
- [ ] Labels legiveis (`feature_set + hash curto`).
- [ ] Valores conferem com `gold_prediction_metrics_by_config.parquet`.
- [ ] `n_oos` por grupo > 0 e consistente com a base OOS.
- [ ] Nao mistura universos fora do escopo selecionado (sweep/coorte alvo).

### 11.2 fig_boxplot_error_by_fold_seed
- [ ] Cada boxplot possui multiplas observacoes (nao degenera em linha unica).
- [ ] Fonte contem variacao real por `fold` e/ou `seed`.
- [ ] Mediana/dispersao conferem com `gold_prediction_robustness_by_horizon.parquet`.
- [ ] Outliers sao rastreaveis por `run_id`.

### 11.3 fig_dm_pvalue_matrix
- [ ] Matriz quadrada por horizonte com alinhamento por `target_timestamp`.
- [ ] Labels legiveis e consistentes com a coorte filtrada.
- [ ] Nao vazio e com quantidade minima de pares validos.
- [ ] p-values conferem com `gold_dm_pairwise_results.parquet`.
- [ ] Interpretacao estatistica usa ajuste de multiplas comparacoes (Holm/FDR).

### 11.4 fig_calibration_curve
- [ ] Para cada horizonte, ha pontos com `nominal_coverage` esperado (ex.: 0.8).
- [ ] `PICP` em faixa valida [0,1] sem colapso sistematico em zero.
- [ ] Distancia da diagonal ideal esta dentro da tolerancia definida.
- [ ] Coerente com `gold_prediction_calibration.parquet`.

### 11.5 fig_interval_width_vs_coverage
- [ ] `MPIW > 0` para modelos quantilicos validos.
- [ ] `PICP` nao colapsado em zero para todos os modelos.
- [ ] Relacao cobertura x largura e interpretavel (trade-off real).
- [ ] Coerente com `gold_prediction_calibration.parquet`.

### 11.6 fig_oos_timeseries_examples
- [ ] Exibe `y_true`, `p50` e banda `p10-p90` (quando quantilico).
- [ ] Janela temporal legivel e representativa da coorte.
- [ ] Caso rastreavel por `run_id`/`model_version`.
- [ ] Permite avaliar under/over-reaction em regimes de alta variabilidade.

### 11.7 fig_feature_importance_global
- [ ] Metodo de importancia documentado e reprodutivel.
- [ ] Escala/sinal interpretaveis.
- [ ] Nao colapsa artificialmente em valores quase identicos por artefato de agregacao.
- [ ] Coerente com `gold_feature_impact_by_horizon.parquet`.

### 11.8 fig_feature_contrib_local_cases
- [ ] Nao vazio para o escopo analisado.
- [ ] Casos mostram top contribuicoes com sinal (+/-).
- [ ] Linhas rastreaveis por `timestamp`,`horizon`,`model_version`.
- [ ] Coerente com `fact_feature_contrib_local` e `gold_feature_contrib_local_summary.parquet`.

### 11.9 Gates finais (obrigatorios)
- [ ] `python -m src.main_refresh_analytics_store --fail-on-quality` retorna `failed_checks=[]`.
- [ ] Os 8 graficos foram gerados para o mesmo escopo (`--plots-scope-*` quando aplicavel).
- [ ] Tabelas-chave existem e nao estao vazias:
  - [ ] `gold_prediction_metrics_by_config.parquet`
  - [ ] `gold_quality_statistics_report.parquet`
  - [ ] `gold_model_decision_final.parquet`
  - [ ] `gold_prediction_risk.parquet`
  - [ ] `gold_feature_contrib_local_summary.parquet`
- [ ] Comparacoes estatisticas (DM/MCS/win-rate) usam intersecao temporal explicita.
- [ ] Decisao final por horizonte esta documentada com erro, calibracao, risco e robustez.
