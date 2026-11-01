"""First activity metrics (Phase B2), computed only on days the official was in office.

Pure functions (decision 0007). Definitions follow decision 0014 and the approved B2 adjustments:
- plenary attendance (Câmara only): sessions with registered presence / deliberative plenary
  sessions held on days in office;
- bills authored: bills of the counted types presented on days in office (co-authors count);
- nominal-vote participation: votes with a recorded option (Sim, Não, Abstenção, Obstrução) /
  nominal, non-secret votes held on days in office, excluding votes the official presided;
- speeches: speeches registered on days in office.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from fractions import Fraction

from placar.core.types import Period, SourceRef

from .coverage import CoverageResult, days, merge

BILL_TYPES = frozenset({"PL", "PLP", "PEC", "PDL"})  # decision 0014


class Category:
    """Mirror of activity.models.BallotCategory values (metrics does not import models)."""

    TAKES_PART = "TAKES_PART"
    PRESIDING = "PRESIDING"
    PRESENT_NO_VOTE = "PRESENT_NO_VOTE"
    JUSTIFIED = "JUSTIFIED"
    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Dated:
    key: str
    day: date | None
    source: SourceRef
    kind: str = ""


@dataclass(frozen=True)
class MetricResult:
    metric: str
    coverage: CoverageResult
    numerator: int
    denominator: int | None
    sources: tuple[SourceRef, ...]
    details: dict = field(default_factory=dict)

    @property
    def value(self) -> Fraction | None:
        if self.denominator is None:
            return Fraction(self.numerator)
        if self.denominator == 0:
            return None  # nothing to measure in the period in office
        return Fraction(self.numerator, self.denominator)


def in_office(day: date | None, periods: Iterable[Period]) -> bool:
    return day is not None and any(p.start <= day <= p.end for p in periods)


def _unique(refs: Iterable[SourceRef]) -> tuple[SourceRef, ...]:
    seen: dict[tuple[str, str], SourceRef] = {}
    for ref in refs:
        seen.setdefault((ref.api_url, ref.cache_key), ref)
    return tuple(seen.values())


def plenary_attendance(
    coverage: CoverageResult, sessions: Iterable[Dated], present: Mapping[str, SourceRef]
) -> MetricResult:
    held = [s for s in sessions if in_office(s.day, coverage.periods)]
    attended = [s for s in held if s.key in present]
    sources = _unique([*(s.source for s in held), *(present[s.key] for s in attended)])
    return MetricResult("plenary_attendance", coverage, len(attended), len(held), sources)


def bills_authored(
    coverage: CoverageResult, bills: Iterable[Dated], types: frozenset[str] = BILL_TYPES
) -> MetricResult:
    counted = [b for b in bills if b.kind in types and in_office(b.day, coverage.periods)]
    return MetricResult(
        "bills_authored", coverage, len(counted), None, _unique(b.source for b in counted)
    )


def vote_participation(
    coverage: CoverageResult,
    votings: Iterable[Dated],
    ballots: Mapping[str, tuple[str, str, SourceRef]],
) -> MetricResult:
    held = [v for v in votings if in_office(v.day, coverage.periods)]
    presided = [v for v in held if ballots.get(v.key, ("",))[0] == Category.PRESIDING]
    counted = [v for v in held if v not in presided]
    took_part = [v for v in counted if ballots.get(v.key, ("",))[0] == Category.TAKES_PART]
    by_category: dict[str, int] = {}
    for v in counted:
        category = ballots[v.key][0] if v.key in ballots else "NO_RECORD"
        by_category[category] = by_category.get(category, 0) + 1
    sources = _unique([*(v.source for v in counted), *(ballots[v.key][2] for v in took_part)])
    return MetricResult(
        "vote_participation",
        coverage,
        len(took_part),
        len(counted),
        sources,
        details={"presided_excluded": len(presided), "by_category": by_category},
    )


def speeches(coverage: CoverageResult, items: Iterable[Dated]) -> MetricResult:
    counted = [s for s in items if in_office(s.day, coverage.periods)]
    return MetricResult(
        "speeches", coverage, len(counted), None, _unique(s.source for s in counted)
    )


def leave_days(coverage: CoverageResult, leaves: Iterable[Period], today: date) -> int:
    """Days on leave inside the window, overlapping leaves merged (decision 0014)."""
    window = coverage.window
    clipped = []
    for leave in leaves:
        end = min(leave.end or today, today, window.end)
        start = max(leave.start, window.start)
        if start <= end:
            clipped.append(Period(start, end))
    return days(merge(clipped))
