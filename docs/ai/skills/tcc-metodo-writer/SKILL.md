---
name: tcc-metodo-writer
description: Write or revise Chapter 4 (Método) with emphasis on reproducibility and experimental validity. Use when the task involves data description, features, TFT configuration, evaluation protocol, metrics, and experiment governance.
---

# TCC Método Writer

## Purpose
Write or revise Chapter 4 (Método) with reproducibility and experimental validity as primary constraints.

## Scope
Covers:
1. Data and feature description
2. Model configuration and experimental protocol
3. Metrics, quality controls, and experiment governance

## Inherited from AGENT_CORE
- Priority and quality discipline
- Validation/reporting expectations
- Documentation consistency rules

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Mandatory parent execution (`tcc-writing-core`) before chapter edits
- Method chapter must avoid results leakage
- Academic-language policy for data-engineering design choices

## Flow
1. Apply `tcc-writing-core` first.
2. Read `docs/07_reports/living-paper/20_method.md` and relevant technical documentation in `docs/`.
3. Edit `text/4_Metodo/4_Metodo.tex` section by section.
4. Sync the method summary in the living-paper.

## Specific Rules
- Describe the method with enough detail for reproducibility.
- Clearly separate experimental design, model configuration, and evaluation.
- Make anti-leakage controls and data-quality criteria explicit.
- Avoid results in the method chapter (design and protocol only).
- Translate market/stack terms into academic data-engineering language (for example, immutable and auditable persistence), explaining why choices support robustness and reproducibility.
- Apply clear and direct language, with complexity compatible with undergraduate writing, without losing rigor.

## Target Files
- `text/4_Metodo/4_Metodo.tex`
- `docs/07_reports/living-paper/20_method.md`
- `docs/07_reports/living-paper/tcc_mapping.md`

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/tcc-writing-core/SKILL.md`
- `docs/07_reports/living-paper/20_method.md`
- `docs/ai/skills/tcc-metodo-writer/references/chapter-4-checklist.md`
