from django.core.management.base import BaseCommand

from placar.sources.clients.camara import CamaraClient
from placar.sources.clients.senado import SenadoClient
from placar.sources.runner import (
    cross_check,
    fetch_camara,
    fetch_senado,
    format_report,
    make_fetcher,
)

from ._common import add_fetch_arguments, reference_date


class Command(BaseCommand):
    help = "Fetch deputies and senators of the current legislature into the raw cache."

    def add_arguments(self, parser):
        add_fetch_arguments(parser)

    def handle(self, *args, **options):
        day = reference_date(options["date"])
        camara = CamaraClient(make_fetcher("camara"), refresh=options["refresh"])
        senado = SenadoClient(make_fetcher("senado"), refresh=options["refresh"])
        try:
            reports = [
                fetch_camara(camara, day, limit=options["limit"], progress=self.stdout.write),
                fetch_senado(senado, day, limit=options["limit"], progress=self.stdout.write),
            ]
        finally:
            camara.fetcher.client.close()
            senado.fetcher.client.close()
        self.stdout.write(format_report(reports, cross_check(*reports)))
