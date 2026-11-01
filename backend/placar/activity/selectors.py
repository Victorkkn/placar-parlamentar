"""Read path for activity records (decision 0007: other apps read through these).

Returns plain values with their `SourceRef`s, so `metrics` stays free of ORM details.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from django.db.models import Exists, OuterRef

from placar.core.types import SourceRef

from .models import Ballot, Bill, Presence, Session, Speech, Voting


@dataclass(frozen=True)
class Item:
    key: str
    day: date | None
    source: SourceRef
    kind: str = ""


def held_sessions(house: str) -> list[Item]:
    rows = Session.objects.filter(house=house, situation="Encerrada")
    return [Item(r.natural_key, r.day, r.source, r.type_text) for r in rows]


def presence_keys(official_id: int) -> dict[str, SourceRef]:
    rows = Presence.objects.filter(official_id=official_id).select_related("session")
    return {r.session.natural_key: r.source for r in rows}


def nominal_votings(house: str) -> list[Item]:
    """Votings with individual votes recorded (nominal) and not secret."""
    rows = (
        Voting.objects.filter(house=house)
        .exclude(secret=True)
        .filter(Exists(Ballot.objects.filter(voting=OuterRef("pk"))))
    )
    return [Item(r.natural_key, r.day, r.source) for r in rows]


def ballots_of(official_id: int) -> dict[str, tuple[str, str, SourceRef]]:
    rows = Ballot.objects.filter(official_id=official_id).select_related("voting")
    return {r.voting.natural_key: (r.category, r.option_raw, r.source) for r in rows}


def bills_of(official_id: int) -> list[Item]:
    rows = Bill.objects.filter(authors=official_id)
    return [Item(r.natural_key, r.presented_on, r.source, r.type_code) for r in rows]


def speeches_of(official_id: int) -> list[Item]:
    rows = Speech.objects.filter(official_id=official_id)
    return [Item(r.natural_key, r.day, r.source, r.type_code) for r in rows]


def presence_keys_by_official(house: str) -> dict[int, dict[str, SourceRef]]:
    result: dict[int, dict[str, SourceRef]] = defaultdict(dict)
    rows = Presence.objects.filter(session__house=house).select_related("session")
    for r in rows:
        result[r.official_id][r.session.natural_key] = r.source
    return result


def ballots_by_official(house: str) -> dict[int, dict[str, tuple[str, str, SourceRef]]]:
    result: dict[int, dict[str, tuple[str, str, SourceRef]]] = defaultdict(dict)
    rows = Ballot.objects.filter(voting__house=house).select_related("voting")
    for r in rows:
        result[r.official_id][r.voting.natural_key] = (r.category, r.option_raw, r.source)
    return result


def bills_by_official(house: str) -> dict[int, list[Item]]:
    result: dict[int, list[Item]] = defaultdict(list)
    through = Bill.authors.through.objects.filter(bill__house=house).select_related("bill")
    for link in through:
        b = link.bill
        result[link.official_id].append(Item(b.natural_key, b.presented_on, b.source, b.type_code))
    return result


def speeches_by_official(house: str) -> dict[int, list[Item]]:
    result: dict[int, list[Item]] = defaultdict(list)
    for r in Speech.objects.filter(house=house):
        result[r.official_id].append(Item(r.natural_key, r.day, r.source, r.type_code))
    return result
