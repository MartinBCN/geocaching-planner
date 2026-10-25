# ADR-0007: Tooling with mise and uv in a monorepo

- **Status:** Accepted
- **Date:** 2026-10-25
- **Reviews:** [Council review 1](../reviews/adr/0007-tooling-uv-mise-monorepo-review-1.md)

## Context
The sketch lists both uv and mise. Their roles overlap unless we define them. We also need a frontend next to the backend.

## Decision
- **mise** pins exact, concrete versions of Python, Node, uv, and pnpm in the root `mise.toml`; floating aliases such as `lts` and `latest` are not used. The committed `mise.toml` is the version source of truth. Pin changes are made explicitly and reviewed with the tooling updates (T-001).
- **mise** is the task runner for project-defined tasks: run project tasks through `mise run <task>` (e.g. `dev`, `check`, `test`, `lint`, `fmt`, `db:migrate`, `api:gen`, `brouter:segments`). Git and other system commands required by the workflow are run directly.
- **uv** manages Python dependencies and virtualenvs (`backend/pyproject.toml`, `backend/uv.lock`).
- **pnpm** manages frontend dependencies.
- **Monorepo** layout: `backend/`, `frontend/`, `infra/`, `docs/`, plus `compose.yaml` and `mise.toml` at the root.
- Python package name: `geocaching_planner` (distribution `geocaching-planner`). This fixes the "Geochaching" typo. The folder name is unchanged.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Separate task runners and independently installed tools | Familiar tools can be invoked directly | Duplicated setup and version management; commands vary across environments |
| Poetry for Python dependency management | Integrated Python packaging and dependency workflows | Adds a separate Python toolchain choice instead of using the already selected uv |
| Separate repositories for backend and frontend | Independent release histories | Makes shared API contracts and one-command local development harder to coordinate |

## Consequences
- The root `pyproject.toml` and `.venv` from the initial scaffold are moved or replaced by `backend/` in T-001.
- Project tasks have one discoverable entry point (`mise tasks` lists everything). Running the application requires installing mise and the pinned tools as described in the README quickstart, as well as Docker; contributors additionally use the setup task.
