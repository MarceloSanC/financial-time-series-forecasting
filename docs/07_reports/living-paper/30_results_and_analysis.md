# 30 - Results and Analysis

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

## Validacao de hipoteses (quantis)

### H1. Mapeamento errado na extracao de quantis (ordem do tensor interpretada incorretamente)
- Como validado:
  - Inspecao de `src/adapters/pytorch_forecasting_tft_inference_engine.py` e `src/adapters/pytorch_forecasting_tft_trainer.py`.
  - Confirmacao de que p10/p50/p90 sao extraidos por indice de proximidade dos niveis (`argmin(abs(q_levels - alvo))`), e nao por posicao fixa.
  - Checagem empirica no sweep `0_2_3`: 421 linhas invalidas em 70 runs (padrao esparso, nao sistematico).
- Conclusao:
  - A hipotese de mapeamento posicional invertido foi refutada como causa principal atual.

### H2. `quantile_levels` inconsistente entre treino e inferencia
- Como validado:
  - Em `fact_config` para `0_2_3`, `quantile_levels_json` ficou unificado em `[0.1, 0.5, 0.9]` (675/675, 1 valor distinto).
  - Nos 70 artefatos de runs com erro, leitura de `config.json` sem divergencia de `quantile_levels`.
  - Carregamento real via `LocalTFTInferenceModelLoader` mostrando consistencia entre:
    - `training_config.quantile_levels = [0.1, 0.5, 0.9]`
    - `model.loss.quantiles = [0.1, 0.5, 0.9]`
- Conclusao:
  - A hipotese de inconsistencia treino vs inferencia foi refutada no escopo atual.





### H3. Crossing real de quantile regression
- Como validado:
  - Medicao de crossing por run no escopo `0_2_3` e comparacao com erro pontual OOS.
- Evidencia:
  - 421 violacoes em 674.820 linhas (0,0624%), presentes em 70/675 runs.
  - Runs com crossing tiveram pior erro de teste medio:
    - `test_rmse`: 0,020796 vs 0,018696
    - `test_mae`: 0,014826 vs 0,013536
  - Correlacao positiva entre taxa de crossing e erro de teste:
    - corr com `test_rmse` ~ 0,1449
    - corr com `test_mae` ~ 0,1464
- Conclusao:
  - Hipotese suportada: crossing real existe no output quantilico e associa-se a piora de desempenho OOS.

### H4. Instabilidade numerica/otimizacao
- Como validado:
  - Associacao de crossing com `learning_rate`, `batch_size` e proxies de estabilidade de treino.
  - Analise de variabilidade por grupos de hiperparametros (5 seeds x 3 folds).
- Evidencia:
  - Nao houve suporte para a versao simplificada "LR alto/treino curto/batch pequeno":
    - crossing maior em quartis mais baixos de LR;
    - runs com crossing nao pararam antes (mais epocas em media);
    - batch pequeno nao foi o principal padrAo associado.
  - Houve variabilidade entre repeticoes para alguns grupos (std da taxa de crossing por grupo chegando a ~0,02244; media ~0,00177).
- Conclusao:
  - Hipotese parcialmente suportada: existe componente de instabilidade/sensibilidade entre repeticoes, mas nao por um unico gatilho simples (LR alto etc.).

### H5. Problema de escala/inversao no pos-processamento
- Como validado:
  - Busca de codigo por `inverse_transform`/desnormalizacao em fluxo de predicao quantilica.
  - Revisao de `_apply_scalers` em inferencia e persistencia OOS.
- Evidencia:
  - O pipeline nao aplica inverse transform em `quantile_p10/p50/p90` antes da gravacao.
  - A escala e aplicada nas features de entrada; `target_return` e protegido no caminho de inferencia.
- Conclusao:
  - Hipotese refutada como causa principal atual.

### H6. Mistura de horizonte/split no parser
- Como validado:
  - Revisao da montagem de matrizes no trainer e da persistencia em `_persist_fact_oos_predictions`.
  - Verificacao empirica de distribuicao das violacoes por horizonte e por `max_prediction_length`.
- Evidencia:
  - `421/421` violacoes no `horizon=1`.
  - `0` violacoes em `horizon>1`.
  - `0` violacoes em runs com `max_prediction_length>1` no conjunto analisado.
- Conclusao:
  - Hipotese refutada para o problema atual.
  - Recomendado manter teste de regressao para parser multi-horizonte como hardening.



### H7. Dados com regime shift forte
- Como validado:
  - Analise no escopo `0_2_3` por concentracao temporal das violacoes de ordem quantilica.
  - Proxy OOD por run com `z_train = |y_true - media_treino|/desvio_treino`.
  - Proxy de regime via volatilidade local (rolling std 21d) por `target_timestamp_utc`.
- Evidencia:
  - Violacoes concentram-se em meses de 2019-2020 com taxas mensais superiores ao baseline.
  - `z_train` medio maior nas linhas invalidas (~0,971) que nas validas (~0,818).
  - Taxa de violacao cresce em faixas mais OOD (`z>=2.0/2.5`).
  - Alta volatilidade local apresenta taxa maior de violacao (0,000813) que baixa volatilidade (0,000542).
- Conclusao:
  - Hipotese parcialmente suportada: ha associacao entre regime/OOD e degradacao do head quantilico.
  - A evidência e correlacional; nao estabelece causalidade unica.



#### Acoes corretivas propostas para H7
1. Mitigacao na origem (treino/calibracao)
- Introduzir restricao de monotonicidade no treino do head quantilico (penalizar crossing `q10>q50` e `q50>q90`) ou adotar parametrizacao monotona por construcao (`q50`, `d1=softplus`, `d2=softplus`, com `q10=q50-d1` e `q90=q50+d2`).
- Priorizar calibracao probabilistica no criterio de selecao (pinball/PICP/MPIW) junto com erro pontual, com validacao por horizonte.
- Reforcar robustez em janelas de regime mais volatil (reweight/stratified validation), para reduzir degradacao do quantile head fora da distribuicao de treino.

2. Garantia de contrato na saida (producao)
- Aplicar rearranjo monotono dos quantis como guardrail final de inferencia para garantir `p10<=p50<=p90` em 100% das linhas.
- Registrar auditoria antes/depois (taxa de crossing, impacto em PICP/MPIW/pinball) para nao mascarar comportamento do modelo.
- Tratar o rearranjo como hardening de confiabilidade, nao substituto de melhoria de modelagem.

## Rascunho inicial
- Escopo analisado: coorte `0_2_3_` (AAPL), com foco principal em `h+1`.
- Resultado pontual: faixa de RMSE estreita entre candidatos (`~0.01335` a `~0.01341`), sem separação robusta por ponto estimado isolado.
- Resultado probabilístico: cobertura observada aproximada de `0.75` para cobertura nominal `0.80` (subcobertura no curto prazo).
- Trade-off incerteza: relação positiva entre largura de intervalo (MPIW) e cobertura (PICP), exigindo decisão por equilíbrio e não por extremo.
- Comparações pareadas: predominância de p-valores elevados no DM, com separação estatística apenas localizada.
- Interpretação: evidência de ganhos incrementais e ausência de dominância universal no escopo atual.
- Limites: dependência de coorte/ativo/horizonte e necessidade de replicação para fortalecer validade externa.
