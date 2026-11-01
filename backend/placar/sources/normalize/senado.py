"""Senado records → legislators bundle (decision 0008, rule 1; decision 0014, choice 1).

Pure functions: parsed Phase A records in, `HouseBundle` and notes out. No network, no database.
Time in office comes only from `Exercicios`; leaves are stored separately and do not cut it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from placar.legislators.models import (
    DatePrecision,
    EndReason,
    House,
    Participation,
    StartReason,
)
from placar.legislators.services import (
    AffiliationRecord,
    HouseBundle,
    LeaveRecord,
    LegislatureRecord,
    MandateRecord,
    OfficialRecord,
    PartyRecord,
    ServicePeriodRecord,
)

from ..clients.senado import (
    SenadoAffiliation,
    SenadoLeave,
    SenadoLegislature,
    SenadoListedSenator,
    SenadoMandate,
)

# Codes seen in the cache on 2026-11-01 (`SiglaCausaAfastamento`, trailing spaces removed).
END_REASONS: dict[str, str] = {
    "TER": EndReason.TERM_END,
    "REN": EndReason.RESIGNATION,
    "FAL": EndReason.DEATH,
    "CAS": EndReason.LOSS_OF_MANDATE,
    "LCS": EndReason.LEAVE,
    "LP": EndReason.LEAVE,
    "LS": EndReason.LEAVE,
    "RET": EndReason.TITULAR_RETURNED,
    "AFO": EndReason.OTHER_ABSENCE,
}


@dataclass
class Notes:
    unknown: list[str] = field(default_factory=list)
    inconsistencies: list[str] = field(default_factory=list)


@dataclass
class SenadoInput:
    legislature: SenadoLegislature
    listed: list[SenadoListedSenator]
    current: list[SenadoListedSenator]
    mandates: dict[int, list[SenadoMandate]]
    leaves: dict[int, list[SenadoLeave]]
    affiliations: dict[int, list[SenadoAffiliation]]


def _participation(raw: str | None) -> tuple[str, int | None]:
    if raw == "Titular":
        return Participation.TITULAR, None
    if raw and raw.endswith("Suplente"):
        rank = raw.split("º")[0].strip()
        return Participation.ALTERNATE, int(rank) if rank.isdigit() else None
    return Participation.UNKNOWN, None


def _end_reason(code: str | None, end: date | None, who: str, notes: Notes) -> str:
    if code is None:
        if end is None:
            return ""
        notes.unknown.append(f"{who}: period ends on {end} without a reason code")
        return EndReason.UNKNOWN
    reason = END_REASONS.get(code)
    if reason is None:
        notes.unknown.append(f"{who}: unmapped end reason code {code!r}")
        return EndReason.UNKNOWN
    return reason


def normalize(data: SenadoInput) -> tuple[HouseBundle, Notes]:
    notes = Notes()
    bundle = HouseBundle(house=House.SENADO)
    leg = data.legislature
    legislatures: dict[int, LegislatureRecord] = {
        leg.number: LegislatureRecord(leg.number, leg.start, leg.end, leg.source)
    }
    current = {s.code: s for s in data.current}
    listed = {s.code: s for s in data.listed}
    for s in data.current:
        listed.setdefault(s.code, s)

    for code in sorted(listed):
        senator, now = listed[code], current.get(code)
        state = next((m.state for m in senator.mandates if m.state), "") or ""
        bundle.officials.append(
            OfficialRecord(
                house_id=code,
                parliamentary_name=senator.parliamentary_name or str(code),
                civil_name=senator.civil_name or "",
                state=state,
                photo_url=(now.photo_url if now else senator.photo_url) or "",
                page_url=(now.page_url if now else senator.page_url) or "",
                source=senator.source,
            )
        )

    official_codes = set(listed)
    for code in sorted(listed):
        detailed = data.mandates.get(code)
        if detailed is None:
            _mandates_from_list(listed[code], official_codes, bundle)
            continue
        for mandate in detailed:
            _mandate_with_periods(code, mandate, official_codes, legislatures, bundle, notes)

    for code, leaves in sorted(data.leaves.items()):
        for leave in leaves:
            if leave.start is None:
                notes.inconsistencies.append(f"senado {code}: leave {leave.code} without start")
                continue
            bundle.leaves.append(
                LeaveRecord(
                    natural_key=f"SENADO:lic:{leave.code}" if leave.code else
                    f"SENADO:{code}:lic:{leave.start}",
                    official_id=code,
                    start=leave.start,
                    end=leave.end,
                    type_code=leave.type_code or "",
                    type_text=leave.type_text or "",
                    source=leave.source,
                )
            )  # fmt: skip

    parties: dict[str, PartyRecord] = {}
    for code, affiliations in sorted(data.affiliations.items()):
        for aff in affiliations:
            if aff.start is None or not aff.party_acronym:
                notes.inconsistencies.append(f"senado {code}: affiliation without start or party")
                continue
            parties.setdefault(
                aff.party_acronym,
                PartyRecord(aff.party_acronym, aff.party_name or "", senado_code=aff.party_code),
            )
            bundle.affiliations.append(
                AffiliationRecord(
                    natural_key=f"SENADO:{code}:{aff.party_acronym}:{aff.start}",
                    official_id=code,
                    party_acronym=aff.party_acronym,
                    start=aff.start,
                    end=aff.end,
                    precision=DatePrecision.EXACT,
                    source=aff.source,
                )
            )
    bundle.parties = list(parties.values())
    bundle.legislatures = [legislatures[n] for n in sorted(legislatures)]
    return bundle, notes


def _mandates_from_list(
    senator: SenadoListedSenator, official_codes: set[int], bundle: HouseBundle
) -> None:
    for m in senator.mandates:
        participation, rank = _participation(m.participation)
        bundle.mandates.append(
            MandateRecord(
                natural_key=f"SENADO:{m.mandate_code}:{senator.code}",
                official_id=senator.code,
                external_code=m.mandate_code,
                participation=participation,
                participation_raw=m.participation or "",
                alternate_rank=rank,
                state=m.state or "",
                legislatures=(),
                titular_id=m.titular_code if m.titular_code in official_codes else None,
                source=senator.source,
            )
        )


def _mandate_with_periods(
    code: int,
    mandate: SenadoMandate,
    official_codes: set[int],
    legislatures: dict[int, LegislatureRecord],
    bundle: HouseBundle,
    notes: Notes,
) -> None:
    for span in mandate.legislatures:
        if span.start and span.end:
            known = legislatures.get(span.number)
            if known is None:
                legislatures[span.number] = LegislatureRecord(
                    span.number, span.start, span.end, mandate.source
                )
            elif (known.start, known.end) != (span.start, span.end):
                notes.inconsistencies.append(
                    f"senado legislature {span.number}: dates differ between records "
                    f"({known.start}–{known.end} vs {span.start}–{span.end}); kept the first"
                )
    participation, rank = _participation(mandate.participation)
    numbers = [s.number for s in mandate.legislatures if s.start and s.end]
    if mandate.mandate_code is None or len(numbers) != len(set(numbers)):
        notes.inconsistencies.append(
            f"senado {code}: incomplete mandate record (code {mandate.mandate_code}, "
            f"participation {mandate.participation!r}, legislatures {numbers}); kept as given, "
            "repeated legislatures linked once (data issue 13)"
        )
    key = f"SENADO:{mandate.mandate_code}:{code}"
    starts = [s.start for s in mandate.legislatures if s.start]
    ends = [s.end for s in mandate.legislatures if s.end]
    bundle.mandates.append(
        MandateRecord(
            natural_key=key,
            official_id=code,
            external_code=mandate.mandate_code,
            participation=participation,
            participation_raw=mandate.participation or "",
            alternate_rank=rank,
            state=mandate.state or "",
            legislatures=tuple(sorted(set(numbers))),
            nominal_start=min(starts) if starts else None,
            nominal_end=max(ends) if ends else None,
            titular_id=mandate.titular_code if mandate.titular_code in official_codes else None,
            source=mandate.source,
        )
    )
    for ex in mandate.exercises:
        who = f"senado {code} mandate {mandate.mandate_code}"
        if ex.start is None:
            notes.inconsistencies.append(f"{who}: Exercicio {ex.code} without start; skipped")
            continue
        if ex.end is not None and ex.end < ex.start:
            notes.inconsistencies.append(f"{who}: Exercicio {ex.code} ends before it starts")
            continue
        bundle.periods.append(
            ServicePeriodRecord(
                natural_key=f"SENADO:ex:{ex.code}" if ex.code else f"SENADO:{code}:{ex.start}",
                official_id=code,
                mandate_key=key,
                start=ex.start,
                end=ex.end,
                start_reason=StartReason.NOT_GIVEN,
                end_reason=_end_reason(ex.end_reason_code, ex.end, who, notes),
                end_reason_raw=" / ".join(p for p in (ex.end_reason_code, ex.end_reason_text) if p),
                source=mandate.source,
            )
        )
