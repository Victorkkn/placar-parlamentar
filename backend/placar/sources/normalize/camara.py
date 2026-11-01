"""Câmara records → legislators bundle (decision 0008, rules 2–4; decision 0014, choice 1).

Pure functions: parsed Phase A records in, `HouseBundle` and notes out. No network, no database.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from placar.legislators.models import DatePrecision, EndReason, EventKind, House, Participation
from placar.legislators.services import (
    AffiliationRecord,
    EventRecord,
    HouseBundle,
    LeaveRecord,
    LegislatureRecord,
    MandateRecord,
    OfficialRecord,
    PartyRecord,
    ServicePeriodRecord,
)

from ..clients.camara import CamaraDeputyRow, CamaraHistoryEvent, CamaraLegislature
from .camara_status_map import read_status

ONE_DAY = timedelta(days=1)


@dataclass
class Notes:
    unknown: list[str] = field(default_factory=list)
    inconsistencies: list[str] = field(default_factory=list)
    renewals: int = 0  # exits recorded while already out of office (leave or absence renewed)


def _participation(condition: str | None) -> str:
    return {"Titular": Participation.TITULAR, "Suplente": Participation.ALTERNATE}.get(
        condition or "", Participation.UNKNOWN
    )


def _official(rows: list[CamaraDeputyRow], events: list[CamaraHistoryEvent]) -> OfficialRecord:
    row = rows[0]
    state = next((r.state for r in rows if r.state), "") or ""
    return OfficialRecord(
        house_id=row.deputy_id,
        parliamentary_name=row.name,
        state=state,
        source=row.source,
    )


def _periods(
    deputy_id: int, events: list[CamaraHistoryEvent], readings: list, notes: Notes
) -> tuple[list[ServicePeriodRecord], list[LeaveRecord], list[MandateRecord]]:
    periods: list[ServicePeriodRecord] = []
    leaves: list[LeaveRecord] = []
    mandates: dict[str, MandateRecord] = {}
    open_entry: tuple[CamaraHistoryEvent, object] | None = None
    open_leave: tuple[CamaraHistoryEvent, object] | None = None

    for event, reading in zip(events, readings, strict=True):
        if event.event_date is None:
            continue
        if reading.kind == EventKind.ENTRY:
            if open_leave is not None:
                leave_event, leave_reading = open_leave
                end = event.event_date - ONE_DAY
                leaves.append(
                    LeaveRecord(
                        natural_key=f"CAMARA:{deputy_id}:leave:{leave_event.event_date}",
                        official_id=deputy_id,
                        start=leave_event.event_date + ONE_DAY,
                        end=max(end, leave_event.event_date + ONE_DAY),
                        type_code=EndReason.LEAVE,
                        type_text=leave_reading.matched_text,
                        source=leave_event.source,
                    )
                )
                open_leave = None
            if open_entry is not None:
                notes.inconsistencies.append(
                    f"camara {deputy_id}: entry on {event.event_date} while already in office "
                    f"since {open_entry[0].event_date}; kept the earlier entry"
                )
                continue
            open_entry = (event, reading)
        elif reading.kind == EventKind.EXIT:
            if open_entry is None:
                if periods:
                    notes.renewals += 1  # already out: the absence was renewed; no change
                else:
                    notes.inconsistencies.append(
                        f"camara {deputy_id}: exit on {event.event_date} "
                        f"({reading.matched_text}) before any entry in the records; ignored"
                    )
                continue
            entry, entry_reading = open_entry
            legislature = entry.legislature
            mandate_key = f"CAMARA:{legislature}:{deputy_id}"
            mandates.setdefault(mandate_key, _mandate(mandate_key, deputy_id, entry, legislature))
            periods.append(
                ServicePeriodRecord(
                    natural_key=f"CAMARA:{deputy_id}:{entry.event_date}",
                    official_id=deputy_id,
                    mandate_key=mandate_key,
                    start=entry.event_date,
                    end=event.event_date,
                    start_reason=entry_reading.start_reason,
                    start_reason_raw=entry_reading.matched_text,
                    end_reason=reading.end_reason,
                    end_reason_raw=reading.matched_text,
                    source=event.source,
                )
            )
            open_entry = None
            if reading.end_reason == EndReason.LEAVE:
                open_leave = (event, reading)
        elif reading.kind == EventKind.UNKNOWN:
            notes.unknown.append(
                f"camara {deputy_id}: unmapped history text on {event.event_date}: "
                f"{reading.unknown_part!r}"
            )

    if open_entry is not None:
        entry, entry_reading = open_entry
        mandate_key = f"CAMARA:{entry.legislature}:{deputy_id}"
        mandates.setdefault(mandate_key, _mandate(mandate_key, deputy_id, entry, entry.legislature))
        last_situation = next((e.situation for e in reversed(events) if e.situation), None)
        if last_situation != "Exercício":
            notes.inconsistencies.append(
                f"camara {deputy_id}: period open since {entry.event_date} but last situation "
                f"is {last_situation!r}; kept open"
            )
        periods.append(
            ServicePeriodRecord(
                natural_key=f"CAMARA:{deputy_id}:{entry.event_date}",
                official_id=deputy_id,
                mandate_key=mandate_key,
                start=entry.event_date,
                end=None,
                start_reason=entry_reading.start_reason,
                start_reason_raw=entry_reading.matched_text,
                end_reason="",
                source=entry.source,
            )
        )
    else:
        last = next((e for e in reversed(events) if e.situation), None)
        if last is not None and last.situation == "Exercício":
            notes.inconsistencies.append(
                f"camara {deputy_id}: last situation is 'Exercício' ({last.event_date}) but no "
                "period is open in the records"
            )
    if open_leave is not None:
        leave_event, leave_reading = open_leave
        leaves.append(
            LeaveRecord(
                natural_key=f"CAMARA:{deputy_id}:leave:{leave_event.event_date}",
                official_id=deputy_id,
                start=leave_event.event_date + ONE_DAY,
                end=None,
                type_code=EndReason.LEAVE,
                type_text=leave_reading.matched_text,
                source=leave_event.source,
            )
        )
    return periods, leaves, list(mandates.values())


def _mandate(key: str, deputy_id: int, entry: CamaraHistoryEvent, legislature: int | None):
    return MandateRecord(
        natural_key=key,
        official_id=deputy_id,
        participation=_participation(entry.electoral_condition),
        participation_raw=entry.electoral_condition or "",
        state=entry.state or "",
        legislatures=(legislature,) if legislature else (),
        source=entry.source,
    )


def _affiliations(deputy_id: int, events: list[CamaraHistoryEvent]) -> list[AffiliationRecord]:
    changes: list[tuple[date, str, CamaraHistoryEvent]] = []
    for event in events:
        if event.event_date is None or not event.party:
            continue
        if not changes or changes[-1][1] != event.party:
            if changes and changes[-1][0] == event.event_date:
                changes[-1] = (event.event_date, event.party, event)  # same-day correction
            else:
                changes.append((event.event_date, event.party, event))
    result = []
    for index, (start, party, event) in enumerate(changes):
        end = changes[index + 1][0] - ONE_DAY if index + 1 < len(changes) else None
        result.append(
            AffiliationRecord(
                natural_key=f"CAMARA:{deputy_id}:{party}:{start}",
                official_id=deputy_id,
                party_acronym=party,
                start=start,
                end=end,
                precision=DatePrecision.AT_EVENT,
                source=event.source,
            )
        )
    return result


def normalize(
    legislature: CamaraLegislature,
    rows: list[CamaraDeputyRow],
    histories: dict[int, list[CamaraHistoryEvent]],
) -> tuple[HouseBundle, Notes]:
    notes = Notes()
    bundle = HouseBundle(house=House.CAMARA)
    bundle.legislatures.append(
        LegislatureRecord(
            legislature.number, legislature.start, legislature.end, legislature.source
        )
    )
    by_id: dict[int, list[CamaraDeputyRow]] = defaultdict(list)
    for row in rows:
        by_id[row.deputy_id].append(row)

    parties: set[str] = set()
    for deputy_id in sorted(by_id):
        events = sorted(
            histories.get(deputy_id, []),
            key=lambda e: (e.event_date or date.min, e.raw_datetime or ""),
        )
        readings = [read_status(e.status_text) for e in events]
        bundle.officials.append(_official(by_id[deputy_id], events))
        periods, leaves, mandates = _periods(deputy_id, events, readings, notes)
        bundle.periods += periods
        bundle.leaves += leaves
        bundle.mandates += mandates
        affiliations = _affiliations(deputy_id, events)
        bundle.affiliations += affiliations
        parties |= {a.party_acronym for a in affiliations}
        for index, (event, reading) in enumerate(zip(events, readings, strict=True)):
            bundle.events.append(
                EventRecord(
                    natural_key=f"CAMARA:{deputy_id}:ev:{index}",
                    official_id=deputy_id,
                    date=event.event_date,
                    kind=reading.kind,
                    raw_datetime=event.raw_datetime or "",
                    legislature_number=event.legislature,
                    situation=event.situation or "",
                    electoral_condition=event.electoral_condition or "",
                    party_acronym=event.party or "",
                    status_text=(event.status_text or "")[:500],
                    source=event.source,
                )
            )
    bundle.parties = [PartyRecord(acronym=p) for p in sorted(parties)]
    _drop_unknown_legislatures(bundle, {legislature.number})
    return bundle, notes


def _drop_unknown_legislatures(bundle: HouseBundle, known: set[int]) -> None:
    """Mandates may point to past legislatures without a Câmara legislature record in Phase A;
    the mandate is kept, the link is dropped. The legislature number stays on its events."""
    fixed = []
    for mandate in bundle.mandates:
        missing = [n for n in mandate.legislatures if n not in known]
        if missing:
            fixed.append(
                MandateRecord(
                    **{
                        **mandate.__dict__,
                        "legislatures": tuple(n for n in mandate.legislatures if n in known),
                    }
                )  # fmt: skip
            )
        else:
            fixed.append(mandate)
    bundle.mandates = fixed
