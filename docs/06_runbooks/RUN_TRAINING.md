---
title: Run Training
scope: Comando canonico curto de treino TFT e validacao minima. Para parametros CLI completos, ver 03_modeling/TRAINING_PIPELINE.md.
update_when:
  - comando canonico mudar
  - validacao minima pos-treino mudar
canonical_for: [run_training, training_command]
---

# Run Training

## Command
`python -m src.main_train_tft --asset AAPL --features BASELINE_FEATURES,TECHNICAL_FEATURES`

## Validate
- model artifacts created
- analytics silver rows persisted
