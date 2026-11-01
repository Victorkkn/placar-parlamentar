# Mandato Aberto — Phase 1 (scaffold and data access)

## 2026-11-01 — Proposal

- **Date:** 2026-11-01
- **Agent:** Main Claude Code session
- **Task:** Propose the Phase 1 file structure and the exact API endpoints. No code until the user approves.

### Analysis
- Project folder was empty: no `README.md`, not a git repository.
- Downloaded the current official OpenAPI specs:
  - Câmara: `https://dadosabertos.camara.leg.br/api/v2/api-docs` (version note "0.4.347 - 10/26/2026"). Lists return 15 items by default, 100 max. No rate limit documented.
  - Senado: `https://legis.senado.leg.br/dadosabertos/v3/api-docs` (version 4.1.3.108). No auth. Documented limit: more than 10 req/s can get HTTP 429; 503 under load; avoid requests at round clock times. Many `/materia/*` and `/senador/{codigo}/autorias|votacoes|relatorias` services are deprecated.
- Live spot checks (3 requests):
  - Câmara `/legislaturas?data=2026-11-01` → legislature 57, 2023-02-01 to 2027-01-31.
  - Câmara `/deputados?idLegislatura=57&itens=2` → failed with "upstream request timeout" and `retry-after: 30`.
  - Senado `/senador/lista/legislatura/57` (JSON) → worked; the list includes alternates (suplentes), and senate terms span two legislatures.
- Local Python: 3.15.0; `uv` available.

### Changes made
- Created this history file only. No code written.

### Validation
- Spec downloads and the 3 live requests above were actually performed. Results are as stated.

### Decisions
- Use only non-deprecated Senado endpoints.
- Throttle both APIs to at most 2 req/s, with retries that honor `Retry-After`.

### Remaining work
- Waiting for user approval of the proposal.
- Open questions: missing README, git init, package name, handling of Senado alternates who never took office, SQLite for storage.

## 2026-11-01 — Prompt replaced; Stage 0 (team and roles)

- **Date:** 2026-11-01
- **Agent:** Main Claude Code session
- **Task:** New project prompt: staged process (Stage 0 team, Stage 1 agents, Stage 2 architecture decisions, Stage 3 phases A–E). Stack is Python + React. Project name is **Placar Parlamentar** (replaces "Mandato Aberto").

### Analysis
- The earlier Phase 1 proposal (above) is replaced by the new staged process. Its endpoint research is still valid input for Phase A.
- `README.md` still missing; folder still not a git repository.

### Changes made
- Renamed this history file from `2026-11-01-mandato-aberto-phase1.md` to `2026-11-01-placar-parlamentar-setup.md`.
- Created `docs/decisions/0001-team-and-roles.md` (status: proposed).
- Created `docs/decisions/README.md` (decision index).
- No application code written.

### Validation
- None needed beyond file creation; no code exists yet.

### Decisions
- Team proposal recorded as decision 0001, status "proposed", awaiting approval.

### Remaining work
- Project owner approval of decision 0001 (team, and who covers each role).
- Open: README, git init, UI language.
- Then Stage 1: agent definitions in `.claude/agents/`.

## 2026-11-01 — Stage 0 approved; Stage 1 agents drafted

- **Date:** 2026-11-01
- **Agent:** Main Claude Code session
- **Task:** Owner approved the team, confirmed pt-BR UI with English code/docs, approved `git init`, and asked for a rule that no one may `git push` without asking. Proceed to Stage 1.

