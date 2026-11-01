# Phase D — Summaries (plan)

- **Status:** approved by the owner on 2026-11-01 with the recommended choices: 1A (templates in the MVP, model summaries built but off until the owner adds a key and approves a run), decision 0018 (one banned-wording list), 3–6 sentences of at most 200 characters, and the `anthropic` dependency.
- **Decisions it follows:** 0010 (summaries), 0007 (module boundaries), 0011 (testing), 0012 (security), 0015 (snapshot).

## Goal

The official page shows a short, neutral pt-BR summary of the official's public activity in the chosen window. Every sentence shows the source links of the facts it uses, and a test fails if any sentence cannot be traced to a `SourceRef`. The page says the text was written automatically from official records and whether it is a template summary or a model summary.

## Tasks

| # | Task | Owner | Acceptance |
| --- | --- | --- | --- |
| D0 | `backend/placar/summaries/` app; boundary test: `summaries` reads `core`, `legislators`, `activity`, `metrics`; only `summaries/llm/` may import `anthropic` | architect, backend | `test_rules.py` passes with the new app |
| D1 | **Fact sheet** for an official and a window: time in office, periods and reasons, party affiliations in the window, each available metric (value, numerator, denominator, rate per 365 days), leave days. Each fact has an id, a type, structured values and its `SourceRef`s. No free text from the APIs | backend | Unit tests on the fixtures; every fact has at least one `SourceRef` |
| D2 | **Template summary**: fixed pt-BR sentences filled from the fact sheet, each with its fact ids; sentences for "not available" and "insufficient data" cases | technical writer, backend | Passes the validator for every fixture official and every window preset |
| D3 | **Validator** (plain Python): every sentence cites existing fact ids; every number and date in a sentence appears in its cited facts (after pt-BR formatting); every name appears in its cited facts; no banned term; limits on sentence count and length | backend, QA | One crafted bad draft per rule is rejected; valid drafts pass |
| D4 | `Summary` model: official, window preset, kind (template or model), sentences with fact ids, model id, prompt version, fact-sheet hash, created at, validation result; migration | backend | Migration check passes; out-of-date summaries are detected by hash |
| D5 | **Model adapter** (`summaries/llm/`): Claude API through the `anthropic` SDK, structured outputs (fixed JSON: sentences with fact ids), model from `SUMMARY_MODEL`, key only from `ANTHROPIC_API_KEY` in `.env`; one retry, then template. `generate_summaries` command for the preset windows | backend, security | Tests use a fake adapter only, never the real API; without a key the command makes template summaries only |
| D6 | API: `summary` in `/api/officials/{id}` (stored summary for preset windows, template computed on request for custom windows); OpenAPI contract updated | backend | "Every number has a source" test also walks summary sentences; contract check passes |
| D7 | Frontend: summary section on the official page, each sentence with its source links and the "texto gerado automaticamente" label with its kind | frontend | Component tests; wording test; e2e checks the label and links |
| D8 | Methodology page: how summaries are made, what the validator checks, what template and model summaries are | technical writer, owner review | Owner approves the wording |
| D9 | Test and security notes; README | QA, security, technical writer | Notes written; audits clean or explained |

## Choices for the owner

1. **MVP scope (recommended: A).**
   - **A. Templates in the MVP, model summaries ready but off.** D0–D9 are all built and tested with the fake adapter. The model is only called when you add `ANTHROPIC_API_KEY` to `.env` and approve a `generate_summaries` run. The MVP needs no key and costs nothing.
   - **B. Model summaries in the MVP.** Same code, plus one real `generate_summaries` run on the snapshot before sign-off.
2. **Model for `generate_summaries`** (only matters for B or later). Decision 0010 sets `claude-opus-5-5` as the default and lets the owner pick a cheaper one. Rough cost for one run on legislature 57 (about 750 officials × 2 preset windows = 1,500 calls, about 2,000 input and 400 output tokens each, retries not included; prices checked on 2026-11-01, recheck before running):
   - Opus 5.5 ($4 / $20 per million tokens): about $24;
   - Sonnet 5.5 ($2 / $10): about $12;
   - Haiku 5.5 ($0.10 / $0.50): under $1.
3. **One banned-wording list.** The frontend already checks `docs/wording/banned-pt-BR.txt`. Decision 0010 puts the summaries list in `summaries/wording/`. Proposal: a short decision 0018 that supersedes only that location clause, so both checks use the single file in `docs/wording/`.
4. **Length:** 3 to 6 sentences, each at most 200 characters.

## Dependencies to approve

- `anthropic` (official Claude Python SDK), exact version pinned at install time after checking its release date and advisories. Imported only by `summaries/llm/`.

## Risks

- **Model wording drifts or adds claims.** The validator rejects the draft and the template is shown; no unchecked sentence reaches a visitor.
- **Numbers formatted differently** (for example "1.370" and "1370") make valid drafts fail. The validator compares after one shared pt-BR formatter, the same one the template uses.
- **Cost.** Calls happen only in `generate_summaries`, run by the owner, never during a visitor's request.

## Outcome (2026-11-01, branch `feat/d-summaries`)

D0–D9 implemented on `feat/d-summaries`, built on top of the unmerged Phase B2/C branches.

- Tests and notes: `docs/testing/phase-d.md`, `docs/security/phase-d.md`.
- Methodology page in the app and in `docs/methodology/resumos.md`; flagged for your wording review together with C4.

**Deviations (confirmed by the owner on 2026-11-01):**

1. **Sentence count.** The validator accepts **1–6** sentences, not 3–6. Someone with no time in office in the window gets one template sentence ("não esteve no exercício do cargo"). The model prompt still asks for 3–6.
2. **Bill types.** "PL, PLP, PEC, PDL" are allowed in a sentence only when it cites the bills fact. Found while testing: "PL" is also a party name, and a global allowance would have let a wrong party pass.

**Not done:**

- No real model run. It needs your key and approval (choice 1A).

