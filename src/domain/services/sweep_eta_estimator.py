from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SweepEtaEstimator:
    total_trials: int
    samples_seconds: list[float] = field(default_factory=list)

    def add_sample(self, duration_seconds: float | None) -> None:
        if duration_seconds is None:
            return
        if duration_seconds <= 0:
            return
        self.samples_seconds.append(float(duration_seconds))

    @property
    def avg_seconds(self) -> float | None:
        if not self.samples_seconds:
            return None
        return sum(self.samples_seconds) / len(self.samples_seconds)

    def estimate_remaining_seconds(self, completed_trials: int) -> float | None:
        avg = self.avg_seconds
        if avg is None:
            return None
        remaining = max(0, int(self.total_trials) - int(completed_trials))
        return remaining * avg

    @staticmethod
    def format_seconds(seconds: float | None) -> str:
        if seconds is None:
            return "N/A"
        total = int(round(seconds))
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        if h > 0:
            return f"{h}h {m}m {s}s"
        if m > 0:
            return f"{m}m {s}s"
        return f"{s}s"
