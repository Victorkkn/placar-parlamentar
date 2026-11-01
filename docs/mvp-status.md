# MVP status

What the MVP needs, what is done, and what is left. Updated 2026-11-01.

The MVP is phases A–E of `CLAUDE_CODE_PROMPT.md`, running locally on a snapshot of official data (decisions 0013 and 0015). Every number links to its official record; parts not built yet show "Ainda não disponível".

## Done

| Phase | What | State |
| --- | --- | --- |
| Stage 0–2 | Team, agents, decisions 0001–0017, binding rules | accepted |
| A | Official API clients, raw cache, polite HTTP, recorded fixtures, drift check | signed off, tag `phase-a` |
| B1 | People, service periods, leaves, party affiliations; `coverage(official, window)` | approved, tag `phase-b1` |
| B2 | Activity models (bills, sessions, presences, votes, ballots, memberships, speeches), first four metrics, methodology drafts | code done on `feat/b2-activity`; real data download running |
| C0 | Frontend setup and CI frontend job | merged to `main` |
| C1 | Read-only API (`/api/meta`, `/officials`, `/officials/{id}`, `/compare`, `/parties`) and OpenAPI contract | done on `feat/c1-api` |
| C2–C3 | Typed API client; officials list, official page, comparison, parties, methodology | done on `feat/c3-pages` |
| C5 | End-to-end tests (Playwright, axe) and CI e2e job | done on `chore/ci-and-tests` |
| CI | Migrations check, metrics coverage floor (90%), contract check | done on `chore/ci-and-tests` |

Branches stack in this order: `feat/b2-activity` → `feat/c1-api` → `feat/c3-pages` → `chore/ci-and-tests` → `docs/mvp-readiness`. None is merged into `main` yet.

## Left for the MVP

| # | Item | Needs | Owner action |
| --- | --- | --- | --- |
| 1 | Finish the B2 download, run `normalize_activity`, check unknown vote options, add activity fixture cases, write the B2 outcome | download to finish | review the B2 outcome |
| 2 | Merge the branch stack into `main`, tag `phase-b2` | 1 | **approve the merges** |
| 3 | C4: neutral-wording review of the pt-BR texts and methodology pages (including the "per 365 days in office" rate) | — | **review the wording** |
| 4 | C6: test and security notes, README "how to run" | — | done in `docs/mvp-readiness` (see `docs/testing/phase-c.md`, `docs/security/phase-c.md`) |
| 5 | Sign off Phase C, tag `phase-c` | 2–4 | **sign off** |
| 6 | Phase D: summaries | plan `docs/plans/phase-d-summaries.md` | **approve the plan and its choices** |
| 7 | Phase E: rankings | plan `docs/plans/phase-e-rankings.md` | **approve the plan and its choices** |
| 8 | Final MVP check: full `scripts/check.sh`, e2e, a manual walk through the app on the real snapshot | 1–7 | sign off the MVP |

## Left out of the MVP (listed as decision 0015 requires)

- **Câmara committee attendance** (decision 0014, item 4). Memberships are loaded; attendance is shown as not available.
- **Senado plenary attendance**: the Senado APIs used do not publish attendance per senator (decision 0014). The app says so.
- **Deployment**: local only (decision 0013).
- **Earlier legislatures**: the snapshot covers legislature 57.

## Owner to-dos outside the code

- Update Node 24 to 24.15 or later (one test dependency asks for it).
- Fix the npm cache ownership: `sudo chown -R "$(id -u)":"$(id -g)" ~/.npm`.
