"""Turn cached official responses into committed test fixtures (decision 0011, items 7–11).

Fixtures are made only by the `record_fixtures` command, which the project owner runs by hand.
Personal fields are removed at recording time (decision 0008 allowlist), because fixtures are
committed to git. Fixtures are never edited by hand: re-record them instead.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .cache import CachedFetcher, RawCache, split_url
from .personal import PERSONAL_KEYS, find_personal_keys, strip_personal  # noqa: F401 - re-exported


class FixtureError(Exception):
    pass


def _get_path(data: Any, dotted: str) -> Any:
    for key in dotted.split("."):
        data = data.get(key) if isinstance(data, dict) else None
    return data


def trim(body: Any, rule: dict[str, Any] | None) -> tuple[Any, str]:
    """Keep only some items of one list in the body. Returns (body, description)."""
    if not rule:
        return body, "not trimmed"
    body = copy.deepcopy(body)
    if rule["list_path"] == "$":  # the body itself is the list (e.g. Senado /votacao)
        container, leaf = {"$": body}, "$"
    else:
        *parents, leaf = rule["list_path"].split(".")
        container = _get_path(body, ".".join(parents)) if parents else body
    items = container.get(leaf) if isinstance(container, dict) else None
    if not isinstance(items, list):
        raise FixtureError(f"trim: {rule['list_path']} is not a list")
    if "keep_values" in rule:
        wanted = {str(v) for v in rule["keep_values"]}
        kept = [i for i in items if str(_get_path(i, rule["keep_key"])) in wanted]
        found = {str(_get_path(i, rule["keep_key"])) for i in kept}
        if wanted - found:
            raise FixtureError(f"trim: values not found in response: {sorted(wanted - found)}")
        how = f"kept items with {rule['keep_key']} in {sorted(wanted)}"
    else:
        kept = items[: int(rule["first"])]
        how = f"kept the first {len(kept)}"
    container[leaf] = kept
    if rule["list_path"] == "$":
        body = kept
    return body, f"{rule['list_path']}: {how} of {len(items)}"


@dataclass
class RecordResult:
    name: str
    path: Path
    removed: list[str]
    fetched_live: bool


def record_case(
    case: dict[str, Any],
    *,
    cache: RawCache,
    out_dir: Path,
    spec: dict[str, str],
    fetcher: CachedFetcher | None = None,
    now: datetime | None = None,
) -> RecordResult:
    url, params = split_url(case["url"], case.get("params"))
    entry = cache.read(case["source"], url, params)
    fetched_live = False
    if entry is None:
        if fetcher is None:
            raise FixtureError(
                f"{case['name']}: not in the cache. Run the fetch commands first, or use --fetch."
            )
        fetcher.get(url, params)
        fetched_live = True
        entry = cache.read(case["source"], url, params)
        if entry is None:  # pragma: no cover - defensive
            raise FixtureError(f"{case['name']}: fetch did not write the cache")
    body, trimmed = trim(entry.body, case.get("trim"))
    body, removed = strip_personal(body)
    envelope = {k: v for k, v in entry.envelope.items() if k != "body"}
    fixture = {
        "_fixture": {
            "case": case["name"],
            "recorded_at": (now or datetime.now(UTC)).isoformat(),
            "spec": spec.get(case["source"]),
            "trimmed": trimmed,
            "removed_personal_fields": removed,
            # Named "cache_file_id" (not "...key") so secret scanners do not mistake this
            # SHA-256 of a public URL for a credential.
            "cache_file_id": entry.key,
        },
        **envelope,
        "body": body,
    }
    path = out_dir / case["file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return RecordResult(case["name"], path, removed, fetched_live)


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cache_from_fixtures(fixtures_dir: Path, cache: RawCache) -> int:
    """Write every recorded fixture into a raw cache (used by tests and end-to-end runs).

    Trimmed lists keep their "next page" links; those are removed in this copy only, so the
    one recorded page is read as the whole list. Untrimmed pages keep their links, so a list
    recorded page by page is read in full.
    """
    from .http import HttpResponse

    count = 0
    for path in sorted(Path(fixtures_dir).rglob("*.json")):
        data = load_fixture(path)
        body = copy.deepcopy(data["body"])
        trimmed = data.get("_fixture", {}).get("trimmed", "not trimmed") != "not trimmed"
        if trimmed and isinstance(body, dict) and isinstance(body.get("links"), list):
            body["links"] = [link for link in body["links"] if link.get("rel") != "next"]
        response = HttpResponse(data["url"], data["status"], data["content_type"], body)
        cache.write(data["source"], data["url"], data["params"], response)
        count += 1
    return count
