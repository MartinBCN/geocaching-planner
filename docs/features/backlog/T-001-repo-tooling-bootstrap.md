# T-001: Repository and tooling bootstrap

- **Status:** Ready
- **Milestone:** M0
- **Depends on:** –
- **Requirements:** NFR-3, NFR-4, NFR-8
- **Related ADRs:** ADR-0007, ADR-0008

## Goal
A developer or agent can clone the repo, run `mise install && mise run setup`, and get the pinned toolchain and working pre-commit hooks.

## Context
The repo currently contains a root `pyproject.toml` (name `geochachingplanner`, `requires-python >=3.14`) and a root `.venv`. ADR-0007 moves all Python code into `backend/`. The git repo is already initialized, and `.gitignore` exists.

## Scope
### In
- Remove the root `pyproject.toml` and `.venv`. Create the directories `backend/`, `frontend/`, and `infra/brouter/{segments,profiles}` with `.gitkeep` files where they are empty.
- Root `mise.toml`:
  - `[tools]`: `python = "3.14"`, `node = "lts"` (pin the exact major), `uv = "latest"` (pin the exact version), `pnpm` (pin the exact version).
  - `[env]`: `_.file = ".env"`.
  - Tasks (stubs are fine where later tickets fill them in, but each must exit 0 with a clear "not yet implemented" message): `setup`, `dev`, `check`, `lint`, `fmt`, `test`, `test:backend`, `test:frontend`, `test:e2e`, `db:migrate`, `db:revision`, `api:gen`, `brouter:segments`.
  - `setup` installs pre-commit hooks (`uvx pre-commit install`) and copies `.env.example` to `.env` if it is missing.
- `.pre-commit-config.yaml`: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`, `check-added-large-files` (500 kB), `check-merge-conflict`, and `gitleaks`. ruff, mypy, and biome hooks are added in T-002 and T-004.
- `.env.example` (empty sections with comments for now) and `.editorconfig`.

### Out
- Python and Node project contents (T-002, T-004).

## Acceptance criteria
- [ ] AC1: On a clean clone, `mise install && mise run setup` succeeds and installs the git hooks.
- [ ] AC2: `mise tasks` lists all tasks named above.
- [ ] AC3: `uvx pre-commit run --all-files` passes.
- [ ] AC4: There is no `pyproject.toml` or `.venv` left at the repo root.
- [ ] AC5: `git status` after `mise run setup` shows no untracked `.env`, because it is ignored.

## Test plan
| AC | Test level | Test |
|---|---|---|
| AC1–AC5 | manual + CI (T-005) | Run the commands in a fresh clone and record the output in the completion notes |

## Definition of Done
- [ ] All ACs are verified
- [ ] README quickstart matches the real commands
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
