"""Read-only public API (Phase C1). Only GET; inputs validated (decision 0012); every number
is returned with its official sources (rule 3). Pages are served from the data snapshot
(decision 0015): no official API is called here.
"""

from __future__ import annotations

import hashlib
import statistics
from datetime import date, timedelta
from fractions import Fraction

from django.core.cache import cache
from ninja import NinjaAPI, Query, Schema, Status
from ninja.errors import HttpError

from placar.core.types import DateWindow, SourceRef
from placar.legislators import selectors as legislators
from placar.metrics import selectors as metric_selectors
from placar.metrics.activity import MetricResult
from placar.metrics.coverage import CoverageResult
from placar.summaries import selectors as summaries

from . import schemas as s

api = NinjaAPI(
    title="Placar Parlamentar API",
    version="1",
    description=(
        "Dados públicos de deputados e senadores federais, com fonte oficial para cada número."
    ),
    urls_namespace="api",
)

EARLIEST = date(1988, 10, 5)  # Constitution (decision 0012)
DEFAULT_MIN_SHARE = 0.5  # Phase C default, approved 2026-11-01
HOUSES = ("CAMARA", "SENADO")
METRICS = {
    "CAMARA": ["plenary_attendance", "bills_authored", "vote_participation", "speeches"],
    "SENADO": ["bills_authored", "vote_participation", "speeches"],
}
ALL_METRICS = METRICS["CAMARA"]
COUNT_METRICS = {"bills_authored", "speeches"}
MAX_COMPARE = 6


# --- helpers --------------------------------------------------------------------------------


def _snapshot_date() -> date | None:
    dates = [load.reference_date for load in legislators.latest_loads() if load.kind == "people"]
    return max(dates) if dates else None


def _window(start: date | None, end: date | None) -> DateWindow:
    snapshot = _snapshot_date()
    if snapshot is None:
        raise HttpError(503, "Dados ainda não carregados.")
    legislature = legislators.legislature_on(snapshot)
    end = end or snapshot
    start = start or (legislature.start if legislature else snapshot - timedelta(days=729))
    if start < EARLIEST:
        raise HttpError(400, f"A data inicial deve ser a partir de {EARLIEST.isoformat()}.")
    if end > snapshot:
        raise HttpError(
            400, f"A data final deve ser até a data dos dados ({snapshot.isoformat()})."
        )
    if start > end:
        raise HttpError(400, "A data inicial deve ser anterior à data final.")
    return DateWindow(start, end)


def _threshold(min_days: int | None, min_share: float | None, window: DateWindow) -> s.Threshold:
    if min_days is not None and min_share is not None:
        raise HttpError(400, "Informe o mínimo em dias ou em proporção, não os dois.")
    if min_days is not None:
        if not 0 <= min_days <= window.days:
            raise HttpError(400, f"O mínimo em dias deve estar entre 0 e {window.days}.")
        return s.Threshold(min_days=min_days)
    share = DEFAULT_MIN_SHARE if min_share is None else min_share
    if not 0 <= share <= 1:
        raise HttpError(400, "A proporção mínima deve estar entre 0 e 1.")
    return s.Threshold(min_share=share)


def _sufficient(cov: CoverageResult, threshold: s.Threshold) -> bool:
    if threshold.min_days is not None:
        return cov.days_in_office >= threshold.min_days
    return cov.share_exact >= Fraction(threshold.min_share or 0).limit_denominator(10_000)


def _src(ref: SourceRef) -> s.Source:
    return s.Source(api_url=ref.api_url, public_url=ref.public_url, label=ref.label)


def _window_out(window: DateWindow) -> s.Window:
    return s.Window(start=window.start, end=window.end, days=window.days)


def _coverage_out(cov: CoverageResult) -> s.CoverageOut:
    return s.CoverageOut(
        days_in_office=cov.days_in_office,
        window_days=cov.window_days,
        share=round(cov.share, 6),
        periods=[s.PeriodOut(start=p.start, end=p.end) for p in cov.periods],
        sources=[_src(r) for r in cov.sources],
    )


