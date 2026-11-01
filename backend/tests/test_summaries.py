"""Summaries (Phase D): fact sheets, template, validator, fallback (decision 0010).

REAL officials from the fixtures + SYNTHETIC activity (decision 0011). The model is always a
fake: tests never call the real API.
"""

import io
from dataclasses import replace
from datetime import date

import pytest
from django.core.management import call_command

from placar.activity.services import replace_activity
from placar.core.types import DateWindow, SourceRef
from placar.legislators.selectors import get_official
from placar.legislators.services import record_load
from placar.summaries import formatting as fmt
from placar.summaries.facts import Fact, FactSheet
from placar.summaries.llm import base as llm_base
from placar.summaries.llm import configured_model
from placar.summaries.models import Summary
from placar.summaries.selectors import fact_sheet_for, summary_for
from placar.summaries.services import generate
from placar.summaries.template import template_summary
from placar.summaries.validator import MAX_CHARS, Sentence, validate
from placar.summaries.wording import banned_terms_in

from .builders import synthetic_camara_activity
from .test_legislators_db import load_both

SNAPSHOT = date(2026, 11, 1)
LEGISLATURE = DateWindow(date(2023, 2, 1), SNAPSHOT)
TWO_YEARS = DateWindow(date(2024, 11, 2), SNAPSHOT)
OLD = DateWindow(date(2019, 2, 1), date(2019, 12, 31))  # before most of the fixture mandates
REF = SourceRef(api_url="https://dadosabertos.camara.leg.br/api/v2/x", cache_key="0" * 64)


@pytest.fixture
def snapshot(db):
    load_both()
    replace_activity(synthetic_camara_activity())
    for house in ("CAMARA", "SENADO"):
        record_load(house, "people", SNAPSHOT)
    record_load("CAMARA", "activity", SNAPSHOT)


def deputy():
    return get_official("CAMARA", 220593).pk


def all_officials():
    from placar.legislators.models import Official

    return list(Official.objects.values_list("pk", flat=True))


class FakeModel:
    """Returns prepared drafts in order; an exception in the list is raised instead."""

    model_id = "fake-model"

    def __init__(self, *drafts):
        self.drafts = list(drafts)
        self.calls = 0

    def draft(self, sheet):
        self.calls += 1
        item = self.drafts.pop(0)
        if isinstance(item, Exception):
            raise item
        return item(sheet) if callable(item) else item


def good_draft(sheet):
    """A valid draft worded differently from the template."""
    who, cov = sheet.by_id()["parlamentar"].values, sheet.by_id()["tempo_no_cargo"].values
    return [
        Sentence(f"{who['nome']} esteve no cargo em {cov['dias_no_cargo']} dias.",
                 ("parlamentar", "tempo_no_cargo")),
        Sentence(f"O período analisado vai de {cov['inicio_periodo']} a {cov['fim_periodo']}.",
                 ("tempo_no_cargo",)),
    ]  # fmt: skip


# --- formatting and wording --------------------------------------------------------------------


def test_pt_br_formatting():
    assert fmt.integer(1370) == "1.370"
    assert fmt.decimal(3.26) == "3,3"
    assert fmt.decimal(1234.5) == "1.234,5"
    assert fmt.percent(0.823) == "82,3%"
    assert fmt.day(date(2023, 2, 1)) == "01/02/2023"


def test_banned_wording_ignores_case_and_accents_and_matches_whole_words():
    assert banned_terms_in("O MELHOR resultado") == ["melhor"]
    assert banned_terms_in("um deputado preguicoso") == ["preguiçoso"]
    assert banned_terms_in("melhoria na redação") == []


def test_single_wording_file_is_the_docs_file(settings):
    # Decision 0018: one list, shared with the frontend wording test.
    path = settings.PLACAR["BANNED_WORDING_FILE"]
    assert path.is_file() and path.parts[-3:] == ("docs", "wording", "banned-pt-BR.txt")


# --- fact sheet and template -------------------------------------------------------------------


def test_every_fact_has_a_source_or_is_covered_by_coverage(snapshot):
    sheet = fact_sheet_for(deputy(), LEGISLATURE, SNAPSHOT)
    ids = [f.id for f in sheet.facts]
    assert ids[:2] == ["parlamentar", "tempo_no_cargo"]
    assert {"presenca_plenario", "proposicoes", "votacoes_nominais", "discursos"} <= set(ids)
    by_id = sheet.by_id()
    assert by_id["parlamentar"].sources and by_id["tempo_no_cargo"].sources
    assert by_id["tempo_no_cargo"].values["dias_no_cargo"] == "701"


