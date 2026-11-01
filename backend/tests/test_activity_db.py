"""Activity storage and metrics in the database: REAL officials (fixtures) + SYNTHETIC activity."""

from datetime import date

import pytest

from placar.activity.models import Ballot, BallotCategory, Membership, Presence
from placar.activity.services import (
    ActivityBundle,
    BallotRecord,
    BillRecord,
    MembershipRecord,
    PresenceRecord,
    SessionRecord,
    SpeechRecord,
    VotingRecord,
    replace_activity,
)
from placar.core.types import DateWindow, SourceRef
from placar.legislators.selectors import get_official
from placar.metrics.selectors import activity_metrics

from .test_legislators_db import load_both

pytestmark = pytest.mark.django_db
REF = SourceRef(api_url="https://dadosabertos.camara.leg.br/api/v2/x", cache_key="0" * 64)
TODAY = date(2026, 11, 1)
LEG57 = DateWindow(date(2023, 2, 1), date(2027, 1, 31))


def camara_bundle():
    b = ActivityBundle(house="CAMARA")
    # 220593 was in office 2023-02-01 .. 2025-01-01 (real fixture).
    for key, day in (("e1", date(2024, 3, 5)), ("e2", date(2025, 3, 5))):
        b.sessions.append(
            SessionRecord(f"CAMARA:event:{key}", key, day, REF, "Sessão Deliberativa", "Encerrada")
        )
    b.presences += [
        PresenceRecord("CAMARA:event:e1", 220593, REF),
        PresenceRecord("CAMARA:event:e2", 99999, REF),
    ]
    b.votings.append(VotingRecord("CAMARA:voting:v1", "v1", date(2024, 3, 5), REF))
    b.ballots.append(
        BallotRecord("CAMARA:voting:v1", 220593, "Sim", BallotCategory.TAKES_PART, REF)
    )
    b.bills.append(
        BillRecord("CAMARA:bill:1", "1", (220593, 220714), REF, "PL", 1, 2024, date(2024, 1, 2))
    )
    b.speeches.append(SpeechRecord("CAMARA:speech:1", 220593, date(2024, 3, 5), REF))
    return b


def test_replace_activity_skips_unknown_officials_and_is_idempotent():
    load_both()
    counts = replace_activity(camara_bundle())
    assert counts["presences"] == 1
    assert counts["skipped (presences: official not loaded)"] == 1
    replace_activity(camara_bundle())
    assert Presence.objects.count() == 1 and Ballot.objects.count() == 1


def test_long_official_body_names_are_kept_whole():
    # Data issue 18: a real Câmara committee name has 573 characters.
    load_both()
    bundle = camara_bundle()
    name = "Comissão Especial " + "x" * 600
    bundle.memberships.append(
        MembershipRecord("CAMARA:membership:1", 220593, REF, "1", "CESP", name, "CD", "Titular")
    )
    replace_activity(bundle)
    assert Membership.objects.get().body_name == name


def test_activity_metrics_for_real_official():
    load_both()
    replace_activity(camara_bundle())
    deputy = get_official("CAMARA", 220593)
    result = activity_metrics(deputy.pk, LEG57, TODAY)
    attendance = result["plenary_attendance"]
    assert (attendance.numerator, attendance.denominator) == (1, 1)  # e2 is after he left office
    assert "leave_days" in attendance.details
    assert result["bills_authored"].numerator == 1
    assert (result["vote_participation"].numerator, result["vote_participation"].denominator) == (
        1,
        1,
    )
    assert result["speeches"].numerator == 1
    assert all(ref.api_url.startswith("https://") for ref in attendance.sources)


def test_senator_has_no_attendance_metric():
    load_both()
    senator = get_official("SENADO", 5917)
    assert activity_metrics(senator.pk, LEG57, TODAY)["plenary_attendance"] is None
