# Multi-Horizon Strategy

## Horizons
- Default evaluation horizons: `h+1`, `h+7`, `h+30`

## Contract
- Persist `horizon` per prediction row
- Persist `target_timestamp` for each horizon

## Validation
- coverage by horizon
- comparable temporal intersection per horizon
