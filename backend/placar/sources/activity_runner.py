"""Fetch runs for activity data (Phase B2). Downloads go to the raw cache only.

Same rules as Phase A: polite HTTP layer, cache first, per-item failures reported and the run
continues, so an interrupted run resumes from the cache.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

from .cache import Freshness
from .clients.camara import CamaraClient
from .clients.camara_activity import CamaraActivityClient
from .clients.senado import SenadoClient
from .clients.senado_activity import SenadoActivityClient
from .http import UpstreamError
from .runner import PROGRESS_EVERY, Progress, SourceReport

SETTLED_AFTER = timedelta(days=30)  # past data older than this is cached with no expiry


def freshness_for(today: date) -> Callable[[date], Freshness]:
    def pick(range_end: date) -> Freshness:
        return Freshness.IMMUTABLE if range_end < today - SETTLED_AFTER else Freshness.DAILY

    return pick


def _section(report: SourceReport, label: str, work, default):
    """Run one part of the fetch; if a list request fails, report it and go on."""
    try:
        return work()
    except UpstreamError as exc:
        report.failures.append(f"{label}: {exc}")
        return default


def _each(items, label: str, progress: Progress, work) -> None:
    for index, item in enumerate(items, start=1):
        try:
            work(item)
        except UpstreamError:
            pass  # recorded by the fetcher with its URL; the run continues
        if index % PROGRESS_EVERY == 0:
            progress(f"{label}: {index}/{len(items)}")


def fetch_camara_activity(
    people: CamaraClient,
    activity: CamaraActivityClient,
    today: date,
    *,
    limit: int | None = None,
    progress: Progress = print,
) -> SourceReport:
    report = SourceReport(source="camara activity")
    pick = freshness_for(today)
    try:
        leg = people.legislature_on(today)
        report.legislature, report.legislature_start, report.legislature_end = (
            leg.number,
            leg.start,
            leg.end,
        )
        end = min(today, leg.end)
        sessions = list(
            {
                s.event_id: s
                for s in _section(
                    report,
                    "camara plenary sessions",
                    lambda: activity.plenary_sessions(leg.start, end, pick),
                    [],
                )
            }.values()
        )
        held = [s for s in sessions if (s.situation or "") == "Encerrada"]
        presences = 0

        def presence(session):
            nonlocal presences
            presences += len(activity.presence(session.event_id, pick(session.day or today)))

        _each(held[:limit] if limit else held, "camara presence", progress, presence)

        votings = list(
            {
                v.voting_id: v
                for v in _section(
                    report,
                    "camara plenary votings",
                    lambda: activity.plenary_votings(leg.start, end, pick),
                    [],
                )
            }.values()
        )
        ballots = 0

        def ballot(voting):
            nonlocal ballots
            ballots += len(activity.ballots(voting.voting_id, pick(voting.day or today)))

        _each(votings[:limit] if limit else votings, "camara ballots", progress, ballot)

        deputies = sorted({r.deputy_id for r in people.deputies(leg.number, Freshness.DAILY)})
        selected = deputies[:limit] if limit else deputies
        years = list(range(leg.start.year, end.year + 1))
        totals = {"bills": 0, "memberships": 0, "speeches": 0}

        def per_deputy(deputy_id):
            totals["bills"] += len(activity.bills(deputy_id, years, Freshness.DAILY))
            totals["memberships"] += len(
                activity.memberships(deputy_id, leg.start, end, Freshness.DAILY)
            )
            totals["speeches"] += len(activity.speeches(deputy_id, leg.number, Freshness.DAILY))

        _each(selected, "camara deputies", progress, per_deputy)
        report.counts.update(
            plenary_sessions=len(sessions),
            sessions_held=len(held),
            presence_records=presences,
            plenary_votings=len(votings),
            ballots=ballots,
            deputies=len(selected),
            **totals,
        )
    finally:
        report.absorb(activity.fetcher, [*people.notes.items, *activity.notes.items])
    return report


def fetch_senado_activity(
    people: SenadoClient,
    activity: SenadoActivityClient,
    today: date,
    *,
    limit: int | None = None,
    progress: Progress = print,
) -> SourceReport:
    report = SourceReport(source="senado activity")
    pick = freshness_for(today)
    try:
        leg = people.legislature_on(today)
        report.legislature, report.legislature_start, report.legislature_end = (
            leg.number,
            leg.start,
            leg.end,
        )
        end = min(today, leg.end)
        codes, _ = _section(report, "senado vote codes", activity.vote_codes, ({}, None))
        votings, ballots = _section(
            report, "senado votings", lambda: activity.votings(leg.start, end, pick), ([], [])
        )
        votings = list({v.voting_code: v for v in votings}.values())
        ballots = list({(b.voting_code, b.senator_code): b for b in ballots}.values())
        took = people.senators_in_legislature(leg.number, Freshness.DAILY, took_office_only=True)
        senators = sorted({s.code for s in took})
        selected = senators[:limit] if limit else senators
        totals = {"bills": 0, "memberships": 0, "speeches": 0}

        def per_senator(code):
            totals["bills"] += len(activity.bills(code, Freshness.DAILY))
            totals["memberships"] += len(activity.memberships(code, Freshness.DAILY))
            totals["speeches"] += len(activity.speeches(code, leg.start, end, pick))

        _each(selected, "senado senators", progress, per_senator)
        unknown_options = sorted(
            {b.option for b in ballots if b.option and b.option not in codes}
            - {"Sim", "Não", "Abstenção", "Obstrução"}
        )
        report.counts.update(
            vote_code_table=len(codes),
            votings=len(votings),
            ballots=len(ballots),
            senators=len(selected),
            **totals,
        )
        if unknown_options:
            report.notes.append(
                f"senado vote options not in the official code table: {unknown_options}"
            )
    finally:
        report.absorb(activity.fetcher, [*people.notes.items, *activity.notes.items])
    return report
