"""Câmara activity: plenary sessions and presence, votes, bills, committees, speeches (Phase B2).

Source: Câmara dos Deputados, Dados Abertos API v2.
Spec: https://dadosabertos.camara.leg.br/api/v2/api-docs, version 0.4.347,
checked 2026-11-01 (B2.0 table in docs/plans/phase-b-data-model-and-metrics.md).

Endpoints:
- GET /eventos?idOrgao=180&codTipoEvento=110&dataInicio&dataFim   plenary deliberative sessions
- GET /eventos/{id}/deputados                                      presence (who registered)
- GET /votacoes?idOrgao=180&dataInicio&dataFim                    plenary votes (per quarter)
- GET /votacoes/{id}/votos                                         individual votes (nominal only)
- GET /proposicoes?idDeputadoAutor&siglaTipo&ano                   bills (data issue 16)
- GET /deputados/{id}/orgaos?dataInicio&dataFim                    body memberships
- GET /deputados/{id}/discursos?idLegislatura                      speeches (metadata only)

Kept fields follow the decision 0008 allowlist (no e-mail) and decision 0010 (no speech text or
keywords).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from typing import Any

from placar.core.types import SourceRef

from ..cache import CachedFetcher, Freshness
from ..http import NotOfficialURLError, is_official_url
from ._parse import dig, text, to_brazil_date, to_int
from .camara import BASE_URL, MAX_PAGES, PAGE_SIZE, ParseNotes, next_page_url

PLENARY_ID = 180
DELIBERATIVE_SESSION = 110
BILL_TYPES = ("PL", "PLP", "PEC", "PDL")  # decision 0014


def _last_id(uri: Any) -> str | None:
    value = text(uri)
    return value.rstrip("/").rsplit("/", 1)[-1] if value else None


@dataclass(frozen=True)
class CamaraSession:
    event_id: int
    day: date | None
    type_text: str | None
    situation: str | None
    source: SourceRef


@dataclass(frozen=True)
class CamaraPresence:
    event_id: int
    deputy_id: int
    source: SourceRef


@dataclass(frozen=True)
class CamaraVoting:
    voting_id: str
    day: date | None
    body: str | None
    event_id: int | None
    description: str | None
    source: SourceRef


@dataclass(frozen=True)
class CamaraBallot:
    voting_id: str
    deputy_id: int
    option: str | None
    source: SourceRef


@dataclass(frozen=True)
class CamaraBill:
    bill_id: int
    type_code: str | None
    number: int | None
    year: int | None
    presented_on: date | None
    summary: str | None
    author_id: int
    source: SourceRef


@dataclass(frozen=True)
class CamaraMembership:
    deputy_id: int
    body_id: int | None
    body_acronym: str | None
    body_name: str | None
    role: str | None
    start: date | None
    end: date | None
    source: SourceRef


@dataclass(frozen=True)
class CamaraSpeech:
    key: str
    deputy_id: int
    day: date | None
    raw_datetime: str | None
    speech_type: str | None
    phase: str | None
    event_id: int | None
    source: SourceRef


def parse_sessions(body: Any, source: SourceRef, notes: ParseNotes) -> list[CamaraSession]:
    result = []
    for item in dig(body, "dados") or []:
        event_id = to_int(item.get("id"))
        if event_id is None:
            notes.add("camara session without id")
            continue
        result.append(
            CamaraSession(
                event_id=event_id,
                day=to_brazil_date(item.get("dataHoraInicio")),
                type_text=text(item.get("descricaoTipo")),
                situation=text(item.get("situacao")),
                source=source,
            )
        )
    return result


def parse_presence(event_id: int, body: Any, source: SourceRef, notes: ParseNotes):
    result = []
    for item in dig(body, "dados") or []:
        deputy_id = to_int(item.get("id"))
        if deputy_id is None:
            notes.add(f"camara presence in event {event_id} without deputy id")
            continue
        result.append(CamaraPresence(event_id=event_id, deputy_id=deputy_id, source=source))
    return result


def parse_votings(body: Any, source: SourceRef, notes: ParseNotes) -> list[CamaraVoting]:
    result = []
    for item in dig(body, "dados") or []:
        voting_id = text(item.get("id"))
        if voting_id is None:
            notes.add("camara voting without id")
            continue
        result.append(
            CamaraVoting(
                voting_id=voting_id,
                day=to_brazil_date(item.get("data")),
                body=text(item.get("siglaOrgao")),
                event_id=to_int(_last_id(item.get("uriEvento"))),
                description=text(item.get("descricao")),
                source=source,
            )
        )
    return result


def parse_ballots(voting_id: str, body: Any, source: SourceRef, notes: ParseNotes):
    result = []
    for item in dig(body, "dados") or []:
        deputy_id = to_int(dig(item, "deputado_", "id"))
        if deputy_id is None:
            notes.add(f"camara ballot in voting {voting_id} without deputy id")
            continue
        result.append(CamaraBallot(voting_id, deputy_id, text(item.get("tipoVoto")), source))
    return result


def parse_bills(author_id: int, body: Any, source: SourceRef, notes: ParseNotes):
    result = []
    for item in dig(body, "dados") or []:
        bill_id = to_int(item.get("id"))
        if bill_id is None:
            notes.add(f"camara bill without id (author {author_id})")
            continue
        result.append(
            CamaraBill(
                bill_id=bill_id,
                type_code=text(item.get("siglaTipo")),
                number=to_int(item.get("numero")),
                year=to_int(item.get("ano")),
                presented_on=to_brazil_date(item.get("dataApresentacao")),
                summary=text(item.get("ementa")),
                author_id=author_id,
                source=source,
            )
        )
    return result


def parse_memberships(deputy_id: int, body: Any, source: SourceRef, notes: ParseNotes):
    return [
        CamaraMembership(
            deputy_id=deputy_id,
            body_id=to_int(item.get("idOrgao")),
            body_acronym=text(item.get("siglaOrgao")),
            body_name=text(item.get("nomeOrgao")),
            role=text(item.get("titulo")),
            start=to_brazil_date(item.get("dataInicio")),
            end=to_brazil_date(item.get("dataFim")),
            source=source,
        )
        for item in dig(body, "dados") or []
    ]


def parse_speeches(deputy_id: int, body: Any, source: SourceRef, notes: ParseNotes):
    result = []
    for item in dig(body, "dados") or []:
        raw = text(item.get("dataHoraInicio"))
        speech_type = text(item.get("tipoDiscurso"))
        phase = text(dig(item, "faseEvento", "titulo"))
        # Speeches have no id in the API: the key is built from what identifies one.
        digest = hashlib.sha256(f"{deputy_id}|{raw}|{speech_type}|{phase}".encode()).hexdigest()
        result.append(
            CamaraSpeech(
                key=f"CAMARA:speech:{deputy_id}:{digest[:16]}",
                deputy_id=deputy_id,
                day=to_brazil_date(raw),
                raw_datetime=raw,
                speech_type=speech_type,
                phase=phase,
                event_id=to_int(_last_id(item.get("uriEvento"))),
                source=source,
            )
        )
    return result


def _quarter_ranges(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into calendar quarters. `/votacoes` rejects ranges over 3 months
    (data issue 16), although the spec only says "same calendar year"."""
    pieces = []
    for year in range(start.year, end.year + 1):
        for first_month in (1, 4, 7, 10):
            q_start = date(year, first_month, 1)
            q_end = date(year + 1, 1, 1) if first_month == 10 else date(year, first_month + 3, 1)
            q_end = date.fromordinal(q_end.toordinal() - 1)
            a, b = max(start, q_start), min(end, q_end)
            if a <= b:
                pieces.append((a, b))
    return pieces


