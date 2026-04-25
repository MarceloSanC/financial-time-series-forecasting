from __future__ import annotations

from src.domain.services.quantile_guardrail_service import QuantileGuardrailService


def test_guardrail_keeps_already_ordered_triplet() -> None:
    out = QuantileGuardrailService.enforce_monotonic_triplet(-0.1, 0.0, 0.2)
    assert out.p10_post == -0.1
    assert out.p50_post == 0.0
    assert out.p90_post == 0.2
    assert out.applied is False


def test_guardrail_reorders_crossed_triplet() -> None:
    out = QuantileGuardrailService.enforce_monotonic_triplet(0.2, -0.1, 0.0)
    assert out.p10_post == -0.1
    assert out.p50_post == 0.0
    assert out.p90_post == 0.2
    assert out.applied is True


def test_guardrail_skips_when_any_quantile_is_missing() -> None:
    out = QuantileGuardrailService.enforce_monotonic_triplet(None, 0.0, 0.2)
    assert out.p10_post is None
    assert out.p50_post == 0.0
    assert out.p90_post == 0.2
    assert out.applied is False
