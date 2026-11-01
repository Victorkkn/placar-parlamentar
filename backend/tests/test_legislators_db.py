"""Database tests (PostgreSQL test database): storing bundles and coverage on real cases."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction

from placar.core.types import DateWindow
from placar.legislators.models import Leave, Official, ServicePeriod
from placar.legislators.selectors import get_official
from placar.legislators.services import replace_house
from placar.metrics.selectors import coverage

from .test_normalize import camara_bundle, senado_bundle

pytestmark = pytest.mark.django_db
TODAY = date(2026, 11, 1)
LEG57 = DateWindow(date(2023, 2, 1), date(2027, 1, 31))


def load_both():
    replace_house(senado_bundle()[0])
    replace_house(camara_bundle()[0])


def test_replace_is_idempotent():
    load_both()
    first = (Official.objects.count(), ServicePeriod.objects.count(), Leave.objects.count())
    load_both()
    assert (Official.objects.count(), ServicePeriod.objects.count(), Leave.objects.count()) == first


def test_every_stored_period_has_a_source():
    load_both()
    for period in ServicePeriod.objects.all():
        ref = period.source
        assert ref.api_url.startswith("https://") and len(ref.cache_key) == 64


def test_coverage_real_senado_mandate_526():
    load_both()
    titular = get_official("SENADO", 4545)
    alternate = get_official("SENADO", 5917)
    second = get_official("SENADO", 5918)
    assert coverage(titular.pk, LEG57, TODAY).days_in_office == 1  # 2023-09-04 only
    result = coverage(alternate.pk, LEG57, TODAY)
    assert result.days_in_office == 1370  # 2023-02-01 .. 2026-11-01, merged at 2023-09-04
    assert result.window_days == 1461
    assert coverage(second.pk, LEG57, TODAY).days_in_office == 0


def test_coverage_real_camara_220593_vacancy():
    load_both()
    deputy = get_official("CAMARA", 220593)
    assert coverage(deputy.pk, LEG57, TODAY).days_in_office == 701  # 2023-02-01 .. 2025-01-01


def test_period_dates_constraint():
    load_both()
    official = Official.objects.first()
    with pytest.raises(IntegrityError), transaction.atomic():
        ServicePeriod.objects.create(
            natural_key="bad", official=official, start=date(2024, 2, 1), end=date(2024, 1, 1),
            start_reason="UNKNOWN", source_api_url="https://x.camara.leg.br/", source_cache_file_id="0" * 64,
        )  # fmt: skip
