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
