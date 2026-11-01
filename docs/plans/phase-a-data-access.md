# Phase A — Data access (plan)

- **Status:** approved by the project owner on 2026-11-01, including the dependency list. Deputy details (`/deputados/{id}`) are skipped as planned; the live run (A13) will be confirmed with the owner when reached.
- **Date:** 2026-11-01
- **Decisions applied:** 0004–0013 (see `docs/architecture-rules.md`)

## Goal

One command fetches the current legislature's deputies and senators, and the records needed to build their time in office, from the official APIs. It stores the raw responses in the local cache, respecting rate limits. A second run uses the cache. A test suite passes offline.

## In scope

- Backend project setup (uv, Django 6.1, settings from environment, Docker PostgreSQL, lint and test configuration).
- `core` shared types (`SourceRef`, `DateWindow`, `Period`).
- HTTP layer: rate limiting, retries, `Retry-After`, jitter, `User-Agent`, deprecation-header logging, official-URL allowlist.
- Raw file cache with envelope, keys and freshness rules.
- Câmara and Senado clients that return parsed, typed records (plain Python objects; no database models yet).
- Fetch commands and a run report.
- Fixture recording script, fixtures, upstream drift-check script.
- Offline tests; security review; data-issues updates; README setup section.

## Out of scope

- Django models, normalization into the database, and `coverage()` (Phase B).
- Votes, bills, attendance and speeches endpoints (planned in Phase B).
- Official photos download (Phase C, when the UI needs them).
- Django Ninja API, frontend, summaries.

## Endpoints

All checked against the official specs downloaded on 2026-11-01. Live samples were taken for every endpoint below except Câmara `/deputados/{id}` (not used in this phase).

**Câmara** (spec version 0.4.347, `https://dadosabertos.camara.leg.br/api/v2/api-docs`). Lists return 15 items by default and 100 at most.

| Endpoint | Used for |
| --- | --- |
| `GET /legislaturas?data={today}` | Current legislature number and dates |
| `GET /deputados?idLegislatura={n}&itens=100&pagina={p}` | Everyone who served in the legislature (9 pages for legislature 57) |
| `GET /deputados/{id}/historico` | Entry/exit events and party at each event (0008) |

`/deputados/{id}` (details) is **not** called: it returns out-of-scope personal fields, and the list and history already give the allowlisted fields. The civil name stays empty for now.

**Senado** (spec version 4.1.3.108, `https://legis.senado.leg.br/dadosabertos/v3/api-docs`). JSON is requested with `Accept: application/json`; the documented limit is 10 requests per second.

| Endpoint | Used for |
| --- | --- |
| `GET /dadosabertos/plenario/legislatura/{date}` | Current legislature (cross-check with Câmara) |
| `GET /dadosabertos/senador/lista/legislatura/{n}` | All titulars and alternates linked to the legislature (245 for 57) |
| `GET /dadosabertos/senador/lista/legislatura/{n}?exercicio=S` | Those who actually took office (126 for 57) |
| `GET /dadosabertos/senador/lista/atual` | Who is in office today |
| `GET /dadosabertos/senador/{codigo}/mandatos` | Mandates and `Exercicios` (periods in office) |
| `GET /dadosabertos/senador/{codigo}/licencas` | Leaves |
| `GET /dadosabertos/senador/{codigo}/filiacoes` | Party affiliations |

Details (`mandatos`, `licencas`, `filiacoes`) are fetched only for people who took office. Alternates who never did are kept from the list response.

**Expected first run:** about 860 Câmara and 380 Senado requests. At 2 requests per second per API, about 7–8 minutes. A second run within the freshness window makes no requests for unchanged data.

## Tasks

| # | Task | Owner | Done when |
| --- | --- | --- | --- |
| A0 | Backend setup: `backend/pyproject.toml` (Python 3.14, uv), Django project `config/` with base/dev/test settings from environment, `compose.yaml` (PostgreSQL 18 on `127.0.0.1`), `.env.example` (names only), ruff (including `S` rules), pytest + pytest-django + pytest-socket configuration | backend engineer | `uv run pytest` runs an empty suite offline; `uv run ruff check` is clean; Django starts with dev settings |
| A1 | `core` types: `SourceRef` (API URL, public page URL, cache key, label), `DateWindow`, `Period` | backend engineer | Unit tests for construction and validation |
| A2 | HTTP layer in `sources/http`: ≤ 2 req/s and 1 at a time per API, jitter, retry limit with `Retry-After` and backoff, project `User-Agent`, official-domain allowlist, `Deprecation`/`Sunset` header logging | data engineer | Tests with respx cover throttling, 429/503/504, `Retry-After`, give-up, allowlist rejection |
| A3 | Raw cache in `sources/cache`: gzip JSON envelope, SHA-256 key, freshness rules (no expiry for closed data, 24 h for changing data), `--refresh`, use stale copy on failure | data engineer | Tests: write/read, key stability, expiry, refresh, stale-on-error, no cookies stored |
| A4 | Câmara client and parsers (`sources/clients/camara`): legislature, paged deputies list, history events | data engineer | Parser tests on fixtures; only allowlisted fields kept; spec version cited in code comments |
| A5 | Senado client and parsers (`sources/clients/senado`): legislature, lists, mandates with `Exercicios`, leaves, affiliations; single-item vs list JSON shapes handled | data engineer | Parser tests on fixtures, including the empty-alternate case (5918) |
| A6 | Management commands `fetch_camara`, `fetch_senado`, `fetch_current`, with a run report (requests made, cache hits, records parsed, errors, new data issues) | data engineer | Command tests with replayed responses; report printed |
| A7 | `scripts/record_fixtures.py`: copies chosen cache files into `backend/tests/fixtures/`, strips non-allowlisted personal fields, adds the `_fixture` note | data engineer | Script tested on a sample cache; the owner runs it for real |
| A8 | Fixtures for named real cases: Senado mandate 526 (4545, 5917, 5918), Câmara deputy 220593, a short Câmara list page, legislature responses | QA (recorded by the owner) | Fixture files committed; no personal fields (test passes) |
| A9 | Rules tests: import boundaries (0007), no personal fields in fixtures, no network in tests | QA | Tests fail on a deliberate violation and pass on the real code |
| A10 | `scripts/check_upstream.py`: compares live response structure with fixtures and lists differences | data engineer | Runs by hand; output format documented |
| A11 | Docs: README setup section (uv, Docker, `.env`, hook), `docs/data-issues.md` updates, `docs/testing/phase-a.md` report | technical writer, data engineer, QA | Owner can set up from the README alone |
| A12 | Security review note `docs/security/phase-a.md`: secrets, `pip-audit`, allowlist, logging, fixtures | security engineer | Note lists each check and its real result |
| A13 | Live acceptance run: `fetch_current` against the real APIs, then a second run | owner runs it, or approves the session running it | Report shows counts; second run makes no requests for unchanged data |

