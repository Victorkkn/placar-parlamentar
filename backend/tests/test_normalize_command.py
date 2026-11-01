"""normalize_current end to end: a temporary cache built from the REAL fixtures, offline."""

import io
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from placar.legislators.models import Official, ServicePeriod
from placar.sources.cache import RawCache

FIXTURES = Path(__file__).resolve().parent / "fixtures"
pytestmark = pytest.mark.django_db


def cache_from_fixtures(root: Path) -> None:
    from placar.sources.fixtures import cache_from_fixtures as load

    load(FIXTURES, RawCache(root))


def run(settings, tmp_path) -> str:
    settings.PLACAR = {**settings.PLACAR, "RAW_CACHE_DIR": tmp_path}
    out = io.StringIO()
    call_command("normalize_current", "--date", "2026-11-01", stdout=out)
    return out.getvalue()


def test_normalize_current_offline_from_fixture_cache(settings, tmp_path):
    cache_from_fixtures(tmp_path)
    out = run(settings, tmp_path)
    assert "== camara" in out and "== senado" in out
    assert "unknown values: 0" in out
    assert Official.objects.filter(house="CAMARA").count() == 2
    assert Official.objects.filter(house="SENADO").count() == 3
    assert ServicePeriod.objects.filter(official__house_id=5917).count() == 2
    # Idempotent: a second run gives the same rows.
    before = ServicePeriod.objects.count()
    run(settings, tmp_path)
    assert ServicePeriod.objects.count() == before


def test_normalize_current_fails_clearly_without_cache(settings, tmp_path):
    with pytest.raises(CommandError, match="Run fetch_current first"):
        run(settings, tmp_path)


def test_fixture_snapshot_refuses_non_e2e_database():
    with pytest.raises(CommandError, match="must end with _e2e"):
        call_command("load_fixture_snapshot", stdout=io.StringIO())
