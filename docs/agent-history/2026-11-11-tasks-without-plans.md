# Allow work from specific owner tasks without a plan file

- **Date:** 2026-11-11
- **Agent:** main Claude Code session
- **Task:** Owner asked whether work required a plan, and said it must not: future work will come as specific task prompts without a plan.
- **Analysis:** The "plan first" rule was not in `docs/architecture-rules.md` or any accepted decision. It was in `CLAUDE.md` (Before any work, item 4), `docs/backlog.md`, `docs/definition-of-done.md`, and the backend, frontend and scrum-master agent definitions. Decision 0001 only lists plans as agent inputs, so no decision needed superseding.
- **Changes made:** Those six files now say work starts from a specific task the owner asked for, or from an approved phase plan. Definition of done: a plan outcome section is needed only when a plan exists; otherwise `docs/agent-history/` records the outcome. Agent definition edits were requested by the owner (rules section 4).
- **Validation:** `grep` for remaining "approved plan" wording in the rules, agents and docs; `git diff` reviewed. `scripts/check.sh` not run (docs only, Docker not running); relied on the PR CI checks.
- **Decisions:** Kept the owner-approval gate; only the plan file is optional. Large or unclear requests still need a question before starting.
- **Remaining work:** None.
