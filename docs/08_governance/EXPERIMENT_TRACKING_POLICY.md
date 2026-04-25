---
title: Experiment Tracking Policy
scope: Politica de IDs e rastreabilidade de experimentos (`run_id` deterministico, `execution_id` por tentativa fisica, `parent_sweep_id`, fingerprints). Define o que deve ser persistido para reproducao auditavel.
update_when:
  - composicao do hash de `run_id` ou `execution_id` mudar
  - politica de tracking (que IDs sao obrigatorios) mudar
  - novo campo de rastreabilidade for adicionado
canonical_for: [experiment_tracking_policy, run_id_policy, execution_id_policy, tracking_ids]
---

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
