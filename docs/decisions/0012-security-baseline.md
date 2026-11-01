# 0012 — Security baseline

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 2 (topic 9 of 10)

## Context

Placar Parlamentar is a public, read-only site built on public data. The main risks are:

- leaking secrets (database password, Anthropic API key, Django secret key);
- vulnerable or unmaintained dependencies;
- bad input to our API;
- overloading the official APIs;
- harmful text or URLs arriving inside official API fields;
- collecting visitor data by accident (logs, third-party requests).

Earlier decisions already cover parts of this:

- secrets only in `.env` (rule 6, 0006, 0010);
- admin only in development, read-only for official data (0005);
- no free API text sent to the model, plus a validator (0010);
- no third-party requests from the browser (0009);
- personal fields removed from fixtures (0011).

Versions checked on 2026-11-01: ruff 0.17.3 (local copy installed), pip-audit 2.10.1, gitleaks v8.30.1 (not installed). `npm audit` comes with npm.

## Decision

### 1. Secrets

- Secrets only in the git-ignored `.env`. `.env.example` lists variable names only (`DJANGO_SECRET_KEY`, `DATABASE_*`, `ANTHROPIC_API_KEY`, `SUMMARY_MODEL`).
- Django refuses to start outside development if `DJANGO_SECRET_KEY` is missing.
- **gitleaks** scans staged changes in a local git pre-commit hook, and scans the full history before any push the owner approves.
- Secrets are never printed in logs, errors, test output or reports. If one leaks, it is rotated and the leak is recorded.

### 2. Dependencies

- Every new dependency needs the owner's approval (0002). The security engineer first reviews its purpose, maintenance, license and known vulnerabilities.
- Exact versions are pinned in lockfiles (`uv.lock`, `package-lock.json`), which are committed.
- **pip-audit** and **npm audit** run before each phase is reported done; findings go in the security review note.
- No automatic dependency-update tools for now.

### 3. Input validation (our API)

- The public API is **read-only**: only `GET` (and `HEAD`) are allowed.
- Every parameter is validated by Django Ninja / Pydantic schemas:
  - dates are ISO dates between 1988-10-05 (Constitution) and today; start is before end; the longest window is one legislature span (to be confirmed in Phase C);
  - the coverage threshold is a share between 0 and 1, or a number of days between 0 and the window's length;
  - official ids are positive integers; a comparison has between 2 and 6 officials;
  - lists are paginated with a maximum page size.
- Invalid input returns a 4xx error with a short message and no stack trace.

### 4. Polite use of the official APIs

- At most 2 requests per second per API, one request at a time per API, with small random delays; batch runs avoid exact round clock times (Senado guidance).
- `429` and `5xx` responses: honor `Retry-After`, otherwise exponential backoff, with a retry limit; then stop and report.
- Requests send a `User-Agent` naming the project (no personal email).
- Deprecation headers (`Deprecation`, `Sunset`) from the Senado are logged as data issues.

### 5. Untrusted content from official APIs

- All text from APIs is treated as untrusted:
  - React escapes it by default, and `dangerouslySetInnerHTML` is banned (lint rule);
  - the Django admin escapes it by default.
- **URLs from APIs** (record pages, photos) are used only if they are `https` and on an allowlist of official domains (`camara.leg.br`, `senado.leg.br` and their subdomains). Other URLs are dropped and logged.
- **Official photos are downloaded during ingestion and served by our own server**, so visitors' browsers do not contact official sites just by viewing a page (0009, item 11).
- No free API text goes to the model in the MVP (0010).

### 6. Logging and visitor privacy

- Application logs never contain visitor IP addresses, user agents, cookies, or full request headers. They may contain the path, status code, duration and error type.
- The public site sets no cookies. The admin's session and CSRF cookies exist only in development (0005).
- No analytics or tracking of any kind.
- Server access logs (for example from a web server in front of Django) are part of the deployment decision and must follow the same rule.
- Rate limiting of visitors, if needed, is done in memory or at the server in front, without storing IPs. It is set in the deployment decision.

### 7. Web security settings (outside development)

- `DEBUG = False`, `ALLOWED_HOSTS` set, Django's security middleware on.
- HTTPS-only settings (secure redirects, HSTS) are applied in the deployment decision.
- Response headers: a Content Security Policy that allows only our own origin (`default-src 'self'`, no inline scripts), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and `frame-ancestors 'none'`.

### 8. Code checks

- Backend: **ruff** with its security rules (the `S` set, based on bandit) is part of the lint step.
- Frontend: TypeScript strict mode and a lint rule banning `dangerouslySetInnerHTML`.

### 9. Reviews

- The security engineer writes a review note per phase in `docs/security/`. It covers secrets, dependency audits, input validation, logging, third-party requests and personal data, with how each was checked and the real result.
- Open risks are listed for the owner.

## Alternatives considered

- **detect-secrets instead of gitleaks.** Python-based and baseline-driven; gitleaks is faster and scans history easily. Either works; gitleaks needs installing with Homebrew.
- **Show official photos directly from official sites.** No storage needed, but every page view would send visitors' IP addresses to third-party servers, against decision 0009.
- **Bandit as a separate tool.** Same checks are available inside ruff, which is already planned for linting.
- **Automatic dependency updates (Dependabot/Renovate).** Useful with CI and a remote host; neither exists yet.
- **IP-based visitor rate limiting with stored counters.** Effective, but it stores visitor data; deferred to the deployment decision with an in-memory or front-server approach.

## Consequences

- Tools to approve: gitleaks (Homebrew) now for the pre-commit hook; ruff and pip-audit when the backend is set up.
- Ingestion must download and store official photos (in `data/`, git-ignored), with a `SourceRef` to the original URL.
- The deployment decision must cover HTTPS, access logs without IPs, and visitor rate limiting.
- Each phase ends with a security review note before it is reported done.
