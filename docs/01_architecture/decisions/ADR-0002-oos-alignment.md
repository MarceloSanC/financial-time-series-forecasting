---
title: ADR-0002 Strict OOS Temporal Alignment for Paired Tests
scope: Decisao arquitetural de exigir alinhamento temporal estrito por target_timestamp em todos os testes pareados (DM/MCS/win-rate). Status Accepted.
update_when:
  - decisao for revisada (status mudar de Accepted para Superseded)
  - politica de alinhamento OOS mudar
canonical_for: [adr_0002, oos_alignment_decision, paired_tests_decision]
---

# ADR-0002: Strict OOS Temporal Alignment for Paired Tests

## Status
Accepted

## Context
DM/MCS/win-rate are invalid under misaligned target timestamps.

## Decision
All paired tests must use explicit temporal intersection by `target_timestamp` and `horizon`.

## Consequences
- Some runs become non-comparable in global analysis
- Statistical validity is preserved
