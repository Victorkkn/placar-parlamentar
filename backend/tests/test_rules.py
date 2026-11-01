"""Project rules enforced by tests (decisions 0007, 0008, 0011, 0012)."""

import ast
import json
import socket
from pathlib import Path

import pytest

from placar.sources.fixtures import find_personal_keys

BACKEND = Path(__file__).resolve().parents[1]
PLACAR = BACKEND / "placar"
FIXTURES = BACKEND / "tests" / "fixtures"

# Decision 0007: which placar apps each app may import.
ALLOWED = {
    "core": set(),
    "legislators": {"core"},
    "activity": {"core", "legislators"},
    "sources": {"core", "legislators", "activity"},
    "metrics": {"core", "legislators", "activity"},
    "summaries": {"core", "legislators", "activity", "metrics"},
    "api": {"core", "legislators", "activity", "metrics", "summaries"},
}
# Decision 0010: only summaries/llm may import the model provider's SDK.
PROVIDER_SDKS = {"anthropic"}
# Decision 0007: metrics never imports web code or sources.
METRICS_FORBIDDEN = {"django.http", "ninja", "placar.sources"}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = ".".join(path.relative_to(BACKEND).with_suffix("").parts[:-1])
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")
                base = base[: len(base) - node.level + 1]
                names.add(".".join([*base, node.module] if node.module else base))
            elif node.module:
                names.add(node.module)
    return names


def app_of(module: str) -> str | None:
    parts = module.split(".")
    return parts[1] if len(parts) > 1 and parts[0] == "placar" else None


def python_files():
    return sorted(PLACAR.rglob("*.py"))


def test_every_app_is_known():
    apps = {p.name for p in PLACAR.iterdir() if p.is_dir() and not p.name.startswith("_")}
    assert apps <= set(ALLOWED), f"unknown apps need a decision: {apps - set(ALLOWED)}"


@pytest.mark.parametrize("path", python_files(), ids=lambda p: str(p.relative_to(BACKEND)))
def test_import_boundaries(path):
    own = path.relative_to(PLACAR).parts[0]
    for module in imported_modules(path):
        target = app_of(module)
        if target and target != own:
            assert target in ALLOWED[own], f"{own} may not import {target} ({module})"
        if module.split(".")[0] in PROVIDER_SDKS:
            assert path.is_relative_to(PLACAR / "summaries" / "llm"), (
                f"{module} outside summaries/llm"
            )
        if own == "metrics":
            assert not any(module == f or module.startswith(f + ".") for f in METRICS_FORBIDDEN)


def test_boundary_checker_catches_a_violation(tmp_path):
    bad = PLACAR / "core" / "_tmp_violation.py"
    bad.write_text("from placar.sources import http\n", encoding="utf-8")
    try:
        with pytest.raises(AssertionError, match="core may not import sources"):
            test_import_boundaries(bad)
    finally:
        bad.unlink()


def fixture_files():
    return sorted(FIXTURES.rglob("*.json")) if FIXTURES.exists() else []


@pytest.mark.parametrize("path", fixture_files(), ids=lambda p: str(p.relative_to(FIXTURES)))
def test_fixtures_have_no_personal_fields_and_a_note(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert find_personal_keys(data["body"]) == []
    note = data["_fixture"]
    assert note["recorded_at"] and note["spec"] and note["case"]


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_network_is_blocked_in_tests():
    # 203.0.113.1 is a reserved documentation address (RFC 5737): no DNS lookup happens.
    with pytest.raises(Exception, match="(?i)socket"):
        socket.create_connection(("203.0.113.1", 443), timeout=1)
