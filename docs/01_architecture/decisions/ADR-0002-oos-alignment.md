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
