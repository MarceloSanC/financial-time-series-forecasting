# src/domain/time/trading_calendar.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone


@dataclass(frozen=True)
class TradingDayPolicy:
    open_hour: time = time(0, 0)
    close_hour: time = time(23, 59)
    weekends: bool = True


def _parse_time_like(value: str) -> time:
    v = str(value).strip()
    if not v:
        raise ValueError("Time value cannot be empty")

    # HH:MM or HH:MM:SS
    try:
        parsed = time.fromisoformat(v)
        if parsed.tzinfo is not None:
            raise ValueError("Time with timezone is not supported in trading policy")
        return parsed
    except ValueError:
        pass

    # ISO datetime -> extract time component
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        parsed = dt.timetz().replace(tzinfo=None)
        return parsed
    except ValueError as exc:
        raise ValueError(
            f"Invalid time value '{value}'. Expected HH:MM[:SS] or ISO datetime."
        ) from exc


def trading_policy_from_asset_config(asset_cfg: dict) -> TradingDayPolicy:
    open_raw = asset_cfg.get("open_hour", "00:00")
    close_raw = asset_cfg.get("close_hour", "23:59")
    weekends_raw = asset_cfg.get("weekends", True)

    open_hour = _parse_time_like(str(open_raw))
    close_hour = _parse_time_like(str(close_raw))
    weekends = bool(weekends_raw)

    if open_hour == close_hour:
        raise ValueError("Invalid trading policy: open_hour and close_hour cannot be equal")

    return TradingDayPolicy(open_hour=open_hour, close_hour=close_hour, weekends=weekends)


def _roll_to_business_day(day: date) -> date:
    out = day
    while out.weekday() >= 5:
        out = out + timedelta(days=1)
    return out


def trading_day_from_timestamp(ts: datetime, policy: TradingDayPolicy | None = None) -> date:
    """
    Map a timestamp to an effective trading/reference day in UTC.

    Rule:
    - if ts.time() > close_hour, record belongs to next day;
    - if weekends=False, Saturday/Sunday are rolled forward to Monday.
    """
    if ts.tzinfo is None:
        raise ValueError(
            "Timestamp must be timezone-aware for trading day normalization"
        )

    p = policy or TradingDayPolicy()
    ts_utc = ts.astimezone(timezone.utc)
    day = ts_utc.date()
    if ts_utc.time() > p.close_hour:
        day = day + timedelta(days=1)
    if not p.weekends:
        day = _roll_to_business_day(day)
    return day


def normalize_to_trading_day(ts: datetime) -> date:
    """
    Backward-compatible helper with default policy.
    """
    return trading_day_from_timestamp(ts, TradingDayPolicy())
