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
