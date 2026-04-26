---
title: Writing Protocol (TCC + Artigo)
scope: Protocolo operacional para sessoes de escrita do TCC e artigo. Define fontes canonicas em ordem de prioridade, prompts padronizados, regra de propagacao (atualizar 00_outline primeiro) e checklist de sincronizacao por sessao.
update_when:
  - ordem de fontes canonicas mudar
  - novo prompt padronizado for adicionado
  - regra de propagacao for revisada
canonical_for: [writing_protocol, tcc_writing_rules, paper_writing_session_protocol]
---

# Writing Protocol (TCC + Artigo)

Status: padrao oficial para futuras sessoes de escrita.

## 1) Objetivo deste protocolo
Garantir que toda nova escrita mantenha:
- coerencia com a tese central e o recorte congelado;
- consistencia entre living-paper e TCC em LaTeX;
- rastreabilidade de decisoes, evidencias e mudancas;
- qualidade academica sem perda de contexto entre sessoes.

## 2) Fontes canonicas (ordem de prioridade)
1. `docs/07_reports/living-paper/00_outline.md`
2. `docs/07_reports/living-paper/chapter_structure_freeze.md`
3. `docs/07_reports/living-paper/tcc_mapping.md`
4. `docs/07_reports/living-paper/evidence_log.md`
5. `text/2_Introducao/...` ate `text/6_Conclusoes/...`

Regra: em caso de conflito, atualizar primeiro o `00_outline.md` e propagar depois.

## 3) Nao negociaveis de escopo
- Tema central: forecasting financeiro com TFT.
- Avaliacao: OOS + comparacao reproduzivel entre configuracoes.
- Incerteza: predicao quantilica (nao apenas ponto).
- Rastreabilidade: run_id, configuracoes, artefatos e evidencias.
- Fora de escopo: voltar para CNN de sentimento como eixo central.

## 4) Padrao de escrita por secao
Para qualquer bloco novo (TCC ou artigo), escrever nesta ordem:
1. Proposito da secao (1-2 frases)
2. Conteudo tecnico principal
3. Evidencia que sustenta afirmacoes
4. Limites/condicoes da afirmacao
5. Fecho conectando com a proxima secao

Regras de estilo:
- Linguagem academica objetiva, sem marketing.
- Evitar claims absolutos (usar condicoes e contexto).
- Evitar repeticao entre capitulos; cada secao precisa agregar algo novo.
- Manter termos tecnicos consistentes (TFT, OOS, quantis, leakage, reproducibilidade).

## 5) Fluxo obrigatorio por tarefa de escrita
1. Ler escopo: `00_outline.md` + `chapter_structure_freeze.md`.
2. Definir alvo: secao exata e arquivo destino.
3. Escrever primeiro no living-paper (rascunho base).
4. Propagar para `.tex` correspondente no TCC.
5. Atualizar `tcc_mapping.md` se houve mudanca de estrutura.
6. Registrar evidencias relevantes em `evidence_log.md`.
7. Rodar checklist de validacao (secao 6).

## 6) Checklist de validacao (antes de encerrar)
- [ ] O texto responde a pergunta de pesquisa definida no outline.
- [ ] O texto nao reintroduz escopo antigo (CNN-sentimento como foco).
- [ ] Objetivos, metodo, resultados e conclusoes estao alinhados entre si.
- [ ] Toda afirmacao relevante aponta para evidencia/artefato rastreavel.
- [ ] Terminologia esta consistente com arquivos anteriores.
- [ ] A secao escrita esta mapeada em `tcc_mapping.md` (se necessario).

## 7) Checklist de coerencia entre documentos
- [ ] Mudou tese/pergunta/recorte? Atualizar `00_outline.md` primeiro.
- [ ] Mudou estrutura de capitulo? Atualizar `chapter_structure_freeze.md`.
- [ ] Mudou objetivos? Sincronizar `00_outline.md` e `2_Introducao.tex`.
- [ ] Mudou resultados-chave? Atualizar `30_results_and_analysis.md` e depois `5_Resultados.tex`.
- [ ] Mudou conclusao-chave? Atualizar `40_limitations_and_conclusion.md` e `6_Conclusoes.tex`.

## 8) Template de prompt para sessoes futuras
Use este bloco como prompt-base quando iniciar uma nova rodada:

"""
Contexto fixo:
- Siga `docs/07_reports/living-paper/WRITING_PROTOCOL.md`.
- Preserve alinhamento com `docs/07_reports/living-paper/00_outline.md` e `docs/07_reports/living-paper/chapter_structure_freeze.md`.
- Nao altere escopo central (TFT + OOS + quantis + reproducibilidade).

Tarefa:
- Arquivo alvo: <arquivo>
- Secao alvo: <secao>
- Objetivo da rodada: <o que precisa ser escrito/revisado>

Requisitos:
- Escrever em tom academico objetivo.
- Explicitar premissas e limites.
- Garantir consistencia com objetivos e pergunta de pesquisa.
- Ao final, listar: (i) o que mudou, (ii) por que mudou, (iii) como foi validado.
"""

## 9) Politica de alteracoes estruturais
Se a alteracao impactar tese, recorte ou estrutura:
1. Abrir "proposta curta" no `00_outline.md`.
2. Validar consistencia com capitulos afetados.
3. Atualizar `chapter_structure_freeze.md` e `tcc_mapping.md`.
4. So depois editar os `.tex`.

## 10) Definicao de pronto (DoD) para escrita
Um bloco de texto esta "pronto" quando:
- possui objetivo claro;
- esta coerente com o escopo congelado;
- possui evidencias rastreaveis;
- nao conflita com sessoes anteriores;
- esta sincronizado entre living-paper e TCC (quando aplicavel).
