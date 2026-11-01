# 0014 — Methodology choices for the first metrics

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 3 (Phase B plan, choices 1–4)

## Context

The Phase B plan needs four methodology choices before metrics can be built. They come from what the official data offers (decision 0008, data issues 6 and 10) and from the request volume seen in Phase A (data issue 1). The project owner approved the plan's recommendations on 2026-11-01.

## Decision

1. **Leave days.**
   - **Senado:** time in office follows the Senado's `Exercicio` records. A leave that does not interrupt an `Exercicio` (for example a short leave without an alternate) counts as time in office.
   - **Câmara:** time in office follows the `historico` events. A `Saída` for leave ends the period, because the substitute takes the seat; the next `Entrada` starts a new one.
   - In both houses, leave days within a window are shown separately next to attendance metrics.
2. **Bills authored.**
   - Counted types: Câmara `PL`, `PLP`, `PEC`, `PDL`, and the matching Senado types. The Senado list is fixed in the Phase B2 check (B2.0) from `/processo/siglas` and recorded in the plan. Requests, amendments and opinions are not counted.
   - Any listed author counts, including co-authors. A first-author-only count may be added later as a separate metric.
3. **Senado attendance.**
   - No attendance metric for senators in the MVP. The app says the data is not available in the official sources (data issue 10).
   - A short research task looks for another official Senado source; a new decision is needed to use one.
   - Nominal-vote participation is its own metric, for both houses, and is never labeled as attendance.
4. **Câmara committee attendance** is deferred until after the MVP. Committee memberships are included in Phase B2.

## Alternatives considered

- **Leaves always cut time in office.** It would contradict the Senado's own record, where short leaves do not interrupt the period and no one else holds the seat.
- **All proposal types as "bills".** Would mix requests and amendments with bills, which inflates counts and makes them hard to compare.
- **Nominal-vote participation as Senado "attendance".** Easy, but it measures something different and the label would mislead.
- **Include Câmara committee attendance now.** Thousands more requests and hours of fetching for the MVP.

## Consequences

- Metric definitions and their pt-BR methodology pages must state these rules.
- Attendance leaderboards cover the Câmara only in the MVP.
- Changing any of these rules needs a new decision.
