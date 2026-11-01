# 0016 — Git workflow, local checks and GitHub Actions CI

- **Status:** proposed
- **Date:** 2026-11-01
- **Stage:** 3
- **Supersedes:** decision 0013, item 2, for the parts "no remote repositories" and "no CI services". Everything else in 0013 stays: no deployment in the MVP.
- **Builds on:** decision 0002 (approval gates), which stays in force.

## Context

The owner wants proper git workflows: a branching process, local checks before commits, and CI on GitHub (choices made on 2026-11-01). So far all work has been committed directly to `main` in a local repository with no remote. Decision 0002 requires approval before any push, remote change or pull request.

## Decision

### Branches

1. `main` always passes all checks. Nobody commits to it directly.
2. Work happens on short-lived branches named by type: `feat/<phase>-<topic>` (for example `feat/b2-activity-models`), `fix/<topic>`, `docs/<topic>`, `chore/<topic>`.
3. A branch is merged into `main` with `git merge --no-ff` only when:
   - all local checks pass (`scripts/check.sh`);
   - the project owner approves the merge.
   Branches are deleted after merging; the owner's approval is part of the merge request, so no separate approval is needed for that deletion.
4. When the owner signs off a phase, `main` gets an annotated tag (`phase-a`, `phase-b1`, …).
5. Commit messages: a short imperative summary line with the phase or area first (for example "B2: add activity models"), a blank line, then what changed and why.

### Local checks

6. **Pre-commit hook** (`scripts/git-hooks/pre-commit`), fast:
   - gitleaks on staged changes (as today);
   - `ruff check` and `ruff format --check` on the backend.
7. **`scripts/check.sh`**, before every merge:
   - lint;
   - the full test suite (needs Docker running for PostgreSQL);
   - `pip-audit`;
   - a gitleaks scan of the branch.

### GitHub and CI

8. One **GitHub repository** owned by the project owner. Creating it, choosing private or public, adding the remote and every push still need the owner's explicit approval (decision 0002).
9. **GitHub Actions** workflow `.github/workflows/ci.yml` on every push and pull request:
   - backend: install with `uv`, PostgreSQL service container, ruff, pytest (offline: `pytest-socket` still blocks the internet), `pip-audit`;
   - secrets: gitleaks over the full history;
   - frontend jobs added in Phase C.
10. CI uses **no secrets**. Tests use the test-only Django key, and the database password exists only inside the CI job.
11. Third-party actions are pinned to a full commit SHA, and the workflow has read-only `contents` permission.
12. `main` on GitHub is protected: changes only through pull requests with passing CI. The owner sets this up in the GitHub settings, or approves the session doing it.

## Alternatives considered

- **Branching only, no CI.** No GitHub account or remote needed, but checks then depend on remembering to run them locally.
- **Trunk-based (commit to `main`) with CI.** Simpler, but every unfinished change lands in `main`.
- **pre-commit framework (`pre-commit` package).** Popular, but one more dependency; a small shell hook is enough.
- **Running the full test suite in the pre-commit hook.** Most thorough, but it needs Docker on every commit and slows small commits; it runs in `scripts/check.sh` and CI instead.

## Consequences

- From now on, work in progress goes on branches. Phase B2 continues on `feat/b2-activity`.
- A GitHub repository makes the code visible to whoever the owner chooses; secrets stay out by design (gitleaks and the history scan in CI).
- New tool needed: none locally (gitleaks, ruff and uv are installed). CI downloads uv, gitleaks and the PostgreSQL image at run time.
- The README gets a "Contributing / workflow" section.
