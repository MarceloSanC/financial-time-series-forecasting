# MODEL PERFORMANCE AND RESEARCH ADVISOR

## Purpose
Provide senior-level guidance to evaluate sweeps, models, and forecasting quality with academic rigor and market realism.

Primary objective:
- Improve return prediction and probabilistic quality (calibration + uncertainty) using defensible statistical evidence.

## Scope
Covers:
1. Sweep-level diagnosis (cohort quality, comparability, robustness)
2. Model-level diagnosis (point accuracy, probabilistic quality, stability)
3. Statistical comparison (DM, MCS, win-rate, confidence intervals)
4. Interpretability analysis (global importance + local contributions when available)
5. Decision support (what to keep, retest, recalibrate, or discard)

Does not cover:
- Direct code implementation details (use module/orchestrator/testing skills)
- Generic business storytelling without statistical evidence

## Inherited from AGENT_CORE
- Safety and truthfulness over agreement
- Temporal/data leakage prevention and UTC discipline
- Validation-first behavior
- Documentation and commit governance

Project-specific additions in this skill (aligned with docs/ai/skills/skill-creator/SKILL.md):
- Senior-level evaluation protocol for point, probabilistic, and statistical evidence
- Explicit decision framing (primary/fallback) with confidence and limitations

Additional inheritance for this skill:
- `docs/ai/skills/project-scope-principles/SKILL.md`
  - enforce reproducibility, anti-overengineering, and v0 focus

## When to Use
- User asks to interpret sweep outputs, model quality, or statistical significance
- User asks which model/config to select for final evaluation or production
- User asks to diagnose contradictions across plots/tables
- User asks for academically defensible conclusions

## When Not to Use
- Pure implementation request with no analytical decision-making
- One-off chart description that does not require decision framing

## Inputs Required
- Scoped cohort definition (recommended: `parent_sweep_id` prefix or frozen candidates)
- Relevant artifacts/tables (gold and, when needed, silver)
- Target horizon(s) and split(s)
- Decision objective (e.g., best calibrated, best RMSE, best robust trade-off)

Minimum required data for final decision:
- `gold_prediction_metrics_by_config`
- `gold_prediction_metrics_by_run_split_horizon`
- `gold_dm_pairwise_results`
- `gold_mcs_results`
- `gold_win_rate_pairwise_results`
- `gold_model_decision_final`
- `gold_prediction_calibration`
- `gold_prediction_risk`

## Execution Steps
1. Lock cohort and comparability
- Enforce exact cohort scope before conclusions.
- Reject mixed sweeps/cohorts unless explicitly requested.
- Confirm pairwise comparability by exact `target_timestamp` intersection.

2. Run quality gates mentally (or request command evidence)
- Confirm analytics quality checks passed.
- Flag missing/empty statistical artifacts before interpreting rankings.

3. Evaluate point-performance layer
- Review RMSE/MAE/DA by horizon and split.
- Prefer consistency across folds/seeds over isolated best point estimate.

4. Evaluate probabilistic layer
- Review Pinball, PICP, MPIW.
- Interpret calibration trade-off: coverage vs interval width.
- Penalize degenerate quantile behavior.

5. Evaluate statistical dominance layer
- Use DM p-values, MCS inclusion, and win-rate together.
- Avoid winner claims when pairwise evidence is weak/inconclusive.

6. Evaluate robustness layer
- Check fold/seed dispersion and confidence intervals.
- Highlight fragile winners (small average gain + high variance).

7. Evaluate interpretability layer
- Global: feature importance by horizon/family.
- Local: feature contribution only when data is available and scoped correctly.
- Explicitly state when local explanation is unavailable due to data contract/scope mismatch.

8. Produce decision recommendation
- Return shortlist with rationale and risk notes.
- Provide next experiments ranked by expected information gain.

## Outputs Expected
Produce a structured response with these sections:
1. Scope and validity checks
2. Key findings (point, probabilistic, statistical, robustness)
3. Decision recommendation (primary + fallback)
4. Known limitations and confidence level
5. Next actions (prioritized)

Preferred final artifacts:
- Sweep analysis markdown report in `docs/07_reports/`
- Explicit criteria table (accept/reject per candidate)

## Validation
Hard checks before strong claims:
- Statistical tables exist and are non-empty for the scoped cohort.
- Pairwise comparisons use exact temporal intersection.
- Conclusions do not rely on one metric only.
- Probabilistic conclusions include both PICP and MPIW.

Suggested command examples:
- `python -m src.main_refresh_analytics_store --fail-on-quality`
- Scoped plot refresh:
  - `python -m src.main_refresh_analytics_store --plots-asset <ASSET> --plots-scope-sweep-prefixes <PREFIX>`

## Common Failures and Fixes
- Failure: Declaring a winner from RMSE only.
  - Fix: Require DM/MCS/win-rate + calibration confirmation.

- Failure: Mixing non-comparable cohorts.
  - Fix: Enforce scope by sweep prefix/frozen set and restate scope in output.

- Failure: Interpreting empty local-contribution plot as "no feature effect".
  - Fix: Treat as availability/scope issue, not model evidence.

- Failure: Overstating tiny metric differences.
  - Fix: Compare effect size vs dispersion and CI overlap.

## Definition of Done
- Cohort is explicit and comparable.
- Claims are supported by point + probabilistic + statistical evidence.
- Recommendation includes trade-offs and confidence level.
- Limitations are explicit (data gaps, scope constraints, weak significance).
- Next steps are concrete and prioritized.

## References
- `docs/ai/skills/skill-creator/SKILL.md`
- `docs/ai/AGENT_CORE.md`
- `docs/ai/skills/project-scope-principles/SKILL.md`
- `docs/05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md`
- `docs/05_checklists/ANALYTICS_STORE_CHECKLIST.md`
- `docs/07_reports/SWEEP_0_2_3_PLOTS_ANALYSIS.md`
- `src/use_cases/refresh_analytics_store_use_case.py`
- `src/use_cases/validate_analytics_quality_use_case.py`
