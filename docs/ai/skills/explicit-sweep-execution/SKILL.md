# EXPLICIT SWEEP EXECUTION

## Purpose
Execute explicit-config sweeps in isolated cohorts with reproducible commands, safe resume behavior, and analysis-ready outputs.

## Scope
Covers:
1. Preparing explicit sweep config batches
2. Running multiple explicit configs sequentially
3. Isolating new cohorts by prefix
4. Post-run validation and refresh steps for analytics
5. Merge/resume recovery with deterministic orphan cleanup

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Cohort isolation policy by sweep prefix
- Explicit command templates for batch execution
- Resume policy and reconciliation requirements for interrupted runs
- Post-run checks required for statistical analysis readiness

## When to Use
- Running explicit-config evaluation batches (e.g., `0_2_3_*`).
- Re-running a final cohort after pipeline fixes.
- Preparing data for scoped final analysis/plots.
- Resuming interrupted explicit sweeps with `merge_tests`.

## When Not to Use
- Optuna/HPO sweeps.
- One-off single-model debugging runs.

## Inputs Required
- Asset (e.g., `AAPL`)
- Config prefix (e.g., `0_2_3_`)
- Config directory path
- Continue-on-error requirement
- Plot scope target (`scope csv` and/or `sweep prefixes`)
- Scope intent (`global_health` or `cohort_decision`)
- Resume policy fields (for merge mode):
  - `resume_policy`: `keep_completed | rewind_last | rewind_last_n`
  - `rewind_n`: integer `>= 1` when `rewind_last_n`
  - `reconcile_orphans`: boolean
  - `cleanup_failed_or_incomplete`: boolean
  - `dry_run_cleanup`: boolean

## Scope Discipline Policy
- Any statistical comparison (DM/MCS/win-rate/final ranking) must run on explicit cohort scope.
- Global quality checks are allowed for health monitoring, but cannot be used as final evidence for scoped winner selection.
- Every final analysis report must restate the exact scope used (prefix/csv/splits/horizons/status filter).
- During purge/rerun operations with explicit target prefix:
  - global failures outside target scope must be reported as global health findings,
  - and must not be mislabeled as purge/rerun failure for that scope.

## Quality Modes (Execution Semantics)
- `global_health`:
  - validates full asset history in silver/gold.
  - use for platform health and long-horizon consistency.
- `cohort_decision`:
  - validates only target cohort used in analysis decision.
  - use for winner selection evidence and scoped regression.
- Best practice:
  - run scoped checks first for decision workflows,
  - then run global checks to report platform residual issues separately.

## Resume Policy (Merge Mode)
Use deterministic cleanup before scheduling new runs:
1. Build official run index from `sweep_runs.csv`.
2. Build physical index from `folds/*/models/*`.
3. Build analytics index from `dim_run`/fact tables for target `parent_sweep_id`.
4. If `resume_policy` is rewind:
   - remove last `N` official runs from execution ledger and queue them again.
5. If reconciliation enabled:
   - remove physical artifacts not present in official run index.
   - remove analytics rows for orphan `run_id`s.
6. If `cleanup_failed_or_incomplete=true`:
   - remove failed/incomplete runs from ledger and artifacts, then requeue.

Safety requirements:
- Cleanup must be idempotent.
- Cleanup must emit a plan/report artifact before and after execution.
- In `dry_run_cleanup=true`, no delete action is allowed.

## Execution Steps
1. Isolate new cohort prefix:
   - never reuse old analysis prefix for corrected reruns.
2. Validate config files:
   - ensure `output_subdir` and filename share same target prefix.
3. If merge mode is enabled:
   - compute resume plan and orphan reconciliation plan.
   - apply cleanup policy (or dry-run report only).
4. Execute all explicit configs in sorted order.
5. Continue on failures without stopping batch.
6. Refresh analytics and quality checks.
7. Generate plots using scoped selectors only.

## Outputs Expected
- New sweep artifacts under isolated prefix
- Silver/gold refreshed with new cohort data
- Scoped plots and statistics for final comparison
- No cross-cohort contamination in final analysis scope
- Resume plan + cleanup report for auditability (when merge mode used)

## Validation
- Prefix integrity check:
  - all executed files match target prefix.
- Quality gate check:
  - `main_refresh_analytics_store --fail-on-quality` passes (global health).
- Scoped decision check (mandatory for winner claims):
  - statistical tables/plots are generated from the same scoped cohort used in the decision.
- Scope check:
  - plots generated with `--plots-scope-*` for target cohort.
- Merge/resume consistency checks:
  - no orphan model directory left after cleanup.
  - no orphan analytics `run_id` for the target sweep.
  - no duplicate run counting in cohort expected-run totals.

Example commands:
- Batch execution:
  - `for cfg in $(ls config/sweeps/explicit/0_2_3_explicit_frozen_0_1_configs_*.json | grep -v manifest | sort); do MPLBACKEND=Agg .venv/bin/python -m src.main_tft_test_pipeline --asset AAPL --config-json "$cfg" || echo "FAILED (continuando): $cfg"; done`
- Resume execution:
  - `for cfg in $(ls config/sweeps/explicit/0_2_3_explicit_frozen_0_1_configs_*.json | grep -v manifest | sort); do MPLBACKEND=Agg .venv/bin/python -m src.main_tft_test_pipeline --asset AAPL --config-json "$cfg" --merge-tests || echo "FAILED (continuando): $cfg"; done`
- Refresh + scoped plots:
  - `python -m src.main_refresh_analytics_store --fail-on-quality --plots-asset AAPL --plots-scope-csv data/analytics/selection/frozen_candidates_0_2_3.csv --plots-scope-sweep-prefixes 0_2_3_`

## Common Failures and Fixes
- Failure: mixed old/new cohorts in analysis.
  - Fix: enforce new prefix and scoped plot filters.
- Failure: quality pass fails after batch.
  - Fix: inspect failed checks and rerun only affected configs.
- Failure: rerun overwrites interpretation baseline.
  - Fix: freeze candidates per cohort and keep old cohorts for audit only.
- Failure: interrupted merge leaves orphan artifacts.
  - Fix: enable reconciliation + orphan cleanup before resuming.
- Failure: global findings reported as scoped failure.
  - Fix: split report into `cohort_decision` result and `global_health` residual findings.

## Definition of Done
- Cohort executed under isolated prefix.
- Analytics refresh and quality gates completed.
- Scoped artifacts are available for final statistical analysis.
- Execution log is reproducible via listed commands.
- Merge/resume cleanup report confirms no orphans in target sweep.

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/testing-execution/SKILL.md`
- `docs/ai/skills/project-scope-principles/SKILL.md`
- `docs/05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md`
