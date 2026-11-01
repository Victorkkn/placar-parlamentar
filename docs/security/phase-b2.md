# Phase B2 — security review (activity)

- **Date:** 2026-11-01
- **Reviewer:** main Claude Code session (security engineer role)

| Check | How | Result |
| --- | --- | --- |
| Polite use of official APIs | ≤ 2 requests/s, retries with backoff, `Retry-After` honored; 9,235 Câmara requests over 3 h 50 min; failed items retried once more and only the missing 105 requests sent | OK |
| Untrusted text | Bill summaries (`ementa`) and body names stored as text and only rendered escaped; speech text is not stored | OK |
| Personal data | Activity records hold ids, dates, options and official names; fixture recording removed personal fields (office email, gender) from the 21 new fixtures, and the rules test checks all fixtures | OK |
| Process cache | Party metrics cached in memory per house, window and snapshot; holds only official data, nothing about visitors | OK |
| Dependencies | No new dependency in B2 | `pip-audit`: no known vulnerabilities |
