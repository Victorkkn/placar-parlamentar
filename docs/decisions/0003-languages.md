# 0003 — Languages for the interface, code and docs

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 0

## Context

The app is for Brazilian users, but the codebase and project documents are written in English.

## Decision

- **User interface:** Brazilian Portuguese (pt-BR), including methodology pages shown in the app.
- **Code, comments, commit messages, decisions and internal docs:** English.
- Official field names and terms from the APIs (for example `siglaPartido`, "suplente", "licença") keep their original Portuguese spelling.

## Alternatives considered

- **Everything in Portuguese.** Closer to the audience, but the project prompt and docs are already in English.
- **Bilingual interface.** More work for the MVP; can be added later.

## Consequences

- The technical writer drafts user-facing text in pt-BR; the project owner reviews it for neutral wording.
- Translations of official terms are explained in the methodology, not changed in the data.