def _metric_out(
    key: str, result: MetricResult | None, cov: CoverageResult, loaded: bool = True
) -> s.MetricOut:
    if not loaded:
        # Decision 0015: never show a number for data that is not loaded yet.
        return s.MetricOut(key=key, available=False, reason="not_loaded_yet")
    if result is None:
        return s.MetricOut(key=key, available=False, reason="not_in_official_data")
    value = result.value
    per_year = _per_year(key, result, cov)
    return s.MetricOut(
        key=key,
        available=True,
        numerator=result.numerator,
        denominator=result.denominator,
        value=None if value is None else round(float(value), 6),
        per_365_days_in_office=per_year,
        details=result.details,
        sources=[_src(r) for r in result.sources],
    )


def _per_year(key: str, result: MetricResult, cov: CoverageResult) -> float | None:
    if key in COUNT_METRICS and cov.days_in_office:
        return round(result.numerator * 365 / cov.days_in_office, 4)
    return None


def _aggregate_value(key: str, result: MetricResult | None, cov: CoverageResult) -> float | None:
    """The number a party aggregate uses, without building the member's full output
    (sources included), which made the parties view slow on the full snapshot."""
    if result is None:
        return None
    if key in COUNT_METRICS:
        return _per_year(key, result, cov)
    value = result.value
    return None if value is None else round(float(value), 6)


def _snapshot_stamp() -> str:
    """Changes whenever any data load is recorded, so cached results never outlive their data."""
    loads = sorted(
        f"{x.house}:{x.kind}:{x.loaded_at.isoformat()}" for x in legislators.latest_loads()
    )
    return hashlib.sha256("|".join(loads).encode()).hexdigest()[:16]


def _bulk_metrics(
    house: str, window: DateWindow, coverages: dict[int, CoverageResult]
) -> dict[int, dict[str, MetricResult | None]]:
    """Metrics of every official in office in the window, computed once per house, window and
    snapshot and kept in the process cache (about 15 s for the full Câmara; the threshold only
    filters the result, so changing it is instant). Nothing about visitors is stored."""
    key = f"bulk:{house}:{window.start}:{window.end}:{_snapshot_stamp()}"
    result = cache.get(key)
    if result is None:
        in_office = {pk: cov for pk, cov in coverages.items() if cov.days_in_office}
        result = metric_selectors.activity_metrics_bulk(house, window, window.end, in_office)
        cache.set(key, result, timeout=None)
    return result


def _party_in_window(affiliations: list[legislators.Affiliation], window: DateWindow) -> str | None:
    overlapping = [
        a for a in affiliations
        if a.period.start <= window.end and (a.period.end is None or a.period.end >= window.start)
    ]  # fmt: skip
    return overlapping[-1].party if overlapping else None


def _summary(official, cov, affiliations, threshold) -> s.OfficialSummary:
    return s.OfficialSummary(
        id=official.pk,
        house=official.house,
        house_id=official.house_id,
        name=official.parliamentary_name,
        state=official.state,
        party=_party_in_window(affiliations, cov.window),
        page_url=official.page_url or None,
        coverage=_coverage_out(cov),
        sufficient=_sufficient(cov, threshold),
        sources=[_src(official.source)],
    )


def _activity_loaded(house: str) -> bool:
    return any(x.house == house and x.kind == "activity" for x in legislators.latest_loads())


def _house(value: str | None) -> str | None:
    if value is None:
        return None
    upper = value.upper()
    if upper not in HOUSES:
        raise HttpError(400, "Casa deve ser CAMARA ou SENADO.")
    return upper


# --- endpoints ------------------------------------------------------------------------------


@api.get("/meta", response=s.MetaOut)
def meta(request):
    snapshot = _snapshot_date()
    legislature = legislators.legislature_on(snapshot) if snapshot else None
    loads = legislators.latest_loads()
    houses = []
    for house in HOUSES:
        people = next((x for x in loads if x.house == house and x.kind == "people"), None)
        act = next((x for x in loads if x.house == house and x.kind == "activity"), None)
        fetched = [x.data_fetched_until for x in (people, act) if x and x.data_fetched_until]
        houses.append(
            s.HouseMeta(
                house=house,
                people_loaded_on=people.reference_date if people else None,
                activity_loaded_on=act.reference_date if act else None,
                data_fetched_until=max(fetched) if fetched else None,
                metrics=METRICS[house] if act else [],
            )
        )
    return s.MetaOut(
        snapshot_date=snapshot,
        legislature=legislature.number if legislature else None,
        legislature_start=legislature.start if legislature else None,
        legislature_end=legislature.end if legislature else None,
        earliest_date=EARLIEST,
        houses=houses,
        default_min_share=DEFAULT_MIN_SHARE,
    )


