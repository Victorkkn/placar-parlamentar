# Phase B1 — security review

- **Date:** 2026-11-01
- **Reviewer:** main Claude Code session (security engineer role)

| Check | How | Result |
| --- | --- | --- |
| New dependency `hypothesis` | approved in the Phase B plan; `uv run pip-audit` | No known vulnerabilities found |
| Secrets | pre-commit gitleaks hook on every commit; database password only in `.env` (generated, never displayed) | No leaks found |
| Database exposure | `compose.yaml` binds PostgreSQL to `127.0.0.1` only (`docker compose port db 5432` → `127.0.0.1:5432`) | OK |
| Personal data | models store only the decision 0008 allowlist (no CPF, birth data, e-mail, phones, social media) | OK |
| No network in normalization | `normalize_current` uses a cache-only fetcher with no HTTP client; test runs it with the network blocked | OK |
| Import boundaries | rules test covers `legislators`, `metrics`, `sources` | OK |
| SQL injection | all queries through the Django ORM; no raw SQL | OK |

## Notes

- `replace_house` deletes and recreates the derived rows of one house inside a transaction. It never touches the raw cache, which stays the source of truth.