### Analysis
- Owner added `README.md`. Its title still says "Mandato Aberto" and it refers to a `CLAUDE_CODE_PROMPT.md` that does not exist. Not edited (owner's file); flagged.
- README suggests PostgreSQL for storage; to be settled in the Stage 2 database decision.

### Changes made
- `docs/decisions/0001-team-and-roles.md`: status set to accepted.
- New accepted decisions: `0002-git-and-approval-gates.md` (no push or other external/irreversible action without approval), `0003-languages.md`.
- `docs/decisions/README.md`: index updated.
- `docs/architecture-rules.md`: created with non-negotiable rules, process rules, approval gates, team and language rules.
- Root `CLAUDE.md`: created, points to the rules.
- `.claude/settings.json`: "ask" permission rules for git push, remote, reset --hard, rebase, branch -D, tag, gh, rm -r/-rf.
- `.gitignore`: created (.env, data/, Python and Node artifacts).
- `.claude/agents/`: 8 agent definitions (scrum-master, architect, backend-engineer, frontend-engineer, data-engineer, qa-engineer, security-engineer, technical-writer). Status: awaiting approval.
- `git init` and one local commit. Nothing pushed; no remote configured.

### Validation
- Checked that git user name and email are configured. Commit result is shown in the session.

### Decisions
- The project-manager role has no agent (owner covers it).
- Agent-owned folders under `backend/` and `frontend/` are provisional until the repository layout decision.

### Remaining work
- Owner approval of the Stage 1 agent definitions.
- README title and missing `CLAUDE_CODE_PROMPT.md` (owner's call).
- Then Stage 2, decision by decision, led by the architect.

## 2026-11-01 — Stage 1 approved; Stage 2 started

- **Date:** 2026-11-01
- **Agent:** Main Claude Code session (acting as architect; new agents load in a fresh session)
- **Task:** Owner approved the 8 agents, asked to rename the README title, and to save the project prompt as a reference `.md`.

### Changes made
- `README.md`: title changed from "Mandato Aberto" to "Placar Parlamentar" (only occurrence).
- `CLAUDE_CODE_PROMPT.md`: reference copy of the prompt, with the project name updated and a note that accepted decisions take precedence.
- `docs/architecture-rules.md`: records agent approval; changing an agent needs owner approval.
- Root `CLAUDE.md`: points to `CLAUDE_CODE_PROMPT.md`.
- Commit `86361e7` (local only).
- `docs/decisions/0004-repository-layout.md`: proposed (monorepo with `backend/` and `frontend/`); index updated.

### Validation
- Checked that "Mandato Aberto" no longer appears in `README.md`.

### Decisions
- Decision 0004 is proposed only; not used until accepted.

### Remaining work
- Owner approval of decision 0004, then decisions on topics 2–10 one at a time.

## 2026-11-01 — Decision 0004 accepted; topic 2 deferred

- **Date:** 2026-11-01
- **Agent:** Main Claude Code session
- **Task:** Owner approved decision 0004 and said the backend architecture (Stage 2 topic 2) will be decided later.

### Changes made
- `docs/decisions/0004-repository-layout.md`: status accepted.
- `docs/decisions/README.md`: index updated; added a Stage 2 topic tracker with topic 2 marked deferred.
- `docs/architecture-rules.md`: added section 6 (repository layout rules).
- No folders or code created.

### Validation
- None needed; documentation only.

### Remaining work
- Owner to choose which Stage 2 topic comes next. Topic 2 stays open; Stage 3 cannot start until all Stage 2 topics are accepted.

## 2026-11-01 — Topic 2 resumed: decision 0005 proposed

- **Date:** 2026-11-01
- **Agent:** Main Claude Code session (acting as architect)
- **Task:** Owner asked whether Django can be used and run async, and for layout options. Owner chose option A (Django + Django Ninja, one app per area) and wants the Django admin.

### Analysis
- Checked PyPI: Django 6.1.2 (Python 3.12–3.14 listed), Django Ninja 1.7.3, DRF 3.18.3, adrf 0.1.14, FastAPI 0.162.0.
- Checked Django 6.1 docs: async views and async query methods exist; transactions do not work in async mode; built-in Tasks backends are dev/test only, no worker provided.
- Python 3.15 is not listed by Django 6.1; Python 3.14 is installed locally.

### Changes made
- `docs/decisions/0005-backend-framework.md` (proposed); index and topic tracker updated.

### Validation
- Version and doc checks above were actually performed.

### Decisions
- Proposed: sync by default, async only where it helps; fetching via management commands; admin local-only and read-only for official data; Python 3.14.

### Remaining work
- Owner approval of 0005.

## 2026-11-01 — Decision 0005 accepted

- **Agent:** Main Claude Code session
- **Changes made:** 0005 status accepted; index and topic tracker updated; `docs/architecture-rules.md` section 7 added.
- **Remaining work:** topic 3 (database and raw cache) next.

## 2026-11-01 — Decision 0006 proposed (database and raw cache)

- **Agent:** Main Claude Code session (acting as architect)
- **Analysis:** PostgreSQL not installed locally; Docker installed. endoflife.date reports PostgreSQL 18.6 as latest; PyPI reports psycopg 3.3.6.
- **Changes made:** `docs/decisions/0006-database-and-raw-cache.md` (proposed); index updated.
- **Remaining work:** owner approval of 0006.

## 2026-11-01 — Decision 0006 accepted

- **Agent:** Main Claude Code session
- **Changes made:** 0006 status accepted; index and topic tracker updated; `docs/architecture-rules.md` section 8 added.
- **Decisions:** Owner's "i approve all" read as approval of every point in 0006 (not of future, unwritten decisions).

## 2026-11-01 — Decision 0007 proposed (module boundaries)

- **Agent:** Main Claude Code session (acting as architect)
- **Changes made:** `docs/decisions/0007-module-boundaries.md` (proposed); index updated.
- **Decisions:** Proposes adding a `core` app to the 0005 layout; flagged to the owner as an addition to an accepted decision.
- **Remaining work:** owner approval of 0007.

## 2026-11-01 — Decision 0007 accepted

- **Agent:** Main Claude Code session
- **Task:** Owner asked whether the module structure has a name; explained it is a layered modular monolith with services/selectors and a functional core in metrics, not hexagonal. Owner approved adding an "Architecture style" section and accepted 0007.
- **Changes made:** 0007 gained "Architecture style" and a hexagonal alternative entry, plus markdown lint fixes; status accepted. Index updated. Rules: section 7 layout now includes `core`; section 9 added.

## 2026-11-01 — Decision 0008 proposed (normalization); data-issues log started

- **Agent:** Main Claude Code session (acting as architect)
- **Analysis:** Read Câmara `/deputados/{id}/historico` schema; fetched live samples: Senado mandatos/licencas/filiacoes for senators 5918, 4545, 5917; Senado legislature-57 list with and without `exercicio=S`; Câmara deputies list page 1 and historico for 220593. Findings recorded in 0008 context and `docs/data-issues.md` (7 entries). Samples kept in the session scratchpad only, not in the repo.
- **Changes made:** `docs/decisions/0008-source-normalization.md` (proposed); `docs/data-issues.md` created; index updated.
- **Remaining work:** owner approval of 0008; open methodology question on leave days without an alternate (Phase B).

## 2026-11-01 — Decision 0008 accepted

- **Agent:** Main Claude Code session
- **Changes made:** 0008 accepted; index updated; rules section 10 added.
- **Decisions:** Owner answered "yes" to the 0008 approval and to the suggestion that short leave days without a substitute count as time in office, with leave days shown separately. To be written into the Phase B methodology plan for final confirmation.

## 2026-11-01 — Decision 0009 proposed (frontend)

- **Agent:** Main Claude Code session (acting as architect)
- **Analysis:** Local Node 24.12 / npm 11.6; checked latest npm versions of react, vite, typescript, react-router, TanStack Query, openapi-typescript, openapi-fetch; Node release lines from endoflife.date.
- **Changes made:** `docs/decisions/0009-frontend.md` (proposed); index updated.
- **Remaining work:** owner approval of 0009.

## 2026-11-01 — Decision 0009 accepted

- **Agent:** Main Claude Code session
- **Changes made:** 0009 accepted; index updated; rules section 11 added.

## 2026-11-01 — Decision 0010 proposed (summaries)

- **Agent:** Main Claude Code session (acting as architect)
- **Analysis:** Loaded the Claude API reference skill for current model ids, prices and structured outputs; no API calls made, no code written.
- **Changes made:** `docs/decisions/0010-summaries.md` (proposed); index updated.
- **Decisions:** Proposed default model `claude-opus-5-5`, configurable; model choice for cost is the owner's call.
- **Remaining work:** owner approval of 0010.

## 2026-11-01 — Decision 0010 accepted

- **Agent:** Main Claude Code session
- **Changes made:** 0010 accepted (default model unchanged: `claude-opus-5-5`); index updated; rules section 12 added.

## 2026-11-01 — Decision 0011 proposed (testing)

- **Agent:** Main Claude Code session (acting as architect)
- **Analysis:** Checked current PyPI and npm versions of test tools.
- **Changes made:** `docs/decisions/0011-testing.md` (proposed); index updated.
- **Remaining work:** owner approval of 0011.

## 2026-11-01 — Decision 0011 accepted

- **Agent:** Main Claude Code session
- **Changes made:** 0011 accepted; index updated; rules section 13 added.

## 2026-11-01 — Decision 0012 proposed (security baseline)

- **Agent:** Main Claude Code session (acting as architect)
- **Analysis:** Checked ruff, pip-audit, detect-secrets, bandit (PyPI) and gitleaks (GitHub releases) versions; gitleaks not installed locally, ruff is.
- **Changes made:** `docs/decisions/0012-security-baseline.md` (proposed); index updated.
- **Decisions:** Proposes serving official photos from our server to keep 0009's "no third-party requests" rule.
- **Remaining work:** owner approval of 0012; gitleaks install needs approval.

## 2026-11-01 — Decision 0012 accepted; gitleaks hook; 0013 proposed

- **Agent:** Main Claude Code session
- **Task:** Owner approved 0012 and the gitleaks install.
- **Changes made:**
  - 0012 accepted; rules section 14 added (commit beb7513).
  - Installed gitleaks 8.30.1 with Homebrew (owner approved).
  - Added `scripts/git-hooks/pre-commit` (runs `gitleaks git --pre-commit --staged --redact`) and set local `git config core.hooksPath scripts/git-hooks`.
  - `docs/decisions/0013-deployment.md` (proposed): no deployment in the MVP, local only; index updated.
- **Validation:**
  - Full-history gitleaks scan: 20 commits scanned, no leaks found.
  - Hook test in a throwaway scratchpad repo: a fake `ghp_` token was detected and the commit was blocked (exit 1). The project repo was not used for this test.
- **Remaining work:** owner approval of 0013. `core.hooksPath` is a local git setting; a fresh clone must run `git config core.hooksPath scripts/git-hooks`. To document in the README setup section later.

## 2026-11-01 — Decision 0013 accepted; Stage 2 complete

- **Agent:** Main Claude Code session
- **Changes made:** 0013 accepted; index marks Stage 2 complete; rules file intro updated and section 15 added; root `CLAUDE.md` rewritten with a rules summary, plan-approval rule and hook setup note.
- **Remaining work:** Stage 3, starting with the Phase A plan.

## 2026-11-01 — Stage 3: Phase A plan proposed

- **Agent:** Main Claude Code session
- **Changes made:** `docs/plans/phase-a-data-access.md` (proposed): scope, endpoints with spec versions, tasks A0–A13 with owners, acceptance criteria, dependency list, risks, open questions.
- **Validation:** Endpoint list is based on the spec downloads and live samples taken earlier today; httpx 0.28.1 and psycopg 3.3.6 checked on PyPI; uv 0.9.26 installed locally.
- **Implementation authorized:** no. No code written.
- **Remaining work:** owner approval of the Phase A plan, dependency list, live-run choice, and the decision to skip deputy details.

## 2026-11-01 — Phase A implementation (A0–A12)

- **Agent:** Main Claude Code session (acting as backend, data, QA, security and writer roles)
- **Task:** Owner approved the Phase A plan and dependency list ("approve"). Deputy details skipped as planned; live run to be confirmed with the owner.
- **Implementation authorized:** yes (Phase A only).
- **Analysis during implementation:**
  - Câmara deputies list has one row per deputy and party (data issue 8).
  - Senado `lista/atual` gives `http://` photo/page links; `https` versions checked and working (data issue 9).
  - Senado legislature list: 83 titular mandates among 245 people (data issue 4 updated).
  - Senado `plenario/legislatura/{AAAAMMDD}` and `lista/atual` shapes sampled live (2 requests) before writing parsers.
- **Changes made (commits 6b25415 … 811fd52):**
  - `backend/`: uv project (Python 3.14, Django 6.1, httpx, psycopg; dev tools), settings from env, `core/types.py`, `sources/http.py`, `sources/cache.py`, `sources/clients/{camara,senado,_parse}.py`, `sources/runner.py`, `sources/fixtures.py`, `sources/drift.py`, commands `fetch_camara`, `fetch_senado`, `fetch_current`, `record_fixtures`, `check_upstream`; tests.
  - Repo root: `compose.yaml`, `.env.example`, `scripts/record_fixtures.py`, `scripts/check_upstream.py`, `scripts/fixture_cases.json` (17 cases).
  - Docs: README setup section and status; `docs/data-issues.md` (4 updated, 8, 9 added); `docs/testing/phase-a.md`; `docs/security/phase-a.md`.
- **Validation (actually run):**
  - `uv run pytest`: 94 passed, 9 skipped (skips need recorded fixtures).
  - Coverage of `placar/`: 93%.
  - `uv run ruff check`: clean. `uv run pip-audit`: no known vulnerabilities. `gitleaks dir` on backend: no leaks; pre-commit hook passed on every commit.
  - Parsers checked by hand against live samples saved in the session scratchpad (not committed): Senado mandate 526 sequence and Câmara 220593 events parsed as expected.
  - Not yet done: live `fetch_current` run (A13), fixture recording (A8), real-case tests.
- **Decisions:** `ruff format` rewrote `except (A, B)` to the Python 3.14 unparenthesized form (PEP 758), valid for the pinned Python 3.14. Fixture recorder is a management command with a thin wrapper in `scripts/` so it reuses the cache key logic.
- **Remaining work:** owner runs (or approves the session running) `fetch_current` and `record_fixtures`; then run the full suite with real-case tests and close Phase A.

## 2026-11-01 — Phase A live steps and results

- **Agent:** Main Claude Code session
- **Task:** Owner answered "yes" to: creating `.env`, recording fixtures and running the live fetch in the session.
- **Changes made:**
  - `.env` created with generated `DJANGO_SECRET_KEY` and database password written directly to the file (mode 600, git-ignored, never displayed).
  - Live `fetch_current` run twice; fixtures recorded with `--fetch` (3 downloads for senator 5918).
  - `runner.py`: each failure now reported once.
  - Docs: data issue 1 updated; testing and security notes; plan outcome section.
- **Validation (actually run):**
  - 1st run: 677 Câmara requests (657 downloads, 19 retries after HTTP 504, 1 final failure for deputy 74299) and 382 Senado requests; 21 minutes.
  - 2nd run: 1 Câmara request (74299, succeeded), 0 Senado requests; under 1 second.
  - Raw cache: 1,043 files, 4.1 MB.
  - `uv run pytest`: 119 passed, 0 skipped; coverage 94%; ruff clean; grep found no `@` or `"cpf"` in fixtures; gitleaks hook passed.
- **Hook finding:** the gitleaks pre-commit hook blocked the first two commit attempts (17 `generic-api-key` matches on the fixture field `cache_key`, a SHA-256 of a public URL). Renamed to `cache_file_id`, re-recorded fixtures from cache (no network), tests still 119 passed, rescan clean. Scanner rules unchanged.
- **Remaining work:** owner sign-off on Phase A; then the Phase B plan (data model and metrics), including the leave-days methodology confirmation and the cause of data issue 4.

## 2026-11-01 — Phase A signed off; Phase B plan proposed

- **Agent:** Main Claude Code session
- **Task:** Owner signed off Phase A ("ok"); write the Phase B plan.
- **Analysis:**
  - Read activity endpoints in the downloaded specs (Câmara proposições, votações, eventos, órgãos, discursos; Senado processo, votacao, comissoes, discursos).
  - 4 live sample requests (Senado plenary agenda and committee agenda for 2026-10-28, session 593614, meeting 14998): no per-senator presence list (data issue 10).
  - From the cache only: 64 distinct Câmara history texts; 311 start-of-legislature events tagged legislature 58 (data issue 11).
- **Changes made:** `docs/plans/phase-b-data-model-and-metrics.md` (proposed); Phase A plan marked signed off; data issues 10 and 11.
- **Implementation authorized:** no (Phase B plan awaiting approval).
- **Remaining work:** owner approval of the Phase B plan and answers to Choices 1–4 (to become decision 0014).

## 2026-11-01 — Phase B approved; decision 0014; B1 implemented

- **Agent:** Main Claude Code session
- **Task:** Owner approved the Phase B plan and the recommendations on Choices 1–4 ("approve").
- **Implementation authorized:** yes (Phase B; B2 after B1 passes).
- **Changes made:**
  - Decision 0014 (methodology choices) accepted; rules section 16; plan status updated.
  - Started PostgreSQL 18.6 in Docker (127.0.0.1 only); added `hypothesis`.
  - `legislators` app (models, 3 migrations, services, selectors); `sources/normalize/` (Câmara status map, Câmara and Senado normalizers); `normalize_current` command; cache-only fetcher mode; `metrics/coverage.py` and selector; tests.
  - Docs: data issues 4 (explained), 12–15; B1 outcome in the plan; `docs/testing/phase-b1.md`; `docs/security/phase-b1.md`.
- **Analysis:**
  - Câmara repeated exits while out are leave/absence renewals (26), not errors.
  - Mesa decisions (recount, re-total, restoration) appear only as DIVERSO notes; 4 texts added to the status map after checking every occurrence (data issue 14) — flagged for owner review.
  - Câmara exit date treated as last day in office (data issue 12).
  - Senado incomplete mandates 5718, 6358 (data issue 13); one period end without reason (data issue 15).
- **Validation (actually run):** `normalize_current` on the full cache twice (Câmara 0 unknown, 0 inconsistencies; Senado 1 unknown, 2 incomplete mandates); `uv run pytest` 196 passed; coverage 94%; ruff clean; pip-audit clean; gitleaks hook passed.
- **Remaining work:** owner review of B1 (especially the four Mesa-decision mappings); then B2.0 checks and B2.

## 2026-11-01 — B1 approved; B2.0 checks; B2.1 clients and fetch command

- **Agent:** Main Claude Code session
- **Task:** Owner approved B1 including the four Mesa-decision mappings; start B2.
- **Analysis (B2.0, about 25 small live requests):** plenary id 180; deliberative sessions type 110; `/votacoes` per calendar year; undocumented 3-month limit on `/proposicoes` dates (data issue 16, solved with `ano` list); Senado bill types PL/PLP/PEC/PDL; Senado vote code table at `tiposComparecimento`; committee lists mix other bodies; `.gov.br` document links (data issue 17).
- **Changes made:** plan B2.0 section with adjustments for review (vote participation rules; committee count waits for official body types); `clients/camara_activity.py`, `clients/senado_activity.py`, `activity_runner.py`, `fetch_activity` command; tests.
- **Validation:** parsers checked against live samples (scratchpad, not committed); `uv run pytest` 203 passed; ruff clean; gitleaks hook passed.
- **Remaining work:** owner go-ahead for the live `fetch_activity` run (≈ 8,000 requests); activity models, normalizers and metrics; record activity fixtures; B2 notes.

## 2026-11-01 — Decisions 0015 and 0016; git workflow, CI and private GitHub repository

- **Agent:** Main Claude Code session
- **Task:**
  - Owner said the MVP may use partial data and asked for git workflows.
  - After a question, the owner chose: real data snapshot; a branching process, local pre-commit checks and GitHub Actions CI.
  - The owner approved 0015 and 0016 ("all approve") and asked for a private repository to be created.
- **Changes made:**
  - Decision 0015 (MVP on a snapshot of official data, no mocked numbers) and 0016 (workflow and CI; supersedes part of 0013) accepted; rules sections 17–18; 0013 status note.
  - Branch `chore/git-workflow`:
    - `.github/workflows/ci.yml`: actions pinned to SHAs; gitleaks 8.30.1 binary checksum-verified;
    - `scripts/check.sh`;
    - pre-commit hook now also runs ruff;
    - README workflow section.
    - Merged into `main` with `--no-ff`; branch deleted.
  - Annotated tags: `phase-a` (697fcc5) and `phase-b1` (b63c5a2).
  - Created the private GitHub repository `Victorkkn/placar-parlamentar` (via `gh`); added remote `origin` (SSH); pushed `main` and both tags.
- **Validation (actually run):**
  - `scripts/check.sh`: lint ok, 203 tests passed, no known vulnerabilities, no leaks.
  - Full-history gitleaks scan before the push: no leaks.
  - No tracked `.env`, keys or `data/raw`.
  - Repository visibility checked: PRIVATE.
  - CI run 41329428087: `backend` and `secrets` succeeded.
- **Failed attempt:** branch protection on `main` refused (HTTP 403: needs GitHub Pro or a public repository). Recorded in 0016.
- **Remaining work:** owner to decide whether later pushes after each approved merge are pre-approved; B2 continues on `feat/b2-activity` once the live download finishes.

## 2026-11-01 — Standing push approval

- **Agent:** Main Claude Code session
- **Task:** Owner approved pushing to GitHub after each approved merge without asking separately ("yes, you can").
- **Changes made:** recorded in 0016 notes, rules section 18 and root `CLAUDE.md` (scope: `main` and phase tags only, right after an approved merge); then pushed `main`.

## 2026-11-01 — Phase C plan approved; decision 0017

- **Agent:** Main Claude Code session
- **Task:** Owner asked to start the frontend in parallel with B2. A Phase C plan and decision 0017 were written first, as the process requires. The owner approved both ("ok") and asked whether the app will be React (yes: React, built with Vite, written in TypeScript).
- **Analysis:** npm peer ranges checked: `typescript-eslint` 8.72.1 needs TS < 6.1; `openapi-typescript` 7.13.0 declares TS ^5.x → TypeScript 5.9.3.
- **Changes made:**
  - `docs/plans/phase-c-filters-and-comparison.md` (approved);
  - decision 0017 accepted;
  - rules section 11 updated.
- **Remaining work:** C0 frontend setup (branch `feat/c0-frontend-setup`); B2 download still running.

## 2026-11-01 — Phase C0: frontend setup (branch feat/c0-frontend-setup)

- **Agent:** Main Claude Code session (frontend and security roles)
- **Changes made:**
  - `frontend/`: React 19 + Vite 8 + TypeScript 5.9.3 placeholder app (pt-BR) with routes, pt-BR text file, Vitest + Testing Library setup, and ESLint 10 config.
  - Lint bans `dangerouslySetInnerHTML` and visitor storage, with tests that prove both bans.
  - Exact pins: `.npmrc` sets `save-exact` and `strict-peer-deps`; `package-lock.json` committed.
  - CI `frontend` job; `scripts/check.sh` and the pre-commit hook extended to the frontend; README frontend section; `docs/security/phase-c0.md`.
- **Deviations from the approved list (flagged to the owner):**
  - `eslint-plugin-react` dropped: it supports only ESLint ≤ 9, which is end-of-life. The ban is done with a built-in ESLint rule instead.
  - Added required companions: `@testing-library/dom` 10.4.2 (peer of Testing Library), `@types/react` 19.3.0 and `@types/react-dom` 19.3.0 (types for TypeScript).
- **Problems met:**
  - `npm install` failed with EACCES on root-owned files in `~/.npm`; a session-local cache was used and the owner's files were not changed.
  - Local Node 24.12 is below one test dependency's declared minimum (24.15); tests pass anyway.
- **Validation (actually run):** `npm run lint`, `npm run typecheck`, `npm test` (4 passed), `npm run build`, `npm audit --omit=dev` (0 vulnerabilities), full `npm audit` (one dev-only advisory, documented), workflow YAML parsed, `scripts/check.sh` all passed.
- **Remaining work:** owner approval to merge C0; C1 (API) next; B2 download still running.

## 2026-11-01 — B2.2: activity models, normalizers and metrics (branch feat/b2-activity)

- **Agent:** Main Claude Code session (backend, data and technical writer roles)
- **Task:** Phase B2 as approved: store activity and compute the first metrics.
- **Analysis:** `/proposicoes` and `/votacoes` reject date ranges over 3 months, which the spec does not say (data issue 16). The first live `fetch_activity` run stopped on it.
- **Changes made:**
  - Câmara votes are fetched by quarter and bills by `ano`. A failed list request is now reported instead of stopping the run.
  - `activity` app with models Bill, Session, Presence, Voting, Ballot, Membership and Speech.
  - `normalize/activity.py` classifies vote options. `normalize_activity` command added.
  - Metrics in `metrics/activity.py`: plenary attendance (Câmara), bills authored, nominal-vote participation and speeches, counted only on days in office, plus leave days.
  - pt-BR methodology drafts in `docs/methodology/`.
- **Validation:** backend tests passed on the branch (fixtures and synthetic activity, offline).
- **Remaining work:** live download still running; the B2 outcome is to be written after `normalize_activity` runs on real data.

## 2026-11-01 — C1: read-only API (branch feat/c1-api)

- **Agent:** Main Claude Code session (backend role)
- **Changes made:**
  - Django Ninja API under `/api/`: `meta`, `officials`, `officials/{id}`, `compare`, `parties`. GET only, inputs validated, rate per 365 days in office for count metrics, `not_loaded_yet` instead of zeros.
  - `export_openapi` writes `docs/api/openapi.json`; a test fails when the file is stale.
- **Problems met:**
  - The boundary test caught `sources` importing `api`; the command was moved to the `api` app.
  - The generic "every number has a source" test caught detail values without sources; leave sources are now joined into attendance.
- **Validation:** backend tests passed, including the generic source check.

## 2026-11-01 — C2–C3: typed client and pages (branch feat/c3-pages)

- **Agent:** Main Claude Code session (frontend role)
- **Changes made:**
  - Types generated from the contract (`npm run check:api`) and calls through `openapi-fetch`.
  - Pages: officials list with filters in the URL, official page, comparison, parties, methodology, not found. A `SourceValue` component is used for every number.
- **Problems met:** MSW 3 renamed `onUnhandledRequest`, and `openapi-fetch` captured `fetch` at load time; fetch is now looked up at call time.
- **Validation:** lint, type check, component tests and build passed.

## 2026-11-01 — CI and tests; C5 end-to-end (branch chore/ci-and-tests)

- **Agent:** Main Claude Code session (QA and security roles)
- **Task:** Owner asked what could run in parallel: improve tests and CI.
- **Changes made:**
  - CI and `scripts/check.sh`: migrations check, `metrics/` coverage floor of 90%, contract check, uv cache. A pipe through `tail` that hid coverage failures in `check.sh` was removed.
  - Hypothesis property tests for the metrics; a test that bulk and single-official metrics are equal; frontend helper tests.
  - C5: `load_fixture_snapshot` (refuses databases not ending in `_e2e`); Playwright tests with axe and a check that no request leaves `127.0.0.1`; CI `e2e` job on `main` and pull requests.
- **Validation (actually run):** 279 backend tests, 18 frontend tests and 4 end-to-end tests passed; `metrics/` coverage 98% (was 89% before the new test); `scripts/check.sh` passed. The CI `e2e` job has not run on GitHub yet.

## 2026-11-01 — Documentation review and MVP status (branch docs/mvp-readiness)

- **Agent:** Main Claude Code session (technical writer, QA, security and project manager roles)
- **Task:** Owner asked to check that everything is documented, list what the MVP still needs, and apply it to the project.
- **Analysis:**
  - This history stopped at C0.
  - The README still said "FastAPI is the default candidate" and "Phase A in progress", and its "Getting started" described the project bootstrap.
  - There were no test or security notes for Phase C and no single MVP checklist.
  - The Phase D and E plans had not been written.
- **Changes made:**
  - `docs/mvp-status.md`: done, left and left-out items.
  - `docs/testing/phase-c.md` and `docs/security/phase-c.md` (C6 notes).
  - README: stack as decided, how to run the app on the real snapshot, status, and pre-commit scope. The bootstrap "Getting started" section was replaced. The owner's "What it does", principles and license are kept.
  - Draft plans `docs/plans/phase-d-summaries.md` and `docs/plans/phase-e-rankings.md`, both **proposed** with choices for the owner. Nothing in them is implemented.
  - This history entry and the four above.
- **Validation:**
  - `uv run pip-audit`: no known vulnerabilities.
  - `npm audit --omit=dev`: 0 vulnerabilities.
  - Full `npm audit`: the same single dev-only `minimatch` advisory as in C0.
  - Command flags in the README checked against the code.
  - No session or cookie middleware (checked in settings).
- **Decisions:** none new. Plan D proposes a decision 0018 (one banned-wording file) for approval.
- **Remaining work:**
  - The B2 data load.
  - Owner approval of the merges, the C4 wording review, and the D and E plans.

## 2026-11-01 — Phase D and E plans approved; decision 0018; Phase D built (branch feat/d-summaries)

- **Agent:** Main Claude Code session (backend, frontend, QA, security and technical writer roles)
- **Task:** Owner replied "approved" to the Phase D and E plans with the recommended choices.
  - Read as approval of both plans and of decision 0018.
  - **Not** read as approval to merge branches; that is still to be asked.
- **Changes made:**
  - Decision 0018: one banned-wording file. Index, 0010 status and rules section 12 updated; plan statuses recorded.
  - `backend/placar/summaries/`:
    - pt-BR formatter;
    - fact sheet;
    - wording loader;
    - validator;
    - template;
    - `Summary` model and migration;
    - `llm/` adapter (Claude API, structured outputs, effort low);
    - selectors (read path re-validates stored summaries);
    - services (one retry, then template);
    - `generate_summaries` command (needs a key and `--yes`).
  - Settings: `BANNED_WORDING_FILE` and `SUMMARY_MODEL`; app registered.
  - Dependency: `anthropic==2.3.0`.
  - API: `summary` on `/officials/{id}`; contract regenerated.
  - Frontend:
    - `SummarySection` with the kind label and a methodology link;
    - "Resumos" section on the methodology page;
    - per-365-days text added to the methodology (for C4 review);
    - test data, unit test and e2e check.
  - Docs:
    - `docs/methodology/resumos.md`;
    - `docs/testing/phase-d.md` and `docs/security/phase-d.md`;
    - plan outcome;
    - MVP status;
    - README.
- **Problems met:** reading the real template output showed that allowing "PL" anywhere would let a model name a wrong party "PL". Bill types are now allowed only with the bills fact, and a test covers it.
- **Validation (actually run):**
  - backend: 332 tests passed;
  - frontend: lint, type check, 18 tests, contract check and build passed;
  - e2e: 4 passed (after migrating `placar_e2e`);
  - `scripts/check.sh`: all passed;
  - `pip-audit`: clean.
  - No real model call was made.
- **Decisions:** 0018 accepted. Two deviations from the plan are flagged for the owner: the 1–6 sentence count, and bill types tied to the bills fact.
- **Remaining work:**
  - owner review of the deviations and of the summary wording;
  - Phase E next;
  - B2 data load still running;
  - merges still need approval.

## 2026-11-01 — Documentation and data review against an external program's eligibility terms (branch docs/data-and-backlog)

- **Agent:** Main Claude Code session (technical writer, security and project manager roles)
- **Task:** Owner asked to check that nothing is missing in the documentation and plans, and that the project fits the terms of a remote "build your own project with an AI assistant" contract program.
- **Analysis (verified):**
  - The README says MIT, but there was no `LICENSE` file.
  - Commits are authored only by the owner's personal GitHub no-reply address; the repo is private.
  - The only employer or university mentions are the project's own "personal project" statements.
  - Raw cache scan (9,433 files): no CPF, birth data or education. It does contain office email, office phones and gender.
  - The database stores the civil name (Senado) and the photo URL, which are not shown.
  - Official photos are not shown, and the local photo serving required by decision 0012 is not built.
  - The Claude permissions in `.claude/settings.json` do not block reading `.env`.
- **Changes made:**
  - `LICENSE` (MIT, owner's name).
  - `docs/data-inventory.md`.
  - `docs/backlog.md`.
  - Proposed decision `0019-data-minimization.md`, added to the index as **proposed**; no code changed.
  - Phase C plan outcome.
  - CLAUDE.md "Where things are".
  - README: data-held section and license link.
  - MVP status: photos left out, related links.
- **Validation:** the claims in the data inventory were checked against the models, `PERSONAL_KEYS` and the cache scan.
- **Remaining work:**
  - Owner decision on 0019.
  - Optional deny rule for reading `.env` in the Claude settings.
  - The owner should confirm with the program whether data about public officials is eligible.
