# Explainability

Objetivo: definir como interpretar e reportar contribuicao preditiva de features
no TCC/artigo sem transformar importancia de modelo em claim causal.

## Principio Central

As analises de explicabilidade respondem:

> quais familias de variaveis o modelo usou e a quais variaveis a previsao foi
> sensivel sob este protocolo, ativo, periodo e horizonte.

Elas nao respondem:

> quais variaveis causaram o retorno.

## Hierarquia De Evidencia

| Nivel | Papel | Forca do claim |
|---|---|---|
| Global por horizonte | Evidencia principal para conclusoes | Mais forte |
| Agregada por regime observado | Evidencia contextual, por exemplo alta vs baixa volatilidade | Intermediaria |
| Local pontual | Exemplo narrativo de uma previsao especifica | Ilustrativa |

Explicacoes locais podem entrar no texto, mas devem ser rotuladas como exemplos
ilustrativos e nao como conclusoes generalizaveis.

## Metodos Canonicos

### 1) VSN Weights

- Usar pesos da Variable Selection Network do TFT quando persistidos.
- Agregar por familia de feature, horizonte, split e, quando aplicavel, regime.
- Reportar dispersao entre seeds/folds sempre que houver repeticoes.
- Interpretacao permitida: "o modelo atribuiu maior peso medio a familia X".

### 2) Permutation Importance Por Familia

- Embaralhar todas as features de uma familia mantendo as demais intactas.
- Medir variacao de perda, preferencialmente `delta_pinball`.
- Aplicar bootstrap quando houver amostra suficiente.
- Interpretacao permitida: "a previsao foi sensivel a familia X sob esta coorte".

### 3) Ablation Explicativa

- Treinar N+1 modelos: all-features e um modelo removendo cada familia.
- Usar mesmos splits, seeds e hiperparametros compativeis com o candidato.
- Reportar `delta_pinball`, `delta_picp` e intervalos de confianca quando
  aplicavel.
- A ablation e analise de contribuicao, nao mecanismo para escolher um novo
  modelo vencedor.

## Estabilidade Minima

Claims de contribuicao devem ser qualificados por estabilidade:

- top-k de familias consistente entre seeds/folds fortalece o claim;
- divergencia entre metodos deve ser reportada como limitacao;
- resultado local sem estabilidade nao deve sustentar conclusao global;
- falta de artefato de VSN/permutation/ablation e indisponibilidade de evidencia,
  nao evidencia de irrelevancia.

## Linguagem Permitida

- "O modelo atribuiu maior peso relativo a..."
- "A perturbacao da familia X aumentou a perda em..."
- "A remocao da familia X reduziu/aumentou o pinball em..."
- "A contribuicao preditiva estimada foi instavel entre seeds."

## Linguagem Proibida

- "A feature X causou o retorno."
- "O mercado subiu porque o sentimento subiu."
- "A familia X e irrelevante em geral."
- "Esta explicacao local prova o padrao do mercado."

## Artefatos Esperados

- Tabelas agregadas por familia x horizonte.
- Figuras globais de importancia por horizonte.
- Relatorio de estabilidade entre seeds/folds.
- 3-5 exemplos locais apenas quando houver artefato suficiente e disclaimer.

## Referencias

- `docs/00_overview/STRATEGIC_DIRECTION.md`
- `docs/04_evaluation/METRICS_DEFINITIONS.md`
- `docs/03_modeling/TRAINING_PIPELINE.md`
- `docs/07_reports/living-paper/30_results_and_analysis.md`
