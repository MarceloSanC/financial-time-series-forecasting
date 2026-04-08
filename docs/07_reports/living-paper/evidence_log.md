# Evidence Log

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

## Contexto da investigacao atual (2026-04-07)

Durante a rodada de analise do sweep explicito `0_2_3` (AAPL), o quality gate e as tabelas de avaliacao probabilistica indicaram inconsistencias em parte das previsoes quantilicas OOS, principalmente:

- violacoes de ordenacao de quantis (`quantile_p10 <= quantile_p50 <= quantile_p90`) em um subconjunto de linhas;
- poucos casos de largura de intervalo negativa (`quantile_p90 - quantile_p10 < 0`).

Neste ponto do projeto, os fluxos de treino, inferencia rolling e refresh analytics ja estavam operacionais e com artefatos gold/silver sendo gerados. A investigacao abaixo foi aberta para determinar se a causa estava em problema de contrato/layout da extracao de quantis ou em inconsistencias de configuracao entre treino e inferencia.

Hipoteses levantadas para explicar a causa raiz:

1. Mapeamento errado na extracao dos quantis (ordem de tensor interpretada incorretamente).
2. `quantile_levels` inconsistente entre treino e inferencia (lista/ordem divergente no artefato carregado).
3. Crossing real de quantile regression (quantis se cruzam em parte das amostras).
4. Instabilidade numerica/otimizacao (sensibilidade a seed/hiperparametros/regime).
5. Problema de escala/inversao no pos-processamento (desnormalizacao alterando ordenacao dos quantis).
6. Mistura de horizonte/split no parser (indices de matrizes atribuidos ao alvo errado).
7. Dados com regime shift forte (janelas fora da distribuicao de treino degradam o quantile head antes do ponto medio).

## Entradas
- Data: 2026-04-07
- Questao/Hipotese: H1 - Mapeamento errado na extracao dos quantis (tensor em uma ordem, codigo interpretando em outra).
- Experimento/Execucao:
  - Inspecao de codigo na inferencia e treino:
    - `src/adapters/pytorch_forecasting_tft_inference_engine.py`
    - `src/adapters/pytorch_forecasting_tft_trainer.py`
  - Checagem de dados no silver para sweep `0_2_3`:
    - `fact_oos_predictions` + `dim_run`.
- Configuracao-chave:
  - Regra de extracao observada no codigo: indices de p10/p50/p90 escolhidos por proximidade dos niveis (`argmin(abs(q_levels - alvo))`), nao por posicao fixa.
  - Escopo de dados analisado: runs com `parent_sweep_id` iniciando em `0_2_3_`.
- Resultado observado:
  - Em `0_2_3`: 421 linhas com ordem invalida de quantis, distribuidas em 70 runs.
  - Padrao observado esparso (nao massivo/sistematico).
- Interpretacao:
  - Se houvesse troca fixa de ordem (ex.: salvar q90 como p10), o problema apareceria de forma massiva na maior parte das linhas/runs.
  - A implementacao atual de mapeamento por nivel reduz risco de erro por layout/ordem de tensor.
  - H1 foi refutada como causa principal atual.
- Conclusao:
  - Status: refutada.
  - A causa principal atual nao e mapeamento errado de indices de quantis.
- Possiveis correcoes/melhorias:
  - Manter teste de contrato para garantir extracao por nivel (0.1/0.5/0.9) e nao por posicao fixa.
  - Incluir assertiva explicita de ordem dos niveis no ponto de extracao, com log de diagnostico em caso de divergencia.
  - Preservar monitor de taxa de crossing por run para detectar regressao de parser.
- Artefatos (paths):
  - `src/adapters/pytorch_forecasting_tft_inference_engine.py`
  - `src/adapters/pytorch_forecasting_tft_trainer.py`
  - `data/analytics/silver/fact_oos_predictions/asset=AAPL/**`
  - `data/analytics/silver/dim_run/asset=AAPL/**`
- Uso no texto (TCC/Artigo/Ambos):
  - Ambos.

