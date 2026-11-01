"""Officials, parties, mandates and time in office (decision 0008).

Every model that holds official data stores its `SourceRef` (official API URL, raw cache file id,
public page URL, label). Raw official codes and texts are kept next to normalized values.
Rows are written only by `sources` through `legislators.services` (decision 0007).
"""

from __future__ import annotations

from django.db import models
from django.db.models import F, Q

from placar.core.types import SourceRef


class House(models.TextChoices):
    CAMARA = "CAMARA", "Câmara dos Deputados"
    SENADO = "SENADO", "Senado Federal"


class SourcedModel(models.Model):
    source_api_url = models.URLField(max_length=500)
    source_cache_file_id = models.CharField(max_length=64)
    source_public_url = models.URLField(max_length=500, blank=True)
    source_label = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True

    @property
    def source(self) -> SourceRef:
        return SourceRef(
            api_url=self.source_api_url,
            cache_key=self.source_cache_file_id,
            public_url=self.source_public_url or None,
            label=self.source_label,
        )


class Legislature(SourcedModel):
    number = models.PositiveSmallIntegerField(unique=True)
    start = models.DateField()
    end = models.DateField()

    class Meta:
        ordering = ["number"]
        constraints = [
            models.CheckConstraint(condition=Q(end__gte=F("start")), name="legislature_dates")
        ]

    def __str__(self) -> str:
        return f"Legislatura {self.number}"


class Party(models.Model):
    """A party as named in the official data. Renames and mergers are not inferred (0008)."""

    acronym = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=200, blank=True)
    camara_id = models.PositiveIntegerField(null=True, blank=True)
    senado_code = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["acronym"]

    def __str__(self) -> str:
        return self.acronym


class Official(SourcedModel):
    """One person as a member of one house. Not linked across houses (0008, rule 8)."""

    house = models.CharField(max_length=6, choices=House.choices)
    house_id = models.PositiveIntegerField()
    parliamentary_name = models.CharField(max_length=200)
    state = models.CharField(max_length=2, blank=True)
    page_url = models.URLField(max_length=500, blank=True)

    class Meta:
        ordering = ["house", "parliamentary_name"]
        constraints = [
            models.UniqueConstraint(fields=["house", "house_id"], name="official_house_id")
        ]

    def __str__(self) -> str:
        return f"{self.parliamentary_name} ({self.get_house_display()})"


class Participation(models.TextChoices):
    TITULAR = "TITULAR", "Titular"
    ALTERNATE = "ALTERNATE", "Suplente"
    UNKNOWN = "UNKNOWN", "Desconhecido"


class Mandate(SourcedModel):
    natural_key = models.CharField(max_length=120, unique=True)
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="mandates")
    house = models.CharField(max_length=6, choices=House.choices)
    external_code = models.PositiveIntegerField(null=True, blank=True)
    state = models.CharField(max_length=2, blank=True)
    participation = models.CharField(max_length=10, choices=Participation.choices)
    participation_raw = models.CharField(max_length=100, blank=True)
    alternate_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    legislatures = models.ManyToManyField(Legislature, related_name="mandates", blank=True)
    nominal_start = models.DateField(null=True, blank=True)
    nominal_end = models.DateField(null=True, blank=True)
    titular = models.ForeignKey(
        Official,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="alternate_mandates",
    )


class StartReason(models.TextChoices):
    ELECTED_OATH = "ELECTED_OATH", "Posse de eleito titular"
    ALTERNATE_OATH = "ALTERNATE_OATH", "Posse de suplente"
    ALTERNATE_AS_TITULAR = "ALTERNATE_AS_TITULAR", "Posse de suplente como titular"
    RETURN = "RETURN", "Reassunção"
    MESA_DECISION = (
        "MESA_DECISION",
        "Decisão da Mesa (recontagem, retotalização ou restabelecimento)",
    )
    NOT_GIVEN = "NOT_GIVEN", "Não informado pela fonte"
    UNKNOWN = "UNKNOWN", "Desconhecido"