def test_fact_sheet_has_no_urls_or_free_text_for_the_model(snapshot):
    text = llm_base.user_message(fact_sheet_for(deputy(), LEGISLATURE, SNAPSHOT))
    assert "http" not in text  # sources stay on our side; only ids, codes, dates and counts


def test_senado_activity_not_loaded_gives_no_metric_facts(snapshot):
    sheet = fact_sheet_for(get_official("SENADO", 5917).pk, LEGISLATURE, SNAPSHOT)
    assert {f.type for f in sheet.facts} <= {"parlamentar", "tempo_no_cargo", "filiacao_partidaria"}


@pytest.mark.parametrize("window", [LEGISLATURE, TWO_YEARS, OLD])
def test_template_passes_validator_for_every_fixture_official(snapshot, window):
    for pk in all_officials():
        sheet = fact_sheet_for(pk, window, SNAPSHOT)
        sentences = template_summary(sheet)
        assert validate(sentences, sheet) == [], (pk, window)
        shown = summary_for(pk, window, SNAPSHOT)
        assert shown.kind == "template"
        assert all(s.sources for s in shown.sentences)  # every sentence maps to a SourceRef


def test_template_for_no_time_in_office(snapshot):
    sheet = fact_sheet_for(get_official("SENADO", 5918).pk, LEGISLATURE, SNAPSHOT)
    (only,) = template_summary(sheet)
    assert "não esteve no exercício do cargo" in only.text


def test_party_switch_is_listed_in_order(snapshot):
    sheet = fact_sheet_for(get_official("SENADO", 5917).pk, LEGISLATURE, SNAPSHOT)
    texts = [s.text for s in template_summary(sheet)]
    assert "Partidos no período, em ordem: MDB, PSD." in texts


# --- validator rules (one crafted bad draft per rule) ------------------------------------------


@pytest.fixture
def sheet(snapshot):
    return fact_sheet_for(deputy(), LEGISLATURE, SNAPSHOT)


def test_valid_model_style_draft_passes(sheet):
    assert validate(good_draft(sheet), sheet) == []


@pytest.mark.parametrize(
    ("text", "fact_ids", "problem"),
    [
        ("Esteve no cargo.", (), "cites no fact"),
        ("Esteve no cargo.", ("inventado",), "unknown fact ids"),
        ("Esteve no cargo em 9.999 dias.", ("tempo_no_cargo",), "'9.999'"),
        ("Esteve no cargo em 701 dias.", ("parlamentar",), "'701'"),  # number from an uncited fact
        ("Desde 05/10/1988 no cargo.", ("tempo_no_cargo",), "'05/10/1988'"),
        ("Fulano esteve no cargo.", ("tempo_no_cargo",), "name 'Fulano'"),
        ("Partido no período: XYZ.", ("tempo_no_cargo",), "name 'XYZ'"),
        ("Partido no período: PL.", ("tempo_no_cargo",), "name 'PL'"),  # party, not bill type
        ("Teve o melhor desempenho.", ("tempo_no_cargo",), "banned wording"),
        ("Esteve no cargo " + "a" * MAX_CHARS + ".", ("tempo_no_cargo",), "longer than"),
        ("   ", ("tempo_no_cargo",), "empty"),
    ],
)
def test_each_rule_rejects_a_bad_sentence(sheet, text, fact_ids, problem):
    draft = [*good_draft(sheet), Sentence(text, fact_ids)]
    problems = validate(draft, sheet)
    assert any(problem in p for p in problems), problems


def test_sentence_count_limits(sheet):
    assert any("sentence count" in p for p in validate([], sheet))
    seven = good_draft(sheet) * 4
    assert any("sentence count" in p for p in validate(seven[:7], sheet))


def test_sentence_needs_a_cited_fact_with_a_source():
    window = DateWindow(date(2023, 1, 1), date(2023, 12, 31))
    bare = FactSheet(1, window, 10, (Fact("sem_fonte", "x", {"total": "3"}, ()),))
    problems = validate([Sentence("Total: 3.", ("sem_fonte",))], bare)
    assert any("no official source" in p for p in problems)


