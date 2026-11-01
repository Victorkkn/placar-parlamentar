"""Read path for legislators data (decision 0007: other apps read through these)."""

from __future__ import annotations

from placar.core.types import Period, SourceRef

from .models import Official, ServicePeriod


def get_official(house: str, house_id: int) -> Official:
    return Official.objects.get(house=house, house_id=house_id)


def service_periods_for(official_id: int) -> list[tuple[Period, SourceRef]]:
    rows = ServicePeriod.objects.filter(official_id=official_id).order_by("start")
    return [(Period(row.start, row.end), row.source) for row in rows]
