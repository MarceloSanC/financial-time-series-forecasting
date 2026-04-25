# → CHECKLISTS (DETAILED) USED IN EACH DEVELOPMENT PHASE

Direcionamento estrategico atual (supersede o antigo checklist pos-rodada):
`docs/00_overview/STRATEGIC_DIRECTION.md`

# → CHECKLIST Etapas MVP

- [x] **Etapa 0: Setup e Validação do Ambiente**

**Objetivo**: Garantir que o ambiente está configurado, documentado e reproduzível.

**Componentes**:

- `setup.ps1`, `Makefile`, `pyproject.toml`, `GIT_GUIDE.md`, `docs/`
- Ambiente virtual com dependências (`torch`, `pytorch-forecasting`, `yfinance`, `pytest`, `ruff`, `black`)

**Critério de aceite**:

- [x] `make test` roda sem erro (mesmo com 0 testes)
- [x] `make format` e `make lint` executam sem falha
- [x] `python -c "import pytorch_forecasting"` funciona

**Justificativa (TCC)**:

> Reprodutibilidade é condição necessária para validação científica (Peng, 2011). A automação via Makefile e configuração declarativa em pyproject.toml garantem que o experimento possa ser replicado por terceiros.

---

- [x] **Etapa 1: Domínio (Entidades e Interfaces)**

**Objetivo**: Estabelecer o núcleo conceitual do sistema, independente de tecnologia.

**Componentes**:

- [x] `src/entities/candle.py` (`Candle`)
- [x] `src/entities/news_article.py` (`NewsArticle`)
- [x] `src/entities/scored_news_article.py` (`ScoredNewsArticle`)
- [x] `src/entities/daily_sentiment.py` (`DailySentiment`)
- [x] `src/entities/technical_indicator_set.py` (`TechnicalIndicatorSet`)
- [x] Interfaces: `CandleRepository`, `NewsRepository`, `ScoredNewsRepository`, `SentimentModel`, `TechnicalIndicatorRepository`

**Critério de aceite**:

- [x] Entidades são `@dataclass(frozen=True)`
- [x] Interfaces são abstratas (`ABC`) com métodos assinados
- [x] Nenhuma dependência externa (ex: `pandas`, `requests`) nas camadas internas

**Justificativa (TCC)**:

> A Clean Architecture (Martin, 2017) propõe que o domínio seja independente de frameworks e infraestrutura. Isso aumenta a testabilidade e facilita a manutenção — critérios essenciais em sistemas de decisão financeira (IEEE Std 1012-2016).

---

- [x] **Etapa 2: Coleta e Persistência de Preços (OHLCV)**

**Objetivo**: Coletar e persistir candles diários de forma robusta, testável e idempotente.

**Componentes**:

- [x] `src/adapters/yfinance_candle_fetcher.py`
- [x] `src/adapters/parquet_candle_repository.py`
- [x] `src/use_cases/fetch_candles_use_case.py`
- [x] `src/main_candles.py`
- [x] `config/data_sources.yaml`

**Critério de aceite**:

- [x] `python -m src.main_candles --asset AAPL` gera `data/raw/market/candles/{ASSET}/candles_{ASSET}_1d.parquet`
- [x] Colunas: `timestamp`, `open`, `high`, `low`, `close`, `volume`
- [x] Tipos coerentes (`float32`, `int64`, `datetime64[ns, UTC]`)
- [x] Suporta retries e backoff exponencial
- [x] Testes unitários com mocks passam

**Justificativa (TCC)**:

> A qualidade dos dados é o principal fator de sucesso em modelos preditivos (Dhar, 2013). A persistência em Parquet assegura eficiência, preservação de tipos e compatibilidade com fluxos de ML (Zaharia et al., 2018).

---

- [x] **Etapa 3: Indicadores Técnicos (a partir de OHLCV)**

**Objetivo**: Calcular indicadores técnicos brutos para uso posterior no dataset do TFT.

**Componentes**:

- [x] `src/adapters/technical_indicator_calculator.py`
- [x] `src/adapters/parquet_technical_indicator_repository.py`
- [x] `src/use_cases/technical_indicator_engineering_use_case.py`
- [x] `src/main_technical_indicators.py`

**Critério de aceite**:

- [x] Gera `data/processed/technical_indicators/{ASSET}/technical_indicators_{ASSET}.parquet`
- [x] Formato wide: uma linha por `timestamp`
- [x] Colunas de indicadores consistentes e dtypes válidos
- [x] Ordenação temporal garantida

**Justificativa (TCC)**:

> Indicadores técnicos sintetizam padrões de tendência, momentum e volatilidade e são inputs clássicos para modelos de séries financeiras. Separar indicadores de features finais evita vazamento conceitual e facilita extensão futura.

---

- [x] **Etapa 4: Coleta de Notícias (raw)**

**Objetivo**: Coletar e persistir notícias brutas do ativo, de forma incremental e auditável.

**Componentes**:

- [x] `src/adapters/finnhub_news_fetcher.py`
- [x] `src/adapters/alpha_vantage_news_fetcher.py`
- [x] `src/adapters/parquet_news_repository.py`
- [x] `src/use_cases/fetch_news_use_case.py`
- [x] `src/main_news_dataset.py`

**Critério de aceite**:

- [x] Gera `data/raw/news/{ASSET}/news_{ASSET}.parquet`
- [x] Suporta incremental com cursor e dedup
- [x] Campos de domínio validados (URL, published_at UTC, source)

**Justificativa (TCC)**:

> A separação entre dados brutos e processados preserva auditabilidade e reprocessamento controlado — requisito central em pipelines de dados financeiros.

---

- [x] **Etapa 5: Sentimento (scoring + agregação diária)**

**Objetivo**: Inferir sentimento por notícia e agregar por dia para uso no dataset do TFT.

**Componentes**:

- [x] `src/adapters/finbert_sentiment_model.py`
- [x] `src/use_cases/infer_sentiment_use_case.py`
- [x] `src/use_cases/sentiment_feature_engineering_use_case.py`
- [x] `src/adapters/parquet_scored_news_repository.py`
- [x] `src/adapters/parquet_daily_sentiment_repository.py`
- [x] `src/domain/services/sentiment_aggregator.py`
- [x] `src/main_sentiment.py`
- [x] `src/main_sentiment_features.py`

**Critério de aceite**:

- [x] `sentiment_score` varia entre `-1.0` (negativo) e `+1.0` (positivo)
- [x] Scoring gera `data/processed/scored_news/{ASSET}/scored_news_{ASSET}.parquet`
- [x] Reprocessamento é idempotente por `article_id`
- [x] Agregação diária persiste `data/processed/sentiment_daily/{ASSET}/daily_sentiment_{ASSET}.parquet`
- [x] Cada dia contém `sentiment_score` agregado e `news_volume`
- [x] Agregação diária determinística (mesmo input → mesmo output)
- [x] Validação explícita de causalidade: sentimento diário usa apenas notícias do próprio dia (sem notícia futura)