def test_parse_draft_rejects_bad_format():
    for text in ["not json", '{"other": []}', '{"sentences": [{"text": "x"}]}']:
        with pytest.raises(llm_base.DraftError):
            llm_base.parse_draft(text)
    assert llm_base.parse_draft('{"sentences": [{"text": "a", "fact_ids": ["b"]}]}') == [
        Sentence("a", ("b",))
    ]


# --- generation, storage and fallback (fake model only) ---------------------------------------


def test_valid_model_summary_is_stored_and_shown(snapshot):
    model = FakeModel(good_draft)
    assert generate(deputy(), LEGISLATURE, model, SNAPSHOT) == "model"
    shown = summary_for(deputy(), LEGISLATURE, SNAPSHOT)
    assert shown.kind == "model" and len(shown.sentences) == 2
    assert all(s.sources for s in shown.sentences)
    # Same facts, model and prompt: no second paid call.
    assert generate(deputy(), LEGISLATURE, model, SNAPSHOT) == "up_to_date"
    assert model.calls == 1
    # Other windows (custom or the other preset) still use the template.
    assert summary_for(deputy(), TWO_YEARS, SNAPSHOT).kind == "template"


def test_error_then_valid_draft_uses_the_retry(snapshot):
    model = FakeModel(llm_base.DraftError("APITimeoutError"), good_draft)
    assert generate(deputy(), LEGISLATURE, model, SNAPSHOT) == "model"
    assert model.calls == 2


def test_two_bad_drafts_fall_back_to_the_template(snapshot):
    bad = [Sentence("Teve o melhor desempenho.", ("tempo_no_cargo",))]
    model = FakeModel(bad, llm_base.DraftError("stop_reason=refusal"))
    assert generate(deputy(), LEGISLATURE, model, SNAPSHOT) == "template_fallback"
    stored = Summary.objects.get()
    assert stored.passed is False and stored.sentences == []
    assert any("banned wording" in p for p in stored.problems)
    assert any("refusal" in p for p in stored.problems)
    assert summary_for(deputy(), LEGISLATURE, SNAPSHOT).kind == "template"


def test_no_time_in_office_makes_no_call(snapshot):
    model = FakeModel()
    assert generate(get_official("SENADO", 5918).pk, LEGISLATURE, model, SNAPSHOT) == (
        "no_time_in_office"
    )
    assert model.calls == 0


def test_out_of_date_or_tampered_summary_is_not_shown(snapshot):
    generate(deputy(), LEGISLATURE, FakeModel(good_draft), SNAPSHOT)
    stored = Summary.objects.get()
    stored.fact_sheet_hash = "0" * 64  # facts changed since generation
    stored.save()
    assert summary_for(deputy(), LEGISLATURE, SNAPSHOT).kind == "template"
    sheet = fact_sheet_for(deputy(), LEGISLATURE, SNAPSHOT)
    stored.fact_sheet_hash = sheet.digest()
    stored.sentences = [{"text": "Teve 12.345 votos.", "fact_ids": ["tempo_no_cargo"]}]
    stored.save()
    assert summary_for(deputy(), LEGISLATURE, SNAPSHOT).kind == "template"  # checked again


def test_digest_changes_with_values_and_sources(sheet):
    first = sheet.facts[0]
    changed = replace(sheet, facts=(replace(first, values={"nome": "Outro"}), *sheet.facts[1:]))
    resourced = replace(sheet, facts=(replace(first, sources=(REF,)), *sheet.facts[1:]))
    assert len({sheet.digest(), changed.digest(), resourced.digest()}) == 3


# --- model configuration and command ----------------------------------------------------------


def test_no_key_means_no_model(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert configured_model() is None
    monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")
    assert configured_model() is None


def run_command(*args):
    out = io.StringIO()
    call_command("generate_summaries", *args, stdout=out)
    return out.getvalue()


def test_command_without_key_does_nothing(snapshot, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert "template summaries" in run_command()
    assert not Summary.objects.exists()


def test_command_needs_yes_before_any_call(snapshot, monkeypatch):
    from placar.summaries.management.commands import generate_summaries as command

    model = FakeModel(*[good_draft] * 20)
    monkeypatch.setattr(command, "configured_model", lambda: model)
    out = run_command("--house", "CAMARA")
    assert "Nothing sent" in out and model.calls == 0
    out = run_command("--house", "CAMARA", "--yes")
    assert "model" in out and model.calls > 0
    assert Summary.objects.filter(passed=True).exists()
