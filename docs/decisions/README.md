# Decisions — Placar Parlamentar

One file per decision. Statuses: proposed, accepted, superseded.
An accepted decision is changed only by a new decision that supersedes it, after the project owner approves it.

| # | Decision | Status | Date |
|---|---|---|---|
| [0001](0001-team-and-roles.md) | Team and roles | accepted | 2026-11-01 |
| [0002](0002-git-and-approval-gates.md) | Git workflow and approval gates (no push without approval) | accepted | 2026-11-01 |
| [0003](0003-languages.md) | Languages: pt-BR interface, English code and docs | accepted | 2026-11-01 |
| [0004](0004-repository-layout.md) | Repository layout: monorepo with `backend/` and `frontend/` | accepted | 2026-11-01 |
| [0005](0005-backend-framework.md) | Backend: Django 6.1 + Django Ninja, sync by default, local read-only admin | accepted | 2026-11-01 |
| [0006](0006-database-and-raw-cache.md) | PostgreSQL 18 in Docker; raw API responses cached as files | accepted | 2026-11-01 |
| [0007](0007-module-boundaries.md) | Backend module boundaries, allowed imports, `core` app | accepted | 2026-11-01 |
| [0008](0008-source-normalization.md) | Normalizing Câmara and Senado into one model (service periods, leaves, affiliations) | accepted | 2026-11-01 |
| [0009](0009-frontend.md) | Frontend: React + TypeScript + Vite SPA, OpenAPI contract file, no third-party requests | accepted | 2026-11-01 |
| [0010](0010-summaries.md) | Summaries: isolated LLM adapter, fact sheets, validator, template fallback | accepted (list location in item 7 superseded by 0018) | 2026-11-01 |
| [0011](0011-testing.md) | Testing: offline pytest/Vitest/Playwright, hand-recorded fixtures without personal fields | accepted | 2026-11-01 |
| [0012](0012-security-baseline.md) | Security baseline: secrets, dependencies, input, upstream limits, untrusted content, logging | accepted | 2026-11-01 |
| [0013](0013-deployment.md) | Deployment: none in the MVP, local only; deferred items listed | accepted (item 2 partly superseded by 0016) | 2026-11-01 |
| [0014](0014-metric-methodology-choices.md) | Methodology: leave days, bills authored, no Senado attendance, committee attendance deferred | accepted | 2026-11-01 |
| [0015](0015-mvp-data-snapshot.md) | MVP runs on a snapshot of official data; no mocked numbers | accepted | 2026-11-01 |
| [0016](0016-git-workflow-and-ci.md) | Git workflow (branches, local checks) and GitHub Actions CI; supersedes part of 0013 | accepted | 2026-11-01 |
| [0017](0017-typescript-version.md) | TypeScript 5.9.3 for the frontend; supersedes the version clause of 0009 | accepted | 2026-11-01 |
| [0018](0018-single-banned-wording-list.md) | One banned-wording list (`docs/wording/banned-pt-BR.txt`) for app and summaries; supersedes the list location in 0010 | accepted | 2026-11-01 |

## Stage 2 topics

Stage 2 completed on 2026-11-01: all ten topics accepted.

| Topic | Decision | State |
|---|---|---|
| 1. Repository layout | 0004 | accepted |
| 2. Backend framework and project layout | 0005 | accepted |
| 3. Database and raw response cache | 0006 | accepted |
| 4. Module boundaries | 0007 | accepted |
| 5. Normalizing Câmara and Senado data | 0008 | accepted |
| 6. Frontend framework, build tooling, link to backend | 0009 | accepted |
| 7. Isolating the summary feature, enforcing source links | 0010 | accepted |
| 8. Testing strategy and offline fixtures | 0011 | accepted |
| 9. Security baseline | 0012 | accepted |
| 10. Deployment target (out of MVP scope unless decided) | 0013 | accepted |
