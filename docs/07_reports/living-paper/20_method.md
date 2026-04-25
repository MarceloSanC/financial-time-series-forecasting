# 20 - Method

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

## Base do Método (v1 sincronizada com `text/4_Metodo`)
- Desenho: pesquisa quantitativa e experimental-computacional com foco em validade metodológica.
- Pipeline: ingestão -> features -> dataset -> treino TFT -> inferência -> atualização analítica.
- Dados: combinação de mercado, sentimento agregado, indicadores técnicos e fundamentais.
- Persistência: camadas imutáveis e auditáveis para dados primários de execução + camada analítica derivada e reconstruível para comparação.
- Engenharia: famílias de features com controle anti-leakage e governança de warmup.
- Modelo: TFT em modo pontual e quantílico, com rastreabilidade por assinaturas/fingerprints.
- Protocolo: splits temporais explícitos, múltiplas sementes e alinhamento estrito por `target_timestamp` em comparações pareadas.
- Métricas: pontuais (RMSE, MAE, DA, viés) e probabilísticas (quantis, cobertura, largura de intervalo).
- Qualidade: gates de integridade temporal, consistência contratual e monotonicidade de quantis.