**Justificativa (TCC)**:

> Estudos empíricos demonstram que sentimento coletivo explica parte da volatilidade não capturada por indicadores técnicos (Bollen et al., 2011; Oliveira et al., 2023). A agregação diária reduz ruído e alinha horizonte com candles diários.

---

- [x] **Etapa 6: Indicadores Fundamentalistas**

**Objetivo**: Coletar indicadores fundamentalistas para enriquecer o dataset do TFT.

**Componentes**:

- [x] Adapter de fundamentals (Alpha Vantage)
- [x] Repositório parquet dedicado (processed)
- [x] Use case e orquestrador CLI (`main_fundamentals`)

**Critério de aceite**:

- [x] Dataset fundamentalista salvo com schema estável
- [x] Alinhamento temporal com candles e sentimento

**Justificativa (TCC)**:

> Variáveis fundamentalistas adicionam informação macro e microeconômica ao modelo, complementando sinais técnicos e de sentimento.

---

- [x] **Etapa 7: Pré-processamento e Dataset TFT**

**Objetivo**: Unificar candles, indicadores técnicos, sentimento agregado e fundamentals em um dataset de treino do TFT.

**Componentes**:

- [x] `BuildTFTDatasetUseCase` (join e alinhamento temporal)
- [x] Normalização/escala por janela temporal
- [x] Geração de alvo (`t+1` retorno) e lags
- [x] Persistência `data/processed/dataset_tft/{ASSET}/dataset_tft_{ASSET}.parquet`

**Critério de aceite**:

- [x] Dataset contém features sincronizadas e alvo
- [x] Sem leakage temporal
- [x] Schema consistente e validado
- [x] Política explícita de missing por feature (ex.: `news_volume=0`, `sentiment_score/sentiment_std=0` + `has_news`) 
- [x] Validador de warmup para detectar e alertar `null` iniciais por feature no período de treino

**Justificativa (TCC)**:

> A preparação correta do dataset evita vieses de look-ahead e garante que o TFT receba sinais coerentes no tempo.

---

- [x] **Etapa 8: Treinamento do TFT e Análise de Features**

**Objetivo**: Treinar o modelo e produzir análises de contribuição de features.

**Componentes** (planejados):

- [x] Adapter de treino TFT (pytorch-forecasting)
- [x] Use case de treino e validação temporal
- [x] Estratégia de experimentos para relevância (ablação + permutation importance)

**Critério de aceite**:

- [x] Treina modelo com alvo `retorno_t+1`
- [x] Avalia em test e salva métricas separadas (`train`, `val`, `test`)
- [x] Salva checkpoint e artefatos (scalers, config, `metadata.json` com split efetivo)
- [x] Relatório de importância das features
- [x] Split temporal (train/val/test) sem leakage
- [x] Normalização ajustada no treino e aplicada no val/test
- [x] Early stopping + checkpoint do melhor `val_loss`
- [x] Relevância em duas camadas: ablação controlada (baseline vs +sentimento vs +fundamentals) e permutation importance no conjunto de teste
- [x] Exporta artefatos de análise (`feature_importance.csv`, gráfico comparativo por experimento)

**Justificativa (TCC)**:

> A interpretabilidade é requisito em finanças para validar se o modelo aprendeu relações plausíveis, não apenas correlações espúrias.

---

- [x] **Etapa 9: Análise do Modelo e Sensibilidade de Hiperparâmetros**

**Objetivo**: Executar análise sistemática do modelo treinado para apoiar seleção de configuração.

**Componentes**:

- [x] Use case modular de análise de modelo (`RunTFTModelAnalysisUseCase`)
- [x] Serviço de domínio para geração de experimentos one-at-a-time
- [x] Adapter de execução de treino via CLI para runs controlados
- [x] Orquestrador CLI (`main_model_analysis`), mantendo compatibilidade com `main_tft_param_sweep`

**Critério de aceite**:

- [x] Executa baseline + variações de hiperparâmetros em runs independentes
- [x] Consolida resultados em artefatos comparativos (`sweep_runs`, ranking e impacto por parâmetro)
- [x] Gera `summary.json` com melhor run e métricas de referência

**Justificativa (TCC)**:

> A análise estruturada de sensibilidade reduz overfitting de configuração e torna a escolha de hiperparâmetros mais transparente e reprodutível.

---

- [x] **Etapa 10: Inferência do Modelo em Novos Dados**

**Objetivo**: Executar inferência com o modelo treinado em dados novos e registrar outputs.

**Componentes** (planejados):

- [x] Pipeline de inferência (candles → features → previsão)
- [x] Persistência de previsões e metadados

**Critério de aceite**:

- [x] Gera previsões para janelas recentes
- [x] Loga confiança/quantis do TFT

**Justificativa (TCC)**:

> A inferência operacional valida o uso do modelo em ambiente próximo ao real e permite avaliação contínua de performance.

# → Checklist de Features por Use Case/Componente

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

# → Analytics Store Checklist (DuckDB + Parquet)

Objetivo: coletar dados suficientes para analises futuras sem retraining, em 3 niveis:
- run-level
- epoch-level
- timestamp-level (OOS alinhado)

Legenda de prioridade para implementacao:
- `P0` = indispensavel para defensabilidade academica (v0 obrigatorio)
- `P1` = muito recomendavel (v0 alvo, pode fechar logo apos P0)
- `P2` = pos-v0 (nao bloqueia analises robustas sem retrain)

---

## Decisoes Fechadas (Contrato v0)

- [x] `run_id` = `sha256(asset|feature_set_hash|trial_number|fold|seed|model_version|config_signature|split_signature|pipeline_version)` em JSON canonico.
- [x] `partial_failed` = treino concluiu, mas faltou pelo menos 1 artefato obrigatorio (ex.: sem `fact_oos_predictions` ou sem `fact_epoch_metrics`).
- [x] `schema_version` = coluna obrigatoria em toda `dim_*`/`fact_*`, iniciando em `1`.
- [x] `feature_set_hash` = `sha256("|".join(features_ordered))`.
- [x] `dataset_fingerprint` = `sha256(asset, timestamp_min, timestamp_max, row_count, close_sum, volume_sum, parquet_file_hash)`.
- [x] `split_fingerprint` = `sha256` das listas de timestamps ordenadas por split (`train|val|test`).
- [x] `config_signature` = `sha256(training_config canonico sem campos volateis)`.
- [x] `fact_oos_predictions` grao/PK logica = `run_id + split + horizon + timestamp + target_timestamp`.
- [x] Particionamento Parquet:
- [x] `dim_run`, `fact_config`, `fact_run_snapshot` => `asset/sweep_id`.
- [x] `fact_epoch_metrics` => `asset/sweep_id/fold`.
- [x] `fact_oos_predictions` => `asset/feature_set_name/year`.
- [x] Campos obrigatorios = ids, chaves temporais, metricas core, status, quantis, attention.
- [x] Campos opcionais = hardware detalhado, logs extensos.
- [x] Tipos canonicos: `timestamps` em UTC ISO8601; metricas `float64`; contagens `int64`; ids/status/chaves `string`.
- [x] Nulabilidade: `run_id` nunca nulo; `execution_id` nulo permitido em P0.
- [x] Alinhamento OOS = join por `asset + split + horizon + target_timestamp`; descartar pares incompletos para testes pareados.
- [x] Update policy: `dim_run` upsert por `run_id`; tabelas fato append-only por padrao; upsert apenas em reprocessamento explicito.
- [x] Retencao/backup: Silver Parquet com retencao total em v0; DuckDB reconstruivel com backup diario opcional.
- [x] Escopo Gold P1: `gold_runs_long`, `gold_oos_consolidated`, `vw_runs_latest`, `vw_fold_seed_metrics`, `vw_oos_aligned_pairs`.

