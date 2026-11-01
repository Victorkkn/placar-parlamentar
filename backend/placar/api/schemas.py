"""Response schemas (Django Ninja / Pydantic). Every number travels with its sources (rule 3)."""

from __future__ import annotations

from datetime import date, datetime

from ninja import Schema


class Source(Schema):
    api_url: str
    public_url: str | None = None
    label: str = ""


class Window(Schema):
    start: date
    end: date
    days: int


class Threshold(Schema):
    min_days: int | None = None
    min_share: float | None = None


class PeriodOut(Schema):
    start: date
    end: date | None


class CoverageOut(Schema):
    days_in_office: int
    window_days: int
    share: float
    periods: list[PeriodOut]
    sources: list[Source]


class MetricOut(Schema):
    key: str
    available: bool
    reason: str | None = None
    numerator: int | None = None
    denominator: int | None = None
    value: float | None = None
    per_365_days_in_office: float | None = None
    details: dict = {}
    sources: list[Source] = []


class OfficialSummary(Schema):
    id: int
    house: str
    house_id: int
    name: str
    state: str
    party: str | None
    photo_url: str | None
    page_url: str | None
    coverage: CoverageOut
    sufficient: bool
    sources: list[Source]


class OfficialsPage(Schema):
    window: Window
    threshold: Threshold
    total: int
    page: int
    page_size: int
    items: list[OfficialSummary]


class ServicePeriodOut(Schema):
    start: date
    end: date | None
    start_reason: str
    end_reason: str
    sources: list[Source]


class AffiliationOut(Schema):
    party: str
    start: date
    end: date | None
    precision: str
    sources: list[Source]


class OfficialDetail(Schema):
    window: Window
    threshold: Threshold
    official: OfficialSummary
    periods: list[ServicePeriodOut]
    affiliations: list[AffiliationOut]
    metrics: list[MetricOut]


class CompareOut(Schema):
    window: Window
    threshold: Threshold
    officials: list[OfficialDetail]


class Aggregate(Schema):
    key: str
    available: bool
    members_counted: int
    median: float | None = None
    minimum: float | None = None
    maximum: float | None = None


class PartyRow(Schema):
    """Counts and aggregates are derived from the listed members; each member's own records
    carry their sources (see /officials/{id})."""

    party: str
    member_ids: list[int]
    members_in_window: int
    members_at_start: int
    members_at_end: int
    membership_changed: bool
    members_with_sufficient_data: int
    aggregates: list[Aggregate]


class PartiesOut(Schema):
    window: Window
    threshold: Threshold
    house: str
    parties: list[PartyRow]


class HouseMeta(Schema):
    house: str
    people_loaded_on: date | None
    activity_loaded_on: date | None
    data_fetched_until: datetime | None
    metrics: list[str]


class MetaOut(Schema):
    snapshot_date: date | None
    legislature: int | None
    legislature_start: date | None
    legislature_end: date | None
    earliest_date: date
    houses: list[HouseMeta]
    default_min_share: float


class ErrorOut(Schema):
    detail: str
