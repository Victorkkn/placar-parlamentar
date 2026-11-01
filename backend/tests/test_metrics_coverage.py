"""coverage(): required cases on SYNTHETIC periods (decision 0011, item 6) and property tests."""

from datetime import date, timedelta

from hypothesis import given
from hypothesis import strategies as st

from placar.core.types import DateWindow, Period, SourceRef
from placar.metrics.coverage import coverage_of, merge

TODAY = date(2026, 11, 1)
LEG57 = DateWindow(date(2023, 2, 1), date(2027, 1, 31))
REF = SourceRef(api_url="https://legis.senado.leg.br/dadosabertos/x", cache_key="0" * 64)
REF2 = SourceRef(api_url="https://legis.senado.leg.br/dadosabertos/y", cache_key="1" * 64)


def cov(periods, window=LEG57, today=TODAY):
    return coverage_of([(p, REF) for p in periods], window, today)


def test_full_term():
    window = DateWindow(date(2023, 2, 1), date(2025, 1, 31))
    result = cov([Period(date(2023, 2, 1), date(2027, 1, 31))], window)
    assert result.days_in_office == window.days and result.share == 1.0


def test_mid_term_entry():
    window = DateWindow(date(2024, 1, 1), date(2024, 12, 31))
    result = cov([Period(date(2024, 7, 1), None)], window)
    assert result.days_in_office == 184  # Jul 1 – Dec 31, both included
    assert result.share_exact.numerator * 366 == 184 * result.share_exact.denominator


def test_leave_that_ends_the_period_and_return():
    # Câmara style: "Saída" for leave on 2024-03-10 (last day in office), "Entrada" on 2024-04-01.
    window = DateWindow(date(2024, 3, 1), date(2024, 4, 30))
    result = cov(
        [Period(date(2023, 2, 1), date(2024, 3, 10)), Period(date(2024, 4, 1), None)], window
    )
    assert result.days_in_office == 10 + 30
    assert len(result.periods) == 2


def test_leave_without_interruption_counts():
    # Senado style: a short leave does not interrupt the Exercicio, so the period is unbroken.
    window = DateWindow(date(2022, 4, 1), date(2022, 4, 30))
    assert cov([Period(date(2019, 2, 1), date(2022, 11, 21))], window).share == 1.0


def test_substitute_counts_only_own_days():
    window = DateWindow(date(2022, 11, 1), date(2023, 9, 30))
    titular = cov([Period(date(2019, 2, 1), date(2022, 11, 21)), Period(date(2023, 9, 4), date(2023, 9, 4))], window)  # fmt: skip
    alternate = cov([Period(date(2022, 12, 7), date(2023, 9, 4)), Period(date(2023, 9, 4), None)], window)  # fmt: skip
    assert titular.days_in_office == 21 + 1
    assert alternate.days_in_office == (date(2023, 9, 30) - date(2022, 12, 7)).days + 1


def test_party_switch_has_no_effect():
    # Coverage only reads periods in office; affiliations are not an input.
    one = cov([Period(date(2023, 2, 1), None)])
    assert one.days_in_office == (TODAY - date(2023, 2, 1)).days + 1


def test_touching_periods_are_merged_without_double_counting():
    result = cov([Period(date(2022, 12, 7), date(2023, 9, 4)), Period(date(2023, 9, 4), None)])
    assert len(result.periods) == 1
    assert result.days_in_office == (TODAY - date(2023, 2, 1)).days + 1 == 1370


def test_open_period_stops_at_today_and_future_periods_are_ignored():
    result = cov([Period(date(2026, 10, 30), None), Period(date(2026, 12, 1), None)])
    assert result.days_in_office == 3


def test_no_periods_gives_zero():
    result = cov([])
    assert result.days_in_office == 0 and result.share == 0.0 and result.sources == ()


def test_sources_are_kept_once_and_only_for_periods_used():
    result = coverage_of(
        [(Period(date(2023, 3, 1), date(2023, 3, 5)), REF),
         (Period(date(2023, 3, 6), date(2023, 3, 9)), REF),
         (Period(date(2010, 1, 1), date(2010, 12, 31)), REF2)],
        LEG57, TODAY,
    )  # fmt: skip
    assert result.sources == (REF,)


# --- property tests (hypothesis) ---------------------------------------------------------

BASE = date(2020, 1, 1)
days_st = st.integers(min_value=0, max_value=3000)


@st.composite
def periods(draw):
    start = BASE + timedelta(days=draw(days_st))
    open_ = draw(st.booleans())
    end = None if open_ else start + timedelta(days=draw(st.integers(0, 800)))
    return Period(start, end)


@st.composite
def windows(draw):
    start = BASE + timedelta(days=draw(days_st))
    return DateWindow(start, start + timedelta(days=draw(st.integers(0, 2000))))


TODAY_P = BASE + timedelta(days=2500)


@given(st.lists(periods(), max_size=8), windows())
def test_share_between_zero_and_one(ps, window):
    result = cov(ps, window, TODAY_P)
    assert 0 <= result.days_in_office <= window.days
    assert 0.0 <= result.share <= 1.0


@given(st.lists(periods(), max_size=8))
def test_merge_is_idempotent(ps):
    closed = [Period(p.start, p.end or TODAY_P) for p in ps if p.start <= TODAY_P]
    once = merge(closed)
    assert merge(once) == once


@given(st.lists(periods(), max_size=8), windows(), st.integers(0, 2000))
def test_splitting_a_window_adds_up(ps, window, cut):
    if window.days < 2:
        return
    split = window.start + timedelta(days=cut % (window.days - 1))
    left = DateWindow(window.start, split)
    right = DateWindow(split + timedelta(days=1), window.end)
    whole = cov(ps, window, TODAY_P).days_in_office
    assert whole == cov(ps, left, TODAY_P).days_in_office + cov(ps, right, TODAY_P).days_in_office


@given(st.lists(periods(), max_size=8), windows())
def test_order_of_periods_does_not_matter(ps, window):
    assert cov(ps, window, TODAY_P).days_in_office == cov(ps[::-1], window, TODAY_P).days_in_office
