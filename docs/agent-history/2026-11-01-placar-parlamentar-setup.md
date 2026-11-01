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
