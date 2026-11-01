# 0021 — Protected `main`: every change through a pull request

- **Status:** accepted (2026-11-01), requested by the owner
- **Date:** 2026-11-01
- **Stage:** 3
- **Supersedes:** in decision 0016, local `git merge --no-ff` into `main`, the standing approval to push `main`, and the note that branch protection is unavailable (the repository is now public, where the free plan allows it).

## Context

The owner wants no direct pushes to `main`: every change must arrive through a pull request. The repository became public on 2026-11-01, so GitHub branch protection is now available on the free plan.

## Decision

1. **Branch protection on `main`** (GitHub setting):
   - a pull request is required, with no direct pushes;
   - the CI checks `backend`, `frontend`, `e2e` and `secrets` must pass, on a branch that is up to date with `main`;
   - the rules apply to administrators too, so the owner and the assistant are bound by them;
   - no force pushes and no deletion of `main`;
   - open review conversations must be resolved before merging;
   - required approving reviews: **0**. The owner is the only maintainer, and GitHub does not let authors approve their own pull requests. The owner's approval is given in the session (decision 0002) or by merging on GitHub.
2. **Workflow:**
   1. Work happens on a branch.
   2. `scripts/check.sh` passes locally.
   3. The branch is pushed and a pull request is opened against `main`.
   4. CI must pass.
   5. The owner approves.
   6. The pull request is merged with a **merge commit** (keeps the `--no-ff` history), and the branch is deleted.
3. **Standing approval (replaces the one in decision 0016):** once the owner has approved a change, the assistant may push its branch, open the pull request, merge it after CI passes, delete the branch, and push the phase tag the owner signed off. Any other push, a force push, a remote change or a repository setting still needs the owner's approval (decision 0002).
4. **CI runs once per pull request.** The workflow triggers on `pull_request` and on pushes to `main` only, so a branch push does not start a second, duplicate run. A branch without a pull request gets no CI run, which is fine because every change goes through a pull request.
5. Tags are not protected. Phase tags are still created only after the owner signs off a phase.

## Alternatives considered

- **Require one approving review.** Impossible for a single maintainer without a second account; it would block every merge.
- **Protect `main` without applying it to administrators.** The owner could still push directly, which is what the owner asked to prevent.
- **Squash merges.** A cleaner history, but loses the per-step commits the agent history refers to.

## Consequences

- Every change to `main` leaves a pull request with its CI result.
- Merges happen on GitHub (`gh pr merge --merge`), not locally.
- Emergency fixes also go through a pull request. Turning protection off needs the owner's approval and must be recorded.
