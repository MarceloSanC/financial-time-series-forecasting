---
name: tcc-resultados-writer
description: Write or revise Chapter 5 (Resultados e Discussão) based on traceable evidence. Use when the task involves reporting OOS metrics, uncertainty analysis, configuration comparison, and interpretation without undue extrapolation.
---

# TCC Resultados Writer

## Purpose
Write or revise Chapter 5 (Resultados e Discussão) using traceable evidence and statistically defensible interpretation.

## Scope
Covers:
1. OOS metrics and comparison reporting
2. Uncertainty and robustness discussion
3. Interpretation without undue causal extrapolation

## Inherited from AGENT_CORE
- Priority and quality discipline
- Validation/reporting expectations
- Documentation consistency rules

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Mandatory parent execution (`tcc-writing-core`) before chapter edits
- Evidence-log-first reporting policy for claims
- Round-priority policy for chapter expansion requested by advisor

## Flow
1. Apply `tcc-writing-core` first.
2. Read `docs/07_reports/living-paper/30_results_and_analysis.md` and `docs/07_reports/living-paper/evidence_log.md`.
3. Edit `text/5_Resultados/5_Resultados.tex` section by section.
4. Sync findings in the living-paper.

## Specific Rules
- Report metrics with experimental context (split, horizon, configuration).
- Separate observed results from interpretation.
- Discuss quantile uncertainty and statistical robustness when applicable.
- Do not claim causality where only predictive association exists.
- In advisor-deadline rounds, prioritize expansion of requested chapters before cosmetic refinements.
- Apply clear and direct language, with complexity compatible with undergraduate writing, without losing rigor.

## Target Files
- `text/5_Resultados/5_Resultados.tex`
- `docs/07_reports/living-paper/30_results_and_analysis.md`
- `docs/07_reports/living-paper/evidence_log.md`
- `docs/07_reports/living-paper/tcc_mapping.md`

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/tcc-writing-core/SKILL.md`
- `docs/07_reports/living-paper/30_results_and_analysis.md`
- `docs/07_reports/living-paper/evidence_log.md`
- `docs/ai/skills/tcc-resultados-writer/references/chapter-5-checklist.md`