## Acceptance criteria

1. `uv run python manage.py fetch_current` fetches the current legislature's deputies and senators and their history, mandates, leaves and affiliations into `data/raw/`, and prints a run report.
2. No API receives more than 2 requests per second from the tool, and `Retry-After` is honored (tested).
3. A second run within the freshness window makes no network requests for unchanged data (tested, and shown in the live run report).
4. Every parsed record carries a `SourceRef` with the API URL and cache key.
5. No non-allowlisted personal field appears in parsed records or fixtures (tested).
6. `uv run pytest` passes with all network access blocked except the local database.
7. Every endpoint used is cited in code with its spec URL and version; no deprecated Senado service is used.
8. Data issues found during the work are in `docs/data-issues.md`, including the cause of the 82-titulars count if found.
9. Security review note written; `pip-audit` has no unresolved findings, or each is explained.

## Dependencies to approve

Python (backend), latest versions checked on 2026-11-01:

- runtime: `django` 6.1.x, `httpx` 0.28.x, `psycopg[binary]` 3.3.x;
- development: `pytest` 9.2.x, `pytest-django` 4.14.x, `pytest-socket` 0.8.x, `respx` 0.23.x, `coverage` 7.17.x, `ruff` 0.17.x, `pip-audit` 2.10.x.

Not needed yet: `django-ninja` (Phase C), `hypothesis` (Phase B), `anthropic` (Phase D), frontend packages (Phase C).

## Risks

- The Câmara API sometimes times out (data issue 1). Retries and the stale cache cover it; repeated failures are reported, not hidden.
- API changes during the phase (data issues 2, 3). The drift check and spec citations make changes visible.
- The first full run takes several minutes. The command shows progress and can resume, because finished responses are already cached.

## Open questions for the owner

1. Approve this plan and the dependency list?
2. The live run (A13) makes about 1,240 requests to public official APIs, spaced out. Should the session run it, or will you run it yourself?
3. Skipping `/deputados/{id}` means no civil name for deputies for now. OK? (It can be added later with the allowlist filter.)

## Outcome (2026-11-01)

All tasks A0–A13 done. Evidence: `docs/testing/phase-a.md`, `docs/security/phase-a.md`, `docs/data-issues.md`.

| Criterion | Result |
| --- | --- |
| 1. `fetch_current` fetches both houses and prints a report | Met: live run fetched 648 deputies (6,865 history events) and 126 senators' details |
| 2. ≤ 2 requests/s, `Retry-After` honored | Met: throttle capped at 2/s (tested); 19 live retries after HTTP 504 with backoff |
| 3. Second run makes no requests for unchanged data | Met: 2nd run sent 1 request, only for the history that failed in the 1st run |
| 4. Every parsed record has a `SourceRef` | Met (tests) |
| 5. No non-allowlisted personal field in records or fixtures | Met: parsers use allowlists; 17 fixtures checked by test and grep |
| 6. Offline test suite passes | Met: 119 passed, 0 skipped, network blocked |
| 7. Endpoints cited with spec version; no deprecated Senado service | Met: module docstrings in `clients/camara.py` and `clients/senado.py`; no deprecation headers seen in the live run |
| 8. Data issues logged | Met: issues 1, 4, 8, 9 added or updated; cause of issue 4 left for Phase B |
| 9. Security review written; `pip-audit` clean | Met |

**Differences from the plan:**
- The first run took 21 minutes, not 7–8, because of Câmara timeouts (data issue 1).
- There were 648 deputies, not about 860, so there were fewer history requests than estimated.
- The fixture recorder is a management command with a thin wrapper in `scripts/`, so it reuses the cache code.

**Status:** signed off by the project owner on 2026-11-01.
