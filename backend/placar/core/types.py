"""Shared plain-Python types (decision 0007: `core` imports nothing from other apps)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


class CoreValueError(ValueError):
    """Raised when a core value is built from invalid data."""


@dataclass(frozen=True, slots=True)
class SourceRef:
    """Where a value came from: the official API URL, the raw cache file, and a public page."""

    api_url: str
    cache_key: str
    public_url: str | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if not self.api_url.startswith("https://"):
            raise CoreValueError(f"SourceRef api_url must be https: {self.api_url!r}")
        if len(self.cache_key) != 64:
            raise CoreValueError("SourceRef cache_key must be a SHA-256 hex digest")
        if self.public_url is not None and not self.public_url.startswith("https://"):
            raise CoreValueError(f"SourceRef public_url must be https: {self.public_url!r}")


@dataclass(frozen=True, slots=True)
class DateWindow:
    """A closed date range [start, end], counted in calendar days, both ends included (0008)."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise CoreValueError(f"window end {self.end} is before start {self.start}")

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end


@dataclass(frozen=True, slots=True)
class Period:
    """A period with an inclusive start and an inclusive end; `end=None` means still open."""

    start: date
    end: date | None = None

    def __post_init__(self) -> None:
        if self.end is not None and self.end < self.start:
            raise CoreValueError(f"period end {self.end} is before start {self.start}")

    @property
    def is_open(self) -> bool:
        return self.end is None
