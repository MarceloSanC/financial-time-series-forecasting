from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class TrainingProgressSnapshot:
    total_runs: int
    completed_runs: int
    remaining_runs: int
    avg_train_seconds: float | None
    eta_seconds: float | None


class TrainingProgressEstimator:
    @staticmethod
    def _valid_durations(values: Iterable[float | int | None]) -> list[float]:
        out: list[float] = []
        for value in values:
            if value is None:
                continue
            try:
                val = float(value)
            except Exception:
                continue
            if val > 0.0:
                out.append(val)
        return out

    @staticmethod
    def build_snapshot(
        *,
        total_runs: int,
        completed_runs: int,
        successful_train_durations_seconds: Iterable[float | int | None],
    ) -> TrainingProgressSnapshot:
        total = max(0, int(total_runs))
        completed = max(0, min(int(completed_runs), total))
        remaining = max(0, total - completed)

        durations = TrainingProgressEstimator._valid_durations(
            successful_train_durations_seconds
        )
        if durations:
            avg = float(sum(durations) / len(durations))
            eta = float(avg * remaining)
        else:
            avg = None
            eta = None

        return TrainingProgressSnapshot(
            total_runs=total,
            completed_runs=completed,
            remaining_runs=remaining,
            avg_train_seconds=avg,
            eta_seconds=eta,
        )

    @staticmethod
    def format_eta(eta_seconds: float | None) -> str:
        if eta_seconds is None:
            return "N/A"
        return str(timedelta(seconds=int(max(0.0, eta_seconds))))
