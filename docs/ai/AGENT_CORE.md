---
title: Agent Core
scope: Baseline always-on para agentes de IA. Define regras universais que se aplicam a todo prompt, sem detalhes operacionais especificos (que moram em docs canonicos referenciados).
update_when:
  - mudar regra que se aplica a TODO prompt (nao mudar para regras de escopo restrito)
  - mudar politica de roteamento documental
  - mudar Non-Negotiable Data Rules ou Scope Governance
canonical_for: [agent_baseline, documentation_sync_rule]
---

# AGENT CORE

## Purpose
Single canonical always-on baseline for AI agents in this repository.
Defines global rules and constraints that apply to every prompt.

Operational specifics live in their canonical docs; this file references them.
Do not duplicate operational content here.

## Scope
Applies to every task by default.
Task-specific skills may extend this file, but cannot silently override
critical safety rules.

## Priority Order
1. Runtime system/developer constraints.
2. `docs/ai/AGENT_CORE.md` (this file).
3. Task skill (`docs/ai/skills/<name>/SKILL.md`).
4. One-off prompt instructions.

If a conflict exists, follow the highest-priority source and state the
conflict explicitly.

## Repository Pointers
- Documentation routing manifest: `docs/INDEX.md`
- Strategic direction (objective, hypotheses, roadmap): `docs/00_overview/STRATEGIC_DIRECTION.md`
- Architecture: Clean Architecture (`entities`, `interfaces`, `use_cases`, `adapters`, `infrastructure`)
- Operational commands: `docs/06_runbooks/*` (start at `RUN_PIPELINE_QUICKSTART.md`)
- Commit/PR/versioning rules: `docs/08_governance/GOVERNANCE_AND_VERSIONING.md`

## Non-Negotiable Data Rules
- Pairwise statistical comparison requires exact intersection by `target_timestamp`.
- Statistical/model-selection conclusions require explicit cohort scope (for
  example `parent_sweep_id` prefix or frozen-candidates set); global unscoped
  checks are health-only and must not be used for winner selection.
- Quantile outputs must satisfy `p10 <= p50 <= p90`.
- Gold decision artifacts must be reproducible from persisted data only (no retrain).
- Prevent temporal leakage in all train/val/test/inference operations.

## Global Engineering Rules
- Make minimal, targeted, auditable changes.
- Preserve behavior unless explicit behavior change is requested.
- Never revert unrelated user changes.
- Keep UTC-aware temporal logic.

## Expert Response Policy
- For analysis, recommendations, or technical explanations, respond as a senior
  specialist in the subject.
- Do not default to agreeing with Marcelo; use critical, evidence-oriented
  reasoning and call out weak assumptions when needed.
- Prefer the most defensible answer over confirmation bias, while keeping tone
  collaborative and objective.
- Use external research/data/references only when necessary for correctness,
  temporal accuracy, or high-stakes decisions.

## Skill Traceability Policy
- For each response, declare which skill artifacts are being used.
- `AGENT_CORE` is implicit baseline and does not need to be repeated every time.
- In multi-step tasks, declare skills per step (not one global list for all steps).
- Only consult and declare skills relevant to the current step to avoid context mixing.
- Suggested format:
  - `Step <N> - Skills used: <skill-list>`
  - `Step <N> - Skills used: none specific (AGENT_CORE only)`

## Scope Governance (Implementation + Decision)
- Every operation must declare scope intent: `global_health` or `cohort_decision`.
- `global_health`: checks platform consistency across all stored runs for an asset.
- `cohort_decision`: checks only the cohort under analysis (same sweep/frozen
  set, same splits/horizons).
- Do not report `global_health` failures as if they invalidated a scoped
  purge/rerun operation.
- Do not report scoped pass as if it certified global platform health.

## Documentation Sync Rules

Before closing a PR that changes code behavior, contracts, metrics, commands or
methodology, perform **grep-based verification** of impacted documentation:

1. **List affected items.** Enumerate symbols (function names, paths, configs,
   constants) AND topics (e.g. `baselines`, `quantile_extraction`, `feature_pipeline`,
   `scope_governance`) that the change touches.

2. **Verify symbols and topics in a single batched Bash call** (use `&&` to chain
   greps; this minimizes round-trips and tokens):
   ```bash
   grep -rn '<symbol1>' docs/ && \
   grep -rn '<symbol2>' docs/ && \
   grep -rA2 'canonical_for' docs/ | grep -B1 '<topic1>' && \
   grep -rA2 'canonical_for' docs/ | grep -B1 '<topic2>'
   ```
   Use `grep -rn` (with line numbers) to get matching snippets, NOT `grep -rl`
   (filenames only). The snippet itself is often enough to triage.

3. **Triage from the snippet.** For each match returned, decide from the line
   alone:
   - If the snippet shows the reference is unaffected by the change, mark
     `[path:line] -> sem acao + razao: <trecho nao afetado>`.
   - Only open the full file if the snippet is genuinely ambiguous or the
     reference clearly needs update.

4. **Declare in the PR.** For each verified doc, list:
   `[path] -> [atualizado | sem acao + razao de 1 linha]`.

5. **Gap signal.** If an affected topic has no canonical doc declaring it
   (`canonical_for` empty for that topic), note it as a gap in the PR — either
   create a canonical doc (apply anti-overengineering rule) or justify why none
   is needed.

This rule replaces the previous static "always update X, Y, Z" approach. Coverage
must be derived from the actual diff, not from memory.

## Commit, PR and Versioning
Follow `docs/08_governance/GOVERNANCE_AND_VERSIONING.md` for:
- branch naming, commit message format, PR flow;
- pipeline/schema/model/sweep version identifiers;
- reproducibility policy and scope-aware quality semantics.

## Validation Rules
For relevant changes, run at least one applicable validation:
- touched unit tests,
- schema/contract checks,
- pipeline smoke check.

For analytics-impacting changes, additionally:
- run `python -m src.main_refresh_analytics_store --fail-on-quality` (global
  health gate);
- for statistical/model-selection decisions, run scoped validation (same cohort
  used in analysis) and report scope explicitly.

## Definition of Done
1. Requested outcome is implemented.
2. Relevant validations are executed (or explicitly reported as not run).
3. Documentation Sync Rules executed and result declared in PR.
4. Result is reproducible and traceable.
