"""Load the current legislature from the raw cache into the database (Phase B1). No network."""

from collections import defaultdict
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from placar.legislators.services import record_load, replace_house
from placar.sources.cache import CachedFetcher, CacheMissError, Freshness, RawCache
from placar.sources.clients.camara import CamaraClient
from placar.sources.clients.senado import SenadoClient
from placar.sources.normalize import camara as camara_norm
from placar.sources.normalize import senado as senado_norm

from ._common import reference_date


def offline_fetcher(source: str) -> CachedFetcher:
    root = settings.PLACAR["RAW_CACHE_DIR"]
    if root is None:
        raise CommandError("PLACAR RAW_CACHE_DIR is not set")
    cache = RawCache(Path(root), ttl=timedelta(hours=settings.PLACAR["CACHE_TTL_HOURS"]))
    return CachedFetcher(source, None, cache, offline=True)


class Command(BaseCommand):
    help = "Normalize the cached Câmara and Senado data into the database (offline)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            default=None,
            help="Date used by the fetch run (YYYY-MM-DD); default: today in Brazil.",
        )

    def handle(self, *args, **options):
        day = reference_date(options["date"])
        try:
            reports = [self._camara(day), self._senado(day)]
        except CacheMissError as exc:
            raise CommandError(
                f"not in the cache: {exc}. Run fetch_current first (for the same --date)."
            ) from exc
        for title, counts, notes in reports:
            self.stdout.write(f"== {title}")
            for name, value in counts.items():
                self.stdout.write(f"  {name}: {value}")
            if getattr(notes, "renewals", 0):
                self.stdout.write(
                    f"  exits while already out (renewals, no effect): {notes.renewals}"
                )
            for label, items in (("unknown values", notes.unknown),
                                 ("inconsistencies", notes.inconsistencies)):  # fmt: skip
                self.stdout.write(f"  {label}: {len(items)}")
                for item in items:
                    self.stdout.write(f"    - {item}")

    def _camara(self, day):
        client = CamaraClient(offline_fetcher("camara"))
        leg = client.legislature_on(day)
        freshness = Freshness.DAILY
        rows = client.deputies(leg.number, freshness)
        histories = {i: client.history(i, freshness) for i in sorted({r.deputy_id for r in rows})}
        bundle, notes = camara_norm.normalize(leg, rows, histories)
        notes.unknown += client.notes.items
        counts = replace_house(bundle)
        record_load("CAMARA", "people", day, client.fetcher.stats.latest_fetched_at)
        return "camara", counts, notes

    def _senado(self, day):
        client = SenadoClient(offline_fetcher("senado"))
        leg = client.legislature_on(day)
        freshness = Freshness.DAILY
        listed = client.senators_in_legislature(leg.number, freshness)
        took = client.senators_in_legislature(leg.number, freshness, took_office_only=True)
        current = client.current_senators()
        codes = sorted({s.code for s in took})
        details = defaultdict(dict)
        for code in codes:
            details["mandates"][code] = client.mandates(code, freshness)
            details["leaves"][code] = client.leaves(code, freshness)
            details["affiliations"][code] = client.affiliations(code, freshness)
        data = senado_norm.SenadoInput(
            legislature=leg,
            listed=listed,
            current=current,
            mandates=details["mandates"],
            leaves=details["leaves"],
            affiliations=details["affiliations"],
        )
        bundle, notes = senado_norm.normalize(data)
        notes.unknown += client.notes.items
        counts = replace_house(bundle)
        record_load("SENADO", "people", day, client.fetcher.stats.latest_fetched_at)
        return "senado", counts, notes
