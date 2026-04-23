# Predictions and Metrics Checklist (Inference Output - Y)

Objetivo: definir, de forma canonica, todos os dados de saida do modelo (Y) que precisam ser persistidos para habilitar analises futuras sem retraining.

## Escopo

Este documento cobre somente:
- saidas de inferencia/predicao do modelo (dados primarios)
- estrutura minima para calculo de metricas (dados derivados)
- suporte a previsao multi-horizonte

Nao cobre:
- features de entrada (X)
- metadados de treino/config (Setup), que estao em `ANALYTICS_STORE_CHECKLIST.md`

---

## 1) Predicoes Primarias (dados brutos do modelo)

### 1.0 Politica de horizontes (multi-horizonte)
- [ ] Habilitar e padronizar horizontes: `h+1`, `h+2`, `h+7`, `h+15`, `h+30`.
- [ ] Permitir configuracao explicita dos horizontes por experimento.
- [ ] Registrar horizontes efetivamente usados em cada run.

### 1.1 Chaves de identificacao por linha de predicao
- [ ] `run_id`
- [ ] `model_version`
- [ ] `asset`
- [ ] `feature_set_name`
- [ ] `fold`
- [ ] `seed`
- [ ] `split` (`val|test|inference`)
- [ ] `config_id` (ou assinatura canonica da config)

### 1.2 Chaves temporais
- [ ] `timestamp` (instante da observacao/entrada)
- [ ] `horizon` (obrigatorio para multi-horizonte)
- [ ] `target_timestamp` (timestamp alvo previsto)

### 1.3 Valores alvo/predicao
- [ ] `y_true` (quando existir verdade-terreno)
- [ ] `y_pred_point` (predicao pontual)
- [ ] `y_pred_q10` (quando quantilico)
- [ ] `y_pred_q50` (quando quantilico)
- [ ] `y_pred_q90` (quando quantilico)
- [ ] `quantile_levels` efetivamente usados no run

### 1.4 Integridade minima
- [ ] Garantir 1 linha unica por (`run_id`,`split`,`horizon`,`timestamp`)
- [ ] Garantir `target_timestamp` monotono por (`run_id`,`split`,`horizon`)
- [ ] Garantir tipos numericos consistentes (`float64`) em `y_true/y_pred*`
- [ ] Garantir cobertura completa para os horizontes obrigatorios (`1,2,7,15,30`) quando habilitados.

---

## 2) Derivados Minimos por Linha (timestamp-level)

- [ ] `error = y_pred_point - y_true`
- [ ] `abs_error = abs(error)`
- [ ] `sq_error = error^2`
- [ ] `pred_interval_low` (ex.: q10)
- [ ] `pred_interval_high` (ex.: q90)
- [ ] `pred_interval_width = pred_interval_high - pred_interval_low`

Observacao: estes campos sao derivados, mas devem ser persistidos para acelerar consultas e manter reproducibilidade de relatorios.

---

## 3) Catalogo de Metricas por Nivel de Agregacao

## 3.1 Basicas por split/fold/seed/config
- [ ] RMSE
- [ ] MAE
- [ ] MAPE (quando aplicavel)
- [ ] sMAPE (quando aplicavel)
- [ ] DA (Directional Accuracy)
- [ ] Bias medio (`mean(y_pred - y_true)`)
- [ ] Calcular e salvar todas as metricas basicas por `horizon` (alem do agregado).

## 3.2 Probabilisticas (quantilicas)
- [ ] Pinball loss por quantil (`q10`, `q50`, `q90`, ...)
- [ ] Mean pinball loss
- [ ] PICP (Prediction Interval Coverage Probability)
- [ ] MPIW (Mean Prediction Interval Width)
- [ ] Coverage error (`PICP - cobertura_nominal`)
- [ ] Calcular e salvar metricas probabilisticas por `horizon`.

## 3.3 Sinal de decisao
- [ ] `prob_up` / `prob_down` (quando suportado pelo output quantilico)
- [ ] `confidence_score`
- [ ] `no_trade_rate` (por threshold de incerteza)
- [ ] DA em zona de trade (`DA_on_trade_zone`)

## 3.4 Risco previsto
- [ ] VaR por alfa (`VaR_10`, `VaR_05`, ...)
- [ ] ES (Expected Shortfall) aproximado
- [ ] Expected move
- [ ] Downside risk
- [ ] Risk-reward proxy

## 3.5 Robustez e estabilidade
- [ ] media por config
- [ ] desvio padrao por config
- [ ] IQR por config
- [ ] IC95 por metrica/config
- [ ] gap de generalizacao (`test - val`) por metrica
- [ ] consistencia top-k por fold/seed
- [ ] Repetir analises de robustez por `horizon` (h+1/h+2/h+7/h+15/h+30).

## 3.6 Comparacao estatistica entre modelos (OOS alinhado)
- [ ] DM test (Diebold-Mariano)
- [ ] MCS (Model Confidence Set)
- [ ] win-rate pareado por timestamp

---

## 4) Tabelas Recomendadas (Silver/Gold)

### 4.1 Silver
- [ ] `fact_oos_predictions`
- [ ] `fact_prediction_quantiles` (opcional se preferir long format por quantil)
- [ ] `fact_prediction_errors` (opcional se separado de `fact_oos_predictions`)
- [ ] Garantir `horizon` e `target_timestamp` como colunas obrigatorias nas tabelas de predicao.

### 4.2 Gold
- [ ] `gold_prediction_metrics_by_run_split`
- [ ] `gold_prediction_metrics_by_config`
- [ ] `gold_prediction_calibration`
- [ ] `gold_prediction_risk`
- [ ] `gold_dm_pairwise_results`
- [ ] `gold_mcs_results`
- [ ] `gold_prediction_metrics_by_horizon`

---

## 5) Regras de Alinhamento OOS (criticas)

- [ ] Comparacoes entre modelos devem usar exatamente o mesmo conjunto de `target_timestamp`.
- [ ] Nao comparar metricas entre modelos com cobertura temporal diferente sem intersecao explicita.
- [ ] Para DM/MCS, armazenar e usar perdas por timestamp no mesmo eixo temporal.
- [ ] Executar alinhamento separadamente por `horizon` antes de agregar resultados.

---

## 6) Qualidade e Auditoria

- [ ] Validar ausencia de duplicatas na chave temporal por run.
- [ ] Validar nulos indevidos em `y_pred` e em `y_true` (quando split supervisionado).
- [ ] Validar ranges impossiveis (ex.: `pred_interval_width < 0`).
- [ ] Validar cardinalidade esperada por (`config x fold x seed x split`).
- [ ] Gerar relatorio automatico de qualidade para predicoes.

---

## 7) Definition of Done

- [ ] Todas as predicoes primarias (Y) estao persistidas com chaves completas.
- [ ] Todos os derivados minimos por linha estao disponiveis.
- [ ] Todas as metricas de comparacao entre configs/feature sets sao reproduziveis sem retrain.
- [ ] DM/MCS podem ser executados apenas com dados persistidos.
