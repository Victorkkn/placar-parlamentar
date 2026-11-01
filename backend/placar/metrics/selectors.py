"""Thin shell: loads data through other apps' selectors (decision 0007) for the pure metrics."""

from __future__ import annotations

from datetime import date

from django.utils import timezone

from placar.activity import selectors as activity
from placar.core.types import DateWindow
from placar.legislators import selectors as legislators
from placar.legislators.models import Official

from . import activity as metrics
from .coverage import CoverageResult, coverage_of


def coverage(official_id: int, window: DateWindow, today: date | None = None) -> CoverageResult:
    """Days in office for an official within a window, and the coverage share."""
    return coverage_of(
        legislators.service_periods_for(official_id), window, today or timezone.localdate()
    )


def _dated(items) -> list[metrics.Dated]:
    return [metrics.Dated(i.key, i.day, i.source, i.kind) for i in items]


def activity_metrics(
    official_id: int, window: DateWindow, today: date | None = None
) -> dict[str, metrics.MetricResult | None]:
    """The first metrics for one official; None where the metric does not apply (0014)."""
    today = today or timezone.localdate()
    house = Official.objects.values_list("house", flat=True).get(pk=official_id)
    cov = coverage(official_id, window, today)
    attendance = None
    if house == "CAMARA":  # no Senado attendance in the MVP (decision 0014)
        attendance = metrics.with_leave_days(
            metrics.plenary_attendance(
                cov, _dated(activity.held_sessions(house)), activity.presence_keys(official_id)
            ),
            legislators.leaves_for(official_id),
            today,
        )
    return {
        "plenary_attendance": attendance,
        "bills_authored": metrics.bills_authored(cov, _dated(activity.bills_of(official_id))),
        "vote_participation": metrics.vote_participation(
            cov, _dated(activity.nominal_votings(house)), activity.ballots_of(official_id)
        ),
        "speeches": metrics.speeches(cov, _dated(activity.speeches_of(official_id))),
    }


def coverage_bulk(house: str | None, window: DateWindow, today: date) -> dict[int, CoverageResult]:
    """Coverage for every official of a house (or both houses), in one query."""
    periods = legislators.periods_by_official(house)
    return {
        o.pk: coverage_of(periods.get(o.pk, []), window, today)
        for o in legislators.officials(house)
    }


def activity_metrics_bulk(
    house: str, window: DateWindow, today: date, coverages: dict[int, CoverageResult]
) -> dict[int, dict[str, metrics.MetricResult | None]]:
    """The first metrics for many officials of one house, with a fixed number of queries."""
    sessions = _dated(activity.held_sessions(house)) if house == "CAMARA" else []
    votings = _dated(activity.nominal_votings(house))
    presences = activity.presence_keys_by_official(house) if house == "CAMARA" else {}
    ballots = activity.ballots_by_official(house)
    bills = activity.bills_by_official(house)
    speeches = activity.speeches_by_official(house)
    leaves = legislators.leaves_by_official(house) if house == "CAMARA" else {}
    result = {}
    for pk, cov in coverages.items():
        attendance = None
        if house == "CAMARA":
            attendance = metrics.with_leave_days(
                metrics.plenary_attendance(cov, sessions, presences.get(pk, {})),
                leaves.get(pk, []),
                today,
            )
        result[pk] = {
            "plenary_attendance": attendance,
            "bills_authored": metrics.bills_authored(cov, _dated(bills.get(pk, []))),
            "vote_participation": metrics.vote_participation(cov, votings, ballots.get(pk, {})),
            "speeches": metrics.speeches(cov, _dated(speeches.get(pk, []))),
        }
    return result
