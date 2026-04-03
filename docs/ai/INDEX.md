# AI Playbook Index

This section is the canonical entrypoint for agent-focused documentation.

## Core Baseline
- `docs/ai/AGENT_CORE.md` (always-on baseline)

## Skills Catalog
- `docs/ai/skills/explicit-sweep-execution/SKILL.md` -> run explicit-config cohorts with isolated prefixes and scoped analysis refresh
- `docs/ai/skills/project-scope-principles/SKILL.md` -> enforce v0 scope discipline, reproducibility, interpretability, and anti-overengineering
- `docs/ai/skills/documentation-authoring/SKILL.md` -> author and update docs with canonical references and executable structure
- `docs/ai/skills/documentation-maintenance/SKILL.md` -> maintain docs consistency, deprecation routing, and source-of-truth integrity
- `docs/ai/skills/testing-execution/SKILL.md` -> execute validations with explicit gates, rerun policy, and reproducible reporting
- `docs/ai/skills/testing-implementation/SKILL.md` -> implement deterministic tests by layer with strong regression and contract coverage
- `docs/ai/skills/orchestrator-design/SKILL.md` -> design orchestrators with explicit stage flow, idempotency, and failure semantics
- `docs/ai/skills/module-implementation-clean-arch/SKILL.md` -> implement new modules and improvements with clean boundaries and centralized shared definitions
- `docs/ai/skills/skill-creator/SKILL.md`
  - Create/review/deprecate skills with governance and non-redundancy rules.
- `docs/ai/skills/workflow-governance/SKILL.md`
  - Standard execution/validation workflow for implementation tasks.

## Companion Docs
- `docs/ai/WORKFLOW.md` (light pointer to workflow skill)

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
