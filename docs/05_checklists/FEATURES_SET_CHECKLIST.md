---
title: Features Set Checklist
scope: Tracking de features implementadas por componente do pipeline (build_dataset, technical, sentiment, fundamentals), incluindo backlog de features derivadas. Para registry canonico e regras anti-leakage, ver 02_data/FEATURE_SETS.md.
update_when:
  - nova feature for implementada
  - feature for movida entre familias
  - backlog de features derivadas for atualizado
  - status de implementacao (checkbox) for atualizado
canonical_for: [features_set_checklist, feature_implementation_tracking, feature_backlog]
---

# Checklist de Features por Use Case/Componente

Objetivo: centralizar as features do projeto TFT por componente, incluindo o que ja existe e o backlog de features derivadas sem novas fontes de dados.

## 0) Politica de Registro Unificado de Feature (implementado)

- [x] Criar contrato canonico `FeatureSpec` para toda feature implementada.
- [x] Centralizar todas as features implementadas em um unico `feature_registry`.
- [x] Incluir no contrato: `name`, `group`, `source_cols`, `formula_desc`, `anti_leakage_tag`, `warmup_count`, `dtype`, `null_policy`.
- [x] Derivar `warmup_features` e `anti_leakage_tags` automaticamente a partir do registry (evitar duplicacao manual de regras).
- [x] Expor hash/versionamento do registro para rastreabilidade de experimentos.

## 1) Componente: Build TFT Dataset (`build_dataset_tft`)

### 1.1 Base temporal e alvo
- [x] `time_idx`
- [x] `day_of_week`
- [x] `month`
- [x] `target_return`

### 1.2 Feature set baseline (preco/volume)
- [x] `open` (Anti-leakage: usar somente valor observado em `t`; nunca usar dados de `t+1` no mesmo registro.)
- [x] `high` (Anti-leakage: usar somente valor observado em `t`; nunca usar dados de `t+1` no mesmo registro.)
- [x] `low` (Anti-leakage: usar somente valor observado em `t`; nunca usar dados de `t+1` no mesmo registro.)
- [x] `close` (Anti-leakage: usar somente valor observado em `t`; alvo deve permanecer deslocado para horizonte futuro.)
- [x] `volume` (Anti-leakage: usar somente valor observado em `t`; nunca usar agregacoes que incluam barras futuras.)

