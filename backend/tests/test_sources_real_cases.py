"""Parsers on REAL recorded responses (decision 0011, items 7–10).

Fixtures are recorded by the project owner with `scripts/record_fixtures.py`. Until then these
tests are skipped, and the skip reason says so.
"""

from datetime import date
from pathlib import Path

import pytest

from placar.core.types import SourceRef
from placar.sources.clients import camara, senado
from placar.sources.clients.camara import ParseNotes
from placar.sources.fixtures import load_fixture

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load(relative: str):
    path = FIXTURES / relative
    if not path.exists():
        pytest.skip(f"fixture {relative} not recorded yet (run scripts/record_fixtures.py)")
    data = load_fixture(path)
    from placar.sources.cache import canonical_url

    ref = SourceRef(
        api_url=canonical_url(data["url"], data["params"]),
        cache_key=data["_fixture"]["cache_file_id"],
    )
    return data["body"], ref


def test_legislature_57_same_in_both_houses():
    notes = ParseNotes()
    body, ref = load("camara/legislaturas_2026-11-01.json")
    [cam] = camara.parse_legislatures(body, ref, notes)
    body, ref = load("senado/legislatura_20261101.json")
    [sen] = senado.parse_legislature(body, ref, notes)
    assert (cam.number, cam.start, cam.end) == (57, date(2023, 2, 1), date(2027, 1, 31))
    assert (sen.number, sen.start, sen.end) == (cam.number, cam.start, cam.end)


def test_camara_list_has_one_row_per_party():
    body, ref = load("camara/deputados_57_page1_sample.json")
    rows = camara.parse_deputy_rows(body, ref, ParseNotes())
    parties = {r.party for r in rows if r.deputy_id == 220714}
    assert len(parties) == 2  # data issue 8


def test_camara_220593_entry_and_vacancy():
    body, ref = load("camara/historico_220593.json")
    events = camara.parse_history(220593, body, ref, ParseNotes())
    texts = [(e.event_date, (e.status_text or "").split(" - ")[0]) for e in events]
    assert (date(2023, 2, 1), "Entrada") in texts
    assert (date(2025, 1, 1), "Saída") in texts
    assert all(e.source.api_url.endswith("/deputados/220593/historico") for e in events)


def test_senado_mandate_526_sequence():
    notes = ParseNotes()
    body, ref = load("senado/mandatos_4545.json")
    titular = next(
        m for m in senado.parse_mandates(4545, body, ref, notes) if m.mandate_code == 526
    )
    assert [(e.start, e.end, e.end_reason_code) for e in titular.exercises] == [
        (date(2019, 2, 1), date(2022, 11, 21), "LCS"),
        (date(2023, 9, 4), date(2023, 9, 4), "REN"),
    ]
    body, ref = load("senado/mandatos_5917.json")
    first_alt = next(
        m for m in senado.parse_mandates(5917, body, ref, notes) if m.mandate_code == 526
    )
    assert [(e.start, e.end) for e in first_alt.exercises] == [
        (date(2022, 12, 7), date(2023, 9, 4)),
        (date(2023, 9, 4), None),
    ]
    body, ref = load("senado/mandatos_5918.json")
    [second_alt] = senado.parse_mandates(5918, body, ref, notes)
    assert second_alt.exercises == ()  # never took office: expected, not missing data
    assert notes.items == []


def test_senado_4545_short_leaves_and_affiliations():
    body, ref = load("senado/licencas_4545.json")
    leaves = senado.parse_leaves(4545, body, ref, ParseNotes())
    assert any(lv.start == date(2022, 11, 21) for lv in leaves)
    body, ref = load("senado/filiacoes_4545.json")
    affiliations = senado.parse_affiliations(4545, body, ref, ParseNotes())
    assert {(a.party_acronym, a.start) for a in affiliations} >= {("MDB", date(2018, 5, 21))}


def test_senado_5917_party_switch():
    body, ref = load("senado/filiacoes_5917.json")
    affiliations = senado.parse_affiliations(5917, body, ref, ParseNotes())
    assert ("PSD", date(2026, 4, 2)) in {(a.party_acronym, a.start) for a in affiliations}


def test_senado_5918_has_no_leaves_or_affiliations():
    for name, parser in (
        ("licencas", senado.parse_leaves),
        ("filiacoes", senado.parse_affiliations),
    ):
        body, ref = load(f"senado/{name}_5918.json")
        assert parser(5918, body, ref, ParseNotes()) == []


def test_senado_lists_and_current():
    notes = ParseNotes()
    body, ref = load("senado/lista_legislatura_57_sample.json")
    assert {s.code for s in senado.parse_senator_list(body, ref, notes)} == {4545, 5917, 5918}
    body, ref = load("senado/lista_legislatura_57_exercicio_sample.json")
    assert {s.code for s in senado.parse_senator_list(body, ref, notes)} == {4545, 5917}
    body, ref = load("senado/lista_atual_sample.json")
    [current] = senado.parse_senator_list(body, ref, notes)
    assert current.code == 5917
    assert current.page_url is None or current.page_url.startswith("https://")
