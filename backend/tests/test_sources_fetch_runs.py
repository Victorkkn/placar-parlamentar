"""Fetch runs end to end on SYNTHETIC responses (decision 0011, item 6), fully offline."""

import io
from datetime import date

import httpx
import pytest
import respx
from django.core.management import call_command

from placar.sources import runner
from placar.sources.http import OfficialApiClient, Throttle

CAMARA = "https://dadosabertos.camara.leg.br/api/v2"
SENADO = "https://legis.senado.leg.br/dadosabertos"
LEG = {"NumeroLegislatura": "57", "DataInicio": "2023-02-01", "DataFim": "2027-01-31"}


def senator(code, participation="Titular"):
    return {
        "IdentificacaoParlamentar": {"CodigoParlamentar": str(code), "NomeParlamentar": f"S{code}"},
        "Mandatos": {"Mandato": {"CodigoMandato": "1", "DescricaoParticipacao": participation}},
    }


def mock_apis(*, legislature_end="2027-01-31", history_status=200):
    respx.get(f"{CAMARA}/legislaturas").mock(
        return_value=httpx.Response(
            200,
            json={"dados": [{"id": 57, "dataInicio": "2023-02-01", "dataFim": legislature_end}]},
        )
    )
    page2 = f"{CAMARA}/deputados?idLegislatura=57&pagina=2&itens=100"
    respx.get(f"{CAMARA}/deputados", params={"pagina": "1"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "dados": [
                    {"id": 1, "nome": "A", "siglaPartido": "P1"},
                    {"id": 1, "nome": "A", "siglaPartido": "P2"},
                ],
                "links": [{"rel": "next", "href": page2}],
            },
        )
    )
    respx.get(f"{CAMARA}/deputados", params={"pagina": "2"}).mock(
        return_value=httpx.Response(200, json={"dados": [{"id": 2, "nome": "B"}], "links": []})
    )
    respx.get(f"{CAMARA}/deputados/1/historico").mock(
        return_value=httpx.Response(200, json={"dados": [{"dataHora": "2023-02-01T12:05"}]})
    )
    respx.get(f"{CAMARA}/deputados/2/historico").mock(
        return_value=httpx.Response(history_status, json={"dados": []})
    )
    respx.get(f"{SENADO}/plenario/legislatura/20261101").mock(
        return_value=httpx.Response(
            200, json={"ListaLegislatura": {"Legislaturas": {"Legislatura": LEG}}}
        )
    )
    listed = {"ListaParlamentarLegislatura": {"Parlamentares": {"Parlamentar": [
        senator(10), senator(11, "1º Suplente"), senator(12, "2º Suplente")]}}}  # fmt: skip
    took = {"ListaParlamentarLegislatura": {"Parlamentares": {"Parlamentar": [
        senator(10), senator(11, "1º Suplente")]}}}  # fmt: skip
    respx.get(f"{SENADO}/senador/lista/legislatura/57", params={"exercicio": "S"}).mock(
        return_value=httpx.Response(200, json=took)
    )
    respx.get(f"{SENADO}/senador/lista/legislatura/57").mock(
        return_value=httpx.Response(200, json=listed)
    )
    respx.get(f"{SENADO}/senador/lista/atual").mock(
        return_value=httpx.Response(
            200,
            json={"ListaParlamentarEmExercicio": {"Parlamentares": {"Parlamentar": senator(11)}}},
        )
    )
    for code in (10, 11):
        mandate = {"Mandato": {"CodigoMandato": "1", "Exercicios": {"Exercicio": [
            {"DataInicio": "2023-02-01"}]}}}  # fmt: skip
        respx.get(f"{SENADO}/senador/{code}/mandatos").mock(
            return_value=httpx.Response(
                200, json={"MandatoParlamentar": {"Parlamentar": {"Mandatos": mandate}}}
            )
        )
        respx.get(f"{SENADO}/senador/{code}/licencas").mock(
            return_value=httpx.Response(200, json={"LicencaParlamentar": {"Parlamentar": {}}})
        )
        respx.get(f"{SENADO}/senador/{code}/filiacoes").mock(
            return_value=httpx.Response(200, json={"FiliacaoParlamentar": {"Parlamentar": {}}})
        )


@pytest.fixture
def offline_runner(tmp_path, monkeypatch, settings):
    settings.PLACAR = {**settings.PLACAR, "RAW_CACHE_DIR": tmp_path}
    monkeypatch.setattr(
        runner,
        "make_api_client",
        lambda: OfficialApiClient(
            user_agent="test",
            throttle=Throttle(2.0, jitter_s=0.0, sleep=lambda s: None),
            sleep=lambda s: None,
            rand=lambda: 0.0,
            max_retries=0,
        ),
    )
    return tmp_path


def run(*args) -> str:
    out = io.StringIO()
    call_command("fetch_current", "--date", "2026-11-01", *args, stdout=out)
    return out.getvalue()


@respx.mock
def test_fetch_current_downloads_then_uses_cache(offline_runner):
    mock_apis()
    first = run()
    assert "deputy_rows: 3" in first and "deputies: 2" in first
    assert "history_events: 1" in first
    assert "listed: 3" in first and "took_office: 2" in first and "in_office_today: 1" in first
    assert "exercises: 2" in first
    assert "data issue 8" in first
    assert list(offline_runner.glob("camara/**/*.json.gz"))
    assert list(offline_runner.glob("senado/**/*.json.gz"))

    calls_before = respx.calls.call_count
    second = run()
    assert respx.calls.call_count == calls_before
    assert second.count("requests sent: 0") == 2


@respx.mock
def test_refresh_downloads_again(offline_runner):
    mock_apis()
    run()
    calls_before = respx.calls.call_count
    run("--refresh")
    assert respx.calls.call_count > calls_before


@respx.mock
def test_limit_restricts_details(offline_runner):
    mock_apis()
    out = run("--limit", "1")
    assert "histories: 1" in out and "details_fetched: 1" in out


@respx.mock
def test_one_failure_does_not_stop_the_run(offline_runner):
    mock_apis(history_status=503)
    out = run()
    assert "failures" in out and "camara history 2" in out
    assert "took_office: 2" in out  # the Senado part still ran


@respx.mock
def test_houses_disagreeing_on_legislature_is_reported(offline_runner):
    mock_apis(legislature_end="2027-02-01")
    out = run()
    assert "legislature differs between houses" in out


def test_freshness_for_closed_legislature_is_immutable():
    assert runner._freshness(date(2023, 1, 31), date(2026, 11, 1)).value == "immutable"
    assert runner._freshness(date(2027, 1, 31), date(2026, 11, 1)).value == "daily"


def test_bad_date_option_is_rejected(offline_runner):
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("fetch_camara", "--date", "01/11/2026", stdout=io.StringIO())
