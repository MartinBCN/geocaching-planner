# ADR-0008: Quality gates (linting, typing, testing, CI)

- **Status:** Accepted
- **Date:** 2026-10-26
- **Reviews:** [Council review 1](../reviews/adr/0008-quality-gates-review-1.md)

## Context
Agents implement tickets autonomously. Strong automated gates are the main safety net.

## Decision
- **Backend:** ruff (lint + format), mypy `--strict`, pytest with pytest-asyncio, pytest-cov **≥ 85% line+branch** (fails the build), testcontainers PostGIS for integration tests, respx for HTTP contract tests, and pytest-socket to block network in unit tests.
- **Frontend:** Biome (lint + format), `tsc --noEmit` strict, Vitest + Testing Library + MSW with **≥ 80% line coverage on `frontend/src/`, excluding the generated API client**, and a Playwright smoke suite.
- **pre-commit:** ruff, ruff-format, biome, mypy (changed files), gitleaks, and basic hygiene hooks.
- **CI (GitHub Actions):** jobs `backend` and `frontend` plus required `pre-commit` on every PR and on `main`. The project is private and not deployed, so Playwright E2E is run locally when needed, not on GitHub-hosted runners. The repository owner must require the `backend`, `frontend`, and `pre-commit` checks in GitHub branch protection or a ruleset before merging; T-005 documents the required check names for that repository setting. Branch protection is owner-managed and is not verified by the workflow.
- `mise run check` runs the shared automated quality gates locally. At the owner's request, actionlint is CI-only: its separate pre-commit configuration is run by `mise run ci:lint:workflows` in the required `pre-commit` job, and is neither installed by local setup nor run by local checks. This avoids a local Go-toolchain bootstrap dependency. The separate `mise run test:e2e` task remains available for local E2E testing.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Manual review without automated gates | Low setup cost | Regressions and inconsistent standards are easier to miss in autonomous implementation |
| Include E2E smoke tests on every hosted CI run | Verifies user flow in a clean environment | Adds runner time and maintenance cost for this private, undeployed project |
| Separate local and CI check definitions | Each environment can optimize independently | Checks can drift; `mise run check` would no longer provide a reliable local equivalent of CI |

## Consequences
- Slower first tickets (setup cost) but safer autonomous work. Tooling and local gates are established in T-001–T-004; CI jobs and documentation of required check names are delivered in T-005. E2E remains a local task and is not part of hosted CI.
- Lowering a threshold or disabling a rule globally needs a new ADR. A per-line `# noqa`/`biome-ignore` must include a reason.
