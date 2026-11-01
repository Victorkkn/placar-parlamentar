# Phase E — Rankings (plan)

- **Status:** proposed (2026-11-01), waiting for the owner's approval. Nothing in this plan is implemented.
- **Decisions it follows:** 0007, 0009, 0014, 0015, and the Phase C window and threshold rules.

## Goal

One ranking page per metric, starting with **plenary attendance** (Câmara) and **bills authored** (Câmara and Senado). No composite score. Each ranking shows, above the table: the window, the threshold, the metric definition with a link to its methodology page, and the snapshot date. Every value links to its official records. Ties are shown as ties. Officials below the threshold are listed as unranked, never hidden.

## Tasks

| # | Task | Owner | Acceptance |
| --- | --- | --- | --- |
| E0 | Ranking function in `metrics/` (functional core): input is a list of (official, metric result, sufficient); output is ranked rows and unranked rows. Standard competition ranking ("1, 2, 2, 4"); rows in a tie ordered by name, with the order rule stated | backend | Property tests: ranks never skip without a tie; equal values get equal ranks; unranked rows never get a rank |
| E1 | API `GET /api/rankings?metric=&house=&start=&end=&min_days=\|min_share=&page=`; same validation as Phase C; metric must be available for the house; uses the bulk metrics | backend | "Every number has a source" test; invalid input gives 4xx; contract updated |
| E2 | Page `/classificacao/:metric`: header with window, threshold, definition and methodology link; table with position, name, party, UF, value with sources, days in office; "Empate" marker; separate "Sem classificação — dados insuficientes" list with each person's coverage | frontend | Component tests; wording test; e2e with axe |
| E3 | Methodology text for rankings (ties, threshold, unranked) | technical writer, owner review | Owner approves the wording |
| E4 | Test and security notes; README; MVP final check | QA, security, technical writer | Notes written; `scripts/check.sh` and e2e pass |

## Choices for the owner

1. **Value used for bills authored (recommended: A).**
   - **A. Bills per 365 days in office.** Fair to people with partial terms; the raw count is shown next to it.
   - **B. Raw count.** Simpler, but favors people who held the seat longer.
2. **Houses (recommended: separate).** Câmara and Senado are ranked separately, because their procedures and sizes differ and Senado attendance is not published. A combined bills ranking can be added later.
3. **Order (recommended: highest first, with a button to reverse).** The page never colors rows, adds medals or uses words like "melhores" or "piores".
4. **pt-BR name of the page.** "Classificação por métrica" (recommended) or "Ranking".
5. **Minimum for ratio metrics.** Attendance uses the same threshold as the rest of the app (default 50% of the window). No extra minimum on the number of sessions is proposed.

## Risks

- **Rankings can be read as verdicts.** Mitigated by the definition and methodology link above every table, neutral headings, ties shown, and unranked people listed.
- **Small differences look large.** The table shows the numerator and denominator next to every share.
