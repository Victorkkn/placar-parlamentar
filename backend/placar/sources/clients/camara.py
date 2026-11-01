"""Câmara dos Deputados client and parsers.

Source: Câmara dos Deputados, Dados Abertos API v2.
OpenAPI spec: https://dadosabertos.camara.leg.br/api/v2/api-docs
Spec version: 0.4.347 (10/26/2026), checked 2026-11-01. Lists return 15 items by default, 100 max.

Endpoints used:
- GET /legislaturas?data={YYYY-MM-DD}
- GET /deputados?idLegislatura={n}&itens=100&pagina={p}   (follows rel="next" links)
- GET /deputados/{id}/historico

`/deputados/{id}` is not called: it returns personal fields outside the project's scope
(decision 0008 allowlist; Phase A plan).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from placar.core.types import SourceRef

from ..cache import CachedFetcher, Freshness
from ..http import NotOfficialURLError, is_official_url
from ._parse import dig, text, to_brazil_date, to_date, to_int

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
PAGE_SIZE = 100
MAX_PAGES = 50


@dataclass(frozen=True)
class CamaraLegislature:
    number: int
    start: date
    end: date
    source: SourceRef


@dataclass(frozen=True)
class CamaraDeputyRow:
    """One row of the deputies list. The list has one row per deputy and party (data issue 8)."""

    deputy_id: int
    name: str
    party: str | None
    state: str | None
    legislature: int | None
    source: SourceRef


@dataclass(frozen=True)
class CamaraHistoryEvent:
    deputy_id: int
    legislature: int | None
    event_date: date | None
    raw_datetime: str | None
    situation: str | None
    electoral_condition: str | None
    party: str | None
    state: str | None
    name: str | None
    electoral_name: str | None
    status_text: str | None
    source: SourceRef


@dataclass
class ParseNotes:
    """Things that could not be read as expected. Never filled in by guessing."""

    items: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.items.append(message)


def parse_legislatures(body: Any, source: SourceRef, notes: ParseNotes) -> list[CamaraLegislature]:
    result = []
    for item in dig(body, "dados") or []:
        number, start, end = (
            to_int(item.get("id")),
            to_date(item.get("dataInicio")),
            to_date(item.get("dataFim")),
        )
        if number is None or start is None or end is None:
            notes.add(f"camara legislature with missing fields: {item!r}")
            continue
        result.append(CamaraLegislature(number=number, start=start, end=end, source=source))
    return result


def parse_deputy_rows(body: Any, source: SourceRef, notes: ParseNotes) -> list[CamaraDeputyRow]:
    rows = []
    for item in dig(body, "dados") or []:
        deputy_id, name = to_int(item.get("id")), text(item.get("nome"))
        if deputy_id is None or name is None:
            notes.add(f"camara deputy row without id or name: {item.get('id')!r}")
            continue
        rows.append(
            CamaraDeputyRow(
                deputy_id=deputy_id,
                name=name,
                party=text(item.get("siglaPartido")),
                state=text(item.get("siglaUf")),
                legislature=to_int(item.get("idLegislatura")),
                source=source,
            )
        )
    return rows


def next_page_url(body: Any) -> str | None:
    for link in dig(body, "links") or []:
        if isinstance(link, dict) and link.get("rel") == "next":
            return text(link.get("href"))
    return None


def parse_history(
    deputy_id: int, body: Any, source: SourceRef, notes: ParseNotes
) -> list[CamaraHistoryEvent]:
    events = []
    for item in dig(body, "dados") or []:
        raw = text(item.get("dataHora"))
        event_date = to_brazil_date(raw)
        if event_date is None:
            notes.add(f"camara deputy {deputy_id}: history event without a valid date ({raw!r})")
        events.append(
            CamaraHistoryEvent(
                deputy_id=deputy_id,
                legislature=to_int(item.get("idLegislatura")),
                event_date=event_date,
                raw_datetime=raw,
                situation=text(item.get("situacao")),
                electoral_condition=text(item.get("condicaoEleitoral")),
                party=text(item.get("siglaPartido")),
                state=text(item.get("siglaUf")),
                name=text(item.get("nome")),
                electoral_name=text(item.get("nomeEleitoral")),
                status_text=text(item.get("descricaoStatus")),
                source=source,
            )
        )
    return events


class CamaraClient:
    def __init__(self, fetcher: CachedFetcher, *, refresh: bool = False) -> None:
        self.fetcher = fetcher
        self.refresh = refresh
        self.notes = ParseNotes()

    def legislature_on(self, day: date) -> CamaraLegislature:
        result = self.fetcher.get(
            f"{BASE_URL}/legislaturas", {"data": day.isoformat()}, refresh=self.refresh
        )
        found = parse_legislatures(result.body, result.source, self.notes)
        if len(found) != 1:
            raise ValueError(f"expected one Câmara legislature on {day}, got {len(found)}")
        return found[0]

    def deputies(self, legislature: int, freshness: Freshness) -> list[CamaraDeputyRow]:
        rows: list[CamaraDeputyRow] = []
        url: str | None = f"{BASE_URL}/deputados"
        params: dict[str, Any] | None = {
            "idLegislatura": legislature,
            "itens": PAGE_SIZE,
            "pagina": 1,
            "ordem": "ASC",
            "ordenarPor": "nome",
        }
        for _ in range(MAX_PAGES):
            if url is None:
                return rows
            if not is_official_url(url):
                raise NotOfficialURLError(url)
            result = self.fetcher.get(url, params, freshness=freshness, refresh=self.refresh)
            rows.extend(parse_deputy_rows(result.body, result.source, self.notes))
            url, params = next_page_url(result.body), None
        raise ValueError(f"Câmara deputies list has more than {MAX_PAGES} pages")

    def history(self, deputy_id: int, freshness: Freshness) -> list[CamaraHistoryEvent]:
        result = self.fetcher.get(
            f"{BASE_URL}/deputados/{deputy_id}/historico",
            freshness=freshness,
            refresh=self.refresh,
        )
        return parse_history(deputy_id, result.body, result.source, self.notes)
