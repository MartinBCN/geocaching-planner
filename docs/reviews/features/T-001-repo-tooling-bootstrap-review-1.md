# Council review: T-001-repo-tooling-bootstrap (review 1)

- **Target:** `docs/features/backlog/T-001-repo-tooling-bootstrap.md` (Ticket, status at review time: Ready)
- **Date:** 2026-10-25
- **Council verdict:** **Revise & resubmit**
- **Findings:** 1 Blocker · 3 Major · 8 Minor · 2 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve · Quality & Delivery: Revise & resubmit

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
- docs/features/TEMPLATE.md
- docs/features/README.md

Dependency tickets: none (`Depends on: –`).

**Anomalies:** none

## Top actions
1. Replace the manual-only test plan with an automated bootstrap check (e.g. `scripts/verify-bootstrap.sh` run by a `mise run test:bootstrap` task that `check` calls). Map AC1–AC5 to named checks, and restore the template DoD word for word ("covered by automated tests", "`mise run check` is green", no unlinked TODOs). (#1 QDE-1)
2. Make `check` (and `lint`/`fmt`) real from day one: `check` runs `pre-commit run --all-files` plus the bootstrap check. Remaining stubs must not be called from `check`. (#2 ARC-2, QDE-2)
3. Add `.gitignore` to scope and add an AC: `.env`, `.venv/`, `infra/brouter/segments/*` (except `.gitkeep`), `node_modules/`, and PQ data are ignored, and `.env.example` and the `.gitkeep` files are not. Verify with `git check-ignore`. (#3 ARC-1, PRD-4)
4. Rewrite AC1 as an observable, non-interactive Given/When/Then that includes `mise trust` and handles a missing `.env` when mise loads `_.file = ".env"`. Add `mise trust` to the README quickstart. (#4 QDE-3)
5. Pin pre-commit and hook `rev:` tags, state the version lines (Python 3.14.x, Node Active LTS major), and align spec §9.1's "node LTS" wording with ADR-0007. (#6, #7, #5)

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Blocker | QDE-1 | Test plan: "manual + CI (T-005)"; DoD: "All ACs are verified" | The ticket contradicts spec §9.2 (every AC maps to an automated test), spec §9.4, and AGENTS.md §6. Verification depends on T-005, which is a later ticket that itself depends on T-001. The DoD drops "covered by automated tests", "`mise run check` is green", and the TODO rule. | Restore the template DoD. Add `scripts/verify-bootstrap.sh` via `mise run test:bootstrap`, called from `check`, covering: task names in `mise tasks --json`, stubs exit 0 with "not yet implemented", `.git/hooks/pre-commit` exists after `setup`, `git ls-files pyproject.toml` is empty, `git check-ignore .env` succeeds. Map AC1–AC5 to these checks. Keep the network-dependent clean-clone install as a justified, recorded manual step until T-005. |
| 2 | Major | ARC-2, QDE-2 | Scope In: "each must exit 0 with a clear 'not yet implemented' message: `setup`, `dev`, `check`, …" | A stub `check` is always green but checks nothing. This weakens ADR-0008 ("`mise run check` runs the same checks as CI locally") and the per-ticket DoD, and later tickets inherit a gate that does no work. | `check`, `lint`, and `fmt` are not stubs. `lint`/`check` run `pre-commit run --all-files` (+ `test:bootstrap`), and `fmt` runs the fixing hooks. Stubs must not be called from `check`. Add "`mise run check` exits 0" to the ACs. |
| 3 | Major | ARC-1, PRD-4 | Context: "The git repo is already initialized, and `.gitignore` exists." / Scope In: "`infra/brouter/{segments,profiles}` with `.gitkeep` files" | `.gitignore` is not in scope, yet ADR-0004 requires segments to be git-ignored, AGENTS §5 bans segment files, data, and secrets in git, and AC5 relies on `.env` being ignored. This ticket creates both `segments/` and `.env`. | Scope In: update `.gitignore` for `.env`, `.venv/`, `infra/brouter/segments/*` (with `!.gitkeep`), `node_modules/`, and PQ data patterns outside fixtures. AC: `git check-ignore` matches `infra/brouter/segments/E5_N45.rd5` and `.env`, and matches neither `.env.example` nor `segments/.gitkeep`. |
| 4 | Major | QDE-3 | AC1: "On a clean clone, `mise install && mise run setup` succeeds"; Scope: "`[env]`: `_.file = \".env\"`" | On a clean clone, mise requires `mise trust` before using a config that has `[env]` and tasks, which blocks non-interactive runs. `.env` is loaded before `setup` creates it. "Succeeds" is not observable. | Given a fresh clone with no `.env`, when `mise trust && mise install && mise run setup` runs non-interactively, then all commands exit 0, `.git/hooks/pre-commit` exists, and `.env` equals `.env.example`. Confirm a missing `.env` is tolerated (or make it optional). Add `mise trust` to the README. |
| 5 | Minor | ARC-3 | Scope In: "Do not use floating aliases such as `lts` or `latest`" vs spec §9.1: "`mise.toml` pins python 3.14, node LTS, uv" | Spec and ADR-0007 conflict, and AGENTS §1 tells agents to stop on a conflict. Spec §9.1 also omits pnpm. | Add a scope item to update spec §9.1 to "pins concrete versions of Python 3.14.x, Node, uv, and pnpm (ADR-0007)". |
| 6 | Minor | ARC-4, QDE-4 | Scope In: "`setup` installs pre-commit hooks (`uvx pre-commit install`)" … "`check-merge-conflict`, and `gitleaks`" | The pre-commit version floats and hook `rev:` values are unpinned, so results differ across machines (against ADR-0007). The gitleaks hook may silently need Go. | Pin pre-commit (mise `[tools]` or `uvx pre-commit@<ver>`) and invoke it the same way in `setup`, `check`, and AC3. Require tagged `rev:` values for `pre-commit/pre-commit-hooks` and `gitleaks/gitleaks`. State how gitleaks is built or provided. |
| 7 | Minor | QDE-5 | Scope: "pin concrete versions for Python, Node, uv, and pnpm" | The version lines are not stated, so an agent could pin the wrong major. | Python: latest 3.14.x. Node: latest patch of the current Active LTS major. uv/pnpm: latest stable. Record them in the completion notes. |
| 8 | Minor | QDE-6 | Scope In: "`.env.example` (empty sections with comments for now) and `.editorconfig`." | No AC covers `.env.example`, `.editorconfig`, the directory skeleton, stub behavior, or `.env` being preserved when `setup` re-runs. The content is unspecified. | Add ACs: re-running `setup` leaves `.env` unchanged; the skeleton dirs/`.gitkeep` files are tracked; `.editorconfig` settings are listed. List the `.env.example` section headers. |
| 9 | Minor | QDE-7 | AC4: "There is no `pyproject.toml` or `.venv` left at the repo root." | `.venv` is git-ignored, so the AC cannot be verified from the repo. | "`git ls-files pyproject.toml uv.lock` returns nothing, and after `mise run setup` no root `.venv` exists." |
| 10 | Minor | PRD-3, QDE-8 | DoD: "README quickstart matches the real commands" vs README: "mise run setup          # deps, pre-commit hooks, .env from .env.example" | After T-001, `setup` installs no deps and `dev`/`brouter:segments` are stubs. It is unclear whether the README should describe the state after T-001 or after M0. | State the expected edit: the command names exist as tasks, the "after M0 is complete" heading stays, `mise trust` is added. Otherwise state "no README change expected". |
| 11 | Minor | PRD-1, QDE-10 | Header: "**Requirements:** NFR-3, NFR-4, NFR-8" | NFR-3 (`dev` brings up the stack) and NFR-8 (CI) are only partly delivered here, so they could be traced as done too early. | "NFR-3 (entry point only; T-003/T-004), NFR-4 (`.env.example` scaffold), NFR-8 (local hooks only; CI in T-005)". |
| 12 | Minor | PRD-2 | Scope: "each must exit 0 with a clear "not yet implemented" message" | Stub messages don't tell the user when or where the feature will arrive. (QDE-2 makes the same recommendation.) | Name the implementing ticket in each stub message, e.g. `brouter:segments: not yet implemented (T-003)`. |
| 13 | Nit | ARC-5, QDE-9 | Header: "- **Related ADRs:** ADR-0007, ADR-0008" (no `Reviews:` line); no "Implementation notes" section | The ticket drifts from `docs/features/TEMPLATE.md`, which ADR-0009 requires. The ACs are not in Given/When/Then form. | Add `- **Reviews:** –` and an `## Implementation notes` section (hook repos, trust/`.env` gotchas). Rewrite the ACs as Given/When/Then. |
| 14 | Nit | PRD-5 | Scope: "copies `.env.example` to `.env` if it is missing" | When `setup` re-runs, it doesn't say whether the existing `.env` was kept. | Print "`.env` exists, left unchanged" or "created `.env` from `.env.example`". |

No severity was raised by the Chair. Merged findings take the highest member severity (#3, #11).

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Missing `.gitignore` scope (#3) | ARC-1: Major, because this is the first point where segments and `.env` could be committed, and the existing `.gitignore` should not be the safeguard. | PRD-4: Minor, framed as untracked noise or an accidental commit risk for the user. |
| Partial NFR traceability (#11) | PRD-1: Minor, because someone tracing requirements could mark NFR-3/NFR-8 done too early. | QDE-10: Nit. |
| Manual-only test plan (#1) | QDE-1: Blocker, because it contradicts spec §9.2/§9.4 and AGENTS.md §6. | ARC and PRD raised it only as "out of my lane" notes for QDE and did not rate it. |
| Stub `check` task (#2) | ARC-2 / QDE-2: Major, a false-green quality gate. | PRD: noted it only as out of lane, and listed "All task names are defined from day one" as a strength. |
| Overall verdict | PRD: Approve (foundation ticket; findings are small gaps). | QDE: Revise & resubmit (the ticket cannot be objectively verified as done). ARC: Approve with changes. |

## Open questions for the author
- With `[env] _.file = ".env"`, does the pinned mise version error or warn when `.env` is missing? Should the env file be optional, or should `min_version` be pinned? (ARC open question; relates to #4 QDE-3)
- `.env` is injected into every mise task and also read by pydantic-settings. Which one is the single intended config source for the backend? (ARC)
- Which host OS is targeted? Must the mise tasks and hooks work on Windows, or is macOS/Linux/WSL assumed? (PRD)
- Will the owner accept a recorded manual clean-clone run for AC1 until T-005, as long as everything that can run offline is automated through `check`? (QDE; relates to #1)
- Should pre-commit and gitleaks be pinned through mise `[tools]` (extending ADR-0007's tool list), or only through hook `rev:` values? (QDE; relates to #6)

## Strengths
- The ticket pins concrete versions, bans floating aliases, and requires the chosen versions to be recorded, matching ADR-0007.
- Removing the root `pyproject.toml`/`.venv` and creating the §6.1 layout sets the monorepo boundaries before any code exists.
- `gitleaks` enforces NFR-4 from the first commit. `setup` copies `.env` only when it is missing, and AC5 checks that `.env` is ignored, which protects local config and secrets.
- There is one onboarding path (`mise install && mise run setup`), and all task names are discoverable from day one.
- The scope is tight and fits one PR, with exact task names, hook IDs, and the 500 kB threshold. `Depends on: –` is correct, and T-001 is first in pick order.

## Process notes
- All three custom agent types (`council-architect`, `council-product-designer`, `council-quality-delivery`) were available and launched in parallel. No fallback was used.
- All three reviews followed the output contract. No re-prompts.
- QDE's out-of-lane note: `docs/features/README.md` contains the "council review is recommended" bullet twice. This is not about the target and is recorded here only.

---

## Appendix A: Software Architect (raw)
## Software Architect review: T-001-repo-tooling-bootstrap.md

**Member verdict:** Approve with changes
**Rationale:** The ticket follows ADR-0007 closely, but it leaves `.gitignore` out of scope even though the BRouter segments and `.env` depend on it, and its stub `check` task always passes, which undermines the ADR-0008 gate that every later ticket depends on.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Context: "The git repo is already initialized, and `.gitignore` exists." / Scope In: "Create the directories … `infra/brouter/{segments,profiles}` with `.gitkeep` files" | No `.gitignore` changes are in scope. Yet ADR-0004 requires `.rd5` segment files to be "git-ignored", AGENTS §5 says "No real geocaching.com data, secrets, or BRouter segment files in git", and AC5 needs `.env` to be ignored. This ticket creates `segments/` and `.env`, so it is the first point where these could be committed. Whatever the existing `.gitignore` happens to contain should not be the safeguard. | Add a Scope In item: "Update `.gitignore` so that `.env`, `.venv/`, `infra/brouter/segments/*` (except `!.gitkeep`), `node_modules/`, and PQ data patterns (`*.gpx`, `*.zip` outside `backend/tests/fixtures/`) are ignored. `.env.example` stays tracked." Add an AC: "`git check-ignore infra/brouter/segments/E5_N45.rd5 .env` matches both paths; `git check-ignore .env.example` and `git check-ignore infra/brouter/segments/.gitkeep` match neither." |
| ARC-2 | Major | Scope In: "Tasks (stubs are fine … each must exit 0 with a clear 'not yet implemented' message): `setup`, `dev`, `check`, …" | ADR-0008 says "`mise run check` runs the same checks as CI locally", and spec §9.4 makes a green `check` part of the DoD for every ticket. A `check` that always exits 0 reports green without checking anything. It also sets a pattern where `test:*` stubs exit 0 and could be wired into `check` or CI (T-005) and keep passing silently. The pre-commit hygiene hooks already exist in this ticket, so `check` can be real from day one. | Change the scope to: "`check` is **not** a stub. It runs `pre-commit run --all-files` now, and T-002/T-004 extend it. Stub tasks must not be called from `check` until they are implemented." Add `mise run check` exits 0 to the ACs, and restore the template's "`mise run check` is green" line in the DoD. |
| ARC-3 | Minor | Scope In: "Do not use floating aliases such as `lts` or `latest`" vs spec §9.1: "`mise.toml` pins python 3.14, node LTS, uv" | The ticket correctly follows ADR-0007, which has higher priority. However, spec §9.1 still says "node LTS" (and does not mention pnpm). AGENTS §1 says "If the sources conflict, **stop and report the conflict**", so an implementing agent may stop here. | Add to Scope In: "Update spec §9.1 Tooling row to 'pins concrete versions of Python 3.14.x, Node, uv, and pnpm (ADR-0007)'." The README line `# python 3.14, node, uv, pnpm` is acceptable as it is. |
| ARC-4 | Minor | Scope In: "`setup` installs pre-commit hooks (`uvx pre-commit install`)" | `uvx pre-commit` resolves the latest pre-commit at run time. This floats the one tool that every commit passes through and goes against ADR-0007's goal that "The committed `mise.toml` is the version source of truth." It also needs network access on every cold cache. | Pin pre-commit in `mise.toml` `[tools]` (e.g. `"pipx:pre-commit" = "<x.y.z>"`) or use `uvx pre-commit@<x.y.z>`, and call it the same way in `setup`, `check`, and AC3. Hook `rev:`s in `.pre-commit-config.yaml` must be tags, not branches. |
| ARC-5 | Nit | Header: "- **Related ADRs:** ADR-0007, ADR-0008" (no `Reviews:` line); no "Implementation notes" section | The ticket drifts from `docs/features/TEMPLATE.md`, which ADR-0009 requires ("follows `docs/features/TEMPLATE.md`"). | Add `- **Reviews:** –` (later the link to this review) and an "Implementation notes" section, even if it is short. |

### Strengths
- The concrete-version pinning rule and the instruction to record the chosen versions match ADR-0007 exactly.
- Removing the root `pyproject.toml`/`.venv` and creating the §6.1 layout (`backend/`, `frontend/`, `infra/brouter/{segments,profiles}`) puts the monorepo boundaries in place before any code exists.
- Adding `gitleaks` now enforces NFR-4 ("no secrets in the repo") from the first commit.

### Open questions for the author
- With `[env] _.file = ".env"`, does the pinned mise version error or warn when `.env` is missing? If it errors, `mise run setup` on a clean clone (AC1) could fail before setup creates `.env`. Should the env file be optional, or should the minimum mise version (`min_version`) be pinned so the behavior is predictable?
- `.env` is injected into every mise task, and pydantic-settings will also read it (NFR-4). Which one is the single intended config source for the backend, so T-002 does not create two precedence paths?

### Out of my lane
- QDE: The test plan is "manual + CI (T-005)" for every AC, which conflicts with spec §9.4 "covered by automated tests". Should a scripted check (e.g. a shell or pytest smoke test) be added now?
- QDE: AC1 "on a clean clone" is not reproducible as written. The environment (OS, cache state, network) needs to be specified.
- PRD: The README quickstart says `setup` installs "deps", but this ticket installs none. Should the wording be aligned until T-002/T-004 land?

## Appendix B: Product Designer (raw)
## Product Designer review: T-001-repo-tooling-bootstrap.md

**Member verdict:** Approve
**Rationale:** This is a foundation ticket for developers. It sets up the README quickstart and protects the user's local `.env`, which fits M0. My findings are only small traceability gaps and gaps in what the user sees.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Minor | Header: "**Requirements:** NFR-3, NFR-4, NFR-8" vs Scope: "each must exit 0 with a clear "not yet implemented" message" | NFR-3 requires that "`mise run dev` brings up compose services, backend, and frontend". This ticket only adds a `dev` stub, and NFR-8 needs CI from T-005. Listing these IDs without a note suggests they are delivered here, so someone tracing requirements could mark them done too early. | Mark the partial ones, e.g. "NFR-3 (entry point only; delivered by T-003/T-004), NFR-4 (`.env.example` scaffold), NFR-8 (local hooks only; CI in T-005)". |
| PRD-2 | Minor | Scope: "each must exit 0 with a clear "not yet implemented" message" | Someone running `mise run brouter:segments` or `mise run dev` from the README gets exit 0, and the message doesn't tell them what to do next. The user can't tell when the feature will arrive. | Make each stub message name the ticket that will implement it, e.g. `brouter:segments: not yet implemented (T-003)`. |
| PRD-3 | Minor | DoD: "README quickstart matches the real commands" vs README: "mise run setup          # deps, pre-commit hooks, .env from .env.example" | In T-001, `setup` only installs hooks and copies `.env`. It installs no dependencies. `dev` and `brouter:segments` are also stubs. The DoD doesn't say whether the README must match the state after T-001 or after M0, so the implementer may rewrite the README too early or leave the comments inaccurate. | Change the DoD item to: "README quickstart command names exist as mise tasks; the 'after M0 is complete' heading stays; inline comments describe the final M0 behavior." |
| PRD-4 | Minor | Scope: "Create the directories … `infra/brouter/{segments,profiles}` with `.gitkeep` files" with AC5 covering only `.env` | The ticket creates the segments folder but doesn't require ignoring its contents. AGENTS.md says "No real geocaching.com data, secrets, or BRouter segment files in git". The user's downloaded segments, which can be hundreds of MB, could show up as untracked noise or get committed by accident. | Add a Scope item and an AC: "`.gitignore` ignores `infra/brouter/segments/*` except `.gitkeep`; after placing a dummy `x.rd5` there, `git status` shows nothing new." |
| PRD-5 | Nit | Scope: "copies `.env.example` to `.env` if it is missing" | Not overwriting the file protects the user's edits, which is good. But on a re-run, setup says nothing about an existing `.env`, so the user can't tell whether their settings were kept. | Have setup print "`.env` exists, left unchanged" or "created `.env` from `.env.example`". |

### Strengths
- `setup` copies `.env` only when it is missing, and AC5 makes sure `.env` is git-ignored. This protects the user's local config and secrets.
- The goal is one onboarding path, `mise install && mise run setup`. That matches the one-command experience promised in the README and keeps setup effort low for a solo user.
- All task names are defined from day one, so `mise tasks` gives a discoverable list of commands that later tickets fill in.

### Open questions for the author
- Which host OS is the target user on? GSAK users are often on Windows. Should the mise tasks and hooks also work on Windows, or is macOS/Linux (or WSL) the assumed setup? The answer changes how the stub scripts should be written and what the README should say.

### Out of my lane
- QDE: Stubbed `check` and `test*` tasks that exit 0 show a false green before T-002/T-004.
- QDE: The test plan says "manual + CI (T-005)", but AGENTS.md says "Every acceptance criterion needs at least one automated test".
- QDE: The template's `- **Reviews:**` line is missing from the ticket header.
- ARC: Spec §9.1 says "node LTS", which conflicts with ADR-0007 and this ticket ("Do not use floating aliases such as `lts`"). The spec should be aligned.

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: T-001-repo-tooling-bootstrap.md

**Member verdict:** Revise & resubmit
**Rationale:** The scope fits one PR and the dependencies are correct, but the test plan is manual-only, the DoD drops items that spec §9.4 requires, and `check` is allowed to be an empty stub, so we cannot objectively tell when this Ready ticket is done.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Blocker | Test plan: "manual + CI (T-005)"; DoD: "All ACs are verified" | This contradicts spec §9.2 ("Every ticket's acceptance criteria map to at least one automated test"), spec §9.4 items 1, 2 and 4, and AGENTS.md §6 ("not complete until `mise run check` is green"). It gives no reason why manual-only is acceptable. It also relies on T-005 for verification, but T-005 is a later ticket that depends on T-001. The DoD drops "covered by automated tests", "`mise run check` is green", and "no TODOs without a linked backlog ticket". | Restore the DoD from the template word for word. Add an automated check: a script `scripts/verify-bootstrap.sh`, run by a `mise run test:bootstrap` task called from `check`. It should check: (a) `mise tasks --json` contains every required task name; (b) each stub task exits 0 and prints "not yet implemented"; (c) `.git/hooks/pre-commit` exists after `setup`; (d) `git ls-files pyproject.toml` is empty; (e) `git check-ignore .env` succeeds. Map AC1–AC5 to the named checks in the test plan. The full clean-clone install (needs network) can stay a recorded manual step for now, explicitly justified, with a note that T-005 automates it. |
| QDE-2 | Major | Scope › Tasks: "each must exit 0 with a clear \"not yet implemented\" message" (includes `check`, `lint`, `fmt`) | If `check` is a stub, `mise run check` is green while checking nothing. AGENTS.md step 4 ("run `mise run check` until it is green") then means nothing for this ticket, and later agents inherit a gate that does no work. This weakens ADR-0008 ("`mise run check` runs the same checks as CI locally"). | Exclude `check`, `lint` and `fmt` from the stubs. `lint` = `uvx pre-commit run --all-files`. `check` = `lint` + `test:bootstrap` (QDE-1). `fmt` runs the fixing hooks. Each remaining stub prints which ticket fills it in, e.g. "not yet implemented (T-003)", which also satisfies spec §9.4 item 4. |
| QDE-3 | Major | AC1: "On a clean clone, `mise install && mise run setup` succeeds"; Scope: "`[env]`: `_.file = \".env\"`" | On a clean clone, mise asks for `mise trust` before it uses a config with `[env]` or tasks. This will block or fail in a non-interactive agent or CI shell. `.env` is also only created by `setup`, which runs after mise has already tried to load `_.file = ".env"`. "Succeeds" is not an observable result. | Rewrite AC1: "Given a fresh `git clone` with no `.env`, when `mise trust && mise install && mise run setup` runs non-interactively, then every command exits 0, `.git/hooks/pre-commit` exists, and `.env` exists with the same content as `.env.example`." Tell the implementer to confirm that a missing `.env` is tolerated, or to make it optional. Add `mise trust` to the README quickstart. |
| QDE-4 | Minor | Scope: "`uvx pre-commit install`" … "`check-merge-conflict`, and `gitleaks`" | The pre-commit version and the hook `rev:` values are not pinned, so AC3 may give different results across machines. The upstream gitleaks hook builds from Go source, which is a hidden toolchain dependency. The ticket also does not name the hook repositories. | Pin the pre-commit version (in `mise.toml` `[tools]` or `uvx pre-commit@<ver>`). Require tagged `rev:` values for `pre-commit/pre-commit-hooks` and `gitleaks/gitleaks`, and record them in the completion notes. Say whether the gitleaks hook may build with Go or must use a mise-pinned gitleaks binary through a `language: system` hook. |
| QDE-5 | Minor | Scope: "pin concrete versions for Python, Node, uv, and pnpm" | The ticket does not say which version lines to use. Spec §9.1 and §6 require Python 3.14 and Node LTS, so an agent might pin 3.13 or a non-LTS Node. | "Python: latest 3.14.x patch; Node: latest patch of the current Active LTS major; uv and pnpm: latest stable at implementation time. Record all four in the completion notes." |
| QDE-6 | Minor | Scope › In: "`.env.example` (empty sections with comments for now) and `.editorconfig`." | No AC covers `.env.example`, `.editorconfig`, the directory skeleton, stub behavior, or `setup` leaving an existing `.env` alone. The sections and editor settings are not specified, so an agent will guess. | Add AC6: "Given an existing `.env`, when `mise run setup` runs again, then `.env` is unchanged." Add AC7: "`backend/`, `frontend/`, `infra/brouter/segments/.gitkeep` and `infra/brouter/profiles/.gitkeep` are tracked." Add AC8: "`.editorconfig` sets utf-8, lf, a final newline, 4-space indentation for `*.py` and 2-space for `*.{ts,tsx,json,yaml,yml,toml}`." List the `.env.example` section headers, e.g. `# Backend`, `# Database`, `# BRouter`, `# Frontend`. |
| QDE-7 | Minor | AC4: "There is no `pyproject.toml` or `.venv` left at the repo root." | `.venv` is git-ignored, so a clean clone never has one. As written, AC4 only checks the implementer's own working copy and cannot be verified from the repo. | "AC4: `git ls-files pyproject.toml uv.lock` returns nothing, and after `mise run setup` no `.venv` exists at the repo root." |
| QDE-8 | Minor | DoD: "README quickstart matches the real commands" | The README quickstart is labelled "(after M0 is complete)" and describes `setup` as "deps, pre-commit hooks". After T-001, `brouter:segments` and `dev` are still stubs. "Matches" leaves the expected edit unclear. | Say exactly what to change: add `mise trust`, add the pinned tool list, and keep the "after M0" label. Otherwise state "no README change expected". |
| QDE-9 | Nit | Header: "- **Related ADRs:** ADR-0007, ADR-0008" (no `Reviews:` line); no `## Implementation notes` section | This differs from `docs/features/TEMPLATE.md`. The ACs are not in Given/When/Then form. | Add `- **Reviews:** –` and an `## Implementation notes` section (hook repos, the trust and `.env` gotchas). Rewrite the ACs as Given/When/Then. |
| QDE-10 | Nit | Header: "Requirements: NFR-3, NFR-4, NFR-8" | NFR-3 (`mise run dev` brings up the stack) is not delivered here, because `dev` is a stub. NFR-8 (CI) is delivered by T-005. | Mark them as partial, e.g. "NFR-3 (task entry point only), NFR-4, NFR-8 (local hooks only)". |

### Strengths
- The scope is tight, fits one PR, and lists the exact task names, hook IDs and the 500 kB large-file threshold.
- `Depends on: –` is correct, and T-001 is the first pick under the pick-order rule.
- The ticket follows ADR-0007's ban on floating aliases and asks for the chosen versions to be recorded.

### Open questions for the author
- Will the owner accept a recorded manual clean-clone run for AC1 until T-005, as long as everything that can run offline is automated through `check` (QDE-1)?
- Should pre-commit and gitleaks be pinned through mise `[tools]`, which would extend ADR-0007's tool list, or only through hook `rev:` values?

### Out of my lane
- Architect: spec §9.1 says "node LTS" while ADR-0007 bans the `lts` alias. Consider aligning the spec wording with the ADR.
- Architect: `docs/features/README.md` contains the "council review is recommended" bullet twice.
