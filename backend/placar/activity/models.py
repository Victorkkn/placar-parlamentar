"""Public activity records (Phase B2). Every record keeps its `SourceRef` (decision 0008).

Rows are written only by `sources` through `activity.services` (decision 0007).
Speech texts and keywords are not stored (decision 0010).
"""

from __future__ import annotations

from django.db import models

from placar.legislators.models import House, Official, SourcedModel


class Bill(SourcedModel):
    natural_key = models.CharField(max_length=80, unique=True)
    house = models.CharField(max_length=6, choices=House.choices)
    external_id = models.CharField(max_length=40)
    type_code = models.CharField(max_length=20, blank=True)
    number = models.PositiveIntegerField(null=True, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    presented_on = models.DateField(null=True, blank=True)
    summary = models.TextField(blank=True)  # official "ementa"; untrusted text, shown escaped
    authors = models.ManyToManyField(Official, related_name="bills", blank=True)


class Session(SourcedModel):
    """A plenary session; for the Câmara, a deliberative plenary event (type 110)."""

    natural_key = models.CharField(max_length=80, unique=True)
    house = models.CharField(max_length=6, choices=House.choices)
    external_id = models.CharField(max_length=40)
    day = models.DateField(null=True, blank=True)
    type_text = models.CharField(max_length=120, blank=True)
    situation = models.CharField(max_length=60, blank=True)


class Presence(SourcedModel):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="presences")
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="presences")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["session", "official"], name="presence_once")
        ]


class Voting(SourcedModel):
    natural_key = models.CharField(max_length=80, unique=True)
    house = models.CharField(max_length=6, choices=House.choices)
    external_id = models.CharField(max_length=40)
    day = models.DateField(null=True, blank=True)
    body = models.CharField(max_length=40, blank=True)
    description = models.TextField(blank=True)  # official text; untrusted, shown escaped
    secret = models.BooleanField(null=True)
    identification = models.CharField(max_length=80, blank=True)


class BallotCategory(models.TextChoices):
    """How a recorded option counts for nominal-vote participation (Phase B2 adjustment 1)."""

    TAKES_PART = "TAKES_PART", "Registrou voto"
    PRESIDING = "PRESIDING", "Presidindo a sessão"
    PRESENT_NO_VOTE = "PRESENT_NO_VOTE", "Presente, sem registrar voto"
    JUSTIFIED_ABSENCE = "JUSTIFIED", "Ausência com motivo oficial"
    ABSENT = "ABSENT", "Não compareceu"
    UNKNOWN = "UNKNOWN", "Não classificado"


class Ballot(SourcedModel):
    voting = models.ForeignKey(Voting, on_delete=models.CASCADE, related_name="ballots")
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="ballots")
    option_raw = models.CharField(max_length=80)
    option_text = models.CharField(max_length=200, blank=True)  # official description, if any
    category = models.CharField(max_length=16, choices=BallotCategory.choices)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["voting", "official"], name="ballot_once")]


class Membership(SourcedModel):
    """Membership in a committee or other body, as listed (committee types: later decision)."""

    natural_key = models.CharField(max_length=160, unique=True)
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="memberships")
    house = models.CharField(max_length=6, choices=House.choices)
    body_external_id = models.CharField(max_length=40, blank=True)
    body_acronym = models.CharField(max_length=60, blank=True)
    body_name = models.CharField(max_length=300, blank=True)
    body_house = models.CharField(max_length=10, blank=True)
    role = models.CharField(max_length=120, blank=True)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)


class Speech(SourcedModel):
    natural_key = models.CharField(max_length=80, unique=True)
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="speeches")
    house = models.CharField(max_length=6, choices=House.choices)
    day = models.DateField(null=True, blank=True)
    type_code = models.CharField(max_length=60, blank=True)
    type_text = models.CharField(max_length=200, blank=True)
    phase = models.CharField(max_length=200, blank=True)
    session_external_id = models.CharField(max_length=40, blank=True)
