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
| Security lint | `uv run ruff check` with the `S` rules | All checks passed (two `S603` uses in `scripts/` are fixed commands without a shell, marked inline) |
| Requests only to official https hosts | `is_official_url` allowlist; redirects followed only to official hosts; tests | OK |
| Polite request rate | throttle capped at 2 req/s; one request at a time; retries honor `Retry-After` with capped backoff; tests | OK |
| Personal data | parsers keep only allowlisted fields; `/deputados/{id}` not called; fixture recorder strips personal keys; rule test checks fixtures | OK (fixture check runs once fixtures exist) |
| Cookies and headers in cache | envelope stores only listed fields; test checks `set-cookie` is not stored | OK |
| Logging | logs contain URLs and retry reasons only; no visitor data (no public site yet) | OK |

## Open risks

- `pip-audit` sends the dependency list (names and versions, not code) to public vulnerability databases. This is the approved tool in decision 0012.
- Fixture recording and the live run make real requests; both are run or approved by the owner.
