# PROJECT SCOPE PRINCIPLES

## Purpose
Guide technical decisions toward v0 objectives with academic defensibility, reproducibility, interpretability, and anti-overengineering discipline.

## Scope
Covers:
1. Scope control for v0 vs post-v0 decisions
2. Anti-overengineering tradeoff decisions
3. Reproducibility and statistical defensibility criteria
4. Interpretability requirements for training and inference outputs

## Inherited from AGENT_CORE
- Priority order and conflict handling
- Data/temporal safety requirements
- Validation discipline
- Commit rules and documentation sync expectations

Overrides/additions in this skill:
- Project-specific decision heuristics for what is essential vs optional
- Strong preference for persisted evidence over ad-hoc analysis
- Explicit guardrails for fair model comparison

## When to Use
- Evaluating whether a new task is necessary for v0.
- Choosing between simple robust implementation vs complex automation.
- Defining what evidence is required for final academic analysis.
- Deciding whether a metric/report/plot belongs to current scope.

## When Not to Use
- Pure coding tasks with already-fixed scope and acceptance criteria.
- Local refactors with no project-level tradeoff impact.

## Inputs Required
- Requested change and intended decision impact
- Current checklist status (P0/P1/P2)
- Required evidence outputs (tables/plots/stat tests)
- Risk of retraining/rework if data is not persisted now

## Execution Steps
1. Classify request by scope level:
   - v0-essential (P0), recommended (P1), post-v0 (P2).
2. Apply anti-overengineering filter:
   - prioritize data completeness and reproducibility over sophisticated orchestration.
3. Enforce fairness requirements for comparison:
   - aligned OOS intersection, consistent horizons/splits, same scope cohort.
4. Enforce interpretability minimums:
   - global feature importance + local contribution summary when in scope.
5. Prefer persisted, auditable outputs:
   - silver/gold artifacts and reproducible reports over ephemeral outputs.
6. If ambiguous, ask Marcelo with concrete options and one `(Recommended)`.

## Outputs Expected
- Clear scope decision (P0/P1/P2)
- Rationale aligned with academic defensibility
- Explicit list of required persisted artifacts
- Minimal implementation path without unnecessary complexity

## Validation
- Scope check:
  - decision is mapped to checklist priority and release objective.
- Reproducibility check:
  - outputs can be rebuilt from persisted data without retraining.
- Comparability check:
  - statistical tests use aligned OOS intersection.
- Interpretability check:
  - required feature-level evidence exists for selected scope.

Example checks:
- `python -m src.main_refresh_analytics_store --fail-on-quality`
- Verify relevant tables/plots exist for target sweep scope before analysis.

## Common Failures and Fixes
- Failure: adding complex workflow before securing core evidence.
  - Fix: implement minimal persisted data path first.
- Failure: mixing heterogeneous cohorts in final comparison.
  - Fix: apply frozen/sweep scope filters consistently.
- Failure: interpreting results without statistical validity gates.
  - Fix: enforce DM/MCS/win-rate only on aligned OOS intersection.
- Failure: broad scope expansion in v0.
  - Fix: defer non-essential items to P2 with explicit rationale.

## Definition of Done
- Decision is consistent with v0 objectives and checklist priorities.
- Required evidence for reproducible, defensible analysis is preserved.
- No unnecessary architectural complexity was introduced.
- Tradeoffs are explicit and auditable.

## References
- `docs/ai/AGENT_CORE.md`
- `docs/05_checklists/ANALYTICS_STORE_CHECKLIST.md`
- `docs/05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md`
- `docs/07_reports/PROJECT_FULL_TECHNICAL_REVIEW_2026-03-30.md`
- `docs/07_reports/BUSINESS_REPORT.md`
