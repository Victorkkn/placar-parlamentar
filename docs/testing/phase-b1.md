# Phase B1 — test report

- **Date:** 2026-11-01
- **Command:** `cd backend && uv run pytest` (PostgreSQL 18.6 test database in Docker; network blocked except `127.0.0.1`)

## Result

- 196 passed, 0 skipped.
- Coverage of `placar/`: 94%; `metrics/`: 94% (decision 0011 minimum: 90%).

## What is covered

| Area | Tests |
| --- | --- |
| `coverage()` required cases | `test_metrics_coverage.py`: full term, mid-term entry, leave that ends the period (Câmara), leave without interruption (Senado), substitute, party switch, merging at 2023-09-04, open periods, no periods, sources |
| `coverage()` properties | share in [0, 1]; merge is idempotent; splitting a window adds up; order does not matter (hypothesis) |
| Câmara status map | every ENTRY/EXIT text; composite texts; unlisted `Entrada`/`Saída` → UNKNOWN |
| Câmara normalizer | real fixtures 220593 (resignation) and 220714 (party change); synthetic leave renewals and return, recount exit, unknown text, open period with alternate status, same-day party correction |
| Senado normalizer | real fixtures for mandate 526: periods and reasons, participation and titular, leaves and affiliations kept separately; unknown end codes |
| Database | idempotent replace; every period has a `SourceRef`; real-case coverage via selector (4545 = 1, 5917 = 1,370, 5918 = 0, 220593 = 701 days); period date constraint |
| Command | `normalize_current` on a cache built from fixtures (offline), twice; clear error without cache |
| Rules | import boundaries now include `legislators` and `metrics` |

Synthetic inputs are labeled in each test module.
