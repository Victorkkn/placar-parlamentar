# Phase D — test report (summaries)

- **Date:** 2026-11-01
- **Branch:** `feat/d-summaries`
- **Commands:** `scripts/check.sh`, `cd frontend && npm run e2e`

## Result

- Backend: 332 passed (35 of them in `test_summaries.py`), lint, format and migrations check clean.
- Frontend: 18 passed; lint, type check, contract check and build clean.
- End to end: 4 passed, now also checking the summary label and a source link on every summary sentence.
- No test calls the real model API: a fake model is used everywhere (decision 0010, item 14).

## What is covered

| Area | Tests |
| --- | --- |
| Template | Passes the validator for **every** fixture official in three windows (legislature, last 2 years, a window before most mandates); every shown sentence has at least one `SourceRef` |
| Validator rules | One crafted bad sentence per rule: no fact cited, unknown fact id, number not in facts, number from an uncited fact, date not in facts, unknown name, unknown party, "PL" used as a party without citing it, banned wording, too long, empty; sentence count 0 and 7; cited facts without any source |
| Fact sheet | Metric facts only for loaded activity (Senado not loaded → none); no URLs or free text in what the model sees; the hash changes when a value or a source changes |
| Generation | Valid draft stored and shown as "model"; second run skips (no paid call); error then valid draft uses the retry; two failures fall back to the template and record the problems; no time in office makes no call |
| Read path | A stored summary is not shown if the facts changed (hash) or if it fails the validator again when read |
| Command | Without a key: nothing happens. With a (fake) model: lists the planned calls and sends nothing without `--yes` |
| API | `/officials/{id}` has `summary` with sources on every sentence; `/compare` has none; the generic source check still passes |
| Frontend | Summary section with the kind label, methodology link and a source link per sentence; wording test covers the new text |
