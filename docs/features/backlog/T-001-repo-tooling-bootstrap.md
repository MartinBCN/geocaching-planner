# T-001: Repository and tooling bootstrap

- **Status:** Draft
- **Milestone:** M0
- **Depends on:** –
- **Requirements:** NFR-3 (entry point only; completed by T-003/T-004), NFR-4 (`.env.example` scaffold), NFR-8 (local hooks only; CI gate in T-005)
- **Related ADRs:** ADR-0007, ADR-0008
- **Reviews:** [Council review 1](../../reviews/features/T-001-repo-tooling-bootstrap-review-1.md)

## Goal
A developer or agent can clone the repo, run `mise install && mise run setup`, and get the pinned toolchain and working pre-commit hooks.

## Context
The repo currently contains a root `pyproject.toml` (name `geochachingplanner`, `requires-python >=3.14`) and a root `.venv`. ADR-0007 moves all Python code into `backend/`. The git repo is already initialized; this ticket owns the ignore rules needed for the new repository layout and local data.

## Scope
### In
- Remove the root `pyproject.toml` and `.venv`. Create the directories `backend/`, `frontend/`, and `infra/brouter/{segments,profiles}` with `.gitkeep` files where they are empty.
- Update `.gitignore` to ignore `.env`, `.venv/`, `node_modules/`, `infra/brouter/segments/*` except `.gitkeep`, and Pocket Query `*.gpx`/`*.zip` data outside `backend/tests/fixtures/`. Keep `.env.example` and the segments `.gitkeep` tracked.
- Root `mise.toml`:
  - `[tools]`: pin the latest Python 3.14.x, the latest patch of the current Node Active LTS major, and current stable uv and pnpm versions. Do not use floating aliases such as `lts` or `latest`; record exact versions in completion notes.
  - `[env]`: load `.env` optionally so a clean clone can run setup before the file exists.
  - Tasks: `setup`, `dev`, `check`, `lint`, `fmt`, `test`, `test:bootstrap`, `test:backend`, `test:frontend`, `test:e2e`, `db:migrate`, `db:revision`, `api:gen`, `brouter:segments`, and `check:pre-commit`. `check` and `lint` run `mise run check:pre-commit` and `mise run test:bootstrap`; `fmt` runs the fixing hooks. Other not-yet-implemented tasks must print the owning ticket and exit non-zero; they must not be dependencies of `check`.
  - Pin pre-commit via `uvx pre-commit@<exact-version>` and pin the `pre-commit/pre-commit-hooks` and `gitleaks/gitleaks` hook `rev:` values to tagged releases. Provide gitleaks as a mise-pinned tool and invoke the installed binary from its hook. `setup` installs the pinned pre-commit hooks and copies `.env.example` to `.env` only if `.env` is absent.
- `scripts/verify-bootstrap.sh` and `mise run test:bootstrap`: automated checks for task names, stub behavior, installed git hook, absence of tracked root Python project files, and ignore rules. The checks run from `mise run check`.
- `.pre-commit-config.yaml`: `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`, `check-added-large-files` (500 kB), `check-merge-conflict`, and `gitleaks`. ruff, mypy, and biome hooks are added in T-002 and T-004.
- `.env.example` (empty sections with comments for now) and `.editorconfig`.
- Update spec §9.1 to match ADR-0007's concrete Python, Node, uv, and pnpm pinning.

### Out
- Python and Node project contents (T-002, T-004).

## Acceptance criteria
- [ ] AC1: Given a clean clone without `.env`, when `mise trust && mise install && mise run setup` runs non-interactively, then it exits 0, installs `.git/hooks/pre-commit`, and creates `.env` from `.env.example`.
- [ ] AC2: Given the bootstrap task, when `mise tasks --json` is inspected, then every task named in Scope is present and `mise run check` exits 0 without calling a stub.
- [ ] AC3: Given `mise run setup` has run, when `mise run lint` runs, then all pinned pre-commit hooks pass; re-running setup leaves an existing `.env` byte-for-byte unchanged.
- [ ] AC4: Given the repository layout, when git tracking and ignore rules are checked, then root `pyproject.toml`/`uv.lock` are untracked, no root `.venv` exists, `.env` and a segment `.rd5` are ignored, and `.env.example` and `segments/.gitkeep` are not ignored.
- [ ] AC5: Given any not-yet-implemented task is invoked, when it runs, then it identifies the owning ticket and exits non-zero; `mise run check` never invokes it.
- [ ] AC6: Given the required repository scaffold, when `git ls-files` is checked, then required `.gitkeep` files and the documented `.editorconfig` are tracked.

## Test plan
| AC | Test level | Test |
|---|---|---|
| AC1 | manual clean-clone check until T-005; record output | `mise trust && mise install && mise run setup` |
| AC2 | automated bootstrap | `scripts/verify-bootstrap.sh::verify_task_inventory` |
| AC3 | automated bootstrap | `scripts/verify-bootstrap.sh::verify_hooks_and_setup_idempotence` |
| AC4 | automated bootstrap | `scripts/verify-bootstrap.sh::verify_layout_and_ignore_rules` |
| AC5 | automated bootstrap | `scripts/verify-bootstrap.sh::verify_stub_failures_and_check_is_real` |
| AC6 | automated bootstrap | `scripts/verify-bootstrap.sh::verify_required_scaffold_is_tracked` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] README quickstart matches the real commands
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Implementation notes
- **Must:** README quickstart includes `mise trust`; state that clean-clone setup tolerates a missing `.env`.
- `.env.example` contains commented sections for backend, database, BRouter, and frontend configuration. Pre-commit must be pinned consistently in setup, checks, and tests.

## Completion notes
_…_
