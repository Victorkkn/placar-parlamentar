# 0007 — Backend module boundaries

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 2 (topic 4 of 10)

## Context

Decision 0005 set the backend apps: `sources`, `legislators`, `activity`, `metrics`, `summaries`, `api`. This decision sets what each one does, what it may use, and how the rules are checked. Clear boundaries matter because:

- different agents own different apps (data engineer vs backend engineer);
- metrics must be testable without a database or web code;
- the summary feature must only see structured records with source links;
- the API must never call the official APIs or change official data.

## Decision

### Architecture style

- **Modular monolith:** one deployable backend, split into apps with enforced dependency rules.
- **Layered:** dependencies point one way: `core` → data apps (`legislators`, `activity`) → logic (`metrics`, `summaries`) → `api`. `sources` feeds the data apps.
- **Services and selectors** (from the HackSoft Django Styleguide): each data app exposes `services.py` for writes and `selectors.py` for reads.
- **Functional core, imperative shell** in `metrics`: pure functions on plain `core` types, with a thin selector layer that loads data.
- **Not hexagonal or Clean Architecture:** Django models are the domain models (no separate domain objects or repositories). Only two parts are adapter-style: the official API clients in `sources` and the language model adapter in `summaries`.

### Apps and responsibilities

| App | Does | Does not |
| --- | --- | --- |
| `core` (new) | Shared plain-Python types used everywhere: `SourceRef` (official URL, cache key, label), `DateWindow`, `Period`, and shared errors. No Django models, no imports from other apps. | Hold data or logic specific to one area. |
| `sources` | Clients for the Câmara and Senado APIs, the raw file cache (decision 0006), rate limiting, normalizers that turn raw responses into records, and the fetch management commands. | Serve HTTP, compute metrics, or write to the database directly; it writes only through `legislators` and `activity` services. |
| `legislators` | Models and logic for officials, parties, mandates, exercise periods (including substitutes and leaves) and party affiliations. | Know where data came from beyond the stored `SourceRef`. |
| `activity` | Models for bills authored, votes, sessions, committee memberships and attendance, plenary attendance, speeches. Links to `legislators`. | Compute metrics. |
| `metrics` | `coverage(official, window)` and every metric. A pure-Python core working on `core` types, plus `selectors.py`, which loads the needed data from `legislators` and `activity`. May store computed results in its own tables if Phase B needs it. | Import Django web code, call official APIs, or change official records. |
| `summaries` | The summary feature: builds the input from structured records and metrics, calls the language model through one isolated adapter, and checks that every sentence has a `SourceRef`. Details in topic 7. | Read raw API responses, call official APIs, or change official records. |
| `api` | Django Ninja routers and response schemas. Validates input, calls selectors of the other apps, returns values with their `SourceRef`s. | Contain business logic, write to the database, or call official APIs. |

### Allowed dependencies

An app may import only the apps listed for it:

```text
core          → (nothing)
legislators   → core
activity      → core, legislators
sources       → core, legislators, activity     (through their services)
metrics       → core, legislators, activity     (through their selectors)
summaries     → core, legislators, activity, metrics
api           → core, legislators, activity, metrics, summaries
```

- Nothing imports `api`.
- Only `sources` imports from `sources`; nothing else may reach the official APIs.
- No cycles.

### How apps talk to each other

- Each data app (`legislators`, `activity`) exposes:
  - `selectors.py` for reads,
  - `services.py` for writes.
  Other apps use these, not the other app's models or queries directly. Foreign keys between models are allowed.
- Every value that leaves `metrics` or `summaries` carries the `SourceRef`s it was computed from, so the API can always return the source link.
- Official records are written only by `sources` through `services.py`. The API and the admin are read-only for official data (decision 0005).

### Checking the rules

- A test in `backend/tests/` reads every module's imports (with Python's `ast`, no new dependency) and fails if an import breaks the table above.
- A second test fails if `metrics/` imports anything from `django.http`, `ninja` or `sources`.

## Alternatives considered

- **No shared `core` app; put `SourceRef` and `DateWindow` in `legislators`.** Fewer apps, but metrics and summaries would depend on `legislators` just for basic types, and the types would end up mixed with models.
- **Hexagonal / Clean Architecture** (separate domain objects, repositories, ports and adapters for persistence). Keeps business logic independent of Django, but needs two copies of every model plus mapping code, and gives up much of the ORM, admin and migrations that motivated choosing Django (0005). The hard logic (metrics) already gets the main benefit through the pure core.
- **Free imports between apps, rules only in docs.** Less code, but boundaries erode quickly when several agents work in parallel.
- **`import-linter` package to check the rules.** Mature and expressive, but it is one more dependency; the `ast` test covers what we need. Can be adopted later by a new decision.
- **A separate `ingestion` app for normalizers, apart from `sources`.** Cleaner split between fetching and mapping, but both belong to the data engineer and change together; kept in `sources` as sub-packages (`clients/`, `cache/`, `normalize/`).

## Consequences

- `core` is added to the backend layout from decision 0005 (an addition, not a change of the accepted layout).
- Ownership:
  - data engineer owns `sources/`;
  - backend engineer owns `core/`, `legislators/`, `activity/`, `metrics/`, `summaries/`, `api/` and `config/`;
  - QA owns the boundary tests.
- Metrics can be unit-tested with plain data, without a database.
- Adding a new dependency between apps needs a new decision.
