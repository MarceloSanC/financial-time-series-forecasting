# Project Full Technical Review (v0)

Data da revisao: 2026-03-30  
Projeto: `financial-time-series-forecasting`  
Escopo: revisao end-to-end dos fluxos implementados no codigo, com foco em cobertura funcional, rastreabilidade, qualidade estatistica e riscos para v0.

Atualizacao de registro (2026-04-02): a fragilidade de referencias legadas no README foi tratada; links de onboarding e indice documental foram alinhados com a arvore atual de docs.

---

## 1. Resumo Executivo

Este projeto ja possui uma base forte para v0 em:
- pipeline de dados estruturado (market/news/sentiment/fundamentals/indicators),
- treino TFT com controle de warmup e contratos de qualidade,
- inferencia rolling com persistencia analitica,
- analytics store silver/gold com testes de qualidade e comparacao estatistica,
- geracao de graficos e artefatos para analise final.

No estado atual, a arquitetura cobre os elementos centrais para defesa academica: reproducibilidade de run, comparacao justa entre modelos, metricas OOS, calibracao probabilistica, DM/MCS/win-rate e interpretabilidade global/local.

As principais fragilidades identificadas nao estao no "core" matematico, e sim em:
- higiene operacional (mistura de coortes heterogeneas quando filtros nao sao aplicados),
- qualidade/legibilidade de alguns graficos em cenarios degenerados,
- consistencia documental agora alinhada no README e no indice de docs (paths legados removidos).

---

## 2. Metodologia da Revisao

A revisao foi feita por leitura direta do codigo e contratos do projeto, cobrindo:
- entrypoints `main_*` em `src/`,
- use cases e adapters principais,
- schemas analytics/model artifacts,
- checklists oficiais em `docs/05_checklists/`,
- estrutura de testes em `tests/`.

Evidencia de cobertura usada:
- 56 arquivos de teste detectados em `tests/`.
- Fluxos revisados: ingestao, feature engineering, dataset builder, treino, sweeps, inferencia, refresh analytics, validacao de qualidade e plots.

---

## 3. Arquitetura Geral por Etapas

### Etapa A - Configuracao e Resolucao de Caminhos

**Objetivo**
- Centralizar periodos, paths e comportamento default por pipeline.

**Entradas**
- `config/data_sources.yaml`
- `config/data_paths.yaml`
- configs especificas de qualidade/sweeps

**Processamento**
- resolucao de paths por `path_resolver`
- uso de `data_period` e `training_period` no fluxo atual

**Saidas**
- parametros normalizados para cada main/use case

**Implementado**
- resolucao consistente em todos os mains revisados
- separacao de configuracoes por dominio (`quality`, `sweeps`, `features`)

**Testes**
- cobertura indireta nos testes unitarios de use cases

**Fragilidades/Riscos**
- drift de defaults entre CLI e config pode ocorrer se nao houver validacao central unica.

**Sugestoes v0**
- reforcar validacao unificada de periodo por contrato (data_period/training_period) e erro explicito quando ausente.

---

### Etapa B - Ingestao de Dados Primarios

Inclui candles, news e fundamentals.

#### B1) Candles (`main_candles.py`)

**Objetivo**
- Buscar e persistir candles historicos por ativo com cobertura temporal controlada.

**Entradas**
- ativo, `data_period`, adaptador de mercado.

**Processamento**
- fetch de candles + persistencia parquet + quality report.

**Saidas**
- `data/raw/market/candles/<ASSET>/...parquet`
- relatorio de qualidade do job.

**Implementado**
- pipeline com logs estruturados e fallback de periodo.

**Fragilidades**
- dependencia de fonte externa; variacoes de API podem quebrar sem mudancas no codigo.

#### B2) News Dataset (`main_news_dataset.py`)

**Objetivo**
- Ingerir noticias cruas por ativo (Alpha Vantage), com controle de cobertura/rate-limit.

**Entradas**
- ativo, periodo, chave de API.

**Processamento**
- fetch incremental, verificacao de cobertura, skip quando periodo ja coberto.

