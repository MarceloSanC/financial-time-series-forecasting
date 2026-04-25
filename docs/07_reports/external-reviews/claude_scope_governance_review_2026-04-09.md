---
title: Claude Scope Governance Review 2026-04-09
scope: Review externo (Claude) datado de 2026-04-09 sobre governanca de escopo e rigor metodologico do projeto. Diagnostica sintomas estruturais (mistura de coortes, semantica de quantis, leakage potencial) e propoe arquitetura ScopeSpec incremental. Documento historico congelado.
update_when:
  - nunca apos publicacao (documento historico de review externo)
  - novas rodadas de review externo viram arquivos novos, nao editam este
canonical_for: [external_review_2026_04_09, scope_governance_review, claude_audit_2026_04_09]
---

# Auditoria Técnica: Forecasting de Retornos com TFT — Governança de Escopo e Rigor Metodológico

---

## A) Diagnóstico Crítico do Problema

### O problema é real? Sim. Severidade: Alta para conclusão acadêmica, Média para operação atual.

O problema central não é técnico — é epistemológico. Você está tentando fazer uma **afirmação causal comparativa** ("conjunto de features X supera Y") usando uma infraestrutura de avaliação que mistura populações heterogêneas. Isso invalida a conclusão antes mesmo de olhar para os números.

**Sintomas estruturalmente graves (bloqueantes para publicação/decisão):**

1. **Contaminação de coorte no quality gate global.** Se `ValidateAnalyticsQualityUseCase` usa dados de sweeps anteriores para calcular thresholds ou taxas de falha, a aprovação/reprovação de um candidato atual carrega ruído de experimentos extintos. Isso não é só "sujo" — é um viés de seleção não controlado. Um modelo pode passar o gate global apenas porque sweeps antigos puxaram a média para baixo. O inverso também ocorre: um modelo bom pode reprovar por passivo histórico de outro sweep.

2. **Ausência de grão `parent_sweep_id` em `gold_prediction_metrics_by_config`.** Sem essa chave no grão, qualquer agregação que você apresente como "resultado do experimento 0_2_3" pode incluir predições de configurações de 0_1_x que casualmente compartilham `config_id`. Isso é um erro de cardinalidade silencioso — não falha, mas produz números errados sem aviso.

3. **`gold_oos_quality_report` usando quantis raw onde o validador usa pós-guardrail.** Esse é um **split de semântica dentro do mesmo pipeline**. Se você reporta métricas (PICP, MPIW, pinball) sobre quantis raw e o guardrail não foi aplicado, mas o validator já usa pós-guardrail, os dois sistemas falam de populações diferentes. Qualquer comparação between-model que usa um lado de cada sistema é inválida.

**Sintomas operacionais (não bloqueantes, mas degradam reprodutibilidade):**

- Entrypoints de plots sem escopo uniforme: risco de gráficos em relatório mostrarem dados de sweeps mistos.
- Inferência indireta de sweep (sem chave explícita no grão): frágil a colisões de chave e difícil de auditar.
- Purge pós-operação usando quality global: falso negativo no gate de limpeza, não no gate de decisão — menos grave, mas gera confusão operacional.

---

## B) Validação dos Requisitos de Rigor

### O que está correto:

**Requisito 1 — Comparação pareada por `target_timestamp`:** Correto e obrigatório. Sem interseção temporal exata, você está comparando modelos em amostras diferentes. Para DM test isso é especialmente crítico: o teste assume que os diferenciais de erro são gerados pelo mesmo processo estocástico. Se as amostras temporais diferem, a estatística DM não tem distribuição conhecida sob H0.

**Requisito 2 — Escopo explícito de decisão:** Correto. Isso é o que separa um experimento reprodutível de uma análise exploratória. A exigência de "frozen set" declarado antes da avaliação final é boa prática que previne p-hacking implícito por seleção de janela.

**Requisito 3 — Protocolo homogêneo:** Correto, mas você está subestimando a profundidade disso. "Mesmos splits/folds/seeds" é necessário mas não suficiente. Você precisa garantir que:
- O mesmo lookback window foi usado para todos os candidatos
- A normalização/escalonamento foi fit no mesmo conjunto de treino
- O encoder length máximo é idêntico entre candidatos (TFT é sensível a isso)

