---
title: Business Report (Glossary for Stakeholders)
scope: Glossario tecnico simplificado para stakeholders nao-tecnicos. Definicoes em linguagem de negocio, distinto do GLOSSARY tecnico em 00_overview/.
update_when:
  - novo termo precisar de versao para stakeholders
  - definicao de negocio mudar
canonical_for: [business_glossary, stakeholder_terminology]
---

# → Glossary

- OOS: Out-of-sample
- DM: Diebold-Mariano test
- MCS: Model Confidence Set
- PICP: Prediction Interval Coverage Probability
- MPIW: Mean Prediction Interval Width
- Pinball Loss: Quantile loss metric
- Coverage Error: `PICP - nominal_coverage`

# → Decisions

# ADR-0001: Analytics Store as Source of Truth

## Status
Accepted

## Context
Need reproducible and auditable model evaluation without retraining.

## Decision
Use silver/gold analytics store with explicit schema contracts.

## Consequences
- Higher data persistence footprint
- Strong reproducibility and auditability

# ADR-0002: Strict OOS Temporal Alignment for Paired Tests

## Status
Accepted

## Context
DM/MCS/win-rate are invalid under misaligned target timestamps.

## Decision
All paired tests must use explicit temporal intersection by `target_timestamp` and `horizon`.

## Consequences
- Some runs become non-comparable in global analysis
- Statistical validity is preserved

## Pipelines
1. Data ingestion
2. Dataset build
3. Training/sweeps
4. Inference
5. Analytics refresh (silver -> gold)

# → Calibration and Risk

## Calibration
- Nominal vs observed coverage
- Interval width vs coverage

## Risk
- Expected move
- Downside risk
- VaR_10
- ES approximation

# → Metrics Definitions

Document all formulas used in gold tables.

## Core
- RMSE
- MAE
- DA
- Bias

## Probabilistic
- Pinball
- PICP
- MPIW
- Coverage error

# → Plot Interpretation Guide

For each plot, define:
- what it measures
- acceptable patterns
- warning patterns
- which table validates it

# → Statistical Tests

## Paired comparisons
- Diebold-Mariano (DM)
- Win-rate with confidence interval
- Model Confidence Set (MCS)

## Rules
- Exact temporal alignment by target timestamp
- Horizon-specific comparisons
- Multiple-testing control (Holm/FDR)

# → 00 - Living Paper - Outline

Status: draft vivo para alimentar TCC (ABNT) e artigo estilo ML.
Protocolo operacional de escrita: `docs/living-paper/WRITING_PROTOCOL.md`.

## Objetivo do arquivo
Este arquivo funciona como ancora conceitual do projeto de escrita.
Seu papel e consolidar as definicoes centrais (tese, problema, pergunta, recorte, contribuicoes e hipoteses) antes da escrita detalhada dos capitulos.

Uso esperado:
- Entrada: alinhamentos de orientacao, escopo tecnico do repositorio e decisoes metodologicas.
- Saida: base coerente para Introducao do TCC e Introduction/Contributions do artigo.
- Regra: qualquer alteracao de escopo deve ser atualizada primeiro aqui e depois propagada para os demais arquivos.

## 1) Visao geral
Este repositório suporta uma pesquisa de previsao de series temporais financeiras com foco em robustez metodologica, comparabilidade entre configuracoes e reproducibilidade experimental.

## 2) Tese central
Este trabalho sustenta que a previsao de series temporais financeiras com Temporal Fusion Transformer (TFT), combinada com engenharia sistematica de conjuntos de features e avaliacao reprodutivel em nivel de experimento, produz evidencias mais robustas do que abordagens puramente pontuais, especialmente quando incorpora predicoes quantilicas para analise explicita de incerteza.

## 3) Problema cientifico
Em previsao financeira, modelos podem aparentar bom desempenho sem garantir:
- robustez fora da amostra;
- comparabilidade justa entre configuracoes;
- quantificacao confiavel da incerteza preditiva.

## 4) Pergunta de pesquisa
Em series temporais de precos de ativos, o uso de TFT com saidas quantilicas e protocolo reprodutivel de avaliacao permite melhorar a qualidade e a confiabilidade da comparacao entre configuracoes de features e hiperparametros?

