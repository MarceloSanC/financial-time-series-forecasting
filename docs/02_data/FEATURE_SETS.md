# Feature Sets

## Purpose
Documentar o contrato canonico de feature sets usado em treino, inferencia e
analytics, com foco em composicao, causalidade e warmup.

## Canonical Source of Truth
- Registry: `src/infrastructure/schemas/feature_registry.py`
- Validation schema: `src/infrastructure/schemas/feature_validation_schema.py`
- Dataset build: `src/use_cases/build_tft_dataset_use_case.py`
- Feature token parsing: `src/utils/feature_token_parser.py`

## Feature Contract
Cada feature e registrada via `FeatureSpec` com:
- `name`
- `group`
- `source_cols`
- `formula_desc`
- `anti_leakage_tag`
- `warmup_count`
- `dtype`
- `null_policy`

## Canonical Groups
- `baseline`: OHLCV base (`open`, `high`, `low`, `close`, `volume`)
- `technical`: indicadores tecnicos causais (`rsi_14`, `ema_*`, `macd`, etc.)
- `sentiment`: agregados de noticias (`sentiment_score`, `news_volume`, etc.)
- `fundamental`: variaveis fundamentalistas as-of
- `derived`: features derivadas das fontes existentes (sem nova fonte externa)

## Selection Semantics
- CLI/JSON aceitam combinacao de grupos e features explicitas.
- Ordem final das features e preservada e persistida.
- `feature_set_hash` e calculado da lista ordenada para rastreabilidade.
- `required_warmup_count = max(warmup_count das features selecionadas)`.
- Warmup policy:
  - `strict_fail`: aborta em aquecimento insuficiente
  - `drop_leading`: ajusta inicio efetivo de treino

## Anti-Leakage Policy
- Toda feature deve ter `anti_leakage_tag` explicito no registry.
- Regras aceitas:
  - `point_in_time_ohlcv`
  - `trailing_window_causal`
  - `publication_cutoff_asof`
  - `reported_date_asof`
  - `same_timestamp_ohlc_derived`
- Features sem contrato de causalidade nao devem entrar em treino oficial.

## Expected Artifacts
- Dataset TFT com colunas sincronizadas e sem leakage.
- Metadata de run com:
  - `feature_set_name`
  - `feature_list_ordered`
  - `feature_set_hash`
  - `required_warmup_count`
  - `warmup_policy`
  - `effective_train_start` (quando aplicavel)

## Validation
- Unit:
  - `tests/unit/infrastructure/schemas/test_feature_registry.py`
  - `tests/unit/infrastructure/schemas/test_feature_validation_schema.py`
  - `tests/unit/use_cases/test_build_tft_dataset_use_case.py`
- Integration:
  - `tests/integration/*dataset*`
- Runbook:
  - `docs/06_runbooks/RUN_DATASET.md` (notas de warmup e qualidade pre-treino)

## Checklist Cross-Reference
- Tracking de implementacao e backlog:
  - `docs/05_checklists/CHECKLISTS.md` (secao de features)
  - `docs/05_checklists/FEATURES_SET_CHECKLIST.md`
