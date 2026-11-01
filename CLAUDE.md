# Placar Parlamentar

Civic-transparency tool for Brazilian federal legislators, built only from official Câmara and Senado open data. Python (Django) backend, React frontend. Personal project.

## Before any work

1. Read and follow `docs/architecture-rules.md`. Those rules are binding. The decision records in `docs/decisions/` are the authority behind them.
2. Check `docs/decisions/README.md` for the status of every decision. Only accepted decisions are rules. Never change an accepted decision; propose a new one that supersedes it.
3. Never run `git push`, or any other action listed under "Approval gates" in the rules, without the project owner's explicit approval. One standing exception (rules section 18, decision 0021): once the owner has approved a change, push its branch, open a pull request, merge it after CI passes, and push the signed-off phase tag. `main` is protected on GitHub: never commit or push to it directly; every change goes through a pull request.
4. Do not implement a phase until the owner has approved its plan in `docs/plans/`.
5. Log meaningful work in `docs/agent-history/`.

## Key rules at a glance (details in the rules file)

- Official Câmara and Senado APIs only; elected officials in their public role only; no personal or private-life data.
- Every number and summary sentence links to its official source (`SourceRef`).
- Neutral wording, pt-BR interface, English code and docs.
- No visitor accounts, cookies, tracking, analytics or third-party requests.
- Secrets only in the git-ignored `.env`.
- Monorepo: `backend/` (Django 6.1 + Django Ninja, Python 3.14, uv), `frontend/` (React + TypeScript + Vite), linked only by `docs/api/openapi.json`.
- PostgreSQL 18 in Docker; raw API responses cached as files in `data/raw/`.
- Tests run offline with recorded fixtures.
- No deployment in the MVP.

## Local setup notes

- Enable the secret-scanning hook after cloning: `git config core.hooksPath scripts/git-hooks` (needs `gitleaks`).

## Where things are

- `README.md`: scope and principles.
- `CLAUDE_CODE_PROMPT.md`: original project prompt (stages and phases), for reference.
- `docs/decisions/`: decision records and index.
- `docs/architecture-rules.md`: binding rules.
- `docs/plans/`: phase plans (Stage 3).
- `docs/data-issues.md`: gaps and inconsistencies in official data.
- `docs/mvp-status.md`: what is done and left for the MVP; `docs/backlog.md`: work after it.
- `docs/definition-of-done.md`: checks before a merge or a phase is reported done.
- `docs/data-inventory.md`: what data is held about officials, where, and what is never collected.
- `docs/methodology/`: pt-BR methodology pages; `docs/wording/banned-pt-BR.txt`: banned wording.
- `docs/testing/` and `docs/security/`: test and security notes per phase.
- `docs/api/openapi.json`: API contract between backend and frontend.
- `.claude/agents/`: role agent definitions.
