# Multi-Horizon Strategy

## Proposito
Documentar a politica de previsao multi-horizonte do projeto: quais horizontes
sao previstos, como sao representados nos dados persistidos, e como sao
avaliados separadamente. Nao cobre as metricas em si (ver
`04_evaluation/METRICS_DEFINITIONS.md`) nem comandos CLI (ver
`06_runbooks/RUN_TRAINING.md`).

## Conceitos-chave
- **Horizonte (`h+N`):** numero de passos a frente previsto. `h+1` = proximo
  dia util; `h+7` = 7 dias uteis; `h+30` = 30 dias uteis.
- **`max_prediction_length`:** parametro do TFT que define quantos passos a
  frente o modelo emite em uma unica forward pass.
- **`evaluation_horizons`:** lista de horizontes efetivamente avaliados (subset
  de `[1, ..., max_prediction_length]`).
- **`target_timestamp`:** timestamp do periodo alvo previsto. Chave de
  alinhamento em comparacoes pareadas; calculado por horizonte.
- **N efetivo (nao-sobreposto):** numero de observacoes verdadeiramente
  independentes por horizonte. Para h+30 com janelas diarias, `N_overlapped /
  30` aproxima o N estatisticamente util.

## Decisoes e escolhas
- **Horizontes principais: h+1, h+7, h+30.** *Why:* cobrem curto, medio e
  longo prazo dentro do escopo single-asset; alinhados a horizontes praticos
  de decisao em forecasting financeiro.
- **Geracao em uma unica passagem do TFT (`max_prediction_length=30`).** *Why:*
  evita treinar 3 modelos separados; o TFT compartilha representacao temporal
  entre horizontes.
- **Metricas reportadas separadamente por horizonte, nunca agregadas no total.**
  *Why:* agregar mascara degradacao em horizontes longos, que e exatamente
  onde modelos complexos costumam falhar versus baselines simples. Reportar
  separado e exigencia metodologica.
- **Alinhamento OOS pareado feito por (`asset`, `split`, `horizon`,
  `target_timestamp`), separado por horizonte.** *Why:* DM/MCS exige amostras
  identicas; comparar h+1 de um modelo com h+30 de outro e invalido.
- **h+30 tratado com cautela na escrita do paper.** *Why:* N efetivo nao-sobreposto
  e baixo (tipicamente ~25 para 3 anos OOS); poder estatistico limitado para
  DM/MCS. Reportado sempre com declaracao de limitacao.

## Persistencia (contrato por linha de predicao)

| Coluna | Tipo | Descricao |
|---|---|---|
| `horizon` | `int64` | numero de passos a frente (1, 7, 30) |
| `target_timestamp_utc` | `timestamp[utc]` | timestamp alvo previsto |
| `y_true`, `y_pred` | `float64` | valor real e previsao pontual no horizonte |
| `quantile_p10/p50/p90` | `float64` | quantis raw |
| `quantile_p10/p50/p90_post_guardrail` | `float64` | quantis monotonicos |

Grao logico de `fact_oos_predictions`:
`run_id + split + horizon + timestamp + target_timestamp`.

## Validacoes obrigatorias
- Cobertura completa de horizontes esperados por `run_id`/`split`.
- `n_common` por horizonte na intersecao temporal (ver
  `gold_paired_oos_intersection_by_horizon`).
- `target_timestamp` monotonico por (`run_id`, `split`, `horizon`).

## Fonte da verdade (codigo)
- `src/use_cases/train_tft_model_use_case.py` — define
  `evaluation_horizons` e propaga para o trainer
- `src/adapters/pytorch_forecasting_tft_trainer.py` — emissao de predicoes
  multi-horizonte (`selected_horizons`, `selected_idx`)
- `src/use_cases/refresh_analytics_store_use_case.py` — calculo de metricas
  por horizonte e intersecao pareada

## Documentos relacionados
- `04_evaluation/METRICS_DEFINITIONS.md` — formulas das metricas por horizonte
- `04_evaluation/STATISTICAL_TESTS.md` — DM/MCS com alinhamento por horizonte
- `00_overview/STRATEGIC_DIRECTION.md` §5 (Fase B) — politica de horizontes
  na rodada confirmatoria
- `05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md` §1.0 — historico de
  implementacao multi-horizonte
