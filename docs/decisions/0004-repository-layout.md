# 0004 — Repository layout

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 2 (topic 1 of 10)

## Context

Placar Parlamentar has a Python backend and a React frontend, built by one person with Claude Code agents. The backend serves an API that the frontend depends on; most features (filters, comparisons, leaderboards, summaries) change both sides at once. Decisions, rules, agent definitions and the agent history must apply to the whole project.

## Decision

Use **one repository (monorepo)** with this top-level layout:

```
Placar Parlamentar/
├── backend/          Python project (internal layout: decision on backend framework)
├── frontend/         React app (internal layout: decision on frontend tooling)
├── docs/             decisions, architecture rules, methodology, data issues,
│                     testing and security notes, agent history
├── scripts/          developer scripts run by hand (for example, recording fixtures)
├── .claude/          agent definitions and project settings
├── README.md
├── CLAUDE.md
└── CLAUDE_CODE_PROMPT.md
```

- `backend/` and `frontend/` are self-contained: each has its own dependency file, tests and run commands. Neither imports code from the other.
- The only link between them is the HTTP API contract (how it is shared is set in the frontend decision).
- Local data (API cache, database files) stays out of git. Its location is set in the database decision.
- No monorepo build tool (such as Nx or Turborepo) for now.

## Alternatives considered

- **Two repositories (backend and frontend).** Clean separation and independent releases, but one person would have to keep decisions, rules, agents and history in sync across two places, and a feature touching both sides would need two coordinated commits. Not worth it at this size.
- **Monorepo with a build tool (Nx, Turborepo, Pants).** Helps with many packages and shared caching; adds setup and a learning curve the MVP does not need. Can be added later through a new decision.
- **Backend serves the built frontend from one Python package.** Fewer moving parts at deploy time, but mixes the two toolchains and ties frontend builds to backend releases. Deployment is out of scope for the MVP anyway.

## Consequences

- The provisional folders in the agent definitions (`backend/`, `frontend/`, `scripts/`) become confirmed.
- One commit can change the API and the screen that uses it, keeping them consistent.
- Two toolchains (Python and Node) are needed on the development machine.
- If the project grows, splitting the repository later needs a new decision that supersedes this one.
