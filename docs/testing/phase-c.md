# Phase C — test report (C1–C5)

- **Date:** 2026-11-01
- **Branch:** `chore/ci-and-tests` (contains B2, C1, C2–C3 and C5)
- **Commands:** `scripts/check.sh` (backend and frontend), `cd frontend && npm run e2e`

## Result (last full run on 2026-11-01)

- Backend: 279 passed (`uv run pytest`, PostgreSQL in Docker, network blocked except `127.0.0.1`). Coverage of `metrics/`: 98% (minimum 90%, now enforced in CI and `check.sh`).
- Frontend: 18 passed (`npm test`); lint, type check, contract check and build passed.
- End to end: 4 passed (`npm run e2e`, Chromium).
- The CI `e2e` job runs on `main` and pull requests; its first GitHub run (2026-11-01, run 41357174180) passed.

## What is covered

| Area | Tests |
| --- | --- |
| API values and sources | `test_api.py`: a generic walk over every response fails when a data number has no `sources` list (rule 3); detail values, compare, parties |
| API defaults | default window (legislature 57, 1,370 days) and default threshold (50% of the window); officials below the threshold are listed and flagged, never dropped; officials never in office are counted |
| API input | 11 invalid inputs (dates out of range, both threshold kinds, bad house or state, paging) give 4xx without a traceback; only `GET` is allowed; unknown id is 404; no data loaded is 503 |
| API "not available" | a house whose activity is not loaded gives `available: false, reason: not_loaded_yet`, never a zero (decision 0015) |
| Contract | `docs/api/openapi.json` must match the code (backend test) and the frontend types must match the file (`npm run check:api`) |
| Metrics properties | `test_metrics_properties.py` (hypothesis): attended ≤ held, shares in [0, 1], days out of office never count, vote categories add up |
| Bulk vs single | the bulk metrics used by lists and parties equal the one-official metrics for every official in the fixtures |
| Pages | `pages.test.tsx` (MSW, synthetic data): list, official, compare, parties; every number has a source link; "Dados insuficientes" and "Ainda não disponível" states |
| Wording | `wording.test.ts`: the pt-BR text file contains no term from `docs/wording/banned-pt-BR.txt` |
| Lint rules | tests prove the bans on `dangerouslySetInnerHTML` and visitor storage fire |
| End to end | `e2e/app.spec.ts`: real Django + Vite on the fixture snapshot (`placar_e2e` database only); source links, "Ainda não disponível", window above the comparison, party change label, **no request leaves `127.0.0.1`**, **no serious or critical axe violations** |

## Data used

- Backend API tests: real officials from the recorded fixtures plus labeled synthetic activity (decision 0011).
- Frontend unit tests: synthetic data in `src/test/data.ts`, never shown in the app.
- End to end: only the recorded fixtures, loaded by `load_fixture_snapshot`, which refuses any database whose name does not end in `_e2e`.

## Not covered yet

- Pages on the full real snapshot (all deputies and senators): checked by hand at the final MVP check.
- Performance of lists and parties on the full snapshot: measured after B2 data is loaded.
