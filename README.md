# Placar Parlamentar

A civic-transparency tool that summarizes the public activity of Brazilian federal legislators (deputados and senadores) and their parties, using only official open-data sources. Every summary links back to the official record so each claim can be checked.

## What it does

- Pulls public legislative records from the Câmara dos Deputados and Senado Federal open-data APIs.
- Shows, for each official: bills authored, votes cast, committee attendance, plenary attendance, and official speeches.
- Generates neutral, source-linked summaries of each official's public activity over a chosen time window.
- Lets users compare two or more officials, or parties, side by side on the same metrics and the same window.
- Applies date filters and minimum-coverage thresholds so comparisons are fair (for example, only officials who held the seat for at least a set share of the window).
- Publishes separate leaderboards per metric, with the full methodology shown next to each one.

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

Endpoints and field names should be verified against the current API documentation before implementation.

## Suggested stack

- Backend: Python (framework to be decided by the architect; FastAPI is the default candidate)
- Storage: PostgreSQL for normalized records, with a local cache of raw API responses (to be confirmed in an architecture decision)
- Frontend: React
- Team and agents: defined in the first stage of the prompt (project manager, scrum master, architect, backend, frontend, data, QA, security, technical writer)
- Architecture decisions: recorded in `docs/decisions/`; binding rules in `docs/architecture-rules.md`
- Summaries: an LLM-based summarization feature inside the app, given only the structured records and their source links as input
- Tests: pytest

## Getting started

1. Create the repository and copy this README and the project prompt into it.
2. Open a terminal in the project folder and start Claude Code.
3. Paste or reference the contents of `CLAUDE_CODE_PROMPT.md` to begin Stage 0 (team and roles). Later stages follow in order, with approval at each step.
4. Never paste API keys or secrets into the session. Store them in a `.env` file that is git-ignored.

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

## Workflow (contributing)

Decision 0016 defines the workflow:

- `main` always passes all checks. Work happens on short branches: `feat/<phase>-<topic>`, `fix/<topic>`, `docs/<topic>`, `chore/<topic>`.
- Every commit runs the pre-commit hook: secret scan (gitleaks) and backend lint (ruff).
- Before merging into `main`, run `scripts/check.sh`. It runs lint, the full test suite (Docker must be running), the dependency audit and a secret scan of the branch. Merge with `git merge --no-ff` after the owner approves.
- Each phase the owner signs off is tagged on `main` (`phase-a`, `phase-b1`, …).
- GitHub Actions (`.github/workflows/ci.yml`) runs the same checks on every push and pull request. It uses no secrets.

## Status

Phase A (data access) in progress. See `docs/plans/` and `docs/decisions/`.

## License

MIT. Personal project, owned solely by its author. Not developed under any employer, client, university or company resources.