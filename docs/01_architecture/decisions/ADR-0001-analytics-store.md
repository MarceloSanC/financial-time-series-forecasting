---
title: ADR-0001 Analytics Store as Source of Truth
scope: Decisao arquitetural de usar analytics store (Parquet silver + DuckDB gold reconstruivel) como base de avaliacao reproduzivel sem retraining. Status Accepted.
update_when:
  - decisao for revisada (status mudar de Accepted para Superseded)
  - novo ADR derivado tornar este obsoleto
canonical_for: [adr_0001, analytics_store_decision, source_of_truth_decision]
---

# ADR-0001: Analytics Store as Source of Truth

## Status
Accepted

## Context
Need reproducible and auditable model evaluation without retraining.

## Decision
Use silver/gold analytics store with explicit schema contracts.

## Consequences
- Higher data persistence footprint
- Strong reproducibility and auditability
