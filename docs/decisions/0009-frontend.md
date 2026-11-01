# 0009 — Frontend framework, tooling and link to the backend

- **Status:** proposed
- **Date:** 2026-11-01
- **Stage:** 2 (topic 6 of 10)

## Context

The frontend is React (project prompt) in `frontend/`, self-contained and linked to the backend only through the HTTP API contract (decision 0004). The backend uses Django Ninja, which publishes an OpenAPI description (decision 0005). The interface is in pt-BR (decision 0003). Visitors must not be tracked, and no visitor data may be stored (non-negotiable rule 5).

The main screens are read-only: filters by date window and coverage threshold, official and party comparisons, leaderboards, and summaries. Each number on screen links to its official source.

Checked on 2026-11-01:

- Installed: Node 24.12 (an LTS line, supported until 2028-04) and npm 11.6. Node 26 became LTS on 2026-10-28.
- Latest versions on npm: react 19.3.1, vite 8.3.5, typescript 7.0.2, react-router 8.5.1, @tanstack/react-query 5.105.1, openapi-typescript 7.13.0, openapi-fetch 0.17.0.

## Decision

### Tooling

1. **React 19 with TypeScript**, built with **Vite**, as a single-page app.
2. **Node 24 LTS** and **npm**, with the lockfile committed. The Node version is pinned in `frontend/.nvmrc` and `package.json` `engines`.
3. **TypeScript version:** use the latest version that the chosen lint and test tools support. If a tool does not yet work with TypeScript 7, use 6.x. The exact versions are fixed (and approved as dependencies) when the frontend is set up.

### Pages and state

4. **Routing:** React Router.
5. **Filters live in the URL** (for example `?inicio=2023-02-01&fim=2026-10-31&cobertura=0.5`), so every view can be shared and reloaded. No `localStorage`, cookies or other storage of visitor choices.
6. **Server data:** TanStack Query for fetching and caching API responses in memory.

### Link to the backend

7. **The contract is a file:** the backend exports its OpenAPI description to `docs/api/openapi.json` (committed).
   - A backend test fails if the committed file is out of date.
   - The frontend generates TypeScript types from that file with `openapi-typescript` and calls the API with `openapi-fetch`. Neither side imports the other's code.
   - A frontend check fails if the generated types do not match the committed file.
8. **Development:** the Vite dev server forwards `/api` requests to Django on `127.0.0.1:8000`, so the browser sees a single origin and no CORS setup is needed. Production serving is part of the deployment decision.

### Content, style and privacy

9. **User-facing text** lives in `frontend/src/text/pt-BR.ts`, owned by the technical writer. Numbers and dates use `Intl` with `pt-BR`.
10. **Styling:** CSS Modules and a small set of our own components. No UI component library in the MVP. Charts are chosen in the Phase C plan.
11. **No third-party requests at runtime:** no analytics, no tracking pixels, no external fonts or CDNs. Fonts and assets are bundled, so visitors' browsers only talk to our own server, plus the official sites when a visitor clicks a source link.
12. **Source links:** a shared component renders every number together with its source link, so a value without a source cannot be shown by mistake. The link opens the official page with `rel="noopener noreferrer"`.
13. **Accessibility:** semantic HTML, keyboard navigation, labelled controls, enough color contrast, and tables as the base form of every comparison and leaderboard.

## Alternatives considered

- **Next.js or React Router "framework mode" (server rendering).** Better for search engines and first load, but it needs a Node server next to Django, or a static export setup. Can be added later through the deployment decision; the single-page app keeps the MVP simpler.
- **Django templates with a little JavaScript.** One toolchain, but the project prompt asks for React, and interactive comparisons are easier in React.
- **Handwritten API types or `orval`/full client generators.** Handwritten types drift from the backend. Full client generators produce a lot of code; `openapi-typescript` + `openapi-fetch` only generate types and a thin client.
- **Tailwind or a component library (MUI, Chakra).** Faster to start, but more dependencies and less control over accessibility and neutral visual design. Can be revisited.
- **Saving filters in `localStorage`.** Convenient, but stores visitor choices on the device and is not needed when the URL holds the state.

## Consequences

- The technical writer's owned text location is now set: `frontend/src/text/`.
- `docs/api/openapi.json` is a shared contract: the backend engineer generates it; the frontend engineer consumes it. A change to it must be visible in the same commit as the code that caused it.
- Dependencies to approve when the frontend is set up: react, react-dom, react-router, @tanstack/react-query, openapi-fetch, and dev tools (vite, typescript, openapi-typescript, test tools from the testing decision).
- No search-engine optimization beyond basic page titles until the deployment decision.