**Requisito 4 — Contrato probabilístico consistente:** Correto e bem implementado conceitualmente. O guardrail monotônico é necessário. A auditoria before/after é necessária. A questão é que você precisa decidir: **métricas de avaliação usam pós-guardrail ou raw?** A resposta defensável academicamente é: **pós-guardrail**, porque é o que o modelo entrega ao usuário final. Reportar raw e pós-guardrail separadamente como análise de impacto do guardrail é um bônus valioso, mas a métrica primária deve ser pós-guardrail.

**Requisito 5 — Rastreabilidade por artefatos:** Correto e necessário. Sem isso, qualquer revisão do paper que pedir "rode novamente com configuração X" pode produzir resultados diferentes.

### O que está faltando:

**Lacuna crítica A — Teste de estacionariedade dos resíduos por candidato.** Antes de aplicar DM test, você precisa verificar se os diferenciais de loss são estacionários. Se os resíduos têm tendência temporal (o que é comum em dados financeiros com regime change), o DM test tem tamanho incorreto. Solução mínima: ADF/KPSS nos diferenciais de pinball loss por horizonte.

**Lacuna crítica B — Correção para múltiplas comparações.** Se você compara K conjuntos de features com DM/MCS, a taxa de falso positivo familiar explode. MCS controla isso parcialmente, mas você precisa ser explícito sobre qual é a hipótese primária (um único confronto candidato vs baseline) e quais são secundárias. Se não fizer isso, qualquer revisor vai questionar.

**Lacuna crítica C — Calibração não é só PICP.** PICP (cobertura do intervalo) pode ser alto mesmo com quantis mal calibrados se o intervalo for muito largo. Você precisa reportar PICP **conjunto com** MPIW e, idealmente, um reliability diagram (frequência empírica vs nominal para p10/p50/p90 separadamente). Isso é o mínimo para defender calibração probabilística.

**Lacuna operacional D — Seed de inferência.** TFT com dropout ativo em inferência é estocástico. Se você não fixar seed na inferência OOS, runs diferentes do mesmo modelo podem produzir quantis diferentes. Isso precisa ser documentado e controlado.

### O que pode ser simplificado:

- **Walk-forward com N folds** é desejável mas não obrigatório para um paper de forecasting financeiro com janela OOS longa (>252 dias). Um único split temporal bem justificado com análise de estabilidade por subsegmento (primeiro/segundo semestre OOS) é defensável.
- **Bootstrap de intervalos de confiança para DM** é nice-to-have se o N de observações OOS for razoável (>100 por horizonte).

---

## C) Julgamento sobre a Refatoração de Escopo

### Veredicto: Necessária agora, mas não como big bang. Necessária porque os sintomas graves são bloqueantes.

**Argumento para fazer agora:**

A rodada 0_2_4 é descrita como "comparação before/after com melhorias de qualidade/guardrail". Se você rodar 0_2_4 sem corrigir a governança de escopo, você vai gerar um resultado que não é comparável com 0_2_3 de forma limpa, porque o quality gate vai continuar misturando coortes. O before/after vai estar contaminado pelo mesmo problema que você está tentando resolver. Ou seja: adiar a refatoração de escopo invalida o experimento que você está planejando fazer.

**Riscos de fazer agora:**

- Risco de regressão em fluxos que dependem do comportamento global atual (especialmente se algum código downstream assume que qualidade global == qualidade do sweep).
- Risco de aumentar a complexidade do `ScopeSpec` além do necessário, criando um novo passivo de manutenção.
- Risco de timeline: se a refatoração demorar 3 semanas e o deadline acadêmico é próximo, pode não valer a pena fazer completo.

**Riscos de NÃO fazer agora:**

- Qualquer resultado de 0_2_4 é metodologicamente questionável.
- Se um revisor perguntar "como você garantiu que os modelos foram avaliados na mesma coorte?", a resposta honesta seria "não garantimos completamente". Isso é fatal para um paper de comparação de modelos.
- O passivo cresce: cada novo sweep adicionado sem governança de escopo aumenta a entropia do sistema.

**Trade-off objetivo:**

