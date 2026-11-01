"""fetch_activity end to end on SYNTHETIC responses (decision 0011, item 6), fully offline."""

import io
import re

import httpx
import pytest
import respx
from django.core.management import call_command

from placar.sources import runner
from placar.sources.activity_runner import freshness_for
from placar.sources.http import OfficialApiClient, Throttle

CAMARA = "https://dadosabertos.camara.leg.br/api/v2"
SENADO = "https://legis.senado.leg.br/dadosabertos"


@pytest.fixture
def offline(tmp_path, monkeypatch, settings):
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


def mock_camara(ballots_status=200):
    respx.get(f"{CAMARA}/legislaturas").mock(return_value=httpx.Response(200, json={"dados": [
        {"id": 57, "dataInicio": "2023-02-01", "dataFim": "2027-01-31"}]}))  # fmt: skip
    respx.get(f"{CAMARA}/deputados").mock(return_value=httpx.Response(200, json={
        "dados": [{"id": 1, "nome": "A"}, {"id": 2, "nome": "B"}], "links": []}))  # fmt: skip
    respx.get(f"{CAMARA}/eventos").mock(return_value=httpx.Response(200, json={"dados": [
        {"id": 10, "dataHoraInicio": "2024-03-05T14:00", "situacao": "Encerrada", "descricaoTipo": "Sessão Deliberativa"},
        {"id": 11, "dataHoraInicio": "2024-03-06T14:00", "situacao": "Cancelada", "descricaoTipo": "Sessão Deliberativa"},
    ], "links": []}))  # fmt: skip
    respx.get(f"{CAMARA}/eventos/10/deputados").mock(return_value=httpx.Response(200, json={
        "dados": [{"id": 1, "email": "x@y"}]}))  # fmt: skip
    respx.get(f"{CAMARA}/votacoes").mock(return_value=httpx.Response(200, json={"dados": [
        {"id": "9-1", "data": "2024-03-05", "siglaOrgao": "PLEN"}], "links": []}))  # fmt: skip
    respx.get(f"{CAMARA}/votacoes/9-1/votos").mock(return_value=httpx.Response(ballots_status, json={
        "dados": [{"tipoVoto": "Sim", "deputado_": {"id": 1}}]}))  # fmt: skip
    respx.get(url__regex=re.escape(CAMARA) + r"/proposicoes.*").mock(return_value=httpx.Response(200, json={
        "dados": [{"id": 500, "siglaTipo": "PL", "numero": 1, "ano": 2024, "dataApresentacao": "2024-01-02T10:00"}], "links": []}))  # fmt: skip
    respx.get(url__regex=re.escape(CAMARA) + r"/deputados/\d+/orgaos.*").mock(
        return_value=httpx.Response(200, json={"dados": [], "links": []}))  # fmt: skip
    respx.get(url__regex=re.escape(CAMARA) + r"/deputados/\d+/discursos.*").mock(
        return_value=httpx.Response(200, json={"dados": [{"dataHoraInicio": "2024-03-05T15:00", "tipoDiscurso": "BREVES"}], "links": []}))  # fmt: skip


def mock_senado():
    respx.get(f"{SENADO}/plenario/legislatura/20261101").mock(return_value=httpx.Response(200, json={
        "ListaLegislatura": {"Legislaturas": {"Legislatura": {"NumeroLegislatura": "57", "DataInicio": "2023-02-01", "DataFim": "2027-01-31"}}}}))  # fmt: skip
    respx.get(f"{SENADO}/plenario/lista/tiposComparecimento").mock(return_value=httpx.Response(200, json={
        "ListaTiposComparecimento": {"TiposComparecimento": {"TipoComparecimento": [{"Sigla": "AP", "Descricao": "Atividade parlamentar"}]}}}))  # fmt: skip
    respx.get(f"{SENADO}/votacao").mock(return_value=httpx.Response(200, json=[
        {"codigoSessaoVotacao": 7, "dataSessao": "2024-03-05", "casaSessao": "SF", "votacaoSecreta": "N",
         "votos": [{"codigoParlamentar": 10, "siglaVotoParlamentar": "Sim"},
                   {"codigoParlamentar": 11, "siglaVotoParlamentar": "XYZ"}]}]))  # fmt: skip
    respx.get(f"{SENADO}/senador/lista/legislatura/57").mock(return_value=httpx.Response(200, json={
        "ListaParlamentarLegislatura": {"Parlamentares": {"Parlamentar": {"IdentificacaoParlamentar": {"CodigoParlamentar": "10"}}}}}))  # fmt: skip
    respx.get(f"{SENADO}/processo").mock(return_value=httpx.Response(200, json=[
        {"id": 1, "identificacao": "PL 1/2024", "dataApresentacao": "2024-01-02"}]))  # fmt: skip
    respx.get(f"{SENADO}/senador/10/comissoes").mock(return_value=httpx.Response(200, json={}))
    respx.get(url__regex=re.escape(SENADO) + r"/senador/10/discursos.*").mock(
        return_value=httpx.Response(200, json={})
    )


def run(*args):
    out = io.StringIO()
    call_command("fetch_activity", "--date", "2026-11-01", *args, stdout=out)
    return out.getvalue()


@respx.mock
def test_fetch_activity_both_houses_then_cache(offline):
    mock_camara()
    mock_senado()
    first = run()
    # The mocks answer every calendar year (2023–2026) with the same records: duplicates are
    # removed by id.
    assert "sessions_held: 1" in first and "presence_records: 1" in first
    assert "plenary_votings: 1" in first and "\n  ballots: 1\n" in first
    assert "bills: 2" in first and "speeches: 2" in first  # Câmara: deputies 1 and 2
    assert "\n  votings: 1\n" in first and "\n  ballots: 2\n" in first
    assert "senado vote options not in the official code table: ['XYZ']" in first
    calls = respx.calls.call_count
    second = run()
    assert respx.calls.call_count == calls
    assert second.count("requests sent: 0") == 2


@respx.mock
def test_ballot_failure_does_not_stop_the_run(offline):
    mock_camara(ballots_status=503)
    out = run("--house", "camara")
    assert "failures" in out and "/votacoes/9-1/votos" in out
    assert "deputies: 2" in out


def test_freshness_rule():
    from datetime import date

    pick = freshness_for(date(2026, 11, 1))
    assert pick(date(2025, 12, 31)).value == "immutable"
    assert pick(date(2026, 10, 20)).value == "daily"
