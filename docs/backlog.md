# Backlog

Work after the current MVP steps (`docs/mvp-status.md`). Each item needs an approved plan or decision before it starts.

## Waiting for the owner

- Merge the branch stack into `main`; tag `phase-b2`, then `phase-c` and `phase-d` after sign-off.
- C4 wording review: pt-BR interface text, methodology pages (including "por 365 dias no cargo" and "Resumos").
- Phase D: confirm the two deviations (1–6 sentences; bill types tied to the bills fact).
- Decision 0019 (data minimization): approve or reject.
- Optional: one real `generate_summaries` run with your key, outside any recorded session.

## MVP

- B2 wrap-up after the download: `normalize_activity`, unknown vote options, activity fixture cases, B2 outcome and test/security notes.
- Phase E: rankings (plan approved).
- Final MVP check on the real snapshot.

## After the MVP

- Câmara committee attendance (deferred by decision 0014).
- Official photos served locally (decision 0012), if wanted.
- Earlier legislatures (only legislature 57 is in the snapshot).
- Performance on the full snapshot: indexes or stored results if lists, parties or rankings are slow.
- A documented, repeatable snapshot refresh (fetch, normalize, regenerate summaries).
- Deployment, through a new decision covering rate limits, caching and headers (decision 0013).
- Bump TypeScript when the lint and contract tools support a newer major (decision 0017).
