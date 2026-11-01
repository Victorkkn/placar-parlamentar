"""Read path for legislators data (decision 0007: other apps read through these)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from placar.core.types import Period, SourceRef

from .models import DataLoad, Leave, Legislature, Official, PartyAffiliation, ServicePeriod


def get_official(house: str, house_id: int) -> Official:
    return Official.objects.get(house=house, house_id=house_id)


def service_periods_for(official_id: int) -> list[tuple[Period, SourceRef]]:
    rows = ServicePeriod.objects.filter(official_id=official_id).order_by("start")
    return [(Period(row.start, row.end), row.source) for row in rows]


def leaves_for(official_id: int) -> list[tuple[Period, SourceRef]]:
    return [
        (Period(r.start, r.end), r.source) for r in Leave.objects.filter(official_id=official_id)
    ]


def periods_by_official(house: str | None = None) -> dict[int, list[tuple[Period, SourceRef]]]:
    rows = ServicePeriod.objects.all()
    if house:
        rows = rows.filter(official__house=house)
    result: dict[int, list[tuple[Period, SourceRef]]] = defaultdict(list)
    for row in rows.order_by("official_id", "start"):
        result[row.official_id].append((Period(row.start, row.end), row.source))
    return result


def leaves_by_official(house: str | None = None) -> dict[int, list[tuple[Period, SourceRef]]]:
    rows = Leave.objects.all()
    if house:
        rows = rows.filter(official__house=house)
    result: dict[int, list[tuple[Period, SourceRef]]] = defaultdict(list)
    for row in rows:
        result[row.official_id].append((Period(row.start, row.end), row.source))
    return result


@dataclass(frozen=True)
class Affiliation:
    party: str
    period: Period
    precision: str
    source: SourceRef


def affiliations_by_official(house: str | None = None) -> dict[int, list[Affiliation]]:
    rows = PartyAffiliation.objects.select_related("party")
    if house:
        rows = rows.filter(official__house=house)
    result: dict[int, list[Affiliation]] = defaultdict(list)
    for row in rows.order_by("official_id", "start"):
        result[row.official_id].append(
            Affiliation(row.party.acronym, Period(row.start, row.end), row.precision, row.source)
        )
    return result


def officials(house: str | None = None):
    rows = Official.objects.all()
    return rows.filter(house=house) if house else rows


def official_by_id(pk: int) -> Official | None:
    return Official.objects.filter(pk=pk).first()


def legislature_on(day: date) -> Legislature | None:
    return Legislature.objects.filter(start__lte=day, end__gte=day).first()


def latest_loads() -> list[DataLoad]:
    seen, result = set(), []
    for load in DataLoad.objects.all():
        if (load.house, load.kind) not in seen:
            seen.add((load.house, load.kind))
            result.append(load)
    return result