- Data: 2026-04-07
- Questao/Hipotese: H2 - `quantile_levels` inconsistente entre treino e inferencia (lista/ordem diferente ou metadado divergente em checkpoint/config).
- Experimento/Execucao:
  - Checagem de consistencia em dados persistidos:
    - `fact_config.quantile_levels_json` para `0_2_3`.
  - Checagem por artefato em runs com erro de ordem:
    - leitura de `config.json` dos 70 `model_version` associados aos runs invalidos.
  - Checagem de carregamento real de modelo:
    - `LocalTFTInferenceModelLoader().load(...)` e comparacao entre `training_config.quantile_levels` e `model.loss.quantiles`.
- Configuracao-chave:
  - Escopo: sweep `0_2_3`, ativo `AAPL`.
  - Fluxo atual de inferencia usa `model.loss.quantiles` para extracao.
- Resultado observado:
  - `fact_config` em `0_2_3`: `quantile_levels_json = [0.1, 0.5, 0.9]` em 675/675 linhas (1 valor distinto).
  - Runs com erro de ordem: 70 artefatos checados, 0 com `quantile_levels` fora de `[0.1, 0.5, 0.9]`.
  - Exemplo de carregamento real:
    - `training_config.quantile_levels = [0.1, 0.5, 0.9]`
    - `model.loss.quantiles = [0.1, 0.5, 0.9]`
    - `prediction_mode = quantile`
- Interpretacao:
  - Nao foi encontrada evidencia de divergencia treino vs inferencia em `quantile_levels` no escopo atual.
  - H2 foi refutada como causa principal atual.
- Conclusao:
  - Status: refutada.
  - Nao ha inconsistencia de `quantile_levels` entre treino e inferencia no escopo analisado.
- Possiveis correcoes/melhorias:
  - Validar na carga do modelo: `training_config.quantile_levels == model.loss.quantiles`, falhando cedo em caso de mismatch.
  - Persistir `quantile_levels` no metadata do run e no payload de inferencia para rastreabilidade.
  - Adicionar check automatizado no quality gate para detectar divergencia entre configuracao persistida e checkpoint carregado.
- Artefatos (paths):
  - `src/adapters/local_tft_inference_model_loader.py`
  - `src/adapters/pytorch_forecasting_tft_inference_engine.py`
  - `data/analytics/silver/fact_config/asset=AAPL/**`
  - `data/models/AAPL/**/config.json`
- Uso no texto (TCC/Artigo/Ambos):
  - Ambos.


- Data: 2026-04-07
- Questao/Hipotese: H3 - Crossing real de quantile regression (o modelo aprendeu quantis que se cruzam em parte das amostras).
- Experimento/Execucao:
  - Escopo: runs `0_2_3_*` para AAPL.
  - Analise por run da taxa de violacao (`p10>p50` ou `p50>p90`) e associacao com erro pontual (RMSE/MAE OOS).
  - Checagem de efeito de tamanho amostral por run.
- Configuracao-chave:
  - Universo: 674.820 linhas OOS; 421 violacoes (0,0624%) em 70/675 runs.
- Resultado observado:
  - Runs com crossing tiveram pior erro de teste medio:
    - `test_rmse`: 0,020796 (com crossing) vs 0,018696 (sem crossing)
    - `test_mae`: 0,014826 (com crossing) vs 0,013536 (sem crossing)
  - Correlacao positiva (fraca a moderada) entre taxa de crossing e erro de teste:
    - corr(`invalid_rate`,`test_rmse`) ~ 0,1449
    - corr(`invalid_rate`,`test_mae`) ~ 0,1464
  - Nao houve diferenca relevante de tamanho amostral por run (`n` medio praticamente igual).
- Interpretacao:
  - Evidencia suporta H3 como mecanismo real presente: crossing quantilico ocorre no output do modelo e associa-se a piora de erro OOS.
  - O efeito e localizado (baixa taxa global), mas consistente em subgrupos de runs.
