from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class QuantileGuardrailResult:
    p10_post: float | None
    p50_post: float | None
    p90_post: float | None
    applied: bool


class QuantileGuardrailService:
    """Monotonic quantile guardrail (p10 <= p50 <= p90) for persistence contracts."""

    @staticmethod
    def enforce_monotonic_triplet(
        p10: float | None,
        p50: float | None,
        p90: float | None,
    ) -> QuantileGuardrailResult:
        values = [p10, p50, p90]
        if any(v is None for v in values):
            return QuantileGuardrailResult(
                p10_post=p10,
                p50_post=p50,
                p90_post=p90,
                applied=False,
            )

        try:
            a = float(p10)  # type: ignore[arg-type]
            b = float(p50)  # type: ignore[arg-type]
            c = float(p90)  # type: ignore[arg-type]
        except Exception:
            return QuantileGuardrailResult(
                p10_post=p10,
                p50_post=p50,
                p90_post=p90,
                applied=False,
            )

        if not (isfinite(a) and isfinite(b) and isfinite(c)):
            return QuantileGuardrailResult(
                p10_post=a,
                p50_post=b,
                p90_post=c,
                applied=False,
            )

        ordered = sorted([a, b, c])
        applied = not (ordered[0] == a and ordered[1] == b and ordered[2] == c)
        return QuantileGuardrailResult(
            p10_post=float(ordered[0]),
            p50_post=float(ordered[1]),
            p90_post=float(ordered[2]),
            applied=applied,
        )
