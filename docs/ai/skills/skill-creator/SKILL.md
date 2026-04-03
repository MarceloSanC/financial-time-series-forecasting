# SKILL CREATOR

## Purpose
Create, review, and deprecate skills with consistent structure, low redundancy, and clear governance.

Primary objective:
- Standardize task execution and implementation quality across agents.
- Reduce context-window load by keeping skill artifacts focused, modular, and easy to route.

## Scope
Covers:
1. New skill creation
2. Existing skill refactor/review
3. Skill deprecation and replacement routing
4. Skill structure optimization for minimal-relevant-reading per task

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Overrides/additions in this skill:
- Mandatory template for all skills
- Redundancy threshold and overlap policy
- Skill-specific QA checklist and approval flow

## When to Use
- A new capability requires reusable agent instructions.
- An existing skill is too large, ambiguous, or duplicated.
- A skill must be deprecated or replaced.

## When Not to Use
- One-off small task instructions that do not justify reusable artifacts.
- Product/runbook documentation changes unrelated to agent behavior.

## Inputs Required
- Target skill name and intended scope
- Existing related skills to compare overlap
- Expected outputs and validation command(s)
- Owner approval requirement
- Any missing implementation decisions that need Marcelo's preference

## Marcelo Clarification Rule
- When creating a new skill requested by Marcelo, if required information is missing or any policy/implementation detail is ambiguous, the agent must ask Marcelo before finalizing the skill.
- The question must include 2-4 concrete options adapted to this project.
- The best option, according to the agent's judgment, must appear first and be tagged with `(Recommended)`.
- Each option must include a short impact/tradeoff sentence.
- Do not silently assume policy-defining decisions when Marcelo has not confirmed them.

## Execution Steps
1. Run overlap audit against existing skills.
2. If overlap > 40%, refactor existing skill instead of creating a new one.
3. Draft/update skill using the required template sections.
4. Add explicit inheritance section.
5. Add concrete usage example + validation command.
6. Apply skill QA checklist.
7. Submit for manual maintainer approval.

## Outputs Expected
- `docs/ai/skills/<skill-name>/SKILL.md` in English
- Optional companions under the same folder (`templates/`, `examples/`, `checklists/`)
- Updated `docs/ai/INDEX.md` routing when skill is added/deprecated
- Split instructions so agents can load only the relevant subset for the requested task (avoid long monolithic skills)

## Validation
- Structural check:
  - Must include all required template sections.
- Size check:
  - `SKILL.md` <= 180 lines.
- Governance check:
  - Manual approval required before final adoption.

Example command:
- `wc -l docs/ai/skills/<skill-name>/SKILL.md`

## Common Failures and Fixes
- Failure: duplicated content from other skills.
  - Fix: replace duplication with canonical references.
- Failure: missing inheritance section.
  - Fix: add `Inherited from AGENT_CORE` or explicit parent skill.
- Failure: skill too long (>180 lines).
  - Fix: split into parent + child skills.

## Definition of Done
- Skill is English, scoped, and template-compliant.
- Inheritance is explicit.
- Overlap policy respected (<=40% or refactor path chosen).
- Example + validation command included.
- AI index updated when needed.
- Maintainer approval recorded.

## Required Skill Template (for all created skills)
1. Purpose
2. Scope
3. Inherited from AGENT_CORE (or parent skill)
4. When to Use
5. When Not to Use
6. Inputs Required
7. Execution Steps
8. Outputs Expected
9. Validation
10. Common Failures and Fixes
11. Definition of Done
12. References

## Policy Parameters
- Language: English (mandatory)
- Max size: 180 lines per skill file
- Redundancy threshold: 40% overlap
- Commit policy: one commit per skill file by default
- Approval: manual maintainer approval required

## References
- `docs/ai/AGENT_CORE.md`
- `docs/ai/INDEX.md`
- `docs/08_governance/GIT_AND_VERSIONING_GUIDE.md`
- `docs/CONTRIBUTING.md`
