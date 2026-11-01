# Architecture rules — Placar Parlamentar

These rules are binding for every session and every agent. Each rule comes from an accepted decision in `docs/decisions/` or from the project's non-negotiable rules.
A rule changes only through a new decision that supersedes the old one and is approved by the project owner.

Stage 2 (architecture) was completed on 2026-11-01. This file summarizes decisions 0001–0016. When rules conflict, the decision record is the authority, and the conflict must be reported to the project owner.

## 1. Non-negotiable rules

1. Use only official open-data sources (Câmara dos Deputados and Senado Federal APIs). No social media, news scraping, personal accounts, or data about families or private lives.
2. Scope is limited to elected officials acting in their public role.
3. Every number and summary links to its official source record.
4. Neutral language only. No judgmental labels such as "best", "worst", "lazy" or "corrupt".
5. No user accounts, no tracking, no storage of personal data about visitors.
6. Never write API keys, tokens or secrets into code, docs or the conversation. Use environment variables and a git-ignored `.env`.
7. Personal project. Do not reference any employer, client or university resources.
8. If a requirement conflicts with these rules, stop and ask the project owner.

## 2. Process rules

- Every architecture or process decision is written to `docs/decisions/NNNN-<topic>.md` before it is used, with context, decision, alternatives and consequences, and listed in `docs/decisions/README.md`.
- Do not change an accepted decision silently. Propose a new decision that supersedes it.
- Work in stages and phases. Do not start a stage or phase before the project owner approves it.
- Flag incomplete or inconsistent official data in `docs/data-issues.md` instead of guessing.
- Verify every API endpoint against its current official documentation before using it, and cite the document and version in a code comment.

## 3. Approval gates (decision 0002)

Never do these without the project owner's explicit approval for that specific action:

- `git push`, adding or changing remotes, creating pull requests, issues, tags or releases.
- Rewriting or deleting git history (reset --hard, rebase, force, deleting branches).
- Publishing or deploying anything.
- Sending messages or posting to any external service.
- Deleting data (cache, database, fixtures) or files owned by another role.
- Adding a new dependency.

Small, descriptive local commits are allowed.

## 4. Team (decision 0001)

- The project owner is the project manager and the only approver.
- Agents: scrum master, architect, backend engineer, frontend engineer, data engineer, QA engineer, security engineer, technical writer. Definitions are in `.claude/agents/` (approved by the project owner on 2026-11-01). Changing an agent's rules, tools or owned files needs the owner's approval.
- The main session coordinates. Agents do not start other agents.
- Each agent changes only the files its definition says it owns. It reports changes needed elsewhere instead of making them.

## 5. Languages (decision 0003)

- User interface in Brazilian Portuguese (pt-BR).
- Code, comments, commits, decisions and internal docs in English.
- Official API field names and terms keep their original spelling.

## 6. Repository layout (decision 0004)

- One repository. Top-level folders: `backend/` (Python), `frontend/` (React), `docs/`, `scripts/`, `.claude/`.
- `backend/` and `frontend/` are self-contained: each has its own dependencies, tests and run commands, and neither imports code from the other.
- They connect only through the HTTP API contract.
- Local data (API cache, database files) is never committed to git.
- No monorepo build tool unless a new decision adds one.

## 7. Backend framework (decision 0005)

- Django 6.1 with Django Ninja for the HTTP API. Python 3.14, managed with `uv`.
- Backend layout: `backend/config/` (settings), `backend/placar/{core,sources,legislators,activity,metrics,summaries,api}/`, `backend/tests/` (`core` added by decision 0007).
- Views are sync by default. Async only when a view waits on something other than the database.
- Database writes are sync and run inside transactions.
- Fetching official data runs only as management commands, never inside a web request.
- `metrics/` is plain Python with no web code.
- Django admin: development settings only, read-only for official data, account created locally by the owner, password never stored in the repo. No accounts or logins on the public site.

## 8. Database and raw cache (decision 0006)

- PostgreSQL 18 with `psycopg` 3 for all normalized data. Locally it runs in Docker (`compose.yaml`, database service only), bound to `127.0.0.1`.
- Database credentials only in the git-ignored `.env`; `.env.example` lists names without values.
- Tests run against PostgreSQL too.
- Raw API responses are cached as gzip JSON files in `data/raw/<source>/<endpoint-path>/<sha256 key>.json.gz` (git-ignored), with an envelope: URL, parameters, fetch time (UTC), status, content type, API version if reported, unchanged body. No cookies or unneeded headers.
- Every normalized record stores its official source URL and the cache key of its raw response.
- Freshness per endpoint: data that no longer changes never expires; changing data refreshes after 24 hours by default; `--refresh` forces download; on API failure the cached copy is used and shown with its fetch date.
- Deleting or pruning the cache, or removing the database volume, needs the owner's approval.

## 9. Module boundaries (decision 0007)

- Style: modular monolith, layered, with services/selectors; `metrics` is a pure functional core with a thin selector shell. Not hexagonal.
- Allowed imports (nothing else):
  - `core` → nothing
  - `legislators` → core
  - `activity` → core, legislators
  - `sources` → core, legislators, activity
  - `metrics` → core, legislators, activity
  - `summaries` → core, legislators, activity, metrics
  - `api` → core, legislators, activity, metrics, summaries
