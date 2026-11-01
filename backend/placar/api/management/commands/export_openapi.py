"""Write the API contract to docs/api/openapi.json (decision 0009, item 7)."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from placar.api.api import api

CONTRACT = Path(__file__).resolve().parents[5] / "docs" / "api" / "openapi.json"


def contract_text() -> str:
    return json.dumps(api.get_openapi_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


class Command(BaseCommand):
    help = "Export the OpenAPI description of the public API to docs/api/openapi.json."

    def handle(self, *args, **options):
        CONTRACT.parent.mkdir(parents=True, exist_ok=True)
        CONTRACT.write_text(contract_text(), encoding="utf-8")
        self.stdout.write(f"wrote {CONTRACT}")
