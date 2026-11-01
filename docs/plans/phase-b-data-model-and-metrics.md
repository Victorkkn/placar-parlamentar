# Phase B — Data model and metrics (plan)

- **Status:** approved by the project owner on 2026-11-01, with the recommendations on Choices 1–4 (recorded as decision 0014) and the `hypothesis` dependency.
- **Date:** 2026-11-01
- **Decisions applied:** 0005–0013, especially 0007 (module boundaries) and 0008 (normalization)

## Goal

Turn the cached official data into database records for officials, parties, mandates, periods in office, leaves, party affiliations, and their public activity, and compute metrics only over the time each official held the seat:

- `coverage(official, window)` returns the days in office within a window and the coverage share.
- Every stored record and every metric value carries its `SourceRef`.

## Milestones

Phase B is large, so it is split in two milestones, each with its own acceptance check. B2 starts only after B1 passes.

- **B1 — People and time in office.** Models, normalizers from the Phase A cache, and `coverage()`.
- **B2 — Activity and metrics.** New fetches (bills, votes, attendance, committees, speeches), activity models and the first metrics.

## B1 — People and time in office

### Models

Django apps `legislators` (no new fetching; uses the Phase A cache):

| Model | Key fields |
| --- | --- |
| `Legislature` | number, start, end, house-specific source refs |
| `Official` | house (`CAMARA`/`SENADO`), house id, parliamentary name, civil name (Senado only for now), state, official photo URL, page URL, `SourceRef` |
| `Party` | acronym, name, Câmara id, Senado code |
| `Mandate` | official, house, state, legislatures, participation (titular / alternate rank / suplente), nominal start and end, titular (for alternates), `SourceRef` |
| `ServicePeriod` | official, mandate, start, end (null = still in office), start reason, end reason, raw reason code and text, `SourceRef` |
| `Leave` | official, start, end, type (raw code and text), `SourceRef` |
| `PartyAffiliation` | official, party, start, end, date precision (`EXACT` / `AT_EVENT`), `SourceRef` |

`SourceRef` is stored as fields: API URL, cache file id, public URL, label.

### Normalizers (`sources/normalize/`, write only through `legislators/services.py`)

- **Senado:** periods from `Exercicios`, leaves from `licencas`, affiliations from `filiacoes`. Alternates who never took office get a `Mandate` and no `ServicePeriod`.
- **Câmara:** periods built from `historico` events in date order. From the 64 distinct event texts seen in the cache on 2026-11-01:
  - `Entrada - …` opens a period (for example "Posse de Eleito Titular", "Reassunção", "Posse de Suplente").
  - `Saída - …` closes it (for example "Término da Legislatura", "Renúncia", "Afastamento de Suplente", "Secretário de Estado", "Licença para Tratamento de Saúde").
  - `Alteração de partido` starts a new affiliation (precision `AT_EVENT`).
  - `Nome no início da legislatura / Partido no início da legislatura` sets the party at the start of the legislature.
  - `DIVERSO - …` events do not open or close periods; they are stored as raw events.
  - The full mapping table (text → effect → normalized reason) is a reviewed file, `sources/normalize/camara_status_map.py`. Any text not in it is stored as `UNKNOWN` and logged; it is never guessed.
- **Câmara "Saída" for a leave:** a `Saída` whose text describes a leave (for example "Licença para Tratamento de Saúde") closes the period and creates a `Leave` until the next `Entrada`. This follows the Câmara record: the substitute takes the seat.
- **Re-runs are idempotent:** running the normalizer twice gives the same database.

### `coverage(official, window)`

- Pure function in `metrics/coverage.py` on `core` types; a selector loads the official's `ServicePeriod`s.
- Steps: clip each period to the window (open periods end at the window end or today, whichever is earlier), merge overlapping or touching periods, count days with both ends included.
- Returns `days_in_office`, `window_days`, `share` (0–1), the merged periods, and the `SourceRef`s of the periods used.
- Party switches do not affect coverage; leaves follow the house's own record (see Choice 1).

### B1 tests

- `coverage()` for:
  - a full term;
  - a mid-term entry;
  - a leave (Senado: no cut; Câmara: cut by `Saída`/`Entrada`);
  - a substitute;
  - a party switch (no effect on coverage).
