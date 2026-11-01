# Architecture rules — Placar Parlamentar

These rules are binding for every session and every agent. Each rule comes from an accepted decision in `docs/decisions/` or from the project's non-negotiable rules.
A rule changes only through a new decision that supersedes the old one and is approved by the project owner.

Stage 2 (architecture) decisions will add technical rules here as each one is accepted.

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
