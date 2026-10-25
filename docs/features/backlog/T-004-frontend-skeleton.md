# T-004: Frontend skeleton and quality gates

- **Status:** Ready
- **Milestone:** M0
- **Depends on:** T-002
- **Requirements:** NFR-3, NFR-8
- **Related ADRs:** ADR-0005, ADR-0008

## Goal
A strict-TypeScript React app in `frontend/` that calls the backend health endpoint through a generated, typed API client, with lint, test, and e2e gates in place.

## Scope
### In
- Vite + React + TS (pnpm). `tsconfig` has `strict`, `noUncheckedIndexedAccess`, and `noImplicitOverride`.
- Deps: `@tanstack/react-query`, `openapi-fetch`, and `react-router` (routes: `/`, `/caches/:gc`, `/routes`, `/routes/:id`, `/settings`, `/import`, as placeholders).
- Dev deps: `@biomejs/biome`, `vitest`, `@vitest/coverage-v8`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, `msw`, `openapi-typescript`, and `@playwright/test`.
- The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.
- `mise run api:gen`: export the OpenAPI JSON from the backend app (without starting a server, through a small Python script) and generate `src/api/schema.d.ts`. Commit the generated file. `check` fails if it is out of date (regenerate and `git diff --exit-code`).
- `src/api/client.ts`: an `openapi-fetch` client plus a QueryClient provider.
- An app shell layout (header with nav, main area) that shows the backend health status.
- Biome config (formatter + linter, recommended rules). Vitest coverage threshold of 80% lines on `src/` (excluding `src/api/schema.d.ts` and `main.tsx`).
- A Playwright config with a smoke test: the app loads and shows "Backend: ok". It runs against `mise run dev`.
- mise tasks: `test:frontend`, `test:e2e`, frontend parts of `lint`, `fmt`, and `check` (`biome ci`, `tsc --noEmit`, `vitest run --coverage`). `dev` also starts Vite.
- pre-commit: biome hook.

### Out
- Map (T-011).

## Acceptance criteria
- [ ] AC1: `mise run dev` serves the UI at http://localhost:5173, and the UI shows the backend health.
- [ ] AC2: `mise run api:gen` produces `schema.d.ts`. The health call is fully typed (no `any`).
- [ ] AC3: `mise run check` includes biome, tsc, vitest with the coverage gate, and an API schema drift check, and it passes.
- [ ] AC4: A component test with MSW covers the healthy, degraded, and network-error states of the health indicator.
- [ ] AC5: `mise run test:e2e` passes the smoke test.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC4 | component | `src/features/health/HealthIndicator.test.tsx` |
| AC5 | e2e | `e2e/smoke.spec.ts` |
| AC2, AC3 | CI | `mise run check` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] README is updated (frontend dev URL)
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