- Real cases from the fixtures: Senado mandate 526 (4545, 5917, 5918) and Câmara 220593 (vacancy 2025-01-01).
- Property tests (`hypothesis`):
  - the share is always between 0 and 1;
  - covered days never exceed the window's days;
  - merging periods twice gives the same result as merging once;
  - splitting a window into two parts gives covered days that add up.
- Normalizer tests on fixtures:
  - every event text in the fixtures is mapped;
  - an unknown text becomes `UNKNOWN` and is logged;
  - running twice gives the same records.
- Rules tests (already in place) cover the new apps' import boundaries.

### B1 acceptance

1. `uv run python manage.py normalize_current` loads the Phase A cache into PostgreSQL, with no network access.
2. Every `ServicePeriod`, `Leave`, `PartyAffiliation` and `Mandate` has a `SourceRef`.
3. `coverage()` passes the five required cases, the real cases and the property tests.
4. A report lists the counts and every `UNKNOWN` value. No unmapped value is silently dropped.
5. The cause of data issue 4 (83 titular mandates) is found from the stored mandates, or written down as still unexplained.

## B2 — Activity and metrics

### Endpoints (from the official specs checked on 2026-11-01)

**Câmara** (spec 0.4.347):

| Data | Endpoint | Notes |
| --- | --- | --- |
| Bills authored | `GET /proposicoes?idDeputadoAutor={id}&siglaTipo=…&dataApresentacaoInicio=…&dataApresentacaoFim=…` | Paged; one query per deputy |
| Votes (plenary) | `GET /votacoes?idOrgao={plenário}&dataInicio=…&dataFim=…`, then `GET /votacoes/{id}/votos` | Only nominal, non-secret votes have individual votes; the date-range limit per request is to be checked |
| Plenary attendance | `GET /eventos?idOrgao={plenário}&codTipoEvento=…&dataInicio=…&dataFim=…`, then `GET /eventos/{id}/deputados` | For past events, the list is who registered presence |
| Committee memberships | `GET /deputados/{id}/orgaos?dataInicio=…&dataFim=…` | With role and dates |
| Committee attendance | `GET /orgaos/{id}/eventos`, then `GET /eventos/{id}/deputados` | Large volume (see Choice 4) |
| Speeches | `GET /deputados/{id}/discursos?idLegislatura=57` | Paged |

The plenary's `idOrgao` and the event-type codes are read from `/orgaos` and `/referencias/eventos/codTipoEvento`, not assumed.

**Senado** (spec 4.1.3.108, no deprecated services):

| Data | Endpoint | Notes |
| --- | --- | --- |
| Bills authored | `GET /dadosabertos/processo?codigoParlamentarAutor={codigo}&ano={year}` | The service requires one of several filters; `ano` per year |
| Votes | `GET /dadosabertos/votacao?dataInicio=…&dataFim=…` | Individual votes only for nominal votes; secret votes give totals only |
| Committee memberships | `GET /dadosabertos/senador/{codigo}/comissoes` | |
| Speeches | `GET /dadosabertos/senador/{codigo}/discursos?dataInicio=…&dataFim=…` | At most 1 year per request |
| Plenary and committee attendance | **No per-senator presence list found** | See data issue 10 and Choice 3 |

### Volume and time

Roughly 8,000–12,000 requests without committee attendance. At 2 per second, with the Câmara timeouts seen in Phase A, that is about 1.5–3 hours for the first fetch. Data for past dates is cached with no expiry, so later runs only fetch new data, and an interrupted run resumes where it stopped. Committee attendance for the Câmara could add several thousand more requests (Choice 4).

### Activity models (`activity` app)

- `Bill` (house, type, number, year, presentation date, `SourceRef`) and `BillAuthorship` (official, bill).
- `Vote` (house, date, session, proposal reference, nominal or not, `SourceRef`) and `IndividualVote` (official, vote, recorded option as given).
- `Session` (house, body, date, type, `SourceRef`) and `Presence` (official, session).
- `CommitteeMembership` (official, committee, role, start, end, `SourceRef`).
- `Speech` (official, date, type, `SourceRef`). Only metadata and the source link; speech text is not stored (decision 0010: no free text in the MVP).

### First metrics (`metrics/`), each computed only on days the official was in office

