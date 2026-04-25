# Baselines

Objetivo: definir o contrato canonico para baselines usados em comparacoes OOS
contra o candidato TFT.

Baselines nao sao modelos auxiliares decorativos. Eles definem a escala minima
de comparacao para qualquer claim de superioridade preditiva.

## Fonte Da Verdade

- O baseline primario de uma rodada confirmatoria deve ser declarado no
  pre-registro antes da execucao da Fase B.
- Este documento lista baselines admissiveis e requisitos de comparabilidade.
- O `STRATEGIC_DIRECTION.md` define o papel estrategico dos baselines, mas nao
  fixa sozinho o baseline primario de uma rodada.

## Baselines Recomendados

| Baseline | Uso | Saida esperada |
|---|---|---|
| `zero_return` / random walk de preco | Referencia primaria default para retorno diario | ponto e, se aplicavel, quantis via distribuicao residual |
| Media historica rolling | Referencia simples com informacao somente passada | ponto e quantis historicos |
| AR(1) | Referencia linear minima para dependencia serial | ponto e quantis/residuos se implementado |
| EWMA-vol | Referencia probabilistica para largura de intervalo | quantis ou intervalo calibrado por volatilidade |
| Quantis historicos rolling | Referencia quantilica nao-parametrica | p10, p50, p90 |

## Requisitos De Comparabilidade

Todo baseline usado em decisao deve:

- ser gerado para o mesmo `asset`, `split`, `horizon` e `target_timestamp` do TFT;
- respeitar a mesma janela temporal e a mesma regra de disponibilidade de dados;
- ser persistido no mesmo grao de `fact_oos_predictions`;
- possuir `run_id`, `model_version` ou identificador equivalente rastreavel;
- entrar nos testes estatisticos apenas pela intersecao exata de
  `target_timestamp`;
- ter parametros e janelas declarados no pre-registro ou em emenda datada.

## Regras De Decisao

- H2a compara o TFT contra o baseline primario pre-declarado.
- H2b compara o TFT contra todos os baselines simples pre-declarados.
- A ausencia de superioridade contra baseline nao invalida o TCC; muda a
  conclusao para limite empirico, qualidade probabilistica ou diagnostico de
  falha, conforme `STRATEGIC_DIRECTION.md`.
- Comparacoes por RMSE/DA sao secundarias quando a rodada declara pinball como
  metrica primaria.

## Usos Proibidos

- Escolher o baseline primario depois de observar os resultados da Fase B.
- Reportar superioridade contra um baseline nao persistido ou nao alinhado por
  `target_timestamp`.
- Usar baseline fraco como unica comparacao quando baselines simples mais fortes
  estao disponiveis.
- Misturar horizontes ou splits no mesmo teste pareado.

## Artefatos Esperados

- `fact_oos_predictions`: previsoes por baseline no mesmo grao do TFT.
- `gold_prediction_metrics_by_run_split_horizon`: metricas por baseline.
- `gold_dm_pairwise_results`: DM pareado TFT vs baseline.
- `gold_mcs_results`: inclusao/exclusao no conjunto de modelos candidatos.
- `gold_paired_oos_intersection_by_horizon`: tamanho da intersecao pareada.

## Referencias

- `docs/00_overview/STRATEGIC_DIRECTION.md`
- `docs/04_evaluation/METRICS_DEFINITIONS.md`
- `docs/04_evaluation/STATISTICAL_TESTS.md`
- `docs/08_governance/preregistration_round1_<date>.md` (a criar por rodada)