### 1.3 Feature set technical (ja implementado)
- [x] `volatility_20d` (Anti-leakage: calcular em janela trailing apenas com dados `<= t`; respeitar warmup de 20 periodos. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `rsi_14` (Anti-leakage: calcular em janela trailing apenas com dados `<= t`; respeitar warmup de 14 periodos. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `candle_body` (Anti-leakage: derivar apenas de OHLC do proprio `t`, sem informacao futura.)
- [x] `macd_signal` (Anti-leakage: calcular EMAs e sinal apenas com historico `<= t`; sem centralizacao de janela. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `ema_100` (Anti-leakage: EMA causal usando apenas historico `<= t`; respeitar warmup. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `macd` (Anti-leakage: derivar de EMAs causais calculadas com historico `<= t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `ema_10` (Anti-leakage: EMA causal usando apenas historico `<= t`; respeitar warmup. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `ema_200` (Anti-leakage: EMA causal usando apenas historico `<= t`; respeitar warmup de 200 periodos. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `ema_50` (Anti-leakage: EMA causal usando apenas historico `<= t`; respeitar warmup. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `candle_range` (Anti-leakage: derivar apenas de OHLC do proprio `t`, sem informacao futura.)

### 1.4 Feature set sentiment (ja implementado)
- [x] `sentiment_score` (Anti-leakage: aplicar cutoff por timestamp de publicacao; incluir somente noticias publicadas ate `t` na sessao correta.)
- [x] `news_volume` (Anti-leakage: contar apenas noticias com publication_time `<= t`; sem incluir noticias futuras do mesmo dia apos o cutoff.)
- [x] `sentiment_std` (Anti-leakage: calcular dispersao apenas com noticias disponiveis ate `t`.)
- [x] `has_news` (Anti-leakage: flag baseada apenas na existencia de noticias publicadas ate `t`.)

### 1.5 Feature set fundamental (ja implementado)
- [x] `revenue` (Anti-leakage: usar politica as-of pela data de divulgacao; forward-fill somente apos release oficial.)
- [x] `net_income` (Anti-leakage: usar politica as-of pela data de divulgacao; forward-fill somente apos release oficial.)
- [x] `operating_cash_flow` (Anti-leakage: usar politica as-of pela data de divulgacao; forward-fill somente apos release oficial.)
- [x] `total_shareholder_equity` (Anti-leakage: usar politica as-of pela data de divulgacao; forward-fill somente apos release oficial.)
- [x] `total_liabilities` (Anti-leakage: usar politica as-of pela data de divulgacao; forward-fill somente apos release oficial.)

### 1.6 Novas features derivadas (sem novas fontes)

#### Retorno e momentum multi-janela
- [x] `log_return_1d` (Anti-leakage: calcular somente com precos ate `t`; alvo deve permanecer em `t+h`.)
- [x] `log_return_5d` (Anti-leakage: janela trailing de 5 dias com dados `<= t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `log_return_21d` (Anti-leakage: janela trailing de 21 dias com dados `<= t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `momentum_5d` (Anti-leakage: calcular variacao acumulada apenas com historico `<= t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `momentum_21d` (Anti-leakage: calcular variacao acumulada apenas com historico `<= t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `momentum_63d` (Anti-leakage: calcular variacao acumulada apenas com historico `<= t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `reversal_1d` (Anti-leakage: derivar de retorno passado; nunca usar retorno futuro.)
- [x] `reversal_5d` (Anti-leakage: derivar de retorno passado; nunca usar retorno futuro. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `drawdown_lookback` (Anti-leakage: maximo rolling causal com historico `<= t`, sem olhar pico futuro. Warmup: entra na lista de `warmup_features` para validacao na selecao.)

#### Volatilidade robusta (OHLC)
- [x] `volatility_parkinson` (Anti-leakage: estimar em janela trailing usando OHLC `<= t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `volatility_garman_klass` (Anti-leakage: estimar em janela trailing usando OHLC `<= t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `downside_semivolatility` (Anti-leakage: usar apenas retornos passados na janela ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `vol_of_vol` (Anti-leakage: calcular sobre serie de volatilidade trailing ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)

#### Liquidez e impacto
- [x] `amihud_illiquidity_proxy` (`abs(return)/volume`) (Anti-leakage: usar retorno e volume observados ate `t`; sem usar barras futuras.)
- [x] `volume_zscore` (Anti-leakage: media/desvio em janela trailing fitada no passado; sem estatistica global com futuro. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `volume_spike_flag` (Anti-leakage: threshold calculado com historico ate `t` ou apenas treino do fold. Warmup: entra na lista de `warmup_features` para validacao na selecao.)

#### Regime de mercado
- [x] `volatility_regime` (`low/med/high`) (Anti-leakage: classificar regime com volatilidade trailing e limiares calibrados sem usar futuro. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `trend_regime` (ex.: slope/ma_spread) (Anti-leakage: usar indicadores causais `<= t`; sem regressao com janela centrada. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `stress_tail_return_flag` (Anti-leakage: flag baseada apenas em retornos passados na janela ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)

#### Dinamica de sentimento
- [x] `sentiment_lag_1` (Anti-leakage: lag estritamente passado com cutoff de publicacao ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `sentiment_lag_3` (Anti-leakage: lag estritamente passado com cutoff de publicacao ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `sentiment_lag_5` (Anti-leakage: lag estritamente passado com cutoff de publicacao ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `sentiment_ema` (Anti-leakage: EMA causal de sentimento usando somente serie disponivel ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `sentiment_surprise` (Anti-leakage: diferenca contra media movel trailing sem informacao futura. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `sentiment_x_volatility` (Anti-leakage: interacao entre componentes ja causais/as-of no instante `t`.)
- [x] `sentiment_x_volume` (Anti-leakage: interacao entre componentes ja causais/as-of no instante `t`.)

#### Ratios fundamentalistas derivados
- [x] `net_margin` (`net_income/revenue`) (Anti-leakage: ambos componentes com politica as-of por data de divulgacao.)
- [x] `leverage_ratio` (`total_liabilities/total_shareholder_equity`) (Anti-leakage: ambos componentes com politica as-of por data de divulgacao.)
- [x] `cashflow_efficiency` (`operating_cash_flow/revenue`) (Anti-leakage: ambos componentes com politica as-of por data de divulgacao.)
- [x] `revenue_yoy_growth` (Anti-leakage: crescimento calculado so com valores historicos ja divulgados ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)
- [x] `net_income_yoy_growth` (Anti-leakage: crescimento calculado so com valores historicos ja divulgados ate `t`. Warmup: entra na lista de `warmup_features` para validacao na selecao.)

## 2) Componente: Feature Selection/Config (`feature_set resolver`)

- [x] Selecionar feature sets por label canonico (`BASELINE_FEATURES`, `TECHNICAL_FEATURES`, `SENTIMENT_FEATURES`, `FUNDAMENTAL_FEATURES` e combinacoes).
- [x] Permitir combinacao de feature sets no treino/sweep.
- [x] Adicionar grupos canonicos para novas features derivadas (implementado: `MOMENTUM_LIQUIDITY_FEATURES`, `VOLATILITY_ROBUST_FEATURES`, `REGIME_FEATURES`, `SENTIMENT_DYNAMICS_FEATURES`, `FUNDAMENTAL_DERIVED_FEATURES`).
- [x] Validar compatibilidade de feature set com janela minima (warmup) antes do treino.
- [x] Registrar lista final ordenada de features usadas por run (para reproducao) + `feature_set_hash`.

### 2.1 Governanca de Warmup (definicao de referencia)

- [x] Definir arquivo de referencia `warmup_features` (por exemplo em schema/config): `feature_name -> warmup_count` (em barras).
- [x] Definir uma tabela canonica unica (single source of truth) `feature_name -> warmup_count`, versionada no repositorio.
- [ ] Manter `warmup_count` versionado e auditavel por feature (mudancas com changelog).
- [x] Definir regra para features sem warmup explicito: `warmup_count = 0`.
- [x] Expor no config de treino/sweep a politica de warmup: `strict_fail` ou `drop_leading`.
- [x] Na selecao de features, consolidar `required_warmup_count = max(warmup_count das features selecionadas)` para uso no treino.

## 3) Componente: Treino TFT (`main_train_tft` / sweeps)

- [x] Treinar com feature sets atuais (baseline/technical/sentiment/fundamental e combinacoes suportadas).
- [x] Habilitar novas features derivadas na pipeline de treino.
- [x] Salvar metadados de features por run (`feature_set_name`, `feature_list_ordered`, `feature_set_hash`).
- [x] Validar que o dataset possui todas as features esperadas antes de iniciar treino.
- [x] Expor flag/config para ativar subconjuntos de features derivadas por experimento.

### 3.1 Validacao operacional de warmup (etapa correta)

- [x] Executar a inspecao de warmup no inicio do treino/fold (apos carregar dataset e selecionar features).
- [x] Calcular `effective_train_start` a partir dos leading nulls reais das `warmup_features` selecionadas.
- [x] Se `effective_train_start > train_start`:
  - [x] `strict_fail`: abortar treino com erro orientativo.
  - [x] `drop_leading`: ajustar janela e continuar treino.
- [x] Revalidar amostras minimas por split apos ajuste de warmup; falhar se insuficiente.
- [x] Persistir no metadata do run: `warmup_policy`, `required_warmup_count`, `effective_train_start`, `warmup_applied`.
- [x] Persistir no metadata do run: `feature_list_ordered` (ordem exata usada no treino).

## 4) Componente: Inferencia TFT (`main_tft_inference_pipeline`)

- [x] Inferir com as features do modelo treinado.
- [x] Validar 100% de compatibilidade entre feature list do modelo e colunas do dataset de inferencia.
- [x] Emitir diagnostico claro de colunas faltantes/excedentes.

## 5) Componente: Qualidade e Validacao de Features

- [x] Testes unitarios por calculadora de feature (incluindo bordas de janela).
- [x] Testes de leak temporal para features com rolling/lag.
- [x] Teste de determinismo de features (mesma entrada => mesma saida).
- [x] Testes de schema (tipos, nulos, ordenacao temporal, colunas obrigatorias).
- [x] Validacao de warmup por feature set (strict_fail e drop_leading).
- [x] Quality gate pre-treino minimo: `%NaN` por feature, cobertura temporal minima e ausencia de duplicatas de `timestamp`.

## 6) Componente: Documentacao

- [x] Documentar definicao matematica de cada nova feature.
- [x] Documentar janela minima necessaria por feature/grupo.
- [x] Documentar riscos de leakage e como foram mitigados.
- [x] Atualizar guias de execucao (`RUNNING_PIPELINE.md`, `RUNNING_TESTS.md`) com exemplos por feature set.

### 6.1 Definicoes matematicas (novas features)

#### Retorno, momentum e liquidez
- `log_return_1d = log(close_t / close_{t-1})`
- `log_return_5d = log(close_t / close_{t-5})`
- `log_return_21d = log(close_t / close_{t-21})`
- `momentum_5d = close_t / close_{t-5} - 1`
- `momentum_21d = close_t / close_{t-21} - 1`
- `momentum_63d = close_t / close_{t-63} - 1`
- `reversal_1d = -pct_change_1d(close)`
- `reversal_5d = -momentum_5d`
- `drawdown_lookback = close_t / max(close_{t-62...t}) - 1`
- `amihud_illiquidity_proxy = abs(pct_change_1d(close_t)) / volume_t`
- `volume_zscore = (volume_t - mean(volume_{t-20...t-1})) / std(volume_{t-20...t-1})`
- `volume_spike_flag = 1{volume_zscore > 3.0}`

#### Volatilidade robusta e regimes
- `volatility_parkinson = sqrt(mean((log(high/low))^2, janela=20) / (4*log(2)))`
- `volatility_garman_klass = sqrt(mean(0.5*(log(high/low))^2 - (2*log(2)-1)*(log(close/open))^2, janela=20))`
- `downside_semivolatility = sqrt(mean(min(ret_1d, 0)^2, janela=20))`
- `vol_of_vol = std(volatility_20d, janela=20)`
- `volatility_regime in {0,1,2}` por tercis de volatilidade trailing (janela=63, shift=1)
- `trend_regime in {-1,0,1}` por spread `ema_10-ema_50` com deadband trailing (janela=63, shift=1)
- `stress_tail_return_flag = 1{ret_1d <= q10(ret_1d trailing 63, shift=1)}`

#### Dinamica de sentimento
- `sentiment_lag_k = sentiment_score.shift(k)` para `k in {1,3,5}`
- `sentiment_ema = ewm(sentiment_score, span=10, adjust=False)`
- `sentiment_surprise = sentiment_score_t - mean(sentiment_score_{t-5...t-1})`
- `sentiment_x_volatility = sentiment_score * volatility_20d`
- `sentiment_x_volume = sentiment_score * volume`

#### Fundamental derivado
- `net_margin = net_income / revenue` (safe ratio)
- `leverage_ratio = total_liabilities / total_shareholder_equity` (safe ratio)
- `cashflow_efficiency = operating_cash_flow / revenue` (safe ratio)
- `revenue_yoy_growth = pct_change(revenue, 252)`
- `net_income_yoy_growth = pct_change(net_income, 252)`

### 6.2 Warmup minimo por grupo (referencia operacional)

- `TECHNICAL_FEATURES`: depende da maior janela selecionada (ex.: `ema_200` => 200).
- `MOMENTUM_LIQUIDITY_FEATURES`: ate `63` (por `momentum_63d`/`drawdown_lookback`).
- `VOLATILITY_ROBUST_FEATURES`: ate `20`.
- `REGIME_FEATURES`: ate `63` (limiares trailing de regime).
- `SENTIMENT_DYNAMICS_FEATURES`: ate `20` (interacao com `volatility_20d`), e lags/medias menores.
- `FUNDAMENTAL_DERIVED_FEATURES`: ate `252` (YoY), quando selecionado.

Regra aplicada no treino: `required_warmup_count = max(warmup_count das features selecionadas)`.
Politicas: `strict_fail` (falha) e `drop_leading` (ajusta `effective_train_start`).

### 6.3 Riscos de leakage e mitigacoes

- Risco: usar janela centrada/global para estatisticas de rolling.
Mitigacao: somente janelas trailing causais (`<= t`) e, quando necessario, `shift(1)` para limiares.
- Risco: usar dados de noticia/fundamental antes da divulgacao.
Mitigacao: politica as-of por `reported_date` e cutoff via `close_hour` na definicao de dia util.
- Risco: target contaminado por input futuro.
Mitigacao: `target_return` deslocado para horizonte futuro; features calculadas apenas com passado/presente.
- Risco: inferencia com colunas diferentes das usadas no treino.
Mitigacao: validacao de compatibilidade 100% no pipeline de inferencia.

## Prioridade sugerida (execucao)

### Fase A (rapido impacto)
- [x] Retornos/momentum multi-janela
- [x] Liquidez/volume (`amihud`, `volume_zscore`, `volume_spike_flag`)

### Fase B (robustez)
- [x] Volatilidade robusta (Parkinson/Garman-Klass)
- [x] Regimes de mercado
- [x] Dinamica de sentimento (lags/ema/surprise/interacoes)

### Fase C (fundamental avancado)
- [x] Ratios e crescimento YoY
