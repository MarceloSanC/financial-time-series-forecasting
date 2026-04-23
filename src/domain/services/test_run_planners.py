from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.domain.services.tft_sweep_experiment_builder import (
    SweepExperiment,
    build_one_at_a_time_experiments,
)


@dataclass(frozen=True)
class TestRunSpec:
    run_label: str
    training_config: dict[str, Any]
    varied_param: str | None
    varied_value: Any | None


def build_ofat_run_specs(
    *,
    base_config: dict[str, Any],
    param_ranges: dict[str, list[Any]],
) -> list[TestRunSpec]:
    experiments = build_one_at_a_time_experiments(
        base_config=base_config,
        param_ranges=param_ranges,
    )
    return [
        TestRunSpec(
            run_label=exp.run_label,
            training_config=dict(exp.config),
            varied_param=exp.varied_param,
            varied_value=exp.varied_value,
        )
        for exp in experiments
    ]


def build_explicit_run_specs(
    *,
    base_config: dict[str, Any],
    explicit_configs: list[dict[str, Any]],
) -> list[TestRunSpec]:
    specs: list[TestRunSpec] = []
    for idx, item in enumerate(explicit_configs, start=1):
        cfg = dict(base_config)
        cfg.update(dict(item.get("training_config", {})))
        run_label = str(item.get("run_label") or f"config_{idx:03d}")
        specs.append(
            TestRunSpec(
                run_label=run_label,
                training_config=cfg,
                varied_param=None,
                varied_value=None,
            )
        )
    return specs


def run_specs_to_experiments(run_specs: list[TestRunSpec]) -> list[SweepExperiment]:
    return [
        SweepExperiment(
            run_label=s.run_label,
            config=dict(s.training_config),
            varied_param=s.varied_param,
            varied_value=s.varied_value,
        )
        for s in run_specs
    ]
