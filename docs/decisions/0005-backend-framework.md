# 0005 — Backend framework and project layout

- **Status:** proposed
- **Date:** 2026-11-01
- **Stage:** 2 (topic 2 of 10)

## Context

The backend fetches official Câmara and Senado data, stores and normalizes it, computes metrics, produces source-linked summaries, and serves an HTTP API to the React frontend (decision 0004). The project owner prefers Django and asked whether it can work asynchronously.

Facts checked on 2026-11-01:
- Django 6.1.2 is the current release. PyPI lists support for Python 3.12, 3.13 and 3.14 (not 3.15). Python 3.14 is installed on the development machine.
- Django docs (6.1, "Asynchronous support"): async views are supported and run efficiently under ASGI. Every query method has an async variant (`afirst()`, `acreate()`, `async for`). **Transactions do not work in async mode**; the docs recommend putting transactional code in a sync function called with `sync_to_async()`.
- Django docs (6.1, "Tasks framework"): the built-in backends are "for development and testing only"; Django "does not provide a worker mechanism".
- Django REST Framework (3.18.3) has no async views; the async add-on `adrf` is at 0.1.14.
- Django Ninja 1.7.3 supports sync and async views, uses Pydantic 2 schemas, and generates an OpenAPI description.

Where async matters in this project:
- Upstream fetching is rate-limited to about 2 requests per second, so async gives little speed gain.
- The frontend API is mostly database reads; sync views are fast enough.
- LLM summaries are slow; they are better generated ahead of time and stored than produced during a request.

## Decision

1. **Framework:** Django 6.1 with **Django Ninja** for the HTTP API.
2. **Python:** 3.14, managed with `uv`. Revisit when Django lists 3.15 support.
3. **Async policy:**
   - Views are sync by default. A view may be async only when it waits on something other than the database.
   - Code that writes to the database runs sync, inside transactions.
   - Source clients may use an async HTTP client internally (for example, to wait politely between requests), called from management commands.
   - `asgi.py` is kept so the app can run under an ASGI server later. The server choice is part of the deployment decision.
4. **Data fetching:** runs as Django management commands (for example `fetch_camara`, `fetch_senado`), not inside web requests.
5. **Layout** (inside `backend/`):

```
backend/
├── pyproject.toml
├── manage.py
├── config/                 settings (base, dev, test), urls, asgi.py, wsgi.py
├── placar/
│   ├── sources/            Câmara and Senado clients, raw cache, fetch commands
│   ├── legislators/        officials, parties, mandates, leaves, party switches
│   ├── activity/           bills, votes, attendance, speeches
│   ├── metrics/            coverage() and metrics; plain Python, no web code
│   ├── summaries/          LLM summary feature, kept separate
│   └── api/                Ninja routers and response schemas (OpenAPI)
└── tests/
```

   The exact responsibilities and allowed imports between these apps are set in the module-boundaries decision (topic 4).

6. **Django admin:** enabled as a **local tool for the project owner only**:
   - Only in development settings; the admin URL is not included in any other settings.
   - Models holding official data are **read-only** in the admin, so records always match their official source.
   - The admin account is created locally by the owner; its password is never written in code, docs, `.env.example` or git.
   - This is not a visitor account. The public site has no accounts or logins (non-negotiable rule 5).

## Alternatives considered

- **FastAPI.** Async by default, light, built-in OpenAPI. Needs SQLAlchemy and Alembic for the database and a separate admin solution. A good fit too; not chosen because the owner prefers Django and Django brings migrations, management commands and the admin.
- **Django + Django REST Framework.** More mature and better known; sync only, and OpenAPI needs an extra package (`drf-spectacular`). Ninja gives typed schemas and OpenAPI with less code.
- **Django with a single app (`core/`).** Simpler start, but weaker boundaries between areas and more overlap in agent file ownership.
- **Fully async Django.** Little gain here (rate-limited upstream, read-heavy API) and transactions do not work in async mode.

## Consequences

- The frontend can use the OpenAPI description from Ninja as its API contract (details in the frontend decision).
- The data engineer owns `placar/sources/`; the backend engineer owns `legislators/`, `activity/`, `metrics/`, `summaries/`, `api/` and `config/` (to be confirmed with topic 4).
- New dependencies to approve when Phase A starts: `django`, `django-ninja`, an HTTP client (`httpx`), and test tools (decided in the testing decision).
- Background jobs for summaries need a worker outside Django; chosen in the summaries decision (topic 7).
- The admin must be checked in every security review to stay local-only and read-only for official data.
