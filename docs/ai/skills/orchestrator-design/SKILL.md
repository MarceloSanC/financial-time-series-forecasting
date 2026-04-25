# ORCHESTRATOR DESIGN

## Purpose
Design and implement orchestrators that coordinate use cases and adapters without embedding domain business rules.

## Scope
Covers:
1. Creation of new orchestrators
2. Refactor of existing orchestration flows
3. Integration sequencing across use cases/adapters
4. Reliability patterns (idempotency, retries, failure handling)

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Orchestrator as coordination layer only
- Explicit boundary rules for orchestration vs domain logic
- Mandatory execution traceability and failure semantics

## When to Use
- A task spans multiple use cases, repositories, or adapters.
- A workflow needs sequencing, branching, retries, or compensation.
- Entrypoints (`main_*`, CLI runners, schedulers) need clean composition.

## When Not to Use
- Single isolated domain rule changes.
- Pure adapter implementation with no cross-flow coordination.
- UI-only changes without backend flow orchestration.

## Inputs Required
- Workflow objective and success criteria
- Steps involved and dependency order
- Required side effects and persistence points
- Failure handling policy (retry, skip, fail-fast, partial-fail)
- Idempotency and replay expectations
- Required logs/metrics/traces

## Execution Steps
1. Define orchestration contract:
   - inputs, outputs, execution stages, and final status model.
2. Map boundaries:
   - keep domain rules in use cases/entities; orchestrator only coordinates calls.
3. Implement execution flow:
   - stage sequencing, branching conditions, retries/timeouts, and compensation where needed.
4. Enforce idempotency:
   - stable keys, duplicate-safe writes, and deterministic replay behavior.
5. Add observability:
   - stage-level logs, elapsed times, counts, and explicit failure reasons.
6. Preserve deterministic status model:
   - `ok`, `partial_failed`, `failed` (or project equivalent) with clear criteria.
7. Validate with orchestrator-focused tests and update docs/contracts.

## Outputs Expected
- Orchestrator implementation with explicit stages
- Clear separation: orchestration logic vs business/domain logic
- Traceable execution logs and stable failure semantics
- Updated docs/checklists when flow behavior changes

## Validation
- Boundary check:
  - orchestrator does not implement domain business rules.
- Flow check:
  - execution ordering and branch conditions are explicit and test-covered.
- Idempotency check:
  - replay/re-run does not duplicate side effects.
- Failure semantics check:
  - failure statuses are deterministic and auditable.

Example commands:
- `rg -n "orchestr|execute\(|partial_failed|retry|idempot" src`
- `.venv/bin/pytest -q tests/unit`

## Common Failures and Fixes
- Failure: orchestrator contains business calculations.
  - Fix: move business logic into domain/use case and keep orchestrator as coordinator.
- Failure: side effects happen before validation gates.
  - Fix: reorder stages and add guard checks before writes.
- Failure: retries produce duplicates.
  - Fix: add idempotency keys and upsert/append policy safeguards.
- Failure: ambiguous final status.
  - Fix: define stage-level outcome mapping to final status contract.

## Definition of Done
- Orchestrator coordinates without domain leakage.
- Stage flow is explicit, testable, and observable.
- Failure and retry behavior is deterministic.
- Idempotency/replay behavior is validated.
- Documentation reflects the orchestration contract.

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/skills/documentation-authoring/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/module-implementation-clean-arch/SKILL.md`
- `docs/05_checklists/*`
- `docs/08_governance/GIT_AND_VERSIONING_GUIDE.md`
