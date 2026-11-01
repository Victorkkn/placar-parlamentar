"""Write path for activity records (decision 0007: only `sources` calls these).

`replace_activity` replaces one house's activity rows in one transaction (idempotent re-runs).
Records refer to officials by the house's own id; records for officials not in the database are
skipped and counted, never attached to a guessed person.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from django.db import transaction

from placar.core.types import SourceRef
from placar.legislators.models import House, Official

from .models import Ballot, Bill, Membership, Presence, Session, Speech, Voting

BATCH = 5000


def _src(ref: SourceRef) -> dict[str, str]:
    return {
        "source_api_url": ref.api_url,
        "source_cache_file_id": ref.cache_key,
        "source_public_url": ref.public_url or "",
        "source_label": ref.label,
    }


@dataclass(frozen=True)
class BillRecord:
    natural_key: str
    external_id: str
    author_ids: tuple[int, ...]
    source: SourceRef
    type_code: str = ""
    number: int | None = None
    year: int | None = None
    presented_on: date | None = None
    summary: str = ""


@dataclass(frozen=True)
class SessionRecord:
    natural_key: str
    external_id: str
    day: date | None
    source: SourceRef
    type_text: str = ""
    situation: str = ""


@dataclass(frozen=True)
class PresenceRecord:
    session_key: str
    official_id: int
    source: SourceRef


@dataclass(frozen=True)
class VotingRecord:
    natural_key: str
    external_id: str
    day: date | None
    source: SourceRef
    body: str = ""
    description: str = ""
    secret: bool | None = None
    identification: str = ""


@dataclass(frozen=True)
class BallotRecord:
    voting_key: str
    official_id: int
    option_raw: str
    category: str
    source: SourceRef
    option_text: str = ""


@dataclass(frozen=True)
class MembershipRecord:
    natural_key: str
    official_id: int
    source: SourceRef
    body_external_id: str = ""
    body_acronym: str = ""
    body_name: str = ""
    body_house: str = ""
    role: str = ""
    start: date | None = None
    end: date | None = None


@dataclass(frozen=True)
class SpeechRecord:
    natural_key: str
    official_id: int
    day: date | None
    source: SourceRef
    type_code: str = ""
    type_text: str = ""
    phase: str = ""
    session_external_id: str = ""


@dataclass
class ActivityBundle:
    house: str
    bills: list[BillRecord] = field(default_factory=list)
    sessions: list[SessionRecord] = field(default_factory=list)
    presences: list[PresenceRecord] = field(default_factory=list)
    votings: list[VotingRecord] = field(default_factory=list)
    ballots: list[BallotRecord] = field(default_factory=list)
    memberships: list[MembershipRecord] = field(default_factory=list)
    speeches: list[SpeechRecord] = field(default_factory=list)


@transaction.atomic
def replace_activity(bundle: ActivityBundle) -> dict[str, int]:
    house = bundle.house
    if house not in House.values:
        raise ValueError(f"unknown house {house!r}")
    officials = dict(Official.objects.filter(house=house).values_list("house_id", "pk"))
    skipped: dict[str, int] = {}

    def official(kind: str, house_id: int) -> int | None:
        pk = officials.get(house_id)
        if pk is None:
            skipped[kind] = skipped.get(kind, 0) + 1
        return pk

    for model in (Bill, Session, Voting, Membership, Speech):
        model.objects.filter(house=house).delete()  # cascades to presences and ballots

    bills = {}
    for rec in bundle.bills:
        bills[rec.natural_key] = Bill(
            natural_key=rec.natural_key, house=house, external_id=rec.external_id,
            type_code=rec.type_code, number=rec.number, year=rec.year,
            presented_on=rec.presented_on, summary=rec.summary, **_src(rec.source),
        )  # fmt: skip
    Bill.objects.bulk_create(bills.values(), batch_size=BATCH)
    links = set()
    for rec in bundle.bills:
        for author in rec.author_ids:
            pk = official("bill authors", author)
            if pk:
                links.add((bills[rec.natural_key].pk, pk))
    Bill.authors.through.objects.bulk_create(
        [Bill.authors.through(bill_id=b, official_id=o) for b, o in sorted(links)], batch_size=BATCH
    )

    sessions = {
        rec.natural_key: Session(
            natural_key=rec.natural_key,
            house=house,
            external_id=rec.external_id,
            day=rec.day,
            type_text=rec.type_text,
            situation=rec.situation,
            **_src(rec.source),
        )  # fmt: skip
        for rec in bundle.sessions
    }
    Session.objects.bulk_create(sessions.values(), batch_size=BATCH)
    presences = {}
    for rec in bundle.presences:
        pk = official("presences", rec.official_id)
        session = sessions.get(rec.session_key)
        if pk and session:
            presences[(session.pk, pk)] = Presence(
                session=session, official_id=pk, **_src(rec.source)
            )
    Presence.objects.bulk_create(presences.values(), batch_size=BATCH)

    votings = {
        rec.natural_key: Voting(
            natural_key=rec.natural_key,
            house=house,
            external_id=rec.external_id,
            day=rec.day,
            body=rec.body,
            description=rec.description,
            secret=rec.secret,
            identification=rec.identification,
            **_src(rec.source),
        )  # fmt: skip
        for rec in bundle.votings
    }
    Voting.objects.bulk_create(votings.values(), batch_size=BATCH)
    ballots = {}
    for rec in bundle.ballots:
        pk = official("ballots", rec.official_id)
        voting = votings.get(rec.voting_key)
        if pk and voting:
            ballots[(voting.pk, pk)] = Ballot(
                voting=voting, official_id=pk, option_raw=rec.option_raw,
                option_text=rec.option_text, category=rec.category, **_src(rec.source),
            )  # fmt: skip
    Ballot.objects.bulk_create(ballots.values(), batch_size=BATCH)

    memberships = {}
    for rec in bundle.memberships:
        pk = official("memberships", rec.official_id)
        if pk:
            memberships[rec.natural_key] = Membership(
                natural_key=rec.natural_key, official_id=pk, house=house,
                body_external_id=rec.body_external_id, body_acronym=rec.body_acronym,
                body_name=rec.body_name, body_house=rec.body_house, role=rec.role,
                start=rec.start, end=rec.end, **_src(rec.source),
            )  # fmt: skip
    Membership.objects.bulk_create(memberships.values(), batch_size=BATCH)

    speeches = {}
    for rec in bundle.speeches:
        pk = official("speeches", rec.official_id)
        if pk:
            speeches[rec.natural_key] = Speech(
                natural_key=rec.natural_key, official_id=pk, house=house, day=rec.day,
                type_code=rec.type_code, type_text=rec.type_text, phase=rec.phase,
                session_external_id=rec.session_external_id, **_src(rec.source),
            )  # fmt: skip
    Speech.objects.bulk_create(speeches.values(), batch_size=BATCH)

    counts = {
        "bills": len(bills), "bill_authorships": len(links), "sessions": len(sessions),
        "presences": len(presences), "votings": len(votings), "ballots": len(ballots),
        "memberships": len(memberships), "speeches": len(speeches),
    }  # fmt: skip
    counts.update({f"skipped ({k}: official not loaded)": v for k, v in skipped.items()})
    return counts