| Metric | Definition (draft; final wording in `docs/methodology/`) |
| --- | --- |
| Plenary attendance (Câmara) | Sessions with registered presence ÷ deliberative plenary sessions held on days in office |
| Bills authored | Number of bills of the chosen types (Choice 2) presented on days in office |
| Nominal-vote participation | Nominal votes in which a vote option was recorded ÷ nominal votes held on days in office |
| Speeches | Number of registered speeches on days in office |
| Committee memberships | Number of committees with a membership overlapping days in office |

Every metric value returns its numerator, denominator, window, coverage and the `SourceRef`s of the records counted.

### B2 acceptance

1. A fetch command for the activity data (`fetch_activity`), with the same politeness, cache and report as Phase A.
2. Activity normalized into the database with `SourceRef`s.
3. Each metric is tested with: activity outside the period in office (not counted), a substitute (only their own days), a party switch (no effect), and a real case from fixtures.
4. Methodology choices recorded as decision 0014 before use.

## Choices needed from the owner (recorded as decision 0014 once answered)

1. **Leave days.** Proposed, and earlier agreed in principle:
   - **Senado:** a short leave without an alternate counts as time in office, because the Senado keeps the period in office running.
   - **Câmara:** a `Saída` for leave ends the period, because the substitute takes the seat.
   - In both houses, leave days are shown separately next to attendance metrics.
2. **What counts as a "bill authored".**
   - **Types.** Proposal: PL, PLP, PEC and PDL in the Câmara, and the matching types in the Senado. Excluded: requests, amendments, opinions.
   - **Authorship.** Proposal: any listed author, with co-authorship counted. A first-author-only count needs one extra request per bill and could be added later.
3. **Senado attendance.** The endpoints checked give no per-senator presence list (data issue 10). Options:
   - **(a)** No attendance metric for senators in the MVP; the app shows "not available in the official data".
   - **(b)** Use nominal-vote participation for senators, clearly labeled as a different metric.
   - **(c)** Spend a short research task looking for another official Senado source.
   - **Recommendation:** (a) now, plus (c), with (b) available anyway as its own metric for both houses.
4. **Câmara committee attendance.**
   - **Include in B2:** several thousand more requests and hours more fetching.
   - **Defer to after the MVP:** committee *memberships* stay in B2.
   - **Recommendation:** defer.

## Dependencies to approve

- `hypothesis` 6.170.x (development; already listed in decision 0011).
- No new runtime dependencies. PostgreSQL runs in Docker (`docker compose up -d db`).

## Risks

- Câmara timeouts make B2's first fetch slow; it resumes from the cache.
- Câmara event texts may include values not seen yet; they are logged as `UNKNOWN`, not guessed.
- The `/votacoes` date-range limit and the plenary's `idOrgao` are checked at the start of B2, before fetching.

## Tasks and owners

| # | Task | Owner |
| --- | --- | --- |
| B1.1 | `legislators` models and migrations; services and selectors | backend engineer |
| B1.2 | Câmara status mapping table (reviewed list of the 64 texts) | data engineer, reviewed by the owner |
| B1.3 | Normalizers and `normalize_current` command with report | data engineer |
| B1.4 | `coverage()` and selector; unit, real-case and property tests | backend engineer, QA |
| B1.5 | Data issue 4 investigation; data-issues updates | data engineer |
| B1.6 | Test and security notes for B1 | QA, security engineer |
| B2.0 | Check plenary `idOrgao`, event-type codes, `/votacoes` range limit; record in the plan | data engineer |
| B2.1 | Activity clients, `fetch_activity`, fixtures for named cases | data engineer |
| B2.2 | `activity` models, normalizers | backend engineer, data engineer |
| B2.3 | Metrics and tests | backend engineer, QA |
| B2.4 | Decision 0014 and methodology drafts (pt-BR) | architect, technical writer |
| B2.5 | Test and security notes for B2; live fetch | QA, security engineer, owner approval |

## B1 outcome (2026-11-01)

