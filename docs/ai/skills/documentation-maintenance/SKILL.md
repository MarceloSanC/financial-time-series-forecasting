# DOCUMENTATION MAINTENANCE

## Purpose
Maintain long-term documentation quality by enforcing consistency, deprecation hygiene, and source-of-truth integrity across the docs system.

## Scope
Covers:
1. Periodic documentation audits
2. Deprecation and migration of outdated docs
3. Broken link/reference cleanup
4. Documentation inventory and ownership clarity

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Overrides/additions in this skill:
- Maintenance lifecycle for docs assets
- Deprecation workflow and redirect policy
- Drift detection between code and docs

## When to Use
- Scheduled documentation cleanup/review cycles.
- Large refactors that leave old docs obsolete.
- Index/navigation drift or broken references.
- Need to consolidate duplicated docs content.

## When Not to Use
- Single targeted doc authoring tasks (use documentation-authoring).
- One-off typo fixes only.

## Inputs Required
- Maintenance objective (audit/deprecate/consolidate)
- Target docs scope (folders/files)
- Current canonical docs map
- Deprecation/migration constraints
- Validation/reporting requirements

## Execution Steps
1. Build docs inventory and classify each artifact:
   - active canonical, duplicate, obsolete, or uncertain.
2. Detect drift and inconsistencies:
   - stale commands, old paths, conflicting guidance.
3. Execute maintenance actions:
   - update, merge, deprecate, relocate, or remove references.
4. Preserve migration safety:
   - add deprecation notes and pointers to replacement docs.
5. Update all affected indexes and navigation paths.
6. Produce maintenance summary:
   - what changed, what was deprecated, what remains pending.

## Outputs Expected
- Cleaner docs tree with explicit canonical sources
- Deprecated docs routed to current replacements
- Updated indexes and consistent references
- Maintenance report with remaining actions (if any)

## Validation
- Link/reference integrity check:
  - no broken critical references after maintenance.
- Canonicality check:
  - each critical topic has one clear source-of-truth.
- Deprecation check:
  - deprecated docs point to valid replacement docs.

Example commands:
- `rg -n "deprecated|obsolete|legacy" docs`
- `rg -n "\.md\)" docs/INDEX.md docs/ai/INDEX.md`

## Common Failures and Fixes
- Failure: deprecated file removed without redirect.
  - Fix: keep stub/pointer file until migration is complete.
- Failure: duplicated canonical docs survive cleanup.
  - Fix: select one source and downgrade others to references.
- Failure: index not updated after moving docs.
  - Fix: patch all impacted index files immediately.
- Failure: maintenance done without summary.
  - Fix: add concise maintenance report section.

## Definition of Done
- Documentation set is internally consistent and navigable.
- Deprecated artifacts have explicit migration pointers.
- Canonical source ownership is clear for key topics.
- Maintenance actions are reported and traceable.

## References
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/documentation-authoring/SKILL.md`
- `docs/INDEX.md`
- `docs/08_governance/GIT_AND_VERSIONING_GUIDE.md`
