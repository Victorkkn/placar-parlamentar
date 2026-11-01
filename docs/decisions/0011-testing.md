# 0011 — Testing strategy and offline fixtures

- **Status:** proposed
- **Date:** 2026-11-01
- **Stage:** 2 (topic 8 of 10)

## Context

Tests must run offline, using recorded official responses rather than live calls (project prompt, Phase A). Earlier decisions already require some specific tests:

- the import-boundary test (0007);
- the OpenAPI contract check on both sides (0009);
- the summary validator and source-mapping tests with a fake model adapter (0010);
- tests run against PostgreSQL (0006).

Real cases found in the official data (0008, `docs/data-issues.md`) cover the hard parts of coverage:

- Senado seat mandate 526: titular on leave, alternate in office, return and resignation on the same day, alternate's later party switch;
- Câmara deputy 220593: entry in 2023, vacancy in 2025.

Versions checked on 2026-11-01:

- PyPI: pytest 9.2.0, pytest-django 4.14.0, respx 0.23.1, pytest-socket 0.8.1, hypothesis 6.170.14, coverage 7.17.0.
- npm: vitest 5.0.5, @testing-library/react 16.3.3, msw 3.0.3, @playwright/test 1.64.1, @axe-core/playwright 4.14.0.

## Decision

### Backend tools

1. **pytest** with **pytest-django**, against a throwaway PostgreSQL test database in the local Docker container.
2. **No network in tests:** `pytest-socket` blocks all connections except to the local database (`127.0.0.1`). A test that tries to reach the internet fails.
3. **respx** replays recorded responses to the `httpx` clients in `sources`.
4. **hypothesis** for property tests of `coverage()` and period merging, for example:
   - the share is always between 0 and 1;
   - covered days never exceed the window's days;
   - merging periods twice gives the same result as merging once.
5. **coverage.py** reports line coverage. Minimum 90% for `metrics/` and the summary validator; reported but not enforced elsewhere.
6. Test data for cases not seen in real records comes from small builder functions in `backend/tests/builders.py` (no factory library). Synthetic data is labeled as such and never shown in the app.

### Recorded fixtures

7. Fixtures are made by `scripts/record_fixtures.py`, which **the project owner runs by hand** (it is the only script that calls the live APIs for testing). It copies selected responses from the raw cache (0006) into `backend/tests/fixtures/<source>/<endpoint>/<case>.json`.
8. Each fixture keeps the official envelope (URL, parameters, fetch time, status, API version) plus a `_fixture` note:
   - the recording date;
   - the spec version used;
   - what was trimmed (for example "kept 3 of 100 deputies").
9. **Personal fields are removed at recording time**, using the same allowlist as decision 0008 (no CPF, birth date or place, social media, personal email or address), because fixtures are committed to git.
10. Each named real case gets its own fixture set and test module (for example `case_senado_mandate_526`), so a metric change shows which real situations it affects.
11. Fixtures are never edited by hand. To change one, re-record it. Deleting fixtures needs the owner's approval (0002).

### Backend test layers

| Layer | What it checks | Owner |
| --- | --- | --- |
| Client | `sources` clients against replayed responses: paging, retries, `Retry-After`, cache hits, deprecated-header warnings | data engineer |
| Normalizer | fixtures → records, including `UNKNOWN` values being logged instead of guessed | data engineer |
| Metrics | `coverage()` for full term, mid-term entry, leave, substitute, party switch, and the real cases; property tests | backend engineer |
| Summaries | validator rules, template fallback, fake adapter | backend engineer |
| API | Ninja test client; a generic check that walks every JSON response and fails if any number lacks a `SourceRef` | backend engineer / QA |
| Rules | import boundaries (0007), contract file up to date (0009), no personal fields in fixtures | QA |

### Frontend

12. **Vitest** with **Testing Library** for components and pages.
13. **MSW** serves typed responses (matching the generated API types) to component tests, so no backend is needed.
14. A source-link check renders each page and fails if a number appears outside the shared source-link component (0009).
15. A wording check fails if `frontend/src/text/pt-BR.ts` or the summary templates contain banned wording (0010 list).

### End-to-end

16. **Playwright** (Chromium only in the MVP) runs against the local backend loaded from the recorded fixtures, fully offline. It also runs **axe** accessibility checks on each main page.
17. End-to-end tests run before a phase is reported done, not on every commit.

### Commands and live checks

18. One command per suite: `uv run pytest` (backend), `npm test` (frontend), `npm run e2e` (end-to-end).
19. Continuous integration (CI) is out of scope until the deployment decision.
20. **Upstream drift check:** `scripts/check_upstream.py`, run by hand, compares the field structure of live responses with the fixtures and lists differences. It is not part of any test suite, and its findings go to `docs/data-issues.md`.

## Alternatives considered

- **SQLite for tests.** Faster setup, but it behaves differently from PostgreSQL (0006).
- **VCR-style cassettes (record on first run).** Convenient, but a test could silently call the live API when a cassette is missing, and personal fields would be recorded unfiltered.
- **factory_boy for test data.** Handy for many models, but one more dependency; plain builder functions are enough for now.
- **No property tests.** Fewer dependencies, but hand-picked cases miss edge cases in date arithmetic, which is where coverage bugs are likely.
- **Cypress for end-to-end.** Mature, but Playwright is faster, supports axe directly and runs headless without extra setup.

## Consequences

- Dependencies to approve when each phase starts:
  - backend: pytest, pytest-django, pytest-socket, respx, hypothesis, coverage;
  - frontend: vitest, @testing-library/react, msw, @playwright/test, @axe-core/playwright.
- QA owns `backend/tests/fixtures/`, the rules tests, `scripts/record_fixtures.py` usage notes and `docs/testing/`. The data engineer writes the recording script; the owner runs it.
- Docker must be running for backend tests.
- Fixtures age; the drift check and re-recording keep them close to the live APIs.