**Saidas**
- `data/raw/news/...parquet`
- quality report de ingestao.

**Implementado**
- parse temporal robusto (UTC aware) e throttling minimo.

**Fragilidades**
- risco de gaps por indisponibilidade da API ou limites de cota.

#### B3) Fundamentals (`main_fundamentals.py`)

**Objetivo**
- Ingerir dados fundamentalistas e manter cobertura temporal valida para joins.

**Entradas**
- ativo, periodo de dados, chave de API.

**Processamento**
- fetch + normalizacao + persistencia parquet + quality.

**Saidas**
- `data/processed/fundamentals/...parquet`

**Fragilidades**
- natureza esparsa dos fundamentals (mudanca lenta) exige estrategia de preenchimento/propagacao consistente para treino.

---

### Etapa C - NLP de Sentimento

Inclui scoring e agregacao diaria.

#### C1) Sentiment Scoring (`main_sentiment.py`)

**Objetivo**
- Pontuar noticias com FinBERT para gerar sinal diario de sentimento.

**Entradas**
- dataset de noticias cruas.

**Processamento**
- inferencia NLP + persistencia de scores por noticia.

**Saidas**
- `data/processed/sentiment/...`

#### C2) Sentiment Daily Features (`main_sentiment_features.py`)

**Objetivo**
- Agregar sentimento para granularidade diaria alinhada ao mercado.

**Entradas**
- noticias pontuadas.

**Processamento**
- agregacoes (score, volume, dispersao, flags), regras de temporalidade de pregao.

**Saidas**
- `data/processed/sentiment_daily/...`

**Fragilidades**
- risco de leakage temporal se regras de agregacao/pre-market/after-market forem alteradas sem testes dedicados.

**Sugestao v0**
- manter testes de causalidade temporal como gate obrigatorio para qualquer mudanca nesse modulo.

---

### Etapa D - Feature Engineering de Mercado

#### D1) Indicadores Tecnicos (`main_technical_indicators.py`)

**Objetivo**
- Derivar indicadores de candles para enriquecer sinal preditivo.

**Entradas**
- candles diarios.

**Processamento**
- calculo de indicadores tecnicos + persistencia.

**Saidas**
- `data/processed/technical_indicators/<ASSET>/...`

**Fragilidades**
- indicadores com janelas longas causam warmup diferente por feature set.

#### D2) Dataset TFT (`main_dataset_tft.py`)

**Objetivo**
- Montar dataset final de treino/inferencia com uniao de todas as familias de features.

**Entradas**
- candles + indicadores + sentiment_daily + fundamentals.

**Processamento**
- joins, ordenacao temporal, criacao de target/time_idx, quality gate.

**Saidas**
- `data/processed/dataset_tft/<ASSET>/dataset_tft_*.parquet`
- relatorio de dataset com secao de quality gate.

**Implementado**
- quality gate formal em `DatasetQualityGate`, incluindo:
  - monotonicidade e unicidade temporal,
  - cobertura minima,
  - limite de NaN por feature,
  - exclusao de warmup por feature na validacao de NaN.

**Fragilidades**
- thresholds muito permissivos (`max_nan_ratio=1.0`) em alguns cenarios podem mascarar problemas de qualidade.

---

### Etapa E - Treino de Modelo TFT (`main_train_tft.py`)

**Objetivo**
- Treinar TFT com contratos reprodutiveis e persistencia analitica completa.

**Entradas**
- dataset_tft,
- feature set,
- split temporal,
- hiperparametros,
- politica de warmup,
- configuracao de modo de previsao (point/quantile),
- horizontes de avaliacao.

**Processamento**
- validacao de split anti-leakage,
- aplicacao de warmup policy (`strict_fail`/`drop_leading`),
- treinamento Lightning/PyTorch Forecasting,
- avaliacao OOS e persistencia analytics.

**Saidas**
- artefatos de modelo em `data/models/{ASSET}/runs/{VERSION}`,
- tabelas silver de analytics (run/config/snapshot/epoch/split/oos/artifacts/features/failures).

