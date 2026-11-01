# 0020 — The MVP ships without rankings (Phase E moves after the MVP)

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 3

## Context

`CLAUDE_CODE_PROMPT.md` lists phases A–E. The owner needs a working MVP to show soon. Phases A–D (data, metrics, filters and comparison, summaries) are built. The Phase E plan (rankings) is approved but not started. On 2026-11-01 the owner decided not to build Phase E now.

## Decision

1. The MVP is phases A–D on the real data snapshot (decision 0015).
2. Phase E stays approved as written in `docs/plans/phase-e-rankings.md` and is the first item after the MVP (`docs/backlog.md`).
3. The app shows no rankings page and no "Ainda não disponível" placeholder for it. Officials can still be sorted and compared in the existing pages.

## Alternatives considered

- **Build Phase E before showing the MVP.** Completes the original prompt, but delays the MVP.

## Consequences

- The MVP sign-off covers phases A–D only.
- The README and `docs/mvp-status.md` list rankings as not in the MVP.
