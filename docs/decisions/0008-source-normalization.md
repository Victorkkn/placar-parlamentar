# 0008 — Normalizing Câmara and Senado data into one model

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 2 (topic 5 of 10)

## Context

Metrics must use only the time each official actually held the seat (decision 0007, `metrics`). The two houses describe that time very differently. Checked on 2026-11-01 with the official specs and a few live responses:

**Câmara** (`/deputados/{id}/historico`, spec version 0.4.347):

- Returns a list of **events**, not periods. Each event has `dataHora`, `situacao` (e.g. `Exercício`, `VACANCIA`), `condicaoEleitoral` (`Titular`/`Suplente`), `siglaPartido` and a free-text `descricaoStatus` starting with `Entrada - …` or `Saída - …`.
- Example: deputy 220593 has an entry on 2023-02-01 ("Posse de Eleito Titular") and a vacancy on 2025-01-01.
- The party is known only at each event; there is no separate affiliation list.
- `/deputados?idLegislatura=57` returns 9 pages of 100 (801 to 900 people) for 513 seats, because substitutes are included.

**Senado** (spec version 4.1.3.108):

- `/senador/{codigo}/mandatos` (service v5) gives each mandate with its two legislatures, participation (`Titular`, `1º Suplente`, `2º Suplente`), and **`Exercicios`**: periods with start, end and the reason it ended (e.g. `LCS` leave with alternate called, `RET` return of the titular, `REN` resignation).
- `/senador/{codigo}/licencas` lists leaves with dates and type. Short leaves (up to 120 days) can happen **without** an alternate taking over: the titular 4545 had several short health leaves in 2022 while his `Exercicio` ran without a break.
- `/senador/{codigo}/filiacoes` gives party affiliations with start and end dates.
- Alternates who never took office have no `Exercicios` and no affiliations (senator 5918). This is expected, not missing data.
- Real sequence for seat mandate 526 (PE): titular 4545 in office until 2022-11-21 (leave), alternate 5917 from 2022-12-07, titular returns and resigns on 2023-09-04, alternate 5917 in office again from 2023-09-04. Alternate 5917 changed party (PSD from 2026-04-02).
- Legislature 57 list: 245 people (82 titulars, 82 first alternates, 81 second alternates); 126 took office. There are 82 titulars for 81 seats, which needs explaining (see data issues).

**Private data:** `/deputados/{id}` also returns fields that are outside the project's scope (for example CPF, birth date and place, social media links). These must not be stored.

## Decision

### Entities (shared by both houses)

| Entity | Meaning | Key fields |
| --- | --- | --- |
| `Legislature` | A four-year legislature. | number, start, end |
| `Official` | One person as a member of **one house**. | house, house's own id, parliamentary name, state (UF), official photo URL, `SourceRef` |
| `Party` | A party as named in the official data. | acronym, name, each house's own party id |
| `Mandate` | An elected term for a seat. | official, house, UF, legislatures covered, participation (titular / alternate rank), nominal start and end, `SourceRef` |
| `ServicePeriod` | A period when the official was **actually in office**. | official, mandate, start, end (open if still in office), start reason, end reason, `SourceRef` |
| `Leave` | An official leave. | official, start, end, type, whether an alternate took over, `SourceRef` |
| `PartyAffiliation` | Party membership over time. | official, party, start, end, date precision (exact / known only at event), `SourceRef` |

Every entity stores the raw official code and text next to any normalized value (for example `end_reason = RESIGNATION` and `end_reason_raw = "REN / Renúncia"`).

### Mapping rules

1. **Senado periods** come directly from `Exercicios`. **Senado affiliations** come from `filiacoes`. **Senado leaves** come from `licencas`.
2. **Câmara periods** are built from `historico` events, in date order: an `Entrada` event opens a period; the next `Saída` event closes it. The reason is taken from the event text.
3. **Câmara affiliations** are built from the party shown at each event. A change of party between two events starts a new affiliation on the later event's date, with precision "known only at event".
4. **Câmara leaves** are built from `Saída` events whose text describes a leave, until the matching `Entrada`.
5. **Dates:** all dates are calendar days in Brazil time (`America/Sao_Paulo`); Câmara timestamps are converted to dates. Periods include both their first and last day.
6. **Overlaps:** if two periods of the same official overlap or touch (for example ending and starting on 2023-09-04), they are merged for counting days, and the original periods are kept for display.
7. **Never guess:**
   - an event or reason that cannot be mapped is stored with reason `UNKNOWN` and logged in `docs/data-issues.md`;
   - an unmatched `Entrada` is treated as still open **only** if the official is listed as currently in office; otherwise it is logged;
   - when the two houses disagree (for example on legislature dates), both values are kept and the difference is logged.
8. **Same person in both houses:** the APIs use different ids and offer no official link. Officials are **not** linked across houses by name or any other guess. If an official link source is found later, a new decision adds it.
9. **Parties:** identified by the acronym and name as given. Renames and mergers are **not** inferred; parties with different acronyms stay separate unless an official source links them.
10. **Fields stored about a person** (allowlist): house id, parliamentary name, civil name, state, party, official photo URL, institutional page URL. Nothing else from the personal data fields: no CPF, birth date or place, social media, personal email or address.

### Source links

- Each record's `SourceRef` holds the API URL, the raw cache key (decision 0006) and, when one exists, the official public web page (for example the deputy's page on camara.leg.br or the senator's page on senado.leg.br). The app shows the public page when there is one, otherwise the API URL.

### Activity records

- Bills, votes, sessions, attendance and speeches follow the same pattern: house, date, official, normalized fields plus raw values, and a `SourceRef`. Their detailed fields are set in the Phase B plan.

## Alternatives considered

- **Store only Câmara and Senado records as they come, and compute periods at query time.** Less upfront work, but every metric would repeat the house-specific logic, and the two houses would be hard to compare.
- **Use leaves to cut service periods.** Simpler coverage numbers, but it contradicts the Senado's own data: short leaves do not interrupt `Exercicio` and no one else holds the seat. Leaves are kept separate so metrics can decide, with a published method, how to treat leave days.
- **Link the same person across houses by name.** Convenient, but it is a guess; homonyms and name changes would produce wrong links.
- **One `Person` table above `Official`.** Useful only if a cross-house link exists; not needed without one.

## Consequences

- `coverage(official, window)` (Phase B) counts the days of merged `ServicePeriod`s inside the window. How leave days without an alternate affect attendance metrics is a methodology choice for the Phase B plan, written down and shown in the app.
- Party comparisons can show members per party for any date, and flag officials whose party changed in the window.
- Câmara party-change dates are only as exact as the event dates; the methodology must say so.
- The data engineer must log every unmapped value instead of filling it in.
- A deputy who later becomes a senator appears as two officials.
