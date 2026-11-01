"""Load the recorded fixtures as a small data snapshot, for end-to-end tests (Phase C5).

Refuses to run unless the database name ends with "_e2e", so the real snapshot in the
development database is never replaced (decision 0002: no deleting data without approval).
"""

import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.test.utils import override_settings

from placar.sources.cache import RawCache
from placar.sources.fixtures import cache_from_fixtures

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures"
SNAPSHOT_DATE = "2026-11-01"  # the date the fixtures were recorded


class Command(BaseCommand):
    help = "Load the recorded test fixtures into an *_e2e database (end-to-end tests only)."

    def handle(self, *args, **options):
        name = settings.DATABASES["default"]["NAME"]
        if not str(name).endswith("_e2e"):
            raise CommandError(
                f"refusing to load fixtures into database {name!r}: name must end with _e2e"
            )
        call_command("migrate", verbosity=0)
        with tempfile.TemporaryDirectory() as tmp:
            count = cache_from_fixtures(FIXTURES, RawCache(Path(tmp)))
            with override_settings(PLACAR={**settings.PLACAR, "RAW_CACHE_DIR": Path(tmp)}):
                call_command("normalize_current", "--date", SNAPSHOT_DATE, stdout=self.stdout)
        self.stdout.write(f"loaded {count} fixtures into {name}")