| Dimensão | Fazer agora | Adiar |
|---|---|---|
| Validade de 0_2_4 | Alta | Baixa |
| Risco de regressão | Médio | Zero |
| Complexidade adicionada | Média | Zero |
| Dívida técnica acumulada | Estável | Cresce |
| Defensabilidade acadêmica | Alta | Baixa |

---

## D) Proposta de Arquitetura Incremental

### Princípio norteador: consertar o caminho crítico para 0_2_4 primeiro, generalizar depois.

---

### Fase 0 — Remediação Cirúrgica (bloqueante para 0_2_4) — 3 a 5 dias

**Objetivo:** Garantir que a comparação 0_2_3 vs 0_2_4 seja válida sem refatoração completa.

**Entregável 1:** Adicionar `parent_sweep_id` como coluna obrigatória em `gold_prediction_metrics_by_config`. Não é refatoração — é uma migração de schema + backfill para 0_2_3.

**Critério de aceite:** `SELECT DISTINCT parent_sweep_id FROM gold_prediction_metrics_by_config` retorna exatamente os sweeps esperados, sem outros.

**Entregável 2:** Unificar semântica de quantis em `gold_oos_quality_report`. Decisão: pós-guardrail como primário, raw como coluna adicional com sufixo `_raw`. Nenhuma métrica de avaliação calcula sobre raw sem label explícito.

**Critério de aceite:** PICP calculado sobre `quantile_p10_post_guardrail` e `quantile_p90_post_guardrail` em todos os paths. Query de auditoria que compara PICP_raw vs PICP_post e reporta delta.

**Entregável 3:** Parâmetro `scope_sweep_prefix` obrigatório (sem default global) no entrypoint de quality gate e geração de tabelas de decisão. Valor `"global"` permitido explicitamente como opt-in consciente, não como default silencioso.

**Critério de aceite:** Rodar quality gate sem `--scope_sweep_prefix` retorna erro com mensagem explicativa. Rodar com `--scope_sweep_prefix=0_2_3` retorna apenas métricas dessa coorte.

---

### Fase 1 — ScopeSpec Mínimo Viável (necessário para 0_2_4) — 5 a 8 dias

**Objetivo:** Introduzir o objeto `ScopeSpec` no caminho crítico sem refatorar tudo.

**Entregável 1:** Dataclass `ScopeSpec` com campos:
```python
@dataclass
class ScopeSpec:
    scope_mode: Literal["global_health", "cohort_decision"]
    sweep_prefixes: list[str]  # obrigatório para cohort_decision
    splits: list[str] | None = None
    horizons: list[int] | None = None
    frozen_timestamp: datetime | None = None  # timestamp de congelamento do set
```

**Entregável 2:** `ValidateAnalyticsQualityUseCase` recebe `ScopeSpec` como parâmetro. Em `cohort_decision`, todos os checks usam filtro por `sweep_prefixes`. Em `global_health`, comportamento atual preservado.

**Critério de aceite:** Teste unitário com dois sweeps na base: quality gate em `cohort_decision` para sweep A não é afetado por dados ruins do sweep B. Teste deve falhar antes da mudança e passar depois.

**Entregável 3:** Purge pós-operação usa quality escopada (não global) para validação de resíduo zero.

**Critério de aceite:** Após purge de sweep A, quality check escopado para sweep A retorna zero registros. Quality global pode ainda retornar falhas de outros sweeps — isso é esperado e documentado.

---

### Fase 2 — Consistência de Superfície (melhoria de qualidade, não bloqueante) — ongoing

**Objetivo:** Uniformizar escopo em plots, CLIs, e inferência indireta. Não bloqueia 0_2_4.

**Entregável 1:** Todos os entrypoints de plot aceitam `--scope_sweep_prefix` e filtram dados antes de renderizar.

**Entregável 2:** Substituir inferência indireta de sweep por chave explícita `parent_sweep_id` em todas as tabelas gold restantes.

**Entregável 3:** Documentação de `ScopeSpec` com exemplos de uso para cada modo.

**Critério de aceite:** Não há gráfico gerado automaticamente que não declare explicitamente seu escopo no título ou metadado.

---

