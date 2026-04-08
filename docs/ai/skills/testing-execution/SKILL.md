# TESTING EXECUTION

## Purpose
Execute tests consistently with clear approval criteria, reproducible commands, and concise reporting that prevents silent validation gaps.

## Scope
Covers:
1. Test execution planning by change scope
2. Command selection and run order
3. Failure triage and rerun strategy
4. Validation reporting for user-facing updates

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Explicit execution matrix by impact area
- Standard pass/fail gate and rerun policy
- Standardized test report format

## When to Use
- Any code change that requires validation before handoff.
- Bugfix verification and regression confirmation.
- Contract/schema changes requiring targeted and broader checks.

## When Not to Use
- Documentation-only changes with no behavior impact.
- Early exploratory spikes when user explicitly asked to skip validation.

## Inputs Required
- Changed files/modules and expected behavior impact
- Required quality gates (unit/contract/integration/analytics)
- Available test commands and environment constraints
- User constraints (time budget, strictness level)

## Execution Steps
1. Determine validation scope:
   - minimal targeted tests for changed modules
   - required broader gates when contracts/pipelines are affected.
2. Build execution plan:
   - fast deterministic checks first, expensive suites later.
3. Run tests with reproducible commands.
4. If failures occur, classify:
   - product regression vs flaky/environment issue.
5. Apply rerun policy:
   - rerun flaky suspects once after isolation;
   - do not hide persistent failures.
6. Report outcome in standard format:
   - commands run, pass/fail summary, failed tests, next action.

## Outputs Expected
- Executed test commands list
- Clear pass/fail status by test group
- Actionable failure summary with probable root cause
- Explicit note of what was not run (if any)

## Validation
- Coverage adequacy check:
  - executed tests match change impact.
- Reproducibility check:
  - commands can be rerun as provided.
- Transparency check:
  - failures and skipped validations are explicit.

Example command set:
- `.venv/bin/pytest -q tests/unit/<module_path>`
- `.venv/bin/pytest -q tests/unit`
- `python -m src.main_refresh_analytics_store --fail-on-quality` (analytics-impacting changes)

## Common Failures and Fixes
- Failure: only broad suite executed, missing targeted signal.
  - Fix: run module-focused tests first for faster diagnosis.
- Failure: hidden skipped validations.
  - Fix: explicitly list skipped commands and reason.
- Failure: flaky retry loop masks real issue.
  - Fix: max one controlled rerun and then escalate as failure.
- Failure: ambiguous report.
  - Fix: use structured summary with command -> result mapping.

## Definition of Done
- Validation scope matches change impact.
- Commands and outcomes are reproducible and explicit.
- Failures are triaged and not hidden.
- User receives clear summary with next steps when needed.

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/testing-implementation/SKILL.md`
- `docs/08_governance/GIT_AND_VERSIONING_GUIDE.md`
