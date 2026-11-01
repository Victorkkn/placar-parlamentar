"""Thin shell: loads data through other apps' selectors (decision 0007) for the pure metrics."""

from __future__ import annotations

from datetime import date

from django.utils import timezone

from placar.core.types import DateWindow
from placar.legislators import selectors as legislators

from .coverage import CoverageResult, coverage_of


def coverage(official_id: int, window: DateWindow, today: date | None = None) -> CoverageResult:
    """Days in office for an official within a window, and the coverage share."""
    return coverage_of(
        legislators.service_periods_for(official_id), window, today or timezone.localdate()
    )
