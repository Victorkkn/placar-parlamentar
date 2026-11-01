"""Senado activity: votes, bills, committee memberships, speeches, vote code table (Phase B2).

Source: Senado Federal, Dados Abertos Legislativos.
Spec: https://legis.senado.leg.br/dadosabertos/v3/api-docs, version 4.1.3.108,
checked 2026-11-01 (B2.0 table in docs/plans/phase-b-data-model-and-metrics.md).
None of these services is deprecated.

Endpoints:
- GET /dadosabertos/votacao?dataInicio&dataFim             votes, with individual votes (≤ 1 year)
- GET /dadosabertos/processo?codigoParlamentarAutor        processes the senator is an author of
- GET /dadosabertos/senador/{codigo}/comissoes              body memberships
- GET /dadosabertos/senador/{codigo}/discursos?dataInicio&dataFim (AAAAMMDD, ≤ 1 year)
- GET /dadosabertos/plenario/lista/tiposComparecimento      official vote attendance codes

Kept fields follow decisions 0008 and 0010: no sex or e-mail; no speech text or summaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from placar.core.types import SourceRef

from ..cache import CachedFetcher, Freshness
from ._parse import as_list, dig, text, to_date, to_int
from .camara import ParseNotes
from .senado import BASE_URL

BILL_TYPES = ("PL", "PLP", "PEC", "PDL")  # decision 0014; B2.0 checked /processo/siglas


@dataclass(frozen=True)
class SenadoVoting:
    voting_code: int
    session_code: int | None
    day: date | None
    house: str | None
    description: str | None
    identification: str | None
    secret: bool | None
    process_id: int | None
    source: SourceRef


@dataclass(frozen=True)
class SenadoBallot:
    voting_code: int
    senator_code: int
    option: str | None
    option_text: str | None
    source: SourceRef


@dataclass(frozen=True)
class SenadoBill:
    process_id: int
    type_code: str | None
    number: int | None
    year: int | None
    identification: str | None
    presented_on: date | None
    summary: str | None
    author_code: int
    source: SourceRef


@dataclass(frozen=True)
class SenadoMembership:
    senator_code: int
    body_code: int | None
    body_acronym: str | None
    body_name: str | None
    body_house: str | None
    role: str | None
    start: date | None
    end: date | None
    source: SourceRef


@dataclass(frozen=True)
class SenadoSpeech:
    speech_code: int
    senator_code: int
    day: date | None
    type_code: str | None
    type_text: str | None
    house: str | None
    session_code: int | None
    source: SourceRef


def _identification(value: str | None) -> tuple[str | None, int | None, int | None]:
    """ "PL 123/2023" → ("PL", 123, 2023)."""
    if not value:
        return None, None, None
    parts = value.split()
    kind = parts[0] if parts else None
    number = year = None
    if len(parts) > 1 and "/" in parts[1]:
        n, y = parts[1].split("/", 1)
        number, year = to_int(n), to_int(y)
    return kind, number, year


def parse_votings(body: Any, source: SourceRef, notes: ParseNotes):
    votings, ballots = [], []
    for item in as_list(body):
        code = to_int(item.get("codigoSessaoVotacao"))
        if code is None:
            notes.add("senado voting without codigoSessaoVotacao")
            continue
        secret_flag = text(item.get("votacaoSecreta"))  # "S"/"N": secret ballot or not
        votings.append(
            SenadoVoting(
                voting_code=code,
                session_code=to_int(item.get("codigoSessao")),
                day=to_date(item.get("dataSessao")),
                house=text(item.get("casaSessao")),
                description=text(item.get("descricaoVotacao")),
                identification=text(item.get("identificacao")),
                secret=None if secret_flag is None else secret_flag == "S",  # noqa: S105 - not a password
                process_id=to_int(item.get("idProcesso")),
                source=source,
            )
        )
        for vote in as_list(item.get("votos")):
            senator = to_int(vote.get("codigoParlamentar"))
            if senator is None:
                notes.add(f"senado ballot in voting {code} without senator code")
                continue
            ballots.append(
                SenadoBallot(
                    voting_code=code,
                    senator_code=senator,
                    option=text(vote.get("siglaVotoParlamentar")),
                    option_text=text(vote.get("descricaoVotoParlamentar")),
                    source=source,
                )
            )
    return votings, ballots


def parse_bills(author_code: int, body: Any, source: SourceRef, notes: ParseNotes):
    result = []
    for item in as_list(body):
        process_id = to_int(item.get("id"))
        if process_id is None:
            notes.add(f"senado process without id (author {author_code})")
            continue
        kind, number, year = _identification(text(item.get("identificacao")))
        result.append(
            SenadoBill(
                process_id=process_id,
                type_code=kind,
                number=number,
                year=year,
                identification=text(item.get("identificacao")),
                presented_on=to_date(item.get("dataApresentacao")),
                summary=text(item.get("ementa")),
                author_code=author_code,
                source=source,
            )
        )
    return result


def parse_memberships(senator_code: int, body: Any, source: SourceRef, notes: ParseNotes):
    items = dig(body, "MembroComissaoParlamentar", "Parlamentar", "MembroComissoes", "Comissao")
    return [
        SenadoMembership(
            senator_code=senator_code,
            body_code=to_int(dig(item, "IdentificacaoComissao", "CodigoComissao")),
            body_acronym=text(dig(item, "IdentificacaoComissao", "SiglaComissao")),
            body_name=text(dig(item, "IdentificacaoComissao", "NomeComissao")),
            body_house=text(dig(item, "IdentificacaoComissao", "SiglaCasaComissao")),
            role=text(item.get("DescricaoParticipacao")),
            start=to_date(item.get("DataInicio")),
            end=to_date(item.get("DataFim")),
            source=source,
        )
        for item in as_list(items)
    ]


def parse_speeches(senator_code: int, body: Any, source: SourceRef, notes: ParseNotes):
    items = dig(body, "DiscursosParlamentar", "Parlamentar", "Pronunciamentos", "Pronunciamento")
    result = []
    for item in as_list(items):
        code = to_int(item.get("CodigoPronunciamento"))
        if code is None:
            notes.add(f"senado speech without code (senator {senator_code})")
            continue
        result.append(
            SenadoSpeech(
                speech_code=code,
                senator_code=senator_code,
                day=to_date(item.get("DataPronunciamento")),
                type_code=text(dig(item, "TipoUsoPalavra", "Sigla")),
                type_text=text(dig(item, "TipoUsoPalavra", "Descricao")),
                house=text(item.get("SiglaCasaPronunciamento")),
                session_code=to_int(dig(item, "SessaoPlenaria", "CodigoSessao")),
                source=source,
            )
        )
    return result


def parse_vote_codes(body: Any) -> dict[str, str]:
    items = dig(body, "ListaTiposComparecimento", "TiposComparecimento", "TipoComparecimento")
    return {
        code: description
        for code, description in (
            (text(i.get("Sigla")), text(i.get("Descricao"))) for i in as_list(items)
        )
        if code and description
    }


def year_ranges(start: date, end: date) -> list[tuple[date, date]]:
    """Calendar-year pieces, so each request covers at most one year."""
    return [
        (max(start, date(y, 1, 1)), min(end, date(y, 12, 31)))
        for y in range(start.year, end.year + 1)
    ]


class SenadoActivityClient:
    def __init__(self, fetcher: CachedFetcher, *, refresh: bool = False) -> None:
        self.fetcher = fetcher
        self.refresh = refresh
        self.notes = ParseNotes()

    def _get(self, path: str, params: dict[str, Any] | None, freshness: Freshness):
        return self.fetcher.get(
            f"{BASE_URL}{path}", params, freshness=freshness, refresh=self.refresh
        )

    def votings(self, start: date, end: date, freshness_for):
        votings, ballots = [], []
        for a, b in year_ranges(start, end):
            params = {"dataInicio": a.isoformat(), "dataFim": b.isoformat()}
            result = self._get("/votacao", params, freshness_for(b))
            v, bl = parse_votings(result.body, result.source, self.notes)
            votings += v
            ballots += bl
        return votings, ballots

    def bills(self, code: int, freshness: Freshness) -> list[SenadoBill]:
        result = self._get("/processo", {"codigoParlamentarAutor": code}, freshness)
        return parse_bills(code, result.body, result.source, self.notes)

    def memberships(self, code: int, freshness: Freshness) -> list[SenadoMembership]:
        result = self._get(f"/senador/{code}/comissoes", None, freshness)
        return parse_memberships(code, result.body, result.source, self.notes)

    def speeches(self, code: int, start: date, end: date, freshness_for):
        speeches = []
        for a, b in year_ranges(start, end):
            params = {"dataInicio": f"{a:%Y%m%d}", "dataFim": f"{b:%Y%m%d}"}
            result = self._get(f"/senador/{code}/discursos", params, freshness_for(b))
            speeches += parse_speeches(code, result.body, result.source, self.notes)
        return speeches

    def vote_codes(self) -> tuple[dict[str, str], SourceRef]:
        result = self._get("/plenario/lista/tiposComparecimento", None, Freshness.DAILY)
        return parse_vote_codes(result.body), result.source
