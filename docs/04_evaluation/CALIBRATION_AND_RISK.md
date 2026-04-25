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

### Computation
- Cobertura nominal: `0.80` (intervalo p10-p90)
- `PICP = mean(quantile_p10 <= y_true <= quantile_p90)`
- `MPIW = mean(quantile_p90 - quantile_p10)`
- `coverage_error = PICP - 0.80`
- `confidence_calibrated` conforme formula em `METRICS_DEFINITIONS.md`

### Calibration Interpretation
- `coverage_error ~ 0`: calibracao adequada
- `coverage_error < 0`: under-coverage (otimista demais)
- `coverage_error > 0`: over-coverage (intervalos conservadores)

## Calibration Acceptance Thresholds
Para decisao oficial, aplicar por horizonte e coorte:
- `abs(coverage_error) <= 0.02` (target)
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
