# Phase A — Code Audit (Pre-Experiment Gate)

**Status:** pendente
**Criado:** 2026-04-24
**Bloqueante para:** qualquer treino confirmatorio da Fase B

Este documento e o gate de entrada da Fase A (sanidade). Nenhum experimento
confirmatorio pode ser iniciado antes de todos os modulos P0 receberem veredicto
GREEN ou YELLOW (com acao documentada).

Referencia de contexto: `docs/00_overview/STRATEGIC_DIRECTION.md` §5 (Fase A).

---

## Como usar

Para cada modulo P0, preencher:
- **Veredicto:** GREEN / YELLOW / RED
- **Achados:** o que foi verificado e o que foi encontrado (nao o que se esperava)
- **Acao:** se YELLOW ou RED, o que precisa ser corrigido antes da Fase B

Veredictos:
- `GREEN` — sem problemas. Fase B pode prosseguir neste modulo.
- `YELLOW` — problema menor com acao documentada. Fase B pode prosseguir apos acao.
- `RED` — problema bloqueante. Fase B nao pode comecar.

---

## Modulos P0

---

### M1 — `train_tft_model_use_case.py`

**Por que e critico:** orquestra o pipeline inteiro. E onde a sequencia
split → scaler fit → dataset build pode introduzir leakage silencioso.
O maior arquivo do projeto (1.442 linhas).

**Questoes a verificar:**

| # | Questao | Arquivo:linha | Veredicto |
|---|---|---|---|
| Q1 | `known_real_cols` so contem features genuinamente futuro-conhecidas (calendario)? Nao ha override via config que injete features de preco/retorno? | `train_tft_model_use_case.py:1187` | |
| Q2 | O scaler interno do pytorch-forecasting (`TimeSeriesDataSet`) e fit apenas em `train_df`? O `from_dataset(training, val_df)` usa os parametros do training sem re-fit? | `pytorch_forecasting_tft_trainer.py:221-236` | |
| Q3 | A warmup policy remove corretamente os primeiros N dias antes de calcular splits, garantindo que features com `warmup_count > 0` nao produzam NaN no inicio do treino? | `train_tft_model_use_case.py:_apply_warmup_policy_to_split` | |
| Q4 | Ha algum caminho de codigo onde `test_df` e usado como criterio de HPO (mesmo indiretamente, como via `mean_test_rmse` sendo o objetivo padrao)? | `run_tft_optuna_search_use_case.py:49,176-184` | |

**Veredicto geral:** ___

**Achados:**

**Acao (se YELLOW/RED):**

---

### M2 — `pytorch_forecasting_tft_trainer.py`

**Por que e critico:** executa o treino real do TFT. O bug do fallback foi
corrigido em `f7901a4` (2026-04-03), mas a correcao nao foi validada
end-to-end com uma config all-features + multi-horizonte.

**Questoes a verificar:**

| # | Questao | Arquivo:linha | Veredicto |
|---|---|---|---|
| Q1 | Early stopping: o `monitor` e `val_loss` (correto) ou `train_loss`/metrica de test (invalido)? | `pytorch_forecasting_tft_trainer.py`: procurar `EarlyStopping` / `ModelCheckpoint` | |
| Q2 | `QuantileLoss(quantiles=[0.1, 0.5, 0.9])`: os pesos sao uniformes? Algum override reduz o peso de p10/p90 a zero (causaria colapso de gradiente)? | `pytorch_forecasting_tft_trainer.py:254` | |
| Q3 | O novo fallback `_manual_forward_quantiles_and_actuals` funciona para `max_prediction_length > 1`? O cubo `[N, H, Q]` e indexado corretamente para H > 1? | `pytorch_forecasting_tft_trainer.py:358-430` | |
| Q4 | Gate de degeneracao: apos o treino, ha verificacao de que `% linhas com p10==p90 < 5%` no OOS? Ou o pipeline passa silenciosamente com quantis degenerados? | `train_tft_model_use_case.py`: buscar check de MPIW | |

**Veredicto geral:** ___

**Achados:**

**Acao (se YELLOW/RED):**

---

### M3 — `build_tft_dataset_use_case.py`

**Por que e critico:** constroi o dataset que alimenta o TFT. Leakage aqui
contamina todos os runs — nao pode ser detectado por metricas OOS.

**Questoes a verificar:**

| # | Questao | Arquivo:linha | Veredicto |
|---|---|---|---|
| Q1 | O `sklearn_indicator_normalizer` (`fit()`) e chamado ANTES do split temporal ou DEPOIS? Se antes, leakage de normalizacao garantido. | `build_tft_dataset_use_case.py`: buscar `normalizer.fit` / `sklearn_indicator_normalizer` | |
| Q2 | Features com `warmup_count > 0` no `feature_registry`: o dataset exclui os primeiros N dias dessas features corretamente, ou os inclui com NaN? | `feature_registry.py`: verificar `warmup_count`; `build_tft_dataset_use_case.py`: verificar aplicacao | |
| Q3 | Todas as features de retorno/preco estao em `time_varying_unknown_reals`, nao em `time_varying_known_reals`? Confirmar que o `known_real_cols` do trainer bate com o que foi definido aqui. | `build_tft_dataset_use_case.py:228-229` | |