---

## Stage 0 - Contrato e Escopo (obrigatorio antes de implementar)

- [x] `[P0]` Definir `run_id` como identidade logica deterministica.
- [ ] `[P2]` Definir `execution_id` como identidade fisica por execucao (UUID).
- [ ] `[P2]` Definir relacao oficial `execution_id -> run_id` (many-to-one).
- [x] `[P0]` Definir status canonicos de execucao: `ok`, `failed`, `partial_failed`.
- [x] `[P1]` Definir `schema_version` por tabela.
- [x] `[P0]` Definir Parquet (`silver`) como source of truth.
- [x] `[P0]` Definir DuckDB como camada derivada/reconstruivel.
- [x] `[P0]` Definir contrato de `feature_set_name`.
- [x] `[P0]` Definir contrato da lista de features com ordem preservada.
- [x] `[P0]` Definir contrato de `feature_set_hash` (hash da lista ordenada de features).
- [x] `[P0]` Definir contrato de `prediction_mode` por run: `point` ou `quantile`.
- [x] `[P0]` Definir politica default: `prediction_mode=quantile` (point permitido apenas por override explicito).
- [x] `[P0]` Definir quantis e attention como campos obrigatorios para analise comparativa oficial.

---

## Stage 1 - Coleta Run-Level (identidade, config, snapshot, falhas)

### 1.1 Identidade e rastreabilidade do experimento

- [x] `[P0]` Salvar `run_id`, `parent_sweep_id`, `trial_number`, `fold`, `seed`, `asset`.
- [x] `[P0]` Salvar `feature_set_name` e lista exata de features usadas (ordem preservada).
- [x] `[P0]` Salvar `feature_set_hash` por run para rastreabilidade de combinacao exata de features.
- [x] `[P0]` Salvar `model_version`.
- [x] `[P1]` Salvar `checkpoint_path_final` e `checkpoint_path_best`.
- [x] `[P1]` Salvar `git_commit`, `pipeline_version`, `created_at_utc`.
- [x] `[P1]` Salvar versao das libs: torch, lightning, pytorch-forecasting, pandas e dependencias criticas.
- [x] `[P1]` Salvar hardware: CPU/GPU, nome da placa, memoria.

### 1.2 Snapshot de dados e splits

- [x] `[P0]` Salvar intervalo temporal total do dataset usado.
- [x] `[P0]` Salvar `train_start/end`, `val_start/end`, `test_start/end` efetivos.
- [x] `[P0]` Salvar politica de warmup (`strict_fail`/`drop_leading`) e datas ajustadas.
- [x] `[P0]` Salvar numero de amostras por split e por fold.
- [x] `[P0]` Salvar hash/fingerprint do dataset.
- [x] `[P0]` Salvar hash/fingerprint dos splits.
- [x] `[P1]` Salvar lista de timestamps por split ou referencia reproduzivel.

### 1.3 Configuracao completa de treino

- [x] `[P0]` Salvar hiperparametros finais do modelo.
- [x] `[P0]` Salvar search space (quando Optuna).
- [x] `[P0]` Salvar objetivo de otimizacao e funcao de score.
- [x] `[P0]` Salvar early stopping params, batch size, max epochs, learning rate.
- [x] `[P1]` Salvar parametros de normalizacao/scalers.
- [x] `[P0]` Salvar `dataset_parameters` completos do TimeSeriesDataSet.
- [x] `[P0]` Salvar `config_json` completo serializado.
- [x] `[P0]` Salvar `prediction_mode` e loss usada no treino.
- [x] `[P0]` Salvar lista de quantis treinados (ex.: `[0.1, 0.5, 0.9]`) quando `prediction_mode=quantile`.
- [x] `[P0]` Garantir que configs default de treino/sweep publiquem `prediction_mode=quantile`.

### 1.4 Metadados de execucao e falhas

- [x] `[P0]` Salvar status por run (`ok`, `failed`, `partial_failed`).
- [x] `[P0]` Salvar traceback/erro resumido quando falha.
- [x] `[P1]` Salvar `cmdline`/`entrypoint`.
- [x] `[P2]` Salvar `stdout/stderr` truncados.
- [x] `[P1]` Salvar duracao total de execucao.
- [x] `[P2]` Salvar ETA estimado registrado (quando houver).
- [x] `[P2]` Salvar numero de tentativas/retries.

---

## Stage 2 - Coleta Epoch-Level

- [x] `[P0]` Salvar `train_loss`, `val_loss` por epoca.
- [x] `[P0]` Salvar `best_epoch`.
- [x] `[P0]` Salvar `stopped_epoch`.
- [x] `[P0]` Salvar `early_stop_reason`.
- [x] `[P1]` Salvar tempo por epoca.
- [x] `[P1]` Salvar tempo total de treino.
- [x] `[P1]` Salvar curva de convergencia reproduzivel.

---

## Stage 3 - Coleta Timestamp-Level (OOS essencial)

- [x] `[P0]` Salvar por timestamp: `y_true`, `y_pred`.
- [x] `[P0]` Salvar por timestamp: `error`, `abs_error`, `sq_error`.
- [x] `[P0]` Salvar identificadores por linha: `run_id`, `fold`, `seed`, `config_id/signature`, `feature_set`, `asset`.
- [x] `[P0]` Salvar `horizon` e `target_timestamp` para multi-horizonte.
- [x] `[P0]` Salvar quantis TFT (`p10`, `p50`, `p90` ou lista configurada) como obrigatorios no OOS.
- [x] `[P0]` Garantir alinhamento temporal OOS entre modelos para DM/MCS.
- [x] `[P0]` Politica default de coleta timestamp-level: persistir apenas `val/test` (split `train` opcional via `evaluate_train_split=true` para diagnostico in-sample).

---

## Stage 4 - Artefatos e Estruturas Analiticas Pre-Prontas

### 4.1 Artefatos de modelo

- [x] `[P1]` Salvar checkpoint e config serializada.
- [x] `[P1]` Salvar scalers/encoders versionados.
- [x] `[P0]` Salvar feature importance/attention.
- [x] `[P0]` Politica de performance v0: `compute_feature_importance=false` por padrao em sweeps optuna; habilitar em rerun dedicado/top-k para reduzir latencia pos-treino sem perder analise final.
- [x] `[P0]` Fluxo recomendado de interpretabilidade: executar sweeps com `compute_feature_importance=false` e depois rerodar apenas `top3` por `feature_set` via `explicit_configs` com `compute_feature_importance=true`.
- [x] `[P2]` Salvar historico de treino e referencias de logs estruturados.

