"""Activity metrics and vote classification on SYNTHETIC data (decision 0011, item 6)."""

from datetime import date
from fractions import Fraction

import pytest

from placar.activity.models import BallotCategory
from placar.core.types import DateWindow, Period, SourceRef
from placar.metrics import activity as m
from placar.metrics.coverage import coverage_of
from placar.sources.clients.camara_activity import CamaraBallot, CamaraVoting
from placar.sources.normalize.activity import Notes, camara, classify

REF = SourceRef(api_url="https://dadosabertos.camara.leg.br/api/v2/x", cache_key="0" * 64)
TODAY = date(2024, 12, 31)
WINDOW = DateWindow(date(2024, 1, 1), date(2024, 12, 31))


def cov(*periods):
    return coverage_of([(p, REF) for p in periods], WINDOW, TODAY)


def d(key, day, kind=""):
    return m.Dated(key, day, REF, kind)


# --- classification of vote options ---------------------------------------------------------


@pytest.mark.parametrize(
    ("option", "category"),
    [
        ("Sim", BallotCategory.TAKES_PART),
        ("Não", BallotCategory.TAKES_PART),
        ("Abstenção", BallotCategory.TAKES_PART),
        ("Obstrução", BallotCategory.TAKES_PART),
        ("Artigo 17", BallotCategory.PRESIDING),
        ("Presidente (art. 51 RISF)", BallotCategory.PRESIDING),
        ("P-NRV", BallotCategory.PRESENT_NO_VOTE),
        ("NCom", BallotCategory.ABSENT),
        ("AP", BallotCategory.JUSTIFIED_ABSENCE),
        ("Votou", BallotCategory.TAKES_PART),  # Senado secret ballot: voted, content secret
    ],
)
def test_classify_known_options(option, category):
    notes = Notes()
    got, text = classify(option, {"AP": "Atividade parlamentar"}, notes)
    assert got == category
    assert notes.unknown_options == {}
    if option == "AP":
        assert text == "Atividade parlamentar"


def test_classify_unknown_option_is_reported_not_guessed():
    notes = Notes()
    assert classify("XYZ", {}, notes)[0] == BallotCategory.UNKNOWN
    assert classify("XYZ", {}, notes)[0] == BallotCategory.UNKNOWN
    assert notes.unknown_options == {"XYZ": 2}


def test_camara_voting_with_only_empty_options_is_secret():
    # Data issue 19: Câmara secret ballots list who voted with every option empty.
    votings = [
        CamaraVoting("s-1", date(2025, 10, 29), "PLEN", None, "Indicação", REF),
        CamaraVoting("n-1", date(2025, 10, 29), "PLEN", None, "PL 1/2025", REF),
    ]
    ballots = [
        CamaraBallot("s-1", 1, "", REF),
        CamaraBallot("s-1", 2, None, REF),
        CamaraBallot("n-1", 1, "Sim", REF),
        CamaraBallot("n-1", 2, "", REF),  # one empty option in an open vote stays unknown
    ]
    bundle, notes = camara([], [], votings, ballots, [], [], [])
    secret = {v.external_id: v.secret for v in bundle.votings}
    assert secret == {"s-1": True, "n-1": None}
    by_voting = {(b.voting_key, b.official_id): b.category for b in bundle.ballots}
    assert by_voting[("CAMARA:voting:s-1", 1)] == BallotCategory.TAKES_PART
    assert by_voting[("CAMARA:voting:n-1", 2)] == BallotCategory.UNKNOWN
    assert notes.unknown_options == {"": 1}


# --- metrics only count days in office -------------------------------------------------------


def test_attendance_counts_only_sessions_while_in_office():
    coverage = cov(Period(date(2024, 3, 1), date(2024, 6, 30)))
    sessions = [d("s1", date(2024, 2, 1)), d("s2", date(2024, 3, 5)), d("s3", date(2024, 6, 30)),
                d("s4", date(2024, 7, 1))]  # fmt: skip
    result = m.plenary_attendance(coverage, sessions, {"s1": REF, "s2": REF})
    assert (result.numerator, result.denominator) == (1, 2)  # s1 and s4 are outside the period
    assert result.value == Fraction(1, 2)