class OfficialsQuery(Schema):
    house: str | None = None
    state: str | None = None
    party: str | None = None
    q: str | None = None
    start: date | None = None
    end: date | None = None
    min_days: int | None = None
    min_share: float | None = None
    include_not_in_office: bool = False
    page: int = 1
    page_size: int = 50


class OfficialsPageOut(s.OfficialsPage):
    not_in_office: int


@api.get("/officials", response=OfficialsPageOut)
def list_officials(request, query: Query[OfficialsQuery]):
    if not 1 <= query.page <= 10_000 or not 1 <= query.page_size <= 100:
        raise HttpError(400, "Página inválida (tamanho entre 1 e 100).")
    if query.state is not None and (len(query.state) != 2 or not query.state.isalpha()):
        raise HttpError(400, "UF deve ter duas letras.")
    if query.q is not None and len(query.q) > 100:
        raise HttpError(400, "Busca muito longa.")
    if query.party is not None and len(query.party) > 40:
        raise HttpError(400, "Sigla de partido muito longa.")
    house = _house(query.house)
    window = _window(query.start, query.end)
    threshold = _threshold(query.min_days, query.min_share, window)
    today = window.end
    coverages = metric_selectors.coverage_bulk(house, window, today)
    affiliations = legislators.affiliations_by_official(house)
    rows, not_in_office = [], 0
    needle = (query.q or "").casefold()
    for official in legislators.officials(house).order_by("parliamentary_name"):
        cov = coverages[official.pk]
        summary = _summary(official, cov, affiliations.get(official.pk, []), threshold)
        if query.state and official.state.upper() != query.state.upper():
            continue
        if query.party and (summary.party or "").upper() != query.party.upper():
            continue
        if needle and needle not in official.parliamentary_name.casefold():
            continue
        if cov.days_in_office == 0 and not query.include_not_in_office:
            not_in_office += 1
            continue
        rows.append(summary)
    first = (query.page - 1) * query.page_size
    return OfficialsPageOut(
        window=_window_out(window),
        threshold=threshold,
        total=len(rows),
        page=query.page,
        page_size=query.page_size,
        items=rows[first : first + query.page_size],
        not_in_office=not_in_office,
    )


def _summary_out(official_id: int, window: DateWindow) -> s.SummaryOut:
    shown = summaries.summary_for(official_id, window, window.end)
    return s.SummaryOut(
        kind=shown.kind,
        sentences=[
            s.SummarySentenceOut(text=x.text, sources=[_src(r) for r in x.sources])
            for x in shown.sentences
        ],
    )


def _detail(official, window: DateWindow, threshold: s.Threshold) -> s.OfficialDetail:
    cov = metric_selectors.coverage(official.pk, window, window.end)
    affiliations = legislators.affiliations_by_official(official.house).get(official.pk, [])
    results = metric_selectors.activity_metrics(official.pk, window, window.end)
    periods = [
        s.ServicePeriodOut(start=p.start, end=p.end, start_reason=p.start_reason,
                           end_reason=p.end_reason, sources=[_src(p.source)])
        for p in official.service_periods.order_by("start")
    ]  # fmt: skip
    return s.OfficialDetail(
        window=_window_out(window),
        threshold=threshold,
        official=_summary(official, cov, affiliations, threshold),
        periods=periods,
        affiliations=[
            s.AffiliationOut(
                party=a.party,
                start=a.period.start,
                end=a.period.end,
                precision=a.precision,
                sources=[_src(a.source)],
            )
            for a in affiliations
        ],  # fmt: skip
        metrics=[
            _metric_out(k, results.get(k), cov, _activity_loaded(official.house))
            for k in ALL_METRICS
        ],
    )


