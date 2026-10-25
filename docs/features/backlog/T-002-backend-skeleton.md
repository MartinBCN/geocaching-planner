# T-002: Backend skeleton and quality gates

- **Status:** Ready
- **Milestone:** M0
- **Depends on:** T-001
- **Requirements:** NFR-4, NFR-5, NFR-7, NFR-8
- **Related ADRs:** ADR-0002, ADR-0007, ADR-0008

## Goal
A typed FastAPI app in `backend/` with a `/api/v1/health` endpoint, configuration, logging, error handling, and all backend quality gates enforced.

## Context
See spec §6 (layering) and §9 (standards). This ticket sets the patterns that every later ticket copies, so get them right.

## Scope
### In
- `backend/pyproject.toml` (uv project `geocaching-planner`, src layout `src/geocaching_planner/`, Python 3.14).
- Runtime deps: `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `structlog`.
- Dev deps: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-socket`, `httpx`, `mypy`, `ruff`.
- Package structure: `api/`, `services/`, `domain/`, `adapters/`, `config.py` (`Settings` via pydantic-settings, env prefix `GCP_`), `main.py` (`create_app()` factory), `logging.py`.
- `GET /api/v1/health` → `{"status": "ok", "version": "..."}`. DB and BRouter checks are added in T-003 and T-015.
- RFC 9457 problem+json exception handlers for `HTTPException`, `RequestValidationError`, and unhandled `Exception` (500 without leaking internals).
- structlog: console renderer in dev, JSON when `GCP_LOG_JSON=true`.
- Uvicorn binds to `127.0.0.1:8000` by default.
- Tool config in `pyproject.toml`:
  - ruff: `line-length = 100`, `target-version = "py314"`, select `E,F,W,I,N,UP,B,A,C4,SIM,RUF,S,PT,ASYNC,TID`, and allow `S101` in tests.
  - mypy: `strict = true` with the pydantic plugin.
  - pytest: `asyncio_mode = "auto"`, markers `integration`, `contract`, `brouter`, `--disable-socket --allow-unix-socket` by default (integration/contract tests opt in with `@pytest.mark.enable_socket`), and coverage `--cov=geocaching_planner --cov-branch --cov-fail-under=85`.
- mise tasks: `test:backend`, and backend parts of `lint`, `fmt`, and `check` (`ruff check`, `ruff format --check`, `mypy`, `pytest`). `dev` runs `uvicorn --reload`.
- pre-commit: add `ruff`, `ruff-format`, and `mypy` (local hook through `uv run`).
- Add the backend variables to `.env.example`.
- **Verify that every dependency installs and works on Python 3.14.** If one does not, document it and stop (see spec §11).

### Out
- Database (T-003).

## Acceptance criteria
- [ ] AC1: `GET /api/v1/health` returns 200 and `{"status":"ok","version":<pkg version>}`.
- [ ] AC2: An unknown route returns 404 with `Content-Type: application/problem+json` and the fields `type`, `title`, `status`.
- [ ] AC3: A validation error returns 422 problem+json with field errors.
- [ ] AC4: An unhandled exception returns 500 problem+json without a stack trace in the body, and the error is logged.
- [ ] AC5: Settings load from env with the `GCP_` prefix. Defaults bind to 127.0.0.1.
- [ ] AC6: `mise run check` runs ruff, ruff-format check, mypy strict, and pytest with an 85% coverage gate, and all of them pass.
- [ ] AC7: A unit test that tries a network call fails (pytest-socket is active).
- [ ] AC8: `/api/v1/openapi.json` is served.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC4, AC8 | unit (httpx ASGITransport) | `tests/unit/api/test_health.py`, `tests/unit/api/test_errors.py` |
| AC5 | unit | `tests/unit/test_config.py` |
| AC6 | CI | `mise run check` |
| AC7 | unit | `tests/unit/test_socket_guard.py` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] AGENTS.md command table is verified
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
