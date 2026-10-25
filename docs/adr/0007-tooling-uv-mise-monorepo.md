# ADR-0007: Tooling with mise and uv in a monorepo

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
The sketch lists both uv and mise. Their roles overlap unless we define them. We also need a frontend next to the backend.

## Decision
- **mise** pins tool versions (`python 3.14`, `node` LTS, `uv`, `pnpm`) and is the **single task runner**: every developer or agent command is `mise run <task>` (e.g. `dev`, `check`, `test`, `lint`, `fmt`, `db:migrate`, `api:gen`, `brouter:segments`).
- **uv** manages Python dependencies and virtualenvs (`backend/pyproject.toml`, `backend/uv.lock`).
- **pnpm** manages frontend dependencies.
- **Monorepo** layout: `backend/`, `frontend/`, `infra/`, `docs/`, plus `compose.yaml` and `mise.toml` at the root.
- Python package name: `geocaching_planner` (distribution `geocaching-planner`). This fixes the "Geochaching" typo. The folder name is unchanged.

## Consequences
- The root `pyproject.toml` and `.venv` from the initial scaffold are moved or replaced by `backend/` in T-001.
- One entry point for agents (`mise tasks` lists everything).
