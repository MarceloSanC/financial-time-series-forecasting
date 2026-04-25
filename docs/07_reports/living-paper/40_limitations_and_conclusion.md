# 40 - Limitations and Conclusion

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

## Limitacoes ja estabelecidas pelo direcionamento estrategico

Estas limitacoes devem aparecer no Capitulo 6, independentemente do resultado
da Fase B/C:

- Estudo single-asset: resultados restritos a AAPL no periodo analisado.
- Sem claim de generalizacao para outros ativos, mercados ou periodos.
- Sem inferencia causal: VSN, permutation importance e ablation indicam
  contribuicao preditiva condicional ao modelo, nao causalidade.
- Retornos diarios de ativo liquido tem edge esperado baixo; ausencia de
  superioridade contra baseline e resultado empiricamente plausivel.
- h+30 e suplementar por padrao devido a amostra efetiva pequena e sobreposicao
  temporal.
- Round 0 e exploratoria; claims confirmatorios dependem da Fase B
  pre-registrada.
- Interpretabilidade local e ilustrativa; conclusoes de contribuicao devem vir
  de evidencia global/por horizonte e estabilidade entre seeds/folds.

## Resultados validos mesmo com hipoteses refutadas

- Se H2a for refutada, o trabalho ainda pode concluir sobre limites do TFT em
  AAPL sob protocolo OOS auditavel.
- Se o modelo nao melhorar RMSE/DA, mas produzir intervalos calibrados, a
  contribuicao e probabilistica, nao pontual.
- Se a calibracao falhar, a contribuicao vira diagnostico de risco, cobertura e
  limites do pipeline atual.
- Se VSN, permutation e ablation divergirem, a conclusao correta e instabilidade
  de contribuicao preditiva.

## Trabalhos futuros

- Avaliacao multi-asset para testar generalizacao cross-sectional.
- Classificacao ou deteccao de regimes como estudo separado, com rotulos ou
  metodologia propria.
- Avaliacao de causalidade/econometria apenas com desenho especifico para esse
  objetivo.
- Aplicacao em portfolio/trading apenas apos validacao fora do escopo atual.
