"""Remove personal fields from raw cache files written before decision 0019. Offline.

New downloads are cleaned when they are written; this command cleans what was already cached.
It changes nothing else in the files, so their freshness and cache keys stay the same.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from placar.sources.cache import RawCache


class Command(BaseCommand):
    help = "Remove personal and contact fields from the raw cache (decision 0019)."

    def handle(self, *args, **options):
        root = Path(settings.PLACAR["RAW_CACHE_DIR"])
        cache = RawCache(root)
        files = cleaned = removed = 0
        for path in sorted(root.rglob("*.json.gz")):
            files += 1
            count = cache.scrub(path)
            if count:
                cleaned += 1
                removed += count
        self.stdout.write(
            f"checked {files} files; cleaned {cleaned}; removed {removed} personal fields"
        )
