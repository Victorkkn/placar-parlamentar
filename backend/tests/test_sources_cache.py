import gzip
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from placar.sources.cache import (
    CachedFetcher,
    Freshness,
    RawCache,
    canonical_url,
    make_key,
    split_url,
)
from placar.sources.http import OfficialApiClient, Throttle, UpstreamError

BASE = "https://legis.senado.leg.br/dadosabertos/senador/4545/mandatos"


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


def make_fetcher(tmp_path, clock, **client_kwargs) -> CachedFetcher:
    client = OfficialApiClient(
        user_agent="test",
        throttle=Throttle(2.0, jitter_s=0.0, sleep=lambda s: None),
        sleep=lambda s: None,
        rand=lambda: 0.0,
        **client_kwargs,
    )
    cache = RawCache(tmp_path, ttl=timedelta(hours=24), clock=clock)
    return CachedFetcher("senado", client, cache)


def test_key_is_stable_and_order_independent():
    a = make_key("GET", "https://x.camara.leg.br/a", {"b": "2", "a": "1"})
    b = make_key("get", "https://x.camara.leg.br/a", {"a": "1", "b": "2"})
    assert a == b and len(a) == 64
    assert a != make_key("GET", "https://x.camara.leg.br/a", {"a": "1"})


def test_split_url_moves_query_into_params():
    url, params = split_url(
        "https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura=57&pagina=2",
        {"itens": 100},
    )
    assert url == "https://dadosabertos.camara.leg.br/api/v2/deputados"
    assert params == {"idLegislatura": "57", "pagina": "2", "itens": "100"}
    assert canonical_url(url, params).endswith("?idLegislatura=57&itens=100&pagina=2")


@respx.mock
def test_download_then_cache_hit(tmp_path):
    route = respx.get(BASE).mock(return_value=httpx.Response(200, json={"x": 1}))
    fetcher = make_fetcher(tmp_path, Clock())
    first = fetcher.get(BASE)
    second = fetcher.get(BASE)
    assert route.call_count == 1
    assert not first.from_cache and second.from_cache
    assert first.source == second.source
    assert first.source.api_url == BASE
    assert fetcher.stats.downloads == 1 and fetcher.stats.cache_hits == 1


@respx.mock
def test_envelope_contents_and_layout(tmp_path):
    body = {"MandatoParlamentar": {"Metadados": {"VersaoServico": "5"}, "Parlamentar": {}}}
    respx.get(BASE).mock(
        return_value=httpx.Response(
            200,
            json=body,
            headers={"set-cookie": "session=abc", "content-type": "application/json"},
        )
    )
    result = make_fetcher(tmp_path, Clock()).get(BASE, {"v": 5})
    path = (
        tmp_path
        / "senado"
        / "dadosabertos/senador/4545/mandatos"
        / f"{result.source.cache_key}.json.gz"
    )
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        envelope = json.load(handle)
    assert envelope["body"] == body
    assert envelope["params"] == {"v": "5"}
    assert envelope["api_version"] == "5"
    assert envelope["fetched_at"] == "2026-11-01T12:00:00+00:00"
    assert "set-cookie" not in json.dumps(envelope)
    assert "session=abc" not in json.dumps(envelope)


@respx.mock
def test_daily_entries_expire_after_ttl(tmp_path):
    route = respx.get(BASE).mock(return_value=httpx.Response(200, json={}))
    clock = Clock()
    fetcher = make_fetcher(tmp_path, clock)
    fetcher.get(BASE)
    clock.now += timedelta(hours=23)
    fetcher.get(BASE)
    assert route.call_count == 1
    clock.now += timedelta(hours=2)
    fetcher.get(BASE)
    assert route.call_count == 2


@respx.mock
def test_immutable_entries_never_expire(tmp_path):
    route = respx.get(BASE).mock(return_value=httpx.Response(200, json={}))
    clock = Clock()
    fetcher = make_fetcher(tmp_path, clock)
    fetcher.get(BASE, freshness=Freshness.IMMUTABLE)
    clock.now += timedelta(days=400)
    fetcher.get(BASE, freshness=Freshness.IMMUTABLE)
    assert route.call_count == 1


@respx.mock
def test_refresh_forces_download(tmp_path):
    route = respx.get(BASE).mock(return_value=httpx.Response(200, json={}))
    fetcher = make_fetcher(tmp_path, Clock())
    fetcher.get(BASE)
    fetcher.get(BASE, refresh=True)
    assert route.call_count == 2


@respx.mock
def test_stale_copy_used_when_api_fails(tmp_path):
    respx.get(BASE).mock(side_effect=[httpx.Response(200, json={"v": "old"}), httpx.Response(503)])
    clock = Clock()
    fetcher = make_fetcher(tmp_path, clock, max_retries=0)
    fetcher.get(BASE)
    clock.now += timedelta(days=2)
    result = fetcher.get(BASE)
    assert result.stale and result.body == {"v": "old"}
    assert result.fetched_at == datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
    assert fetcher.stats.stale_used == 1 and len(fetcher.stats.failures) == 1


@respx.mock
def test_failure_without_cache_raises(tmp_path):
    respx.get(BASE).mock(return_value=httpx.Response(503))
    fetcher = make_fetcher(tmp_path, Clock(), max_retries=0)
    with pytest.raises(UpstreamError):
        fetcher.get(BASE)
    assert fetcher.stats.failures


@respx.mock
def test_deprecations_are_collected(tmp_path):
    respx.get(BASE).mock(
        return_value=httpx.Response(200, json={}, headers={"sunset": "Sun, 01 Feb 2026"})
    )
    fetcher = make_fetcher(tmp_path, Clock())
    fetcher.get(BASE)
    assert list(fetcher.stats.deprecations.values()) == [{"sunset": "Sun, 01 Feb 2026"}]


def test_raw_cache_is_written_atomically(tmp_path):
    cache = RawCache(tmp_path, clock=Clock())
    from placar.sources.http import HttpResponse

    entry = cache.write("camara", BASE, {}, HttpResponse(BASE, 200, "application/json", {"a": 1}))
    assert entry.path.is_file()
    assert not list(entry.path.parent.glob("*.tmp"))