- Conclusao:
  - Status: suportada.
  - Existe crossing real de quantile regression no output do modelo, com associacao a pior erro OOS.
- Possiveis correcoes/melhorias:
  - Melhorar treinamento probabilistico: ajustar regularizacao/capacidade e priorizar calibracao por horizonte.
  - Avaliar perda com penalizacao de crossing ou parametrizacao monotona dos quantis.
  - Aplicar rearranjo monotono como guardrail de saida apenas com auditoria before/after (taxa crossing, PICP, MPIW, pinball).
  - Introduzir monitor por regime/periodo para identificar concentracao de crossing em janelas especificas.
- Artefatos (paths):
  - `data/analytics/silver/fact_oos_predictions/asset=AAPL/**`
  - `data/analytics/silver/fact_split_metrics/asset=AAPL/**`
  - `data/analytics/silver/dim_run/asset=AAPL/**`
- Uso no texto (TCC/Artigo/Ambos):
  - Ambos.


- Data: 2026-04-07
- Questao/Hipotese: H4 - Instabilidade numerica/otimizacao (LR alto, treino curto, seed sensivel, batch pequeno).
- Experimento/Execucao:
  - Escopo: runs `0_2_3_*` para AAPL.
  - Analise de associacao entre crossing por run e hiperparametros (`learning_rate`, `batch_size`).
  - Analise de proxies de estabilidade de treino (`last_epoch`, `best_epoch`, `overfit_gap_last`).
  - Analise de sensibilidade por seeds/folds para mesmo grupo de hiperparametros (config canônica sem seed/split metadata).
- Configuracao-chave:
  - Agrupamento por 45 grupos de configuracao (15 execucoes por grupo = 5 seeds x 3 folds).
- Resultado observado:
  - Nao houve suporte para sub-hipoteses literais "LR alto" e "treino curto":
    - crossing maior em quartis mais baixos de LR (nao nos mais altos);
    - runs com crossing tiveram, em media, mais epocas executadas (nao menos).
  - Nao houve suporte para "batch pequeno": runs com crossing tenderam a batch maior (mediana 128).
  - Houve suporte para componente de sensibilidade/instabilidade entre repeticoes:
    - desvio-padrao medio da taxa de crossing entre seeds/folds por grupo ~ 0,00177;
    - alguns grupos (especialmente em `S`) com variabilidade alta (std ate ~0,02244).
- Interpretacao:
  - H4 fica parcialmente suportada: existe sensibilidade de estabilidade entre repeticoes, mas os gatilhos simplificados (LR alto/treino curto/batch pequeno) nao explicam os dados observados neste escopo.
- Conclusao:
  - Status: parcialmente suportada.
  - Ha instabilidade entre repeticoes (seed/fold/config), mas nao sustentada pelos gatilhos simplificados testados.
- Possiveis correcoes/melhorias:
  - Reduzir sensibilidade: aumentar robustez de selecao por estabilidade (mediana/IC95 e criterio de consistencia entre seeds).
  - Revisar espaco de busca com foco em combinacoes estaveis (nao apenas melhor media de erro).
  - Adotar protocolo de retreino para candidatos finais com repeticoes extras e auditoria de variancia.
  - Registrar no ranking final penalidade para configuracoes com alta variabilidade de crossing.
- Artefatos (paths):
  - `data/analytics/silver/fact_config/asset=AAPL/**`
  - `data/analytics/silver/fact_epoch_metrics/asset=AAPL/**`
  - `data/analytics/silver/fact_split_metrics/asset=AAPL/**`
  - `data/analytics/silver/fact_oos_predictions/asset=AAPL/**`
  - `data/analytics/silver/dim_run/asset=AAPL/**`
- Uso no texto (TCC/Artigo/Ambos):
  - Ambos.