**Implementado**
- contratos deterministas:
  - `feature_set_hash`, `config_signature`, `split_fingerprint`, `run_id`.
- persistencia robusta com status `ok|failed|partial_failed`.
- compatibilidade com `prediction_mode=quantile` default.

**Testes**
- testes unitarios de `train_tft_model_use_case`, schema e repositorios.

**Fragilidades**
- warnings de `StandardScaler` com/sem feature names ainda aparecem em inferencia/treino (nao quebram fluxo, mas poluem e podem ocultar issues reais).

---

### Etapa F - Orquestracao de Experimentos (Sweeps)

Inclui OFAT, Optuna e explicit configs.

**Objetivo**
- Explorar hiperparametros e comparar combinacoes de feature sets com rigor controlado.

**Entradas**
- configs em `config/sweeps/...`.

**Processamento**
- execucao por fold/seed,
- merge/resume com validacoes de contexto,
- contagem de trials completos,
- limpeza de artefatos incompletos,
- consolidacao de resultados.

**Saidas**
- diretorios de sweep com modelos,
- sqlite do Optuna,
- relatorios de sweep e top-k configs.

**Implementado**
- validacoes fortes de `--merge-tests` (base config/splits/walk-forward),
- protecoes contra mistura silenciosa de estudos incompativeis.

**Fragilidades**
- interrupcoes durante run podem gerar artefatos orfaos; existe backfill, mas operacionalmente ainda requer disciplina.

**Sugestao v0**
- adicionar runbook curto de recuperacao (passo a passo) no fluxo de sweep interrompido.

---

### Etapa G - Inferencia TFT (`main_infer_tft.py`)

**Objetivo**
- Produzir previsoes em producao/avaliacao com rastreabilidade e persistencia analytics.

**Entradas**
- modelo treinado,
- ativo,
- periodo de inferencia,
- modo (`rolling`/`last_point`),
- politica strict de quantis.

**Processamento**
- validacao de compatibilidade de features,
- elegibilidade temporal por contexto (`max_encoder_length`, contiguidade de `time_idx`),
- inferencia rolling em lote,
- extracao de quantis com fallback robusto (`quantiles` -> `raw` -> `forward`).

**Saidas**
- `data/processed/inference_tft/...parquet`,
- `fact_inference_predictions`,
- `fact_feature_contrib_local`,
- `fact_inference_runs`.

**Implementado**
- cobertura rolling com logs detalhados (requested/eligible/inferred/skipped),
- strict quantile validation para evitar salvar saida inconsistente,
- deduplicacao e suporte a `overwrite`.

**Fragilidades**
- em alguns modelos, `predict(mode=quantiles)` retorna vazio; fallback resolveu operacionalmente, mas deve continuar com monitoramento por versao de PF/Lightning.

**Sugestao v0**
- manter teste de regressao fixo para este caso (modelo quantile + inferencia rolling), garantindo quantis nao nulos no contrato final.

---

### Etapa H - Analytics Store (Silver/Gold)

**Objetivo**
- Consolidar dados necessarios para comparacao estatistica e interpretabilidade sem retrain.

**Entradas**
- tabelas silver de treino e inferencia.

**Processamento**
- refresh gold por agregacoes de run/config/horizon,
- validacoes de qualidade e contratos,
- materializacao de tabelas estatisticas e de decisao.

**Saidas**
- tabelas gold em `data/analytics/gold/*.parquet`.

**Implementado (principal)**
- metricas por run/config/horizonte,
- calibracao (`PICP`, `MPIW`, coverage error),
- risco (`expected_move`, `downside_risk`, `VaR_10`, `ES_10 aproximado`),
- robustez (`mean/std/median/IQR/CI95`),
- comparacoes pareadas (`DM`, `MCS`, `win-rate`),
- decisao final (`gold_model_decision_final`),
- relatorios de qualidade estatistica.

**Qualidade/Contrato**
- `main_refresh_analytics_store --fail-on-quality` executa checks de contrato/consistencia.

**Fragilidades**
- sem filtro de coorte, comparar tudo de um asset pode misturar runs heterogeneas e enfraquecer validade inferencial.

