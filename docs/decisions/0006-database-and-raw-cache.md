# 0006 — Database and raw API response cache

- **Status:** proposed
- **Date:** 2026-11-01
- **Stage:** 2 (topic 3 of 10)

## Context

The backend is Django 6.1 (decision 0005). It needs:
- a database for normalized records (officials, mandates, votes, attendance, bills, speeches) and computed metrics;
- a local cache of raw responses from the official APIs, so repeated runs do not hit them again, and every stored record can be traced to the exact response it came from.

The README suggests PostgreSQL plus a local raw cache. Facts checked on 2026-11-01:
- PostgreSQL 18 is the current major release (18.6; supported until 2030-11). `psycopg` 3.3.6 is the current Python driver, supported by Django.
- On the development machine PostgreSQL is not installed; Docker is.
- The Senado API documents a limit (over 10 requests per second can get HTTP 429). The Câmara API documents none, but returned a timeout with `retry-after: 30` in a spot check.

## Decision

### Database
1. **PostgreSQL 18** for all normalized data, using Django's PostgreSQL backend with `psycopg` 3.
2. Locally it runs in **Docker** through a `compose.yaml` at the repo root that defines only the database service.
   - The port is bound to `127.0.0.1` only.
   - The database name, user and password come from the git-ignored `.env`; `.env.example` lists the variable names with no values.
   - Data lives in a named Docker volume. Removing that volume counts as deleting data and needs the owner's approval (decision 0002).
3. Tests also run against PostgreSQL (a throwaway test database in the same container), so tests and real runs behave the same. Details in the testing decision.
4. PostgreSQL features (date ranges, constraints, window functions) may be used where the data model decision (topic 5) calls for them.

### Raw response cache
5. Raw responses are stored as **files** under `data/raw/` (git-ignored), not in the database:
   ```
   data/raw/<source>/<endpoint-path>/<key>.json.gz
   ```
   - `<source>` is `camara` or `senado`.
   - `<key>` is a SHA-256 hash of the method, full URL and sorted query parameters.
6. Each file holds an envelope: the request URL and parameters, fetch time (UTC), HTTP status, content type, the API version reported by the response when available, and the unchanged response body. Cookies and other request or response headers that are not needed are not stored.
7. Every normalized record stores its official source URL and the cache key of the response it came from.
8. **Freshness** is set per endpoint and configurable:
   - Data that no longer changes (closed legislatures, past votes, past sessions): kept with no expiry.
   - Data that changes (current officials, ongoing mandates, open bills): default refresh after 24 hours.
   - A `--refresh` option forces new downloads.
   - If the API fails and a cached copy exists, the cached copy is used and the record shows the date it was fetched.
9. Deleting or pruning the cache needs the owner's approval (decision 0002).
10. Test fixtures are copies of selected cache files, trimmed and moved into the test folder by the fixture script (testing decision).

## Alternatives considered

- **SQLite.** No server and nothing to install, and Django supports it well. Rejected as the main database because it has no date range types, has weaker handling of concurrent writes, and would differ from a likely PostgreSQL deployment. Could still be considered for quick experiments.
- **PostgreSQL installed with Homebrew instead of Docker.** Fewer moving parts, but the version is not pinned in the repo and setup differs between machines. Docker is already installed.
- **Raw cache inside PostgreSQL (JSONB table).** Queryable and backed up with the database, but it makes the database much larger, makes fixtures harder to extract, and ties cache cleanup to database operations.
- **An HTTP caching library (for example `hishel` for `httpx`).** Less code, but less control over per-endpoint freshness rules and over the envelope used for traceability and fixtures.

## Consequences

- Developers need Docker running to use the backend and run tests.
- New dependency to approve when Phase A starts: `psycopg` (with Django's PostgreSQL support).
- The cache can grow large (all votes and sessions of a legislature). Its size will be measured in Phase A and logged; any pruning needs approval.
- Every number shown can be traced from the record to its cache file and to the official URL.
- If deployment later needs a different setup, a new decision supersedes this one.
