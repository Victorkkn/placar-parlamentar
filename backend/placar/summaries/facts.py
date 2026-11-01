"""Fact sheets: the only input to summaries (decision 0010, items 4-5). Functional core.

A fact holds display strings already formatted in pt-BR (see `formatting`) and the official
records it comes from. No free text from the APIs is used: only names, codes, dates and counts.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from placar.core.types import DateWindow, Period, SourceRef
from placar.metrics.activity import BILL_TYPES, MetricResult
from placar.metrics.coverage import CoverageResult

from . import formatting as fmt

HOUSE_NAMES = {"CAMARA": "Câmara dos Deputados", "SENADO": "Senado Federal"}

# Fact ids used by the template and given to the model.
OFFICIAL = "parlamentar"
COVERAGE = "tempo_no_cargo"
ATTENDANCE = "presenca_plenario"
BILLS = "proposicoes"
VOTES = "votacoes_nominais"
SPEECHES = "discursos"
METRIC_FACTS = {
    "plenary_attendance": ATTENDANCE,
    "bills_authored": BILLS,
    "vote_participation": VOTES,
    "speeches": SPEECHES,
}


@dataclass(frozen=True)
class Fact:
    id: str
    type: str
    values: Mapping[str, str]
    sources: tuple[SourceRef, ...]


@dataclass(frozen=True)
class OfficialInfo:
    id: int
    name: str
    house: str
    state: str
    source: SourceRef


@dataclass(frozen=True)
class PartySpell:
    party: str
    period: Period
    source: SourceRef


@dataclass(frozen=True)
class FactSheet:
    official_id: int
    window: DateWindow
    days_in_office: int
    facts: tuple[Fact, ...]

    def by_id(self) -> dict[str, Fact]:
        return {f.id: f for f in self.facts}

    def as_data(self) -> list[dict]:
        """What the model sees: ids, types and display values. No URLs, no visitor data."""
        return [{"id": f.id, "tipo": f.type, "valores": dict(f.values)} for f in self.facts]

    def digest(self) -> str:
        """Changes whenever a value or a source changes; marks stored summaries out of date."""
        payload = [
            [f.id, f.type, sorted(f.values.items()), sorted(s.api_url for s in f.sources)]
            for f in self.facts
        ]
        text = json.dumps([self.window.start.isoformat(), self.window.end.isoformat(), payload])
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clip(period: Period, window: DateWindow) -> Period | None:
    start = max(period.start, window.start)
    end = min(period.end or window.end, window.end)
    return Period(start, end) if start <= end else None


def build_fact_sheet(
    official: OfficialInfo,
    coverage: CoverageResult,
    parties: Sequence[PartySpell],
    metrics: Mapping[str, MetricResult | None],
) -> FactSheet:
    """`metrics` holds only metrics that are loaded; a None value means "not in official data"."""
    window = coverage.window
    facts = [
        Fact(
            OFFICIAL,
            "parlamentar",
            {"nome": official.name, "casa": HOUSE_NAMES[official.house], "uf": official.state},
            (official.source,),
        ),
        Fact(
            COVERAGE,
            "tempo_no_cargo",
            {
                "inicio_periodo": fmt.day(window.start),
                "fim_periodo": fmt.day(window.end),
                "dias_no_periodo": fmt.integer(window.days),
                "dias_no_cargo": fmt.integer(coverage.days_in_office),
                "proporcao": fmt.percent(coverage.share_exact),
            },
            # Zero days still comes from the official's records of time in office.
            coverage.sources or (official.source,),
        ),
    ]
    spells = [(s, _clip(s.period, window)) for s in parties]
    for n, (spell, clipped) in enumerate([x for x in spells if x[1] is not None], start=1):
        values = {
            "partido": spell.party,
            "inicio": fmt.day(clipped.start),
            "fim": fmt.day(clipped.end),
        }
        facts.append(Fact(f"partido_{n}", "filiacao_partidaria", values, (spell.source,)))
    days = coverage.days_in_office
    for key, fact_id in METRIC_FACTS.items():
        if key not in metrics or metrics[key] is None:
            continue
        facts.append(_metric_fact(fact_id, metrics[key], days))
    return FactSheet(official.id, window, days, tuple(facts))


def _per_365(numerator: int, days: int) -> dict[str, str]:
    if not days:
        return {}
    return {"por_365_dias_no_cargo": fmt.decimal(numerator * 365 / days), "base_dias": "365"}


def _metric_fact(fact_id: str, result: MetricResult, days: int) -> Fact:
    values: dict[str, str]
    details = result.details
    if fact_id == ATTENDANCE:
        values = {
            "sessoes_com_presenca": fmt.integer(result.numerator),
            "sessoes_nos_dias_no_cargo": fmt.integer(result.denominator or 0),
            "dias_de_licenca": fmt.integer(details.get("leave_days", 0)),
        }
    elif fact_id == VOTES:
        values = {
            "votacoes_com_voto": fmt.integer(result.numerator),
            "votacoes_nos_dias_no_cargo": fmt.integer(result.denominator or 0),
            "votacoes_presididas": fmt.integer(details.get("presided_excluded", 0)),
        }
    else:
        values = {"total": fmt.integer(result.numerator), **_per_365(result.numerator, days)}
        if fact_id == BILLS:
            # Bill types are named only through this fact, so "PL" the party is never assumed.
            values["tipos"] = ", ".join(t for t in ("PL", "PLP", "PEC", "PDL") if t in BILL_TYPES)
    if result.denominator:
        values["proporcao"] = fmt.percent(result.value)
    return Fact(fact_id, fact_id, values, result.sources)
