"""Fixture recording on SYNTHETIC cache entries (decision 0011, item 6)."""

import gzip
import json
from datetime import UTC, datetime

import pytest

from placar.sources.cache import RawCache
from placar.sources.fixtures import (
    FixtureError,
    find_personal_keys,
    load_fixture,
    record_case,
    strip_personal,
    trim,
)
from placar.sources.http import HttpResponse

URL = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"
SPEC = {"senado": "spec 4.1.3.108"}
BODY = {
    "ListaParlamentarEmExercicio": {
        "Parlamentares": {
            "Parlamentar": [
                {"IdentificacaoParlamentar": {"CodigoParlamentar": "1", "NomeParlamentar": "A",
                 "EmailParlamentar": "a@senado.leg.br", "SexoParlamentar": "X",
                 "Telefones": {"Telefone": [{"NumeroTelefone": "1"}]}}},
                {"IdentificacaoParlamentar": {"CodigoParlamentar": "2", "NomeParlamentar": "B"}},
                {"IdentificacaoParlamentar": {"CodigoParlamentar": "3", "NomeParlamentar": "C"}},
            ]
        }
    }
}  # fmt: skip
TRIM = {
    "list_path": "ListaParlamentarEmExercicio.Parlamentares.Parlamentar",
    "keep_key": "IdentificacaoParlamentar.CodigoParlamentar",
    "keep_values": [1, 3],
}


def cache_with_body(tmp_path):
    cache = RawCache(tmp_path / "raw", clock=lambda: datetime(2026, 11, 1, tzinfo=UTC))
    cache.write("senado", URL, {}, HttpResponse(URL, 200, "application/json", BODY))
    return cache


def test_strip_personal_removes_keys_at_any_depth():
    clean, removed = strip_personal(BODY)
    assert "EmailParlamentar" not in str(clean) and "Telefones" not in str(clean)
    assert len(removed) == 3
    assert find_personal_keys(clean) == []
    assert find_personal_keys({"dados": [{"cpf": "x", "nome": "y"}]}) == ["dados[0].cpf"]


def test_trim_by_values_and_by_first():
    body, how = trim(BODY, TRIM)
    codes = [p["IdentificacaoParlamentar"]["CodigoParlamentar"] for p in
             body["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]]  # fmt: skip
    assert codes == ["1", "3"] and "of 3" in how
    body, how = trim(BODY, {"list_path": TRIM["list_path"], "first": 1})
    assert len(body["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]) == 1
    assert len(BODY["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]) == 3


def test_trim_fails_when_a_wanted_value_is_missing():
    with pytest.raises(FixtureError, match="not found"):
        trim(BODY, {**TRIM, "keep_values": [1, 99]})


def test_record_case_writes_clean_fixture_with_note(tmp_path):
    cache = cache_with_body(tmp_path)
    case = {"name": "atual", "source": "senado", "url": URL, "file": "senado/atual.json",
            "trim": TRIM}  # fmt: skip
    result = record_case(
        case,
        cache=cache,
        out_dir=tmp_path / "fixtures",
        spec=SPEC,
        now=datetime(2026, 11, 2, tzinfo=UTC),
    )
    fixture = load_fixture(result.path)
    assert fixture["_fixture"]["case"] == "atual"
    assert fixture["_fixture"]["spec"] == "spec 4.1.3.108"
    assert fixture["_fixture"]["recorded_at"].startswith("2026-11-02")
    assert "kept items" in fixture["_fixture"]["trimmed"]
    # Decision 0019: the cache never held them, so recording finds nothing more to remove.
    assert fixture["_fixture"]["removed_personal_fields"] == []
    assert fixture["removed_personal_fields"] == 3  # counted when the cache was written
    assert fixture["url"] == URL and fixture["fetched_at"].startswith("2026-11-01")
    assert find_personal_keys(fixture["body"]) == []
    assert not result.fetched_live


def test_record_case_without_cache_and_without_fetch_fails(tmp_path):
    case = {"name": "missing", "source": "senado", "url": URL + "?x=1", "file": "x.json"}
    with pytest.raises(FixtureError, match="not in the cache"):
        record_case(case, cache=RawCache(tmp_path), out_dir=tmp_path, spec=SPEC)


def test_cache_write_removes_personal_fields(tmp_path):
    # Decision 0019: contact and gender fields never reach the cache file.
    cache = cache_with_body(tmp_path)
    entry = cache.read("senado", URL, {})
    assert find_personal_keys(entry.body) == []
    assert entry.envelope["removed_personal_fields"] == 3
    assert "a@senado.leg.br" not in gzip.decompress(entry.path.read_bytes()).decode()


def test_scrub_cleans_a_file_written_before_decision_0019(tmp_path):
    cache = cache_with_body(tmp_path)
    path = cache.read("senado", URL, {}).path
    old = json.loads(gzip.decompress(path.read_bytes()))
    old["body"], old["removed_personal_fields"] = BODY, 0  # as an old file looked
    path.write_bytes(gzip.compress(json.dumps(old).encode()))
    assert cache.scrub(path) == 3
    entry = cache.read("senado", URL, {})
    assert find_personal_keys(entry.body) == []
    assert entry.envelope["fetched_at"] == old["fetched_at"]  # freshness unchanged
    assert cache.scrub(path) == 0  # idempotent
