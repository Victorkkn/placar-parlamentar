# Phase D — security review (summaries)

- **Date:** 2026-11-01
- **Reviewer:** main Claude Code session (security engineer role)

| Check | How | Result |
| --- | --- | --- |
| API key | Read only from `ANTHROPIC_API_KEY` in the environment (`.env`), only in `summaries/llm/`; not stored in Django settings, never logged or printed; no key in tests, fixtures or CI | OK |
| Provider SDK isolation | Boundary test: only `summaries/llm/` may import `anthropic`; the SDK is imported only when a key is set | OK |
| Data sent to the provider | Only the fact sheet: ids, types and formatted values from official records. No URLs, no free text from the APIs, no visitor data | OK (tested) |
| Prompt injection | No free text from the APIs reaches the prompt; the prompt marks facts as data; every draft is checked by the validator before storage and again when shown | OK |
| Paid calls | Only in `generate_summaries`, which needs a key **and** `--yes`; never during a visitor's request; up-to-date summaries are skipped | OK (tested) |
| Error details | Stored problems keep only the exception type or validator message, not provider messages | OK |
| New dependency | `anthropic==2.3.0` (released 2026-10-23), pinned exactly, lockfile committed. It adds `httpx2`, `jiter`, `opentelemetry-api`, `sniffio`, `truststore` and others (`uv.lock`) | `pip-audit`: no known vulnerabilities |
| Frontend | Summary text rendered as plain text (no `dangerouslySetInnerHTML`); links only from `SourceRef` URLs | OK |

## Notes for the owner

- The SDK major version 2 is 11 days old. If a real `generate_summaries` run shows problems, pinning the latest 1.x is a fallback (needs your approval).
- No real model run has been made. To make one: add `ANTHROPIC_API_KEY` to `.env`, run `uv run python manage.py generate_summaries` to see the planned calls, then add `--yes`.
