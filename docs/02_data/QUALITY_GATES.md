---
title: Quality Gates
scope: Catalogo de checks aplicados durante o refresh do analytics store (integridade temporal, cobertura, contratos quantilicos, scope governance). Define quando o pipeline deve falhar (`--fail-on-quality`) e quando deve apenas avisar.
update_when:
  - novo check de qualidade for adicionado
  - threshold de check existente mudar
  - politica de fail vs warn mudar
  - novo modo de escopo for introduzido
canonical_for: [quality_gates, validation_checks, fail_on_quality, scope_aware_quality]
---

# Quality Gates

## Purpose
Definir os gates de qualidade obrigatorios para dados, predicoes e tabelas
analiticas antes de qualquer comparacao ou decisao final.

## Canonical Source of Truth
- CLI entrypoint: `src/main_refresh_analytics_store.py`
- Refresh logic: `src/use_cases/refresh_analytics_store_use_case.py`
- Quality checks: `src/use_cases/validate_analytics_quality_use_case.py`
- Domain checks (quantile contract): `src/domain/services/quantile_contract_analyzer.py`
- Data quality helpers: `src/domain/services/dataset_quality_gate.py`

## Gate Taxonomy

### 1) Dataset gates (pre-train)
- Schema consistency and required columns
- Timestamp monotonicity and uniqueness
- Minimal temporal coverage
- Missing ratio constraints per feature
- Warmup feasibility (`strict_fail` or `drop_leading`)

### 2) Analytics silver gates
- Referential consistency (`dim_*` x `fact_*`)
- Required numeric fields not null
- OOS key uniqueness
- Quantile ordering (`p10 <= p50 <= p90`)
- Non-negative interval width

### 3) Gold decision gates
- Metrics tables materialized and non-empty
- Pairwise statistics executable from persisted data
- Scoped temporal alignment for paired comparisons
- `confidence_calibrated` present by horizon
- Scope-aware reporting (`global_health` vs `cohort_decision`)

## Scope Semantics (mandatory)
- `global_health`: plataforma inteira para monitoramento
- `cohort_decision`: somente a coorte candidata a decisao
- Regra: decisao estatistica final exige `cohort_decision` com escopo explicito
  e comparabilidade por `target_timestamp`.

## Required Command
```bash
python -m src.main_refresh_analytics_store --fail-on-quality
```

## Optional Scoped Validation (Block A)
Quando a analise exigir filtros de coorte/split/horizon no contrato quantilico:
```bash
python -m src.main_refresh_analytics_store \
  --fail-on-quality \
  --block-a-scope-sweep-prefixes 0_2_3_ \
  --block-a-splits val,test \
  --block-a-horizons 1
```

## Acceptance Criteria (minimum)
- `failed_checks=[]` no gate principal.
- Nenhum crossing pos-guardrail.
- Nenhuma largura de intervalo negativa.
- Tabelas gold principais existentes e com dados para o escopo de decisao.
- DM/MCS/win-rate executaveis sobre intersecao temporal valida.

## Related Runbooks
- `docs/06_runbooks/RUN_REFRESH_ANALYTICS.md`
- `docs/06_runbooks/RUN_SWEEPS.md`
- `docs/06_runbooks/P2_INFERENCE_EXPLAINABILITY_RUNBOOK.md`

## Checklist Cross-Reference
- `docs/05_checklists/ANALYTICS_STORE_CHECKLIST.md`
- `docs/05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md`
- `docs/05_checklists/CHECKLISTS.md`
