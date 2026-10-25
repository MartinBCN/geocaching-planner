# T-004: Frontend skeleton and quality gates

- **Status:** Complete
- **Milestone:** M0
- **Depends on:** T-002, T-003, T-023
- **Requirements:** NFR-3, NFR-8
- **Related ADRs:** ADR-0005, ADR-0008, ADR-0011
- **Reviews:** [Council review 1](../../reviews/features/T-004-frontend-skeleton-review-1.md)

## Goal
A strict-TypeScript React app in `frontend/` that calls the backend health endpoint through a generated, typed API client, with lint, test, and e2e gates in place.

## Context
ADR-0002 requires loopback-only local services. ADR-0005 requires the generated OpenAPI client and ADR-0008 requires the frontend quality gates. T-003 and T-023 provide the database and BRouter services used by `mise run dev`.

## Scope
### In
- Vite + React + TS (pnpm). `tsconfig` has `strict`, `noUncheckedIndexedAccess`, and `noImplicitOverride`.
- Deps: `@tanstack/react-query`, `openapi-fetch`, and React Router (ADR-0011; routes `/`, `/caches/:gc`, `/routes`, `/routes/:id`, `/settings`, `/import`, plus a not-found route).
- Dev deps: `@biomejs/biome`, `vitest`, `@vitest/coverage-v8`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, `msw`, `openapi-typescript`, and `@playwright/test`.
- Vite binds to `127.0.0.1` with `strictPort: true` and proxies `/api` to a configurable `VITE_API_TARGET` defaulting to `http://127.0.0.1:8000`.
- `mise run api:gen`: `backend/scripts/export_openapi.py` calls `create_app().openapi()` without starting lifespan or I/O; generate `src/api/schema.d.ts`. Commit the generated file. Biome excludes that generated file. The drift check is path-limited and fails with `API schema out of date: run mise run api:gen`.
- `src/api/client.ts`: an `openapi-fetch` client plus a QueryClient provider.
- An app shell layout (header with nav, main area) that shows the backend health status.
- Biome config (formatter + linter, recommended rules), excluding generated `src/api/schema.d.ts`. Vitest coverage threshold is 80% lines on `src/`, excluding only the generated API schema.
- Playwright starts `mise run dev` using `webServer`, waits for `http://127.0.0.1:5173`, reuses an existing server, and times out after 120 seconds. Setup installs Chromium. `test:e2e` is a separate CI job, not part of `check`.
- mise tasks: `test:frontend`, `test:e2e`, `lint:frontend`, `fmt:frontend`, `typecheck:frontend`, `check:frontend`; aggregates include backend tasks. `dev` also starts Vite.
- pre-commit: biome hook.

### Out
- Map (T-011).

## Acceptance criteria
- [ ] AC1: Given the backend and database are running, when `mise run dev` starts, then Vite serves the app at `http://127.0.0.1:5173` and does not listen on a non-loopback interface; the page shows backend health.
- [ ] AC2: Given the OpenAPI schema, when `mise run api:gen` runs, then it produces the committed schema and the health call has the exact generated `HealthResponse` type; a type-level test rejects an unknown API path.
- [ ] AC3: `mise run check` includes biome, tsc, vitest with the coverage gate, and an API schema drift check, and it passes.
- [ ] AC4: Given health is pending, 200 with `status:"ok"`, 200 with another status, 5xx problem+json, or a fetch failure, when the indicator renders, then it shows respectively “Checking backend…”, “Backend: ok”, “Backend: degraded”, “Backend: degraded — {problem title/failing component}”, or “Backend not reachable — is `mise run dev` running?”; status is text with `role="status"`.
- [ ] AC5: Given an API route changes without schema regeneration, when the path-limited drift check runs, then it fails with the actionable regeneration message and does not fail due to unrelated changes.
- [ ] AC6: Given each placeholder URL is rendered in a MemoryRouter, when navigation occurs, then the shell nav and page title are visible; an unknown URL shows “Page not found” and a link to the map.
- [ ] AC7: Given Vite or the e2e server is started, when the configured port is occupied, then strict-port behavior fails instead of silently switching ports; Playwright uses Chromium and the documented webServer readiness settings.
- [ ] AC8: Given the frontend checks, when `mise run check:frontend` runs, then Biome, tsc, Vitest, and the 80% coverage gate pass.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1 | e2e | `e2e/smoke.spec.ts::backend_health_is_visible` |
| AC2 | type test | `src/api/client.test-d.ts` |
| AC3, AC5, AC8 | frontend checks | `mise run check:frontend` and schema drift test |
| AC4 | component | `src/features/health/HealthIndicator.test.tsx` |
| AC6 | component | `src/app/routes.test.tsx` |
| AC7 | e2e/configuration | `e2e/smoke.spec.ts`, Playwright config test |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Implementation notes
- Main navigation order is Map (`/`), Import, Routes, Settings. The main region fills the remaining viewport height without page scrolling; each placeholder has a title.
- Type-level tests use `expectTypeOf` and `@ts-expect-error`; the client base URL is absolute using `window.location.origin`. Vitest sets a jsdom URL and MSW handlers match `*/api/v1/health`.
- API export script is `backend/scripts/export_openapi.py`; ruff and strict mypy apply. The exported JSON is not committed.
- `VITE_API_TARGET` is documented in `.env.example`; it defaults to `http://127.0.0.1:8000` and can be aligned with the configured backend port.
- Poll health or refetch on window focus so the status does not remain stale. The health indicator uses text, not color alone, and navigation links have visible keyboard focus.

## Completion notes
_…_