### 4.2 Estruturas para analise posterior

- [x] `[P0]` Disponibilizar tabela longa de runs (`config x fold x seed`).
- [x] `[P2]` Disponibilizar tabela de ranking por config.
- [x] `[P2]` Disponibilizar tabela de impacto por grupo de feature set (agregado por fold/seed e metrica).
- [x] `[P2]` Disponibilizar tabela de consistencia top-k.
- [x] `[P2]` Disponibilizar tabela de IC95 por metrica/config.
- [x] `[P1]` Disponibilizar tabela consolidada de predições OOS.

---

## Stage 5 - Qualidade de Dados e Validacoes

- [x] `[P0]` Validar unicidade e consistencia de `run_id` e `execution_id` (quando existir).
- [x] `[P0]` Validar integridade referencial entre fatos e dimensoes.
- [x] `[P0]` Validar ausencia de NaN em metricas obrigatorias.
- [x] `[P0]` Validar consistencia temporal dos timestamps.
- [x] `[P0]` Validar cardinalidade esperada (`config x fold x seed`).
- [x] `[P0]` Validar minimos por split (`n_samples >= contexto`).
- [x] `[P0]` Validar contratos obrigatorios de quantis/attention para runs oficiais.
- [ ] `[P2]` Publicar relatorio automatico de qualidade por ingestao em `gold`.
- [x] `[P1]` Suportar `fail-on-quality` para CI/CD.

---

## Stage 6 - CI/CD e Operacao Escalavel

### 6.1 CI por estagios

- [x] `[P1]` Rodar `lint + type + unit` em todo PR.
- [x] `[P1]` Rodar testes de integracao de escrita Parquet + refresh DuckDB.
- [x] `[P1]` Rodar contract-tests de schema.
- [x] `[P1]` Rodar quality gate com dataset sintetico.

### 6.2 CD e operacao

- [ ] `[P2]` Gerar artefatos `gold` em toda execucao relevante.
- [ ] `[P2]` Versionar SQLs analiticos em pacote estavel.
- [ ] `[P2]` Definir rollback (rebuild DuckDB a partir de Parquet).
- [ ] `[P2]` Definir backup e retencao de Parquet + DuckDB.
- [ ] `[P2]` Garantir `.duckdb` e Parquet volumosos fora do Git.
- [ ] `[P2]` Definir ownership tecnico (schema, ingestao, qualidade, operacao).
- [ ] `[P2]` Documentar runbook de troubleshooting.

---

## Definition of Done (Sem Retraining para Analises Planejadas)

- [x] `[P0]` Todos os dados de run-level, epoch-level e timestamp-level estao persistidos.
  1. Execute um treino real: `python -m src.main_train_tft --asset AAPL --features BASELINE_FEATURES,TECHNICAL_FEATURES`.
  2. Valide existencia de parquet com linhas em `dim_run`, `fact_config`, `fact_run_snapshot`, `fact_split_metrics`, `fact_epoch_metrics`, `fact_oos_predictions`, `fact_model_artifacts`, `bridge_run_features`.
  3. Aceite: todas as tabelas acima possuem ao menos 1 `run_id` do treino executado.
- [x] `[P0]` Configuracao, dataset snapshot e artefatos permitem reproducao auditavel.
  1. No `run_id` do treino, valide preenchimento de: `training_config_json`, `dataset_parameters_json`, `dataset_fingerprint`, `split_fingerprint`, `feature_set_hash`, `model_version`, `checkpoint_path_best/final`.
  2. Rode inferencia com o mesmo modelo: `python -m src.main_infer_tft --asset AAPL --model-path <MODEL_DIR> --start 20260101 --end 20260228`.
  3. Aceite: inferencia executa sem erro de contrato de dataset/feature e gera previsoes para o mesmo `asset`.
- [x] `[P0]` OOS alinhado permite DM/MCS e comparacoes pareadas sem retrain.
  1. Garanta pelo menos 2 `run_id` com mesmo `asset/split/horizon`.
  2. Execute refresh: `python -m src.main_refresh_analytics_store --fail-on-quality`.
  3. Valide no `gold_oos_consolidated.parquet` que existe intersecao por `asset + split + horizon + target_timestamp`.
  4. Aceite: para cada par de modelos comparados, existem pares completos (sem faltantes) apos alinhamento temporal.
- [x] `[P1]` Tabelas pre-prontas para ranking, robustez, consistencia e IC95 estao disponiveis.
  1. Execute refresh: `python -m src.main_refresh_analytics_store`.
  2. Valide existencia dos arquivos: `gold_ranking_by_config.parquet`, `gold_consistency_topk.parquet`, `gold_ic95_by_config_metric.parquet`, `gold_runs_long.parquet`, `gold_oos_consolidated.parquet`.
  3. Aceite: todos os arquivos existem e possuem pelo menos 1 linha.
- [x] `[P1]` Pipeline validado em CI com qualidade controlada e rastreabilidade completa.
  1. Local: `source .venv/bin/activate && make ci-local`.
  2. Remoto: abrir PR e confirmar jobs verdes em `.github/workflows/ci.yml` (`lint-type-unit` e `analytics-contract-and-quality`).
  3. Aceite: CI verde no PR e sem falha no `--fail-on-quality`.

---

## Referencia de Estruturas de Schema (Engenharia de Dados)

### Silver (fonte canonica em Parquet)

1. `dim_run`
- PK logica: `run_id`.
- Identidade fisica: `execution_id` (unico por tentativa).
- Campos: `parent_sweep_id`, `trial_number`, `fold`, `seed`, `asset`, `feature_set_name`,
  `model_version`, `checkpoint_path_final`, `checkpoint_path_best`, `git_commit`,
  `pipeline_version`, `created_at_utc`, `library_versions_json`, `hardware_info_json`,
  `status`, `duration_total_seconds`, `eta_recorded_seconds`, `retries`.

2. `fact_run_snapshot`
- FK: `run_id`.
- Campos: intervalo total do dataset, `train/val/test start/end` efetivos,
  politica e ajuste de warmup, `n_samples` por split/fold, `dataset_fingerprint`,
  `split_fingerprint`.

3. `fact_config`
- FK: `run_id`.
- Campos: hiperparametros finais, search space/objetivo (quando Optuna), early stopping,
  parametros de normalizacao/scalers, `dataset_parameters`, `config_json`,
  `prediction_mode`, `loss_name`, `quantile_levels` (quando aplicavel).

4. `fact_split_metrics`
- FK: `run_id`.
- Grao: `run_id + split`.
- Campos: RMSE, MAE, MAPE/sMAPE (quando aplicavel), DA, `n_samples`.

