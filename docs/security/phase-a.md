# Phase A — security review

- **Date:** 2026-11-01
- **Reviewer:** main Claude Code session (security engineer role)

| Check | How | Result |
| --- | --- | --- |
| Secrets in the working tree | `gitleaks dir --redact backend` | No leaks found |
| Secrets in git history | pre-commit hook on every commit; full-history scan before Phase A (`gitleaks git`) | No leaks found |
| `.env` ignored, `.env.example` names only | read `.gitignore` and `.env.example` | OK: all values empty |
| Django refuses to start without `DJANGO_SECRET_KEY` | ran `django.setup()` with an empty key | `ImproperlyConfigured` raised |
| Python dependency vulnerabilities | `uv run pip-audit` | No known vulnerabilities found |
| Security lint | `uv run ruff check` with the `S` rules, on `backend/` | All checks passed. `scripts/` is outside this lint scope; its two `subprocess.call` uses were reviewed by reading: fixed `uv` commands, no shell, user arguments passed as list items |
| Requests only to official https hosts | `is_official_url` allowlist; redirects followed only to official hosts; tests | OK |
| Polite request rate | throttle capped at 2 req/s; one request at a time; retries honor `Retry-After` with capped backoff; tests | OK |
| Personal data | parsers keep only allowlisted fields; `/deputados/{id}` not called; fixture recorder strips personal keys; rule test checks fixtures; grep for `@` and `"cpf"` in fixtures | OK: 17 fixtures pass, grep found nothing |
| Cookies and headers in cache | envelope stores only listed fields; test checks `set-cookie` is not stored | OK |
| Logging | logs contain URLs and retry reasons only; no visitor data (no public site yet) | OK |

## Pre-commit hook finding (2026-11-01)

The gitleaks hook blocked the commit of the 17 recorded fixtures: rule `generic-api-key` matched the `_fixture.cache_key` field (a SHA-256 hash of the public API URL, not a secret). Fix: the field was renamed `cache_file_id` and the fixtures were re-recorded from the cache. The scanner rules were not weakened. Rescan: no leaks found.

## Open risks

- `pip-audit` sends the dependency list (names and versions, not code) to public vulnerability databases. This is the approved tool in decision 0012.
- Fixture recording and the live run made real requests (about 1,060 in total, at most 2 per second); both were approved by the owner.
- `.env` was created by the session with generated values written directly to the file (mode 600) and never displayed.
