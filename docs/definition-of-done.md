# Definition of done

A task or phase is done only when every item below is true. Owned by the scrum master (decision 0001); the checks come from the accepted decisions and `docs/architecture-rules.md`.

## Every change

- Work is on a branch, never directly on `main` (decision 0016).
- The pre-commit hook passed: secret scan, backend lint, and frontend lint and type check when frontend files changed.
- New behavior has tests that run offline. Real cases use recorded fixtures; synthetic data comes from `backend/tests/builders.py` and is never shown in the app (decision 0011).
- Every number and summary sentence shown to visitors has its official source link (rule 3); the generic source test and the frontend source-link test pass.
- User-facing text is in pt-BR, neutral, and passes the banned-wording check (rule 4, decision 0018).
- A new decision is recorded before it is relied on; an accepted decision is changed only by a new one.

## Before a merge into `main`

- `scripts/check.sh` passes: lint, migrations check, full test suite with the `metrics/` coverage floor (90%), `pip-audit`, frontend checks and contract check, and a secret scan of the branch.
- `npm run e2e` passes when pages, the API or the fixtures changed.
- The owner approved the merge. Merges use `git merge --no-ff`.

## Before a phase is reported done

- Its plan in `docs/plans/` has an outcome section with what was built, deviations and what is left.
- Test and security notes are in `docs/testing/` and `docs/security/`; `pip-audit` and `npm audit` are clean or explained.
- Data problems found are in `docs/data-issues.md`.
- `docs/agent-history/` records the work actually done and the checks actually run.
- `docs/mvp-status.md` and the README are up to date.
- The owner signed off; the phase is tagged on `main` (`phase-a`, `phase-b1`, …) and pushed.