class EndReason(models.TextChoices):
    TERM_END = "TERM_END", "Término do mandato ou da legislatura"
    RESIGNATION = "RESIGNATION", "Renúncia"
    DEATH = "DEATH", "Falecimento"
    LOSS_OF_MANDATE = "LOSS_OF_MANDATE", "Perda ou cassação do mandato"
    LEAVE = "LEAVE", "Licença"
    EXECUTIVE_OFFICE = "EXECUTIVE_OFFICE", "Afastamento para cargo no Executivo"
    TITULAR_RETURNED = "TITULAR_RETURNED", "Retorno do titular"
    SUSPENSION = "SUSPENSION", "Suspensão"
    COURT_DECISION = "COURT_DECISION", "Decisão judicial"
    RECOUNT = "RECOUNT", "Recontagem ou retotalização de votos"
    OTHER_ABSENCE = "OTHER_ABSENCE", "Outro afastamento"
    UNKNOWN = "UNKNOWN", "Desconhecido"


class ServicePeriod(SourcedModel):
    """A period actually in office; `end` is null while still in office. Both ends included."""

    natural_key = models.CharField(max_length=120, unique=True)
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="service_periods")
    mandate = models.ForeignKey(
        Mandate, null=True, blank=True, on_delete=models.SET_NULL, related_name="service_periods"
    )
    start = models.DateField()
    end = models.DateField(null=True, blank=True)
    start_reason = models.CharField(max_length=24, choices=StartReason.choices)
    start_reason_raw = models.CharField(max_length=300, blank=True)
    end_reason = models.CharField(max_length=24, choices=EndReason.choices, blank=True)
    end_reason_raw = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["official", "start"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end__isnull=True) | Q(end__gte=F("start")), name="period_dates"
            )
        ]


class Leave(SourcedModel):
    natural_key = models.CharField(max_length=120, unique=True)
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="leaves")
    start = models.DateField()
    end = models.DateField(null=True, blank=True)
    type_code = models.CharField(max_length=60, blank=True)
    type_text = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["official", "start"]


class DatePrecision(models.TextChoices):
    EXACT = "EXACT", "Data exata"
    AT_EVENT = "AT_EVENT", "Conhecida apenas na data de um evento"


class PartyAffiliation(SourcedModel):
    natural_key = models.CharField(max_length=160, unique=True)
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="affiliations")
    party = models.ForeignKey(Party, on_delete=models.PROTECT, related_name="affiliations")
    start = models.DateField()
    end = models.DateField(null=True, blank=True)
    precision = models.CharField(max_length=8, choices=DatePrecision.choices)

    class Meta:
        ordering = ["official", "start"]


class EventKind(models.TextChoices):
    ENTRY = "ENTRY", "Entrada"
    EXIT = "EXIT", "Saída"
    PARTY = "PARTY", "Alteração de partido"
    START_OF_LEGISLATURE = "START", "Nome e partido no início da legislatura"
    OTHER = "OTHER", "Outro registro"
    UNKNOWN = "UNKNOWN", "Desconhecido"


class OfficialEvent(SourcedModel):
    """Câmara history events as given, with how they were read (for audit)."""

    natural_key = models.CharField(max_length=120, unique=True)
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name="events")
    date = models.DateField(null=True, blank=True)
    raw_datetime = models.CharField(max_length=40, blank=True)
    legislature_number = models.PositiveSmallIntegerField(null=True, blank=True)
    kind = models.CharField(max_length=8, choices=EventKind.choices)
    situation = models.CharField(max_length=60, blank=True)
    electoral_condition = models.CharField(max_length=60, blank=True)
    party_acronym = models.CharField(max_length=40, blank=True)
    status_text = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["official", "date", "natural_key"]


class DataLoad(models.Model):
    """When a snapshot of official data was loaded (decision 0015: the date is shown in the app)."""

    house = models.CharField(max_length=6, choices=House.choices)
    kind = models.CharField(max_length=20)  # "people" or "activity"
    reference_date = models.DateField()
    data_fetched_until = models.DateTimeField(null=True, blank=True)
    loaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-loaded_at"]
