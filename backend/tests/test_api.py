"""Public API (Phase C1): REAL officials from fixtures + SYNTHETIC activity (decision 0011)."""

from datetime import date
from pathlib import Path

import pytest
from django.test import Client

from placar.activity.services import replace_activity
from placar.api.management.commands.export_openapi import CONTRACT, contract_text
from placar.legislators.selectors import get_official
from placar.legislators.services import record_load

from .test_activity_db import camara_bundle
from .test_legislators_db import load_both

pytestmark = pytest.mark.django_db
SNAPSHOT = date(2026, 11, 1)

# Numbers that are inputs, identifiers or paging, not data, so they need no source.
NON_DATA_KEYS = {
    "id", "house_id", "total", "page", "page_size", "not_in_office", "days", "window_days",
    "min_days", "min_share", "legislature", "default_min_share", "member_ids",
}  # fmt: skip
# Party rows are derived from their listed members (`member_ids`), whose records carry sources.
DERIVED_CONTAINERS = {"parties"}


@pytest.fixture
def client():
    load_both()
    replace_activity(camara_bundle())
    for house in ("CAMARA", "SENADO"):
        record_load(house, "people", SNAPSHOT)
    record_load("CAMARA", "activity", SNAPSHOT)
    return Client()


def numbers_without_sources(data, path="$", inside_derived=False):
    """Every dict holding a data number must also hold a `sources` list (rule 3)."""
    problems = []
    if isinstance(data, dict):
        has_sources = isinstance(data.get("sources"), list)
        for key, value in data.items():
            here = f"{path}.{key}"
            is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
            if is_number and key not in NON_DATA_KEYS and not has_sources and not inside_derived:
                problems.append(here)
            # A metric's `details` are counts of the same records listed in the metric's sources.
            covered = (
                inside_derived or key in DERIVED_CONTAINERS or (key == "details" and has_sources)
            )
            problems += numbers_without_sources(value, here, covered)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            problems += numbers_without_sources(item, f"{path}[{i}]", inside_derived)
    return problems


def get(client, url, status=200):
    response = client.get(url)
    assert response.status_code == status, response.content
    return response.json()


def test_meta(client):
    data = get(client, "/api/meta")
    assert data["snapshot_date"] == "2026-11-01" and data["legislature"] == 57
    houses = {h["house"]: h for h in data["houses"]}
    assert "plenary_attendance" in houses["CAMARA"]["metrics"]
    assert houses["SENADO"]["metrics"] == []  # Senado activity not loaded in this test
    assert data["default_min_share"] == 0.5


def test_officials_default_window_and_threshold(client):
    data = get(client, "/api/officials")
    assert data["window"] == {"start": "2023-02-01", "end": "2026-11-01", "days": 1370}
    assert data["threshold"] == {"min_days": None, "min_share": 0.5}
    by_id = {(o["house"], o["house_id"]): o for o in data["items"]}
    alternate = by_id[("SENADO", 5917)]
    assert alternate["coverage"]["days_in_office"] == 1370 and alternate["sufficient"] is True
    titular = by_id[("SENADO", 4545)]
    assert (
        titular["coverage"]["days_in_office"] == 1 and titular["sufficient"] is False
    )  # shown, flagged
    assert data["not_in_office"] == 1  # 5918 never took office; counted, not silently dropped
    assert numbers_without_sources(data) == []


def test_officials_filters_and_paging(client):
    assert get(client, "/api/officials?house=senado&state=PE")["total"] == 2
    assert get(client, "/api/officials?q=dueire")["total"] == 1
    assert get(client, "/api/officials?include_not_in_office=true")["not_in_office"] == 0
    page = get(client, "/api/officials?page_size=1&page=2")
    assert page["page"] == 2 and len(page["items"]) == 1


def test_threshold_in_days(client):
    data = get(client, "/api/officials?min_days=1&house=SENADO")
    assert all(o["sufficient"] for o in data["items"])


@pytest.mark.parametrize(
    "query",
    [
        "start=1980-01-01",
        "end=2030-01-01",
        "start=2025-01-01&end=2024-01-01",
        "min_days=5&min_share=0.5",
        "min_share=1.5",
        "min_days=99999",
        "house=XYZ",
        "state=ABC",
        "page_size=101",
        "page=0",
        "start=not-a-date",
    ],
)
def test_invalid_input_is_rejected_without_details(client, query):
    response = client.get(f"/api/officials?{query}")
    assert 400 <= response.status_code < 500
    assert "Traceback" not in response.content.decode()


def test_only_get_is_allowed(client):
    assert client.post("/api/officials").status_code == 405
    assert client.delete("/api/meta").status_code == 405


def test_official_detail_with_metrics_and_sources(client):
    deputy = get_official("CAMARA", 220593)
    data = get(client, f"/api/officials/{deputy.pk}")
    metrics = {m["key"]: m for m in data["metrics"]}
    assert metrics["plenary_attendance"]["numerator"] == 1
    assert metrics["bills_authored"]["numerator"] == 1
    assert metrics["bills_authored"]["per_365_days_in_office"] == round(365 / 701, 4)
    assert data["periods"][-1]["end_reason"] == "RESIGNATION"
    assert numbers_without_sources(data) == []
    # Phase D: template summary, every sentence with at least one official source.
    assert data["summary"]["kind"] == "template"
    assert data["summary"]["sentences"]
    assert all(sentence["sources"] for sentence in data["summary"]["sentences"])


def test_senator_metrics_are_marked_not_available(client):
    senator = get_official("SENADO", 5917)
    metrics = {m["key"]: m for m in get(client, f"/api/officials/{senator.pk}")["metrics"]}
    # Activity not loaded for the Senado here: never a made-up zero (decision 0015).
    assert all(m["available"] is False for m in metrics.values())
    assert metrics["bills_authored"]["reason"] == "not_loaded_yet"
    assert metrics["bills_authored"]["numerator"] is None


def test_unknown_official_is_404(client):
    assert client.get("/api/officials/999999").status_code == 404


def test_compare(client):
    a, b = get_official("SENADO", 4545), get_official("SENADO", 5917)
    data = get(client, f"/api/compare?ids={a.pk},{b.pk}&start=2023-01-01&end=2023-12-31")
    assert data["window"]["start"] == "2023-01-01" and len(data["officials"]) == 2
    assert all(o["summary"] is None for o in data["officials"])  # summaries only on detail
    assert numbers_without_sources(data) == []


@pytest.mark.parametrize("ids", ["1", "1,2,3,4,5,6,7", "a,b", "1,1"])
def test_compare_rejects_bad_ids(client, ids):
    assert client.get(f"/api/compare?ids={ids}").status_code == 400


def test_parties(client):
    data = get(client, "/api/parties?house=SENADO")
    rows = {r["party"]: r for r in data["parties"]}
    assert "PSD" in rows and "MDB" in rows  # 5917 switched MDB → PSD on 2026-04-02
    assert rows["PSD"]["membership_changed"] is True
    assert all(r["member_ids"] for r in rows.values())
    assert numbers_without_sources(data) == []


def test_openapi_contract_is_up_to_date():
    assert Path(CONTRACT).read_text(encoding="utf-8") == contract_text(), (
        "docs/api/openapi.json is stale: run `uv run python manage.py export_openapi`"
    )


def test_no_data_loaded_gives_503():
    load_both()
    assert Client().get("/api/officials").status_code == 503
