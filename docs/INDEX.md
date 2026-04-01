# Documentation Index

This index is the single entrypoint for project documentation.

## How To Use This Docs Set
- Start at `docs/00_overview/PROJECT_OVERVIEW.md` for scope and goals.
- Use `docs/06_runbooks/*` for execution commands.
- Use `docs/05_checklists/*` as implementation and validation gates.
- Use `docs/04_evaluation/*` for metric/statistical definitions.

## Sections
- `00_overview/`: project scope, glossary, and high-level framing.
- `01_architecture/`: architecture, data flow, and technical decisions (ADR).
- `02_data/`: data sources, contracts, feature sets, and quality gates.
- `03_modeling/`: training, inference, sweeps, multi-horizon strategy.
- `04_evaluation/`: metrics, statistical tests, calibration/risk, plot interpretation.
- `05_checklists/`: delivery checklists and completion criteria.
- `06_runbooks/`: operational commands, expected outputs, troubleshooting.
- `07_reports/`: report templates and living-paper material.
- `08_governance/`: contribution rules, versioning policy, roadmap.

## Canonical Files In Current Project State
- Analytics store checklist: `docs/05_checklists/ANALYTICS_STORE_CHECKLIST.md`
- Predictions/metrics checklist: `docs/05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md`
- Feature set checklist: `docs/05_checklists/FEATURES_SET_CHECKLIST.md`
- Training pipeline (legacy params doc): `docs/03_modeling/TRAINING_PIPELINE.md`
- Inference pipeline (legacy params doc): `docs/03_modeling/INFERENCE_PIPELINE.md`
- Sweeps runbook: `docs/06_runbooks/RUN_SWEEPS.md`

## Documentation Rules
- One topic, one source of truth.
- Cross-link; avoid duplicated definitions.
- Keep runbooks command-first and verifiable.
- Any metric or table used in decisions must have a documented definition.
