# WORKFLOW GOVERNANCE

## Purpose
Define the standard operating workflow for agent-driven implementation tasks.

## Scope
Applies to execution discipline, validation discipline, and delivery hygiene.
Does not redefine global safety/priority rules from AGENT_CORE.

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data and temporal safety rules
- Default commit policy and message skeleton
- Documentation sync requirements

Adds:
- Ordered execution flow for day-to-day tasks
- Escalation points for high-risk changes

## When to Use
- Any implementation task requiring a repeatable execution process.
- Multi-step tasks where validation and handoff quality matter.

## When Not to Use
- Purely informational responses with no code or doc changes.

## Inputs Required
- Task objective and acceptance criteria
- Affected modules/files
- Expected validations (tests/commands)

## Execution Steps
1. Clarify objective and acceptance criteria.
2. Inspect impacted modules/contracts.
3. Implement minimal targeted changes.
4. Run relevant validations.
5. Update docs/checklists when behavior/contracts/paths changed.
6. Prepare concise handoff with validation results.

## Outputs Expected
- Implemented change set
- Validation evidence (what ran and result)
- Updated docs when required

## Validation
- For analytics-impacting changes:
  - `python -m src.main_refresh_analytics_store --fail-on-quality`
- For module-specific changes:
  - run related unit tests

## Common Failures and Fixes
- Failure: change merged without relevant validation.
  - Fix: run targeted validations and report outcomes.
- Failure: docs drift after contract/path changes.
  - Fix: update README + docs index + relevant runbook/checklist.

## Definition of Done
- Requested objective met.
- Relevant validations executed or explicitly reported as not run.
- Documentation synchronized for impacted contracts/paths/commands.
- Handoff includes residual risks/follow-up.

## References
- `docs/ai/AGENT_CORE.md`
- `docs/ai/INDEX.md`
- `docs/08_governance/GIT_AND_VERSIONING_GUIDE.md`
