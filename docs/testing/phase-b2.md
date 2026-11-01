# Phase B2 — test report (activity and metrics)

- **Date:** 2026-11-01
- **Commands:** `scripts/check.sh`, `cd frontend && npm run e2e`

## Result

- Backend: 359 passed; metrics coverage 98% (minimum 90%).
- Frontend: 18 passed.
- End to end: 4 passed.

## What is covered

| Area | Tests |
| --- | --- |
| Metric rules (synthetic) | Activity outside the period in office not counted; substitute counts only own days; party switch has no effect; property tests (`test_metrics_properties.py`) |
| Metric rules (real) | `test_activity_real_cases.py`: real clients, normalizers, storage and metrics, offline on recorded responses. Deputy 220593: attendance 1 of 2 (one session after leaving office not counted), votes 1 of 2, 49 bills, 202 speeches. Senator 5917: votes 1 of 2 (justified absence shown separately, secret vote left out), 37 bills, 48 speeches. Totals match the full load |
| Vote options | Every known option, unknown options reported not guessed; Senado `Votou`; Câmara all-empty votings treated as secret, a single empty option in an open vote still reported |
| Storage | Idempotent replace; unknown officials skipped and counted; committee names longer than 300 characters kept whole |
| Bulk vs single | Bulk metrics (lists, parties) equal single-official metrics |
| Fixtures | Personal fields removed and checked for all 38 fixtures; next-page links kept for untrimmed pages so multi-page lists are read in full |

## Measured on the full snapshot (not automated)

| Call | Time |
| --- | --- |
| `/api/officials` (100 rows) | 0.3 s |
| `/api/officials/{id}` | 0.6–1.0 s |
| `/api/compare` (3 officials) | 0.9 s |
| `/api/parties?house=CAMARA` | 9 s first time per window, then 0.2 s |
| `/api/parties?house=SENADO` | 1.3 s |