## E) Regras de Bloqueio para Decisão Acadêmica Final

### Gates obrigatórios (bloqueiam declaração de vencedor):

**Gate 1 — Interseção temporal.** O conjunto de `target_timestamp` usado para avaliar cada candidato deve ser idêntico. Verificação: `len(set_A.timestamps.symmetric_difference(set_B.timestamps)) == 0`. Se não for zero, a comparação é inválida.

**Gate 2 — Homogeneidade de protocolo.** Todos os candidatos foram treinados com os mesmos splits temporais, mesmo lookback, mesma semente de inicialização (ou média sobre as mesmas sementes). Verificação por inspeção de artefatos de treino persistidos.

**Gate 3 — Semântica de quantis unificada.** Todas as métricas de avaliação usam quantis pós-guardrail. Taxa de `quantile_guardrail_applied` deve ser reportada por candidato como informação de diagnóstico (não como gate, mas como dado).

**Gate 4 — PICP dentro de tolerância por quantil.** Para p10: cobertura empírica entre 0.07 e 0.13. Para p90: cobertura empírica entre 0.87 e 0.93. Para p50: entre 0.45 e 0.55. Candidato fora dessas bandas está mal calibrado e não pode ser declarado vencedor em regime probabilístico, mesmo que tenha melhor pinball loss (modelos descalibrados podem ter pinball baixo por razões espúrias).

**Gate 5 — Estacionariedade dos diferenciais de loss.** ADF test (p<0.05) nos diferenciais de pinball loss entre candidato e baseline para cada horizonte. Se não estacionário, DM test não é aplicável e deve ser substituído por análise de dominância estocástica por subperíodo.

### Warnings (não bloqueiam, mas devem ser reportados):

