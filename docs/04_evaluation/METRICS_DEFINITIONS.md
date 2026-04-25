# Metrics Definitions

Objetivo: definir formulas, agregacoes e implementacao canonica das metricas.
Este arquivo complementa o `GLOSSARY` (sem repetir semantica basica).

## Canonical Implementation
- `src/use_cases/refresh_analytics_store_use_case.py`
- `src/adapters/pytorch_forecasting_tft_trainer.py` (split metrics de treino)

## Row-Level Derived Columns
Para cada linha OOS (run, split, horizon, timestamp, target_timestamp):
- `error = y_pred - y_true`
- `abs_error = abs(error)`
- `sq_error = error^2`
- `pred_interval_width = quantile_p90 - quantile_p10`
- `covered_80 = 1{quantile_p10 <= y_true <= quantile_p90}`
- `da_row = 1{sign(y_pred) == sign(y_true)}`

## Core Metrics (aggregated)
Agregacao por (`run_id`, `split`, `horizon`) e derivados superiores.

- `rmse = sqrt(mean(sq_error))`
- `mae = mean(abs_error)`
- `mape = mean(abs(error / y_true))` (com protecao para `y_true=0`)
- `smape = mean(2*abs_error / (abs(y_true)+abs(y_pred)))`
- `directional_accuracy = mean(da_row)`
- `bias = mean(error)`

## Probabilistic Metrics
- `pinball_q = mean(max(q*(y_true-y_pred_q), (q-1)*(y_true-y_pred_q)))`
- `mean_pinball = mean(pinball_q10, pinball_q50, pinball_q90)`
- `picp = mean(covered_80)`
- `mpiw = mean(pred_interval_width)`
- `coverage_nominal = 0.8` (intervalo p10-p90)
- `coverage_error = picp - coverage_nominal`

## Confidence Proxy
Usada no gold para leitura operacional de calibracao + sharpness:
- `calibration_term = clip(1 - abs(coverage_error)/coverage_nominal, 0, 1)`
- `width_term = 1 / (1 + clip(pred_interval_width, lower=0))`
- `confidence_calibrated = calibration_term * width_term`

## Risk Metrics (from predictions)
- `expected_move = mean(abs(y_pred))`
- `downside_risk = mean(max(-y_pred, 0))`
- `var_10 = mean(quantile_p10)`
- `es_10_approx = mean(min(1.125*quantile_p10 - 0.125*quantile_p50, quantile_p10))`

## Gold Tables (primary)
- `gold_prediction_metrics_by_run_split_horizon.parquet`
- `gold_prediction_metrics_by_config.parquet`
- `gold_prediction_metrics_by_horizon.parquet`
- `gold_prediction_calibration.parquet`
- `gold_prediction_risk.parquet`

## Validation Rules
- All metric columns must be numeric finite values where required.
- `pred_interval_width >= 0`
- `0 <= picp <= 1`
- `n_samples > 0` for valid aggregated rows
- no duplicated OOS keys in source predictions
