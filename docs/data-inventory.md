# Data inventory

What data the project holds, where, and why. Checked against the code and the local cache on 2026-11-01.

## Visitors

**None.** No accounts, cookies, sessions, analytics or tracking. The API stores nothing about requests. The frontend may not use browser storage (lint rule, tested). See rules 1 and 5 and decision 0012.

## Elected officials (public role only)

Source: the official open-data APIs of the Câmara dos Deputados and the Senado Federal. Scope: deputies and senators of legislature 57, in their public role.

| Where | What | Notes |
| --- | --- | --- |
| Database (`legislators`) | House id, parliamentary name, state (UF), party affiliations with dates, institutional page URL; periods in office, leaves and their official reasons | Allowlist in decisions 0008 and 0019. No civil name and no photo |
| Database (`activity`) | Bills authored (type, number, year, date, official summary or "ementa"), plenary sessions and presence, nominal votes and ballots, committee memberships, speech records (date, type and session; not the speech text) | Public parliamentary activity only |
| Database (`summaries`) | Model summaries generated from the above (none generated so far) | Decision 0010 |
| Raw cache (`data/raw/`, git-ignored, local only) | Official API responses in their original form (decision 0006) | Personal and contact fields (email, phone, address, gender, CPF, birth data, education, social media) are **removed before each response is written** (decision 0019). The cache written before that was cleaned with `scrub_cache` on 2026-11-01: 686,635 fields removed from 2,689 of 11,191 files; a scan afterwards found none |
| Test fixtures (`backend/tests/fixtures/`, in git) | Small recorded responses for 2 deputies and 3 senators | Personal fields removed when recorded; a test fails if any remain (decision 0011) |

**Never collected:** CPF, birth date or place, education, social media, personal email, home address, family members, or anything about private life (rule 1, decision 0008).

## Sent to third parties

- **Official APIs:** only the requests needed to download public data, under a project `User-Agent` without personal email (decision 0012).
- **Claude API (optional, off by default):** only when the owner runs `generate_summaries --yes` with a key. Only the fact sheet is sent: ids, types and formatted values from official records, with no URLs, free text or visitor data (decision 0010). No call has been made so far.

## Retention

The raw cache and the database are local to the owner's machine (decision 0013: no deployment). They are refreshed by hand and can be deleted at any time; nothing is published.