def test_attendance_with_no_sessions_in_office_has_no_value():
    result = m.plenary_attendance(cov(), [d("s1", date(2024, 3, 5))], {})
    assert result.denominator == 0 and result.value is None


def test_substitute_counts_only_own_days():
    titular = cov(Period(date(2024, 1, 1), date(2024, 3, 31)))
    substitute = cov(Period(date(2024, 4, 1), None))
    sessions = [d("a", date(2024, 2, 1)), d("b", date(2024, 5, 1)), d("c", date(2024, 9, 1))]
    present = {"a": REF, "b": REF, "c": REF}
    assert m.plenary_attendance(titular, sessions, present).denominator == 1
    assert m.plenary_attendance(substitute, sessions, present).denominator == 2


def test_bills_counted_types_and_period():
    coverage = cov(Period(date(2024, 1, 1), None))
    bills = [d("1", date(2024, 2, 1), "PL"), d("2", date(2024, 2, 1), "REQ"),
             d("3", date(2023, 12, 31), "PL"), d("4", None, "PEC")]  # fmt: skip
    result = m.bills_authored(coverage, bills)
    assert result.numerator == 1 and result.denominator is None and result.value == 1


def test_vote_participation_excludes_presided_and_counts_categories():
    coverage = cov(Period(date(2024, 1, 1), None))
    votings = [d(k, date(2024, 5, i + 1)) for i, k in enumerate("abcde")]
    ballots = {
        "a": (BallotCategory.TAKES_PART, "Sim", REF),
        "b": (BallotCategory.PRESIDING, "Artigo 17", REF),
        "c": (BallotCategory.JUSTIFIED_ABSENCE, "AP", REF),
        "d": (BallotCategory.PRESENT_NO_VOTE, "P-NRV", REF),
    }  # "e": no record (Câmara lists only those who voted)
    result = m.vote_participation(coverage, votings, ballots)
    assert (result.numerator, result.denominator) == (1, 4)
    assert result.details["presided_excluded"] == 1
    assert result.details["by_category"] == {
        "TAKES_PART": 1, "JUSTIFIED": 1, "PRESENT_NO_VOTE": 1, "NO_RECORD": 1
    }  # fmt: skip


def test_party_switch_does_not_affect_activity_metrics():
    # Metrics only read periods in office and dated records; affiliations are not an input.
    coverage = cov(Period(date(2024, 1, 1), None))
    assert m.speeches(coverage, [d("x", date(2024, 4, 1)), d("y", date(2024, 8, 1))]).numerator == 2


def test_leave_days_merges_overlaps_and_clips():
    coverage = cov(Period(date(2024, 1, 1), None))
    leaves = [(Period(date(2023, 12, 20), date(2024, 1, 10)), REF),
              (Period(date(2024, 1, 5), date(2024, 1, 15)), REF),
              (Period(date(2024, 12, 30), None), REF)]  # fmt: skip
    days_on_leave, refs = m.leave_days(coverage, leaves, TODAY)
    assert days_on_leave == 15 + 2 and refs == (REF,)


def test_leave_sources_join_attendance_sources():
    leave_ref = SourceRef(
        api_url="https://legis.senado.leg.br/dadosabertos/lic", cache_key="1" * 64
    )
    coverage = cov(Period(date(2024, 1, 1), None))
    result = m.with_leave_days(
        m.plenary_attendance(coverage, [d("s", date(2024, 2, 1))], {}),
        [(Period(date(2024, 3, 1), date(2024, 3, 3)), leave_ref)],
        TODAY,
    )
    assert result.details["leave_days"] == 3 and leave_ref in result.sources


def test_sources_are_unique():
    coverage = cov(Period(date(2024, 1, 1), None))
    result = m.speeches(coverage, [d("x", date(2024, 4, 1)), d("y", date(2024, 4, 2))])
    assert result.sources == (REF,)
