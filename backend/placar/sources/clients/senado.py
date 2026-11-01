"""Senado Federal client and parsers.

Source: Senado Federal, Dados Abertos Legislativos API.
OpenAPI spec: https://legis.senado.leg.br/dadosabertos/v3/api-docs
Spec version: 4.1.3.108, checked 2026-11-01. JSON via `Accept: application/json`.
Documented limit: more than 10 requests per second may get HTTP 429 (we use at most 2).

Endpoints used (none are deprecated):
- GET /dadosabertos/plenario/legislatura/{AAAAMMDD}              (ListaLegislatura v3)
- GET /dadosabertos/senador/lista/legislatura/{n}[?exercicio=S]  (ListaParlamentarLegislatura v4)
- GET /dadosabertos/senador/lista/atual                          (ListaParlamentarEmExercicio)
- GET /dadosabertos/senador/{codigo}/mandatos                    (MandatoParlamentar v5)
- GET /dadosabertos/senador/{codigo}/licencas                    (LicencaParlamentar v6)
- GET /dadosabertos/senador/{codigo}/filiacoes                   (FiliacaoParlamentar v5)

Fields kept follow the decision 0008 allowlist: no sex, e-mail, phones or other personal data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from placar.core.types import SourceRef

from ..cache import CachedFetcher, Freshness
from ..http import to_official_https
from ._parse import as_list, dig, text, to_date, to_int
from .camara import ParseNotes

BASE_URL = "https://legis.senado.leg.br/dadosabertos"


@dataclass(frozen=True)
class SenadoLegislature:
    number: int
    start: date
    end: date
    source: SourceRef


@dataclass(frozen=True)
class SenadoLegislatureSpan:
    number: int
    start: date | None
    end: date | None


@dataclass(frozen=True)
class SenadoListedMandate:
    mandate_code: int | None
    state: str | None
    participation: str | None
    legislatures: tuple[SenadoLegislatureSpan, ...]
    titular_code: int | None


@dataclass(frozen=True)
class SenadoListedSenator:
    code: int
    parliamentary_name: str | None
    party: str | None
    page_url: str | None
    mandates: tuple[SenadoListedMandate, ...]
    source: SourceRef


@dataclass(frozen=True)
class SenadoExercise:
    """A period in office (`Exercicio`); `end=None` means still in office."""

    code: int | None
    start: date | None
    end: date | None
    end_reason_code: str | None
    end_reason_text: str | None


@dataclass(frozen=True)
class SenadoMandate:
    senator_code: int
    mandate_code: int | None
    state: str | None
    participation: str | None
    legislatures: tuple[SenadoLegislatureSpan, ...]
    titular_code: int | None
    alternate_codes: tuple[int, ...]
    exercises: tuple[SenadoExercise, ...]
    source: SourceRef


@dataclass(frozen=True)
class SenadoLeave:
    senator_code: int
    code: int | None
    start: date | None
    end: date | None
    type_code: str | None
    type_text: str | None
    source: SourceRef


@dataclass(frozen=True)
class SenadoAffiliation:
    senator_code: int
    party_code: int | None
    party_acronym: str | None
    party_name: str | None
    start: date | None
    end: date | None
    source: SourceRef


def _spans(mandate: dict[str, Any]) -> tuple[SenadoLegislatureSpan, ...]:
    spans = []
    for key in ("PrimeiraLegislaturaDoMandato", "SegundaLegislaturaDoMandato"):
        leg = mandate.get(key)
        number = to_int(dig(leg, "NumeroLegislatura"))
        if number is not None:
            spans.append(
                SenadoLegislatureSpan(
                    number=number,
                    start=to_date(dig(leg, "DataInicio")),
                    end=to_date(dig(leg, "DataFim")),
                )
            )
    return tuple(spans)


def _listed_mandate(mandate: dict[str, Any]) -> SenadoListedMandate:
    return SenadoListedMandate(
        mandate_code=to_int(mandate.get("CodigoMandato")),
        state=text(mandate.get("UfParlamentar")),
        participation=text(mandate.get("DescricaoParticipacao")),
        legislatures=_spans(mandate),
        titular_code=to_int(dig(mandate, "Titular", "CodigoParlamentar")),
    )


def parse_legislature(body: Any, source: SourceRef, notes: ParseNotes) -> list[SenadoLegislature]:
    result = []
    for item in as_list(dig(body, "ListaLegislatura", "Legislaturas", "Legislatura")):
        number = to_int(item.get("NumeroLegislatura"))
        start, end = to_date(item.get("DataInicio")), to_date(item.get("DataFim"))
        if number is None or start is None or end is None:
            notes.add(f"senado legislature with missing fields: {item.get('NumeroLegislatura')!r}")
            continue
        result.append(SenadoLegislature(number=number, start=start, end=end, source=source))
    return result


def parse_senator_list(
    body: Any, source: SourceRef, notes: ParseNotes
) -> list[SenadoListedSenator]:
    """Reads both the legislature list and the current (`atual`) list."""
    wrapper = dig(body, "ListaParlamentarLegislatura") or dig(body, "ListaParlamentarEmExercicio")
    result = []
    for item in as_list(dig(wrapper, "Parlamentares", "Parlamentar")):
        ident = item.get("IdentificacaoParlamentar") or {}
        code = to_int(ident.get("CodigoParlamentar"))
        if code is None:
            notes.add("senado list item without CodigoParlamentar")
            continue
        mandates = as_list(dig(item, "Mandatos", "Mandato")) or as_list(item.get("Mandato"))
        # Decision 0019: no civil name or photo; only the official page link is kept.
        page_raw = ident.get("UrlPaginaParlamentar")
        page = to_official_https(page_raw)
        if page_raw and not page:
            notes.add(f"senado senator {code}: link not on an official domain, dropped")
        result.append(
            SenadoListedSenator(
                code=code,
                parliamentary_name=text(ident.get("NomeParlamentar")),
                party=text(ident.get("SiglaPartidoParlamentar")),
                page_url=page,
                mandates=tuple(_listed_mandate(m) for m in mandates if isinstance(m, dict)),
                source=source,
            )
        )
    return result


def parse_mandates(
    senator_code: int, body: Any, source: SourceRef, notes: ParseNotes
) -> list[SenadoMandate]:
    result = []
    for mandate in as_list(dig(body, "MandatoParlamentar", "Parlamentar", "Mandatos", "Mandato")):
        exercises = []
        for ex in as_list(dig(mandate, "Exercicios", "Exercicio")):
            start = to_date(ex.get("DataInicio"))
            if start is None:
                notes.add(f"senado senator {senator_code}: Exercicio without start date")
            exercises.append(
                SenadoExercise(
                    code=to_int(ex.get("CodigoExercicio")),
                    start=start,
                    end=to_date(ex.get("DataFim")),
                    end_reason_code=text(ex.get("SiglaCausaAfastamento")),
                    end_reason_text=text(ex.get("DescricaoCausaAfastamento")),
                )
            )
        alternates = tuple(
            code
            for code in (
                to_int(s.get("CodigoParlamentar"))
                for s in as_list(dig(mandate, "Suplentes", "Suplente"))
            )
            if code is not None
        )
        result.append(
            SenadoMandate(
                senator_code=senator_code,
                mandate_code=to_int(mandate.get("CodigoMandato")),
                state=text(mandate.get("UfParlamentar")),
                participation=text(mandate.get("DescricaoParticipacao")),
                legislatures=_spans(mandate),
                titular_code=to_int(dig(mandate, "Titular", "CodigoParlamentar")),
                alternate_codes=alternates,
                exercises=tuple(sorted(exercises, key=lambda e: e.start or date.min)),
                source=source,
            )
        )
    return result


def parse_leaves(
    senator_code: int, body: Any, source: SourceRef, notes: ParseNotes
) -> list[SenadoLeave]:
    result = []
    for item in as_list(dig(body, "LicencaParlamentar", "Parlamentar", "Licencas", "Licenca")):
        start = to_date(item.get("DataInicio"))
        if start is None:
            notes.add(f"senado senator {senator_code}: leave without start date")
        result.append(
            SenadoLeave(
                senator_code=senator_code,
                code=to_int(item.get("Codigo")),
                start=start,
                end=to_date(item.get("DataFim")),
                type_code=text(item.get("SiglaTipoAfastamento")),
                type_text=text(item.get("DescricaoTipoAfastamento")),
                source=source,
            )
        )
    return result


def parse_affiliations(
    senator_code: int, body: Any, source: SourceRef, notes: ParseNotes
) -> list[SenadoAffiliation]:
    result = []
    for item in as_list(dig(body, "FiliacaoParlamentar", "Parlamentar", "Filiacoes", "Filiacao")):
        start = to_date(item.get("DataFiliacao"))
        if start is None:
            notes.add(f"senado senator {senator_code}: affiliation without start date")
        result.append(
            SenadoAffiliation(
                senator_code=senator_code,
                party_code=to_int(dig(item, "Partido", "CodigoPartido")),
                party_acronym=text(dig(item, "Partido", "SiglaPartido")),
                party_name=text(dig(item, "Partido", "NomePartido")),
                start=start,
                end=to_date(item.get("DataDesfiliacao")),
                source=source,
            )
        )
    return result


class SenadoClient:
    def __init__(self, fetcher: CachedFetcher, *, refresh: bool = False) -> None:
        self.fetcher = fetcher
        self.refresh = refresh
        self.notes = ParseNotes()

    def _get(self, path: str, params: dict[str, Any] | None = None, *, freshness: Freshness):
        return self.fetcher.get(
            f"{BASE_URL}{path}", params, freshness=freshness, refresh=self.refresh
        )

    def legislature_on(self, day: date) -> SenadoLegislature:
        result = self._get(f"/plenario/legislatura/{day:%Y%m%d}", freshness=Freshness.DAILY)
        found = parse_legislature(result.body, result.source, self.notes)
        if len(found) != 1:
            raise ValueError(f"expected one Senado legislature on {day}, got {len(found)}")
        return found[0]

    def senators_in_legislature(
        self, number: int, freshness: Freshness, *, took_office_only: bool = False
    ) -> list[SenadoListedSenator]:
        params = {"exercicio": "S"} if took_office_only else None
        result = self._get(f"/senador/lista/legislatura/{number}", params, freshness=freshness)
        return parse_senator_list(result.body, result.source, self.notes)

    def current_senators(self) -> list[SenadoListedSenator]:
        result = self._get("/senador/lista/atual", freshness=Freshness.DAILY)
        return parse_senator_list(result.body, result.source, self.notes)

    def mandates(self, code: int, freshness: Freshness) -> list[SenadoMandate]:
        result = self._get(f"/senador/{code}/mandatos", freshness=freshness)
        return parse_mandates(code, result.body, result.source, self.notes)

    def leaves(self, code: int, freshness: Freshness) -> list[SenadoLeave]:
        result = self._get(f"/senador/{code}/licencas", freshness=freshness)
        return parse_leaves(code, result.body, result.source, self.notes)

    def affiliations(self, code: int, freshness: Freshness) -> list[SenadoAffiliation]:
        result = self._get(f"/senador/{code}/filiacoes", freshness=freshness)
        return parse_affiliations(code, result.body, result.source, self.notes)