## 5) Recorte (delimitacao)
- Tarefa: previsao supervisionada de series temporais financeiras.
- Modelo principal: TFT (sem foco central em comparar arquiteturas profundas distintas).
- Entradas: preco/volume, indicadores tecnicos, sentimento agregado e fundamentals (conforme disponibilidade no pipeline).
- Incerteza: previsao quantilica (ex.: p10, p50, p90).
- Avaliacao: metricas pontuais e probabilisticas + comparacao pareada OOS com alinhamento temporal.
- Reprodutibilidade: rastreabilidade de run_id, configuracao, split e artefatos em Parquet/DuckDB.
- Fora de escopo: estrategia de trading em producao, otimizacao de carteira em tempo real, inferencia intradiaria de alta frequencia.

## 6) Contribuicoes esperadas
- Protocolo reprodutivel de avaliacao para forecasting financeiro com TFT.
- Analise de incerteza com saida quantilica integrada ao pipeline.
- Estrutura de comparacao entre feature sets e configuracoes sem retraining (Analytics Store).

## 7) Hipoteses de trabalho (rascunho)
- H1: configuracoes com features enriquecidas melhoram desempenho OOS frente ao baseline.
- H2: metricas probabilisticas e cobertura de intervalo agregam informacao relevante alem da acuracia pontual.
- H3: alinhamento temporal estrito reduz risco de conclusoes espurias em comparacoes entre modelos.

## 8) Mapeamento de uso
- Uso TCC: texto-base para Introducao (tema, problema, justificativa, objetivos e delimitacoes).
- Uso Artigo: Abstract/Introduction/Contributions.

## 9) Objetivos do trabalho (versao congelada v1)
Objetivo geral:
- Investigar e avaliar um pipeline reproduzivel de previsao de series temporais financeiras baseado em Temporal Fusion Transformer, com predicao quantilica e comparacao sistematica de configuracoes de features e hiperparametros em ambiente fora da amostra.

Objetivos especificos:
- Estruturar um fluxo integrado de dados financeiros, indicadores tecnicos, sentimento agregado e fundamentos, com controle de consistencia temporal e mitigacao de leakage.
- Implementar treinamento e inferencia com Temporal Fusion Transformer em modo pontual e quantilico, com rastreabilidade completa de configuracoes e artefatos de execucao.
- Definir e aplicar protocolo experimental reproduzivel, com particionamento temporal, multiplas sementes e criterios padronizados de comparacao entre experimentos.
- Avaliar o desempenho preditivo com metricas pontuais e probabilisticas, incluindo analise de cobertura e largura de intervalos de predicao.
- Comparar configuracoes de features e hiperparametros com base em evidencias fora da amostra, identificando ganhos de desempenho, robustez e limitacoes.

## 10) Pendencias imediatas
- Definir conjunto minimo de experimentos para secao de resultados.
- Consolidar bibliografia principal para este recorte.

## 11) Base da Introducao (v1 sincronizada com `text/2_Introducao`)
- Contextualizacao: forecasting financeiro como problema desafiador sob HME/HMA e sob dinamica adaptativa de mercado.
- Problema: comparacoes pouco auditaveis entre configuracoes e excesso de foco em erro pontual.
- Justificativa: necessidade de protocolo reproduzivel com TFT, avaliacao OOS e incerteza quantilica.
- Delimitacao: foco em TFT + covariaveis estruturadas + avaliacao pontual/probabilistica; fora de escopo comparacao exaustiva de arquiteturas e trading em producao.
- Estrutura do trabalho: cap. 3 (fundamentacao), cap. 4 (metodo), cap. 5 (resultados), cap. 6 (conclusoes).

Referencias nucleares da Introducao:
- `FAMA1991`, `LO2004`
- `LIMZOHREN2021`, `LIMETAL2021TFT`
- `GNEITING2007`, `KOENKERBASSETT1978`
- `DIEBOLDMARIANO1995`
- `PINEAU2021REPRODUCIBILITY`

# → 10 - Problem and Related Work

## Objetivo deste arquivo
Registrar, em linguagem de artigo, o contexto do problema e a revisao de literatura orientada ao recorte da pesquisa.

Detalhamento do objetivo:
- Definir o estado da arte relevante ao recorte (forecasting financeiro, TFT/transformers, previsao quantilica, avaliacao OOS).
- Explicitar lacunas tecnicas/metodologicas que justificam o trabalho.
- Posicionar claramente a contribuicao do projeto frente a trabalhos relacionados.
- Evitar revisao ampla sem foco no problema de pesquisa definido no `00_outline.md`.