- Taxa de `quantile_guardrail_applied` > 5% para qualquer candidato (sinal de que o modelo está produzindo quantis estruturalmente ruins antes do guardrail).
- MPIW médio > 2 desvios padrão acima da baseline (intervalo excessivamente largo, calibração trivial).
- Win-rate por horizonte com variância alta entre subperíodos OOS (modelo não estável temporalmente).
- Diferença de pinball loss estatisticamente significativa no DM mas com effect size pequeno (Cohen's d < 0.2): significância estatística sem relevância prática.

---

## F) Plano de Validação Estatística Final

### Comparabilidade justa entre modelos:

**Passo 1 — Definir o conjunto de avaliação canônico antes de olhar resultados.** O `frozen_timestamp` no `ScopeSpec` serve exatamente para isso: você declara "avaliação acontece sobre predições geradas até T, para target_timestamps no intervalo [T1, T2]" antes de rodar qualquer métrica. Isso previne data snooping implícito na seleção da janela OOS.

**Passo 2 — Calcular métricas por horizonte separadamente.** Agregar todos os horizontes juntos mascara degradação de performance em horizontes longos, que é exatamente onde modelos complexos como TFT costumam deteriorar em relação a benchmarks simples. Reporte pinball loss e PICP para h=1, h=5, h=10 (ou os horizontes do seu projeto) separadamente.

**Passo 3 — Baseline obrigatório.** Se você não tem um baseline (random walk, média histórica, ou modelo AR simples), qualquer afirmação de superioridade do TFT não tem referência. A pergunta não é "qual feature set é melhor", mas "qual feature set supera o baseline por mais margem".

### Tratamento de múltiplos sweeps sem mistura indevida:

**Regra operacional:** Cada comparação reportada deve ter um `scope_id` explícito que identifica unicamente o conjunto de sweeps incluídos. Esse `scope_id` vai para o paper como identificador do experimento.

**Regra estatística:** Se você comparar K > 2 conjuntos de features, use MCS (Model Confidence Set, Hansen et al. 2011) como teste primário, não múltiplos DM pareados. MCS controla o FWER por construção. O resultado reportado é "conjunto de modelos que não podem ser rejeitados ao nível α=0.10".

**Tratamento de empates:** É comum que MCS não rejeite nenhum modelo. Nesse caso, o critério de desempate deve ser declarado a priori (ex.: menor MPIW para cobertura equivalente, ou menor latência de inferência). Não escolher o critério de desempate após ver os resultados.

### DM/MCS/win-rate de forma defensável:

**DM test:** Use a versão de Harvey, Leybourne & Newbold (1997) com correção de viés para amostras pequenas. Reporte o p-value two-sided. Nunca reporte DM sem reportar também o N de observações e a autocorrelação dos diferenciais de loss (se alta, o teste tem tamanho inflado).

**Win-rate:** Reportar como estatística descritiva, não como teste. "Modelo A tem menor pinball loss em 68% dos target_timestamps" é uma afirmação descritiva válida. "Portanto modelo A é melhor" é uma inferência que requer o DM test. Não confunda os dois.

**Calibração:** Use um reliability diagram com bandas de confiança bootstrap (1000 resamples). Cada quantil nominal (0.10, 0.50, 0.90) deve ter sua frequência empírica calculada e plotada contra a diagonal. Desvio sistemático da diagonal é evidência de miscalibração que não aparece no pinball loss agregado.

---

## G) Red Flags que Podem Invalidar Conclusões Mesmo Após Refatoração

**Red flag 1 — Look-ahead leak no encoder do TFT.**
TFT usa covariáveis conhecidas no futuro (`time_varying_known_reals`). Se qualquer feature técnica calculada sobre preços futuros foi colocada nessa categoria por engano, o modelo viu o futuro durante treino. Verificação obrigatória: inspecionar o manifesto de features e confirmar que cada feature em `time_varying_known_reals` é genuinamente conhecida no momento da previsão (ex.: calendário, feriados planejados). Features de retorno passado não pertencem a essa categoria.

**Red flag 2 — Normalização com dados OOS.**
Se o scaler (StandardScaler ou similar) foi fit em treino+OOS (ou se o target encoder do TFT usa estatísticas globais), há leakage. Verificação: o fit do scaler deve usar apenas dados com `target_timestamp <= split_date_treino`.

**Red flag 3 — Seleção de hiperparâmetros baseada em OOS.**
Se a HPO (rodadas 0_1_x) usou o conjunto OOS como critério de seleção (mesmo indiretamente, como early stopping monitorando loss OOS), os hiperparâmetros estão sobreajustados ao OOS. Nesse caso, você precisa de um hold-out separado (test set) para avaliação final, diferente do validation set usado na HPO. Se você não tem esse hold-out, a comparação 0_2_3 está comprometida estruturalmente.

**Red flag 4 — Regime change não modelado.**
AAPL em diferentes regimes de mercado (alta volatilidade, bear market, earnings seasons) pode tornar o OOS não representativo do treino. Se o período OOS inclui eventos estruturais ausentes no treino (ex.: choque de volatilidade, mudança de política de juros), o modelo está sendo avaliado fora da distribuição de treino. Isso não invalida o experimento, mas requer que você reporte performance por subregime e declare que os resultados são condicionais ao período analisado.

**Red flag 5 — Quantis pós-guardrail com taxa de intervenção alta.**
Se `quantile_guardrail_applied` > 10% para um candidato, o guardrail está mascarando um problema estrutural do modelo (quantis crus sistematicamente não monótonos). Nesse caso, o modelo não aprendeu a estrutura probabilística correta e o guardrail está "consertando" output inválido. Declarar esse modelo como competitivo é questionável.

**Red flag 6 — Ausência de teste de igualdade de distribuição dos erros.**
Antes do DM test, verifique se os diferenciais de pinball loss têm caudas pesadas. Se sim, o DM test paramétrico (baseado em normalidade assintótica) tem tamanho incorreto. Use a versão bootstrap do DM test ou o teste de Diebold-Mariano não-paramétrico.

---

## H) Recomendação Final Executiva

### Faça agora (obrigatório para validade de 0_2_4):

**1. Fase 0 completa nos próximos 3-5 dias.** Especificamente: (a) adicionar `parent_sweep_id` em `gold_prediction_metrics_by_config`, (b) unificar semântica de quantis para pós-guardrail como primário, (c) tornar `scope_sweep_prefix` obrigatório nos entrypoints de quality gate. Sem isso, 0_2_4 não produz evidência comparável com 0_2_3.

**2. Verificação de look-ahead leak (Red flag 1 e 2).** Isso tem custo baixo (inspeção de código + query de auditoria) e impacto potencial catastrófico. Deve ser feito antes de qualquer rodada de avaliação final.

**3. Definir e persistir o conjunto de avaliação canônico (`frozen_timestamp` + lista de `target_timestamps`)** antes de rodar métricas comparativas. Esse artefato vai para o paper como "Tabela 1 — Configuração do Experimento".

### Faça em paralelo com 0_2_4 (necessário para publicação):

**4. Fase 1 do ScopeSpec** — pode ser desenvolvida enquanto 0_2_4 roda, desde que Fase 0 já esteja no ar. O ScopeSpec mínimo viável não bloqueia a rodada, mas é necessário para que os resultados de 0_2_4 sejam auditáveis.

**5. Implementar reliability diagram com bootstrap** e ADF test nos diferenciais de loss. Esses são os dois itens faltantes mais críticos para defensabilidade estatística.

### Deixe para depois (melhoria, não bloqueante):

**6. Fase 2** — uniformização de plots e substituição de inferência indireta de sweep. Importante para manutenibilidade, mas não afeta validade das conclusões do paper.

**7. Walk-forward com múltiplos folds** — se o deadline permitir, agrega robustez. Se não, um único split temporal bem justificado com análise de subperíodo é suficiente.

---

**Nível de confiança desta recomendação:** Alto para os itens de Fase 0 e verificação de leakage — esses são consenso na literatura de avaliação de modelos de forecasting financeiro. Médio para o design específico do ScopeSpec — a arquitetura proposta é razoável, mas há alternativas igualmente válidas dependendo da stack existente. A suposição implícita desta auditoria é que o paper alvo tem rigor de venue A/B em forecasting ou ML financeiro; se for venue mais aplicado, alguns gates podem ser relaxados.

---

**Uma observação final que não foi solicitada mas é necessária:** O problema mais sério que identifico não é técnico. É que a decisão de qual feature set "vence" parece estar sendo tomada de forma iterativa, olhando para resultados parciais e ajustando o pipeline. Se for esse o caso, qualquer resultado final tem um grau de p-hacking implícito que nenhuma correção de infraestrutura resolve. A única solução é declarar a priori, por escrito, antes de rodar 0_2_4: qual é o candidato principal, qual é o baseline, qual é a métrica primária de decisão, e qual é o threshold de diferença mínima considerada relevante. Esse documento se torna o pre-registration do experimento e é o que diferencia ciência de mineração de dados.
---

## [GPT-5.3-Codex] Respostas Estruturadas ao Review do Claude

### [GPT-5.3-Codex] A) Diagnóstico Crítico do Problema

- [GPT-5.3-Codex] Concordo com a severidade proposta: alta para conclusao academica e media para operacao.
- [GPT-5.3-Codex] Concordo que o risco central e metodologico (mistura de populacoes de avaliacao), nao apenas de implementacao.
- [GPT-5.3-Codex] Confirmo que ha sinais concretos no projeto de mistura entre visao global e necessidade de coorte para decisao.
- [GPT-5.3-Codex] Ajuste de nuance: alguns riscos citados sao vulnerabilidades potenciais (estruturais), nao necessariamente erro material ativo em 100% das consultas atuais.

### [GPT-5.3-Codex] B) Requisitos de Rigor

- [GPT-5.3-Codex] Concordo integralmente com os cinco requisitos centrais:
  1. intersecao temporal exata em comparacao pareada,
  2. escopo explicito,
  3. protocolo homogeneo,
  4. contrato probabilistico consistente,
  5. rastreabilidade por artefatos persistidos.
- [GPT-5.3-Codex] Sobre "o que falta":
  - ADF/KPSS para diferenciais de loss e util, mas recomendo como P1/P2 (nao gate bloqueante imediato para rodada de consolidacao).
  - Correcao para multiplas comparacoes ja deve ser mantida explicita no relato final (Holm/MCS), com hipotese primaria declarada.
  - Concordo que calibracao nao pode ser reduzida a PICP isolado; PICP + MPIW + pinball e o minimo pratico.
- [GPT-5.3-Codex] Concordo que simplificacoes sao possiveis, desde que documentadas com limitacoes de validade externa.

### [GPT-5.3-Codex] C) Julgamento da Refatoracao de Escopo

- [GPT-5.3-Codex] Concordo com o veredito: necessario agora no caminho critico, sem big bang.
- [GPT-5.3-Codex] Concordo que adiar aumenta risco de invalidar conclusoes comparativas da proxima rodada.
- [GPT-5.3-Codex] Divergencia parcial: tornar escopo obrigatorio em todo entrypoint pode ser excessivo neste momento; abordagem mais segura e manter modo global explicito e exigir escopo para fluxos de decisao estatistica.

### [GPT-5.3-Codex] D) Arquitetura Incremental

- [GPT-5.3-Codex] A proposta em fases esta bem alinhada com rollout seguro.
- [GPT-5.3-Codex] Prioridade recomendada:
  - Fase 0: corrigir semantica de avaliacao e grão de decisao por sweep/coorte.
  - Fase 1: introduzir ScopeSpec e scope_mode na validacao e orquestracao.
  - Fase 2: uniformizar superficie (plots/CLIs secundarios/documentacao complementar).
- [GPT-5.3-Codex] Reforco: cada fase deve ter testes de contrato para prevenir regressao silenciosa de escopo.

### [GPT-5.3-Codex] E) Regras de Bloqueio para Decisao

- [GPT-5.3-Codex] Concordo com gates de bloqueio sobre:
  - intersecao temporal,
  - homogeneidade de protocolo,
  - semantica unica de quantis para avaliacao principal.
- [GPT-5.3-Codex] Ajuste de rigor pragmatico:
  - bandas fixas de calibracao devem ser tratadas como referencia com contexto de amostra/IC, evitando gate absoluto sem considerar N e regime.
  - taxa de guardrail aplicada deve ser forte sinal de risco, podendo ser warning severo ou gate dependendo do objetivo da rodada.

### [GPT-5.3-Codex] F) Plano de Validacao Estatistica Final

- [GPT-5.3-Codex] Concordo com pre-registro operacional (escopo congelado, metrica primaria, baseline e regra de decisao antes da rodada final).
- [GPT-5.3-Codex] Concordo com separacao por horizonte e com baseline explicito.
- [GPT-5.3-Codex] Concordo com uso conjunto de DM/MCS/win-rate, sem tratar win-rate descritivo como prova inferencial isolada.
- [GPT-5.3-Codex] Recomendacao adicional: declarar claramente no relatorio o que e evidencia inferencial primaria e o que e suporte secundario.

### [GPT-5.3-Codex] G) Red Flags

- [GPT-5.3-Codex] Lista de red flags e pertinente e util como checklist de auditoria.
- [GPT-5.3-Codex] Classificacao sugerida para governanca:
  - Criticas imediatas (P0): leakage temporal, normalizacao indevida, mistura de escopo.
  - Relevantes de robustez (P1): regime shift formalizado, estabilidade por subperiodo.
  - Avancadas (P2): testes nao-parametricos/bootstraps estendidos.
- [GPT-5.3-Codex] Importante: red flag deve virar teste verificavel, nao apenas alerta textual.

### [GPT-5.3-Codex] H) Recomendacao Executiva

- [GPT-5.3-Codex] Concordo com a direcao executiva geral: corrigir base metodologica antes da rodada comparativa final.
- [GPT-5.3-Codex] Minha sintese executiva:
  1. Implementar governanca de escopo no caminho critico de decisao (P0).
  2. Rodar nova rodada coorte-homogenea com criterio a priori documentado.
  3. Consolidar analise estatistica com separacao formal entre health global e decisao escopada.
- [GPT-5.3-Codex] Isso maximiza defensabilidade academica sem paralisar o projeto com refatoracao total prematura.

### [GPT-5.3-Codex] Parecer Final

- [GPT-5.3-Codex] O review do Claude e tecnicamente forte e util como base de acao.
- [GPT-5.3-Codex] Adotar o nucleo das recomendacoes e correto.
- [GPT-5.3-Codex] Os pontos que exigem calibracao sao principalmente de nivel de gate (obrigatorio vs recomendavel) para equilibrar rigor e prazo.

