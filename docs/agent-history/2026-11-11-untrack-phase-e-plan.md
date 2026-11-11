# Untrack the Phase E plan

- **Date:** 2026-11-11
- **Agent:** main Claude Code session
- **Task:** Owner asked to remove the remaining (unbuilt) phase plan from git.
- **Analysis:** Phases A–D are built; `docs/plans/phase-e-rankings.md` is the only plan left (deferred by decision 0020). Decision 0020 (accepted) cites the file by path, so it was kept on disk rather than deleted; accepted decisions are not edited. The file remains in earlier commits of the public repository; removing it from history would need a history rewrite (approval gate, decision 0002) and was not done.
- **Changes made:** `git rm --cached docs/plans/phase-e-rankings.md` (file kept locally); `.gitignore` ignores it; `docs/backlog.md` notes the plan is local only.
- **Validation:** `git check-ignore` confirms the file is untracked and ignored. `scripts/check.sh` did not run locally (Docker/PostgreSQL not running); relied on the PR CI checks.
- **Decisions:** Untrack and ignore instead of deleting, so the approved plan is not lost and decision 0020's reference still resolves locally.
- **Remaining work:** Owner to decide whether to purge it from git history, and whether the other (built) plans should also leave git.
