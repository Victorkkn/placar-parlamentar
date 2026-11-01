"""Raw API response cache as gzip JSON files (decision 0006).

Layout: <root>/<source>/<endpoint-path>/<sha256 key>.json.gz

Each file holds an envelope: request URL and parameters, fetch time (UTC), HTTP status,
content type, API version when the response reports one, deprecation headers, and the
unchanged response body. No cookies or other headers are stored.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from placar.core.types import SourceRef

from .http import HttpResponse, OfficialApiClient, UpstreamError

ENVELOPE_SCHEMA = 1
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


class CacheMissError(LookupError):
    """An offline read found nothing in the cache."""


class Freshness(Enum):
    """How long a cached response stays valid."""

    IMMUTABLE = "immutable"  # data that no longer changes (closed legislatures, past events)
    DAILY = "daily"  # data that changes (current officials, ongoing mandates)


def split_url(url: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, str]]:
    """Separate a URL's query string into params, so equal requests get equal keys."""
    parsed = httpx.URL(url)
    merged = {k: str(v) for k, v in parsed.params.multi_items()}
    merged.update({k: str(v) for k, v in (params or {}).items()})
    return str(parsed.copy_with(query=None)), merged


def canonical_url(url: str, params: dict[str, str]) -> str:
    query = urlencode(sorted(params.items()))
    return f"{url}?{query}" if query else url


def make_key(method: str, url: str, params: dict[str, str]) -> str:
    canonical = f"{method.upper()}\n{canonical_url(url, params)}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _api_version(body: Any) -> str | None:
    """Senado responses report `Metadados.VersaoServico` under their single top-level key."""
    if isinstance(body, dict) and len(body) == 1:
        inner = next(iter(body.values()))
        if isinstance(inner, dict):
            meta = inner.get("Metadados")
            if isinstance(meta, dict) and meta.get("VersaoServico"):
                return str(meta["VersaoServico"])
    return None


@dataclass
class CacheEntry:
    key: str
    path: Path
    envelope: dict[str, Any]

    @property
    def body(self) -> Any:
        return self.envelope["body"]

    @property
    def fetched_at(self) -> datetime:
        return datetime.fromisoformat(self.envelope["fetched_at"])

    @property
    def api_url(self) -> str:
        return canonical_url(self.envelope["url"], self.envelope["params"])


class RawCache:
    def __init__(
        self,
        root: Path,
        ttl: timedelta = timedelta(hours=24),
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.root = Path(root)
        self.ttl = ttl
        self._clock = clock

    def path_for(self, source: str, url: str, key: str) -> Path:
        path = httpx.URL(url).path.strip("/")
        segments = [_UNSAFE.sub("_", part) for part in path.split("/") if part] or ["_root"]
        return self.root / _UNSAFE.sub("_", source) / Path(*segments) / f"{key}.json.gz"

    def read(self, source: str, url: str, params: dict[str, str]) -> CacheEntry | None:
        key = make_key("GET", url, params)
        path = self.path_for(source, url, key)
        if not path.is_file():
            return None
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            envelope = json.load(handle)
        return CacheEntry(key=key, path=path, envelope=envelope)

    def write(
        self, source: str, url: str, params: dict[str, str], response: HttpResponse
    ) -> CacheEntry:
        key = make_key("GET", url, params)
        path = self.path_for(source, url, key)
        envelope = {
            "schema": ENVELOPE_SCHEMA,
            "source": source,
            "method": "GET",
            "url": url,
            "params": dict(sorted(params.items())),
            "fetched_at": self._clock().isoformat(),
            "status": response.status,
            "content_type": response.content_type,
            "api_version": _api_version(response.body),
            "deprecation": response.deprecation,
            "body": response.body,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
                gz.write(json.dumps(envelope, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return CacheEntry(key=key, path=path, envelope=envelope)

    def is_fresh(self, entry: CacheEntry, freshness: Freshness) -> bool:
        if freshness is Freshness.IMMUTABLE:
            return True
        return self._clock() - entry.fetched_at < self.ttl


@dataclass
class FetchResult:
    body: Any
    source: SourceRef
    fetched_at: datetime
    from_cache: bool
    stale: bool = False


@dataclass
class FetchStats:
    cache_hits: int = 0
    downloads: int = 0
    stale_used: int = 0
    failures: list[str] = field(default_factory=list)
    deprecations: dict[str, dict[str, str]] = field(default_factory=dict)


class CachedFetcher:
    """Reads from the cache when fresh; otherwise downloads and stores the response."""

    def __init__(
        self,
        source: str,
        client: OfficialApiClient | None,
        cache: RawCache,
        *,
        offline: bool = False,
    ) -> None:
        if client is None and not offline:
            raise ValueError("a client is required unless offline=True")
        self.source = source
        self.client = client
        self.cache = cache
        self.offline = offline
        self.stats = FetchStats()

    @property
    def requests_sent(self) -> int:
        return self.client.requests_sent if self.client else 0

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        *,
        freshness: Freshness = Freshness.DAILY,
        refresh: bool = False,
    ) -> FetchResult:
        base_url, merged = split_url(url, params)
        entry = self.cache.read(self.source, base_url, merged)
        if self.offline:
            # Offline reads use whatever is cached, however old, and never download (Phase B).
            if entry is None:
                raise CacheMissError(canonical_url(base_url, merged))
            self.stats.cache_hits += 1
            return self._result(entry, from_cache=True)
        if entry and not refresh and self.cache.is_fresh(entry, freshness):
            self.stats.cache_hits += 1
            return self._result(entry, from_cache=True)
        try:
            response = self.client.get_json(base_url, merged)
        except UpstreamError as exc:
            self.stats.failures.append(f"{canonical_url(base_url, merged)}: {exc}")
            if entry is not None:
                self.stats.stale_used += 1
                return self._result(entry, from_cache=True, stale=True)
            raise
        entry = self.cache.write(self.source, base_url, merged, response)
        self.stats.downloads += 1
        if response.deprecation:
            self.stats.deprecations[entry.api_url] = response.deprecation
        return self._result(entry, from_cache=False)

    @staticmethod
    def _result(entry: CacheEntry, *, from_cache: bool, stale: bool = False) -> FetchResult:
        return FetchResult(
            body=entry.body,
            source=SourceRef(api_url=entry.api_url, cache_key=entry.key),
            fetched_at=entry.fetched_at,
            from_cache=from_cache,
            stale=stale,
        )