5. `fact_epoch_metrics`
- FK: `run_id`.
- Grao: `run_id + epoch`.
- Campos: `train_loss`, `val_loss`, `epoch_time_seconds`, `best_epoch`, `stopped_epoch`,
  `early_stop_reason`.

6. `fact_oos_predictions`
- FK: `run_id`.
- Grao: `run_id + split + horizon + timestamp + target_timestamp`.
- Campos: `y_true`, `y_pred`, `error`, `abs_error`, `sq_error`, `target_timestamp`.
- Quantis (`p10/p50/p90` ou lista configurada): obrigatorios.

7. `fact_model_artifacts` (`P0`)
- FK: `run_id`.
- Campos: paths de checkpoint/config/scalers/encoders, importance/attention (obrigatorios), referencias de logs.

8. `fact_failures` (`P0`)
- FK: `run_id` (nullable quando falha pre-run), `execution_id`.
- Campos: stage, erro resumido, traceback/hash, timestamp.
- Pos-v0 (`P2`): `cmdline`, `stdout/stderr` truncados.

9. `fact_inference_runs` (`P1`)
- FK: `run_id` (ou referencia consistente com `model_version`/`inference_run_id`).
- Campos: janela de inferencia, overwrite, batch, status, contadores
  (`inferred/skipped/upserts`), duracao.

10. `bridge_run_features` (`P0`)
- FK: `run_id`.
- Grao: `run_id + feature_order`.
- Campos: `feature_name`, `feature_order` (preserva ordem exata).

11. `fact_split_timestamps_ref` (`P1`)
- FK: `run_id`.
- Campos: `split`, referencia reproduzivel para timestamps (`artifact_path`/hash/lista compacta).

### Gold (camada analitica pronta para consumo)

- `gold_runs_long` (`config x fold x seed`) (`P1`).
- `gold_oos_consolidated` (`P1`).
- `gold_paired_oos_intersection_by_horizon` (`P0`): incluir `n_common`, `n_union`, `coverage_ratio`, `aligned_exact` por coorte comparavel (sweep/split_signature/split/horizon).
- `gold_ranking_by_config` (`P2`).
- `gold_consistency_topk` (`P2`).
- `gold_ic95_by_config_metric` (`P2`).

### Relacionamento principal

- `dim_run` e dimensao central.
- Todas as `fact_*` fazem join primario por `run_id`.
- `execution_id` separa tentativas fisicas de um mesmo `run_id`.
- `asset/feature_set/fold/seed/trial_number` devem ser materializados onde fizer sentido
  para consultas analiticas com menos joins.

# → Predictions and Metrics Checklist (Inference Output - Y)

Objetivo: definir, de forma canonica, os dados de saida do modelo (Y) necessarios para analise interpretavel, estimativa estatistica de retorno esperado e comparacao robusta entre modelos sem retraining.

## Escopo

Este documento cobre:
- saidas de inferencia/predicao do modelo (dados primarios)
- estrutura para metricas e testes estatisticos (dados derivados)
- suporte multi-horizonte (h+1, h+7, h+30)
- explicabilidade da previsao (global e local)

Nao cobre:
- features de entrada (X)
- setup/metadados de treino em detalhe (ver `ANALYTICS_STORE_CHECKLIST.md`)

---

## 0) Resultado Esperado Em Producao

- [x] Para cada inferencia, gerar retorno previsto para `h+1`, `h+7`, `h+30` (quando habilitados no run).
- [x] Para cada horizonte, salvar previsao probabilistica minima (`p10`, `p50`, `p90`).
- [ ] Fornecer grau de certeza calibrado (nao apenas score unico), baseado em intervalo + calibracao historica.
- [x] Fornecer explicabilidade global por feature (importancia media por periodo/run).
- [x] Fornecer explicabilidade local por inferencia (`timestamp`) com contribuicao por feature.

---

## 1) Predicoes Primarias (dados brutos do modelo)

### 1.0 Politica de horizontes (multi-horizonte)
- [x] Habilitar e padronizar horizontes de interesse: `h+1`, `h+7`, `h+30`.
- [x] Permitir configuracao explicita dos horizontes por experimento.
- [x] Registrar horizontes efetivamente usados em cada run.

### 1.1 Chaves de identificacao por linha de predicao
- [x] `run_id`
- [x] `model_version`
- [x] `asset`
- [x] `feature_set_name`
- [x] `fold`
- [x] `seed`
- [x] `split` (`train|val|test|inference`)
- [x] `config_id` (ou assinatura canonica da config)

### 1.2 Chaves temporais
- [x] `timestamp` (instante da observacao/entrada)
- [x] `horizon` (obrigatorio para multi-horizonte)
- [x] `target_timestamp` (timestamp alvo previsto)

### 1.3 Valores alvo/predicao
- [x] `y_true` (quando existir verdade-terreno)
- [x] `y_pred_point` (predicao pontual)
- [x] `y_pred_q10` (quando quantilico)
- [x] `y_pred_q50` (quando quantilico)
- [x] `y_pred_q90` (quando quantilico)
- [x] `quantile_levels` efetivamente usados no run

### 1.4 Integridade minima
- [x] Garantir 1 linha unica por (`run_id`,`split`,`horizon`,`timestamp`,`target_timestamp`).
- [x] Garantir `target_timestamp` monotono por (`run_id`,`split`,`horizon`).
- [x] Garantir tipos numericos consistentes (`float64`) em `y_true/y_pred*`.
- [x] Garantir cobertura completa para os horizontes obrigatorios (`1,7,30`) quando habilitados.

---

## 2) Derivados Minimos por Linha (timestamp-level)

- [x] `error = y_pred_point - y_true`
- [x] `abs_error = abs(error)`
- [x] `sq_error = error^2`
- [x] `pred_interval_low` (usar `quantile_p10`)
- [x] `pred_interval_high` (usar `quantile_p90`)
- [x] `pred_interval_width = pred_interval_high - pred_interval_low` (persistido por linha quando necessario; obrigatorio no gold)
- [x] `prob_up = P(y>0)` derivado dos quantis/distribuicao (ou aproximacao documentada)

Observacao: manter como principio P0 a persistencia dos dados primarios; derivados pesados podem ser materializados em gold.

---

## 3) Catalogo de Metricas por Nivel de Agregacao

### 3.1 Basicas por split/fold/seed/config
- [x] RMSE
- [x] MAE
- [x] MAPE (quando aplicavel)
- [x] sMAPE (quando aplicavel)
- [x] DA (Directional Accuracy)
- [x] Bias medio (`mean(y_pred - y_true)`)
- [x] Salvar metricas basicas por `horizon` (alem do agregado).

### 3.2 Probabilisticas (quantilicas)
- [x] Pinball loss por quantil (`q10`, `q50`, `q90`, ...)
- [x] Mean pinball loss
- [x] PICP (Prediction Interval Coverage Probability)
- [x] MPIW (Mean Prediction Interval Width)
- [x] Coverage error (`PICP - cobertura_nominal`)
- [x] Salvar metricas probabilisticas por `horizon`.

