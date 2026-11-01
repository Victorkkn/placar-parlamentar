"""Record test fixtures from the raw cache. Run by the project owner by hand (decision 0011)."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from placar.sources.cache import RawCache
from placar.sources.fixtures import FixtureError, record_case
from placar.sources.runner import make_fetcher


class Command(BaseCommand):
    help = "Copy the cases listed in scripts/fixture_cases.json from the cache into test fixtures."

    def add_arguments(self, parser):
        root = Path(__file__).resolve().parents[5]
        parser.add_argument("--manifest", default=str(root / "scripts" / "fixture_cases.json"))
        parser.add_argument("--out", default=str(root / "backend" / "tests" / "fixtures"))
        parser.add_argument(
            "--fetch",
            action="store_true",
            help="Download cases missing from the cache from the official APIs (live requests).",
        )

    def handle(self, *args, **options):
        manifest = json.loads(Path(options["manifest"]).read_text(encoding="utf-8"))
        root = settings.PLACAR["RAW_CACHE_DIR"]
        if root is None:
            raise CommandError("PLACAR RAW_CACHE_DIR is not set")
        fetchers = {}
        recorded = 0
        try:
            for case in manifest["cases"]:
                source = case["source"]
                fetcher = None
                if options["fetch"]:
                    fetcher = fetchers.setdefault(source, make_fetcher(source))
                try:
                    result = record_case(
                        case,
                        cache=RawCache(Path(root)),
                        out_dir=Path(options["out"]),
                        spec=manifest["spec"],
                        fetcher=fetcher,
                    )
                except FixtureError as exc:
                    raise CommandError(str(exc)) from exc
                recorded += 1
                live = " (downloaded)" if result.fetched_live else ""
                removed = (
                    f", removed {len(result.removed)} personal fields" if result.removed else ""
                )
                self.stdout.write(f"{result.name}: {result.path.name}{live}{removed}")
        finally:
            for fetcher in fetchers.values():
                fetcher.client.close()
        self.stdout.write(f"recorded {recorded} fixtures into {options['out']}")
