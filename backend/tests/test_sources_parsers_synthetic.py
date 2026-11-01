"""Parser edge cases on SYNTHETIC inputs shaped like the official responses.

These bodies are made up for testing (decision 0011, item 6) and are never shown in the app.
Tests on real recorded responses live in the fixture-based test modules.
"""

from datetime import date

from placar.core.types import SourceRef
from placar.sources.clients import camara, senado
from placar.sources.clients._parse import as_list, to_brazil_date
from placar.sources.clients.camara import ParseNotes

REF = SourceRef(api_url="https://legis.senado.leg.br/dadosabertos/x", cache_key="0" * 64)


def test_as_list_handles_single_object_and_missing():
    assert as_list(None) == []
    assert as_list({"a": 1}) == [{"a": 1}]
    assert as_list([1, 2]) == [1, 2]


def test_brazil_date_converts_offsets_and_keeps_local_times():
    assert to_brazil_date("2023-02-01T12:05") == date(2023, 2, 1)
    # 01:30 UTC on Feb 2 is still Feb 1 in Brasília (UTC-3).
    assert to_brazil_date("2023-02-02T01:30:00+00:00") == date(2023, 2, 1)
    assert to_brazil_date("not a date") is None


def test_camara_rows_keep_one_row_per_party_and_drop_unofficial_photos():
    body = {
        "dados": [
            {"id": 1, "nome": "Pessoa A", "siglaPartido": "P1", "siglaUf": "AM",
             "idLegislatura": 57, "urlFoto": "https://www.camara.leg.br/f/1.jpg",
             "email": "x@example.com"},
            {"id": 1, "nome": "Pessoa A", "siglaPartido": "P2", "siglaUf": "AM",
             "idLegislatura": 57, "urlFoto": "https://example.com/1.jpg"},
            {"nome": "Sem id"},
        ]
    }  # fmt: skip
    notes = ParseNotes()
    rows = camara.parse_deputy_rows(body, REF, notes)
    assert [(r.deputy_id, r.party) for r in rows] == [(1, "P1"), (1, "P2")]
    assert rows[1].photo_url is None
    assert not hasattr(rows[0], "email")
    assert len(notes.items) == 2


def test_camara_history_event_without_date_is_noted_not_guessed():
    body = {"dados": [{"dataHora": None, "situacao": "Exercício", "descricaoStatus": "Entrada"}]}
    notes = ParseNotes()
    events = camara.parse_history(9, body, REF, notes)
    assert events[0].event_date is None
    assert notes.items == ["camara deputy 9: history event without a valid date (None)"]


def test_camara_next_link():
    body = {"links": [{"rel": "self", "href": "a"}, {"rel": "next", "href": "b"}]}
    assert camara.next_page_url(body) == "b"
    assert camara.next_page_url({"links": [{"rel": "last", "href": "c"}]}) is None


def test_senado_single_mandate_and_single_exercise_objects():
    body = {
        "MandatoParlamentar": {
            "Parlamentar": {
                "Mandatos": {
                    "Mandato": {
                        "CodigoMandato": "1",
                        "UfParlamentar": "PE",
                        "DescricaoParticipacao": "Titular",
                        "PrimeiraLegislaturaDoMandato": {
                            "NumeroLegislatura": "57",
                            "DataInicio": "2023-02-01",
                            "DataFim": "2027-01-31",
                        },
                        "Suplentes": {"Suplente": {"CodigoParlamentar": "2"}},
                        "Exercicios": {
                            "Exercicio": {"CodigoExercicio": "9", "DataInicio": "2023-02-01"}
                        },
                    }
                }
            }
        }
    }
    notes = ParseNotes()
    [mandate] = senado.parse_mandates(1, body, REF, notes)
    assert mandate.alternate_codes == (2,)
    assert mandate.exercises[0].start == date(2023, 2, 1)
    assert mandate.exercises[0].end is None
    assert [s.number for s in mandate.legislatures] == [57]
    assert notes.items == []


def test_senado_exercises_are_sorted_and_missing_start_is_noted():
    body = {
        "MandatoParlamentar": {
            "Parlamentar": {
                "Mandatos": {
                    "Mandato": [
                        {
                            "CodigoMandato": "1",
                            "Exercicios": {
                                "Exercicio": [
                                    {"CodigoExercicio": "2", "DataInicio": "2024-01-01"},
                                    {"CodigoExercicio": "1", "DataInicio": "2023-01-01",
                                     "DataFim": "2023-06-30", "SiglaCausaAfastamento": "LCS"},
                                    {"CodigoExercicio": "3"},
                                ]
                            },
                        }
                    ]
                }
            }
        }
    }  # fmt: skip
    notes = ParseNotes()
    [mandate] = senado.parse_mandates(1, body, REF, notes)
    assert [e.code for e in mandate.exercises] == [3, 1, 2]
    assert notes.items == ["senado senator 1: Exercicio without start date"]


def test_senado_list_drops_personal_fields_and_upgrades_official_links():
    body = {
        "ListaParlamentarEmExercicio": {
            "Parlamentares": {
                "Parlamentar": {
                    "IdentificacaoParlamentar": {
                        "CodigoParlamentar": "7",
                        "NomeParlamentar": "Nome",
                        "NomeCompletoParlamentar": "Nome Completo",
                        "SexoParlamentar": "X",
                        "EmailParlamentar": "x@senado.leg.br",
                        "UrlFotoParlamentar": "http://www.senado.leg.br/f/7.jpg",
                        "UrlPaginaParlamentar": "http://example.com/7",
                    },
                    "Mandato": {"CodigoMandato": "5", "DescricaoParticipacao": "Titular"},
                }
            }
        }
    }
    notes = ParseNotes()
    [senator] = senado.parse_senator_list(body, REF, notes)
    assert senator.photo_url == "https://www.senado.leg.br/f/7.jpg"
    assert senator.page_url is None
    assert senator.mandates[0].mandate_code == 5
    fields = set(senado.SenadoListedSenator.__dataclass_fields__)
    assert not {"sex", "email", "phones"} & fields
    assert notes.items == ["senado senator 7: link not on an official domain, dropped"]


def test_senado_empty_leaves_and_affiliations():
    leaves = {"LicencaParlamentar": {"Parlamentar": {"Codigo": "5918"}}}
    affs = {"FiliacaoParlamentar": {"Parlamentar": {"Codigo": "5918"}}}
    notes = ParseNotes()
    assert senado.parse_leaves(5918, leaves, REF, notes) == []
    assert senado.parse_affiliations(5918, affs, REF, notes) == []
