---
name: tcc-introducao-writer
description: Write or revise Chapter 2 (Introdução) of the TCC based on the outline and global protocol. Use when the task involves context, problem statement, justification, objectives, delimitation, and work structure while keeping core references aligned with scope.
---

# TCC Introdução Writer

## Purpose
Write or revise Chapter 2 (Introdução) with strong alignment between research problem, objectives, and project scope.

## Scope
Covers:
1. Context and research problem
2. Justification and objectives
3. Delimitation and work structure

## Inherited from AGENT_CORE
- Priority and quality discipline
- Validation/reporting expectations
- Documentation consistency rules

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Mandatory parent execution (`tcc-writing-core`) before chapter edits
- High-adhesion reference policy for Introduction
- Mandatory alignment between pre-textual elements and implemented method

## Flow
1. Apply `tcc-writing-core` first.
2. Read `docs/07_reports/living-paper/00_outline.md` and `docs/07_reports/living-paper/WRITING_PROTOCOL.md`.
3. Edit `text/2_Introducao/2_Introducao.tex` in the target sections.
4. Sync summary updates to `docs/07_reports/living-paper/00_outline.md` and status updates to `docs/07_reports/living-paper/tcc_mapping.md`.

## Specific Rules
- Cover: context, problem, justification, objectives, delimitation, and work structure.
- Keep strong alignment between the research question and the general objective.
- Use core references (few and central), without inflating the Introduction review.
- Avoid deep methodological detail that belongs in Chapter 4.
- Ensure that Title, Resumo, and Abstract reflect the current focus (TFT + probabilistic/quantile forecasting).
- Apply clear and direct language, with complexity compatible with undergraduate writing, without losing rigor.

## Target Files
- `text/2_Introducao/2_Introducao.tex`
- `docs/07_reports/living-paper/00_outline.md`
- `docs/07_reports/living-paper/tcc_mapping.md`

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/tcc-writing-core/SKILL.md`
- `docs/07_reports/living-paper/WRITING_PROTOCOL.md`
- `docs/07_reports/living-paper/00_outline.md`
- `docs/ai/skills/tcc-introducao-writer/references/chapter-2-checklist.md`
