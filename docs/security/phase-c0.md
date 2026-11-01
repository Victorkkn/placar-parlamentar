# Phase C0 — security review (frontend setup)

- **Date:** 2026-11-01
- **Reviewer:** main Claude Code session (security engineer role)

| Check | How | Result |
| --- | --- | --- |
| Exact versions, no forced installs | `.npmrc`: `save-exact=true`, `strict-peer-deps=true`; `package-lock.json` committed | OK; no peer conflicts |
| Production dependency audit | `npm audit --omit=dev --audit-level=moderate` | 0 vulnerabilities |
| Development dependency audit | `npm audit` | 12 "moderate" entries from **one** advisory: `minimatch` < 11.0.1, GHSA-g3hv-75wg-m249 (denial of service through crafted glob patterns). Pulled in only by dev tools (`eslint`, `typescript-eslint`, `openapi-typescript`), which only process our own config patterns. Not in the built app. npm's suggested "fix" downgrades these tools by several majors. **Accepted risk**; recheck when the tools update |
| `dangerouslySetInnerHTML` banned | ESLint `no-restricted-syntax`; a test proves the rule fires | OK |
| No visitor storage | ESLint bans `localStorage` and `sessionStorage`; test proves it | OK |
| No third-party requests | Placeholder app loads no external fonts, scripts or CDNs | OK (checked again in C3/C5) |
| CI | `frontend` job: `npm ci`, lint, type check, tests, build, production audit; actions pinned to SHAs | OK |

## Notes for the owner

- ESLint 9 is end-of-life. Because `eslint-plugin-react` only supports ESLint ≤ 9, it was dropped. The React-specific ban is done with ESLint's built-in `no-restricted-syntax` rule, which keeps the approved ESLint 10.14.0.
- Local Node is 24.12.0. One test dependency (`w3c-xmlserializer`, via `jsdom`) declares Node ≥ 24.15. Tests pass, but updating Node 24 to the latest 24.x LTS is recommended. CI uses the latest 24.x.
- The user-level npm cache (`~/.npm`) contains files owned by `root`, which made `npm install` fail with EACCES. The session used a separate cache and did not change those files. To fix it: `sudo chown -R "$(id -u)":"$(id -g)" ~/.npm`.
