# Analytics Store Architecture

## Layers
- Silver: atomic and traceable records
- Gold: aggregated decision-ready tables

## Principles
- Schema-versioned tables
- Append-only facts (except explicit reprocess)
- Contract tests and quality gates