**Sugestao v0**
- usar sempre escopo congelado (frozen candidates/sweep prefix) para analises finais e publicacao de resultados.

---

### Etapa I - Graficos e Relatorios de Analise

**Objetivo**
- Gerar evidencias visuais e tabelares para analise tecnica/academica.

**Entradas**
- tabelas gold e filtros de escopo.

**Processamento**
- geracao de 8 graficos principais,
- manifest de saida,
- filtros por sweep prefix/scope csv.

**Saidas**
- `data/analytics/reports/prediction_analysis_plots/asset=<ASSET>/...png` + manifest.

**Implementado**
- backend `Agg` para evitar falhas Tkinter em execucao nao interativa.
- filtros de escopo (evita mistura de coortes).

**Fragilidades**
- alguns graficos ficam degenerados/ilegiveis quando os dados estatisticos estao pobres (ex.: 1 ponto, matriz muito densa).

**Sugestao v0**
- adicionar regras de legibilidade no plotter:
  - fallback textual quando cardinalidade < limite,
  - matriz DM com top-k pares mais relevantes,
  - anotacao de "dados insuficientes" no proprio grafico.

---

### Etapa J - Governanca, Testes e Documentacao

**Objetivo**
- garantir evolucao segura e rastreavel.

**Implementado**
- reorganizacao de docs por dominio (`00_overview` a `08_governance`),
- checklists de analytics e prediction metrics,
- suite de testes relevante (56 arquivos),
- guias de commit/versionamento.

**Fragilidades**
- risco residual baixo de desatualizacao documental futura quando novos arquivos forem movidos sem atualizar o README/INDEX.

**Sugestao v0**
- manter checklist de revisao documental em PRs que alterem paths de docs (README + docs/INDEX.md + runbooks).

---

## 4. Cobertura de Objetivos do Projeto (Status Atual)

### 4.1 O que ja esta bem coberto

- previsao quantilica com contratos de persistencia,
- rastreabilidade completa de treino (`run_id`, assinaturas, fingerprints),
- qualidade de dados e contratos analytics automatizados,
- comparacao pareada com alinhamento temporal,
- interpretabilidade global e local (com limites conhecidos).

### 4.2 O que ainda merece atencao para fechamento robusto de v0

- padronizar consumo de coortes na analise final (sempre filtrado),
- melhorar legibilidade e robustez semantica de parte dos plots,
- reduzir ruido de warnings nao criticos em pipelines longos,
- endurecer thresholds de qualidade por fase (dataset e gold) conforme objetivo final.

---

## 5. Fragilidades e Possiveis Bugs (Priorizados)

### Alta prioridade

1. Mistura de coortes heterogeneas na analise final se refresh/plots forem rodados sem escopo.
- Impacto: invalida comparacoes estatisticas (DM/MCS/win-rate) por falta de comparabilidade estrita.
- Mitigacao: obrigar escopo em analise final (frozen/sweep prefix).

2. Graficos estatisticos degenerados podem induzir interpretacao errada.
- Impacto: decisao visual incorreta mesmo com dados corretos.
- Mitigacao: regras de fallback/insuficiencia de dados.

### Media prioridade

3. Warnings recorrentes de scaler/feature names.
- Impacto: ruido operacional e risco de mascarar warning relevante.
- Mitigacao: harmonizar fit/transform com nomes consistentes.

4. Dependencia de APIs externas sem camada de resiliencia mais rica.
- Impacto: gaps em ingestao e resultados enviesados por cobertura.
- Mitigacao: monitor de cobertura e retry/backoff mais robusto por fonte.

### Baixa prioridade

5. Governanca documental depende de disciplina de manutencao continua.
- Impacto: se README/INDEX nao forem atualizados junto com mudancas de estrutura, onboarding volta a degradar.
- Mitigacao: gate documental em PR com alteracao de paths e comandos.

---

## 6. Matriz de Prontidao v0 (pragmatica)

