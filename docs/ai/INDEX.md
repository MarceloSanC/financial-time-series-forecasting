---
title: AI Playbook Index
scope: Entrypoint canonico da documentacao para agentes de IA. Lista AGENT_CORE (sempre obrigatorio), catalogo de skills disponiveis em docs/ai/skills/* e ordem de carregamento (AGENT_CORE -> skill da tarefa).
update_when:
  - novo skill for adicionado em docs/ai/skills/
  - skill existente for renomeado/removido
  - ordem de carregamento (Usage Order) mudar
  - source-of-truth boundaries forem revisados
canonical_for: [ai_playbook_index, ai_skills_catalog, ai_loading_order]
---

# AI Playbook Index

This section is the canonical entrypoint for agent-focused documentation.

## Core Baseline
- `docs/ai/AGENT_CORE.md` (always-on baseline)

## Skills Catalog
- `docs/ai/skills/explicit-sweep-execution/SKILL.md` -> run explicit-config cohorts with isolated prefixes and scoped analysis refresh
- `docs/ai/skills/project-scope-principles/SKILL.md` -> enforce v0 scope discipline, reproducibility, interpretability, and anti-overengineering
- `docs/ai/skills/model-performance-and-research-advisor/SKILL.md` -> evaluate sweeps/models with statistical rigor, calibration trade-offs, and decision-oriented recommendations
- `docs/ai/skills/documentation-authoring/SKILL.md` -> author and update docs with canonical references and executable structure
- `docs/ai/skills/documentation-maintenance/SKILL.md` -> maintain docs consistency, deprecation routing, and source-of-truth integrity
- `docs/ai/skills/testing-execution/SKILL.md` -> execute validations with explicit gates, rerun policy, and reproducible reporting
- `docs/ai/skills/testing-implementation/SKILL.md` -> implement deterministic tests by layer with strong regression and contract coverage
- `docs/ai/skills/orchestrator-design/SKILL.md` -> design orchestrators with explicit stage flow, idempotency, and failure semantics
- `docs/ai/skills/module-implementation-clean-arch/SKILL.md` -> implement new modules and improvements with clean boundaries and centralized shared definitions
- `docs/ai/skills/skill-creator/SKILL.md`
  - Project extension of Codex system skill-creator; adds local governance, non-redundancy rules, and Marcelo clarification policy.
- `docs/ai/skills/workflow-governance/SKILL.md`
  - Standard execution/validation workflow for implementation tasks.
- `docs/ai/skills/tcc-writing-core/SKILL.md` -> global writing baseline for the TCC document set
- `docs/ai/skills/tcc-introducao-writer/SKILL.md` -> specialized guidance for introduction chapter writing
- `docs/ai/skills/tcc-revisao-teorica-writer/SKILL.md` -> specialized guidance for literature review chapter writing
- `docs/ai/skills/tcc-metodo-writer/SKILL.md` -> specialized guidance for methodology chapter writing
- `docs/ai/skills/tcc-resultados-writer/SKILL.md` -> specialized guidance for results and discussion chapter writing
- `docs/ai/skills/tcc-conclusoes-writer/SKILL.md` -> specialized guidance for conclusions and future work chapter writing

## Usage Order
1. Load `docs/ai/AGENT_CORE.md`.
2. Load required task skill(s) from `docs/ai/skills/*`.
3. Execute task and validate per AGENT_CORE + selected skill.

## Source-of-Truth Boundaries
- AI guidance: `docs/ai/*`
- Product/process canonical docs:
  - `docs/05_checklists/*`
  - `docs/06_runbooks/*`
  - `docs/08_governance/*`
  - `docs/INDEX.md`
