"""Command wrappers on SYNTHETIC data, fully offline (decision 0011, item 6)."""

import io
import json
from datetime import UTC, datetime

import httpx
import pytest
import respx
from django.core.management import call_command
from django.core.management.base import CommandError

from placar.sources import runner
from placar.sources.cache import RawCache
from placar.sources.http import HttpResponse, OfficialApiClient, Throttle

URL = "https://legis.senado.leg.br/dadosabertos/senador/1/filiacoes"
BODY = {"FiliacaoParlamentar": {"Parlamentar": {"Codigo": "1", "EmailParlamentar": "x@y"}}}


@pytest.fixture
def offline(tmp_path, monkeypatch, settings):
    settings.PLACAR = {**settings.PLACAR, "RAW_CACHE_DIR": tmp_path / "raw"}
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
    manifest = tmp_path / "cases.json"
    manifest.write_text(
        json.dumps(
            {
                "spec": {"senado": "spec"},
                "cases": [{"name": "aff_1", "source": "senado", "url": URL, "file": "aff_1.json"}],
            }
        )
    )
    return tmp_path, manifest


def test_record_fixtures_from_cache(offline):
    tmp_path, manifest = offline
    RawCache(tmp_path / "raw", clock=lambda: datetime(2026, 11, 1, tzinfo=UTC)).write(
        "senado", URL, {}, HttpResponse(URL, 200, "application/json", BODY)
    )
    out = io.StringIO()
    call_command("record_fixtures", "--manifest", manifest, "--out", tmp_path / "fx", stdout=out)
    fixture = json.loads((tmp_path / "fx" / "aff_1.json").read_text())
    assert "EmailParlamentar" not in json.dumps(fixture["body"])
    assert "recorded 1 fixtures" in out.getvalue()


def test_record_fixtures_missing_cache_without_fetch_fails(offline):
    tmp_path, manifest = offline
    with pytest.raises(CommandError, match="not in the cache"):
        call_command(
            "record_fixtures",
            "--manifest",
            manifest,
            "--out",
            tmp_path / "fx",
            stdout=io.StringIO(),
        )


@respx.mock
def test_record_fixtures_with_fetch_downloads_missing(offline):
    tmp_path, manifest = offline
    respx.get(URL).mock(return_value=httpx.Response(200, json=BODY))
    out = io.StringIO()
    call_command(
        "record_fixtures", "--manifest", manifest, "--out", tmp_path / "fx", "--fetch", stdout=out
    )
    assert "(downloaded)" in out.getvalue()


@respx.mock
def test_check_upstream_reports_changes(offline):
    tmp_path, manifest = offline
    RawCache(tmp_path / "raw").write(
        "senado", URL, {}, HttpResponse(URL, 200, "application/json", BODY)
    )
    call_command(
        "record_fixtures", "--manifest", manifest, "--out", tmp_path / "fx", stdout=io.StringIO()
    )
    changed = {"FiliacaoParlamentar": {"Parlamentar": {"Codigo": "1", "Novo": "x"}}}
    respx.get(URL).mock(return_value=httpx.Response(200, json=changed))
    out = io.StringIO()
    call_command("check_upstream", "--fixtures", tmp_path / "fx", stdout=out)
    text = out.getvalue()
    assert "CHANGED" in text and "+ FiliacaoParlamentar.Parlamentar.Novo" in text
    assert "EmailParlamentar" not in text  # personal fields are not compared or printed


def test_check_upstream_without_fixtures(offline):
    tmp_path, _ = offline
    out = io.StringIO()
    call_command("check_upstream", "--fixtures", tmp_path / "none", stdout=out)
    assert "no fixtures found" in out.getvalue()
