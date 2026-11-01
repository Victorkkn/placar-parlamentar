# Data inventory

What data the project holds, where, and why. Checked against the code and the local cache on 2026-11-01.

## Visitors

**None.** No accounts, cookies, sessions, analytics or tracking. The API stores nothing about requests. The frontend may not use browser storage (lint rule, tested). See rules 1 and 5 and decision 0012.

## Elected officials (public role only)

Source: the official open-data APIs of the Câmara dos Deputados and the Senado Federal. Scope: deputies and senators of legislature 57, in their public role.

| Where | What | Notes |
| --- | --- | --- |
| Database (`legislators`) | House id, parliamentary name, civil name (Senado only), state (UF), party affiliations with dates, official photo URL, institutional page URL; periods in office, leaves and their official reasons | Allowlist in decision 0008, item 10. Civil name and photo URL are stored but **not shown** in the app |
| Database (`activity`) | Bills authored (type, number, year, date, official summary or "ementa"), plenary sessions and presence, nominal votes and ballots, committee memberships, speech records (date, type and session; not the speech text) | Public parliamentary activity only |
| Database (`summaries`) | Model summaries generated from the above (none generated so far) | Decision 0010 |
| Raw cache (`data/raw/`, git-ignored, local only) | Official API responses in their original form (decision 0006) | Scan of all 11,191 files after the full download (2026-11-01), by field name: **no** CPF, birth date, birthplace or education fields. The responses do include **office** email (institutional addresses such as `dep.…@camara.leg.br`, repeated in every vote and presence list), **office** phone numbers (Senado) and gender (`sexo`) for officials. These fields are not normalized, stored in the database or shown. Proposed decision 0019 would remove them before caching |
| Test fixtures (`backend/tests/fixtures/`, in git) | Small recorded responses for 2 deputies and 3 senators | Personal fields removed when recorded; a test fails if any remain (decision 0011) |

**Never collected:** CPF, birth date or place, education, social media, personal email, home address, family members, or anything about private life (rule 1, decision 0008).

## Sent to third parties

- **Official APIs:** only the requests needed to download public data, under a project `User-Agent` without personal email (decision 0012).
- **Claude API (optional, off by default):** only when the owner runs `generate_summaries --yes` with a key. Only the fact sheet is sent: ids, types and formatted values from official records, with no URLs, free text or visitor data (decision 0010). No call has been made so far.

## Retention

The raw cache and the database are local to the owner's machine (decision 0013: no deployment). They are refreshed by hand and can be deleted at any time; nothing is published.
