"""Write path for legislators data (decision 0007: only `sources` calls these).

Normalizers build a `HouseBundle` of plain records; `replace_house` stores it in one transaction.
The derived rows of that house are replaced as a whole, so re-running a normalization gives the
same database (idempotent). The raw cache, the source of truth, is never touched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from django.db import transaction

from placar.core.types import SourceRef

from .models import (
    DataLoad,
    House,
    Leave,
    Legislature,
    Mandate,
    Official,
    OfficialEvent,
    Party,
    PartyAffiliation,
    ServicePeriod,
)


def _source_fields(ref: SourceRef) -> dict[str, str]:
    return {
        "source_api_url": ref.api_url,
        "source_cache_file_id": ref.cache_key,
        "source_public_url": ref.public_url or "",
        "source_label": ref.label,
    }


@dataclass(frozen=True)
class LegislatureRecord:
    number: int
    start: date
    end: date
    source: SourceRef


@dataclass(frozen=True)
class PartyRecord:
    acronym: str
    name: str = ""
    camara_id: int | None = None
    senado_code: int | None = None


@dataclass(frozen=True)
class OfficialRecord:
    house_id: int
    parliamentary_name: str
    source: SourceRef
    civil_name: str = ""
    state: str = ""
    photo_url: str = ""
    page_url: str = ""


@dataclass(frozen=True)
class MandateRecord:
    natural_key: str
    official_id: int
    participation: str
    source: SourceRef
    participation_raw: str = ""
    alternate_rank: int | None = None
    external_code: int | None = None
    state: str = ""
    legislatures: tuple[int, ...] = ()
    nominal_start: date | None = None
    nominal_end: date | None = None
    titular_id: int | None = None


@dataclass(frozen=True)
class ServicePeriodRecord:
    natural_key: str
    official_id: int
    start: date
    end: date | None
    start_reason: str
    end_reason: str
    source: SourceRef
    mandate_key: str | None = None
    start_reason_raw: str = ""
    end_reason_raw: str = ""


@dataclass(frozen=True)
class LeaveRecord:
    natural_key: str
    official_id: int
    start: date
    end: date | None
    source: SourceRef
    type_code: str = ""
    type_text: str = ""


@dataclass(frozen=True)
class AffiliationRecord:
    natural_key: str
    official_id: int
    party_acronym: str
    start: date
    end: date | None
    precision: str
    source: SourceRef


@dataclass(frozen=True)
class EventRecord:
    natural_key: str
    official_id: int
    date: date | None
    kind: str
    source: SourceRef
    raw_datetime: str = ""
    legislature_number: int | None = None
    situation: str = ""
    electoral_condition: str = ""
    party_acronym: str = ""
    status_text: str = ""


@dataclass
class HouseBundle:
    """Everything normalized for one house. `*_id` fields are the house's own ids."""

    house: str
    legislatures: list[LegislatureRecord] = field(default_factory=list)
    parties: list[PartyRecord] = field(default_factory=list)
    officials: list[OfficialRecord] = field(default_factory=list)
    mandates: list[MandateRecord] = field(default_factory=list)
    periods: list[ServicePeriodRecord] = field(default_factory=list)
    leaves: list[LeaveRecord] = field(default_factory=list)
    affiliations: list[AffiliationRecord] = field(default_factory=list)
    events: list[EventRecord] = field(default_factory=list)


def _upsert_legislatures(records: list[LegislatureRecord]) -> dict[int, Legislature]:
    result = {}
    for rec in records:
        obj, _ = Legislature.objects.update_or_create(
            number=rec.number,
            defaults={"start": rec.start, "end": rec.end, **_source_fields(rec.source)},
        )
        result[rec.number] = obj
    return result


def _upsert_parties(records: list[PartyRecord]) -> dict[str, Party]:
    result: dict[str, Party] = {}
    for rec in records:
        party, _ = Party.objects.get_or_create(acronym=rec.acronym)
        changed = False
        for attr in ("name", "camara_id", "senado_code"):
            value = getattr(rec, attr)
            if value and not getattr(party, attr):
                setattr(party, attr, value)
                changed = True
        if changed:
            party.save()
        result[rec.acronym] = party
    return result


