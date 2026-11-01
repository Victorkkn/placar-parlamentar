# Phase C — security review (C1–C5)

- **Date:** 2026-11-01
- **Reviewer:** main Claude Code session (security engineer role)
- **Scope:** read-only API (C1), typed client and pages (C2–C3), end-to-end tests and CI job (C5)

| Check | How | Result |
| --- | --- | --- |
| Read-only API | Only `GET` routes; tests check `POST` and `DELETE` give 405 | OK |
| Input validation (decision 0012) | Dates between 1988-10-05 and the snapshot date; start before end; one threshold kind; share in [0, 1]; days within the window; house and state from fixed lists; page size ≤ 100; 2–6 distinct ids for compare | OK; 4xx with a short pt-BR message, no traceback (tested) |
| No personal data about visitors | No accounts, cookies or sessions in the API, and nothing about requests is stored (the local development server only prints request lines to the terminal); ESLint bans `localStorage` and `sessionStorage` | OK |
| No third-party requests | No external fonts, scripts or CDNs; the e2e test fails if any request leaves `127.0.0.1` | OK |
| Untrusted text from the APIs | React escapes all text; `dangerouslySetInnerHTML` banned by lint (tested) | OK |
| Links to official records | Built only from `SourceRef` URLs, which the HTTP client restricts to `https` official hosts (`camara.leg.br`, `senado.leg.br`) | OK |
| e2e cannot replace development data | `load_fixture_snapshot` refuses databases not ending in `_e2e` (tested) | OK |
| CI | No secrets; `permissions: contents: read`; actions pinned to commit SHAs; gitleaks checksum-verified | OK |
| Backend dependency audit | `uv run pip-audit` | No known vulnerabilities |
| Frontend production audit | `npm audit --omit=dev` | 0 vulnerabilities |
| Frontend development audit | `npm audit` | Same single advisory as C0: `minimatch` < 11.0.1 (GHSA-g3hv-75wg-m249), through ESLint, typescript-eslint and openapi-typescript (`@redocly/openapi-core`). Dev tools only, not in the built app. **Accepted risk**, unchanged from `phase-c0.md`; recheck when the tools update |

## Notes for the owner

- The API has no rate limit. It runs only locally in the MVP (decision 0013); a public deployment needs a new decision covering rate limits and caching.
- Django's development server is used locally only; it is not a production server.
