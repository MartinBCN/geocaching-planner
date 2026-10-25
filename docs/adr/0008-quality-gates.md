# ADR-0008: Quality gates (linting, typing, testing, CI)

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
Agents implement tickets autonomously. Strong automated gates are the main safety net.

## Decision
- **Backend:** ruff (lint + format), mypy `--strict`, pytest with pytest-asyncio, pytest-cov **≥ 85% line+branch** (fails the build), testcontainers PostGIS for integration tests, respx for HTTP contract tests, and pytest-socket to block network in unit tests.
- **Frontend:** Biome (lint + format), `tsc --noEmit` strict, Vitest + Testing Library + MSW with **≥ 80% line coverage**, and a Playwright smoke suite.
- **pre-commit:** ruff, ruff-format, biome, mypy (changed files), gitleaks, and basic hygiene hooks.
- **CI (GitHub Actions):** jobs `backend`, `frontend`, and `e2e` on every PR and on `main`. All are required.
- `mise run check` runs the same checks as CI locally.

## Consequences
- Slower first tickets (setup cost) but safer autonomous work.
- Lowering a threshold or disabling a rule globally needs a new ADR. A per-line `# noqa`/`biome-ignore` must include a reason.
