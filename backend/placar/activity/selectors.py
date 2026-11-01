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


SOURCE_FIELDS = ("source_api_url", "source_cache_file_id", "source_public_url", "source_label")


class _Refs:
    """Builds one shared SourceRef per distinct source while reading many plain rows.

    Bulk reads use `values_list` instead of model instances: the Câmara has about 450,000
    ballots, and building model objects for them took over a minute.
    """

    def __init__(self) -> None:
        self._seen: dict[tuple, SourceRef] = {}

    def __call__(self, api_url: str, cache_key: str, public_url: str, label: str) -> SourceRef:
        key = (api_url, cache_key, public_url, label)
        ref = self._seen.get(key)
        if ref is None:
            ref = SourceRef(api_url=api_url, cache_key=cache_key,
                            public_url=public_url or None, label=label)  # fmt: skip
            self._seen[key] = ref
        return ref


def presence_keys_by_official(house: str) -> dict[int, dict[str, SourceRef]]:
    result: dict[int, dict[str, SourceRef]] = defaultdict(dict)
    ref = _Refs()
    rows = Presence.objects.filter(session__house=house).values_list(
        "official_id", "session__natural_key", *SOURCE_FIELDS
    )
    for official_id, key, *source in rows.iterator(chunk_size=20_000):
        result[official_id][key] = ref(*source)
    return result


def ballots_by_official(house: str) -> dict[int, dict[str, tuple[str, str, SourceRef]]]:
    result: dict[int, dict[str, tuple[str, str, SourceRef]]] = defaultdict(dict)
    ref = _Refs()
    rows = Ballot.objects.filter(voting__house=house).values_list(
        "official_id", "voting__natural_key", "category", "option_raw", *SOURCE_FIELDS
    )
    for official_id, key, category, option, *source in rows.iterator(chunk_size=20_000):
        result[official_id][key] = (category, option, ref(*source))
    return result


def bills_by_official(house: str) -> dict[int, list[Item]]:
    result: dict[int, list[Item]] = defaultdict(list)
    ref = _Refs()
    bill_fields = tuple(f"bill__{f}" for f in SOURCE_FIELDS)
    rows = Bill.authors.through.objects.filter(bill__house=house).values_list(
        "official_id", "bill__natural_key", "bill__presented_on", "bill__type_code", *bill_fields
    )
    for official_id, key, day, type_code, *source in rows.iterator(chunk_size=20_000):
        result[official_id].append(Item(key, day, ref(*source), type_code))
    return result


def speeches_by_official(house: str) -> dict[int, list[Item]]:
    result: dict[int, list[Item]] = defaultdict(list)
    ref = _Refs()
    rows = Speech.objects.filter(house=house).values_list(
        "official_id", "natural_key", "day", "type_code", *SOURCE_FIELDS
    )
    for official_id, key, day, type_code, *source in rows.iterator(chunk_size=20_000):
        result[official_id].append(Item(key, day, ref(*source), type_code))
    return result
