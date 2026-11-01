from django.core.management.base import BaseCommand

from placar.sources.clients.camara import CamaraClient
from placar.sources.runner import fetch_camara, format_report, make_fetcher

from ._common import add_fetch_arguments, reference_date


class Command(BaseCommand):
    help = "Fetch the current legislature's deputies and their history into the raw cache."

    def add_arguments(self, parser):
        add_fetch_arguments(parser)

    def handle(self, *args, **options):
        client = CamaraClient(make_fetcher("camara"), refresh=options["refresh"])
        try:
            report = fetch_camara(
                client,
                reference_date(options["date"]),
                limit=options["limit"],
                progress=self.stdout.write,
            )
        finally:
            client.fetcher.client.close()
        self.stdout.write(format_report([report]))
