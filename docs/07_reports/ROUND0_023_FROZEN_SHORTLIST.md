---
title: Round 0 (0_2_3) Frozen Shortlist
scope: Shortlist congelada da Round 0 (sweep 0_2_3) com champion provisorio + fallback selecionados pre-Round 1. Documento historico congelado — nao deve ser re-rankeado pos-fato.
update_when:
  - nunca apos congelamento (documento historico)
  - apenas se nova rodada Round 0 (ex.: 0_3_X) gerar nova shortlist (criar arquivo novo, nao editar este)
canonical_for: [round0_023_frozen_shortlist, frozen_candidates_023]
---

# Round 0 (0_2_3) Frozen Shortlist

Purpose: freeze provisional champion + fallback from Round 0 for Round 1 confirmation (`1_X_X`).

Selection policy: test split, scoped to `parent_sweep_id` starting with `0_2_3_`, sorted by `rank_rmse` (tie-breakers: `rank_da`, `win_rate_ex_ties_mean` when available).

| role | horizon | feature_set | config_signature | config_label | rank_rmse | rank_da | dm_net_wins | win_rate_ex_ties_mean | parent_sweep_id |
|---|---:|---|---|---|---:|---:|---:|---:|---|
| champion_provisorio | 1 | S | e6785be1e45c603d45360ba79344fd5ee92036145b206af23e9dae1473becc89 | S|e6785be1e45c603d45360ba79344fd5ee92036145b206af23e9dae1473becc89 | 19 | 5594 | 4 | 0.5031 | 0_2_3_explicit_frozen_0_1_configs_sentiment_features |
| fallback_provisorio | 1 | S | 0b8dca588f90a77676abf1b7aeafce65c3f53ca5d2c095490a05bcaa405c8d7e | S|0b8dca588f90a77676abf1b7aeafce65c3f53ca5d2c095490a05bcaa405c8d7e | 21 | 1620 | 9 | 0.5264 | 0_2_3_explicit_frozen_0_1_configs_sentiment_features |
