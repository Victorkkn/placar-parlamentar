# Placar Parlamentar

A civic-transparency tool that summarizes the public activity of Brazilian federal legislators (deputados and senadores) and their parties, using only official open-data sources. Every number and every summary sentence links back to the official record, so each claim can be checked.

The interface is in Brazilian Portuguese; code and documentation are in English.

## What it does

- Pulls public legislative records from the Câmara dos Deputados and Senado Federal open-data APIs.
- Shows, for each official: bills authored, votes cast, committee attendance, plenary attendance, and official speeches.
- Generates neutral, source-linked summaries of each official's public activity over a chosen time window.
- Lets users compare two or more officials, or parties, side by side on the same metrics and the same window.
- Applies date filters and minimum-coverage thresholds so comparisons are fair (for example, only officials who held the seat for at least a set share of the window).
- Publishes separate leaderboards per metric, with the full methodology shown next to each one.

### In the current version (MVP)

The MVP covers all of the above except committee attendance and leaderboards, which come next (see [Status and roadmap](#status-and-roadmap)). With the snapshot of 1 November 2026 it shows:

- **Officials list**:
  - every deputy and senator who served in the current legislature (since 1 February 2023), with days in office and coverage of the chosen period;
  - filters for house, state (UF), party and name;
  - period presets: current legislature, last 2 years, or custom dates;
  - a minimum time in office, as % of the period or in days. People below it are labeled **"Dados insuficientes"**, never hidden.
- **Official page**:
  - periods in office with official reasons (term, substitution, leave, resignation, …);
  - party affiliations;
  - the metrics:
    - **plenary attendance** (Câmara);
    - **bills authored** (PL, PLP, PEC, PDL);
    - **participation in nominal votes**;
    - **speeches**;
    - counts also given **per 365 days in office**;
  - a short neutral **summary** in which every sentence shows its sources.
- **Comparison** of 2 to 6 officials side by side, with the period and threshold shown above the table.
- **Parties**: members in the period, at its start and end, a label when membership changed, and the median (minimum–maximum) of each metric among members with enough time in office.
- **Methodology**: how every number is calculated, in Portuguese.

Metrics count only the days each person was actually in office. Data that is not published or not loaded shows **"Ainda não disponível"** or **"Não disponível nos dados oficiais"**, never a made-up zero.

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

## How it works

```
Official APIs (Câmara, Senado)
      │  fetch_current, fetch_activity: polite live requests (≤ 2 per second), run by hand
      ▼
Raw cache  data/raw/  (original responses, gzip JSON, git-ignored)
      │  normalize_current, normalize_activity: offline
      ▼
PostgreSQL  (officials, periods in office, leaves, parties, bills, sessions, votes, speeches)
      │  metrics and summaries, computed only over days in office
      ▼
Read-only API  /api/…  (Django Ninja; contract in docs/api/openapi.json)
      │
      ▼
React app  (Vite + TypeScript, pt-BR)
```

- The app serves a **snapshot**: pages never call the official APIs. Refreshing the data is a manual step.
- Every stored record keeps a `SourceRef` (API URL and public page) so the interface can link each number to its origin.
- Summaries are built from a fact sheet of structured facts, never from free text. A plain-Python validator checks every sentence (numbers, dates, names and banned wording) before it is shown. Template sentences are the default. Summaries written by a language model (Claude API) are optional: they need a key in `.env` and an explicit command, and they are never generated while a visitor waits.

## Quick start: try it with sample data (about 10 minutes)

This runs the full app on the small set of recorded official responses used by the tests (2 deputies and 3 senators). Nothing is downloaded from the official APIs.

**Requirements:**
- macOS, Linux or Windows with WSL2;
- [Docker](https://docs.docker.com/get-docker/);
- [uv](https://docs.astral.sh/uv/) (installs Python 3.14 if needed);
- Node.js 24 (`nvm use` reads `frontend/.nvmrc`);
- [gitleaks](https://github.com/gitleaks/gitleaks), only for committing.

1. **Configure.** Copy the example settings and fill them in. `.env` is git-ignored; never commit it.
   ```sh
   cp .env.example .env
   ```
   - `DJANGO_SECRET_KEY`: generate one with `uv run --directory backend python -c "import secrets; print(secrets.token_urlsafe(50))"`.
   - `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`: any values, for example `placar`, `placar` and a password of your choice. The local database is created with them.
   - Leave `ANTHROPIC_API_KEY` empty. The app works fully without it.
2. **Start the database** (PostgreSQL 18 in Docker, reachable only from your machine):
   ```sh
   docker compose up -d db
   ```
3. **Load the sample data** into a separate database whose name ends in `_e2e`. The loader refuses any other name, so your real data is never replaced.
   ```sh
   docker compose exec db createdb -U <your DATABASE_USER> placar_e2e
   cd backend
   uv sync
   DATABASE_NAME=placar_e2e uv run python manage.py load_fixture_snapshot
   ```
4. **Start the API** (keep it running):
   ```sh
   DATABASE_NAME=placar_e2e uv run python manage.py runserver 127.0.0.1:8000
   ```
5. **Start the app** in a second terminal, from the project folder:
   ```sh
   cd frontend
   npm ci
   npm run dev
   ```
   Open http://127.0.0.1:5173. The sample data has people and their time in office; their activity metrics show "Ainda não disponível", because activity is not part of the sample.

## Run with the real data

This downloads the current legislature from the official APIs, loads it, and runs the app on it. Do steps 1–2 of the quick start first.

1. **Create the tables:**
   ```sh
   cd backend
   uv sync
   uv run python manage.py migrate
   ```
2. **Download the data** into `data/raw/` with polite live requests. Both commands resume from the cache if interrupted, and only fetch what is missing.
   ```sh
   uv run python manage.py fetch_current --date 2026-11-01    # people and time in office, about 20 minutes
   uv run python manage.py fetch_activity --date 2026-11-01   # sessions, votes, bills, speeches, about 4 hours
   ```
   - Use today's date, or leave `--date` out to use today in Brazil.
   - `--limit N` fetches details for only the first N people, for a quick trial.
   - Failures, such as the Câmara's frequent timeouts, are listed at the end. Running the command again fetches only those.
3. **Load the snapshot** into the database, offline, using the same date:
   ```sh
   uv run python manage.py normalize_current --date 2026-11-01
   uv run python manage.py normalize_activity --date 2026-11-01
   ```
   **Always run them in this order.** Reloading people removes their activity, so run `normalize_activity` again after every `normalize_current`. Both commands report unknown values and missing items instead of guessing.
4. **Start the API and the app** as in steps 4–5 of the quick start, without `DATABASE_NAME=placar_e2e`.
   ```sh
   uv run python manage.py runserver 127.0.0.1:8000
   ```
   The first Câmara party view for a period takes about 10 seconds while the server computes it; later views are instant until the server restarts.

Optional: **model-written summaries.**
1. Put an Anthropic API key in `ANTHROPIC_API_KEY` in `.env`.
2. Run `uv run python manage.py generate_summaries`. It only lists the planned calls and their number.
3. Run it again with `--yes` to make the paid calls.

Each draft that fails the validator falls back to the template.

## Tests and checks

Everything runs offline: the tests use recorded official responses (`backend/tests/fixtures/`) and labeled synthetic data, and the network is blocked during backend tests. The database must be running. Run each line from the project folder.

```sh
cd backend && uv run pytest                 # backend tests, coverage of metrics/ must stay ≥ 90%
cd frontend && npm test                     # component and unit tests
cd frontend && npm run lint && npm run typecheck && npm run check:api
scripts/check.sh                            # everything above, plus migrations check, audits and secret scan
```

End-to-end tests run a real browser (Chromium) against the sample data (quick start step 3 creates the `placar_e2e` database), with accessibility checks (axe), and fail if any request leaves the machine. Run each line from the project folder:

```sh
cd frontend && npx playwright install chromium        # once
cd backend && DATABASE_NAME=placar_e2e uv run python manage.py load_fixture_snapshot
cd frontend && npm run e2e
```

GitHub Actions (`.github/workflows/ci.yml`) runs the same checks on every push and pull request, without any secrets.

## Project layout

```
backend/                 Django 6.1 + Django Ninja, Python 3.14 (uv)
  config/                settings (values come from .env)
  placar/core/           shared types: SourceRef, DateWindow, Period
  placar/sources/        official API clients, raw cache, normalizers, fetch and load commands
  placar/legislators/    officials, mandates, periods in office, leaves, party affiliations
  placar/activity/       bills, sessions, presences, votes, ballots, memberships, speeches
  placar/metrics/        coverage and metrics (pure functions)
  placar/summaries/      fact sheets, validator, template, optional model adapter
  placar/api/            read-only public API
  tests/                 pytest suite, recorded fixtures, synthetic builders
frontend/                React 19 + TypeScript + Vite
  src/pages/             officials, official, compare, parties, methodology
  src/text/pt-BR.ts      every user-facing text
  e2e/                   Playwright tests
docs/                    decisions, rules, plans, methodology, notes (see below)
scripts/                 check.sh, git hooks, fixture recording
data/raw/                downloaded official responses (git-ignored, created by the fetch commands)
```

## Documentation

| Where | What |
| --- | --- |
| [`docs/mvp-status.md`](docs/mvp-status.md) | What the MVP includes and what is left |
| [`docs/decisions/`](docs/decisions/README.md) | Every architecture and process decision, with alternatives |
| [`docs/architecture-rules.md`](docs/architecture-rules.md) | The binding rules that follow from the decisions |
| [`docs/methodology/`](docs/methodology/README.md) | How each metric and summary is calculated (pt-BR) |
| [`docs/data-issues.md`](docs/data-issues.md) | Gaps and inconsistencies found in the official data, and how they are handled |
| [`docs/data-inventory.md`](docs/data-inventory.md) | What data is held about officials, where, and what is never collected |
| [`docs/plans/`](docs/plans/) | Phase plans and their outcomes |
| [`docs/testing/`](docs/testing/), [`docs/security/`](docs/security/) | Test and security notes per phase |
| [`docs/backlog.md`](docs/backlog.md) | Work after the MVP |
| [`docs/definition-of-done.md`](docs/definition-of-done.md) | Checks before a merge or a phase is done |
| [`docs/api/openapi.json`](docs/api/openapi.json) | API contract between backend and frontend |

## Data sources

- Câmara dos Deputados Dados Abertos API (`dadosabertos.camara.leg.br`)
- Senado Federal Dados Abertos API (`legis.senado.leg.br/dadosabertos`)

Every endpoint used was checked against the official API documentation. The Senado does not publish plenary attendance per senator in the APIs used, so the app says so instead of estimating it.

## Data held

Only public records of elected officials in their public role, and nothing about visitors: no accounts, cookies, analytics or third-party requests. Details: [`docs/data-inventory.md`](docs/data-inventory.md).

## Status and roadmap

- **Done (MVP, phases A–D, signed off on 2026-11-01):** data access, data model and metrics, filters and comparison, summaries, on real data for legislature 57.
- **Next:** rankings with one table per metric (Phase E, plan approved); committee attendance; faster party views; a repeatable data refresh. See [`docs/backlog.md`](docs/backlog.md).
- **Not planned yet:** deployment. The app runs locally only.

## Contributing workflow

Decision 0016 defines the workflow:

- `main` always passes all checks. Work happens on short branches: `feat/<phase>-<topic>`, `fix/<topic>`, `docs/<topic>`, `chore/<topic>`.
- Turn on the pre-commit hook once: `git config core.hooksPath scripts/git-hooks`. It runs on every commit:
  - a secret scan (gitleaks);
  - the backend lint (ruff);
  - the frontend lint and type check, when frontend files change.
- Before merging into `main`, run `scripts/check.sh`, and merge with `git merge --no-ff`.
- Each finished phase is tagged on `main` (`phase-a`, `phase-b1`, …).

## License

MIT (see [`LICENSE`](LICENSE)). Personal project, owned solely by its author. Not developed under any employer, client, university or company resources.
