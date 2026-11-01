"""Shared options for the fetch commands."""

from datetime import date

from django.core.management.base import CommandError
from django.utils import timezone


def add_fetch_arguments(parser) -> None:
    parser.add_argument(
        "--refresh", action="store_true", help="Download again even if the cache is fresh."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Fetch details for only the first N people (for small test runs).",
    )
    parser.add_argument(
        "--date", default=None, help="Reference date YYYY-MM-DD (default: today in Brazil)."
    )


def reference_date(value: str | None) -> date:
    if value is None:
        return timezone.localdate()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CommandError(f"--date must be YYYY-MM-DD, got {value!r}") from exc
