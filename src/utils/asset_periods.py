from __future__ import annotations

from datetime import datetime

from src.domain.time.utc import parse_iso_utc


def resolve_data_period(asset_cfg: dict) -> tuple[datetime, datetime]:
    period = asset_cfg.get("data_period")
    if not isinstance(period, dict):
        raise ValueError("Asset config must define data_period.start_date/end_date")
    start_raw = period.get("start_date")
    end_raw = period.get("end_date")
    if not start_raw or not end_raw:
        raise ValueError("Asset config must define data_period.start_date/end_date")
    start = parse_iso_utc(str(start_raw))
    end = parse_iso_utc(str(end_raw))
    if start > end:
        raise ValueError("data_period.start_date must be <= data_period.end_date")
    return start, end


def resolve_training_range(asset_cfg: dict) -> tuple[str, str] | None:
    period = asset_cfg.get("training_period")
    if not isinstance(period, dict):
        return None
    start_raw = period.get("start_date")
    end_raw = period.get("end_date")
    if not start_raw or not end_raw:
        return None
    start = parse_iso_utc(str(start_raw))
    end = parse_iso_utc(str(end_raw))
    if start > end:
        raise ValueError("training_period.start_date must be <= training_period.end_date")
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def resolve_training_split(asset_cfg: dict) -> dict[str, str] | None:
    period = asset_cfg.get("training_period")
    if not isinstance(period, dict):
        return None

    split_keys = (
        "train_start",
        "train_end",
        "val_start",
        "val_end",
        "test_start",
        "test_end",
    )
    if not all(period.get(k) for k in split_keys):
        return None

    out: dict[str, str] = {}
    for key in split_keys:
        dt = parse_iso_utc(str(period[key]))
        out[key] = dt.strftime("%Y%m%d")
    return out
