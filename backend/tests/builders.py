"""SYNTHETIC test data shared by several test modules (decision 0011, item 6).

Small builder functions, no factory library. Everything here is made up for tests, labeled as
synthetic, and never shown in the app. Real cases come from recorded fixtures instead
(`tests/fixtures/`, see `test_activity_real_cases.py`).
"""

from datetime import date

from placar.activity.models import BallotCategory
from placar.activity.services import (
    ActivityBundle,
    BallotRecord,
    BillRecord,
    PresenceRecord,
    SessionRecord,
    SpeechRecord,
    VotingRecord,
)
from placar.core.types import SourceRef

# A made-up source on an official host, for synthetic records.
SYNTHETIC_REF = SourceRef(api_url="https://dadosabertos.camara.leg.br/api/v2/x", cache_key="0" * 64)


def synthetic_camara_activity() -> ActivityBundle:
    """Activity for the REAL fixture deputy 220593 (in office 2023-02-01 to 2025-01-01).

    One session and one vote in office (present, voted "Sim"), one session after he left
    office, one bill co-authored with 220714, one speech; plus a presence of an official who is
    not loaded (99999), which storage must skip.
    """
    ref = SYNTHETIC_REF
    b = ActivityBundle(house="CAMARA")
    for key, day in (("e1", date(2024, 3, 5)), ("e2", date(2025, 3, 5))):
        b.sessions.append(
            SessionRecord(f"CAMARA:event:{key}", key, day, ref, "Sessão Deliberativa", "Encerrada")
        )
    b.presences += [
        PresenceRecord("CAMARA:event:e1", 220593, ref),
        PresenceRecord("CAMARA:event:e2", 99999, ref),
    ]
    b.votings.append(VotingRecord("CAMARA:voting:v1", "v1", date(2024, 3, 5), ref))
    b.ballots.append(
        BallotRecord("CAMARA:voting:v1", 220593, "Sim", BallotCategory.TAKES_PART, ref)
    )
    b.bills.append(
        BillRecord("CAMARA:bill:1", "1", (220593, 220714), ref, "PL", 1, 2024, date(2024, 1, 2))
    )
    b.speeches.append(SpeechRecord("CAMARA:speech:1", 220593, date(2024, 3, 5), ref))
    return b
