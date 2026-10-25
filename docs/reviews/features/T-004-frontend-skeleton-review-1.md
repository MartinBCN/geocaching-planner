# Council review: T-004-frontend-skeleton (review 1)

- **Target:** `docs/features/backlog/T-004-frontend-skeleton.md` (Ticket, status at review time: Ready)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 7 Major · 9 Minor · 2 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve with changes · Quality & Delivery: Approve with changes

## Context provided
- README.md
- AGENTS.md
- docs/specification.md
- docs/adr/0001-record-architecture-decisions.md
- docs/adr/0002-local-single-user-deployment.md
- docs/adr/0003-gpx-first-pluggable-cache-source.md
- docs/adr/0004-brouter-routing.md
- docs/adr/0005-frontend-react-maplibre.md
- docs/adr/0006-postgis.md
- docs/adr/0007-tooling-uv-mise-monorepo.md
- docs/adr/0008-quality-gates.md
- docs/adr/0009-ticket-workflow.md
- docs/adr/0010-council-review.md
- docs/features/backlog/T-002-backend-skeleton.md
- docs/features/TEMPLATE.md
- docs/features/README.md

**Anomalies:** none

## Top actions
1. Define the health indicator states against the real contract: give each of loading, ok, degraded, and unreachable its trigger (HTTP status and payload), its exact visible text, and a next step for the user. Rewrite AC4 as Given/When/Then for each state. Either add "degraded" now with explicit semantics or defer it to T-003/T-015. Also settle whether T-003 is a dependency. (#1, #7)
2. Record the `react-router` choice and the UI URL scheme in an ADR, or amend ADR-0005, and list that ADR under Related ADRs. Until then, keep routing out of scope or block the ticket. (#2)
3. Pin the Vite dev server to loopback (`server.host: '127.0.0.1'`, `strictPort: true`) and verify it, as ADR-0002 requires. (#3, #18)
4. Make the generated-schema pipeline deterministic: Biome ignores `src/api/schema.d.ts`, the drift check is limited to that file and fails with a clear message, and an AC covers it. Add a type-level test that proves AC2 ("no `any`"). (#4, #5)
5. Specify the Playwright lifecycle (`webServer`, readiness, browser install, whether e2e is part of `check`). Map every AC and scope item to a test, and restore the missing template sections and DoD wording. (#6, #14, #15)

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | ARC-3, PRD-1, QDE-1 | AC4: "covers the healthy, degraded, and network-error states of the health indicator"; T-002 AC1: "`{"status":"ok","version":<pkg version>}`" | The T-002 health contract has no "degraded" value, so the generated types cannot express it and the implementer will invent the trigger and the shape. Only "Backend: ok" has defined text. The loading state, the degraded and error wording, the user's next step, and handling of RFC 9457 problem+json responses are all missing. Later screens will copy this first UI-state pattern. | Add a state table and rewrite AC4 as Given/When/Then: **Loading** → "Checking backend…"; **OK** (200, `status:"ok"`) → "Backend: ok"; **Degraded** (200 with any other `status`, or 5xx problem+json; show `title` or failing component) → "Backend: degraded"; **Unreachable** (fetch failure) → "Backend not reachable — is `mise run dev` running?". Alternatively, drop "degraded" until T-003/T-015 extend the schema (ARC-3). |
| 2 | Major | ARC-1 | Scope/In: "`openapi-fetch`, and `react-router` (routes: `/`, `/caches/:gc`, `/routes`, `/routes/:id`, `/settings`, `/import`" | ADR-0005 does not list a router. ADR-0001 treats "a new dependency or framework" as significant. The ticket chooses a routing framework and fixes the URL scheme without recording the decision, and T-011 to T-019 will build on both. | Add a short ADR, or amend or supersede ADR-0005, that records `react-router` and the alternatives considered, and link it under Related ADRs. Until then, set the ticket to Blocked or limit it to the shell without routing. |
| 3 | Major | ARC-2 | Scope/In: "The Vite dev server proxies `/api` to `http://127.0.0.1:8000`." AC1: "serves the UI at http://localhost:5173" | ADR-0002 requires binding to `127.0.0.1`, with automated checks. The Vite server also proxies the unauthenticated API. If it binds to `0.0.0.0`, the API is exposed on the LAN, which bypasses NFR-7. The ticket does not specify the bind host. | Add to Scope: "`vite.config.ts` sets `server.host: '127.0.0.1'` and `strictPort: true`". Add an AC or check that the server does not listen on a non-loopback interface. Use `http://127.0.0.1:5173` in AC1 and README. |
| 4 | Major | QDE-2, ARC-5 | Scope: "Commit the generated file. `check` fails if it is out of date (regenerate and `git diff --exit-code`)" + "Biome config (formatter + linter, recommended rules)" | `biome ci` will lint and format the generated `schema.d.ts`, which causes false failures or a drift check that keeps flipping between pass and fail. A `git diff --exit-code` without a path fails on unrelated local edits, and regenerating overwrites the working tree. No AC covers the drift check. | `biome.json` excludes `src/api/schema.d.ts`. The drift check is limited to `git diff --exit-code -- frontend/src/api/schema.d.ts` (or compares against a temp file) and fails with "API schema out of date: run mise run api:gen". Add an AC for a backend route change that was not regenerated. |
| 5 | Major | QDE-3 | AC2: "The health call is fully typed (no `any`)" / Test plan: "AC2, AC3 \| CI \| `mise run check`" | `tsc` and Biome `noExplicitAny` do not detect an inferred `any` (for example from a misconfigured `paths` generic), so nothing verifies AC2. | Add a type-level test (`src/api/client.test-d.ts`) that uses `expectTypeOf(...).toEqualTypeOf<components["schemas"]["HealthResponse"]>()` and a `// @ts-expect-error` on an unknown path. Enable `vitest --typecheck` and map AC2 to that test. |
| 6 | Major | QDE-4 | Scope: "A Playwright config with a smoke test … It runs against `mise run dev`." | The ticket does not say who starts and stops the stack, how readiness is detected, what the timeouts are, how Chromium is installed, or whether `test:e2e` is part of `check`. ADR-0008 says `check` "runs the same checks as CI", and CI has an e2e job. | Specify `webServer` (`command: 'mise run dev'`, `url`, `reuseExistingServer: true`, `timeout: 120_000`, Chromium only), have `mise run setup` install Chromium, and state that `test:e2e` is not part of `check` (it runs as a CI job in T-005). Rewrite AC5 as Given/When/Then. |
| 7 | Major | QDE-5 | Header: "**Depends on:** T-002" vs T-002: "DB and BRouter checks are added in T-003" | T-003 changes both the health payload and what `mise run dev` starts (Compose/Docker). Because T-003 is not a dependency, T-004 may be built against either health shape, which affects AC4, the e2e test, and the committed `schema.d.ts`. | Either add T-003 to `Depends on` and describe the health schema after T-003, or state explicitly that the ticket is built against the T-002 schema and that `status != "ok"` means degraded once T-003 lands. Update the index in `docs/features/README.md` if the dependency changes. |
| 8 | Minor | ARC-4, QDE-7 | Scope/In: "coverage threshold of 80% lines on `src/` (excluding `src/api/schema.d.ts` and `main.tsx`)" | ADR-0008 allows only the generated API client as an exclusion. Excluding `main.tsx` too goes beyond that, and ADR-0008 says that lowering a gate needs a new ADR. | Either cover `main.tsx`, or add a one-line justification ("entry bootstrap with no logic") and confirm that it stays within ADR-0008's intent. |
| 9 | Minor | ARC-6, QDE-8 | Scope/In: "export the OpenAPI JSON from the backend app (without starting a server, through a small Python script)" | The ticket does not say where the script lives, which quality gates apply to it, whether its output is committed, or whether `create_app()` needs runtime settings. | Specify `backend/scripts/export_openapi.py` (run with `uv run`, ruff and mypy strict apply). It writes `create_app().openapi()` without running the lifespan or any I/O. The JSON is not committed. |
| 10 | Minor | ARC-7 | Scope/In: "proxies `/api` to `http://127.0.0.1:8000`" | A hard-coded proxy target breaks silently when the user changes the backend port through the `GCP_` settings (NFR-4). | Read the target from an env var (for example `VITE_API_TARGET` or `GCP_PORT`), default to `127.0.0.1:8000`, and document it in `.env.example`. |
| 11 | Minor | PRD-2 | Scope/In: "An app shell layout (header with nav, main area)" | The nav labels and order, and the sizing of the main area, are undefined. T-011 (the map-first desktop view) needs a main area that fills the viewport, and without that it would have to rework the layout. | Nav order: Map (`/`), Import, Routes, Settings. The main area fills the remaining viewport height with no page scroll. |
| 12 | Minor | PRD-3 | Scope/In: "routes: `/`, `/caches/:gc`, `/routes`, `/routes/:id`, `/settings`, `/import`, as placeholders" | Placeholder content is undefined, and there is no unknown-route page, so a stale URL shows a blank page with no way back. | Each placeholder shows its page title. Add a catch-all "Page not found" route that links back to the map. |
| 13 | Minor | PRD-4 | AC1: "the UI shows the backend health" | Accessibility is not covered: the status could rely on color alone, changes are not announced, and keyboard navigation is not addressed. | Add to AC4: the status is shown as text, the indicator uses `role="status"`, and nav links can be reached with Tab and show a visible focus. |
| 14 | Minor | QDE-6 | Test plan: rows only for "AC4", "AC5", "AC2, AC3" | AC1 is not mapped to any test. The placeholder routes, nav shell, `/api` proxy, mise tasks, and Biome pre-commit hook have no AC. | Map AC1 to `e2e/smoke.spec.ts`. Add AC6, which renders each route in a `MemoryRouter` and expects the nav and a placeholder heading, tested in `src/app/routes.test.tsx`. |
| 15 | Minor | QDE-9 | Template: missing "**Reviews:**", "## Context", "## Implementation notes". DoD: "All ACs are covered" | The ticket drops template sections, and its DoD drops "by automated tests". It also has no AGENTS.md command-table check, which T-002 includes. | Restore the missing sections. Change the DoD to "All ACs are covered by automated tests". Add a check of the AGENTS.md command table for `test:frontend`, `test:e2e`, and `api:gen`. |
| 16 | Minor | QDE-10 | Scope: "`src/api/client.ts`: an `openapi-fetch` client" | A relative `baseUrl` fails in jsdom/Node fetch under MSW. This is a known gotcha that will cost the implementer time. | Add an implementation note: `baseUrl = new URL('/api/v1', window.location.origin).href`, set the Vitest `environmentOptions.jsdom.url`, and have MSW handlers match `*/api/v1/health`. |
| 17 | Nit | PRD-5 | Scope/In: "shows the backend health status" | The ticket does not say whether the indicator refreshes, so it can show a stale "ok" after the backend stops. | Say whether the indicator polls (`refetchInterval`) or refetches on window focus. |
| 18 | Nit | QDE-11 | AC1: "serves the UI at http://localhost:5173" | If port 5173 is busy, Vite silently switches ports, and AC1 and the e2e URL drift apart. | Add `server.strictPort: true` (this overlaps with the recommendation in #3). |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Severity of the generated-schema Biome/drift-check issue (#4) | QDE-2: Major, because the drift check will keep flipping between pass and fail and block `check` | ARC-5: Minor, a configuration detail with low risk |
| How to resolve the "degraded" health state (#1) | ARC-3: define it against the current contract (200 with a non-ok status, or 5xx problem+json), **or drop it** until T-003/T-015 extend the schema | PRD-1: keep it and show the failing component with an actionable message. QDE-1: keep it, defined as `status != "ok"` or 503 problem+json, with exact text |
| Routing in this ticket (#2) | ARC-1: `react-router` and the URL scheme are an unrecorded architectural decision; block the ticket or remove routing until there is an ADR | PRD (strength): the placeholder routes that match the spec flow are a strength, because later tickets fill pages rather than change navigation |

## Open questions for the author
- Do the OpenAPI paths include the `/api/v1` prefix? This decides whether the `openapi-fetch` `baseUrl` is `/` or `/api/v1`. (ARC)
- How will the SPA be served outside Vite dev (a static build mounted by FastAPI, or Vite preview), and who handles the history fallback for deep links? (ARC)
- Spec §9.2 says e2e "Runs against the compose stack", but the ticket says `mise run dev`. Which one is intended, including for the T-005 CI e2e job? (ARC, related to #6/#7)
- Will `/` hold both the map and the cache list (MAP-4 shared state), or will the list get its own `/caches` route? (PRD)
- Should the shell show the app version from the health endpoint? (PRD)
- Will T-003 be complete before T-004 starts? If so, which health payload and "degraded" semantics should T-004 build against? (QDE)
- Should `mise run check` include the Playwright smoke test? (QDE)

## Strengths
- The API contract runs end to end: OpenAPI is generated into a committed `schema.d.ts`, the `openapi-fetch` client is typed, and `check` detects drift (ADR-0005, spec §8).
- The strict TypeScript options (`strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`), the 80% coverage threshold, and `biome ci` are concrete settings that can be checked against spec §9.1 and ADR-0008.
- The feature-folder layout and the single typed client with QueryClient follow AGENTS.md's rule on server state.
- Health is visible in the UI from day one, and the placeholder routes match the spec's main flow.
- Scope is tight: the map is explicitly deferred to T-011. Dependencies and test files are listed by name.

## Process notes
- All three custom agent types (`council-architect`, `council-product-designer`, `council-quality-delivery`) were available and launched in parallel. No fallback was used.
- All three reviews followed the output contract. No follow-up prompts were needed.
- The ticket is already marked `Ready`, before this council review.

---

## Appendix A: Software Architect (raw)
## Software Architect review: T-004-frontend-skeleton.md

**Member verdict:** Approve with changes
**Rationale:** The ticket follows ADR-0005, ADR-0008 and spec §9 closely, but it adds a routing framework without an ADR, does not say which host the Vite server binds to, and asks for a "degraded" health state that the backend contract does not have yet.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Scope/In: "`openapi-fetch`, and `react-router` (routes: `/`, `/caches/:gc`, `/routes`, `/routes/:id`, `/settings`, `/import`" | ADR-0005 lists every frontend library choice but does not include a router. ADR-0001 says "Significant means: a new dependency or framework". The ticket picks a routing framework (instead of options like TanStack Router or no router) and fixes the UI URL scheme. Later tickets (T-011 to T-019) will build on both. This is an architectural decision made silently inside a ticket. | Add a short ADR, or amend or supersede ADR-0005, recording `react-router` and the alternatives considered. Then add that ADR to "Related ADRs". Until then, set the ticket to Blocked, or remove routing from scope and keep only the shell. |
| ARC-2 | Major | Scope/In: "The Vite dev server proxies `/api` to `http://127.0.0.1:8000`." AC1: "serves the UI at http://localhost:5173" | ADR-0002 requires everything to stay local: "bound to `127.0.0.1`… Automated checks must verify this boundary". The Vite server serves the UI and also proxies the API, which has no authentication. If it binds to `0.0.0.0` (for example with `host: true`), the API is exposed on the LAN and the backend's NFR-7 binding no longer protects it. The ticket does not say which host Vite binds to. | Add to Scope: "`vite.config.ts` sets `server.host: '127.0.0.1'` and `strictPort: true`." Add an AC or check that the dev server does not listen on a non-loopback interface. Use `http://127.0.0.1:5173` in AC1 and README so the loopback host is explicit. |
| ARC-3 | Major | AC4: "covers the healthy, degraded, and network-error states of the health indicator" vs T-002 AC1: "`{"status":"ok","version":<pkg version>}`" | T-004 depends only on T-002. In T-002 the health schema has no degraded value, and the DB and BRouter status come later in T-003 and T-015. The OpenAPI-generated types (AC2, "no `any`") therefore cannot express "degraded". The implementer would invent a client-side shape, and that shape will drift from the real contract when T-003 or T-015 extend `/health`. The ticket also does not say how the indicator handles RFC 9457 problem+json error responses (NFR-5), which are separate from network errors. | Define the states against the current contract: healthy = 200 with `status:"ok"`; degraded = 200 with any other `status`, or a 5xx problem+json response (show its `title`); network error = fetch failure. Alternatively, drop "degraded" here and add it in T-003 or T-015 when the schema has it. |
| ARC-4 | Minor | Scope/In: "coverage threshold of 80% lines on `src/` (excluding `src/api/schema.d.ts` and `main.tsx`)" | ADR-0008 allows one exclusion: "≥ 80% line coverage on `frontend/src/`, excluding the generated API client". Also excluding `main.tsx` goes beyond that, and ADR-0008 says that lowering gates needs a new ADR. The impact is tiny, but it sets a precedent. | Either cover `main.tsx` (keep it trivial and include it), or state in the ticket that a bootstrap file with no logic falls under ADR-0008's intent, and record that in the completion notes. |
| ARC-5 | Minor | Scope/In: "Commit the generated file. `check` fails if it is out of date (regenerate and `git diff --exit-code`)." | `biome ci` runs on all of `src/`, so it will lint and format-check the generated `schema.d.ts`. That causes false failures, or pushes people to add `biome-ignore` to generated code. Also, `git diff --exit-code` without a path argument fails on any unrelated uncommitted change when run locally. | Exclude `src/api/schema.d.ts` in `biome.json`. Limit the drift check to `git diff --exit-code -- frontend/src/api/schema.d.ts` (and the exported JSON, if that is committed). |
| ARC-6 | Minor | Scope/In: "export the OpenAPI JSON from the backend app (without starting a server, through a small Python script)" | The ticket does not say where the script lives. If it lives in `frontend/`, the frontend depends on Python internals. If it lives in the package, it adds tooling to `geocaching_planner`. The ticket also does not say whether `create_app()` may need runtime settings (DB URL after T-003). | Specify `backend/scripts/export_openapi.py` (run with `uv run`). It calls `create_app().openapi()`, does not trigger the lifespan, and needs no I/O or env beyond the defaults. |
| ARC-7 | Minor | Scope/In: "proxies `/api` to `http://127.0.0.1:8000`" | The backend host and port come from `GCP_`-prefixed settings (NFR-4, T-002 AC5). If the proxy target is hard-coded, it breaks silently when the user changes the backend port. | Read the target from an env var (for example `GCP_PORT` or `VITE_API_TARGET`), keep `127.0.0.1:8000` as the default, and document it in `.env.example`. |

### Strengths
- The API contract runs end to end: OpenAPI is generated into a committed `schema.d.ts`, the client uses typed `openapi-fetch`, and drift is checked inside `check`. This matches ADR-0005 and spec §8.
- The TypeScript strictness (`strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`) and the gate set match spec §9.1 and ADR-0008. Adding `noImplicitOverride` makes it stricter, not weaker.
- The feature-folder layout (`src/features/health/`) and the single typed client with a QueryClient follow AGENTS.md: "server state only through TanStack Query and the generated API client".

### Open questions for the author
- Do the OpenAPI paths include the `/api/v1` prefix (for example `/api/v1/health`)? This decides whether the `openapi-fetch` `baseUrl` is `/` or `/api/v1`, and every later feature copies that choice.
- How will the SPA be served outside Vite dev (a static build mounted by FastAPI, or Vite preview)? Deep links like `/routes/:id` need a history fallback there. Does this need a ticket or ADR now?
- Spec §9.2 says e2e "Runs against the compose stack", but this ticket says "against `mise run dev`" (reload servers). Is that the intended target for the T-005 CI `e2e` job too?

### Out of my lane
- QDE: the ticket has no Context, Implementation notes, or Reviews sections (see TEMPLATE.md), and its status is Ready before council review.
- QDE: AC1 has no matching row in the test plan, and the README DoD item is not tied to any check.
- QDE: AC4's three states depend on how ARC-3 is resolved, so check that the MSW handlers match the final definitions.
- PRD: should the placeholder routes show meaningful empty states or nav labels for the bicycle geocacher, or only stubs?

## Appendix B: Product Designer (raw)
## Product Designer review: T-004-frontend-skeleton.md

**Member verdict:** Approve with changes
**Rationale:** The ticket sets up the shell that every later screen builds on, but it does not define what the user sees in each health state, and it leaves the shell layout and navigation unspecified, so later tickets would copy undefined patterns.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Major | AC4: "covers the healthy, degraded, and network-error states of the health indicator" | This is the app's first UI-state pattern, and T-011, T-008 and T-017 will copy it. Only three state names are given, and only "ok" has visible text ("Backend: ok"). The ticket has no loading state, no wording for degraded or network error, and no next step for the user. Spec §8 says health covers "DB and BRouter status", and ADR-0004 needs "an actionable error", but "degraded" is never explained. A cyclist whose BRouter is down would see a vague status and not know what to do. | Add a state table to Scope: **Loading** → "Checking backend…"; **OK** → "Backend: ok"; **Degraded** → "Backend: degraded" plus the failing component, if the API reports one; **Unreachable** → "Backend not reachable — is `mise run dev` running?" Make AC4 assert this visible text for all four states. |
| PRD-2 | Minor | Scope/In: "An app shell layout (header with nav, main area)" | The nav labels and their order are not defined, and neither is how the main area is sized. The product is map-first on a desktop (≥1280 px), and T-011 needs a main area that fills the viewport below the header. Otherwise the map ticket has to redo the layout. | Specify nav items that follow the main flow: Map (`/`), Import, Routes, Settings. Also require that the main area fills the remaining viewport height with no page scroll. |
| PRD-3 | Minor | Scope/In: "routes: `/`, `/caches/:gc`, `/routes`, `/routes/:id`, `/settings`, `/import`, as placeholders" | Placeholder content is not defined, and there is no unknown-route page. A mistyped or stale URL (for example an old `/routes/:id`) shows a blank page with no way back to the map. | Each placeholder shows its page title. Add a catch-all "Page not found" route with a link back to the map. |
| PRD-4 | Minor | AC1: "the UI shows the backend health" | The ACs don't cover accessibility for the indicator or the nav. A colored dot alone would rely on color, and status changes would not be announced. | Add to AC4: status is shown as text, not color alone; the indicator uses `role="status"`; and all nav links are reachable with Tab and show a visible focus. |
| PRD-5 | Nit | Scope/In: "shows the backend health status" | It's unclear whether the indicator refreshes. If the backend stops partway through a session, the user would still see "ok" until they reload. | Say whether the indicator polls (for example with a TanStack Query `refetchInterval`) or refreshes on window focus. |

### Strengths
- Health is shown in the UI from day one, which gives the local Docker/BRouter setup a visible status.
- The placeholder routes match the spec's main flow (import, cache detail, routes, settings), so later tickets fill pages instead of changing the navigation.
- The map is explicitly out of scope ("Map (T-011)"), which keeps this ticket from growing.

### Open questions for the author
- Will `/` hold both the map and the cache list (MAP-4 shared state), or will the list get its own `/caches` route? Deciding now keeps the nav stable for T-011 and T-012.
- Should the shell also show the app version that the health endpoint returns (`"version"`)? This would help when reporting bugs.

### Out of my lane
- QDE: The T-002 health schema only returns `"status": "ok"`, so AC4's "degraded" state may not exist in the typed client yet.
- QDE: The e2e smoke test "runs against `mise run dev`", which per NFR-3 includes Compose, but Compose comes from T-003 and that ticket is not a dependency.
- ARC: Excluding `main.tsx` from coverage goes beyond ADR-0008's "excluding the generated API client" exclusion.
- QDE: The template's "Context" section and "Reviews:" line are missing.

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: T-004-frontend-skeleton.md

**Member verdict:** Approve with changes
**Rationale:** The scope is concrete and fits one PR, but several ACs lack defined outputs or verification methods, and the test plan has gaps that would make an autonomous agent guess. The biggest gaps are the "degraded" state, the "no `any`" check, the e2e server lifecycle, and how the generated schema interacts with Biome and the drift check.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | AC4: "covers the healthy, degraded, and network-error states of the health indicator" | T-002 only defines `{"status":"ok","version":...}`. It says "DB and BRouter checks are added in T-003", so nothing defines what "degraded" is on the wire. The ticket also doesn't say what the UI shows for degraded or error. Only "Backend: ok" is given. The agent will invent both the trigger and the text, and the test will just confirm whatever it invented. | Define each state with its trigger and exact text. Rewrite AC4 as: "Given MSW returns 200 `{status:"ok"}`, when the indicator renders, then it shows `Backend: ok`. Given 200 with any `status` other than `"ok"` (or a 503 problem+json), then it shows `Backend: degraded`. Given a network error (`HttpResponse.error()`), then it shows `Backend: unreachable`. While the request is pending, it shows `Backend: checking…`." |
| QDE-2 | Major | Scope: "Commit the generated file. `check` fails if it is out of date (regenerate and `git diff --exit-code`)" + "Biome config (formatter + linter, recommended rules)" | The ticket doesn't say whether Biome ignores `src/api/schema.d.ts`. If Biome formats or lints it, `biome ci` fails on generator output. If someone runs `fmt` on it, the next `api:gen` produces a diff, and the drift check flaps forever. Also, `git diff --exit-code` in `check` overwrites the working tree and fails whenever the developer has local edits. | Add: "**Must:** `biome.json` excludes `src/api/schema.d.ts`. The drift check writes to a temp file and compares it with the committed file (`diff -u`), or runs `git diff --exit-code -- frontend/src/api/schema.d.ts` only after `api:gen`, and it fails with the message `API schema out of date: run mise run api:gen`." Add an AC: "Given a backend route change without regeneration, when `mise run check` runs, then it fails with that message." |
| QDE-3 | Major | AC2: "The health call is fully typed (no `any`)" / Test plan: "AC2, AC3 \| CI \| `mise run check`" | `tsc` and Biome's `noExplicitAny` don't catch an *inferred* `any`, for example from a misconfigured `paths` generic. Nothing in `check` would detect that AC2 is broken. | Add a type-level test such as `src/api/client.test-d.ts` using Vitest `expectTypeOf(data).toEqualTypeOf<components["schemas"]["HealthResponse"]>()` plus a `// @ts-expect-error` on an unknown path. Enable `vitest --typecheck` (or include it in `tsc`), and map AC2 to that file in the test plan. |
| QDE-4 | Major | Scope: "A Playwright config with a smoke test … It runs against `mise run dev`." | The ticket doesn't say who starts and stops the stack. Is it Playwright's `webServer` or a server that is already running? It also doesn't cover readiness checks (backend and 5173), timeouts, Chromium install (`playwright install chromium` in `setup`?), or whether `test:e2e` is part of `check`. AC3 doesn't list it, but ADR-0008 says `check` "runs the same checks as CI", and CI has an `e2e` job. | Specify: "**Must:** `playwright.config.ts` uses `webServer` with `command: 'mise run dev'`, `url: 'http://localhost:5173'`, `reuseExistingServer: true`, `timeout: 120_000`, Chromium only. `mise run setup` installs the Chromium browser. `test:e2e` is **not** part of `check` (it is a CI job in T-005)." Rewrite AC5 as: "Given no running dev stack, when `mise run test:e2e` runs, then Playwright starts the stack, `e2e/smoke.spec.ts` sees `Backend: ok` within 10 s, and the stack is torn down." |
| QDE-5 | Major | Header: "**Depends on:** T-002" vs T-002: "DB and BRouter checks are added in T-003" | T-003 changes both the health payload and what `mise run dev` starts (compose/Docker, per NFR-3). The pick-order rule usually runs T-003 first, but only if it's Ready, so T-004 may be built against either health shape. AC4, the e2e smoke test, and the committed `schema.d.ts` all depend on which shape exists. | Either add `T-003` to `Depends on` and describe the post-T-003 health schema, or state explicitly: "Built against the T-002 health schema. If T-003 is complete, regenerate and treat `status != "ok"` as degraded." Also update the index in `docs/features/README.md` if the dependency changes. |
| QDE-6 | Minor | Test plan: rows only for "AC4", "AC5", "AC2, AC3" | AC1 isn't mapped to any test. The scope items (six placeholder routes, nav shell, `/api` proxy, `test:frontend`/`lint`/`fmt` tasks, biome pre-commit hook) have no AC at all, so "done" for them can't be checked. | Map AC1 to `e2e/smoke.spec.ts`. Add AC6: "Given the app, when each of `/`, `/caches/GC1`, `/routes`, `/routes/1`, `/settings`, `/import` is rendered in a `MemoryRouter`, then the header nav and a placeholder heading are shown." Test it in `src/app/routes.test.tsx` (component). |
| QDE-7 | Minor | Scope: "80% lines on `src/` (excluding `src/api/schema.d.ts` and `main.tsx`)" vs ADR-0008: "excluding the generated API client" | Excluding `main.tsx` goes beyond what ADR-0008 allows. That ADR says "Lowering a threshold … needs a new ADR", so an agent may stop here or treat it as a quiet weakening of the gate. | Either remove the `main.tsx` exclusion and test the bootstrap, or add a one-line justification ("entry bootstrap with no logic; mirrors exclusion of generated code") and confirm that it stays within ADR-0008. |
| QDE-8 | Minor | Scope: "export the OpenAPI JSON from the backend app (without starting a server, through a small Python script)" | The script's path, whether its output JSON is committed, and whether it falls under backend ruff, mypy, and coverage gates are all unspecified. | Specify: "`backend/scripts/export_openapi.py` (ruff + mypy strict apply) writes `create_app().openapi()` to stdout. The JSON is not committed. `openapi-typescript` reads it from a temp file." |
| QDE-9 | Minor | Template: missing "**Reviews:**", "## Context", "## Implementation notes". DoD: "All ACs are covered" | The ticket drops template sections, and the DoD drops "by automated tests" from the template and spec §9.4(1). It also leaves out an AGENTS.md command-table check (T-002 has one) for `test:frontend`, `test:e2e`, and `api:gen`. | Restore the missing sections, with a `Reviews:` link once this report exists. Change the DoD to "All ACs are covered by automated tests". Add "AGENTS.md command table is verified for `test:frontend`, `test:e2e`, `api:gen`". |
| QDE-10 | Minor | Scope: "`src/api/client.ts`: an `openapi-fetch` client" | There's a known gotcha: a relative `baseUrl` (`/api/v1`) fails in jsdom/Node fetch under MSW, because Node fetch needs an absolute URL. The ticket doesn't mention it, so the agent will likely lose time on it. | Add an implementation note: "`baseUrl` is `new URL('/api/v1', window.location.origin).href`. In Vitest, set `environmentOptions.jsdom.url = 'http://localhost:5173'`. MSW handlers use `*/api/v1/health`." |
| QDE-11 | Nit | AC1: "serves the UI at http://localhost:5173" | If port 5173 is taken, Vite silently moves to the next free port, and AC1 and the e2e URL go out of sync. | Add "`server.strictPort: true`" to the scope. |

### Strengths
- The dependency lists are explicit, so no runtime dependency comes as a surprise (AGENTS.md §3), and the test files are named in the test plan.
- The drift check and committed generated schema follow ADR-0005 directly.
- The quality gates (strict TS options, the 80% coverage threshold, `biome ci`) are stated as concrete, checkable settings.

### Open questions for the author
- Will T-003 be complete before T-004 starts? If so, what health payload and "degraded" semantics should T-004 build against?
- Should `mise run check` include the Playwright smoke test? ADR-0008 says it "runs the same checks as CI", but AC3 leaves it out.

### Out of my lane
- Architect: should the Vite dev server bind explicitly to `127.0.0.1`, in line with ADR-0002's localhost-only boundary?
- Product Designer: the wording and visual treatment for the health indicator's degraded and unreachable states in the header.