### 3.3 Grau de certeza (operacional)
- [x] `interval_width` medio por horizonte (proxy primaria de incerteza)
- [x] `prob_up` / `prob_down` por horizonte
- [x] `confidence` calibrada (derivada de cobertura historica + largura de intervalo)
- [x] Evitar score unico sem calibracao documentada

### 3.4 Risco previsto
- [x] VaR por alfa (`VaR_10`, `VaR_05`, ...)
- [x] ES (Expected Shortfall) aproximado
- [x] Expected move
- [x] Downside risk
- [ ] [P2] Risk-reward proxy

Definicoes matematicas (implementadas em `gold_prediction_risk`):
- `expected_move`: media de `abs(y_pred)` por (`run_id`,`split`,`horizon`).
- `downside_risk`: media de `max(-y_pred, 0)` por (`run_id`,`split`,`horizon`).
- `VaR_10`: media de `quantile_p10` por (`run_id`,`split`,`horizon`).
- `ES_10` aproximado: media de `1.125*q10 - 0.125*q50` (com clamp `ES_10 <= VaR_10`) por (`run_id`,`split`,`horizon`).
- `confidence_calibrated`: `(1 - |coverage_error|/coverage_nominal)_clip * 1/(1+pred_interval_width)` por (`run_id`,`split`,`horizon`).

### 3.5 Robustez e estabilidade
- [x] media por config
- [x] desvio padrao por config
- [x] IQR por config
- [x] IC95 por metrica/config
- [x] gap de generalizacao (`test - val`) por metrica
- [x] consistencia top-k por fold/seed
- [x] Repetir analises de robustez por `horizon` (h+1/h+7/h+30)

### 3.6 Comparacao estatistica entre modelos (OOS alinhado)
- [x] DM test (Diebold-Mariano)
- [x] MCS (Model Confidence Set)
- [x] win-rate pareado por timestamp

### 3.7 Explicabilidade de features (ligada a Y)
- [x] Importancia global por feature (periodo/run)
- [x] Contribuicao local por inferencia (`run_id`,`timestamp`,`horizon`,`feature`,`contribution`)
- [x] Estabilidade da explicacao local (top-k consistency entre seeds/janelas)

---

## 4) Estrategia de Tabelas (Reusar vs Criar)

### 4.1 Silver (P0: reusar o que ja existe)
- [x] Reusar `fact_oos_predictions` para predicoes, quantis, erros e chaves temporais.
- [x] Reusar `fact_config` para guardar `evaluation_horizons_json` e configuracao probabilistica.
- [x] Reusar `fact_model_artifacts` para importancia global (feature importance).
- [x] Criar `fact_inference_predictions` para unificar inferencia operacional com OOS em analytics (separado de `data/processed/inference_tft`).

### 4.2 Silver (P1: novos fatos apenas se necessario)
- [x] `fact_feature_contrib_local` (explicabilidade local por inferencia).
- [ ] `fact_prediction_distribution` (opcional; somente se formato de saida probabilistica exigir mais que q10/q50/q90).

### 4.3 Gold
- [x] `gold_prediction_metrics_by_run_split_horizon`
- [x] `gold_prediction_metrics_by_config`
- [x] `gold_prediction_metrics_by_horizon`
- [x] `gold_prediction_calibration`
- [x] `gold_prediction_risk`
- [x] `gold_prediction_generalization_gap`
- [x] `gold_prediction_robustness_by_horizon`
- [x] `gold_dm_pairwise_results`
- [x] `gold_mcs_results`
- [x] `gold_win_rate_pairwise_results`
- [x] `gold_paired_oos_intersection_by_horizon`
- [x] `gold_model_decision_final`
- [x] `gold_quality_run_sweep_summary`
- [x] `gold_feature_impact_by_horizon` (global)
- [x] `gold_feature_contrib_local_summary` (local)

---

## 5) Regras de Alinhamento OOS (criticas)

- [x] Comparacoes entre modelos devem usar exatamente o mesmo conjunto de `target_timestamp`.
- [x] Nao comparar metricas entre modelos com cobertura temporal diferente sem intersecao explicita.
- [x] Para DM/MCS, armazenar e usar perdas por timestamp no mesmo eixo temporal.
- [x] Executar alinhamento separadamente por `horizon` antes de agregar resultados.
- [x] Enforce tecnico antes de DM/MCS/win-rate: `inner join` por `asset+split+horizon+target_timestamp` (coorte comparavel).
- [x] Persistir diagnostico de alinhamento por coorte: `n_common`, `n_union`, `coverage_ratio`, `aligned_exact`.
- [x] Gate de comparacao pareada: falhar quando `n_common==0` ou cobertura abaixo do limiar definido.

---

## 6) Qualidade e Auditoria

- [x] Validar ausencia de duplicatas na chave temporal por run.
- [x] Validar nulos indevidos em `y_pred` e em `y_true` (quando split supervisionado).
- [x] Validar ranges impossiveis (ex.: `pred_interval_width < 0`).
- [x] Validar cardinalidade esperada por (`config x fold x seed x split`).
- [x] Validar tipos numericos nas colunas de predicao/erro.
- [x] Validar cobertura de horizontes esperados por run/split.
- [x] Validar ordem dos quantis `q10 <= q50 <= q90` quando disponiveis.
- [x] Validar `confidence_calibrated` por horizonte no gold (`gold_prediction_metrics_by_run_split_horizon`).
- [x] Validar contrato `n_oos` em `gold_prediction_metrics_by_config` (presenca, positividade e consistencia com `sum(n_samples)` do run-level).
- [x] Gerar relatorio automatico de qualidade para predicoes.

---

## 7) Definition of Done

- [x] Todas as predicoes primarias (Y) estao persistidas com chaves completas.
- [x] Grau de certeza e calibracao estao disponiveis por horizonte.
- [x] Analise de importancia global por feature esta disponivel por horizonte/split.
- [x] Contribuicao local por inferencia esta disponivel (ou explicitamente fora de escopo da release).
- [x] Todas as metricas de comparacao entre configs/feature sets sao reproduziveis sem retrain.
- [x] DM/MCS podem ser executados apenas com dados persistidos.

---

## 8) Prioridade para Rigor Academico (Proposta)

### P0 (obrigatorio para defesa robusta)
- [x] Metricas OOS basicas por split/fold/seed/config: RMSE, MAE, DA e Bias.
- [x] Calibracao probabilistica minima: Pinball por quantil, PICP e MPIW.
- [x] Comparacao pareada com alinhamento temporal estrito por `target_timestamp`:
- [x] DM test (com correcao small-sample).
- [x] MCS para selecao de conjunto de melhores modelos.
- [x] Robustez entre replicas:
- [x] media/desvio por config.
- [x] IC95 por metrica/config.
- [x] consistencia top-k por fold/seed.