@transaction.atomic
def replace_house(bundle: HouseBundle) -> dict[str, int]:
    """Replace all derived rows for one house with the bundle's rows."""
    house = bundle.house
    if house not in House.values:
        raise ValueError(f"unknown house {house!r}")
    legislatures = _upsert_legislatures(bundle.legislatures)
    for number in {n for m in bundle.mandates for n in m.legislatures} - set(legislatures):
        existing = Legislature.objects.filter(number=number).first()
        if existing is None:
            raise ValueError(f"mandate refers to legislature {number}, which is not loaded")
        legislatures[number] = existing
    parties = _upsert_parties(bundle.parties)

    Official.objects.filter(house=house).delete()  # cascades to the house's derived rows
    officials = {
        rec.house_id: Official(
            house=house,
            house_id=rec.house_id,
            parliamentary_name=rec.parliamentary_name,
            civil_name=rec.civil_name,
            state=rec.state,
            photo_url=rec.photo_url,
            page_url=rec.page_url,
            **_source_fields(rec.source),
        )
        for rec in bundle.officials
    }
    Official.objects.bulk_create(officials.values())

    mandates = {}
    for rec in bundle.mandates:
        mandates[rec.natural_key] = Mandate(
            natural_key=rec.natural_key,
            official=officials[rec.official_id],
            house=house,
            external_code=rec.external_code,
            state=rec.state,
            participation=rec.participation,
            participation_raw=rec.participation_raw,
            alternate_rank=rec.alternate_rank,
            nominal_start=rec.nominal_start,
            nominal_end=rec.nominal_end,
            titular=officials.get(rec.titular_id) if rec.titular_id else None,
            **_source_fields(rec.source),
        )
    Mandate.objects.bulk_create(mandates.values())
    pairs = {
        (mandates[rec.natural_key].pk, legislatures[n].pk)
        for rec in bundle.mandates
        for n in rec.legislatures
    }
    links = [
        Mandate.legislatures.through(mandate_id=m, legislature_id=leg) for m, leg in sorted(pairs)
    ]
    Mandate.legislatures.through.objects.bulk_create(links)

    ServicePeriod.objects.bulk_create(
        ServicePeriod(
            natural_key=rec.natural_key,
            official=officials[rec.official_id],
            mandate=mandates.get(rec.mandate_key) if rec.mandate_key else None,
            start=rec.start,
            end=rec.end,
            start_reason=rec.start_reason,
            start_reason_raw=rec.start_reason_raw,
            end_reason=rec.end_reason,
            end_reason_raw=rec.end_reason_raw,
            **_source_fields(rec.source),
        )
        for rec in bundle.periods
    )
    Leave.objects.bulk_create(
        Leave(
            natural_key=rec.natural_key,
            official=officials[rec.official_id],
            start=rec.start,
            end=rec.end,
            type_code=rec.type_code,
            type_text=rec.type_text,
            **_source_fields(rec.source),
        )
        for rec in bundle.leaves
    )
    PartyAffiliation.objects.bulk_create(
        PartyAffiliation(
            natural_key=rec.natural_key,
            official=officials[rec.official_id],
            party=parties[rec.party_acronym],
            start=rec.start,
            end=rec.end,
            precision=rec.precision,
            **_source_fields(rec.source),
        )
        for rec in bundle.affiliations
    )
    OfficialEvent.objects.bulk_create(
        OfficialEvent(
            natural_key=rec.natural_key,
            official=officials[rec.official_id],
            date=rec.date,
            raw_datetime=rec.raw_datetime,
            legislature_number=rec.legislature_number,
            kind=rec.kind,
            situation=rec.situation,
            electoral_condition=rec.electoral_condition,
            party_acronym=rec.party_acronym,
            status_text=rec.status_text,
            **_source_fields(rec.source),
        )
        for rec in bundle.events
    )
    return {
        "officials": len(officials),
        "mandates": len(mandates),
        "periods": len(bundle.periods),
        "leaves": len(bundle.leaves),
        "affiliations": len(bundle.affiliations),
        "events": len(bundle.events),
    }


def record_load(house: str, kind: str, reference_date: date, fetched_until=None) -> DataLoad:
    return DataLoad.objects.create(
        house=house, kind=kind, reference_date=reference_date, data_fetched_until=fetched_until
    )
