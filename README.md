# Placar Parlamentar

A civic-transparency tool that summarizes the public activity of Brazilian federal legislators (deputados and senadores) and their parties, using only official open-data sources. Every summary links back to the official record so each claim can be checked.

## What it does

- Pulls public legislative records from the Câmara dos Deputados and Senado Federal open-data APIs.
- Shows, for each official: bills authored, votes cast, committee attendance, plenary attendance, and official speeches.
- Generates neutral, source-linked summaries of each official's public activity over a chosen time window.
- Lets users compare two or more officials, or parties, side by side on the same metrics and the same window.
- Applies date filters and minimum-coverage thresholds so comparisons are fair (for example, only officials who held the seat for at least a set share of the window).
- Publishes separate leaderboards per metric, with the full methodology shown next to each one.

The MVP state of each item is in [`docs/mvp-status.md`](docs/mvp-status.md). Committee attendance (decision 0014) and leaderboards (Phase E, decision 0020) are left out of the MVP.

## What it does not do

- No social media, personal accounts, family information, or private life data.
- No personal data about users: no accounts, no location history, no tracking.
- No judgments: summaries describe what the record shows. No "good" or "bad" labels.
- No composite score unless its weights are published and user-adjustable.

## Principles

1. **Public records only.** Data comes from official open-data APIs.
2. **Source-linked.** Every number and statement links to the underlying official record.
3. **Fair comparisons.** Same metrics, same window, same data source. Metrics are normalized to the time each person actually held the seat.
4. **Neutral.** Factual descriptions and sortable metrics, not verdicts.
5. **Transparent methodology.** Every metric, window and threshold is documented in the app.

## Data sources

- Câmara dos Deputados Dados Abertos API (`dadosabertos.camara.leg.br`)
- Senado Federal Dados Abertos API (`legis.senado.leg.br/dadosabertos`)

Every endpoint used was checked against the official API documentation in Phase A; gaps and inconsistencies found in the official data are listed in [`docs/data-issues.md`](docs/data-issues.md).

## Stack

Decided in `docs/decisions/` (index in [`docs/decisions/README.md`](docs/decisions/README.md)); binding rules in [`docs/architecture-rules.md`](docs/architecture-rules.md).

- Backend: Django 6.1 + Django Ninja, Python 3.14 with uv (decision 0005).
- Storage: PostgreSQL 18 in Docker for normalized records; raw official responses cached as files in `data/raw/` (decision 0006).
- Frontend: React + TypeScript + Vite, linked to the backend only by the OpenAPI contract `docs/api/openapi.json` (decisions 0009, 0017).
- Summaries (Phase D): built from structured records only, every sentence tied to its sources and checked by a validator; template summaries by default, model summaries (Claude API) only after `generate_summaries` is run with a key in `.env` (decisions 0010, 0018).
- Tests: pytest, Vitest and Playwright, all offline on recorded fixtures (decision 0011).
- Team and agents: `.claude/agents/` (decision 0001). Project prompt: `CLAUDE_CODE_PROMPT.md`.

## Local setup (development)

Requirements: [uv](https://docs.astral.sh/uv/) (Python 3.14 is installed by uv if needed), Docker, and `gitleaks` (`brew install gitleaks`).

1. Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.
2. Turn on the secret-scanning hook: `git config core.hooksPath scripts/git-hooks`
3. Install the backend: `cd backend && uv sync`
4. Run the tests (offline): `uv run pytest`
5. Fetch the current legislature into the local cache (live requests to the official APIs, a few minutes on the first run): `uv run python manage.py fetch_current`
   - `--limit N` fetches details for only the first N people; `--refresh` downloads again even if the cache is fresh.
6. Optional, by hand:
   - record test fixtures from the cache: `python3 scripts/record_fixtures.py` (add `--fetch` to download missing cases);
   - compare the live APIs with the fixtures: `python3 scripts/check_upstream.py`.

The PostgreSQL database (`docker compose up -d db`) is needed from Phase B on.

### Frontend (React)

Requirements: Node 24 (24.15 or later recommended; see `frontend/.nvmrc`).

1. `cd frontend && npm ci`
2. Development server: `npm run dev` → http://127.0.0.1:5173 (requests to `/api` go to Django on 127.0.0.1:8000).
3. Checks: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`.
4. End-to-end tests (real browser, offline, with accessibility checks). They use their own database, so the development data is never replaced:
   - once: `docker compose exec db createdb -U <DATABASE_USER> placar_e2e` and `npx playwright install chromium`;
   - load the recorded fixtures: `cd backend && DATABASE_NAME=placar_e2e uv run python manage.py load_fixture_snapshot`;
   - run: `cd frontend && npm run e2e`.

## Run the app on the real snapshot

The app serves a snapshot of official data (decision 0015); it never calls the official APIs while serving pages. With `.env` filled in and Docker running:

1. Database: `docker compose up -d db`, then `cd backend && uv run python manage.py migrate`.
2. Download the official data into `data/raw/` (live, polite requests; the activity download takes hours on the first run and resumes from the cache):
   - people and time in office: `uv run python manage.py fetch_current`
   - activity (bills, sessions, votes, speeches): `uv run python manage.py fetch_activity --date YYYY-MM-DD`
3. Load the snapshot into the database (offline, from the cache): `uv run python manage.py normalize_current --date YYYY-MM-DD`, then `uv run python manage.py normalize_activity --date YYYY-MM-DD` with the same date.
4. API: `uv run python manage.py runserver 127.0.0.1:8000` (read-only, under `/api/`).
5. App: `cd frontend && npm run dev`, then open http://127.0.0.1:5173.

To try the app without downloading anything, load the recorded fixtures (2 deputies, 3 senators) into the `placar_e2e` database as in step 4 of the frontend section, and start the API with `DATABASE_NAME=placar_e2e`.

## Workflow (contributing)

Decision 0016 defines the workflow:

- `main` always passes all checks. Work happens on short branches: `feat/<phase>-<topic>`, `fix/<topic>`, `docs/<topic>`, `chore/<topic>`.
- Every commit runs the pre-commit hook: secret scan (gitleaks), backend lint (ruff) and, when frontend files change, frontend lint and type check.
- Before merging into `main`, run `scripts/check.sh`. It runs lint, the full test suite (Docker must be running), the dependency audit and a secret scan of the branch. Merge with `git merge --no-ff` after the owner approves.
- Each phase the owner signs off is tagged on `main` (`phase-a`, `phase-b1`, …).
- GitHub Actions (`.github/workflows/ci.yml`) runs the same checks on every push and pull request. It uses no secrets.

## Status

Phases A and B1 are on `main`; B2 (activity) and Phase C (API, pages, end-to-end tests) are built on branches waiting for review. Phase D (summaries) is built on a branch. The MVP is phases A–D; rankings (Phase E) come after it (decision 0020). Details and the remaining steps: [`docs/mvp-status.md`](docs/mvp-status.md).

## Data held

Only public records of elected officials in their public role; nothing about visitors. Details: [`docs/data-inventory.md`](docs/data-inventory.md).

## License

MIT (see [`LICENSE`](LICENSE)). Personal project, owned solely by its author. Not developed under any employer, client, university or company resources.