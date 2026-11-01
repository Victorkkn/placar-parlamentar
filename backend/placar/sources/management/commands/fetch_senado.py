from django.core.management.base import BaseCommand

from placar.sources.clients.senado import SenadoClient
from placar.sources.runner import fetch_senado, format_report, make_fetcher

from ._common import add_fetch_arguments, reference_date


class Command(BaseCommand):
    help = "Fetch the current legislature's senators, mandates, leaves and affiliations."

    def add_arguments(self, parser):
        add_fetch_arguments(parser)

    def handle(self, *args, **options):
        client = SenadoClient(make_fetcher("senado"), refresh=options["refresh"])
        try:
            report = fetch_senado(
                client,
                reference_date(options["date"]),
                limit=options["limit"],
                progress=self.stdout.write,
            )
        finally:
            client.fetcher.client.close()
        self.stdout.write(format_report([report]))
