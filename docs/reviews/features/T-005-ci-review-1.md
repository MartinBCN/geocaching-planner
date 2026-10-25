# Council review: T-005-ci (review 1)

- **Target:** `docs/features/backlog/T-005-ci.md` (Ticket, status at review time: Ready)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 6 Major · 7 Minor · 1 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve · Quality & Delivery: Approve with changes

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
- docs/features/backlog/T-003-compose-db-migrations.md
- docs/features/backlog/T-004-frontend-skeleton.md
- docs/features/TEMPLATE.md
- docs/features/README.md

**Anomalies:** none

## Top actions
1. Make every CI job call only mise tasks (`check:backend`, `check:frontend`, `test:e2e:ci`), creating them here if needed, so `mise run check` and CI share one definition. Add an AC that rejects raw tool commands in `ci.yml`. This also fixes the `api:gen` backend-env gap. (#1, #3)
2. Specify the CI e2e harness exactly: a `test:e2e:ci` task (db only, migrate, backend host/port/env, build + preview port, Playwright `baseURL`), and a smoke assertion that does not depend on BRouter. (#4, #7)
3. Decide whether `pre-commit` (with gitleaks) is a required check. Document the decision in the README and AC, and say whether the mypy hook is skipped in CI. (#2)
4. Restore the template DoD (spec §9.4) and add automated checks for the workflow (an actionlint hook plus a unit test that parses `ci.yml`). Keep manual runs only for AC1–AC3. Add a `workflow_dispatch` trigger and fix the Goal/Scope mismatch on triggers so those runs are possible. (#5, #6)
5. Tighten AC1–AC5: name the concrete violations and thresholds, define "version pins", split AC5, and add the missing template sections (`Reviews:`, Context, Implementation notes). (#10, #11, #14, #15)

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | ARC-1, QDE-2 | Goal: "runs the same gates as `mise run check`"; Job `backend`: "`uv sync --frozen`, ruff, ruff-format check, mypy, and pytest"; ADR-0008: "Checks can drift" | The workflow re-lists raw tool commands and its own e2e startup steps instead of calling mise tasks. This brings back the local/CI drift that ADR-0008 rejects and goes against ADR-0007 ("through `mise run <task>`"). Nothing verifies that CI and `check` stay equivalent. The drift check is also defined twice: in T-004's `check` and in this ticket's `git diff`. | Jobs call only `mise run check:backend`, `mise run check:frontend`, and `mise run test:e2e:ci`. `mise run check` depends on the split tasks; create them here if T-002/T-004 did not. New AC: "every `run:` step except checkout/cache/artifact steps starts with `mise run`; no ruff/mypy/pytest/biome/tsc/vitest/playwright appears directly in `ci.yml`." |
| 2 | Major | ARC-2, QDE-8 | Scope/In: "Job `pre-commit`: `pre-commit run --all-files` (includes gitleaks)"; Out: "required status-check names (`backend`, `frontend`, `e2e`)" | The only CI secret scan runs in a job that is not required before merge. NFR-8 requires the §9.1 gates (which include pre-commit/gitleaks) to pass before merge, and NFR-4 says "no secrets in the repo". QDE-8 adds that the mypy pre-commit hook may fail `--strict` under `--all-files` in its isolated env. | Either list `pre-commit` as a required check (README + AC), noting in the completion notes that this extends ADR-0008's job list, or state on purpose that it is advisory and why. Say whether the mypy hook is skipped in CI (`SKIP=mypy`), because `backend` already runs mypy. |
| 3 | Major | ARC-3, QDE-5 | Job `frontend`: "`pnpm install --frozen-lockfile`, … Run `mise run api:gen`"; T-004: "export the OpenAPI JSON from the backend app … through a small Python script" | `api:gen` needs a synced backend Python environment, but the frontend job installs only pnpm dependencies. The drift check will fail, or the implementer will couple the jobs in a way the ticket doesn't describe. | Add `uv sync --frozen` for the backend before `api:gen` in the frontend job, or better, make `api:gen` / `check:frontend` declare that dependency in `mise.toml` (see #1). |
| 4 | Major | QDE-1 | Job `e2e`: "start the backend and the Vite preview, and run Playwright"; T-004: "It runs against `mise run dev`." | The T-004 smoke targets `mise run dev`, which starts `db` and `brouter`. Preview defaults to `:4173` and needs a build first, while dev uses `:5173`. The backend start command, host, port, and env (`DATABASE_URL`) are not given, and neither is how Playwright's `baseURL`/`webServer` changes. Expect a guessed, fragile harness. | **Must** note: create `mise run test:e2e:ci` → `docker compose up -d --wait db` → `mise run db:migrate` → uvicorn on `127.0.0.1:8000` in the background → `pnpm build && pnpm preview --port 5173 --strictPort` → `playwright test`. `playwright.config.ts` reads `E2E_BASE_URL` (default `http://localhost:5173`). The CI `e2e` job calls only this task. The smoke text "Backend: ok" must not depend on BRouter. |
| 5 | Major | QDE-3 (also noted out-of-lane by ARC, PRD) | DoD: "All ACs are verified"; Test plan: "Verified with throwaway PRs or branches"; spec §9.4: "covered by automated tests" | The DoD drops spec §9.4 items 1–3. Every AC is verified by hand, which goes against AGENTS.md: "Every acceptance criterion needs at least one automated test." No reason is given, even though several ACs can be automated. | Restore the template DoD lines. Add an `actionlint` pre-commit hook and `backend/tests/unit/test_ci_workflow.py`, which parses `ci.yml` and asserts the job ids, triggers, concurrency, that no setup-python/setup-node/version inputs exist, and that the README check names equal the job ids. Keep manual runs only for AC1–AC3, with an explicit "manual: needs a live GitHub runner" note. |
| 6 | Major | QDE-4 | Scope: "triggered on `pull_request` and on `push` to `main`"; Test plan: "throwaway PRs or branches"; Goal: "Every push and PR" | A push to a throwaway branch triggers nothing, so the "or branches" path cannot verify AC1–AC3. The Goal ("every push") also contradicts the Scope (push to `main` only). | Add a `workflow_dispatch` trigger. Test plan: "throwaway PRs (or `workflow_dispatch` runs on a throwaway branch); link run URLs." Goal: "Every PR and every push to `main`…". |
| 7 | Minor | ARC-4, PRD-2, QDE-9 | Job `e2e`: "BRouter is skipped in CI unless tests need it; see T-015"; spec §9.2: "Runs against the compose stack" / "optional `@pytest.mark.brouter` live test" | CI drops BRouter, but no ticket owns adding BRouter (or recorded responses) back so that the spec's "create route" smoke step runs. Once `/health` reports BRouter, the smoke check could fail in CI only. The live `brouter` pytest marker is also not deselected, so it would break `backend` later. | Name the CI stack (db only) as an explicit mise task or compose profile. State the health and smoke expectations without BRouter. Name the follow-up ticket (e.g. T-015/T-017) that extends CI e2e for routing. Backend CI deselects `-m 'not brouter'` (or the marker is opt-in), documented in `check:backend`. |
| 8 | Minor | ARC-5 | Scope/In: "It uses `jdx/mise-action`"; "`concurrency` group to cancel superseded runs." | No `permissions:` scope is set and third-party actions are not pinned, which is a supply-chain risk. Cancelling superseded runs on `push` to `main` can leave a `main` commit with no completed CI result. | Set `permissions: contents: read` at the workflow level and pin third-party actions to a commit SHA. Use `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`. |
| 9 | Minor | PRD-1 | Scope/In: "Add a CI badge to the README." / Out: "Document the required status-check names … in the README" | Owner-facing branch-protection details mixed into the user-facing README make the geocacher's Quickstart path noisier. | Put the required-checks list in a `## Development / CI` section below the Quickstart. DoD: "README has the badge and a 'Development / CI' section listing the required checks." |
| 10 | Minor | QDE-6 | AC1: "A PR with a lint error fails the corresponding job." AC2: "drops coverage below the threshold fails." AC3: "A green PR finishes all jobs" | It isn't clear which linter, which threshold, which job should fail, or what "finishes" means. There is no time budget. | AC1: ruff `F401` in `backend/src` → `backend` fails; Biome `noUnusedVariables` in `frontend/src` → `frontend` fails. AC2: backend < 85% / frontend < 80% → the matching job fails at the coverage step. AC3: all of `backend`, `frontend`, `e2e`, `pre-commit` succeed, and each job sets `timeout-minutes` (≤ 20). |
| 11 | Minor | QDE-7 | AC4: "no duplicate version pins in the workflow" | "Version pins" is ambiguous: action refs and container images are pins too. | AC4: `ci.yml` contains no `actions/setup-python`, `actions/setup-node`, `astral-sh/setup-uv`, or `pnpm/action-setup` steps, and no version inputs for those tools; tools come only from `jdx/mise-action` reading `mise.toml`. Make this checkable by the test in #5. |
| 12 | Minor | QDE-10 | Scope: "Add a CI badge to the README." | The badge URL needs the GitHub `owner/repo`, which is unknown because no remote is configured. The agent will invent it. | "Derive `owner/repo` from `git remote get-url origin`; if there is no GitHub remote, stop and ask." |
| 13 | Minor | QDE-11, PRD-3 | Header: "**Related ADRs:** ADR-0008" (no `Reviews:` line); no `## Context` or `## Implementation notes` | The ticket does not follow `TEMPLATE.md`. There is no place for the binding notes from #1 and #4, and nowhere to link council reviews. | Add `- **Reviews:** –`, a Context section (ADR-0005 drift check, ADR-0008, spec §9.1/§9.2), and Implementation notes holding the task and port decisions. |
| 14 | Nit | QDE-12 | AC5: "fails when running `mise run api:gen` changes … and the README names `backend`, `frontend`, and `e2e`" | Two unrelated outcomes share one AC. | Split it: AC5 (schema drift fails `frontend`) and AC6 (README lists required checks that match the job ids). |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| `pre-commit` as a required check (#2) | ARC-2: Major. It contradicts NFR-8. Making it required strengthens ADR-0008's list and does not change it. | QDE-8: Minor (either make it required or document it as advisory). PRD: only an open question, and making it required "would mean changing ADR-0008", which is the owner's decision. |
| `api:gen` needs the backend env (#3) | ARC-3: Major (the drift check fails, or the jobs get coupled implicitly). | QDE-5: Minor (fix with one extra step). |
| BRouter absence in CI e2e (#4, #7) | QDE-1: Major. The e2e harness, including BRouter-independent smoke, is underspecified enough to cause rework. | ARC-4, PRD-2: Minor. The concern is ownership of the spec divergence and of future route coverage. |
| Template conformance (#13) | QDE-11: Minor. Binding implementation notes have nowhere to go. | PRD-3: Nit (consistency only). |
| Overall verdict | ARC, QDE: Approve with changes. | PRD: Approve (only Minor/Nit product concerns). |

## Open questions for the author
- Should `pre-commit` be a required check, or should gitleaks run inside `backend` or `frontend`? (ARC, PRD, QDE)
- Should e2e use `vite preview` (a production build) when the T-004 smoke is written against `mise run dev`? If so, which mise task builds the bundle? (ARC; see QDE-1)
- Which ticket owns adding BRouter (or a stub/recorded responses) to CI e2e once the smoke includes routing? (ARC, PRD-2)
- Can the implementing agent push branches and open PRs or `workflow_dispatch` runs on GitHub? If not, AC1–AC3 can't be verified by the agent at all. (QDE)
- Do `check:backend` and `check:frontend` already exist after T-002/T-004, or should T-005 create them? (QDE)

## Strengths
- The job names match ADR-0008 exactly (`backend`, `frontend`, `e2e`), and branch protection is correctly left as owner-managed and out of scope.
- Tool versions come only from `mise.toml` through `jdx/mise-action` (AC4), which matches ADR-0007's single source of truth and limits "works on my machine" surprises.
- The concrete OpenAPI drift check (`git diff --exit-code -- frontend/src/api/schema.d.ts`) carries out ADR-0005's contract-sync consequence.
- Frozen lockfiles, caching, and `concurrency` show good CI hygiene, and the ticket fits one PR.

## Process notes
- All three custom agent types were available. No fallback was used.
- All three reviews met the output contract. No re-prompts were needed.
- Out-of-lane notes from ARC and PRD about manual-only verification were folded into #5. ARC's note about the duplicated "council review is recommended" bullet in `docs/features/README.md` is unrelated to T-005 and is not counted as a finding.

---

## Appendix A: Software Architect (raw)
## Software Architect review: T-005-ci.md

**Member verdict:** Approve with changes
**Rationale:** The workflow fits ADR-0008's three named jobs and ADR-0007's version pinning, but it re-lists each gate as a raw command instead of calling mise tasks, which brings back the local-vs-CI drift that ADR-0008 rejected. It also leaves the `pre-commit` job and gitleaks out of the required checks, which contradicts NFR-8.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Scope/In, `backend` job: "`uv sync --frozen`, ruff, ruff-format check, mypy, and pytest (unit + integration + contract…)"; `e2e` job: "migrate, start the backend and the Vite preview, and run Playwright" | The Goal says CI runs "the same gates as `mise run check`". But each job writes out its own tool commands and its own e2e startup steps. ADR-0008 rejects "Separate local and CI check definitions" because "Checks can drift". ADR-0007 says project tasks run "through `mise run <task>`". With two definitions, a new ruff, mypy, or coverage option added locally can silently skip CI, and the reverse. The drift check is also defined twice: T-004 already makes `check` fail on drift, and this ticket adds a separate `git diff`. | Make every job call mise tasks only, e.g. `mise run check:backend`, `mise run check:frontend`, `mise run test:e2e` (or `test:e2e:ci`). If those sub-tasks don't exist yet, create them here so that `mise run check` becomes `check:backend` plus `check:frontend`. Add an AC: "The workflow invokes only `mise run …` tasks for gates; no tool command (ruff, mypy, pytest, biome, tsc, vitest, playwright) appears directly in `ci.yml`." |
| ARC-2 | Major | Scope/Out: "Document the required status-check names (`backend`, `frontend`, `e2e`)"; Scope/In: "Job `pre-commit`: `pre-commit run --all-files` (includes gitleaks)" | NFR-8 requires that "Code quality gates (section 9) pass in CI before any merge to `main`". §9.1 lists pre-commit with gitleaks as a gate. The new `pre-commit` job is not on the required-check list, so a PR could merge with a leaked secret or hygiene failure even though NFR-4 says "There are no secrets in the repo." | Either add `pre-commit` to the required checks in the README and AC5, or move gitleaks and the hygiene hooks into a required job. Adding a required check strengthens ADR-0008's list rather than changing it, but say this explicitly in the completion notes so the ADR's job list is not silently extended. |
| ARC-3 | Major | Scope/In, `frontend` job: "`pnpm install --frozen-lockfile`, … Run `mise run api:gen`" | T-004 says `api:gen` exports the OpenAPI schema "from the backend app … through a small Python script". So the frontend job also needs a synced backend Python environment, but the ticket lists only pnpm. Either the drift check fails, or the implementer quietly couples the jobs in a way the ticket doesn't describe. | State that the `frontend` job also runs `uv sync --frozen` for the backend, or that it uses the mise task's own dependencies. Better still, make `api:gen` declare its dependencies in `mise.toml` so CI and local runs behave the same. |
| ARC-4 | Minor | `e2e` job: "start compose `db` only (BRouter is skipped in CI unless tests need it; see T-015)" | Spec §9.2 says the e2e smoke "Runs against the compose stack", and T-004 says the smoke test "runs against `mise run dev`", which starts BRouter too. This ticket drops BRouter but doesn't say who owns that difference later. Once `/health` reports BRouter status (spec §8), the "Backend: ok" smoke check could fail in CI only. T-015 depends on T-005 and is not in context. | Record the CI stack (db only) as an explicit, named variant: a mise task or compose profile. Add a sentence on the health and smoke expectations without BRouter, and name the follow-up ticket that will add BRouter or a stub to CI e2e. |
| ARC-5 | Minor | Scope/In: "It uses `jdx/mise-action`"; "`concurrency` group to cancel superseded runs." | Two workflow-security and robustness gaps. (a) No `permissions:` scope is given, and third-party actions are not pinned, which is a supply-chain risk. (b) Cancelling superseded runs on `push` to `main` can leave a `main` commit with no completed CI result. | Add "`permissions: contents: read` at the workflow level; third-party actions pinned to a commit SHA". Limit `cancel-in-progress` to `pull_request` events, e.g. `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`. |

### Strengths
- Tool versions come only from `mise.toml` through `jdx/mise-action` (AC4), which matches ADR-0007's single source of truth.
- The job names match ADR-0008 exactly, and branch protection is correctly left as owner-managed and out of scope.
- The OpenAPI drift check in CI carries out ADR-0005's contract-sync consequence.

### Open questions for the author
- Should `pre-commit` be a required check, or should gitleaks run inside `backend` or `frontend`? The answer decides whether ARC-2 is fixed by documentation or by restructuring a job.
- Should the e2e job use `vite preview` (a production build) when T-004's smoke test is written against the dev server through `mise run dev`? If so, which mise task builds the bundle?
- Which ticket owns adding BRouter, or a stub, to CI e2e once the smoke flow includes routing?

### Out of my lane
- QDE: the AC1–AC3 test plan uses manual throwaway PRs rather than automated tests, which falls short of "Every acceptance criterion needs at least one automated test" (AGENTS.md §2.3).
- QDE: the ticket leaves out the template's `Reviews:`, `Context`, and `Implementation notes` sections, and its DoD drops "`mise run check` is green".
- Chair/docs: `docs/features/README.md` has the "council review is recommended" bullet twice. This is unrelated to T-005.

## Appendix B: Product Designer (raw)
## Product Designer review: T-005-ci.md

**Member verdict:** Approve
**Rationale:** This developer-facing ticket enables NFR-8 and stays within M0 scope; my only product concerns are minor ones about who the README is written for and how CI will protect the main user flow later.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Minor | Scope/In: "Add a CI badge to the README." and Out: "Document the required status-check names (`backend`, `frontend`, `e2e`) in the README" | The README is the first thing the geocacher sees. It has a short user Quickstart and "Data and licensing notes". Branch-protection instructions for the repository owner mixed into that page make the user path noisier. | Put the required-checks list in a separate `## Development / CI` section below the Quickstart. Keep the user Quickstart the first thing a user reads. Example DoD wording: "README has the badge and a 'Development / CI' section listing the required checks." |
| PRD-2 | Minor | Job `e2e`: "BRouter is skipped in CI unless tests need it; see T-015" vs spec §9.2: "Happy path: import fixture → see markers → create route → export. Runs against the compose stack." | The spec says the e2e smoke covers the user's whole main flow, and the "create route" step needs BRouter. With "unless tests need it", no ticket clearly owns adding BRouter or recorded responses to CI e2e. The route-planning part of the main flow could stay unguarded in CI without anyone noticing. | Name a ticket that owns this, e.g. "T-017 (route planning UI) extends the CI `e2e` job so that the route step of the smoke runs (BRouter service or recorded responses)." Also add a matching line to T-017's scope when that ticket is refined. |
| PRD-3 | Nit | Header: "- **Related ADRs:** ADR-0008" | The ticket has no `Reviews:` line, and it is missing the template's `Context` and `Implementation notes` sections. This is inconsistent with the template that other tickets follow. | Add `- **Reviews:** –` and link this council report there. Add short Context and Implementation notes sections, or write "–" in them. |

### Strengths
- The required check names match ADR-0008 exactly (`backend`, `frontend`, `e2e`). AC5 ties the README to the workflow job names, so the owner has one consistent list of names.
- The API schema drift check protects the frontend–backend contract. Without it, the user could see UI states that are broken in subtle ways.
- AC4 forbids duplicate version pins ("Tool versions in CI come from `mise.toml`"). CI therefore uses the same setup as the user's local `mise install`, which keeps "works on my machine" surprises low.

### Open questions for the author
- The `pre-commit` job runs gitleaks and the large-file check. Should it also be a required check? It is the closest thing to a guard against committing real Pocket Query data or secrets, which README says "Do not commit". Making it required would mean changing ADR-0008, so this is the owner's decision. I am not requesting it here.

### Out of my lane
- Architect/QDE: the spec says `/health` reports "DB and BRouter status". After T-015 adds BRouter to health, CI e2e without BRouter could show "degraded" instead of the "Backend: ok" the T-004 smoke expects. The ticket should define what the smoke expects when BRouter is absent.
- QDE: AC1–AC3 are verified through "throwaway PRs or branches" instead of automated tests. Check that this is an acceptable exception to the rule that every AC needs an automated test.
- QDE: AC5 bundles two unrelated checks (the schema drift check and the README check names). Consider splitting it.

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: T-005-ci.md

**Member verdict:** Approve with changes
**Rationale:** The workflow shape is right and the ticket fits one PR, but an agent cannot deliver it correctly on the first try: the e2e job doesn't fit the T-004 Playwright setup, CI copies commands instead of calling `mise run check` tasks, and the DoD and verification plan are weaker than spec §9.4 and can't be carried out as written.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Scope › Job `e2e`: "start the backend and the Vite preview, and run Playwright"; T-004: "It runs against `mise run dev`." | The T-004 smoke test targets `mise run dev`, which runs `docker compose up -d --wait` on `db` **and** `brouter` (T-003). In CI there are no segments, so brouter may never become healthy. The dev server is on `:5173`, but Vite preview defaults to `:4173` and needs a build first. The ticket doesn't give the backend start command, host, port, or env (`DATABASE_URL`), and doesn't say how Playwright's `baseURL`/`webServer` changes. Expect a guessed and fragile harness. | Add **must** notes: "Create `mise run test:e2e:ci`. It runs `docker compose up -d --wait db`, then `mise run db:migrate`, then starts uvicorn on `127.0.0.1:8000` in the background, then `pnpm build && pnpm preview --port 5173 --strictPort`, then `playwright test`. `playwright.config.ts` reads `E2E_BASE_URL` (default `http://localhost:5173`). The CI `e2e` job only calls this task." Also state that the smoke text "Backend: ok" must not depend on BRouter. |
| QDE-2 | Major | Goal: "runs the same gates as `mise run check`"; Job `backend`: "`uv sync --frozen`, ruff, ruff-format check, mypy, and pytest"; ADR-0008: "Checks can drift" | The workflow re-lists raw tool commands instead of calling mise tasks. This is the local/CI drift that ADR-0008 rejected. It also can't be checked: nothing proves that CI and `check` stay the same. | Require: "CI jobs call only mise tasks: `backend` runs `mise run check:backend`, `frontend` runs `mise run check:frontend`, `e2e` runs `mise run test:e2e:ci`. `mise run check` depends on `check:backend` + `check:frontend`. Create the split tasks in this ticket if T-002/T-004 didn't." Add an AC: "Given `ci.yml`, every `run:` step except checkout/cache/artifact steps starts with `mise run`." |
| QDE-3 | Major | DoD: "All ACs are verified"; Test plan: "Verified with throwaway PRs or branches"; spec §9.4: "covered by automated tests" | The DoD drops spec §9.4 items 1–3 ("covered by automated tests", "`mise run check` passes", docs). Every AC is verified only by hand, and AC4 by "Workflow inspection". AGENTS.md says "Every acceptance criterion needs at least one automated test." There's no justification for manual-only checks, even though several ACs can be automated. | Restore the template DoD lines. Add automated checks: (a) an `actionlint` pre-commit hook, and (b) `backend/tests/unit/test_ci_workflow.py` that parses `ci.yml` (with the YAML parser already used for the T-003 AC7 compose test) and asserts job ids `backend`/`frontend`/`e2e`/`pre-commit`, the triggers, `concurrency.cancel-in-progress: true`, no `actions/setup-python`/`setup-node`/`*-version:` inputs, and that the README check names equal the job ids. Keep throwaway runs only for AC1–AC3, with an explicit "manual: needs a live GitHub runner" note. |
| QDE-4 | Major | Scope: "triggered on `pull_request` and on `push` to `main`"; Test plan: "throwaway PRs or branches"; Goal: "Every push and PR" | A push to a throwaway branch triggers nothing, so the "or branches" option can't verify AC1–AC3. The Goal ("every push") also contradicts the Scope (push to `main` only). | Add a `workflow_dispatch` trigger and change the test plan to "throwaway PRs (or `workflow_dispatch` runs on a throwaway branch); link the run URLs". Change the Goal to "Every PR and every push to `main`…". |
| QDE-5 | Minor | Job `frontend`: "`pnpm install --frozen-lockfile`, biome ci, tsc, vitest"; T-004: "export the OpenAPI JSON from the backend app … through a small Python script" | `mise run api:gen` needs the backend Python environment, but the frontend job only installs pnpm dependencies. The drift check will fail on the first run. | Add "`uv sync --frozen` (backend) before `mise run api:gen`" to the frontend job, or make it part of `check:frontend` (see QDE-2). |
| QDE-6 | Minor | AC1: "A PR with a lint error fails the corresponding job." AC2: "drops coverage below the threshold fails." AC3: "A green PR finishes all jobs" | It isn't clear which linter, which threshold (85% backend or 80% frontend), which job should fail, or what "finishes" means. There's no time budget. | AC1: "Given a PR adding a ruff `F401` violation in `backend/src`, then job `backend` fails; given a Biome `noUnusedVariables` violation in `frontend/src`, then job `frontend` fails." AC2: "Given a PR that makes backend coverage < 85% (or frontend < 80%), then `backend` (or `frontend`) fails at the coverage step." AC3: "Given a PR with no defects, then `backend`, `frontend`, `e2e`, and `pre-commit` all succeed; each job sets `timeout-minutes` (≤ 20)." |
| QDE-7 | Minor | AC4: "no duplicate version pins in the workflow" | "Version pins" is ambiguous. Action refs (`@v4`) and the testcontainers image are pins too, so an agent could read this too broadly or too narrowly. | "AC4: `ci.yml` contains no `actions/setup-python`, `actions/setup-node`, `astral-sh/setup-uv`, or `pnpm/action-setup` steps, and no `python-version`/`node-version`/`version` inputs for those tools; tools come only from `jdx/mise-action` reading `mise.toml`." It can be checked by the QDE-3 test. |
| QDE-8 | Minor | Scope: "Job `pre-commit`: `pre-commit run --all-files` (includes gitleaks)"; Out: "required status-check names (`backend`, `frontend`, `e2e`)" | The only CI secret scan (gitleaks) runs in a job that isn't required before merge, so a leaked secret could still be merged. Also, the mypy pre-commit hook usually runs in an isolated env and may fail `--strict` with `--all-files`. | Either list `pre-commit` as a required check in the README, or state on purpose that it's advisory and why. Say whether the mypy hook is skipped in CI (`SKIP=mypy`), because the `backend` job already runs mypy. |
| QDE-9 | Minor | Job `backend`: "pytest (unit + integration + contract, using Docker for testcontainers)"; spec §9.2: "An optional `@pytest.mark.brouter` live test runs against the compose BRouter." | CI has no BRouter. Unless CI deselects the marker, T-015's live test will break CI later. | Add: "Backend CI deselects `-m 'not brouter'` (or the marker is opt-in through `--run-brouter`); document this in the `check:backend` task." |
| QDE-10 | Minor | Scope: "Add a CI badge to the README." | A badge URL needs the GitHub `owner/repo`, which is unknown (no git remote is configured). The agent will invent it. | "Derive `owner/repo` from `git remote get-url origin`; if there's no GitHub remote, stop and ask." |
| QDE-11 | Minor | Header/sections: "**Related ADRs:** ADR-0008" (no `Reviews:` line); no `## Context` or `## Implementation notes` | This doesn't follow `TEMPLATE.md`. There's no place for the **must** notes from QDE-1 and QDE-2, and nowhere to link a council review. | Add `- **Reviews:** –`, a Context section (links to ADR-0005 drift check, ADR-0008, spec §9.1/§9.2), and Implementation notes holding the binding task and port decisions. |
| QDE-12 | Nit | AC5: "fails when running `mise run api:gen` changes … and the README names `backend`, `frontend`, and `e2e`" | Two unrelated outcomes share one AC, so passing or failing it is unclear. | Split into AC5 (schema drift fails `frontend`) and AC6 (README lists the required checks, and they match the job ids). |

### Strengths
- The jobs are clearly split, and the job names match ADR-0008 (`backend`, `frontend`, `e2e`). Branch protection is correctly put out of scope as owner-managed.
- The drift check is concrete and objective: `git diff --exit-code -- frontend/src/api/schema.d.ts`.
- `jdx/mise-action`, frozen lockfiles, caching, and `concurrency` show good CI hygiene. The ticket fits one PR.

### Open questions for the author
- Can the implementing agent push branches and open PRs or `workflow_dispatch` runs on GitHub? If not, AC1–AC3 can't be verified by the agent at all.
- Should `pre-commit` (with gitleaks) be a required check?
- Do the per-side tasks `check:backend` and `check:frontend` already exist after T-002/T-004, or should T-005 create them?

### Out of my lane
- Architect: running e2e against `db` only goes against spec §9.2 ("Runs against the compose stack") and §9.1 ("e2e job (compose)"). Decide whether to amend the spec or start the full stack.
- Architect: once T-015 adds BRouter status, the health endpoint will report `degraded` in CI if BRouter is missing. That affects the smoke assertion "Backend: ok".