- Data: 2026-04-07
- Questao/Hipotese: H5 - Problema de escala/inversao no pos-processamento (desnormalizacao/reversao de scaler invertendo relacao entre quantis).
- Experimento/Execucao:
  - Inspecao de codigo de escala e persistencia:
    - `src/use_cases/train_tft_model_use_case.py`
    - `src/use_cases/run_tft_inference_use_case.py`
    - `src/adapters/pytorch_forecasting_tft_trainer.py`
  - Busca por uso de `inverse_transform`/desnormalizacao aplicada em `y_pred`/`quantile_*`.
- Configuracao-chave:
  - Em inferencia, `_apply_scalers` protege `target_return` e colunas estruturais (`time_idx`, `timestamp`, `asset_id`), aplicando scaler apenas nas features de entrada.
  - Quantis OOS sao persistidos diretamente dos tensores de saida do modelo (sem etapa de inverse transform no pos-processamento).
- Resultado observado:
  - Nao foi encontrado caminho de codigo que aplique `inverse_transform` em `quantile_p10/p50/p90` antes de persistir OOS.
  - O padrao de violacao e esparso, nao caracterizando inversao global apos desnormalizacao.
- Interpretacao:
  - A hipotese de inversao por pos-processamento de escala foi refutada como causa principal atual.
  - O problema remanescente e mais consistente com crossing pontual dos quantis produzidos pelo modelo.
- Conclusao:
  - Status: refutada.
  - Nao ha evidencia de inversao dos quantis causada por desnormalizacao/pos-processamento no pipeline atual.
- Possiveis correcoes/melhorias:
  - Manter cobertura de testes para protecao das colunas de alvo/quantis contra transformacoes indevidas.
  - Incluir validacao de integridade no ponto de persistencia OOS (ordem dos quantis e largura de intervalo).
  - Fortalecer logs de debug no caminho de escalonamento para facilitar investigacoes futuras.
- Artefatos (paths):
  - `src/use_cases/train_tft_model_use_case.py`
  - `src/use_cases/run_tft_inference_use_case.py`
  - `src/adapters/pytorch_forecasting_tft_trainer.py`
- Uso no texto (TCC/Artigo/Ambos):
  - Ambos.

- Data: 2026-04-07
- Questao/Hipotese: H6 - Mistura de horizonte/split no parser (saida multi-horizonte/multi-head lida com indice errado).
- Experimento/Execucao:
  - Inspecao da montagem e persistencia de matrizes por horizonte:
    - selecao de horizontes no trainer (`selected_horizons`, `selected_idx`).
    - persistencia em `_persist_fact_oos_predictions` usando o mesmo `h_idx` para `y_true`, `y_pred`, `q10`, `q50`, `q90`.
  - Validacao empirica no silver:
    - distribuicao das violacoes por `horizon`.
    - cruzamento com `fact_config.max_prediction_length`.
- Configuracao-chave:
  - Em `0_2_3`, os runs com violacao estao em modelos `max_prediction_length=1`.
- Resultado observado:
  - `421/421` violacoes em `horizon=1`.
  - `0` violacoes em `horizon>1`.
  - `0` violacoes em runs com `max_prediction_length>1` (no conjunto analisado).
- Interpretacao:
  - A hipotese de mistura de horizonte/split no parser foi refutada para o problema atual observado.
  - Como hardening, manter teste dedicado para cenarios multi-horizonte (quando houver runs com `max_prediction_length>1` em producao analitica).
- Conclusao:
  - Status: refutada.
  - Nao ha evidencia de erro de parser por mistura de horizonte/split no problema observado.
- Possiveis correcoes/melhorias:
  - Manter testes unitarios/integracao especificos para alinhamento `h_idx` entre `y_true`, `y_pred`, `q10`, `q50`, `q90`.
  - Incluir validacao de sanidade por horizonte no quality gate para execucoes multi-horizonte.
  - Expandir suite com caso sintetico multi-head para prevenir regressao silenciosa.
- Artefatos (paths):
  - `src/adapters/pytorch_forecasting_tft_trainer.py`
  - `src/use_cases/train_tft_model_use_case.py`
  - `data/analytics/silver/fact_oos_predictions/asset=AAPL/**`
  - `data/analytics/silver/fact_config/asset=AAPL/**`
