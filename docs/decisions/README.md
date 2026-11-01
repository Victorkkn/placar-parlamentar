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

## Stage 2 topics

| Topic | Decision | State |
|---|---|---|
| 1. Repository layout | 0004 | accepted |
| 2. Backend framework and project layout | 0005 | accepted |
| 3. Database and raw response cache | 0006 | accepted |
| 4. Module boundaries | 0007 | accepted |
| 5. Normalizing Câmara and Senado data | — | not started |
| 6. Frontend framework, build tooling, link to backend | — | not started |
| 7. Isolating the summary feature, enforcing source links | — | not started |
| 8. Testing strategy and offline fixtures | — | not started |
| 9. Security baseline | — | not started |
| 10. Deployment target (out of MVP scope unless decided) | — | not started |
