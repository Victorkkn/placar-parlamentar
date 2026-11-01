"""HTTP access to the official APIs, with polite limits (decision 0012, section 4).

- At most `rate_per_sec` requests per second (capped at 2) and one request at a time per client.
- Small random delay (jitter) between requests.
- 429, 5xx, timeouts and connection errors are retried: `Retry-After` is honored, otherwise
  exponential backoff, up to `max_retries`. Then `UpstreamError` is raised.
- Only `https` URLs on official domains are requested; redirects are followed only to them.
- `Deprecation` / `Sunset` headers are reported so they can be logged as data issues.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

logger = logging.getLogger("placar.sources.http")

OFFICIAL_DOMAINS = ("camara.leg.br", "senado.leg.br")
MAX_RATE_PER_SEC = 2.0
MAX_REDIRECTS = 3
DEPRECATION_HEADERS = ("deprecation", "sunset", "link")


class UpstreamError(Exception):
    """The official API could not give a usable answer."""


class NotOfficialURLError(ValueError):
    """A URL is not https on an official domain."""


def is_official_url(url: str) -> bool:
    try:
        parsed = httpx.URL(url)
    except Exception:  # noqa: BLE001 - any parse failure means "not official"
        return False
    host = (parsed.host or "").lower()
    return parsed.scheme == "https" and any(
        host == domain or host.endswith("." + domain) for domain in OFFICIAL_DOMAINS
    )


def to_official_https(url: str | None) -> str | None:
    """Return the URL as https if it is on an official domain, else None.

    The Senado returns some links as `http://` (data issue 9); for official hosts only, the
    scheme is upgraded to https. Anything else is dropped.
    """
    if not url:
        return None
    candidate = url.strip()
    if candidate.startswith("http://"):
        candidate = "https://" + candidate[len("http://") :]
    return candidate if is_official_url(candidate) else None


def parse_retry_after(value: str | None, now: datetime | None = None) -> float | None:
    """Seconds to wait from a `Retry-After` header (seconds or HTTP date)."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except TypeError, ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, (when - (now or datetime.now(UTC))).total_seconds())


class Throttle:
    """Keeps at least `1 / rate` seconds (plus jitter) between consecutive requests."""

    def __init__(
        self,
        rate_per_sec: float,
        jitter_s: float = 0.25,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
    ) -> None:
        if rate_per_sec <= 0:
            raise ValueError("rate_per_sec must be positive")
        self.interval = 1.0 / min(rate_per_sec, MAX_RATE_PER_SEC)
        self.jitter_s = jitter_s
        self._clock = clock
        self._sleep = sleep
        self._rand = rand
        self._last: float | None = None

    def wait(self) -> None:
        if self._last is not None:
            ready_at = self._last + self.interval + self.jitter_s * self._rand()
            delay = ready_at - self._clock()
            if delay > 0:
                self._sleep(delay)
        self._last = self._clock()


@dataclass
class HttpResponse:
    url: str
    status: int
    content_type: str
    body: Any
    deprecation: dict[str, str] = field(default_factory=dict)


class OfficialApiClient:
    """GETs JSON from one official API, one request at a time."""

    def __init__(
        self,
        *,
        user_agent: str,
        rate_per_sec: float = MAX_RATE_PER_SEC,
        max_retries: int = 4,
        backoff_base_s: float = 2.0,
        max_wait_s: float = 120.0,
        timeout_s: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        throttle: Throttle | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
        on_deprecation: Callable[[str, dict[str, str]], None] | None = None,
    ) -> None:
        self._http = httpx.Client(
            timeout=timeout_s,
            headers={"User-Agent": user_agent, "Accept": "application/json"},
            follow_redirects=False,
            transport=transport,
        )
        self._throttle = throttle or Throttle(rate_per_sec, sleep=sleep, rand=rand)
        self._sleep = sleep
        self._rand = rand
        self.max_retries = max_retries
        self.backoff_base_s = backoff_base_s
        self.max_wait_s = max_wait_s
        self.on_deprecation = on_deprecation
        self.requests_sent = 0

    def close(self) -> None:
        self._http.close()

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> HttpResponse:
        if not is_official_url(url):
            raise NotOfficialURLError(url)
        attempt = 0
        redirects = 0
        while True:
            self._throttle.wait()
            self.requests_sent += 1
            retry_after: float | None = None
            try:
                response = self._http.get(url, params=params)
            except httpx.TransportError as exc:
                reason = f"{type(exc).__name__}"
            else:
                status = response.status_code
                if status in (301, 302, 303, 307, 308):
                    location = response.headers.get("location", "")
                    target = str(response.url.join(location))
                    if not is_official_url(target) or redirects >= MAX_REDIRECTS:
                        raise UpstreamError(f"redirect to non-official or too many: {target}")
                    redirects += 1
                    url, params = target, None
                    continue
                if status == 429 or status >= 500:
                    reason = f"HTTP {status}"
                    retry_after = parse_retry_after(response.headers.get("retry-after"))
                elif status >= 400:
                    raise UpstreamError(f"HTTP {status} for {response.url}")
                else:
                    return self._build(response)
            if attempt >= self.max_retries:
                raise UpstreamError(f"gave up after {attempt + 1} attempts ({reason}) for {url}")
            delay = retry_after
            if delay is None:
                delay = self.backoff_base_s * (2**attempt) + self._rand()
            delay = min(delay, self.max_wait_s)
            logger.warning("retrying %s in %.1fs (%s)", url, delay, reason)
            self._sleep(delay)
            attempt += 1

    def _build(self, response: httpx.Response) -> HttpResponse:
        content_type = response.headers.get("content-type", "")
        try:
            body = response.json()
        except ValueError as exc:
            raise UpstreamError(f"response is not JSON for {response.url}") from exc
        deprecation = {
            name: response.headers[name]
            for name in DEPRECATION_HEADERS
            if name in response.headers and (name != "link" or "deprecation" in response.headers)
        }
        if deprecation:
            logger.warning("deprecated service %s: %s", response.url, deprecation)
            if self.on_deprecation:
                self.on_deprecation(str(response.url), deprecation)
        return HttpResponse(
            url=str(response.url),
            status=response.status_code,
            content_type=content_type,
            body=body,
            deprecation=deprecation,
        )
