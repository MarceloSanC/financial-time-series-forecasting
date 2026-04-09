# Reproducibility Policy

## Must Have
- immutable run records
- schema contracts
- quality-gated analytics refresh

## Validation
- documented rerun procedure
- deterministic comparison inputs

## Scope-Aware Quality Semantics
- Global quality checks validate platform/asset health and historical consistency.
- Scoped quality checks validate a specific cohort decision context.
- For statistical winner selection, scoped validation is mandatory and must match the same cohort/splits/horizons used in analysis.
- A global failure does not invalidate a scoped purge/rerun operation by itself; it indicates unresolved issues outside (or across) the chosen scope.

## Decision Integrity
- Every final decision artifact must record the exact analysis scope.
- Re-running with a new cohort prefix must preserve old cohorts for auditability, unless an explicit purge is requested.
