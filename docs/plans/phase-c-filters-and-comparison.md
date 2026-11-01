# Phase C — Filters and comparison (plan)

- **Status:** approved by the project owner on 2026-11-01, with decision 0017, the three defaults and the dependency list. C0 and C1 may run in parallel with the end of B2.
- **Date:** 2026-11-01
- **Decisions applied:** 0003, 0005, 0007, 0009, 0011, 0012, 0014, 0015, 0016, 0017

## Goal

A pt-BR React app, backed by a read-only API, where a visitor can:

- choose a time window: the current legislature, the last 2 years, or custom dates;
- set a minimum coverage, as days in office or as a share of the window;
- see officials below the minimum labeled **"Dados insuficientes"** with their covered period, never hidden;
- compare two or more officials side by side on the same metrics and window, with the window shown at the top;
- compare parties, with member counts and a label when membership changed during the window.

It runs on the data snapshot (decision 0015): every number has its source link, the snapshot date is shown, and unbuilt parts say "Ainda não disponível".

## Parallel work with B2

- **C0** (frontend setup) and **C1** (API) can start now, while Phase B2 finishes.
- **C1** uses the activity tables built in B2, which are already on the B2 branch. The C1 branch starts from it, or from `main` after B2 is merged.

## Tasks

| # | Task | Owner | Done when |
| --- | --- | --- | --- |
| C0 | Frontend setup in `frontend/`: Vite + React + TypeScript 5.9.3 (decision 0017), Node 24 pinned (`.nvmrc`, `engines`), React Router, TanStack Query, CSS Modules; ESLint with `react/no-danger`; Vitest + Testing Library + MSW; pt-BR text file `src/text/pt-BR.ts`; CI `frontend` job (lint, type check, tests) | frontend engineer | `npm run lint`, `npm run typecheck`, `npm test` pass locally and in CI; a placeholder page renders |
| C1 | Read-only API with Django Ninja under `/api/` (only `GET`/`HEAD`); input validation as in decision 0012; OpenAPI exported to `docs/api/openapi.json` with a staleness test | backend engineer | Endpoints below return values with `SourceRef`s; invalid input returns 4xx; the generic "every number has a source" test passes |
| C2 | Frontend types generated from `docs/api/openapi.json` (`openapi-typescript`) and calls through `openapi-fetch`; a check that types match the contract | frontend engineer | `npm run check:api` passes |
| C3 | Pages: officials list with filters; official page; comparison; parties. Window presets, threshold as days or share, filters in the URL, snapshot banner, `SourceValue` component for every number, "Dados insuficientes" and "Ainda não disponível" states | frontend engineer | Component tests pass; source-link and wording checks pass |
| C4 | pt-BR texts and methodology links in the app; neutral-wording review | technical writer, owner review | Owner approves the wording |
| C5 | End-to-end tests (Playwright, Chromium) offline against the local backend with fixture data, with axe accessibility checks | QA | `npm run e2e` passes |
| C6 | Test and security notes; README updates (how to run the app) | QA, security engineer, technical writer | Notes written; `pip-audit` and `npm audit` clean or explained |

## API (C1)

All endpoints are `GET`, read-only, and validated. Windows are limited to 1988-10-05 through the snapshot date. A threshold is either `min_days` (0 to the window's days) or `min_share` (0 to 1).

| Endpoint | Returns |
| --- | --- |
| `GET /api/meta` | Snapshot date (latest fetch time in the cache), current legislature, available metrics per house |
| `GET /api/officials?house&state&party&q&start&end&min_days\|min_share&page` | Officials with coverage (days, share, periods) and a `sufficient` flag; officials below the threshold included and flagged |
| `GET /api/officials/{id}?start&end` | Profile: periods in office, affiliations, leaves in the window, coverage, metrics (each with numerator, denominator, sources) or "not available" |
| `GET /api/compare?ids=1,2,…&start&end&min_days\|min_share` | 2 to 6 officials on the same window and metrics |
| `GET /api/parties?house&start&end` | Per party: members with any affiliation in the window, members at the window start and end, a `membership_changed` flag, and per-metric aggregates over members with sufficient coverage |

## Defaults to confirm

1. **Default minimum coverage:** 50% of the window. It can be changed to a number of days instead.
2. **"Last 2 years" preset:** the 730 days up to the snapshot date.
3. **Party aggregates:** median and range of each metric over members with sufficient coverage, shown next to the member count. No party-level "score".

## Dependencies to approve

**Backend:** `django-ninja` 1.7.3.

**Frontend runtime:** `react` 19.3.1, `react-dom` 19.3.1, `react-router` 8.5.1, `@tanstack/react-query` 5.105.1, `openapi-fetch` 0.17.0.

**Frontend development:**

- build and types: `vite` 8.3.5, `@vitejs/plugin-react` 6.1.2, `typescript` 5.9.3 (decision 0017), `openapi-typescript` 7.13.0;
- lint: `eslint` 10.14.0, `typescript-eslint` 8.72.1, `eslint-plugin-react` 7.37.5;
- tests: `vitest` 5.0.5, `@testing-library/react` 16.3.3, `@testing-library/jest-dom` 7.0.1, `jsdom` 30.1.3, `msw` 3.0.3;
- end-to-end (C5): `@playwright/test` 1.64.1, `@axe-core/playwright` 4.14.0.

## Risks

- **Large votes and attendance tables** (hundreds of thousands of rows) may make comparisons slow. Indexes are added in C1, and computed results can be stored later if needed.
- **Charts** are left out of Phase C. Tables come first (decision 0009, item 13).

## Outcome (2026-11-01)

- C0–C3 and C5 merged to `main` on 2026-11-01 (merge `424c20f`). The CI e2e job passed on its first GitHub run.
- C6 notes: `docs/testing/phase-c.md`, `docs/security/phase-c.md`. README updated.
- C4 wording approved by the owner on 2026-11-01. Phase C signed off on 2026-11-01 (tag `phase-c`).

