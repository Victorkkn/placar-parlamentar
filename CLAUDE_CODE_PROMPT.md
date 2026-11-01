# Project prompt for Claude Code: Placar Parlamentar

> Reference copy of the original project prompt (2026-11-01). The only change from the original is the project name, which was "Mandato Aberto".
> Later decisions and rules (for example, decision 0002: no `git push` without approval) are in `docs/decisions/` and `docs/architecture-rules.md`. If this file and an accepted decision differ, the accepted decision wins.

You are helping me build **Placar Parlamentar**, a civic-transparency tool for Brazilian federal legislators. Read `README.md` first for the scope and principles. Follow them strictly.

Stack: **Python** (backend) and **React** (frontend).

Do not write any application code until Stage 0 and Stage 1 are approved by me.

## Non-negotiable rules

1. Use only official open-data sources (Câmara dos Deputados and Senado Federal APIs). No social media, news scraping, personal accounts, or data about families or private lives.
2. Scope is limited to elected officials acting in their public role.
3. Every number and summary must link to its official source record.
4. Neutral language only. No judgmental labels such as "best", "worst", "lazy" or "corrupt".
5. No user accounts, no tracking, no storage of personal data about visitors.
6. Never write API keys, tokens or secrets into code, docs or the conversation. Use environment variables and a git-ignored `.env`.
7. Personal project. Do not reference any employer, client or university resources.
8. If a requirement conflicts with these rules, stop and ask me.

## How we work: decisions are recorded

- Every architecture or process decision is written to a file before it is used. Store decisions as short records in `docs/decisions/` (one file per decision, numbered, e.g. `0001-backend-framework.md`) with: context, decision, alternatives considered, consequences.
- Keep a single index at `docs/decisions/README.md` listing every decision and its status (proposed, accepted, superseded).
- Once a decision is accepted, it is a rule. Put the binding rules in `docs/architecture-rules.md` and reference them from `CLAUDE.md` at the repo root, so future sessions follow them.
- Do not change an accepted decision silently. Propose a new decision that supersedes it, and get my approval.

## Stage 0: Team and roles

Before any architecture work, propose the team needed to build this project. For each role, give: the responsibility, the inputs it needs, the outputs it produces, and whether it is needed for the MVP.

Propose at least these roles:

- **Project manager**: scope, priorities, risks, decisions log, status reports.
- **Scrum master**: sprint breakdown, backlog, definition of done, ceremonies as written notes.
- **Architect**: system design, module boundaries, data model, decision records, architecture rules.
- **Backend engineer (Python)**: API clients for the official sources, data model, metrics, API for the frontend.
- **Frontend engineer (React)**: filters, comparison views, leaderboards, summary display.
- **Data engineer**: ingestion pipelines, caching, handling incomplete or inconsistent official data.
- **QA engineer**: test strategy, fixtures from recorded API responses, end-to-end checks, checks that every number has a source link.
- **Security engineer**: secrets handling, dependency review, input validation, rate limiting, protection against injection through scraped or API text, privacy checks.
- **Technical writer**: README, methodology pages, user-facing explanations of metrics.

Then say which roles I can cover myself and which should be automated agents.

Wait for my approval of the team before continuing.

## Stage 1: Agents for each role

For each approved role, create a Claude Code subagent definition in `.claude/agents/<role>.md` with:

- Name and one-line description of when to use it.
- Responsibilities and what it must not do.
- The rules it must follow (point to `docs/architecture-rules.md` and the non-negotiable rules above).
- The files and folders it owns.
- Its definition of done.

Do not give any agent permission to publish, deploy, send messages, or delete data without my approval.

Wait for my approval of the agent definitions.

## Stage 2: Architecture (first decisions)

The architect role leads this stage. Write decision records, one at a time, for at least these topics, and wait for my approval on each before accepting it:

1. Repository layout (monorepo with `backend/` and `frontend/`, or two repositories).
2. Backend framework and project layout (FastAPI or an alternative, with reasons).
3. Database choice and how raw API responses are cached.
4. Module boundaries: ingestion, data model, metrics, summaries, API.
5. How the Câmara and Senado sources are normalized into one data model.
6. Frontend framework and build tooling for React, and how it talks to the backend.
7. How the LLM summarization feature is isolated, and how source links are enforced.
8. Testing strategy and the fixture approach for offline tests.
9. Security baseline: secrets, dependency scanning, input validation, rate limits to upstream APIs, logging rules that avoid storing personal data.
10. Deployment target, kept out of scope for the MVP unless I decide otherwise.

After all accepted decisions, write `docs/architecture-rules.md` as the binding summary and create `CLAUDE.md` pointing to it.

## Stage 3: Detailed phases (only after Stage 2 is accepted)

Plan the phases below in detail, with tasks, owners (agents), acceptance criteria and tests. Do not start implementing a phase until I approve its plan.

- **Phase A: Data access.** Clients for both official APIs, recorded fixtures, local cache, rate-limit handling. Verify each endpoint against its current documentation and note the source in code comments.
- **Phase B: Data model and metrics.** Officials, parties, mandates (including substitutes, leaves and party switches), bills authored, votes, committee and plenary attendance, speeches. A function `coverage(official, window)` that returns the days in office within a window and the coverage share. Metrics computed only over the period the official held the seat.
- **Phase C: Filters and comparison.** Date presets (current legislature, last 2 years, custom), a minimum-coverage threshold that can be set as days or as a share of the window, "insufficient data" labels instead of dropped officials, side-by-side comparison of officials, and party comparison with member counts.
- **Phase D: Summaries.** Neutral summaries from structured records only. Every factual sentence must trace to a source link, and a test must enforce this. Present summarization as a feature inside the app, not as model evaluation or training.
- **Phase E: Rankings.** One leaderboard per metric, starting with attendance and bills authored. No composite score in the MVP. Each leaderboard shows the window, threshold, metric definition and source. Ties handled explicitly. Insufficient-data officials marked as unranked.

## Working style

- Work in small steps. After each stage or phase, summarize what changed, list open questions, and wait for approval where this prompt says so.
- Record every decision in `docs/decisions/` before relying on it.
- Keep commits small and descriptive.
- Flag incomplete or inconsistent official data rather than guessing.
- Never skip a stage.

Begin with Stage 0: propose the team and roles.
