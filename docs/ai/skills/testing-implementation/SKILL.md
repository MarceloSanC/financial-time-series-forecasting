# TESTING IMPLEMENTATION

## Purpose
Implement tests with clear scope, deterministic behavior, and architecture-aligned coverage so code changes are validated without fragile or noisy suites.

## Scope
Covers:
1. Unit test implementation
2. Contract/schema test implementation
3. Adapter/integration test implementation (when needed)
4. Regression test implementation for bug fixes

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Test design by layer (domain/use_case/adapter/infrastructure)
- Determinism and anti-flakiness policy
- Explicit assertion strategy and failure readability

## When to Use
- A change introduces behavior that needs verification.
- A bug fix needs regression coverage.
- A contract/schema evolved and compatibility must be enforced.
- A pipeline/use case needs robust guardrails against silent regressions.

## When Not to Use
- Pure documentation-only tasks.
- One-off local debugging checks not intended for repository tests.
- Performance benchmarking as primary goal (use dedicated benchmark workflow).

## Inputs Required
- Target behavior and acceptance criteria
- Changed files/layers and expected side effects
- Existing testing patterns in the module
- Required test level (unit, contract, integration)
- Determinism constraints (time, randomness, ordering)

## Execution Steps
1. Map test scope by layer:
   - domain logic -> unit tests
   - use-case contract -> unit/contract tests
   - adapter I/O mapping -> integration-like adapter tests
2. Define test cases:
   - happy path, edge cases, validation failures, and error propagation.
3. Build deterministic fixtures:
   - freeze time, seed randomness, stable ordering, fixed IDs/timestamps.
4. Implement focused assertions:
   - assert behavior and contracts, not irrelevant internals.
5. Add regression tests for known failures:
   - encode bug scenario + expected corrected behavior.
6. Keep tests maintainable:
   - shared factories/helpers only when reuse is real.
7. Run relevant test subset and report what was executed.

## Outputs Expected
- New/updated tests aligned with changed behavior
- Deterministic, readable assertions
- Coverage of critical paths and failure modes
- Minimal, non-duplicated test helpers

## Validation
- Coverage relevance check:
  - each new test maps to a changed behavior or contract.
- Determinism check:
  - tests do not depend on wall-clock time, random state, or external mutable state.
- Signal quality check:
  - failing tests clearly indicate what broke.
- Scope check:
  - avoid over-mocking when real contract behavior should be tested.

Example commands:
- `.venv/bin/pytest -q tests/unit`
- `.venv/bin/pytest -q tests/unit/<module_path>`

## Common Failures and Fixes
- Failure: flaky test due to time/randomness.
  - Fix: freeze time, set seeds, and remove non-deterministic ordering assumptions.
- Failure: assertions too broad or brittle.
  - Fix: assert domain outcomes/contract fields only.
- Failure: duplicated fixture setup across files.
  - Fix: extract minimal shared fixture/factory.
- Failure: integration test leaking external dependencies.
  - Fix: isolate repository boundaries and use controlled local test doubles.

## Definition of Done
- Tests cover changed behavior and key failure modes.
- Test suite additions are deterministic and maintainable.
- Assertions are explicit, readable, and contract-oriented.
- Regression scenario is covered when applicable.
- Executed test subset and result are reported.

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/skills/documentation-authoring/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/module-implementation-clean-arch/SKILL.md`
- `docs/ai/skills/orchestrator-design/SKILL.md`
- `docs/08_governance/GOVERNANCE_AND_VERSIONING.md`
