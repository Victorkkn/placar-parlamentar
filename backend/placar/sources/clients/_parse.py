"""Small helpers for reading official JSON safely."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def dig(data: Any, *keys: str) -> Any:
    """Follow nested dict keys; return None if any step is missing."""
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def as_list(value: Any) -> list[Any]:
    """Senado JSON (converted from XML) gives one item as an object and many as a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def text(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def to_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except TypeError, ValueError:
        return None


def to_date(value: Any) -> date | None:
    """ISO date (YYYY-MM-DD); None if missing or invalid."""
    raw = text(value)
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def to_brazil_date(value: Any) -> date | None:
    """Calendar day in Brazil time (decision 0008).

    Timestamps without an offset are taken as Brazil local time, as the Câmara gives them.
    """
    raw = text(value)
    if raw is None:
        return None
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError:
        return to_date(raw)
    if moment.tzinfo is not None:
        moment = moment.astimezone(BRAZIL_TZ)
    return moment.date()
