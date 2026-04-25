---
title: Contributing Guide
scope: Checklist de pull request, convencao de commit (delega para GOVERNANCE_AND_VERSIONING) e regra de obrigatoriedade de update de docs por tipo de mudanca (AI workflow, paths, schemas, metricas, CLI, artefatos).
update_when:
  - checklist de PR mudar
  - regra de obrigatoriedade de docs update for revisada
  - novo tipo de mudanca exigir docs no mesmo PR
canonical_for: [contributing, pr_checklist, docs_update_obligation]
---

# Contributing Guide

## Pull Request Checklist
- Run relevant unit tests.
- Update docs/checklists if behavior or contracts changed.
- Ensure commands in runbooks still work.
- Keep changes scoped and traceable.

## Commit Message Convention
- Follow the existing project guide in:
  - `docs/08_governance/GOVERNANCE_AND_VERSIONING.md`
- Keep commits scoped, coherent, and reviewable.
- Do not include files outside the task scope.

## Documentation Update Rule
Any change in one of these requires docs update in the same PR:
- AI workflow/skill updates (check `docs/ai/INDEX.md` and `docs/ai/AGENT_CORE.md`)
- documentation path reorganization (must update `README.md` and `docs/INDEX.md`)
- data schema/contract
- metric/statistical method
- run command/CLI flags
- artifact path conventions
