# MVP status

What the MVP includes, what is left, and what is out of scope. Updated 2026-11-01.

The MVP is phases A–D of `CLAUDE_CODE_PROMPT.md`. Phase E (rankings) comes after it (decision 0020). It runs locally on a snapshot of official data (decisions 0013 and 0015). Every number links to its official record, and parts not built yet show "Ainda não disponível".

## What the MVP includes

- **Data:** the official Câmara and Senado open-data APIs, legislature 57 (2023-02-01 to the snapshot of 2026-11-01).
  - 648 deputies and 245 senators.
  - 393 plenary sessions with 185,708 presence records.
  - 491,343 individual votes.
  - 30,322 bills (PL, PLP, PEC, PDL).
  - 66,592 speeches.
- **Time in office:** periods built from the official records, with substitutes, leaves and party changes. Metrics count only days in office.
- **Metrics** (pt-BR, each with its methodology page):
  - plenary attendance (Câmara);
  - bills authored;
  - nominal-vote participation, with secret and presided votes left out;
  - speeches;
  - per-365-days rates for counts.
- **Pages:**
  - officials list with period presets (legislature, last 2 years, custom) and a minimum time in office as % or days, with "Dados insuficientes" instead of hiding people;
  - official page;
  - side-by-side comparison of 2–6 officials;
  - parties with member counts and changes;
  - methodology.
- **Summaries:** a neutral pt-BR summary on each official page. Every sentence links to its sources and passes an automatic check. Template sentences are used by default; summaries written by a model are possible but off.
- **Quality:**
  - offline tests on recorded official responses: 359 backend, 18 frontend, 4 end-to-end with accessibility checks;
  - metrics coverage of 98%;
  - GitHub Actions CI;
  - secret scanning;
  - dependency audits.

## Phases

| Phase | What | State |
| --- | --- | --- |
| Stages 0–2 | Team, agents, decisions, binding rules | accepted (decisions 0001–0020; 0019 proposed) |
| A | Official API clients, raw cache, polite HTTP, recorded fixtures, drift check | signed off, tag `phase-a` |
| B1 | People, periods in office, leaves, party affiliations; `coverage(official, window)` | signed off, tag `phase-b1` |
| B2 | Activity data and the first four metrics, real snapshot loaded and checked | merged and pushed, tag `phase-b2` |
| C | Read-only API, pages, filters, comparison, parties, end-to-end tests, CI | signed off 2026-11-01, tag `phase-c` |
| D | Summaries (template on, model off) | signed off 2026-11-01, tag `phase-d` |
| E | Rankings | after the MVP (decision 0020) |

## Left for the MVP

| # | Item | State | Owner action |
| --- | --- | --- | --- |
| 1 | Final walk through the app on the real snapshot | done 2026-11-01: every page loads, no browser errors, no requests outside the machine | — |
| 2 | Walk-through display fixes, documentation update and README rewrite | approved and merged 2026-11-01 | — |
| 3 | MVP sign-off; tags `phase-c` and `phase-d` | signed off by the owner on 2026-11-01 | — |

## Left out of the MVP (listed as decision 0015 requires)

- **Rankings (Phase E)**: plan approved, built after the MVP (decision 0020).
- **Câmara committee attendance** (decision 0014, item 4). Committee memberships are loaded but not shown; there is no committee attendance in the app.
- **Senado plenary attendance**: the Senado APIs used do not publish attendance per senator (decision 0014). The app says so.
- **Deployment**: local only (decision 0013).
- **Official photos**: not shown. Decision 0012 requires local serving, which is not built; proposed decision 0019 would stop storing the photo URL.
- **Earlier legislatures**: the snapshot covers legislature 57.

## Related

- What data is held and why: `docs/data-inventory.md`.
- Work after the MVP: `docs/backlog.md`.

## Owner to-dos outside the code

- Update Node 24 to 24.15 or later (one test dependency asks for it).
- Fix the npm cache ownership: `sudo chown -R "$(id -u)":"$(id -g)" ~/.npm`.
