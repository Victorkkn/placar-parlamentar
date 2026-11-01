"""Fetch runs for the current legislature (Phase A, task A6).

Downloads go to the raw cache only; nothing is written to the database in Phase A.
A failure for one person is recorded and the run continues; failures are never hidden.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .cache import CachedFetcher, Freshness, RawCache
from .clients.camara import CamaraClient
from .clients.senado import SenadoClient
from .http import OfficialApiClient, UpstreamError

Progress = Callable[[str], None]
PROGRESS_EVERY = 50


@dataclass
class SourceReport:
    source: str
    legislature: int | None = None
    legislature_start: date | None = None
    legislature_end: date | None = None
    counts: dict[str, int] = field(default_factory=dict)
    requests_sent: int = 0
    downloads: int = 0
    cache_hits: int = 0
    stale_used: int = 0
    failures: list[str] = field(default_factory=list)
    deprecations: dict[str, dict[str, str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def absorb(self, fetcher: CachedFetcher, notes: list[str]) -> None:
        self.requests_sent = fetcher.requests_sent
        self.downloads = fetcher.stats.downloads
        self.cache_hits = fetcher.stats.cache_hits
        self.stale_used = fetcher.stats.stale_used
        self.failures = [*self.failures, *fetcher.stats.failures]
        self.deprecations = dict(fetcher.stats.deprecations)
        self.notes = [*self.notes, *notes]


def make_api_client() -> OfficialApiClient:
    return OfficialApiClient(
        user_agent=settings.PLACAR["USER_AGENT"],
        rate_per_sec=settings.PLACAR["REQUESTS_PER_SECOND"],
    )


def make_fetcher(source: str, cache_dir: Path | None = None) -> CachedFetcher:
    root = cache_dir or settings.PLACAR["RAW_CACHE_DIR"]
    if root is None:
        raise ImproperlyConfigured("PLACAR RAW_CACHE_DIR is not set")
    cache = RawCache(Path(root), ttl=timedelta(hours=settings.PLACAR["CACHE_TTL_HOURS"]))
    return CachedFetcher(source, make_api_client(), cache)


def _freshness(end: date, today: date) -> Freshness:
    return Freshness.IMMUTABLE if end < today else Freshness.DAILY


def fetch_camara(
    client: CamaraClient, today: date, *, limit: int | None = None, progress: Progress = print
) -> SourceReport:
    report = SourceReport(source="camara")
    try:
        leg = client.legislature_on(today)
        report.legislature, report.legislature_start, report.legislature_end = (
            leg.number,
            leg.start,
            leg.end,
        )
        freshness = _freshness(leg.end, today)
        rows = client.deputies(leg.number, freshness)
        ids = sorted({row.deputy_id for row in rows})
        report.counts.update(deputy_rows=len(rows), deputies=len(ids))
        if len(rows) != len(ids):
            report.notes.append(
                f"camara deputies list: {len(rows)} rows for {len(ids)} people "
                "(one row per deputy and party; data issue 8)"
            )
        selected = ids[:limit] if limit else ids
        events = 0
        for index, deputy_id in enumerate(selected, start=1):
            try:
                events += len(client.history(deputy_id, freshness))
            except UpstreamError:
                pass  # already recorded by the fetcher (with the URL); the run continues
            if index % PROGRESS_EVERY == 0:
                progress(f"camara: {index}/{len(selected)} deputies")
        report.counts.update(histories=len(selected), history_events=events)
    finally:
        report.absorb(client.fetcher, client.notes.items)
    return report


def fetch_senado(
    client: SenadoClient, today: date, *, limit: int | None = None, progress: Progress = print
) -> SourceReport:
    report = SourceReport(source="senado")
    try:
        leg = client.legislature_on(today)
        report.legislature, report.legislature_start, report.legislature_end = (
            leg.number,
            leg.start,
            leg.end,
        )
        freshness = _freshness(leg.end, today)
        listed = client.senators_in_legislature(leg.number, freshness)
        took_office = client.senators_in_legislature(leg.number, freshness, took_office_only=True)
        current = client.current_senators()
        codes = sorted({s.code for s in took_office})
        titular_mandates = sum(
            1 for s in listed for m in s.mandates if (m.participation or "") == "Titular"
        )
        report.counts.update(
            listed=len(listed),
            took_office=len(codes),
            in_office_today=len(current),
            titular_mandates_listed=titular_mandates,
        )
        missing = sorted({s.code for s in current} - set(codes))
        if missing:
            report.notes.append(
                f"senado: in office today but not in the took-office list: {missing}"
            )
        selected = codes[:limit] if limit else codes
        totals = {"mandates": 0, "exercises": 0, "leaves": 0, "affiliations": 0}
        for index, code in enumerate(selected, start=1):
            try:
                mandates = client.mandates(code, freshness)
                totals["mandates"] += len(mandates)
                totals["exercises"] += sum(len(m.exercises) for m in mandates)
                totals["leaves"] += len(client.leaves(code, freshness))
                totals["affiliations"] += len(client.affiliations(code, freshness))
            except UpstreamError:
                pass  # already recorded by the fetcher (with the URL); the run continues
            if index % PROGRESS_EVERY == 0:
                progress(f"senado: {index}/{len(selected)} senators")
        report.counts.update(details_fetched=len(selected), **totals)
    finally:
        report.absorb(client.fetcher, client.notes.items)
    return report


def cross_check(camara: SourceReport, senado: SourceReport) -> list[str]:
    """Both houses should report the same legislature; differences are kept and reported."""
    if camara.legislature is None or senado.legislature is None:
        return []
    ours = (camara.legislature, camara.legislature_start, camara.legislature_end)
    theirs = (senado.legislature, senado.legislature_start, senado.legislature_end)
    if ours != theirs:
        return [f"legislature differs between houses: camara={ours} senado={theirs}"]
    return []


def format_report(reports: list[SourceReport], extra_notes: list[str] | None = None) -> str:
    lines = []
    for r in reports:
        lines.append(f"== {r.source}: legislature {r.legislature} ({r.legislature_start} to "
                     f"{r.legislature_end})")  # fmt: skip
        for name, value in r.counts.items():
            lines.append(f"  {name}: {value}")
        lines.append(
            f"  requests sent: {r.requests_sent} | downloads: {r.downloads} | "
            f"cache hits: {r.cache_hits} | stale copies used: {r.stale_used}"
        )
        for title, items in (("failures", r.failures), ("notes", r.notes)):
            if items:
                lines.append(f"  {title} ({len(items)}):")
                lines.extend(f"    - {item}" for item in items)
        if r.deprecations:
            lines.append(f"  deprecated services ({len(r.deprecations)}):")
            lines.extend(f"    - {url}: {h}" for url, h in r.deprecations.items())
    if extra_notes:
        lines.append("== cross-checks")
        lines.extend(f"  - {note}" for note in extra_notes)
    return "\n".join(lines)
