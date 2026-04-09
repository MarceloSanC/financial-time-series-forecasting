# Experiment Tracking Policy

## Required IDs
- run_id
- model_version
- config_signature
- split_fingerprint
- parent_sweep_id

## Reproducibility Requirements
- persisted artifacts
- deterministic config serialization

## Cohort Scope Governance
- Statistical/model-selection conclusions must be based on an explicit cohort scope.
- Accepted scope selectors:
  - parent_sweep_id prefix (for example `0_2_3_`)
  - frozen candidates list (csv)
- Any report/table used for winner selection must declare:
  - scope selector used
  - splits used
  - horizons used
- Global unscope outputs are health monitoring artifacts and must not be used alone for scoped winner claims.

## Cross-Cohort Safety
- Never mix runs from different cohorts in pairwise statistical decision tables (DM/MCS/win-rate) without explicit declaration and justification.
- Pairwise comparisons must use exact target timestamp intersection.
