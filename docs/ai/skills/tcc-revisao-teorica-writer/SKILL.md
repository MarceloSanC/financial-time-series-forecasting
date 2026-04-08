---
name: tcc-revisao-teorica-writer
description: Write or revise Chapter 3 (Fundamentação Teórica) with focus on literature directly aligned with the TCC. Use when the task involves curating core references, building the research gap, and theoretical positioning for financial forecasting with TFT, quantiles, and OOS evaluation.
---

# TCC Revisão Teórica Writer

## Purpose
Write or revise Chapter 3 (Fundamentação Teórica) with literature directly tied to the TCC research gap and method.

## Scope
Covers:
1. Core reference curation
2. Method-aligned theoretical organization
3. Explicit research-gap construction

## Inherited from AGENT_CORE
- Priority and quality discipline
- Validation/reporting expectations
- Documentation consistency rules

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Mandatory parent execution (`tcc-writing-core`) before chapter edits
- Relevance-over-volume literature policy
- Parallel-citation policy (do not postpone references to final rounds)

## Flow
1. Apply `tcc-writing-core` first.
2. Read `docs/07_reports/living-paper/10_problem_and_related_work.md`.
3. Edit `text/3_Revisao_Teorica/3_Revisao_Teorica.tex` by frozen section.
4. Sync key points in the living-paper and mapping.

## Specific Rules
- Prioritize source quality and adherence over quantity.
- Organize the review by function in the work: context, method, uncertainty, evaluation.
- Avoid broad review content that does not support the chosen method.
- End with a clear gap that justifies the following chapters.
- Anchor TCC technical decisions (metrics, protocol, modeling) in literature during writing, not only in the final review.
- Apply clear and direct language, with complexity compatible with undergraduate writing, without losing rigor.

## Target Files
- `text/3_Revisao_Teorica/3_Revisao_Teorica.tex`
- `docs/07_reports/living-paper/10_problem_and_related_work.md`
- `docs/07_reports/living-paper/tcc_mapping.md`

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/tcc-writing-core/SKILL.md`
- `docs/07_reports/living-paper/10_problem_and_related_work.md`
- `docs/ai/skills/tcc-revisao-teorica-writer/references/chapter-3-checklist.md`
