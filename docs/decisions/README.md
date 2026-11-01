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
| [0010](0010-summaries.md) | Summaries: isolated LLM adapter, fact sheets, validator, template fallback | accepted | 2026-11-01 |
| [0011](0011-testing.md) | Testing: offline pytest/Vitest/Playwright, hand-recorded fixtures without personal fields | accepted | 2026-11-01 |
| [0012](0012-security-baseline.md) | Security baseline: secrets, dependencies, input, upstream limits, untrusted content, logging | accepted | 2026-11-01 |
| [0013](0013-deployment.md) | Deployment: none in the MVP, local only; deferred items listed | proposed | 2026-11-01 |

## Stage 2 topics

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
| 10. Deployment target (out of MVP scope unless decided) | 0013 | proposed |
