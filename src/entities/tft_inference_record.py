from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TFTInferenceRecord:
    asset_id: str
    timestamp: datetime
    model_version: str
    model_path: str
    feature_set_name: str
    features_used_csv: str
    prediction: float
    quantile_p10: float | None = None
    quantile_p50: float | None = None
    quantile_p90: float | None = None
    inference_run_id: str | None = None
    # Explicit temporal semantics for analytics:
    # - decision_timestamp: instant when model made decision
    # - target_timestamp: instant being predicted
    # timestamp remains backwards-compatible (defaults to target timestamp in engine).
    target_timestamp: datetime | None = None
    decision_timestamp: datetime | None = None
    horizon: int = 1
