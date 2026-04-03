# MODULE IMPLEMENTATION (CLEAN ARCH)

## Purpose
Implement new modules and code improvements following Clean Architecture with clear domain/adapters separation, reusable contracts, and centralized shared definitions.

## Scope
Covers:
1. New module implementation
2. Incremental improvements and refactors
3. Shared configuration and threshold centralization
4. Contract-safe integration across use cases, adapters, and infrastructure

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Overrides/additions in this skill:
- Strict domain-first modeling before adapter wiring
- Shared threshold/constants policy to avoid duplicated rules
- Clean dependency direction enforcement

## When to Use
- A feature requires adding domain behavior plus I/O integration.
- Existing logic is duplicated across adapters/use cases and needs consolidation.
- Business thresholds/definitions are scattered and should be centralized.

## When Not to Use
- Tiny one-line fixes with no architecture impact.
- Pure documentation updates without code changes.
- UI-only adjustments that do not touch domain/application layers.

## Inputs Required
- Feature/change objective and expected behavior
- Affected boundaries (domain/use_case/adapters/infrastructure)
- Existing sources of truth for constants/thresholds
- Backward compatibility expectations
- Required validations/tests

## Execution Steps
1. Define domain behavior first.
2. Define application contract.
3. Implement adapters second.
4. Centralize shared definitions and thresholds.
5. Wire infrastructure and entrypoints.
6. Add/update tests by layer.
7. Run targeted validation and document changed contracts.

## Outputs Expected
- Domain-first implementation aligned to Clean Architecture
- No business rules duplicated across adapters
- Canonical shared definitions for thresholds/constants
- Updated docs/checklists when behavior/contracts change

## Validation
- Architecture check: domain must not depend on adapter/infrastructure modules.
- Contract check: use-case interfaces are explicit and stable.
- Reuse check: shared thresholds/constants come from one canonical source.
- Test check: changed behavior covered by unit tests (and integration tests when relevant).

Example commands:
- `rg -n "threshold|hardcode|magic number" src`
- `.venv/bin/pytest -q tests/unit`

## Common Failures and Fixes
- Failure: business logic implemented in adapter.
  - Fix: move logic to domain/use_case and keep adapter as translation layer.
- Failure: duplicated thresholds in multiple files.
  - Fix: create/extend canonical definitions module and replace local literals.
- Failure: domain imports infrastructure/adapters.
  - Fix: invert dependency via interface/port.
- Failure: refactor breaks compatibility silently.
  - Fix: add contract tests and migration-safe defaults.

## Definition of Done
- Domain and adapters are clearly separated.
- Shared definitions/thresholds are centralized and reused.
- Contracts are explicit and validated by tests.
- Documentation/checklists updated for changed behavior.
- Implementation is traceable, reusable, and consistent with Clean Architecture.

## References
- `docs/ai/skills/documentation-authoring/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/INDEX.md`
- `docs/05_checklists/*`
- `docs/08_governance/GIT_AND_VERSIONING_GUIDE.md`