Entrada e saida esperadas:
- Entrada: tese central, pergunta de pesquisa e recorte.
- Saida: narrativa de revisao pronta para alimentar a Fundamentacao Teorica (TCC) e Related Work (artigo).

## Estrutura sugerida
- Problema e motivacao
- Lacunas na literatura
- Trabalhos relacionados (forecasting financeiro, TFT/transformers, predicao quantilica)
- Posicionamento deste trabalho

## Rascunho inicial
- [a preencher]

# → 20 - Method

## Objetivo deste arquivo
Descrever de forma reproduzivel o metodo: dados, features, modelo, treinamento, inferencia e avaliacao.

Detalhamento do objetivo:
- Registrar o metodo com nivel de detalhe suficiente para reproducao tecnica.
- Documentar o fluxo completo do pipeline real: dados -> features -> treino TFT -> inferencia -> analytics.
- Definir protocolo experimental e criterios de comparacao justa entre configuracoes.
- Tornar explicito onde estao os mecanismos de rastreabilidade (run_id, fingerprints, contratos de schema).

Entrada e saida esperadas:
- Entrada: documentacao tecnica do repositorio (`README.md`, checklists e runbooks em `docs/`).
- Saida: secao de Metodo pronta para TCC e secoes Data/Method/Experimental Setup do artigo.

## Estrutura sugerida
- Dados e pipelines
- Engenharia de features
- Modelo (TFT)
- Protocolo experimental (splits, seeds, folds)
- Metricas pontuais e probabilisticas
- Reprodutibilidade e rastreabilidade (run_id, fingerprints, analytics store)

## Rascunho inicial
- [a preencher]

# → 30 - Results and Analysis

## Objetivo deste arquivo
Consolidar resultados, comparacoes e interpretacoes para TCC e artigo.

Detalhamento do objetivo:
- Centralizar resultados por horizonte, split e configuracao de experimento.
- Diferenciar desempenho pontual de desempenho probabilistico (incerteza e calibracao).
- Registrar comparacoes pareadas e evidencias de robustez estatistica sem retraining.
- Produzir interpretacoes tecnicas defensaveis, evitando afirmacoes sem suporte empirico.

Entrada e saida esperadas:
- Entrada: artefatos analiticos persistidos (silver/gold), metricas e logs de evidencias.
- Saida: secao de Resultados e Discussao do TCC e Results/Analysis do artigo.

## Estrutura sugerida
- Configuracoes avaliadas
- Resultados principais por horizonte/split
- Analise de incerteza (quantis, cobertura)
- Comparacoes estatisticas (ex.: DM/MCS, quando aplicavel)
- Interpretabilidade e implicacoes praticas

## Rascunho inicial
- [a preencher]

# → 40 - Limitations and Conclusion

## Objetivo deste arquivo
Registrar limitacoes, ameacas a validade e conclusoes tecnicas sem exagero de claim.

Detalhamento do objetivo:
- Delimitar de forma transparente o que os resultados permitem afirmar e o que nao permitem.
- Organizar ameacas a validade (dados, modelagem, avaliacao, generalizacao).
- Consolidar contribuicoes efetivas sem inflar escopo alem do que foi testado.
- Fechar com propostas de trabalhos futuros tecnicamente coerentes com as limitacoes observadas.

Entrada e saida esperadas:
- Entrada: achados do arquivo de resultados e registro de evidencias.
- Saida: Conclusoes do TCC e Discussion/Limitations/Conclusion do artigo.

## Estrutura sugerida
- Limitacoes do estudo
- Ameacas a validade
- Conclusoes
- Trabalhos futuros

## Rascunho inicial
- [a preencher]

# → Chapter Structure Freeze (TCC ABNT)

Status: estrutura congelada para reescrita do conteudo, mantendo o formato ABNT atual.

## Objetivo do arquivo
Congelar a macroestrutura de capitulos antes da escrita detalhada para evitar deriva de escopo e retrabalho.

