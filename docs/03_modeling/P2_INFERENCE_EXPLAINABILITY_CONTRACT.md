---
title: P2 Inference Explainability Contract
scope: Schema versionado canonico da resposta de inferencia explicavel em producao (`p2.inference_explainability.v1`). Define payload por horizonte com p10/p50/p90, risk_summary, feature_contributions, explanation_text e explanation_reliability.
update_when:
  - schema do payload mudar (nova versao p2.inference_explainability.vN)
  - novo campo for adicionado ao contrato
  - politica de top_k ou full contributions mudar
  - restricao semantica da explicacao for revisada
canonical_for: [p2_inference_contract, inference_payload_schema, explainability_contract, explanation_reliability]
---

# P2 Inference Explainability Contract

Objetivo: definir o contrato tecnico canonico da inferencia explicavel em producao, incluindo previsao multi-horizonte, risco e explicabilidade local por feature.

## 1. Escopo

Este contrato cobre:
- resposta de inferencia para horizontes habilitados no modelo (`h+1`, `h+7`, `h+30` quando aplicavel);
- saidas probabilisticas (`p10`, `p50`, `p90`) por horizonte;
- resumo de risco por horizonte;
- contribuicao local por feature para cada previsao (top-k e lista completa);
- regras de estabilidade e flags de confianca explicativa.

Este contrato nao cobre:
- treino/otimizacao de hiperparametros;
- explicabilidade global offline (ja coberta em artefatos gold de analise).

## 2. Versao de contrato

- `schema_version`: `p2.inference_explainability.v1`
- Compatibilidade:
  - campos novos devem ser adicionados de forma backward-compatible;
  - remocao/renomeacao de campo exige nova versao de schema.

## 3. Entrada minima do endpoint/use case

- `asset_id`
- `model_version` (ou `model_path` resolvido)
- `decision_timestamp_utc` (ou periodo para inferencia rolling)
- `requested_horizons` (opcional; default = horizontes do modelo)
- `top_k_features` (default: 5)
- `include_full_feature_contrib` (default: `false`)

## 4. Payload de saida (normativo)

```json
{
  "schema_version": "p2.inference_explainability.v1",
  "asset_id": "AAPL",
  "model_version": "20260402_142837_BF",
  "inference_run_id": "20260407_193000",
  "decision_timestamp_utc": "2025-02-28T00:00:00+00:00",
  "predictions_by_horizon": [
    {
      "horizon": 1,
      "target_timestamp_utc": "2025-03-03T00:00:00+00:00",
      "prediction_mode": "quantile",
      "quantiles": {
        "p10": -0.005,
        "p50": 0.030,
        "p90": 0.120
      },
      "risk_summary": {
        "expected_move": 0.030,
        "interval_width": 0.125,
        "downside_risk_proxy": 0.005,
        "confidence_calibrated": 0.71
      },
      "feature_contributions": {
        "top_positive": [
          {"feature": "sentiment_score", "contribution": 0.011, "pct_abs": 0.21},
          {"feature": "momentum_21d", "contribution": 0.008, "pct_abs": 0.15}
        ],
        "top_negative": [
          {"feature": "volatility_20d", "contribution": -0.006, "pct_abs": 0.12}
        ],
        "top_k": [
          {"feature": "sentiment_score", "contribution": 0.011, "abs_contribution": 0.011, "sign": "+"}
        ],
        "full": []
      },
      "explanation_text": "Sinal esperado positivo com incerteza moderada. Contribuicoes mais relevantes: sentiment_score (+), momentum_21d (+), volatility_20d (-).",
      "explanation_reliability": {
        "stability_score": 0.78,
        "status": "ok",
        "flags": []
      }
    }
  ]
}
```

## 5. Regras obrigatorias por horizonte

1. Quantis ordenados: `p10 <= p50 <= p90`.
2. Largura de intervalo nao negativa: `interval_width = p90 - p10 >= 0`.
3. `target_timestamp_utc` coerente com `decision_timestamp_utc + horizon` no calendario util adotado.
4. `feature_contributions.top_k` ordenado por `abs_contribution` desc.
5. `pct_abs` normalizado no conjunto retornado (`0..1`).

## 6. Persistencia (analytics)

### 6.1 Tabela de predicoes de inferencia
- destino: `fact_inference_predictions`
- granularidade: 1 linha por (`inference_run_id`,`decision_timestamp_utc`,`target_timestamp_utc`,`horizon`).
- campos minimos:
  - `asset_id`, `model_version`, `prediction`, `quantile_p10`, `quantile_p50`, `quantile_p90`, `horizon`.

### 6.2 Tabela de contribuicao local
- destino: `fact_feature_contrib_local`
- granularidade: 1 linha por (`inference_run_id`,`decision_timestamp_utc`,`target_timestamp_utc`,`horizon`,`feature`).
- campos minimos:
  - `contribution`, `abs_contribution`, `rank`, `sign`, `explanation_method`, `stability_score`.

## 7. Regras de explicabilidade

- Metodo default recomendado: perturbacao local controlada (deterministica por seed de explicacao).
- Atenuacao de risco interpretativo:
  - exibir como "fatores associados";
  - nao apresentar causalidade forte.
- Se estabilidade local < limiar:
  - manter previsao;
  - marcar explicacao como `status="low_reliability"`.

## 8. Quality gates (P2)

1. `inference_quantile_order`: 100% das linhas com `p10<=p50<=p90` apos pos-processamento final.
2. `inference_interval_width_non_negative`: 100% das linhas com largura >= 0.
3. `inference_feature_contrib_presence`: >= 1 feature por horizonte quando explicacao habilitada.
4. `inference_feature_contrib_topk_sorted`: ranking top-k consistente por `abs_contribution`.
5. `inference_explainability_stability`: `% explicacoes com stability_score >= limiar` por horizonte.

## 9. Criterios de aceite de release P2

- Payload produzido com schema `p2.inference_explainability.v1`.
- Inference rolling preenchendo todos os dias elegiveis no periodo solicitado.
- Persistencia completa em `fact_inference_predictions` e `fact_feature_contrib_local`.
- Quality gates P2 aprovados no escopo do sweep/producao definido.
- Documentacao e runbook atualizados.

## 10. Dependencias documentais

- `docs/05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md`
- `docs/06_runbooks/P2_INFERENCE_EXPLAINABILITY_RUNBOOK.md`
- `docs/07_reports/living-paper/*` (evidencias e decisoes)
