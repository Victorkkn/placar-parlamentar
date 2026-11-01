"""Time in office within a window (Phase B, `coverage(official, window)`).

Pure functions on `core` types ("functional core", decision 0007). Rules (decisions 0008, 0014):
- Periods include both their first and last day; an open period runs until `today`.
- Overlapping or touching periods are merged, so no day is counted twice.
- Party switches have no effect; leaves count only as each house's own record says, which is
  already reflected in the stored periods.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction

from placar.core.types import DateWindow, Period, SourceRef

ONE_DAY = timedelta(days=1)


@dataclass(frozen=True)
class CoverageResult:
    window: DateWindow
    days_in_office: int
    periods: tuple[Period, ...]  # merged and clipped to the window, all closed
    sources: tuple[SourceRef, ...]

    @property
    def window_days(self) -> int:
        return self.window.days

    @property
    def share_exact(self) -> Fraction:
        return Fraction(self.days_in_office, self.window.days)

    @property
    def share(self) -> float:
        return float(self.share_exact)


def close(period: Period, today: date) -> Period | None:
    """Give an open period an end of `today`. Returns None if it starts after `today`."""
    if period.start > today:
        return None
    return Period(period.start, period.end if period.end is not None else today)


def clip(period: Period, window: DateWindow) -> Period | None:
    if period.end is None:
        raise ValueError("clip expects a closed period")
    start, end = max(period.start, window.start), min(period.end, window.end)
    return Period(start, end) if start <= end else None


def merge(periods: Iterable[Period]) -> list[Period]:
    """Merge closed periods that overlap or touch (end + 1 day >= next start)."""
    ordered = sorted(periods, key=lambda p: (p.start, p.end))
    merged: list[Period] = []
    for p in ordered:
        if p.end is None:
            raise ValueError("merge expects closed periods")
        if merged and p.start <= merged[-1].end + ONE_DAY:
            last = merged[-1]
            merged[-1] = Period(last.start, max(last.end, p.end))
        else:
            merged.append(p)
    return merged


def days(periods: Iterable[Period]) -> int:
    return sum((p.end - p.start).days + 1 for p in periods)


def coverage_of(
    periods: Iterable[tuple[Period, SourceRef]], window: DateWindow, today: date
) -> CoverageResult:
    used: list[Period] = []
    sources: list[SourceRef] = []
    for period, source in periods:
        closed = close(period, today)
        clipped = clip(closed, window) if closed else None
        if clipped is not None:
            used.append(clipped)
            if source not in sources:
                sources.append(source)
    merged = merge(used)
    return CoverageResult(
        window=window, days_in_office=days(merged), periods=tuple(merged), sources=tuple(sources)
    )