def _year_ranges(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into calendar-year pieces (Câmara `/votacoes` rule)."""
    return [
        (max(start, date(y, 1, 1)), min(end, date(y, 12, 31)))
        for y in range(start.year, end.year + 1)
    ]


class CamaraActivityClient:
    def __init__(self, fetcher: CachedFetcher, *, refresh: bool = False) -> None:
        self.fetcher = fetcher
        self.refresh = refresh
        self.notes = ParseNotes()

    def _pages(self, url: str, params: dict[str, Any] | None, freshness: Freshness):
        for _ in range(MAX_PAGES):
            if url is None:
                return
            if not is_official_url(url):
                raise NotOfficialURLError(url)
            result = self.fetcher.get(url, params, freshness=freshness, refresh=self.refresh)
            yield result
            url, params = next_page_url(result.body), None
        raise ValueError(f"more than {MAX_PAGES} pages for {url}")

    def plenary_sessions(self, start: date, end: date, freshness_for) -> list[CamaraSession]:
        sessions = []
        for a, b in _year_ranges(start, end):
            params = {
                "idOrgao": PLENARY_ID,
                "codTipoEvento": DELIBERATIVE_SESSION,
                "dataInicio": a.isoformat(),
                "dataFim": b.isoformat(),
                "itens": PAGE_SIZE,
                "ordem": "ASC",
                "ordenarPor": "dataHoraInicio",
            }
            for result in self._pages(f"{BASE_URL}/eventos", params, freshness_for(b)):
                sessions += parse_sessions(result.body, result.source, self.notes)
        return sessions

    def presence(self, event_id: int, freshness: Freshness) -> list[CamaraPresence]:
        result = self.fetcher.get(
            f"{BASE_URL}/eventos/{event_id}/deputados", freshness=freshness, refresh=self.refresh
        )
        return parse_presence(event_id, result.body, result.source, self.notes)

    def plenary_votings(self, start: date, end: date, freshness_for) -> list[CamaraVoting]:
        votings = []
        for a, b in _quarter_ranges(start, end):
            params = {"idOrgao": PLENARY_ID, "dataInicio": a.isoformat(),
                      "dataFim": b.isoformat(), "itens": PAGE_SIZE, "ordem": "ASC",
                      "ordenarPor": "dataHoraRegistro"}  # fmt: skip
            for result in self._pages(f"{BASE_URL}/votacoes", params, freshness_for(b)):
                votings += parse_votings(result.body, result.source, self.notes)
        return votings

    def ballots(self, voting_id: str, freshness: Freshness) -> list[CamaraBallot]:
        result = self.fetcher.get(
            f"{BASE_URL}/votacoes/{voting_id}/votos", freshness=freshness, refresh=self.refresh
        )
        return parse_ballots(voting_id, result.body, result.source, self.notes)

    def bills(self, deputy_id: int, years: list[int], freshness: Freshness) -> list[CamaraBill]:
        params = {"idDeputadoAutor": deputy_id, "siglaTipo": ",".join(BILL_TYPES),
                  "ano": ",".join(str(y) for y in years), "itens": PAGE_SIZE,
                  "ordem": "ASC", "ordenarPor": "id"}  # fmt: skip
        bills = []
        for result in self._pages(f"{BASE_URL}/proposicoes", params, freshness):
            bills += parse_bills(deputy_id, result.body, result.source, self.notes)
        return bills

    def memberships(self, deputy_id: int, start: date, end: date, freshness: Freshness):
        params = {"dataInicio": start.isoformat(), "dataFim": end.isoformat(),
                  "itens": PAGE_SIZE, "ordem": "ASC", "ordenarPor": "idOrgao"}  # fmt: skip
        result_list = []
        for result in self._pages(f"{BASE_URL}/deputados/{deputy_id}/orgaos", params, freshness):
            result_list += parse_memberships(deputy_id, result.body, result.source, self.notes)
        return result_list

    def speeches(self, deputy_id: int, legislature: int, freshness: Freshness):
        params = {"idLegislatura": legislature, "itens": PAGE_SIZE, "ordem": "ASC",
                  "ordenarPor": "dataHoraInicio"}  # fmt: skip
        speeches = []
        url = f"{BASE_URL}/deputados/{deputy_id}/discursos"
        for result in self._pages(url, params, freshness):
            speeches += parse_speeches(deputy_id, result.body, result.source, self.notes)
        return speeches
