# Phase A — test report

- **Date:** 2026-11-01
- **Command:** `cd backend && uv run pytest` (network blocked by `pytest-socket`; only `127.0.0.1` allowed)

## Result (run on 2026-11-01)

- 94 passed, 9 skipped.
- The 9 skipped tests need the recorded fixtures (8 real-case tests and the "no personal fields in fixtures" check). They run after the owner records fixtures with `scripts/record_fixtures.py`.
- Line and branch coverage of `placar/`: 93% (`uv run coverage run -m pytest && uv run coverage report`).

## Coverage of the plan's acceptance criteria

| Criterion | Tests |
| --- | --- |
| 1. `fetch_current` fetches and reports | `test_sources_fetch_runs.py` (synthetic responses); live run pending (A13) |
| 2. ≤ 2 requests/s, `Retry-After` honored | `test_sources_http.py` (throttle, 429/503/504, backoff cap, give-up) |
| 3. Second run makes no requests | `test_fetch_current_downloads_then_uses_cache`; live run pending |
| 4. Every record has a `SourceRef` | parser tests; real cases check source URLs |
| 5. No personal fields | synthetic parser tests; fixture recorder tests; `test_rules.py` fixture check (pending fixtures) |
| 6. Offline suite | `test_network_is_blocked_in_tests` |
| 7. Endpoints cited, no deprecated Senado services | module docstrings in `clients/camara.py`, `clients/senado.py` (review) |
| 8. Data issues logged | `docs/data-issues.md` entries 4, 8, 9 |
| 9. Security review | `docs/security/phase-a.md` |

## Synthetic vs real data

Synthetic test bodies are labeled in each test module's docstring and are never shown in the app (decision 0011). Real-case tests use only recorded fixtures.
