# Documentation Index

This index is the single entrypoint for project documentation.

README synchronization note:
- `README.md` was aligned on 2026-04-02 to reference the current docs tree and canonical runbooks/checklists.

## How To Use This Docs Set
- **Start at `docs/00_overview/STRATEGIC_DIRECTION.md`** for current objective, methodological pivot, and execution roadmap (supersedes earlier plans).
- Then `docs/00_overview/PROJECT_OVERVIEW.md` for scope and goals.
- Use `docs/06_runbooks/*` for execution commands.
- Use `docs/05_checklists/*` as implementation and validation gates.
- Use `docs/04_evaluation/*` for metrics, baselines, calibration, statistical
  tests, and explainability definitions.
- Use `docs/ai/*` for agent-specific workflow and reusable skills.

## AI Playbook
- AI index: `docs/ai/INDEX.md`
- Agent core: `docs/ai/AGENT_CORE.md`
- Agent workflow: `docs/ai/WORKFLOW.md`

## Sections
- `00_overview/`: project scope, glossary, and high-level framing.
- `01_architecture/`: architecture, data flow, and technical decisions (ADR).
- `02_data/`: data sources, contracts, feature sets, and quality gates.
- `03_modeling/`: training, inference, sweeps, multi-horizon strategy.
- `04_evaluation/`: metrics, baselines, statistical tests, calibration/risk,
  explainability, plot interpretation.
- `05_checklists/`: delivery checklists and completion criteria.
- `06_runbooks/`: operational commands, expected outputs, troubleshooting.
- `07_reports/`: report templates, living-paper material, and phase gates.
  - `phase-gates/`: auditorias e gates de entrada por fase (A, B, C...) — artefatos datados de ciclo de vida.
- `08_governance/`: governance, branch/commit/PR flow, versioning, reproducibility, roadmap.
- `ai/`: agent-focused skills, context, and workflow guidance.

## Canonical Files In Current Project State
- **Strategic direction (current): `docs/00_overview/STRATEGIC_DIRECTION.md`**
- Analytics store checklist: `docs/05_checklists/ANALYTICS_STORE_CHECKLIST.md`
- Predictions/metrics checklist: `docs/05_checklists/PREDICTIONS_AND_METRICS_CHECKLIST.md`
- Feature set checklist: `docs/05_checklists/FEATURES_SET_CHECKLIST.md`
- Training pipeline (legacy params doc): `docs/03_modeling/TRAINING_PIPELINE.md`
- Inference pipeline (legacy params doc): `docs/03_modeling/INFERENCE_PIPELINE.md`
- Sweeps runbook: `docs/06_runbooks/RUN_SWEEPS.md`
- Sweep purge runbook: `docs/06_runbooks/RUN_SWEEPS.md` (section 11)
- Governance and versioning: `docs/08_governance/GOVERNANCE_AND_VERSIONING.md`
- Baselines contract: `docs/04_evaluation/BASELINES.md`
- Calibration and risk contract: `docs/04_evaluation/CALIBRATION_AND_RISK.md`
- Explainability contract: `docs/04_evaluation/EXPLAINABILITY.md`

## Documentation Rules
- One topic, one source of truth.
- Cross-link; avoid duplicated definitions.
- Keep runbooks command-first and verifiable.
- Any metric or table used in decisions must have a documented definition.
