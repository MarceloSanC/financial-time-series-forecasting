# AGENT CORE

## Purpose
Single canonical always-on baseline for AI agents in this repository.
Defines global rules, constraints, and quality expectations.

## Scope
Applies to every task by default.
Task-specific skills may extend this file, but cannot silently override critical safety rules.

## Role in Skill Hierarchy
- Root baseline document (not a task skill).
- Parent for all skills under `docs/ai/skills/*`.

## Priority Order
1. Runtime system/developer constraints.
2. `docs/ai/AGENT_CORE.md`.
3. Task skill (`docs/ai/skills/<name>/SKILL.md`).
4. One-off prompt instructions.

If a conflict exists, follow the highest-priority source and state the conflict explicitly.

## Repository Context
- Project root: `financial-time-series-forecasting`
- Primary docs index: `docs/INDEX.md`
- AI index: `docs/ai/INDEX.md`
- Canonical checklists: `docs/05_checklists/*`
- Architecture: Clean Architecture (`entities`, `interfaces`, `use_cases`, `adapters`, `infrastructure`)
- Data stack: Parquet (silver source-of-truth) + derived gold analytics

## Canonical Commands
- Analytics refresh + quality:
  - `python -m src.main_refresh_analytics_store --fail-on-quality`
- Train:
  - `python -m src.main_train_tft --asset AAPL --features BASELINE_FEATURES,TECHNICAL_FEATURES`
- Infer:
  - `python -m src.main_infer_tft --asset AAPL --model-path <MODEL_VERSION> --start YYYYMMDD --end YYYYMMDD --overwrite`

## Non-Negotiable Data Rules
- Pairwise statistical comparison requires exact intersection by `target_timestamp`.
- Quantile outputs must satisfy `p10 <= p50 <= p90`.
- Gold decision artifacts must be reproducible from persisted data only (no retrain).
- Prevent temporal leakage in all train/val/test/inference operations.

## Global Engineering Rules
- Make minimal, targeted, auditable changes.
- Preserve behavior unless explicit behavior change is requested.
- Never revert unrelated user changes.
- Keep UTC-aware temporal logic.
- Keep documentation synchronized with changed contracts/paths/CLI.


## Expert Response Policy
- For analysis, recommendations, or technical explanations, respond as a senior specialist in the subject.
- Do not default to agreeing with Marcelo; use critical, evidence-oriented reasoning and call out weak assumptions when needed.
- Prefer the most defensible answer over confirmation bias, while keeping tone collaborative and objective.
- Use external research/data/references only when necessary for correctness, temporal accuracy, or high-stakes decisions.

## Skill Traceability Policy
- For each response, declare which skill artifacts are being used.
- `AGENT_CORE` is implicit baseline and does not need to be repeated every time.
- In multi-step tasks, declare skills per step (not one global list for all steps).
- Only consult and declare skills relevant to the current step to avoid context mixing.
- Suggested format:
  - `Step <N> - Skills used: <skill-list>`
  - `Step <N> - Skills used: none specific (AGENT_CORE only)`

## Validation Rules
For relevant changes, run at least one applicable validation:
- touched unit tests,
- schema/contract checks,
- pipeline smoke check.

For analytics-impacting changes, require:
- `python -m src.main_refresh_analytics_store --fail-on-quality`

## Documentation Sync Rules
If behavior/contracts/paths change, update as needed:
- `docs/ai/INDEX.md`
- related skill docs in `docs/ai/skills/*`
- `docs/05_checklists/*`
- `docs/06_runbooks/*`
- `docs/INDEX.md`
- `README.md` (onboarding-impacting changes)

## Commit Rules
- Follow `docs/08_governance/GIT_AND_VERSIONING_GUIDE.md`.
- Default when commits are requested: one commit per file.
- Group multiple files only when explicitly requested by user.
- Message skeleton (required):
  - `<tipo>(<escopo>): <título curto>`
  - `[descricao geral da alteracao/criacao]`
  - `- [itemN] one bullet per concrete responsibility`

## Definition of Done
1. Requested outcome is implemented.
2. Relevant validations are executed (or explicitly reported as not run).
3. Docs are updated where required.
4. Result is reproducible and traceable.
