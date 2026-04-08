# Post-Round-1 Model Selection Checklist

Objetivo: definir os passos canonicos apos a primeira rodada de experimentos para transformar resultados de sweep em decisao final robusta, reproducivel e defensavel academicamente.

Contexto concluido (entrada desta etapa):
- sweep baseline para identificar hiperparametros mais sensiveis
- sweep extensivo por feature set para achar melhores configuracoes por conjunto
- sweep explicito com configs vencedoras por feature set para comparacao robusta entre `modelo_otimizado + feature_set`

Convencao de rodadas:
- Round 0 (exploratoria): prefixos `0_X_X`.
- Round 1 (confirmatoria): prefixos `1_X_X`.
- Este checklist governa a transicao de `0_X_X` para `1_X_X` e a decisao final.

---

## 0) Gate de entrada (obrigatorio)

- [ ] Cohort oficial definido (ex.: prefixo `0_2_3_`) e documentado.
- [ ] Shortlist oficial da Round 0 congelada (champion provisório + fallback por horizonte).
- [ ] Regra de naming da Round 1 definida (ex.: `1_0_0`, `1_0_1`).
- [ ] `python -m src.main_refresh_analytics_store --fail-on-quality` sem falhas bloqueantes para o cohort.
- [ ] Tabelas estatisticas nao vazias para o cohort:
  - [ ] `gold_dm_pairwise_results`
  - [ ] `gold_mcs_results`
  - [ ] `gold_win_rate_pairwise_results`
  - [ ] `gold_model_decision_final`
- [ ] Relatorio de plots versionado para o cohort (arquivo em `docs/07_reports/`).

Critério de aceite:
- [ ] Sem isso, nenhuma conclusao final de vencedor pode ser emitida.

---

## 1) Execucao confirmatoria da Round 1 (P0)

- [ ] Criar e executar cohort confirmatorio com prefixo `1_X_X` (recomendado: iniciar em `1_0_0`).
- [ ] Incluir apenas finalistas congelados da Round 0.
- [ ] Repetir exatamente o protocolo estatistico da Round 0 (comparabilidade estrita).
- [ ] Validar que as conclusoes da Round 0 se sustentam no cohort confirmatorio.

Criterio de aceite:
- [ ] Round 1 concluida com artefatos completos e pronta para decisao final.

---

## 2) Fechamento da decisao para h+1 (P0)

- [ ] Consolidar leaderboard por `config + feature_set` com:
  - [ ] RMSE, MAE, DA
  - [ ] Pinball, PICP, MPIW
  - [ ] `n_oos`
- [ ] Aplicar regra de selecao com prioridade explicita:
  1. significancia pareada (DM/win-rate)
  2. inclusao no MCS
  3. calibracao (PICP proximo do nominal com MPIW contido)
  4. metrica primaria (RMSE/MAE)
- [ ] Classificar candidatos em:
  - [ ] Campeao primario
  - [ ] Campeao alternativo (fallback)
  - [ ] Rejeitados (com motivo)

Critério de aceite:
- [ ] Top-1 e fallback definidos com justificativa estatistica e de risco.

---

## 3) Extensao multi-horizonte (P0)

- [ ] Repetir decisao para `h+7` e `h+30` no mesmo protocolo.
- [ ] Verificar se o campeao de `h+1` se sustenta nos outros horizontes.
- [ ] Se houver conflito entre horizontes, definir politica:
  - [ ] campeao por horizonte
  - [ ] ou modelo unico com melhor compromisso medio

Critério de aceite:
- [ ] Tabela final com recomendacao por horizonte (ou regra de consolidacao documentada).

---

## 4) Robustez e estabilidade (P0)

- [ ] Validar dispersao por fold/seed (media, desvio, IQR, IC95).
- [ ] Marcar como fragil qualquer ganho pequeno com variancia alta.
- [ ] Confirmar consistencia do ranking (top-k) entre folds/seeds.

Critério de aceite:
- [ ] Campeao final nao depende de unico fold/seed para se manter competitivo.

---

## 5) Calibracao probabilistica final (P0)

- [ ] Confirmar cobertura nominal vs observada por horizonte.
- [ ] Quantificar under/over-coverage (em pontos percentuais).
- [ ] Aplicar criterio de aprovacao de incerteza:
  - [ ] cobertura aceitavel
  - [ ] largura de intervalo (MPIW) nao excessiva

Critério de aceite:
- [ ] Modelo final aprovado para uso probabilistico (nao apenas pontual).

---

## 6) Interpretabilidade final (P1)

- [ ] Fechar importancia global por horizonte (top-k + all-features).
- [ ] Adicionar visao agregada por familia de features:
  - [ ] baseline
  - [ ] technical
  - [ ] sentiment
  - [ ] fundamental
- [ ] Verificar disponibilidade de contribuicao local para o cohort final.
- [ ] Se local contribution estiver indisponivel, registrar explicitamente como limitacao de escopo/dados.

Critério de aceite:
- [ ] Narrativa de "por que o modelo funciona" sustentada por evidencias globais e limitacoes locais claras.

---

## 7) Benchmark academico e posicionamento (P1)

- [ ] Comparar achados com literatura de escopo equivalente.
- [ ] Registrar convergencias/divergencias de forma objetiva.
- [ ] Evitar claims de dominancia universal quando evidencias forem incrementais.

Critério de aceite:
- [ ] Secao de benchmark incluida no relatorio final com referencias e limites.

---

## 8) Pacote final para defesa (P0)

- [ ] Tabela de decisao final por horizonte pronta para reproducao.
- [ ] Relatorio unico de analise (plots + tabelas + conclusao + limites).
- [ ] Lista de riscos residuais e proximos experimentos priorizados.
- [ ] Comandos de reproducao documentados em runbook.

Critério de aceite:
- [ ] Um avaliador externo consegue reproduzir e entender a decisao final sem retrain adicional.

---

## 9) Sensibilidade de janela temporal (AAPL) (P1)

- [ ] Rodar ao menos 3 estrategias de janela temporal para AAPL:
  - [ ] janela curta (recente)
  - [ ] janela media
  - [ ] janela longa
- [ ] Manter o restante do protocolo fixo para comparacao justa.
- [ ] Selecionar janela final por OOS recente + calibracao (PICP/MPIW), nao apenas RMSE.

Criterio de aceite:
- [ ] Comprimento de janela final definido com justificativa empirica e estatistica.

---

## 10) Proximos passos tecnicos apos decisao (P2)

- [ ] Definir pacote de inferencia operacional do campeao e fallback.
- [ ] Definir monitoramento em producao:
  - [ ] degradacao de erro
  - [ ] drift
  - [ ] calibracao de intervalos
- [ ] Definir gatilhos objetivos de retreino.

Critério de aceite:
- [ ] Plano de operacao continua do modelo aprovado e documentado.

---

## Definition of Done da etapa pos-round-1

- [ ] Existe recomendacao final por horizonte com justificativa estatistica robusta.
- [ ] O trade-off desempenho x calibracao x robustez esta documentado.
- [ ] A contribuicao de features esta explicada sem overclaim causal.
- [ ] Os artefatos necessarios para defesa/reproducao estao versionados em `docs/07_reports` e `data/analytics/gold`.
