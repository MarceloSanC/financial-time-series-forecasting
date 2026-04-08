---
name: tcc-writing-core
description: Apply the global academic writing standards for the financial forecasting TCC project. Use when the request involves writing, revision, organization, synchronization, or validation of TCC/article chapters and artifacts, ensuring alignment with thesis, scope, cross-file coherence, and traceability.
---

# TCC Writing Core

## Purpose
Apply global academic writing guardrails for the TCC/article and coordinate chapter-specific writer skills with consistent evidence and scope.

## Scope
Covers:
1. Global writing governance for TCC chapters
2. Living-paper to `text/` synchronization discipline
3. Chapter skill orchestration and final validation

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Validation discipline and delivery hygiene
- Documentation and traceability expectations

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- TCC central thesis and scope guardrails
- Mandatory living-paper first workflow
- Chapter orchestration contract for specialized writer skills
- Advisor-feedback integration policy (round-based)

## Overview
Apply global guardrails for any TCC/article writing task.
Use this skill as the parent layer before running chapter-specific child skills.

## Mandatory Flow
1. Read `docs/07_reports/living-paper/WRITING_PROTOCOL.md`.
2. Read `docs/07_reports/living-paper/00_outline.md`.
3. Read `docs/07_reports/living-paper/chapter_structure_freeze.md`.
4. Define the target file and target section.
5. Write in the living-paper first when applicable, then propagate to `text/`.
6. Run the validation checklist before closing the task.

## Global Rules (Non-Negotiable)
- Keep the central scope: TFT + OOS evaluation + quantile uncertainty + reproducibility.
- Do not reintroduce CNN-sentiment as a central axis.
- Use a small set of highly adherent core references per chapter.
- Ensure coherence across problem, objectives, method, results, and conclusions.
- Link relevant claims to traceable evidence/artifacts.
- Ensure immediate alignment between title, resumo, abstract, and the real technical scope (probabilistic/quantile TFT).
- Avoid software-manual language; prioritize academic data-engineering language and scientific justification for design choices.
- Build theoretical grounding/citations in parallel with chapter writing, without postponing to the final stage.

## Language Policy (Undergraduate Level)
- Prioritize clear, direct, easy-to-read language, close to the student's writing level.
- Avoid long sentences and overly ornate vocabulary when a simpler equivalent exists.
- Keep technical rigor without jargon for its own sake: explain technical terms on first use.
- Prefer subject-verb-object sentence structure and short logical paragraph progression.
- When revising existing text, simplify complex wording without changing scientific meaning.

## Advisor Round Policy (Round-Based Delivery)
- For each round, prioritize a single compiled and end-to-end readable PDF (`text/Main.pdf`).
- If some content is not yet mature for the main body, place it temporarily in appendix/annex with future-incorporation indication.
- Name the delivery artifact with a round identifier (for example, `rodada-2.pdf`) per advisor guidance.
- Prioritize expansion of chapters requested in the current round before peripheral polishing.

## Child Skill Orchestration
Choose the child skill according to the target chapter:
- Chapter 2: `tcc-introducao-writer`
- Chapter 3: `tcc-revisao-teorica-writer`
- Chapter 4: `tcc-metodo-writer`
- Chapter 5: `tcc-resultados-writer`
- Chapter 6: `tcc-conclusoes-writer`

Executar esta skill antes da skill filha e reaplicar os checklists ao final.

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/INDEX.md`
- `docs/ai/skills/tcc-introducao-writer/SKILL.md`
- `docs/ai/skills/tcc-revisao-teorica-writer/SKILL.md`
- `docs/ai/skills/tcc-metodo-writer/SKILL.md`
- `docs/ai/skills/tcc-resultados-writer/SKILL.md`
- `docs/ai/skills/tcc-conclusoes-writer/SKILL.md`
- `docs/07_reports/living-paper/WRITING_PROTOCOL.md`
- `docs/07_reports/living-paper/WRITING_PROTOCOL.md`
- `docs/07_reports/living-paper/00_outline.md`
- `docs/07_reports/living-paper/chapter_structure_freeze.md`
- `docs/ai/skills/tcc-writing-core/references/global-checklist.md`
- `docs/ai/skills/tcc-writing-core/references/artifact-map.md`
