# Phase A — test report

- **Date:** 2026-11-01
- **Command:** `cd backend && uv run pytest` (network blocked by `pytest-socket`; only `127.0.0.1` allowed)

## Result (run on 2026-11-01)

- Before fixtures: 94 passed, 9 skipped (tests needing recorded fixtures).
- After recording 17 fixtures (2026-11-01, `scripts/record_fixtures.py --fetch`, run in the session with the owner's approval): **119 passed, 0 skipped**, including 8 real-case tests and the personal-field check on all 17 fixtures.
- Line and branch coverage of `placar/`: 93% (`uv run coverage run -m pytest && uv run coverage report`).
- Extra check: no `@` or `"cpf"` found anywhere in `backend/tests/fixtures/` (grep).

## Live acceptance run (A13), 2026-11-01

Run in the session with the owner's approval.

| Run | Câmara | Senado | Time |
| --- | --- | --- | --- |
| 1st `fetch_current` | 677 requests (19 retries after HTTP 504), 657 downloads; 882 list rows for 648 deputies; 6,841 history events; 1 failure (deputy 74299, 5 attempts) | 382 requests, 382 downloads; 245 listed, 126 took office, 81 in office today; 154 mandates, 231 periods in office, 5,174 leaves, 301 affiliations; no failures | 21 min |
| 2nd `fetch_current` (same day) | 1 request (the missing 74299 history, now fetched), 657 cache hits | 0 requests, 382 cache hits | < 1 s |

Raw cache after both runs: 1,043 files, 4.1 MB (`data/raw/`, git-ignored). Both houses report legislature 57, 2023-02-01 to 2027-01-31 (no cross-check difference).

## Coverage of the plan's acceptance criteria

| Criterion | Tests |
| --- | --- |
| 1. `fetch_current` fetches and reports | `test_sources_fetch_runs.py`; live run done (see above) |
| 2. ≤ 2 requests/s, `Retry-After` honored | `test_sources_http.py` (throttle, 429/503/504, backoff cap, give-up) |
| 3. Second run makes no requests | `test_fetch_current_downloads_then_uses_cache`; live 2nd run: 0 requests for cached data |
| 4. Every record has a `SourceRef` | parser tests; real cases check source URLs |
| 5. No personal fields | synthetic parser tests; fixture recorder tests; `test_rules.py` fixture check (17 fixtures pass) |
| 6. Offline suite | `test_network_is_blocked_in_tests` |
| 7. Endpoints cited, no deprecated Senado services | module docstrings in `clients/camara.py`, `clients/senado.py` (review) |
| 8. Data issues logged | `docs/data-issues.md` entries 4, 8, 9 |
| 9. Security review | `docs/security/phase-a.md` |

## Synthetic vs real data

Synthetic test bodies are labeled in each test module's docstring and are never shown in the app (decision 0011). Real-case tests use only recorded fixtures.
