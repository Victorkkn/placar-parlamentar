"""Fetch activity data for the current legislature into the raw cache (Phase B2). Live requests."""

from django.core.management.base import BaseCommand

from placar.sources.activity_runner import fetch_camara_activity, fetch_senado_activity
from placar.sources.clients.camara import CamaraClient
from placar.sources.clients.camara_activity import CamaraActivityClient
from placar.sources.clients.senado import SenadoClient
from placar.sources.clients.senado_activity import SenadoActivityClient
from placar.sources.runner import format_report, make_fetcher

from ._common import add_fetch_arguments, reference_date


class Command(BaseCommand):
    help = "Fetch votes, attendance, bills, memberships and speeches into the raw cache."

    def add_arguments(self, parser):
        add_fetch_arguments(parser)
        parser.add_argument("--house", choices=["camara", "senado", "both"], default="both")

    def handle(self, *args, **options):
        day = reference_date(options["date"])
        refresh, limit = options["refresh"], options["limit"]
        reports = []
        if options["house"] in ("senado", "both"):
            fetcher = make_fetcher("senado")
            people = SenadoClient(fetcher, refresh=False)
            activity = SenadoActivityClient(fetcher, refresh=refresh)
            try:
                reports.append(
                    fetch_senado_activity(
                        people, activity, day, limit=limit, progress=self.stdout.write
                    )
                )
            finally:
                fetcher.client.close()
        if options["house"] in ("camara", "both"):
            fetcher = make_fetcher("camara")
            people = CamaraClient(fetcher, refresh=False)
            activity = CamaraActivityClient(fetcher, refresh=refresh)
            try:
                reports.append(
                    fetch_camara_activity(
                        people, activity, day, limit=limit, progress=self.stdout.write
                    )
                )
            finally:
                fetcher.client.close()
        self.stdout.write(format_report(reports))
