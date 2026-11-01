"""Properties of the activity metrics (hypothesis) and bulk-vs-single consistency (database)."""

from datetime import date, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from placar.activity.services import replace_activity
from placar.core.types import DateWindow, Period, SourceRef
from placar.legislators.models import Official
from placar.metrics import activity as m
from placar.metrics.coverage import coverage_of
from placar.metrics.selectors import (
    activity_metrics,
    activity_metrics_bulk,
    coverage,
    coverage_bulk,
)

from .builders import synthetic_camara_activity
from .test_legislators_db import load_both

REF = SourceRef(api_url="https://dadosabertos.camara.leg.br/api/v2/x", cache_key="0" * 64)
BASE = date(2023, 1, 1)
TODAY = BASE + timedelta(days=1500)
CATEGORIES = ["TAKES_PART", "PRESIDING", "PRESENT_NO_VOTE", "JUSTIFIED", "ABSENT", "UNKNOWN"]


@st.composite
def periods(draw):
    start = BASE + timedelta(days=draw(st.integers(0, 1400)))
    end = None if draw(st.booleans()) else start + timedelta(days=draw(st.integers(0, 600)))
    return Period(start, end)


@st.composite
def window(draw):
    start = BASE + timedelta(days=draw(st.integers(0, 1400)))
    return DateWindow(start, start + timedelta(days=draw(st.integers(0, 800))))


@st.composite
def dated(draw, n=40):
    days = draw(st.lists(st.integers(0, 1500), max_size=n))
    return [m.Dated(f"k{i}", BASE + timedelta(days=d), REF, "PL") for i, d in enumerate(days)]


def cov(ps, w):
    return coverage_of([(p, REF) for p in ps], w, TODAY)


@given(st.lists(periods(), max_size=5), window(), dated(), st.data())
def test_attendance_bounds_and_only_days_in_office(ps, w, sessions, data):
    present = {s.key: REF for s in sessions if data.draw(st.booleans())}
    result = m.plenary_attendance(cov(ps, w), sessions, present)
    assert 0 <= result.numerator <= result.denominator
    if result.value is not None:
        assert 0 <= result.value <= 1
    in_office = [s for s in sessions if m.in_office(s.day, cov(ps, w).periods)]
    assert result.denominator == len(in_office)


@given(st.lists(periods(), max_size=5), window(), dated(), st.data())
def test_vote_participation_bounds(ps, w, votings, data):
    ballots = {
        v.key: (data.draw(st.sampled_from(CATEGORIES)), "x", REF)
        for v in votings
        if data.draw(st.booleans())
    }
    result = m.vote_participation(cov(ps, w), votings, ballots)
    assert 0 <= result.numerator <= result.denominator
    counted = sum(result.details["by_category"].values())
    assert counted == result.denominator
    assert result.details["presided_excluded"] + result.denominator == len(
        [v for v in votings if m.in_office(v.day, cov(ps, w).periods)]
    )


@given(st.lists(periods(), max_size=5), window(), dated())
def test_counts_never_include_days_out_of_office(ps, w, items):
    c = cov(ps, w)
    assert m.speeches(c, items).numerator == sum(1 for i in items if m.in_office(i.day, c.periods))
    assert m.bills_authored(c, items).numerator <= len(items)


@given(window(), dated())
def test_nobody_in_office_counts_nothing(w, items):
    c = cov([], w)
    assert m.speeches(c, items).numerator == 0
    assert m.plenary_attendance(c, items, {i.key: REF for i in items}).denominator == 0


@pytest.mark.django_db
def test_bulk_metrics_match_single_official_metrics():
    load_both()
    replace_activity(synthetic_camara_activity())
    window_57 = DateWindow(date(2023, 2, 1), date(2026, 11, 1))
    today = date(2026, 11, 1)
    for house in ("CAMARA", "SENADO"):
        coverages = coverage_bulk(house, window_57, today)
        bulk = activity_metrics_bulk(house, window_57, today, coverages)
        for pk in Official.objects.filter(house=house).values_list("pk", flat=True):
            assert coverages[pk].days_in_office == coverage(pk, window_57, today).days_in_office
            single = activity_metrics(pk, window_57, today)
            for key, result in single.items():
                other = bulk[pk][key]
                if result is None:
                    assert other is None
                    continue
                assert (other.numerator, other.denominator) == (
                    result.numerator,
                    result.denominator,
                )
                assert set(other.sources) == set(result.sources)
                assert other.details == result.details