Detalhamento do objetivo:
- Preservar o formato ABNT ja adotado no projeto.
- Definir fronteiras claras de conteudo por capitulo.
- Garantir alinhamento com o escopo tecnico real (TFT, quantis, reproducibilidade).
- Servir como referencia de validacao antes de cada rodada de edicao dos arquivos em `text/`.

## Capitulo 1 - Elementos pre-textuais
Arquivos:
- `text/1_Resumo/1_4_Resumo.tex`
- `text/1_Resumo/1_5_Abstract.tex`

Escopo de conteudo:
- problema, objetivo, metodo, resultados principais, contribuicoes.
- alinhado ao escopo TFT + avaliacao quantilica + reprodutibilidade.

## Capitulo 2 - Introducao
Arquivo:
- `text/2_Introducao/2_Introducao.tex`

Secoes congeladas:
1. Contextualizacao e motivacao
2. Problema de pesquisa
3. Justificativa
4. Objetivos
5. Delimitacao do estudo
6. Estrutura do trabalho

## Capitulo 3 - Fundamentacao teorica
Arquivo:
- `text/3_Revisao_Teorica/3_Revisao_Teorica.tex`

Secoes congeladas:
1. Previsao de series temporais financeiras
2. Modelagem com deep learning para series temporais
3. Temporal Fusion Transformer (TFT)
4. Predicao probabilistica e quantilica
5. Avaliacao de modelos em ambiente OOS
6. Reprodutibilidade experimental e rastreabilidade

## Capitulo 4 - Metodo
Arquivo:
- `text/4_Metodo/4_Metodo.tex`

Secoes congeladas:
1. Desenho da pesquisa
2. Dados e pipelines de processamento
3. Engenharia de features
4. Configuracao do modelo TFT
5. Protocolo experimental (splits, seeds, folds)
6. Metricas de avaliacao (pontuais e probabilisticas)
7. Analytics Store e governanca de experimento
8. Criterios de qualidade e validacao

## Capitulo 5 - Resultados e discussao
Arquivo:
- `text/5_Resultados/5_Resultados.tex`

Secoes congeladas:
1. Cenarios experimentais avaliados
2. Resultados agregados por horizonte e split
3. Analise da incerteza (quantis, cobertura, largura de intervalo)
4. Comparacoes entre configuracoes e feature sets
5. Analise estatistica pareada (quando aplicavel)
6. Interpretabilidade e implicacoes
7. Ameacas a validade dos resultados

## Capitulo 6 - Conclusoes
Arquivo:
- `text/6_Conclusoes/6_Conclusoes.tex`

Secoes congeladas:
1. Sintese dos achados
2. Contribuicoes do trabalho
3. Limitacoes
4. Trabalhos futuros

## Capitulo 7 - Referencias
Arquivo:
- `text/7_Referencias/7_Referencias.bib`

Escopo de atualizacao:
- substituir base de template por referencias aderentes ao recorte atual.

## Capitulo 8 - Apendices
Arquivo:
- `text/8_Apendices/8_Apendices.tex`

Escopo sugerido:
- tabelas completas de experimento, configuracoes, e detalhes operacionais.

## Capitulo 9 - Anexos
Arquivo:
- `text/9_Anexos/9_Anexos.tex`

Escopo sugerido:
- materiais complementares externos quando necessario.

---

## Regra de escrita (congelada)
- O texto deve refletir pipeline real do projeto: dados -> features -> treino TFT -> inferencia -> analytics -> avaliacao.
- Evitar retorno ao escopo antigo de classificacao de sentimento com CNN como tema central.
- Manter consistencia entre: titulo, problema, objetivos, metodo, resultados e conclusoes.

# → Evidence Log

Objetivo: registrar evidencias de forma rastreavel para suportar afirmacoes no TCC e no artigo.

Detalhamento do objetivo:
- Vincular cada afirmacao relevante a uma evidencia observavel e reproduzivel.
- Registrar contexto de experimento (configuracao, periodo, ativo, split, horizonte) para auditoria.
- Facilitar escrita de resultados, discussoes e limitacoes com base em fatos.
- Evitar conclusoes baseadas apenas em memoria ou interpretacao nao documentada.

## Template de entrada
- Data:
- Questao/Hipotese:
- Experimento/Execucao:
- Configuracao-chave:
- Resultado observado:
- Interpretacao:
- Artefatos (paths):
- Uso no texto (TCC/Artigo/Ambos):

## Entradas
- [a preencher]