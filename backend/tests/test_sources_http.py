from datetime import UTC, datetime

import httpx
import pytest
import respx

from placar.sources.http import (
    NotOfficialURLError,
    OfficialApiClient,
    Throttle,
    UpstreamError,
    is_official_url,
    parse_retry_after,
    to_official_https,
)

URL = "https://dadosabertos.camara.leg.br/api/v2/legislaturas"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(clock: FakeClock, **kwargs) -> OfficialApiClient:
    throttle = Throttle(2.0, jitter_s=0.0, clock=clock.clock, sleep=clock.sleep)
    return OfficialApiClient(
        user_agent="test-agent",
        throttle=throttle,
        sleep=clock.sleep,
        rand=lambda: 0.0,
        **kwargs,
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://dadosabertos.camara.leg.br/api/v2", True),
        ("https://legis.senado.leg.br/dadosabertos", True),
        ("https://senado.leg.br/x", True),
        ("http://legis.senado.leg.br/x", False),
        ("https://evil-senado.leg.br.example.com/x", False),
        ("https://notcamara.leg.br/x", False),
        ("javascript:alert(1)", False),
        ("", False),
    ],
)
def test_is_official_url(url, expected):
    assert is_official_url(url) is expected


def test_to_official_https_upgrades_only_official_hosts():
    assert (
        to_official_https("http://www.senado.leg.br/senadores/img/fotos-oficiais/senador5672.jpg")
        == "https://www.senado.leg.br/senadores/img/fotos-oficiais/senador5672.jpg"
    )
    assert to_official_https("http://example.com/x.jpg") is None
    assert to_official_https(None) is None


def test_parse_retry_after_seconds_and_date():
    now = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)
    assert parse_retry_after("30") == 30.0
    assert parse_retry_after("Sun, 01 Nov 2026 12:00:10 GMT", now=now) == 10.0
    assert parse_retry_after("garbage") is None
    assert parse_retry_after(None) is None


def test_throttle_keeps_two_requests_per_second():
    clock = FakeClock()
    throttle = Throttle(2.0, jitter_s=0.0, clock=clock.clock, sleep=clock.sleep)
    for _ in range(3):
        throttle.wait()
    assert clock.sleeps == [0.5, 0.5]


def test_throttle_never_exceeds_two_per_second():
    assert Throttle(10.0).interval == 0.5


@respx.mock
def test_get_json_success_sends_user_agent():
    route = respx.get(URL).mock(return_value=httpx.Response(200, json={"dados": []}))
    client = make_client(FakeClock())
    response = client.get_json(URL, params={"data": "2026-11-01"})
    assert response.body == {"dados": []}
    assert route.calls.last.request.headers["user-agent"] == "test-agent"
    assert route.calls.last.request.url.params["data"] == "2026-11-01"
    assert client.requests_sent == 1


@respx.mock
def test_retry_after_is_honored_on_504():
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(504, text="upstream request timeout", headers={"retry-after": "30"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    clock = FakeClock()
    client = make_client(clock)
    assert client.get_json(URL).body == {"ok": True}
    assert 30.0 in clock.sleeps
    assert client.requests_sent == 2


@respx.mock
def test_429_without_retry_after_uses_backoff():
    respx.get(URL).mock(
        side_effect=[httpx.Response(429), httpx.Response(429), httpx.Response(200, json={})]
    )
    clock = FakeClock()
    client = make_client(clock, backoff_base_s=2.0)
    client.get_json(URL)
    backoff = [s for s in clock.sleeps if s not in (0.5,)]
    assert backoff == [2.0, 4.0]


@respx.mock
def test_gives_up_after_max_retries():
    respx.get(URL).mock(return_value=httpx.Response(503))
    client = make_client(FakeClock(), max_retries=2)
    with pytest.raises(UpstreamError, match="gave up after 3 attempts"):
        client.get_json(URL)
    assert client.requests_sent == 3


@respx.mock
def test_retry_wait_is_capped():
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(503, headers={"retry-after": "9999"}),
            httpx.Response(200, json={}),
        ]
    )
    clock = FakeClock()
    make_client(clock, max_wait_s=60.0).get_json(URL)
    assert max(clock.sleeps) == 60.0


@respx.mock
def test_timeout_is_retried():
    respx.get(URL).mock(side_effect=[httpx.ReadTimeout("slow"), httpx.Response(200, json={})])
    client = make_client(FakeClock())
    client.get_json(URL)
    assert client.requests_sent == 2


@respx.mock
def test_client_errors_are_not_retried():
    respx.get(URL).mock(return_value=httpx.Response(404))
    client = make_client(FakeClock())
    with pytest.raises(UpstreamError, match="HTTP 404"):
        client.get_json(URL)
    assert client.requests_sent == 1


def test_non_official_url_is_refused_before_any_request():
    client = make_client(FakeClock())
    with pytest.raises(NotOfficialURLError):
        client.get_json("https://example.com/api")
    assert client.requests_sent == 0


@respx.mock
def test_redirect_followed_only_to_official_host():
    respx.get(URL).mock(
        return_value=httpx.Response(301, headers={"location": "https://example.com/x"})
    )
    with pytest.raises(UpstreamError, match="non-official"):
        make_client(FakeClock()).get_json(URL)


@respx.mock
def test_redirect_to_official_host_is_followed():
    target = "https://legis.senado.leg.br/dadosabertos/x"
    respx.get(URL).mock(return_value=httpx.Response(301, headers={"location": target}))
    respx.get(target).mock(return_value=httpx.Response(200, json={"moved": True}))
    assert make_client(FakeClock()).get_json(URL).body == {"moved": True}


@respx.mock
def test_non_json_body_is_an_error():
    respx.get(URL).mock(return_value=httpx.Response(200, text="<html>"))
    with pytest.raises(UpstreamError, match="not JSON"):
        make_client(FakeClock()).get_json(URL)


@respx.mock
def test_deprecation_headers_are_reported():
    headers = {
        "deprecation": "Mon, 10 Mar 2025 00:00:00 GMT",
        "sunset": "Sun, 01 Feb 2026 00:00:00 GMT",
        "link": "<https://legis.senado.leg.br/dadosabertos/new>; rel=successor",
    }
    respx.get(URL).mock(return_value=httpx.Response(200, json={}, headers=headers))
    seen = []
    client = make_client(FakeClock(), on_deprecation=lambda url, h: seen.append((url, h)))
    response = client.get_json(URL)
    assert set(response.deprecation) == {"deprecation", "sunset", "link"}
    assert seen and seen[0][1]["sunset"].startswith("Sun")