- Uso no texto (TCC/Artigo/Ambos):
  - Ambos.


- Data: 2026-04-07
- Questao/Hipotese: H7 - Dados com regime shift forte (janelas fora da distribuicao de treino degradam o quantile head antes do ponto medio).
- Experimento/Execucao:
  - Escopo: runs `0_2_3_*` para AAPL.
  - Checagem 1 (concentracao temporal): taxa de violacao por mes (`target_timestamp_utc`).
  - Checagem 2 (proxy OOD por run): `z_train = |y_true - media_treino|/desvio_treino` usando janelas de treino por `run_id` (via `fact_run_snapshot`) e `target_return` do `dataset_tft`.
  - Checagem 3 (proxy de regime): taxa de violacao em timestamps de alta volatilidade local (rolling std 21d no `y_true` agregado por timestamp).
- Configuracao-chave:
  - Universo analisado: 674.820 linhas OOS no escopo `0_2_3`.
  - Violacoes observadas: 421 (taxa 0,0624%), concentradas em `horizon=1`.
- Resultado observado:
  - Concentracao temporal em meses de 2019-2020 (ex.: 2020-12, 2020-10, 2020-11), com taxa mensal superior ao baseline.
  - OOD proxy: `z_train` maior nas linhas invalidas (media ~0,971) vs validas (media ~0,818).
  - Taxa de violacao maior em amostras mais OOD:
    - `z>=2.0`: 0,000926 vs 0,000599
    - `z>=2.5`: 0,001073 vs 0,000606
    - `z>=3.0`: 0,000913 vs 0,000617
  - Regime proxy: taxa em alta volatilidade local maior que baixa volatilidade:
    - high_vol: 0,000813
    - low_vol: 0,000542
- Interpretacao:
  - Evidencia consistente com degradacao do componente quantilico em janelas mais fora da distribuicao de treino e em regime mais volatil.
  - Hipotese H7 fica parcialmente suportada (associacao observada), sem prova de causalidade unica.
- Conclusao:
  - Status: parcialmente suportada.
  - Ha associacao entre regime mais OOD/volatil e maior taxa de crossing, sem isolar causalidade unica.
- Possiveis correcoes/melhorias:
  - Recalibrar quantis por horizonte em janela recente (rolling/expanding) para reduzir misscoverage em mudanca de regime.
  - Adotar monitoramento de drift/regime com gatilhos de retreino/recalibracao.
  - Considerar ponderacao temporal ou treino com maior enfase em periodos recentes para melhorar adaptacao de caudas.
  - Segmentar analise de qualidade probabilistica por regime para evitar conclusoes agregadas enganosas.
- Artefatos (paths):
  - `data/analytics/silver/fact_oos_predictions/asset=AAPL/**`
  - `data/analytics/silver/dim_run/asset=AAPL/**`
  - `data/analytics/silver/fact_run_snapshot/asset=AAPL/**`
  - `data/processed/dataset_tft/AAPL/**`
- Uso no texto (TCC/Artigo/Ambos):
  - Ambos.


- Data: 2026-04-07
- Questao/Hipotese: Decisao tecnica apos H7 (mitigacao de crossing quantilico).
- Experimento/Execucao:
  - Sintese de alternativas para reduzir crossing sem perder rastreabilidade estatistica.
- Configuracao-chave:
  - Estrategia em 2 camadas: (1) melhoria no treino/calibracao, (2) guardrail de saida.
- Resultado observado:
  - Solucao proposta A (origem): restricao/parametrizacao monotona + calibracao probabilistica por horizonte.
  - Solucao proposta B (saida): rearranjo monotono com auditoria de impacto antes/depois.
- Interpretacao:
  - A combinacao A+B reduz crossing estrutural e garante contrato final de quantis em producao.
- Artefatos (paths):
  - `docs/07_reports/living-paper/30_results_and_analysis.md`
- Uso no texto (TCC/Artigo/Ambos):
  - Ambos.

