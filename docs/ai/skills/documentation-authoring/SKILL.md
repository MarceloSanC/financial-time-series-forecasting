# DOCUMENTATION AUTHORING

## Purpose
Create and update technical documentation with clear structure, traceable contracts, and concise language that supports engineering execution.

## Scope
Covers:
1. Authoring new documentation artifacts
2. Updating existing docs after behavior/contract/path changes
3. Producing runbooks, checklists, and technical reports
4. Keeping links and references aligned with source-of-truth docs

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Documentation templates by artifact type
- Source-of-truth and cross-reference discipline
- Conciseness and anti-duplication guidance

## When to Use
- New feature/process requires documentation.
- Code changes affect CLI, contracts, schemas, paths, or behavior.
- A checklist/runbook/report needs to be created or updated.

## When Not to Use
- No documentation impact from the change.
- Temporary notes not intended as repository artifacts.

## Inputs Required
- Documentation artifact type (README/checklist/runbook/report)
- Scope of changed behavior/contracts/paths
- Canonical source(s) to reference
- Audience and usage context
- Required validation commands (if any)

## Execution Steps
1. Identify target artifact and owner section in docs tree.
2. Apply artifact structure appropriate to type:
   - objective, prerequisites, inputs, steps, outputs, validation, troubleshooting.
3. Link to canonical sources instead of duplicating volatile details.
4. Update related indexes and navigation files when adding/moving docs.
5. Ensure wording is precise, executable, and free of ambiguous guidance.
6. Add/adjust validation and verification instructions when relevant.
7. Confirm consistency with AGENT_CORE and governance guides.

## Outputs Expected
- Clear, actionable documentation artifact
- Updated cross-references and indexes
- Contract/path/CLI changes reflected in docs
- Minimal duplication with strong source linking

## Validation
- Structure check:
  - required sections exist and match doc type.
- Consistency check:
  - no contradiction with current code contracts and canonical docs.
- Navigation check:
  - index/reference links updated and valid.

Example commands:
- `rg -n "TODO|TBD|FIXME" docs`
- `rg -n "<old_path>|<old_command>" docs`

## Common Failures and Fixes
- Failure: duplicated rules across multiple docs.
  - Fix: keep one canonical source and replace duplicates with references.
- Failure: stale commands/paths.
  - Fix: refresh commands/paths and add explicit validation steps.
- Failure: missing update in indexes.
  - Fix: update `docs/INDEX.md` and related sub-indexes.
- Failure: narrative text without executable steps.
  - Fix: convert to actionable checklist/runbook format.

## Definition of Done
- Documentation matches current behavior/contracts.
- Artifact is actionable and audience-appropriate.
- References and indexes are updated.
- No critical ambiguity or stale instructions remain.

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/INDEX.md`
- `docs/08_governance/GOVERNANCE_AND_VERSIONING.md`