**Veredicto geral:** ___

**Achados:**

**Acao (se YELLOW/RED):**

---

### M4 — `run_tft_inference_use_case.py` + `pytorch_forecasting_tft_inference_engine.py`

**Por que e critico:** inferencia deve reproduzir exatamente o protocolo de
treino. Divergencias silenciosas (config, scaler, seed) invalidam a
comparacao treino vs inferencia.

**Questoes a verificar:**

| # | Questao | Arquivo:linha | Veredicto |
|---|---|---|---|
| Q1 | O modelo e carregado com os mesmos `known_real_cols` e `feature_cols` usados no treino? Ou sao recalculados dinamicamente e podem divergir se a config mudar? | `run_tft_inference_use_case.py`: buscar `known_real_cols` / `feature_cols` no loader | |
| Q2 | Seed de inferencia: o modelo e colocado em `eval()` mode (desliga dropout)? Ou ha dropout ativo produzindo quantis diferentes entre runs? | `pytorch_forecasting_tft_inference_engine.py`: buscar `.eval()` / `torch.no_grad()` | |
| Q3 | O guardrail monotonico (`quantile_p*_post_guardrail`) e aplicado na inferencia da mesma forma que no treino? Ou so e aplicado no refresh do analytics store? | `run_tft_inference_use_case.py`: buscar `guardrail` / `post_guardrail` | |
| Q4 | A seed de inferencia e registrada em `fact_config` ou `dim_run` para reproducibilidade? | `run_tft_inference_use_case.py` / `parquet_analytics_run_repository.py` | |

**Veredicto geral:** ___

**Achados:**

**Acao (se YELLOW/RED):**

---

### M5 — `refresh_analytics_store_use_case.py`

**Por que e critico:** calcula todas as metricas do paper. PICP calculado
sobre quantis raw vs pos-guardrail produz numeros diferentes. Scope incorreto
mistura sweeps na mesma metrica.

**Questoes a verificar:**

| # | Questao | Arquivo:linha | Veredicto |
|---|---|---|---|
| Q1 | PICP e calculado sobre `quantile_p10_post_guardrail`/`quantile_p90_post_guardrail` ou sobre `quantile_p10`/`quantile_p90` raw? As duas colunas existem — qual e usada como primaria? | `refresh_analytics_store_use_case.py`: buscar `picp` / `in_interval` | |
| Q2 | As tabelas gold `gold_prediction_metrics_by_config`, `gold_prediction_calibration` e `gold_prediction_robustness_by_horizon` recebem `parent_sweep_id` no output? Se nao, como filtrar escopo na analise final? | Confirmado: nenhuma das tres tem `parent_sweep_id`. Verificar se ha filtro pre-calculo ou so pos-calculo. | |
| Q3 | O `ScopeSpec` com `scope_mode=cohort_decision` e passado corretamente em todos os paths de calculo que alimentam decisao estatistica (DM, MCS, win-rate)? Ou so no quality gate? | `refresh_analytics_store_use_case.py`: buscar `scope_spec` / `ScopeSpec` | |

**Veredicto geral:** ___

**Achados:**

**Acao (se YELLOW/RED):**

---

## Gate de saida da Fase A

Criterio para abrir a Fase B:

- [ ] M1 GREEN ou YELLOW com acao concluida
- [ ] M2 GREEN ou YELLOW com acao concluida
- [ ] M3 GREEN ou YELLOW com acao concluida
- [ ] M4 GREEN ou YELLOW com acao concluida
- [ ] M5 GREEN ou YELLOW com acao concluida
- [ ] Nenhum modulo com veredicto RED em aberto

**Data de abertura da Fase B:** ___
**Responsavel:** Marcelo

---

## Modulos P1 (revisar antes da analise final, nao bloqueantes para Fase B)

| Modulo | Questao principal | Status |
|---|---|---|
| `run_tft_optuna_search_use_case.py` | Desabilitar ou remover `mean_test_rmse` como `objective_metric` para evitar uso acidental de test no HPO. | pendente |
| `feature_registry.py` | Todas as features all-features tem `anti_leakage_tag` e `warmup_count` corretos? Alguma feature nova sem tag? | pendente |
| `validate_analytics_quality_use_case.py` | O Block A (degeneracao) esta configurado como bloqueante (nao apenas warning) para MPIW=0 > 5%? | pendente |
| `sklearn_indicator_normalizer.py` | Confirmar que nunca e instanciado com dados alem do treino. | pendente |

---

## Registro de achados adicionais

_(preencher durante a auditoria com qualquer achado fora das questoes pre-definidas)_
