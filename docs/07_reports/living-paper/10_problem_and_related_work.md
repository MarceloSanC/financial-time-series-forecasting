---
title: Living Paper - Problem and Related Work
scope: Base textual para o Capitulo 3 do TCC (Fundamentacao Teorica) e Related Work do artigo. Cobre previsao de series financeiras, modelagem com deep learning, TFT, predicao quantilica, avaliacao OOS e reprodutibilidade.
update_when:
  - revisao de literatura for expandida
  - novas referencias bibliograficas centrais forem incorporadas
  - delimitacao do escopo da revisao mudar
canonical_for: [living_paper_related_work, tcc_chapter_3_source, literature_review_source]
---

# 10 - Problem and Related Work

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

## Base da Fundamentação Teórica (v1 sincronizada com `text/3_Revisao_Teorica`)
- Previsão financeira: tensão entre eficiência de mercado e adaptação dinâmica de regimes.
- Deep learning temporal: uso condicionado a desenho experimental rigoroso e controle de leakage.
- TFT: justificativa por integração de covariáveis heterogêneas, multi-horizonte e interpretabilidade.
- Predição quantílica: incerteza como componente central da qualidade preditiva.
- Avaliação OOS: comparação justa requer alinhamento temporal e teste estatístico pareado.
- Reprodutibilidade: registro auditável de execuções e artefatos como requisito metodológico.

Referências nucleares do capítulo:
- `FAMA1991`, `LO2004`
- `LIMZOHREN2021`, `LIMETAL2021TFT`
- `KOENKERBASSETT1978`, `GNEITING2007`
- `DIEBOLDMARIANO1995`
- `PINEAU2021REPRODUCIBILITY`
