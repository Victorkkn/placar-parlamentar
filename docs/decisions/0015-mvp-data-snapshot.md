# 0015 — MVP runs on a snapshot of official data

- **Status:** accepted (2026-11-01)
- **Date:** 2026-11-01
- **Stage:** 3

## Context

The owner wants a smaller MVP that does not depend on every official API working: some data can be "mocked" and completed later. The accepted rules say every number links to its official source record (non-negotiable rule 3) and synthetic data is never shown in the app (decision 0011). The raw cache already holds real official data for legislature 57 (Phase A, plus the Phase B2 download). The owner chose the "real snapshot" option on 2026-11-01.

## Decision

1. The MVP works from a **snapshot**: the official responses already in the raw cache, normalized into the database. The app never calls the official APIs while serving pages.
2. The snapshot date is shown in the interface ("Dados oficiais coletados em DD/MM/AAAA"), and every number keeps its official source link.
3. Data or features not built yet show **"Ainda não disponível"** with a short reason. No made-up or sample numbers are ever shown.
4. Refreshing the snapshot is a manual step (`fetch_current`, `fetch_activity`, normalization), run by or with the owner's approval.
5. The MVP scope may leave out data sources that are slow or incomplete; each one left out is listed in the README and the phase plan.

## Alternatives considered

- **Real snapshot plus clearly labeled sample data** for parts not built yet. Faster screens, but needs exceptions to rule 3 and decision 0011, and sample numbers can be mistaken for real ones.
- **Mocked data first, real data later.** Fastest to show, but every screen would have to be re-checked when real data arrives, and it breaks the source-link rule during the MVP.

## Consequences

- Rule 3 and decision 0011 stay unchanged.
- The MVP can be demonstrated offline, as long as the database has been loaded.
- Phase C–E plans state which metrics are available and which show "Ainda não disponível".
