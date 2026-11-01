"""Compare the structure of live official responses with recorded fixtures (decision 0011, item 20).

Only field paths are compared, not values. Differences go to docs/data-issues.md by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def shape(data: Any, path: str = "") -> set[str]:
    """All field paths in a JSON value; list items are merged under `[]`."""
    paths: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            here = f"{path}.{key}" if path else key
            paths.add(here)
            paths |= shape(value, here)
    elif isinstance(data, list):
        for value in data:
            paths |= shape(value, f"{path}[]")
    return paths


def _normalize(paths: set[str]) -> set[str]:
    """The Senado sends one item as an object and many as a list; treat both the same."""
    return {p.replace("[]", "") for p in paths}


@dataclass
class Drift:
    name: str
    added: list[str]
    removed: list[str]

    @property
    def changed(self) -> bool:
        return bool(self.added or self.removed)


def compare(name: str, recorded: Any, live: Any) -> Drift:
    old, new = _normalize(shape(recorded)), _normalize(shape(live))
    return Drift(name=name, added=sorted(new - old), removed=sorted(old - new))