- Pipeline de dados: **Pronto com ressalvas operacionais**.
- Treino e rastreabilidade: **Pronto**.
- Inferencia rolling com contratos: **Pronto**.
- Analytics silver/gold: **Pronto**.
- Qualidade estatistica automatizada: **Pronto**.
- Artefatos de analise final (tabelas/plots): **Pronto com necessidade de filtro de coorte**.
- Governanca documental: **Boa (README ja alinhado com a estrutura atual de docs)**.

Conclusao: o projeto esta em condicao de executar analise final academica, desde que o protocolo de selecao de coorte seja seguido rigorosamente e os graficos sejam interpretados com os checks de qualidade ativos.

---

## 7. Protocolo Recomendado para Analise Final (sem retrain)

1. Definir coorte oficial (ex.: sweeps `0_2_2` + frozen candidates).
2. Rodar refresh com qualidade estrita:
- `.venv/bin/python -m src.main_refresh_analytics_store --fail-on-quality`
3. Gerar plots com filtro de escopo coerente:
- `.venv/bin/python -m src.main_refresh_analytics_store --plots-asset AAPL --plots-scope-csv <arquivo_scope>`
4. Validar tabelas nucleares:
- `gold_prediction_metrics_by_config`
- `gold_quality_statistics_report`
- `gold_model_decision_final`
- `gold_prediction_risk`
- `gold_feature_contrib_local_summary`
5. Registrar conclusoes com referencia de coorte, horizonte e criterio estatistico usado.

---

## 8. Recomendacoes Objetivas de Melhorias (curto prazo)

1. Tornar escopo de coorte obrigatorio para comandos de analise final (modo `--final-analysis`).
2. Reforcar gate de manutencao do `README.md` e `docs/INDEX.md` em PRs de reorganizacao documental.
3. Adicionar teste de regressao para graficos degenerados (1 ponto, sem pares DM).
4. Reduzir warnings de scaler por padronizacao de feature names no pipeline inferencia.
5. Criar um "quality snapshot" unico (JSON/MD) por refresh, com checks + contexto de coorte.

---

## 9. Inventario de Fluxos Revisados (referencia)

### Entry points principais
- `src/main_data_pipeline.py`
- `src/main_candles.py`
- `src/main_news_dataset.py`
- `src/main_sentiment.py`
- `src/main_sentiment_features.py`
- `src/main_fundamentals.py`
- `src/main_technical_indicators.py`
- `src/main_dataset_tft.py`
- `src/main_train_tft.py`
- `src/main_infer_tft.py`
- `src/main_tft_test_pipeline.py`
- `src/main_tft_optuna_sweep.py`
- `src/main_refresh_analytics_store.py`
- `src/main_generate_prediction_analysis_plots.py`
- `src/main_backfill_model_artifacts.py`
- `src/main_rebuild_explicit_sweep_predictions.py`

### Use cases/adapters centrais revisados
- `src/use_cases/train_tft_model_use_case.py`
- `src/use_cases/run_tft_inference_use_case.py`
- `src/adapters/pytorch_forecasting_tft_inference_engine.py`
- `src/adapters/local_tft_inference_model_loader.py`
- `src/use_cases/refresh_analytics_store_use_case.py`
- `src/use_cases/validate_analytics_quality_use_case.py`
- `src/use_cases/generate_prediction_analysis_plots_use_case.py`
- `src/domain/services/dataset_quality_gate.py`
- `src/domain/services/feature_warmup_inspector.py`
- `src/infrastructure/schemas/analytics_store_schema.py`
- `src/infrastructure/schemas/model_artifact_schema.py`

---

## 10. Fechamento

O projeto ja cobre, em codigo, o nucleo necessario para uma avaliacao academica robusta de modelos TFT para retorno financeiro: dados, contratos, rastreabilidade, estatistica comparativa e interpretabilidade.

Os gaps remanescentes sao majoritariamente de operacionalizacao e apresentacao final dos resultados, nao de ausencia de base tecnica.

Em termos praticos: a base v0 esta pronta para a fase de analise final, desde que o processo seja conduzido com coorte congelada e quality gates habilitados.