### P1 (fortemente recomendado)
- [x] Analise por horizonte (h+1/h+7/h+30) para todas as metricas de P0.
- [x] Controle de comparacoes multiplas/data snooping (Holm-Bonferroni sobre DM pairwise).
- [x] Gap de generalizacao (`test - val`) por metrica e por horizonte.
- [ ] Explicabilidade local com validacao de estabilidade.

### P2 (complementar)
- [ ] Testes condicionais avancados (ex.: Giacomini-White, Clark-West quando aplicavel).
- [ ] Metricas de risco avancadas (VaR/ES completos com backtesting formal).
- [ ] Interpretabilidade avancada (attention export estruturado, SHAP/permutation em lote).

---

## 9) Outputs Obrigatorios De Analise (Graficos, Tabelas, Relatorios)

Objetivo: padronizar os artefatos que devem ser gerados para comparacao completa entre modelos,
com foco em rigor estatistico, reprodutibilidade e defesa academica.

### 9.1 Tabelas essenciais (P0)
- [x] `tbl_leaderboard_by_horizon`: RMSE, MAE, DA, Pinball, PICP, MPIW, `n_oos` por (`config`,`feature_set`,`horizon`) (materializado em `gold_prediction_metrics_by_config.parquet`).
  Definicao operacional de `n_oos`: soma de `n_samples` do nivel run (`gold_prediction_metrics_by_run_split_horizon`) para o mesmo (`asset`,`feature_set_name`,`config_signature`,`split`,`horizon`).
  Contrato de qualidade ativo: check `gold_metrics_by_config_n_oos_contract` valida coluna obrigatoria `n_oos`, `n_oos > 0` e consistencia com run-level (`sum(n_samples)`).
- [x] `tbl_paired_tests_by_horizon`: DM statistic, p-value, p-value ajustado (Holm), win-rate pareado e IC95 da diferenca de erro (materializado em `gold_quality_statistics_report.parquet`).
- [x] `tbl_final_decision`: melhor modelo por horizonte com regra explicita de selecao (metrica primaria + criterio estatistico) (materializado em `gold_model_decision_final.parquet`).
- [x] `tbl_robustness_fold_seed`: media, desvio, mediana e IQR por (`config`,`feature_set`,`horizon`).
- [x] `tbl_risk_summary`: expected_move, downside_risk, VaR10, ES por (`config`,`feature_set`,`horizon`) (materializado em `gold_prediction_risk.parquet`).

### 9.2 Graficos essenciais (P0)
- [x] `fig_heatmap_metrics_by_horizon`: heatmap modelo x horizonte para RMSE/MAE/DA/Pinball.
- [x] `fig_boxplot_error_by_fold_seed`: distribuicao de erro OOS por fold/seed para robustez.
- [x] `fig_dm_pvalue_matrix`: matriz de comparacao pareada com p-values ajustados por horizonte.
- [x] `fig_calibration_curve`: cobertura observada vs cobertura nominal (por horizonte).
- [x] `fig_interval_width_vs_coverage`: MPIW vs PICP para avaliar calibracao x sharpness.
- [x] `fig_oos_timeseries_examples`: `y_true` vs `p50` com banda `p10-p90` em janelas representativas.

### 9.3 Interpretabilidade visual (P1)
- [x] `fig_feature_importance_global`: top-k features por horizonte (agregado por run/config).
- [x] `fig_feature_contrib_local_cases`: contribuicao local para casos de maior erro e maior acerto.
- [x] `tbl_feature_explanation_stability`: estabilidade de top-k local entre seeds/janelas (materializado em `gold_feature_contrib_local_summary.parquet`).

### 9.4 Relatorios essenciais (P0)
- [x] `report_quality_and_completeness`: completude, duplicatas, alinhamento temporal, cobertura de horizontes e quantis (materializado em `gold_oos_quality_report.parquet`).
- [x] `report_statistical_comparison`: DM/MCS/win-rate/IC95 por horizonte com conclusao reproduzivel (materializado em `gold_quality_statistics_report.parquet`).
- [x] `report_model_selection`: ranking final e trade-offs (acuracia, calibracao, risco, robustez) (materializado em `gold_model_decision_final.parquet`).
- [x] `report_production_inference_monitoring`: qualidade de inferencias de producao (quantis validos, cobertura recente, drift de erro) (materializado em `gold_quality_run_sweep_summary.parquet`).

### 9.5 Escopo por fluxo (implementacao)
- [ ] Fluxo de testes/sweeps deve gerar todos os artefatos de 9.1, 9.2 e 9.4 automaticamente ao final da execucao.
- [ ] Fluxo de inferencia em producao deve gerar ao menos `report_production_inference_monitoring` e tabelas de qualidade/calibracao rolling.
- [ ] Todos os artefatos devem ser rastreaveis por `run_id`, `model_version`, `feature_set_name`, `config_signature` e `horizon`.

### 9.6 Definition of Done dos artefatos (P0)
- [ ] Comparacao final entre modelos pode ser feita apenas com dados persistidos (sem retrain).
- [ ] Todas as tabelas usam intersecao temporal explicita por `target_timestamp` nas comparacoes pareadas.
- [ ] Relatorio final apresenta vencedores por horizonte com evidencia estatistica (DM/MCS/win-rate/IC95).
- [ ] Relatorio final apresenta incerteza calibrada (PICP/MPIW/coverage error) e risco previsto (VaR/ES/expected_move).


---

## 10) Roteiro Pratico De Analise Final (Academico)

Objetivo: transformar os artefatos gerados em conclusao reproduzivel sobre melhor modelo por horizonte.

### 10.1 Execucao padrao
1. Rodar refresh + qualidade + graficos:
`python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL`
2. Confirmar `failed_checks=[]` no log.
3. Confirmar existencia dos artefatos em `data/analytics/gold` e `data/analytics/reports/prediction_analysis_plots/asset=AAPL`.

### 10.1.1 Execucao com escopo de analise (recomendado para defesa)
1. Escopo por candidatos congelados (mais reproduzivel):
`python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL --plots-scope-csv data/analytics/selection/frozen_candidates_0_2_2.csv`
2. Escopo por prefixo de sweep (suporte operacional):
`python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL --plots-scope-sweep-prefixes 0_2_2_`
3. Escopo combinado (intersecao):
`python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL --plots-scope-csv data/analytics/selection/frozen_candidates_0_2_2.csv --plots-scope-sweep-prefixes 0_2_2_`
4. O escopo afeta apenas a geracao dos graficos de analise (`--plots-*`); o refresh gold global continua sendo recalculado normalmente.

