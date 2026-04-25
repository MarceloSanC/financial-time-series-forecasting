# Statistical Tests

Objetivo: definir protocolo estatistico para comparacao entre modelos usando
somente dados OOS persistidos e alinhados temporalmente.

## Canonical Implementation
- `src/use_cases/refresh_analytics_store_use_case.py`
- `src/use_cases/validate_analytics_quality_use_case.py`

## Required Preconditions
- Comparacao somente em OOS (`split=test` ou split explicitamente definido)
- Alinhamento exato por:
  - `asset`
  - `split`
  - `horizon`
  - `target_timestamp`
- Intersecao temporal explicita antes de qualquer teste pareado
- Escopo declarado (`cohort_decision` para decisao final)

## Tests

### 1) Diebold-Mariano (DM)
- Hipotese nula: igualdade de acuracia preditiva esperada entre dois modelos.
- Base: series de perdas pareadas por `target_timestamp`.
- Saida minima:
  - estatistica DM
  - `pvalue`
  - `pvalue_adj_holm` (controle de comparacoes multiplas)

### 2) Model Confidence Set (MCS)
- Objetivo: conjunto de modelos nao rejeitados como melhores ao nivel `alpha`.
- Nivel default implementado: `alpha=0.05`.
- Saida minima:
  - `selected_in_mcs_alpha_0_05`
  - `aligned_timestamps`
  - `n_configs`

### 3) Pairwise Win-Rate
- Compara vitorias por timestamp entre pares de modelos.
- Reporta win-rate com e sem empates e tamanhos de amostra alinhada.

## Multiple Testing
- Ajuste obrigatorio para DM pairwise:
  - Holm (`pvalue_adj_holm`)
- Resultado significativo:
  - `pvalue_adj_holm < 0.05`

## Scope and Horizon Rules
- Nunca misturar horizontes no mesmo teste.
- Nunca comparar coortes com `split_signature` incompativel.
- Resultado global nao substitui resultado scoped para decisao de vencedor.

## Canonical Output Tables
- `gold_dm_pairwise_results.parquet`
- `gold_mcs_results.parquet`
- `gold_win_rate_pairwise_results.parquet`
- `gold_paired_oos_intersection_by_horizon.parquet`
- `gold_quality_statistics_report.parquet`

## Validation Gate
O quality gate deve confirmar que os testes sao executaveis com dados persistidos:
- check `dm_mcs_persisted_executable` valido
- intersecoes temporais presentes e nao vazias
