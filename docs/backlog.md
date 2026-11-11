# Backlog

Work after the current MVP steps (`docs/mvp-status.md`). Each item starts once the owner asks for it as a task, or approves a plan or decision for it.

## Waiting for the owner

- Optional: one real `generate_summaries` run with your key, outside any recorded session.

## After the MVP

- Phase E: rankings (plan approved; deferred by decision 0020). Its plan file `docs/plans/phase-e-rankings.md` is kept only in the owner's local copy, not in git (owner request, 2026-11-11).
- Câmara committee attendance (deferred by decision 0014).
- Official photos, if wanted: needs a new decision (0019 removed them), with local serving as decision 0012 requires.
- Earlier legislatures (only legislature 57 is in the snapshot).
- Performance: the first Câmara party view per period takes about 9 s (then cached in memory). Storing computed metrics after each load would make every view fast.
- A documented, repeatable snapshot refresh (fetch, normalize, regenerate summaries).
- Deployment, through a new decision covering rate limits, caching and headers (decision 0013).
- Bump TypeScript when the lint and contract tools support a newer major (decision 0017).