- Nothing imports `api`. Only `sources` contacts the official APIs. No import cycles.
- Apps use other apps' `selectors.py` (reads) and `services.py` (writes), not their models' queries directly. Foreign keys are allowed.
- Official records are written only by `sources`, through services. `api` and the admin never write official data.
- Every value leaving `metrics` or `summaries` carries its `SourceRef`s.
- `metrics` never imports `django.http`, `ninja` or `sources`.
- An `ast`-based test in `backend/tests/` enforces these rules. A new dependency between apps needs a new decision.

## 10. Normalizing official data (decision 0008)

- Shared entities: `Legislature`, `Official` (one person in one house), `Party`, `Mandate`, `ServicePeriod`, `Leave`, `PartyAffiliation`. Each stores raw official codes and text next to normalized values, and a `SourceRef`.
- Coverage uses `ServicePeriod`s only. Leaves are stored separately and do not cut service periods.
- Senado: periods from `mandatos` → `Exercicios`; affiliations from `filiacoes`; leaves from `licencas`.
- Câmara: periods, affiliations and leaves are built from `historico` events (`Entrada` opens, `Saída` closes); affiliation dates have precision "known only at event".
- Dates are calendar days in `America/Sao_Paulo`, inclusive at both ends. Overlapping or touching periods of the same official are merged for counting; originals are kept.
- Never guess: unmapped values become `UNKNOWN` and are logged in `docs/data-issues.md`; disagreements between sources keep both values and are logged.
- No linking of the same person across houses, and no inferred party renames or mergers, without an official source.
- Personal fields allowlist: house id, parliamentary name, civil name, state, party, official photo URL, institutional page URL. Never CPF, birth date or place, social media, personal email or address.
- Source links show the official public page when one exists, otherwise the API URL.

## 11. Frontend (decision 0009)

- React 19 + TypeScript + Vite single-page app in `frontend/`. Node 24 LTS and npm, lockfile committed, Node version pinned.
- TypeScript: latest version supported by the chosen lint and test tools (7.x, else 6.x).
- React Router for pages; TanStack Query for server data.
- Filters live in the URL. No cookies, `localStorage` or other storage of visitor choices.
- API contract: `docs/api/openapi.json`, exported by the backend (a backend test fails if it is stale). Frontend types are generated from it with `openapi-typescript`; calls use `openapi-fetch`. A frontend check fails if types and contract differ.
- Dev: Vite proxies `/api` to Django on `127.0.0.1:8000`.
- pt-BR text lives in `frontend/src/text/pt-BR.ts` (technical writer). Numbers and dates are formatted with `Intl` `pt-BR`.
- CSS Modules and own components; no UI library in the MVP.
- No third-party requests at runtime: no analytics, trackers, external fonts or CDNs.
- Every number is rendered through the shared source-link component. External links use `rel="noopener noreferrer"`.
- Accessibility: semantic HTML, keyboard use, labels, contrast; tables as the base form of comparisons and leaderboards.

## 12. Summaries (decision 0010)

- All summary code is in `backend/placar/summaries/`. Only `summaries/llm/` may import the model provider's SDK (`anthropic`).
- Model set by `SUMMARY_MODEL` (default `claude-opus-5-5`); key only in `ANTHROPIC_API_KEY` in `.env`. Without a key, template summaries only.
- Only public official data goes to the model. Never visitor data or visitor-typed text.
- Input is a fact sheet of structured facts with ids and `SourceRef`s. No free text from the APIs in the MVP.
- Output is structured JSON: pt-BR sentences, each with the fact ids it relies on.
- A plain-Python validator rejects the whole draft unless: every sentence cites existing fact ids; every number, date and name appears in its cited facts; no banned wording (`summaries/wording/`); count and length limits hold.
- On rejection, refusal, error or timeout: one retry, then the template summary. Templates are the only summaries for custom windows.
- Model summaries are generated ahead of time by a management command for preset windows only, never during a visitor request. Each stores model id, prompt version, fact-sheet hash, creation time and validation result.
- Each sentence is shown with its source links; the page states the text is automatic and whether it is a model or template summary.
- Tests use a fake adapter, never the real API. No evaluation, training or benchmarking pipeline.

## 13. Testing (decision 0011)

- All test suites run offline. Backend: pytest + pytest-django on a PostgreSQL test database; `pytest-socket` allows only `127.0.0.1`; `respx` replays recorded responses; `hypothesis` for coverage and period-merging properties; coverage.py with a 90% floor for `metrics/` and the summary validator.
- Fixtures come only from `scripts/record_fixtures.py`, run by hand by the owner, copied from the raw cache to `backend/tests/fixtures/<source>/<endpoint>/<case>.json` with a `_fixture` note (date, spec version, what was trimmed).
- Personal fields are removed at recording time (0008 allowlist). Fixtures are never edited by hand; deleting them needs approval.
- Real cases get named fixture sets and test modules. Synthetic test data comes from `backend/tests/builders.py`, is labeled, and is never shown in the app.
- Required checks: every API number has a `SourceRef`; import boundaries; OpenAPI contract up to date; no personal fields in fixtures; every rendered number uses the source-link component; no banned wording in UI text or templates.
- Frontend: Vitest + Testing Library + MSW. End-to-end: Playwright (Chromium) with axe, offline against fixture-loaded backend, run before a phase is reported done.
- Commands: `uv run pytest`, `npm test`, `npm run e2e`. No CI until the deployment decision.
- `scripts/check_upstream.py` (run by hand) compares live response structure with fixtures; findings go to `docs/data-issues.md`.

