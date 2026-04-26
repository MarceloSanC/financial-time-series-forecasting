---
title: Calibration and Risk
scope: Metodologia de calibracao probabilistica (calibracao marginal por quantil, PICP intervalar, MPIW), bandas de aceitacao para gate de elegibilidade e metricas de risco (VaR, ES). Distincao explicita entre cobertura intervalar (PICP do p10-p90) e calibracao marginal por quantil individual.
update_when:
  - bandas de tolerancia de calibracao marginal mudarem
  - thresholds de coverage_error/MPIW serem revisados
  - nova metrica de risco for adicionada (VaR, ES, downside)
  - politica de gate de elegibilidade por calibracao mudar
canonical_for: [calibration, risk_metrics, marginal_quantile_calibration, interval_picp, var_es]
---

# Calibration and Risk

Objetivo: definir metodologia de calibracao e criterios de aceite para risco
predito por horizonte, com base em artefatos persistidos.

## Canonical Implementation
- `src/use_cases/refresh_analytics_store_use_case.py`
- `src/use_cases/validate_analytics_quality_use_case.py`

## Calibration Method

### Inputs
- Quantis por linha (`quantile_p10`, `quantile_p50`, `quantile_p90`)
- Verdade-terreno `y_true` (splits supervisionados)

### Computation: Interval Calibration
- Cobertura nominal: `0.80` (intervalo p10-p90)
- `PICP = mean(quantile_p10 <= y_true <= quantile_p90)`
- `MPIW = mean(quantile_p90 - quantile_p10)`
- `coverage_error = PICP - 0.80`
- `confidence_calibrated` conforme formula em `METRICS_DEFINITIONS.md`

### Computation: Marginal Quantile Calibration
Para quantis individuais, nao usar o termo PICP. O criterio correto e a taxa
empirica de cobertura marginal:

- `coverage_q10 = mean(y_true <= quantile_p10)`; alvo nominal `0.10`
- `coverage_q50 = mean(y_true <= quantile_p50)`; alvo nominal `0.50`
- `coverage_q90 = mean(y_true <= quantile_p90)`; alvo nominal `0.90`
- `quantile_coverage_error_qtau = coverage_qtau - tau`

### Calibration Interpretation
- `coverage_error ~ 0`: cobertura intervalar adequada para p10-p90
- `coverage_error < 0`: under-coverage intervalar (otimista demais)
- `coverage_error > 0`: over-coverage intervalar (intervalos conservadores)
- `coverage_qtau ~ tau`: calibracao marginal adequada do quantil `tau`
- `coverage_qtau < tau`: quantil previsto esta alto demais para o nivel nominal
- `coverage_qtau > tau`: quantil previsto esta baixo demais para o nivel nominal

## Calibration Acceptance Thresholds
Para decisao oficial, aplicar por horizonte e coorte:
- `abs(coverage_error) <= 0.02` (target)
- bandas de calibracao marginal por quantil devem ser declaradas no
  pre-registro (default sugerido para debate: p10 in [0.07, 0.13],
  p50 in [0.45, 0.55], p90 in [0.87, 0.93])
- `MPIW > 0` e finito
- Sem colapso de cobertura (`PICP` nao proximo de 0 em todos modelos)
- Contrato quantilico valido (`p10 <= p50 <= p90`)

Observacao: limites podem ser endurecidos por pre-registro de rodada.

## Quantile Contract Guardrail (Block A)
- Crossing bruto aceito no maximo: `<= 0.10%` (provisorio)
- Crossing pos-guardrail: `0`
- Interval width negativo: `0`
- Impacto do guardrail:
  - `delta_pinball_rel <= +1.0%`
  - `abs(delta_picp) <= 0.02`
  - `delta_mpiw_rel <= +5.0%`

## Risk Method
Agregado por (`run_id`, `split`, `horizon`):
- `expected_move = mean(abs(y_pred))`
- `downside_risk = mean(max(-y_pred, 0))`
- `var_10 = mean(quantile_p10)`
- `es_10_approx = mean(min(1.125*q10 - 0.125*q50, q10))`

## Risk Acceptance (minimum)
- `var_10` e `es_10_approx` coerentes (`es_10_approx <= var_10`)
- Sem valores nao finitos
- Comparacao sempre por mesmo horizonte e mesma coorte

## Canonical Outputs
- `gold_prediction_calibration.parquet`
- `gold_prediction_risk.parquet`
- `gold_quantile_guardrail_audit.parquet`

## Operational Command
```bash
python -m src.main_refresh_analytics_store --fail-on-quality
```
