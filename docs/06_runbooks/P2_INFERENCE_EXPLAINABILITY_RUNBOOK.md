---
title: P2 Inference Explainability Runbook
scope: Operacionalizacao da inferencia explicavel em producao — geracao, validacao e monitoramento. Para schema do payload, ver 03_modeling/P2_INFERENCE_EXPLAINABILITY_CONTRACT.md.
update_when:
  - fluxo operacional de inferencia explicavel mudar
  - novo gate de validacao for adicionado a pipeline P2
  - politica de monitoramento mudar
canonical_for: [p2_inference_runbook, inference_explainability_operation, p2_quality_gates]
---

# P2 Inference Explainability Runbook

Objetivo: operacionalizar geracao, validacao e monitoramento da inferencia explicavel em producao.

## 1. Pre-requisitos

- Modelo TFT valido com `prediction_mode=quantile`.
- Horizontes habilitados no modelo (ideal: `1,7,30`).
- Tabelas silver acessiveis:
  - `fact_inference_runs`
  - `fact_inference_predictions`
  - `fact_feature_contrib_local`
- Analytics refresh operacional.

## 2. Execucao padrao

### 2.1 Inferencia rolling com persistencia

```bash
.venv/bin/python -m src.main_infer_tft \
  --asset AAPL \
  --model-path <MODEL_VERSION> \
  --start YYYYMMDD \
  --end YYYYMMDD \
  --overwrite
```

Resultado esperado:
- `fact_inference_predictions` preenchido para todos os dias elegiveis.
- `fact_feature_contrib_local` preenchido (quando explicacao habilitada no pipeline).

### 2.2 Refresh analytics + quality gate

```bash
.venv/bin/python -m src.main_refresh_analytics_store --fail-on-quality
```

## 3. Checklist operacional rapido

1. Cobertura temporal:
- dias solicitados vs elegiveis vs inferidos.

2. Contrato probabilistico:
- `p10<=p50<=p90`
- `p90-p10 >= 0`

3. Explicabilidade local:
- existe contribuicao por horizonte?
- ranking top-k ordenado por magnitude?
- estabilidade acima do limiar?

4. Rastreabilidade:
- `inference_run_id` consistente entre run/predictions/contribuicoes.

## 4. Consultas de validacao recomendadas

### 4.1 Quantis e largura de intervalo

```python
import pandas as pd

p = "data/analytics/silver/fact_inference_predictions/asset=AAPL/fact_inference_predictions.parquet"
df = pd.read_parquet(p)

invalid_order = ((df["quantile_p10"] > df["quantile_p50"]) | (df["quantile_p50"] > df["quantile_p90"]))
negative_width = (df["quantile_p90"] - df["quantile_p10"]) < 0

print("invalid_order:", int(invalid_order.sum()))
print("negative_width:", int(negative_width.sum()))
```

### 4.2 Presenca de explicacao local

```python
import pandas as pd

pred = pd.read_parquet("data/analytics/silver/fact_inference_predictions/asset=AAPL/fact_inference_predictions.parquet")
feat = pd.read_parquet("data/analytics/silver/fact_feature_contrib_local/asset=AAPL/fact_feature_contrib_local.parquet")

keys = ["inference_run_id", "timestamp_utc", "target_timestamp_utc", "horizon"]
coverage = pred[keys].drop_duplicates().merge(feat[keys].drop_duplicates(), on=keys, how="left", indicator=True)
print(coverage["_merge"].value_counts(dropna=False))
```

## 5. Diagnostico de falhas comuns

1. `fact_feature_contrib_local` vazio:
- explicacao local desabilitada no fluxo;
- erro silencioso no calculo de contribuicoes;
- chave temporal divergente entre previsao e contribuicao.

2. Crossing recorrente:
- revisar calibracao/regularizacao;
- validar regime shift no periodo;
- aplicar guardrail monotono com auditoria de impacto.

3. Cobertura incompleta:
- janelas inelegiveis por falta de contexto;
- `overwrite=False` preservando linhas antigas;
- deduplicacao removendo entradas com chave repetida.

## 6. Operacao segura (idempotencia)

- Reexecucao com `--overwrite` deve substituir somente o escopo solicitado.
- Evitar limpar manualmente silver sem snapshot/backup.
- Para interrupcoes, usar politica de resume/cleanup da pipeline de sweeps.

## 7. Evidencias para defesa academica

Registrar por rodada de producao:
- taxa de quantile crossing;
- distribuicao de `interval_width` e cobertura;
- estabilidade de explicacao local;
- exemplos interpretativos por horizonte (casos de acerto/erro).

Referenciar em:
- `docs/07_reports/living-paper/evidence_log.md`
- relatorio de rodada correspondente.
