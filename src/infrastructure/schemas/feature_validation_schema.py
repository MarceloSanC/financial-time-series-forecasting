from __future__ import annotations

from src.infrastructure.schemas.feature_registry import (
    FEATURE_REGISTRY,
    list_feature_specs,
)

# Canonical list of implemented model input features from centralized registry.
IMPLEMENTED_FEATURES: list[str] = [s.name for s in list_feature_specs()]

FEATURE_WARMUP_BARS: dict[str, int] = {
    name: int(spec.warmup_count)
    for name, spec in FEATURE_REGISTRY.items()
    if int(spec.warmup_count) > 0
}

FEATURE_ANTI_LEAKAGE_TAGS: dict[str, str] = {
    name: spec.anti_leakage_tag
    for name, spec in FEATURE_REGISTRY.items()
}
