"""Normalizers on REAL fixtures, plus mapping-table checks (decision 0011)."""

from datetime import date
from pathlib import Path

import pytest

from placar.core.types import SourceRef
from placar.legislators.models import (
    DatePrecision,
    EndReason,
    EventKind,
    Participation,
    StartReason,
)
from placar.sources.cache import canonical_url
from placar.sources.clients import camara, senado
from placar.sources.clients.camara import ParseNotes
from placar.sources.fixtures import load_fixture
from placar.sources.normalize import camara as camara_norm
from placar.sources.normalize import senado as senado_norm
from placar.sources.normalize.camara_status_map import (
    ENTRY,
    ENTRY_DECISIONS,
    EXIT,
    EXIT_DECISIONS,
    read_status,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load(relative):
    data = load_fixture(FIXTURES / relative)
    ref = SourceRef(
        api_url=canonical_url(data["url"], data["params"]),
        cache_key=data["_fixture"]["cache_file_id"],
    )
    return data["body"], ref


def camara_bundle():
    notes = ParseNotes()
    [leg] = camara.parse_legislatures(*load("camara/legislaturas_2026-11-01.json"), notes)
    rows = camara.parse_deputy_rows(*load("camara/deputados_57_page1_sample.json"), notes)
    histories = {
        i: camara.parse_history(i, *load(f"camara/historico_{i}.json"), notes)
        for i in (220593, 220714)
    }
    return camara_norm.normalize(leg, rows, histories)


def senado_bundle():
    notes = ParseNotes()
    [leg] = senado.parse_legislature(*load("senado/legislatura_20261101.json"), notes)
    listed = senado.parse_senator_list(*load("senado/lista_legislatura_57_sample.json"), notes)
    current = senado.parse_senator_list(*load("senado/lista_atual_sample.json"), notes)
    codes = (4545, 5917, 5918)
    data = senado_norm.SenadoInput(
        legislature=leg,
        listed=listed,
        current=current,
        mandates={
            c: senado.parse_mandates(c, *load(f"senado/mandatos_{c}.json"), notes) for c in codes
        },
        leaves={
            c: senado.parse_leaves(c, *load(f"senado/licencas_{c}.json"), notes) for c in codes
        },
        affiliations={
            c: senado.parse_affiliations(c, *load(f"senado/filiacoes_{c}.json"), notes)
            for c in codes
        },
    )
    return senado_norm.normalize(data)


# --- Câmara mapping table ------------------------------------------------------------------


@pytest.mark.parametrize("text", list(ENTRY) + list(ENTRY_DECISIONS))
def test_every_entry_text_opens(text):
    assert read_status(text).kind == EventKind.ENTRY


@pytest.mark.parametrize("text", list(EXIT) + list(EXIT_DECISIONS))
def test_every_exit_text_closes(text):
    assert read_status(text).kind == EventKind.EXIT


def test_composite_and_other_texts():
    assert (
        read_status("Entrada - Reassunção / DIVERSO - Convocação Eleito ou Suplente").kind
        == EventKind.ENTRY
    )
    assert (
        read_status("Nome no início da legislatura / Partido no início da legislatura").kind
        == EventKind.START_OF_LEGISLATURE
    )
    assert read_status("Alteração de partido").kind == EventKind.PARTY
    assert read_status("Of. 29/2019").kind == EventKind.OTHER
    assert read_status("DIVERSO - Convocação Eleito ou Suplente").kind == EventKind.OTHER
    assert read_status(None).kind == EventKind.OTHER
    assert read_status("").kind == EventKind.OTHER  # fmt: skip


def test_unlisted_entry_or_exit_text_is_unknown_not_guessed():
    reading = read_status("Saída - Afastamento definitivo - Algo Novo")
    assert reading.kind == EventKind.UNKNOWN
    assert reading.unknown_part == "Saída - Afastamento definitivo - Algo Novo"
    assert (
        read_status("Entrada - Reassunção / Saída - Afastamento definitivo - Renúncia").kind
        == EventKind.UNKNOWN
    )


# --- Câmara normalizer on real fixtures ----------------------------------------------------


def test_camara_220593_one_period_ending_in_resignation():
    bundle, notes = camara_bundle()
    periods = [p for p in bundle.periods if p.official_id == 220593 and p.start.year >= 2023]
    assert [(p.start, p.end, p.end_reason) for p in periods] == [
        (date(2023, 2, 1), date(2025, 1, 1), EndReason.RESIGNATION)
    ]
    assert periods[0].start_reason == StartReason.ELECTED_OATH
    assert notes.unknown == [] and notes.inconsistencies == []
    assert all(p.source.api_url.endswith("/deputados/220593/historico") for p in periods)


def test_camara_220714_party_change_creates_affiliations():
    bundle, _ = camara_bundle()
    affs = [a for a in bundle.affiliations if a.official_id == 220714]
    parties = [a.party_acronym for a in affs]
    assert "REPUBLICANOS" in parties and "MDB" in parties
    assert all(a.precision == DatePrecision.AT_EVENT for a in affs)
    for earlier, later in zip(affs, affs[1:], strict=False):
        assert earlier.end is not None and earlier.end < later.start


def test_camara_fixture_events_all_mapped():
    bundle, _ = camara_bundle()
    assert bundle.events and all(e.kind != EventKind.UNKNOWN for e in bundle.events)


def test_camara_officials_from_rows():
    bundle, _ = camara_bundle()
    assert {o.house_id for o in bundle.officials} == {220593, 220714}


# --- Câmara normalizer on SYNTHETIC events (edge cases) --------------------------------------


def _event(day, text, situation="Exercício", party="P1"):
    ref = SourceRef(
        api_url="https://dadosabertos.camara.leg.br/api/v2/deputados/1/historico",
        cache_key="0" * 64,
    )
    return camara.CamaraHistoryEvent(
        deputy_id=1, legislature=57, event_date=day, raw_datetime=day.isoformat(),
        situation=situation, electoral_condition="Titular", party=party, state="SP",
        name="X", electoral_name="X", status_text=text, source=ref,
    )  # fmt: skip


def _synthetic(events):
    ref = SourceRef(api_url="https://dadosabertos.camara.leg.br/api/v2/x", cache_key="0" * 64)
    leg = camara.CamaraLegislature(57, date(2023, 2, 1), date(2027, 1, 31), ref)
    row = camara.CamaraDeputyRow(1, "X", "P1", "SP", 57, None, ref)
    return camara_norm.normalize(leg, [row], {1: events})


def test_leave_renewals_and_return():
    bundle, notes = _synthetic([
        _event(date(2023, 2, 1), "Entrada - Posse de Eleito Titular - Posse na Sessão Preparatória"),
        _event(date(2025, 6, 13), "Saída - Afastamento com prazo determinado - Licença para Tratamento de Saúde", "Licença"),
        _event(date(2025, 7, 10), "Saída - Afastamento com prazo determinado - Licença para Tratamento de Saúde", "Licença"),
        _event(date(2026, 7, 19), "Entrada - Reassunção"),
    ])  # fmt: skip
    assert [(p.start, p.end) for p in bundle.periods] == [
        (date(2023, 2, 1), date(2025, 6, 13)), (date(2026, 7, 19), None)
    ]  # fmt: skip
    assert [(lv.start, lv.end) for lv in bundle.leaves] == [(date(2025, 6, 14), date(2026, 7, 18))]
    assert notes.renewals == 1 and notes.inconsistencies == []


def test_recount_decision_closes_the_period():
    bundle, notes = _synthetic([
        _event(date(2023, 2, 1), "Entrada - Posse de Eleito Titular - Posse na Sessão Preparatória"),
        _event(date(2025, 7, 30), "DIVERSO - Decisão da Mesa - Afastamento de titular  por Recontagem de Votos", "SUPLENCIA"),
    ])  # fmt: skip
    assert [(p.end, p.end_reason) for p in bundle.periods] == [
        (date(2025, 7, 30), EndReason.RECOUNT)
    ]
    assert notes.inconsistencies == []


def test_unknown_text_is_logged_and_does_not_change_periods():
    bundle, notes = _synthetic([
        _event(date(2023, 2, 1), "Entrada - Posse de Eleito Titular - Posse na Sessão Preparatória"),
        _event(date(2024, 1, 1), "Saída - Algo Novo"),
    ])  # fmt: skip
    assert [(p.start, p.end) for p in bundle.periods] == [(date(2023, 2, 1), None)]
    assert len(notes.unknown) == 1 and "Saída - Algo Novo" in notes.unknown[0]


def test_open_period_with_alternate_status_is_flagged():
    _, notes = _synthetic([
        _event(date(2023, 2, 1), "Entrada - Posse de Eleito Titular - Posse na Sessão Preparatória"),
        _event(date(2024, 1, 1), "DIVERSO - Convocação Eleito ou Suplente", "SUPLENCIA"),
    ])  # fmt: skip
    assert len(notes.inconsistencies) == 1 and "SUPLENCIA" in notes.inconsistencies[0]


def test_same_day_party_correction_keeps_last_value():
    bundle, _ = _synthetic([
        _event(date(2023, 2, 1), "Nome no início da legislatura / Partido no início da legislatura", None, "P1"),
        _event(date(2023, 2, 1), "Alteração de partido", None, "P2"),
        _event(date(2024, 5, 1), "Alteração de partido", None, "P3"),
    ])  # fmt: skip
    assert [(a.party_acronym, a.start, a.end) for a in bundle.affiliations] == [
        ("P2", date(2023, 2, 1), date(2024, 4, 30)), ("P3", date(2024, 5, 1), None)
    ]  # fmt: skip


# --- Senado normalizer on real fixtures ----------------------------------------------------


def test_senado_mandate_526_periods_and_reasons():
    bundle, notes = senado_bundle()
    by = {}
    for p in bundle.periods:
        by.setdefault(p.official_id, []).append((p.start, p.end, p.end_reason))
    assert (date(2019, 2, 1), date(2022, 11, 21), EndReason.LEAVE) in by[4545]
    assert (date(2023, 9, 4), date(2023, 9, 4), EndReason.RESIGNATION) in by[4545]
    assert (date(2022, 12, 7), date(2023, 9, 4), EndReason.TITULAR_RETURNED) in by[5917]
    assert (date(2023, 9, 4), None, "") in by[5917]
    assert 5918 not in by
    assert notes.unknown == []


def test_senado_mandates_participation_and_titular():
    bundle, _ = senado_bundle()
    m = {(x.official_id, x.external_code): x for x in bundle.mandates}
    assert m[(4545, 526)].participation == Participation.TITULAR
    assert (m[(5917, 526)].participation, m[(5917, 526)].alternate_rank) == (
        Participation.ALTERNATE,
        1,
    )
    assert (m[(5918, 526)].participation, m[(5918, 526)].alternate_rank) == (
        Participation.ALTERNATE,
        2,
    )
    assert m[(5917, 526)].titular_id == 4545
    assert 57 in m[(4545, 526)].legislatures


def test_senado_leaves_and_affiliations_kept_separately():
    bundle, _ = senado_bundle()
    assert any(lv.official_id == 4545 and lv.start == date(2022, 11, 21) for lv in bundle.leaves)
    affs = {(a.official_id, a.party_acronym, a.start) for a in bundle.affiliations}
    assert (5917, "PSD", date(2026, 4, 2)) in affs
    assert all(a.precision == DatePrecision.EXACT for a in bundle.affiliations)


def test_senado_current_page_url_is_https():
    bundle, _ = senado_bundle()
    official = next(o for o in bundle.officials if o.house_id == 5917)
    assert official.page_url == "" or official.page_url.startswith("https://")


def test_senado_unknown_end_code_is_logged():
    notes = senado_norm.Notes()
    assert senado_norm._end_reason("XYZ", date(2024, 1, 1), "who", notes) == EndReason.UNKNOWN
    assert senado_norm._end_reason(None, date(2024, 1, 1), "who", notes) == EndReason.UNKNOWN
    assert senado_norm._end_reason(None, None, "who", notes) == ""
    assert len(notes.unknown) == 2
