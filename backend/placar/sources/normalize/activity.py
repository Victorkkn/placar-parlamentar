"""Activity records → activity bundles (Phase B2). Pure functions; no network, no database.

Vote options are classified with a reviewed table (approved B2 adjustment 1). Options not in
the table are classified UNKNOWN and reported, never guessed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from placar.activity.models import BallotCategory
from placar.activity.services import (
    ActivityBundle,
    BallotRecord,
    BillRecord,
    MembershipRecord,
    PresenceRecord,
    SessionRecord,
    SpeechRecord,
    VotingRecord,
)
from placar.legislators.models import House

from ..clients.camara_activity import (
    BILL_TYPES as CAMARA_BILL_TYPES,
)
from ..clients.camara_activity import (
    CamaraBallot,
    CamaraBill,
    CamaraMembership,
    CamaraPresence,
    CamaraSession,
    CamaraSpeech,
    CamaraVoting,
)
from ..clients.senado_activity import (
    BILL_TYPES as SENADO_BILL_TYPES,
)
from ..clients.senado_activity import (
    SenadoBallot,
    SenadoBill,
    SenadoMembership,
    SenadoSpeech,
    SenadoVoting,
)

TAKES_PART = {"Sim", "Não", "Abstenção", "Obstrução"}
# Senado secret ballots record only that the senator voted. Secret votings are not counted.
SENADO_SECRET_VOTED = {"Votou"}
PRESIDING = {"Artigo 17", "Presidente (art. 51 RISF)"}
SENADO_PRESENT_NO_VOTE = {"P-NRV"}  # "Presente - não registrou voto"
SENADO_ABSENT = {"NCom"}  # "Não compareceu"


@dataclass
class Notes:
    unknown_options: dict[str, int] = field(default_factory=dict)
    other: list[str] = field(default_factory=list)


def classify(option: str | None, official_codes: dict[str, str], notes: Notes) -> tuple[str, str]:
    """Return (category, official description) for a recorded option."""
    value = (option or "").strip()
    if value in TAKES_PART:
        return BallotCategory.TAKES_PART, ""
    if value in SENADO_SECRET_VOTED:
        return BallotCategory.TAKES_PART, ""
    if value in PRESIDING:
        return BallotCategory.PRESIDING, ""
    if value in SENADO_PRESENT_NO_VOTE:
        return BallotCategory.PRESENT_NO_VOTE, ""
    if value in SENADO_ABSENT:
        return BallotCategory.ABSENT, ""
    if value in official_codes:
        return BallotCategory.JUSTIFIED_ABSENCE, official_codes[value]
    notes.unknown_options[value] = notes.unknown_options.get(value, 0) + 1
    return BallotCategory.UNKNOWN, ""


def camara(
    sessions: list[CamaraSession],
    presences: list[CamaraPresence],
    votings: list[CamaraVoting],
    ballots: list[CamaraBallot],
    bills: list[CamaraBill],
    memberships: list[CamaraMembership],
    speeches: list[CamaraSpeech],
) -> tuple[ActivityBundle, Notes]:
    notes = Notes()
    bundle = ActivityBundle(house=House.CAMARA)
    for s in {s.event_id: s for s in sessions}.values():
        bundle.sessions.append(
            SessionRecord(
                f"CAMARA:event:{s.event_id}",
                str(s.event_id),
                s.day,
                s.source,
                s.type_text or "",
                s.situation or "",
            )  # fmt: skip
        )
    for p in presences:
        bundle.presences.append(PresenceRecord(f"CAMARA:event:{p.event_id}", p.deputy_id, p.source))
    # The Câmara API has no secret flag. In a secret ballot it lists who voted but leaves every
    # option empty (data issue 19), so a voting whose recorded options are all empty is secret.
    options: dict[str, set[str]] = {}
    for b in ballots:
        options.setdefault(b.voting_id, set()).add((b.option or "").strip())
    secret_ids = {vid for vid, found in options.items() if found == {""}}
    if secret_ids:
        notes.other.append(f"secret votings (all options empty): {sorted(secret_ids)}")
    for v in {v.voting_id: v for v in votings}.values():
        bundle.votings.append(
            VotingRecord(
                f"CAMARA:voting:{v.voting_id}",
                v.voting_id,
                v.day,
                v.source,
                body=v.body or "",
                description=v.description or "",
                secret=True if v.voting_id in secret_ids else None,
            )  # fmt: skip
        )
    for b in ballots:
        if b.voting_id in secret_ids:
            # A vote was registered; its content is secret. Secret votings are not counted.
            category, text = BallotCategory.TAKES_PART, ""
        else:
            category, text = classify(b.option, {}, notes)
        bundle.ballots.append(
            BallotRecord(
                f"CAMARA:voting:{b.voting_id}",
                b.deputy_id,
                b.option or "",
                category,
                b.source,
                text,
            )  # fmt: skip
        )
    authors: dict[int, set[int]] = {}
    first: dict[int, CamaraBill] = {}
    for bill in bills:
        if bill.type_code not in CAMARA_BILL_TYPES:
            continue
        authors.setdefault(bill.bill_id, set()).add(bill.author_id)
        first.setdefault(bill.bill_id, bill)
    for bill_id, bill in first.items():
        bundle.bills.append(
            BillRecord(
                f"CAMARA:bill:{bill_id}",
                str(bill_id),
                tuple(sorted(authors[bill_id])),
                bill.source,
                bill.type_code or "",
                bill.number,
                bill.year,
                bill.presented_on,
                bill.summary or "",
            )  # fmt: skip
        )
    for m in memberships:
        key = f"CAMARA:member:{m.deputy_id}:{m.body_id}:{m.role}:{m.start}"
        bundle.memberships.append(
            MembershipRecord(
                key,
                m.deputy_id,
                m.source,
                str(m.body_id or ""),
                m.body_acronym or "",
                m.body_name or "",
                "CD",
                m.role or "",
                m.start,
                m.end,
            )  # fmt: skip
        )
    for sp in speeches:
        bundle.speeches.append(
            SpeechRecord(
                sp.key,
                sp.deputy_id,
                sp.day,
                sp.source,
                sp.speech_type or "",
                "",
                sp.phase or "",
                str(sp.event_id or ""),
            )  # fmt: skip
        )
    _dedupe(bundle)
    return bundle, notes


def senado(
    votings: list[SenadoVoting],
    ballots: list[SenadoBallot],
    vote_codes: dict[str, str],
    bills: list[SenadoBill],
    memberships: list[SenadoMembership],
    speeches: list[SenadoSpeech],
) -> tuple[ActivityBundle, Notes]:
    notes = Notes()
    bundle = ActivityBundle(house=House.SENADO)
    kept = {}
    for v in votings:
        if (v.house or "SF") != "SF":
            continue  # Senado plenary only; Congresso sessions are a separate body
        kept[v.voting_code] = v
    for v in kept.values():
        bundle.votings.append(
            VotingRecord(
                f"SENADO:voting:{v.voting_code}",
                str(v.voting_code),
                v.day,
                v.source,
                body="PLEN",
                description=v.description or "",
                secret=v.secret,
                identification=v.identification or "",
            )  # fmt: skip
        )
    for b in ballots:
        if b.voting_code not in kept:
            continue
        category, text = classify(b.option, vote_codes, notes)
        bundle.ballots.append(
            BallotRecord(
                f"SENADO:voting:{b.voting_code}",
                b.senator_code,
                b.option or "",
                category,
                b.source,
                text or (b.option_text or ""),
            )  # fmt: skip
        )
    authors: dict[int, set[int]] = {}
    first: dict[int, SenadoBill] = {}
    for bill in bills:
        if bill.type_code not in SENADO_BILL_TYPES:
            continue
        authors.setdefault(bill.process_id, set()).add(bill.author_code)
        first.setdefault(bill.process_id, bill)
    for pid, bill in first.items():
        bundle.bills.append(
            BillRecord(
                f"SENADO:process:{pid}",
                str(pid),
                tuple(sorted(authors[pid])),
                bill.source,
                bill.type_code or "",
                bill.number,
                bill.year,
                bill.presented_on,
                bill.summary or "",
            )  # fmt: skip
        )
    for m in memberships:
        key = f"SENADO:member:{m.senator_code}:{m.body_code}:{m.role}:{m.start}"
        bundle.memberships.append(
            MembershipRecord(
                key,
                m.senator_code,
                m.source,
                str(m.body_code or ""),
                m.body_acronym or "",
                m.body_name or "",
                m.body_house or "",
                m.role or "",
                m.start,
                m.end,
            )  # fmt: skip
        )
    for sp in speeches:
        bundle.speeches.append(
            SpeechRecord(
                f"SENADO:speech:{sp.speech_code}",
                sp.senator_code,
                sp.day,
                sp.source,
                sp.type_code or "",
                sp.type_text or "",
                "",
                str(sp.session_code or ""),
            )  # fmt: skip
        )
    _dedupe(bundle)
    return bundle, notes


def _dedupe(bundle: ActivityBundle) -> None:
    """The same record can arrive twice (e.g. overlapping pages); keep the first by key."""
    for name in ("memberships", "speeches"):
        seen: dict[str, object] = {}
        for rec in getattr(bundle, name):
            seen.setdefault(rec.natural_key, rec)
        setattr(bundle, name, list(seen.values()))
