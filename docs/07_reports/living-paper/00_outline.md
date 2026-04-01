# Living Paper - Outline

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
