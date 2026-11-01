# 0013 — Deployment target

- **Status:** proposed
- **Date:** 2026-11-01
- **Stage:** 2 (topic 10 of 10)

## Context

The project prompt keeps deployment out of scope for the MVP unless the project owner decides otherwise. Publishing or deploying anything needs the owner's approval (0002). Several earlier decisions left items for this decision:

- the ASGI server choice (0005);
- server rendering for search engines (0009);
- continuous integration (0011);
- HTTPS settings, web server access logs without IPs, and visitor rate limiting (0012).

## Decision

1. **No deployment in the MVP.** The app runs only on the owner's machine:
   - PostgreSQL in Docker bound to `127.0.0.1` (0006);
   - Django development server on `127.0.0.1:8000`;
   - Vite development server, proxying `/api` to Django (0009).
2. No hosting accounts, domains, public URLs, CI services or remote repositories are created for the MVP.
3. **Deferred to a future deployment decision**, which must supersede this one:
   - host and region;
   - ASGI/WSGI server;
   - how the frontend build is served;
   - HTTPS and HSTS;
   - access logs without visitor IPs;
   - visitor rate limiting without stored IPs;
   - CI and automated audits;
   - production secrets handling;
   - backups;
   - where cached data and photos are stored;
   - whether server rendering is needed.
4. Code should not block a later deployment: settings come from environment variables, and `asgi.py` and `wsgi.py` are kept (0005).

## Alternatives considered

- **Choose a host now** (for example a small VPS or a platform service). It would let the project publish early, but it adds cost, accounts and operational work before the features exist, and every choice above would be made without real usage data.
- **Static export of the frontend to a free static host, backend local only.** The site needs the API for filters and comparisons, so a static-only version would show little.

## Consequences

- The MVP is complete when it works locally and passes all tests; "done" never means "published".
- Visitor-facing protections that only matter in production (HTTPS, access logs, rate limiting) are written down as requirements but not built yet.
- Publishing the project later needs a new decision and the owner's explicit approval.