### 10.2 Ordem de leitura recomendada
1. Qualidade e completude:
`gold_oos_quality_report.parquet`
Validar: duplicatas=0, cobertura de horizontes esperados, quantis ordenados (`p10<=p50<=p90`), alinhamento temporal pareado habilitado.
2. Leaderboard por horizonte:
`gold_prediction_metrics_by_config.parquet`
Validar: RMSE/MAE/DA/Pinball/PICP/MPIW por `horizon` com `n_oos` suficiente e sem outliers de cardinalidade.
3. Comparacao estatistica:
`gold_quality_statistics_report.parquet`, `gold_dm_pairwise_results.parquet`, `gold_mcs_results.parquet`, `gold_win_rate_pairwise_results.parquet`
Validar: DM com ajuste Holm, MCS por horizonte, win-rate e IC95 consistentes.
4. Decisao final:
`gold_model_decision_final.parquet`
Validar: vencedor por horizonte com criterio explicito (acuracia + significancia estatistica + robustez).
5. Risco e calibracao:
`gold_prediction_risk.parquet`, `gold_prediction_calibration.parquet`
Validar: trade-off entre cobertura (PICP), largura (MPIW), VaR/ES e downside risk.
6. Interpretabilidade:
`gold_feature_impact_by_horizon.parquet`, `gold_feature_contrib_local_summary.parquet`
Validar: coerencia entre importancia global e casos locais (maior erro/acerto), estabilidade de top-k.

### 10.3 Leitura dos 8 graficos (9.2/9.3)
1. `fig_heatmap_metrics_by_horizon`:
Usar para triagem inicial de melhores configs por horizonte.
2. `fig_boxplot_error_by_fold_seed`:
Usar para robustez; preferir menor dispersao para desempenho equivalente.
3. `fig_dm_pvalue_matrix`:
Usar para filtrar diferencas nao significativas entre candidatos.
4. `fig_calibration_curve`:
Usar para verificar calibracao de incerteza (pontos proximos da diagonal).
5. `fig_interval_width_vs_coverage`:
Usar para escolher equilibrio calibracao vs sharpness (cobertura alta com intervalos menores).
6. `fig_oos_timeseries_examples`:
Usar para inspeção qualitativa de regime e estabilidade temporal da previsao.
7. `fig_feature_importance_global`:
Usar para contribuição media por feature e horizonte.
8. `fig_feature_contrib_local_cases`:
Usar para explicacao de previsoes especificas (maior erro e maior acerto).

### 10.4 Regra objetiva de decisao (recomendada)
1. Selecionar top-k por `horizon` via RMSE/MAE.
2. Remover modelos sem suporte estatistico (DM Holm p<0.05 contra benchmark/top).
3. Entre empatados, preferir melhor calibracao (menor `|coverage_error|`, menor MPIW).
4. Aplicar desempate por risco (menor downside/VaR/ES para mesma acuracia).
5. Registrar vencedor e runner-up por horizonte com justificativa textual curta e referencias das tabelas.

### 10.5 Evidencias minimas para defesa academica
- Tabela final por horizonte com metricas de erro + calibracao + risco + robustez.
- Resultado de DM/MCS/win-rate/IC95 por horizonte usando intersecao temporal explicita.
- Graficos 9.2/9.3 anexados ao relatorio com interpretacao objetiva.
- Decisao final rastreavel por `run_id`, `model_version`, `feature_set_name`, `config_signature`, `horizon`.

## 11) Checklist De Aceite Dos Graficos (Pass/Fail)

Objetivo: definir gates objetivos para considerar os artefatos visuais prontos para comparacao estatistica e defesa academica.

### 11.1 fig_heatmap_metrics_by_horizon
- [ ] Exibe todos os horizontes exigidos no experimento (`h+1`,`h+7`,`h+30`, quando aplicavel).
- [ ] Labels legiveis (`feature_set + hash curto`).
- [ ] Valores conferem com `gold_prediction_metrics_by_config.parquet`.
- [ ] `n_oos` por grupo > 0 e consistente com a base OOS.
- [ ] Nao mistura universos fora do escopo selecionado (sweep/coorte alvo).

### 11.2 fig_boxplot_error_by_fold_seed
- [ ] Cada boxplot possui multiplas observacoes (nao degenera em linha unica).
- [ ] Fonte contem variacao real por `fold` e/ou `seed`.
- [ ] Mediana/dispersao conferem com `gold_prediction_robustness_by_horizon.parquet`.
- [ ] Outliers sao rastreaveis por `run_id`.

### 11.3 fig_dm_pvalue_matrix
- [ ] Matriz quadrada por horizonte com alinhamento por `target_timestamp`.
- [ ] Labels legiveis e consistentes com a coorte filtrada.
- [ ] Nao vazio e com quantidade minima de pares validos.
- [ ] p-values conferem com `gold_dm_pairwise_results.parquet`.
- [ ] Interpretacao estatistica usa ajuste de multiplas comparacoes (Holm/FDR).

### 11.4 fig_calibration_curve
- [ ] Para cada horizonte, ha pontos com `nominal_coverage` esperado (ex.: 0.8).
- [ ] `PICP` em faixa valida [0,1] sem colapso sistematico em zero.
- [ ] Distancia da diagonal ideal esta dentro da tolerancia definida.
- [ ] Coerente com `gold_prediction_calibration.parquet`.

### 11.5 fig_interval_width_vs_coverage
- [ ] `MPIW > 0` para modelos quantilicos validos.
- [ ] `PICP` nao colapsado em zero para todos os modelos.
- [ ] Relacao cobertura x largura e interpretavel (trade-off real).
- [ ] Coerente com `gold_prediction_calibration.parquet`.

### 11.6 fig_oos_timeseries_examples
- [ ] Exibe `y_true`, `p50` e banda `p10-p90` (quando quantilico).
- [ ] Janela temporal legivel e representativa da coorte.
- [ ] Caso rastreavel por `run_id`/`model_version`.
- [ ] Permite avaliar under/over-reaction em regimes de alta variabilidade.

### 11.7 fig_feature_importance_global
- [ ] Metodo de importancia documentado e reprodutivel.
- [ ] Escala/sinal interpretaveis.
- [ ] Nao colapsa artificialmente em valores quase identicos por artefato de agregacao.
- [ ] Coerente com `gold_feature_impact_by_horizon.parquet`.

### 11.8 fig_feature_contrib_local_cases
- [ ] Nao vazio para o escopo analisado.
- [ ] Casos mostram top contribuicoes com sinal (+/-).
- [ ] Linhas rastreaveis por `timestamp`,`horizon`,`model_version`.
- [ ] Coerente com `fact_feature_contrib_local` e `gold_feature_contrib_local_summary.parquet`.

### 11.9 Gates finais (obrigatorios)
- [ ] `python -m src.main_refresh_analytics_store --fail-on-quality` retorna `failed_checks=[]`.
- [ ] Os 8 graficos foram gerados para o mesmo escopo (`--plots-scope-*` quando aplicavel).
- [ ] Tabelas-chave existem e nao estao vazias:
  - [ ] `gold_prediction_metrics_by_config.parquet`
  - [ ] `gold_quality_statistics_report.parquet`
  - [ ] `gold_model_decision_final.parquet`
  - [ ] `gold_prediction_risk.parquet`
  - [ ] `gold_feature_contrib_local_summary.parquet`
- [ ] Comparacoes estatisticas (DM/MCS/win-rate) usam intersecao temporal explicita.
- [ ] Decisao final por horizonte esta documentada com erro, calibracao, risco e robustez.
