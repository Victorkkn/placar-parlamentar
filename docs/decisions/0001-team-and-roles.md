# 0001 — Team and roles

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 0

## Context

Placar Parlamentar is a personal civic-transparency project (Python backend, React frontend) built by one person working with Claude Code. The work needs clear owners so that rules (official sources only, a source link for every number, neutral language, no visitor data, no secrets in the repo) are checked by someone at every step. Every agent prepares work; the project owner approves it.

## Decision

Nine roles. Each one lists its responsibility, inputs, outputs and whether the MVP needs it. Who fills each role is in the "Who covers what" section.

### 1. Project manager
- **Responsibility:** scope, priorities, risks, the decisions index, approvals, status reports.
- **Inputs:** README, project prompt, stage and phase summaries, open questions from every role.
- **Outputs:** approved scope, priority order, `docs/decisions/README.md` statuses, risk list, a status note after each stage or phase.
- **MVP:** yes.

### 2. Scrum master
- **Responsibility:** splitting phases into tasks and sprints, backlog, definition of done, written notes for ceremonies (planning, review, retrospective).
- **Inputs:** approved phase plans, the decisions, the agents' definitions of done.
- **Outputs:** `docs/backlog.md`, `docs/definition-of-done.md`, sprint notes in `docs/sprints/`.
- **MVP:** yes, kept light (one short note per phase, not formal ceremonies).

### 3. Architect
- **Responsibility:** system design, module boundaries, the shared data model for Câmara and Senado, decision records, architecture rules.
- **Inputs:** project prompt, official API specs, constraints from security and QA.
- **Outputs:** `docs/decisions/NNNN-*.md`, `docs/architecture-rules.md`, root `CLAUDE.md`, data model diagrams.
- **MVP:** yes. Leads Stage 2.

### 4. Backend engineer (Python)
- **Responsibility:** data model code, metrics (including `coverage(official, window)`), summary feature, the HTTP API used by the frontend.
- **Inputs:** accepted decisions, normalized data from the data engineer, phase plans.
- **Outputs:** backend modules for the model, metrics, summaries and API; unit tests; API contract (OpenAPI).
- **MVP:** yes.

### 5. Frontend engineer (React)
- **Responsibility:** date filters and thresholds, "insufficient data" display, comparison views, party view, leaderboards, summary display with source links, accessibility.
- **Inputs:** API contract, methodology texts, neutral-language rules.
- **Outputs:** frontend code, component tests, checks that every number shown has a link.
- **MVP:** yes.

### 6. Data engineer
- **Responsibility:** clients for both official APIs, raw response cache, rate-limit handling, normalizing both houses into one model, reporting gaps and inconsistencies in official data.
- **Inputs:** official API specs (current version), architecture decisions on storage and normalization.
- **Outputs:** ingestion and source modules, the cache, the fetch command, a data-quality log (`docs/data-issues.md`).
- **MVP:** yes.

### 7. QA engineer
- **Responsibility:** test strategy, recorded fixtures, offline test suite, end-to-end checks, a check that every number and summary sentence has a source link, checks on each phase's acceptance criteria.
- **Inputs:** acceptance criteria, API contract, recorded responses.
- **Outputs:** test plan, fixtures, tests, a written pass/fail report per phase.
- **MVP:** yes.

### 8. Security engineer
- **Responsibility:** secrets handling, dependency review, input validation, polite request rates to official APIs, protection against harmful text coming from API fields (for example in summaries or rendered HTML), privacy checks (no visitor data, no data on private lives), logging rules.
- **Inputs:** the code changes, dependency lists, decisions.
- **Outputs:** security baseline decision, a review note per phase, dependency-scan results.
- **MVP:** yes, as a review at the end of each phase.

### 9. Technical writer
- **Responsibility:** README, methodology pages, plain-language explanations of each metric, neutral wording, the user-facing text that says what summaries are and are not.
- **Inputs:** metric definitions, decisions, data-quality log.
- **Outputs:** `README.md`, `docs/methodology/`, UI text reviewed for neutral wording.
- **MVP:** yes (README and methodology for attendance and bills authored at least).

## Who covers what (proposed)

| Role | Covered by |
|---|---|
| Project manager | Project owner. Approvals and priorities stay human. |
| Scrum master | Agent drafts; project owner approves. |
| Architect | Agent drafts decisions; project owner accepts each one. |
| Backend engineer | Agent. |
| Frontend engineer | Agent. |
| Data engineer | Agent. |
| QA engineer | Agent. |
| Security engineer | Agent reviews; project owner approves new dependencies and anything about secrets. |
| Technical writer | Agent drafts; project owner reviews the Portuguese wording for neutrality. |

The main Claude Code session coordinates the agents. Agents do not start other agents.

## Alternatives considered

- **Fewer roles** (for example, merging data and backend, or QA and security). Fewer files, but the boundaries matter here: ingestion has its own failure modes, and the source-link and privacy checks need a separate reviewer.
- **A separate neutrality and methodology reviewer.** Not added: the technical writer owns the wording and QA checks the source links.
- **A UX designer.** Not needed for the MVP; the frontend engineer covers basic layout and accessibility.

## Consequences

- Each role becomes one subagent in Stage 1, with clear owned files.
- The project owner is the single approver, so work waits for approval at each stage gate.
- No agent can publish, deploy, send messages or delete data without the project owner's approval.
