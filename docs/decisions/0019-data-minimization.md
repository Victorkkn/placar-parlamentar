# 0019 — Data minimization for officials' contact and identity fields

- **Status:** accepted (2026-11-01), approved by the owner and implemented the same day.
- **Date:** 2026-11-01
- **Stage:** 3
- **Supersedes:** decision 0006, item 6 (cache keeps the unchanged response body), only for the fields below; decision 0008, item 10 (civil name and photo URL in the allowlist).

## Context

A scan of the raw cache on 2026-11-01 (see `docs/data-inventory.md`) found **office** email, **office** phone numbers and gender in the official responses. The app never uses them. The database also stores the civil name (Senado) and the official photo URL, which the app does not show; decision 0012 requires photos to be downloaded and served locally, which was never built.

Keeping less personal data lowers risk and makes the project's data use easier to explain.

## Decision

1. **Strip before caching.** The fetch step removes the fields in `PERSONAL_KEYS` (`sources/fixtures.py`: CPF, birth data, education, social media, email, phone, address, gender) from response bodies before writing the cache file. The envelope records which paths were removed. The fixtures already use the same function.
2. **Clean the existing cache** once with a management command that applies the same step to every cached file (no new downloads).
3. **Stop storing the civil name and the photo URL**, and remove `photo_url` from the API. Photos stay out of the MVP. Adding them later needs a new decision, with local serving as decision 0012 requires.

## Implementation (2026-11-01)

- `placar/sources/personal.py` holds the field list and the strip function, used by the cache (`RawCache.write`, which counts removals in `removed_personal_fields`) and by fixture recording.
- `scrub_cache` command: run once on the existing cache. It checked 11,191 files, cleaned 2,689 and removed 686,635 fields; a scan afterwards found none left. Loading from the cleaned cache gave the same counts as before.
- Migration `legislators` 0005 drops `civil_name` and `photo_url`; parsers no longer read them; API contract and frontend types regenerated.

## Alternatives considered

- **Keep things as they are.** No work, but the cache keeps contact data the project never uses.
- **Strip only in the database.** That is already the case; the cache would still hold the fields.

## Consequences

- The cache is no longer a byte-for-byte copy of the response for those fields. Every other value stays unchanged, and every record still links to the official URL.
- Migration to drop two columns; the API contract and frontend types change (`photo_url` removed).
