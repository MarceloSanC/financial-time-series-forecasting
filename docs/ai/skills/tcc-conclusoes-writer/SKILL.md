---
name: tcc-conclusoes-writer
description: Write or revise Chapter 6 (Conclusões) consistently with the results. Use when the task involves synthesis of findings, contributions, limitations, and future work without extrapolating beyond study evidence.
---

# TCC Conclusões Writer

## Purpose
Write or revise Chapter 6 (Conclusões) with direct linkage to observed results, explicit limitations, and realistic future work.

## Scope
Covers:
1. Synthesis of main findings
2. Study contributions and limitations
3. Feasible and consistent future work

## Inherited from AGENT_CORE
- Priority and quality discipline
- Validation/reporting expectations
- Documentation consistency rules

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Mandatory parent execution (`tcc-writing-core`) before chapter edits
- No-claim-beyond-evidence policy for final conclusions

## Flow
1. Apply `tcc-writing-core` first.
2. Read `docs/07_reports/living-paper/40_limitations_and_conclusion.md` and the results synthesis.
3. Edit `text/6_Conclusoes/6_Conclusoes.tex` section by section.
4. Sync conclusions in the living-paper.

## Specific Rules
- Answer the research question directly.
- Distinguish effective contribution from future expectations.
- State limitations with technical clarity.
- Propose feasible future work connected to limitations.
- Apply clear and direct language, with complexity compatible with undergraduate writing, without losing rigor.

## Target Files
- `text/6_Conclusoes/6_Conclusoes.tex`
- `docs/07_reports/living-paper/40_limitations_and_conclusion.md`
- `docs/07_reports/living-paper/tcc_mapping.md`

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/tcc-writing-core/SKILL.md`
- `docs/07_reports/living-paper/40_limitations_and_conclusion.md`
- `docs/ai/skills/tcc-conclusoes-writer/references/chapter-6-checklist.md`