@api.get("/officials/{official_id}", response={200: s.OfficialDetail, 404: s.ErrorOut})
def official_detail(
    request,
    official_id: int,
    start: date | None = None,
    end: date | None = None,
    min_days: int | None = None,
    min_share: float | None = None,
):
    official = legislators.official_by_id(official_id) if official_id > 0 else None
    if official is None:
        return Status(404, {"detail": "Parlamentar não encontrado."})
    window = _window(start, end)
    detail = _detail(official, window, _threshold(min_days, min_share, window))
    detail.summary = _summary_out(official.pk, window)
    return detail


@api.get("/compare", response=s.CompareOut)
def compare(
    request,
    ids: str,
    start: date | None = None,
    end: date | None = None,
    min_days: int | None = None,
    min_share: float | None = None,
):
    parts = [p.strip() for p in ids.split(",") if p.strip()]
    if not all(p.isdigit() and 0 < int(p) < 10**9 for p in parts):
        raise HttpError(400, "ids deve ser uma lista de números separados por vírgula.")
    unique = list(dict.fromkeys(int(p) for p in parts))
    if not 2 <= len(unique) <= MAX_COMPARE:
        raise HttpError(400, f"Compare de 2 a {MAX_COMPARE} parlamentares.")
    officials = [legislators.official_by_id(pk) for pk in unique]
    if any(o is None for o in officials):
        raise HttpError(404, "Parlamentar não encontrado.")
    window = _window(start, end)
    threshold = _threshold(min_days, min_share, window)
    return s.CompareOut(
        window=_window_out(window),
        threshold=threshold,
        officials=[_detail(o, window, threshold) for o in officials],
    )


def _members_on(day, coverages, affiliations, party) -> set[int]:
    members = set()
    for pk, cov in coverages.items():
        if not any(p.start <= day <= p.end for p in cov.periods):
            continue
        for a in affiliations.get(pk, []):
            if (
                a.party == party
                and a.period.start <= day
                and (a.period.end is None or a.period.end >= day)
            ):
                members.add(pk)
    return members


@api.get("/parties", response=s.PartiesOut)
def parties(
    request,
    house: str,
    start: date | None = None,
    end: date | None = None,
    min_days: int | None = None,
    min_share: float | None = None,
):
    house_code = _house(house)
    window = _window(start, end)
    threshold = _threshold(min_days, min_share, window)
    coverages = metric_selectors.coverage_bulk(house_code, window, window.end)
    affiliations = legislators.affiliations_by_official(house_code)

    members: dict[str, set[int]] = {}
    for pk, cov in coverages.items():
        for period in cov.periods:
            for a in affiliations.get(pk, []):
                a_end = a.period.end or window.end
                if a.period.start <= period.end and a_end >= period.start:
                    members.setdefault(a.party, set()).add(pk)
    sufficient = {
        pk for pk, cov in coverages.items() if cov.days_in_office and _sufficient(cov, threshold)
    }
    loaded = _activity_loaded(house_code)
    computed = _bulk_metrics(house_code, window, coverages) if loaded else {}

    rows = []
    for party, pks in sorted(members.items()):
        at_start = _members_on(window.start, {k: coverages[k] for k in pks}, affiliations, party)
        at_end = _members_on(window.end, {k: coverages[k] for k in pks}, affiliations, party)
        counted = sorted(pks & sufficient)
        aggregates = []
        for key in ALL_METRICS:
            if key not in METRICS[house_code] or not loaded:
                aggregates.append(s.Aggregate(key=key, available=False, members_counted=0))
                continue
            values = []
            for pk in counted:
                value = _aggregate_value(key, computed[pk][key], coverages[pk])
                if value is not None:
                    values.append(value)
            aggregates.append(
                s.Aggregate(
                    key=key,
                    available=True,
                    members_counted=len(values),
                    median=round(statistics.median(values), 6) if values else None,
                    minimum=min(values) if values else None,
                    maximum=max(values) if values else None,
                )
            )
        rows.append(
            s.PartyRow(
                party=party,
                member_ids=sorted(pks),
                members_in_window=len(pks),
                members_at_start=len(at_start),
                members_at_end=len(at_end),
                membership_changed=len(pks) != len(at_start) or at_start != at_end,
                members_with_sufficient_data=len(counted),
                aggregates=aggregates,
            )
        )
    return s.PartiesOut(
        window=_window_out(window), threshold=threshold, house=house_code, parties=rows
    )
