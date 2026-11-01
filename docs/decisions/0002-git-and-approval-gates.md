# 0002 — Git workflow and approval gates

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 0

## Context

The project is tracked in a local git repository. The project owner wants every action that leaves the machine, or that cannot easily be undone, to need explicit approval first.

## Decision

1. The repository is a local git repo. Small, descriptive local commits are allowed.
2. **No agent or session may run `git push`.** Pushing is done by the project owner, or by an agent only after the owner explicitly approves that specific push.
3. The same "ask first" rule applies to:
   - adding or changing git remotes; creating pull requests, issues, releases or tags on any hosting service;
   - rewriting or deleting history (`reset --hard`, `rebase`, force operations, deleting branches);
   - publishing or deploying anything;
   - sending messages or posting to any external service;
   - deleting data (cache, database, fixtures) or files another role owns.
4. A project-level `.claude/settings.json` asks for confirmation on `git push`, remote changes, the `gh` CLI and recursive deletes, so the rule is enforced by the tool and not only by instructions.

## Alternatives considered

- **Block push completely in settings (deny).** Stricter, but then the owner could never approve a push from inside a session. "Ask" keeps the owner in control.
- **Instructions only, no settings.** Easy for an agent to miss; rejected.

## Consequences

- Every push and external action waits for the owner.
- Agents end their work with local commits at most, and list anything that needs approval.
