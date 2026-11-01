# 0017 — TypeScript version for the frontend

- **Status:** proposed
- **Date:** 2026-11-01
- **Stage:** 3 (Phase C)
- **Supersedes:** decision 0009, item 3 (TypeScript version) only.

## Context

Decision 0009 says to use the latest TypeScript that the lint and test tools support, "7.x, else 6.x". Checked on npm on 2026-11-01:

| Package | Version | TypeScript it declares support for |
| --- | --- | --- |
| typescript | 7.0.2 (latest), 6.0.3, 5.9.3 | — |
| typescript-eslint | 8.72.1 | `>=4.8.4 <6.1.0` |
| openapi-typescript | 7.13.0 | `^5.x` |
| msw | 3.0.3 | `>=5.9.x` |

No 7.x works with `typescript-eslint`. `openapi-typescript`, which generates the API types (decision 0009, item 7), declares only 5.x.

## Decision

- Use **TypeScript 5.9.3**, pinned exactly in `frontend/package.json`.
- Move to a newer major when all three tools declare support for it, through a new decision.

## Alternatives considered

- **TypeScript 6.0.3 with a forced install** (`--legacy-peer-deps` or `overrides`). Works with `typescript-eslint`, but goes against `openapi-typescript`'s declared support and hides peer-dependency problems.
- **TypeScript 7 without `typescript-eslint`.** Loses the lint rule that bans `dangerouslySetInnerHTML` (decision 0012).

## Consequences

- No forced peer-dependency overrides in the frontend.
- TypeScript 6/7 features are not available until the tools catch up.