| Criterion | Result |
| --- | --- |
| 1. `normalize_current` loads the cache into PostgreSQL offline | Met: Câmara 648 officials, 1,421 mandates, 1,990 periods, 7 leaves, 1,440 affiliations, 6,865 events; Senado 245 officials, 273 mandates, 231 periods, 5,174 leaves, 301 affiliations; about 1.5 s; no network |
| 2. Every period, leave, affiliation and mandate has a `SourceRef` | Met (model fields; DB test checks every stored period) |
| 3. `coverage()` passes required, real and property cases | Met: 5 required cases; real cases 4545 = 1 day, 5917 = 1,370 days, 5918 = 0, 220593 = 701 days in legislature 57 up to 2026-11-01; 4 property tests |
| 4. Report lists counts and every `UNKNOWN` | Met: Câmara 0 unknown, 0 inconsistencies, 26 renewals; Senado 1 unknown (data issue 15), 2 incomplete mandates (data issue 13) |
| 5. Cause of data issue 4 | Found (see `docs/data-issues.md`, issue 4) |

**Changes from the plan, for review:**
- The status map has four more texts than the plan's "64 texts": Mesa decisions on recount, re-total or restoration, read as exits (`RECOUNT`) or entries (`MESA_DECISION`). Without them, 9 deputies would keep a period open after losing the seat (data issue 14).
- Repeated exits while already out (leave renewals) do not change periods; they are counted in the report.
- A `Saída` date is the last day in office (data issue 12).

Tests: 196 passed (PostgreSQL test database, network blocked); coverage 94% overall, `metrics/` 94%. `pip-audit`: no known vulnerabilities (with `hypothesis` added).

**Status:** B1 approved by the owner on 2026-11-01, including the four Mesa-decision mappings. B2 started.

## B2.0 checks (2026-11-01)

Done with the downloaded specs and about 25 small live requests.

| Check | Result |
| --- | --- |
| Câmara plenary `idOrgao` | `180` (`/orgaos?sigla=PLEN`) |
| Câmara plenary deliberative sessions | event type `110` "Sessão Deliberativa" (code `204` has the same name but returned no plenary events in Oct 2026). Attendance base: plenary events of type 110 that took place |
| Câmara `/votacoes` date range | Spec: both dates must be in the same calendar year → fetch per year |
| Câmara `/proposicoes` date range | **Not in the spec:** presentation-date ranges over 3 months return HTTP 400 ("A diferença entre as datas não pode ser maior que 3 meses"; data issue 16). Using `ano=2023,2024,2025,2026` with `idDeputadoAutor` and `siglaTipo=PL,PLP,PEC,PDL` works (one request per deputy, ~3 s); presentation dates are then filtered locally |
| Câmara speeches | `/deputados/{id}/discursos?idLegislatura=57` works (paged); free-text keywords are not stored (decision 0010) |
| Senado bill types | `/processo/siglas`: current `PL`, `PLP`, `PEC`, `PDL` (older `PLS`/`PDS` ended 2018). `/processo?codigoParlamentarAutor={codigo}` returns all processes with that senator among the authors, all years; type taken from `identificacao` (e.g. "PL 123/2023") |
| Senado votes | `/votacao?dataInicio&dataFim` (≤ 1 year per request) includes individual votes for nominal votes; option codes include Sim, Não, P-NRV, NCom, AP, LS and "Presidente (art. 51 RISF)" |
| Senado vote code table | Official list at `/plenario/lista/tiposComparecimento` (redirects to `/dadosabertos/dados/ListaTiposComparecimento.json`), e.g. AP = "Atividade parlamentar", L2 = "Licença saúde" |
| Committee lists | Senado `/senador/{codigo}/comissoes` mixes committees with "Frentes Parlamentares" (CN); Câmara `/deputados/{id}/orgaos` mixes committees with other bodies. A committee count needs the official body type, not name matching |

### Adjustments for B2 (for owner review)

1. **Nominal-vote participation, both houses.**
   - **Counts as taking part:** a recorded vote option: Sim, Não, Abstenção, Obstrução.
   - **Excluded from both numerator and denominator:** the presiding officer's non-vote (Câmara "Artigo 17", Senado "Presidente (art. 51 RISF)").
   - **Justified absences** (official codes such as AP, L1–L7) are shown separately with their official description. They are not counted as taking part.
   - Every option is stored as given; any option not in the table is reported, not guessed.
2. **Committee memberships** are fetched and stored with the official body ids and names. The *committee count* metric waits until official body types are loaded (Câmara `/orgaos` types; Senado committee lists); until then it is not shown. This replaces "committee memberships" in the first-metrics list.
