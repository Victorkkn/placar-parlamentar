# 0018 — One banned-wording list for the app and the summaries

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 3 (Phase D)
- **Supersedes:** decision 0010, item 7, only the location of the banned-wording list (`summaries/wording/`).

## Context

Decision 0010 puts the banned-wording list for summaries in `backend/placar/summaries/wording/`. Phase C already created `docs/wording/banned-pt-BR.txt`, which the frontend wording test checks. Two lists could drift apart.

## Decision

- `docs/wording/banned-pt-BR.txt` is the only banned-wording list. The interface text check (frontend) and the summary validator (backend) both read it.
- Matching stays as the file header says: whole words, ignoring accents and case.
- The technical writer owns the file; the owner reviews changes.

## Alternatives considered

- **Two lists, one per side.** Matches 0010 as written, but the lists can disagree.
- **Backend list, frontend copy generated from it.** More moving parts for no gain.

## Consequences

- The summary validator reads a file outside `backend/`. The path is set in settings and checked by a test.