## 14. Security baseline (decision 0012)

- Secrets only in `.env`; `.env.example` has names only. Django refuses to start outside development without `DJANGO_SECRET_KEY`. Secrets are never printed in logs, errors, tests or reports; a leaked secret is rotated and recorded.
- gitleaks scans staged changes in the pre-commit hook (`scripts/git-hooks/`) and the full history before any approved push.
- New dependencies: security review, then owner approval. Lockfiles committed. `pip-audit` and `npm audit` before each phase is reported done. No automatic update tools.
- Public API is read-only (`GET`/`HEAD`). All parameters validated by schemas (dates 1988-10-05 to today, start before end, threshold as share 0–1 or days 0–window, positive integer ids, 2–6 officials per comparison, bounded page size). Errors return 4xx without stack traces.
- Official APIs: ≤ 2 requests/s and one at a time per API, random jitter, no batch runs at exact round times; honor `Retry-After`, otherwise exponential backoff with a retry limit; project `User-Agent` without personal email; log `Deprecation`/`Sunset` headers as data issues.
- API text is untrusted: no `dangerouslySetInnerHTML`; URLs only if `https` on `camara.leg.br` or `senado.leg.br` (and subdomains); official photos downloaded at ingestion and served by our server.
- Logs never contain visitor IPs, user agents, cookies or full headers. The public site sets no cookies. No analytics or tracking.
- Outside development: `DEBUG = False`, `ALLOWED_HOSTS` set, security middleware on; CSP `default-src 'self'` without inline scripts, `nosniff`, `Referrer-Policy: no-referrer`, `frame-ancestors 'none'`.
- ruff with security rules (`S`) on the backend; strict TypeScript and a lint ban on `dangerouslySetInnerHTML` on the frontend.
- A security review note per phase in `docs/security/`.

## 15. Deployment (decision 0013)

- No deployment in the MVP. Everything runs on the owner's machine: PostgreSQL in Docker on `127.0.0.1`, Django on `127.0.0.1:8000`, Vite dev server proxying `/api`.
- No hosting accounts, domains or public URLs for the MVP. A private GitHub repository and GitHub Actions CI are allowed (decision 0016).
- "Done" means working locally with all tests passing, never "published".
- Settings come from environment variables; `asgi.py` and `wsgi.py` are kept.
- Publishing later needs a new decision that supersedes 0013 and the owner's explicit approval.

## 16. Metric methodology choices (decision 0014)

- Time in office: Senado follows `Exercicio` records (short leaves without an alternate count as time in office); Câmara follows `historico` events (a `Saída` for leave ends the period). Leave days are shown separately next to attendance metrics.
- Bills authored: Câmara `PL`, `PLP`, `PEC`, `PDL` and the matching Senado types (fixed in task B2.0); any listed author counts, co-authors included.
- No Senado attendance metric in the MVP; the app states it is not available in the official sources. Nominal-vote participation is a separate metric for both houses and is never labeled attendance.
- Câmara committee attendance is deferred until after the MVP; committee memberships are included.

## 17. MVP data snapshot (decision 0015)

- The MVP serves pages only from the official data already in the raw cache and database; it never calls the official APIs while serving pages.
- The interface shows the snapshot date; every number keeps its official source link.
- Features or data not built yet show "Ainda não disponível". No made-up or sample numbers are ever shown.
- Refreshing the snapshot is manual, run by or approved by the owner. Data sources left out of the MVP are listed in the README.

## 18. Git workflow and CI (decision 0016)

- `main` always passes all checks; no direct commits to it. Work on `feat/<phase>-<topic>`, `fix/…`, `docs/…`, `chore/…` branches.
- Merge with `git merge --no-ff` only after `scripts/check.sh` passes and the owner approves; delete the branch after merging.
- Annotated tag on `main` when the owner signs off a phase (`phase-a`, `phase-b1`, …).
- Commit messages: short imperative summary with the phase or area first, blank line, what and why.
- Pre-commit hook: gitleaks on staged changes, `ruff check`, `ruff format --check`. `scripts/check.sh` before merges: lint, full tests, `pip-audit`, gitleaks on the branch.
- One private GitHub repository. Pushes, remote changes and pull requests still need the owner's approval (decision 0002).
- GitHub Actions CI on every push and pull request: lint, offline tests with a PostgreSQL service, `pip-audit`, gitleaks over the full history. No secrets in CI; actions pinned to commit SHAs; read-only `contents` permission.
