from __future__ import annotations

from datetime import datetime, timezone

from src.domain.time.trading_calendar import (
    TradingDayPolicy,
    normalize_to_trading_day,
    trading_day_from_timestamp,
    trading_policy_from_asset_config,
)


def test_normalize_to_trading_day_default_behavior() -> None:
    ts = datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc)
    assert normalize_to_trading_day(ts).isoformat() == "2026-03-05"


def test_trading_day_after_close_goes_to_next_day() -> None:
    policy = TradingDayPolicy(close_hour=datetime.strptime("16:00", "%H:%M").time(), weekends=True)
    ts = datetime(2026, 3, 5, 18, 30, tzinfo=timezone.utc)
    assert trading_day_from_timestamp(ts, policy).isoformat() == "2026-03-06"


def test_trading_day_rolls_weekend_when_disabled() -> None:
    policy = TradingDayPolicy(close_hour=datetime.strptime("16:00", "%H:%M").time(), weekends=False)
    # Friday after close -> Saturday -> roll to Monday
    ts = datetime(2026, 3, 6, 18, 30, tzinfo=timezone.utc)
    assert trading_day_from_timestamp(ts, policy).isoformat() == "2026-03-09"


def test_policy_parses_time_and_weekends() -> None:
    cfg = {
        "open_hour": "09:30",
        "close_hour": "16:00",
        "weekends": False,
    }
    out = trading_policy_from_asset_config(cfg)
    assert out.open_hour.isoformat() == "09:30:00"
    assert out.close_hour.isoformat() == "16:00:00"
    assert out.weekends is False


def test_policy_accepts_iso_datetime_time_component() -> None:
    cfg = {
        "open_hour": "2026-03-05T09:30:00Z",
        "close_hour": "2026-03-05T16:00:00+00:00",
        "weekends": True,
    }
    out = trading_policy_from_asset_config(cfg)
    assert out.open_hour.isoformat() == "09:30:00"
    assert out.close_hour.isoformat() == "16:00:00"
    assert out.weekends is True
