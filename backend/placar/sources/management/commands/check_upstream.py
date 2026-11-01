"""Compare live official responses with the recorded fixtures (run by hand; live requests)."""

from pathlib import Path

from django.core.management.base import BaseCommand

from placar.sources.cache import split_url
from placar.sources.drift import compare
from placar.sources.fixtures import load_fixture, strip_personal
from placar.sources.http import UpstreamError
from placar.sources.runner import make_api_client


class Command(BaseCommand):
    help = "List field differences between live API responses and the recorded fixtures."

    def add_arguments(self, parser):
        root = Path(__file__).resolve().parents[5]
        parser.add_argument("--fixtures", default=str(root / "backend" / "tests" / "fixtures"))

    def handle(self, *args, **options):
        paths = sorted(Path(options["fixtures"]).rglob("*.json"))
        if not paths:
            self.stdout.write("no fixtures found; record them first")
            return
        client = make_api_client()
        changed = 0
        try:
            for path in paths:
                fixture = load_fixture(path)
                url, params = split_url(fixture["url"], fixture.get("params"))
                try:
                    live = client.get_json(url, params).body
                except UpstreamError as exc:
                    self.stdout.write(f"{path.name}: could not fetch ({exc})")
                    continue
                # Compare like with like: drop personal fields as the recorder did.
                live, _ = strip_personal(live)
                drift = compare(fixture["_fixture"]["case"], fixture["body"], live)
                if drift.changed:
                    changed += 1
                    self.stdout.write(f"{path.name}: CHANGED")
                    self.stdout.writelines(f"  + {p}\n" for p in drift.added)
                    self.stdout.writelines(f"  - {p}\n" for p in drift.removed)
                else:
                    self.stdout.write(f"{path.name}: same structure")
        finally:
            client.close()
        self.stdout.write(f"{changed} of {len(paths)} fixtures differ from the live API")
