# T-002: Backend skeleton and quality gates

- **Status:** Complete
- **Milestone:** M0
- **Depends on:** T-001
- **Requirements:** NFR-4, NFR-5, NFR-7, NFR-8
- **Related ADRs:** ADR-0002, ADR-0007, ADR-0008
- **Reviews:** [Council review 1](../../reviews/features/T-002-backend-skeleton-review-1.md)

## Goal
A typed FastAPI app in `backend/` with a `/api/v1/health` endpoint, configuration, logging, error handling, and all backend quality gates enforced.

## Context
See spec §6 (layering) and §9 (standards). This ticket sets the patterns that every later ticket copies, so get them right. API-only tests without a database live under `tests/unit/api`; DB-backed API tests live under `tests/integration`.

## Scope
### In
- `backend/pyproject.toml` (uv project `geocaching-planner`, src layout `src/geocaching_planner/`, Python 3.14).
- Runtime deps: `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `structlog`.
- Dev deps: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-socket`, `httpx`, `mypy`, `ruff`.
- Package structure: `api/`, `services/`, `domain/`, `adapters/`, `config.py` (`AppConfig` via pydantic-settings, env prefix `GCP_`), `main.py` (`create_app(config: AppConfig | None = None)` factory), and `logging_config.py`.
- `api/deps.py` exposes the configured `AppConfig` using `Annotated[..., Depends(...)]`. Tests use `app.dependency_overrides`; tests construct settings with `_env_file=None` and clear `GCP_*` variables.
- `GET /api/v1/health` → `{"status": "ok", "version": "..."}`. DB and BRouter checks are added in T-003 and T-015.
- RFC 9457 `Problem` (`type`, `title`, `status`, `detail`, `instance`) and `FieldError` models. A 422 includes `errors: [{field, message}]`. Register handlers for `starlette.exceptions.HTTPException`, `RequestValidationError`, and unhandled `Exception`; document 4xx, 422, and 5xx Problem responses as `application/problem+json` in OpenAPI, including the Problem schema.
- Framework-free `DomainError`, `NotFoundError`, `ConflictError`, and `UpstreamUnavailableError` types map to problem+json in `api/`. Add an automated layering test: `domain/` cannot import FastAPI, Starlette, SQLAlchemy, GeoAlchemy2, httpx, or pydantic-settings; `services/` cannot import `api/` or `adapters/`.
- structlog: console renderer in dev, JSON when `GCP_LOG_JSON=true`.
- Route stdlib and Uvicorn logging through `structlog.stdlib.ProcessorFormatter`; include a request ID in 500 `instance` and the associated log event.
- `AppConfig` fields `host="127.0.0.1"`, `port=8000`, `log_json=False`, and `database_url` from `GCP_DATABASE_URL`; `python -m geocaching_planner` starts Uvicorn using `settings.host` and `settings.port`, and `dev` calls that entry point.
- Tool config in `pyproject.toml`:
  - ruff: `line-length = 100`, `target-version = "py314"`, select `E,F,W,I,N,UP,B,A,C4,SIM,RUF,S,PT,ASYNC,TID`, and allow `S101` in tests.
  - mypy: `strict = true` with the pydantic plugin.
  - pytest: `asyncio_mode = "auto"`, markers `integration`, `contract`, `brouter`, `slow`, default `-m "not brouter"`, `--disable-socket --allow-unix-socket` by default (integration/contract tests opt in with `@pytest.mark.enable_socket`), and coverage `--cov=geocaching_planner --cov-branch --cov-fail-under=85`.
- mise tasks: `test:backend`, `lint:backend`, `fmt:backend`, `typecheck:backend`, `check:backend`; aggregate `lint`, `fmt`, and `check` depend on these. `dev` runs the module entry point with reload enabled.
- pre-commit hooks invoke ruff/mypy through `uv run --project backend`; mypy uses `--config-file backend/pyproject.toml` and `files: ^backend/`.
- Add documented backend variables and defaults to `.env.example`.
- **Verify that every dependency installs and works on Python 3.14.** `mise run verify:python:314` performs the locked sync and runtime imports; if one fails, document it and stop (see spec §11).

### Out
- Database (T-003).

## Acceptance criteria
- [ ] AC1: Given default `AppConfig`, when `/api/v1/health` is requested, then the response is 200 and has `{"status":"ok","version":<importlib.metadata.version("geocaching-planner")>}`.
- [ ] AC2: Given an unknown route and a method-not-allowed route, when requested, then each returns 404/405 `application/problem+json` with `type:"about:blank"`, the matching title/status, non-empty `detail`, and `instance`.
- [ ] AC3: Given an invalid request body, when submitted, then the response is 422 `application/problem+json` with a `Problem` body and `errors` entries shaped as `{field, message}`; OpenAPI advertises that media type and schema.
- [ ] AC4: Given a test-only route that raises `RuntimeError("secret-xyz")`, when requested through ASGI transport with `raise_app_exceptions=False`, then it returns 500 Problem JSON containing neither the secret nor `Traceback`, and exactly one captured error log has `exc_info` and the same request ID as `instance`.
- [ ] AC5: Given no environment overrides, when settings are loaded, then host/port/log_json are `127.0.0.1`/8000/false; given `GCP_PORT=9000`, then port is 9000 and the module entry point passes configured host and port to Uvicorn.
- [ ] AC6: `mise run check` runs ruff, ruff-format check, mypy strict, and pytest with an 85% coverage gate, and all of them pass.
- [ ] AC7: Given a unit test calling `socket.create_connection(("127.0.0.1", 9))`, pytest-socket raises `SocketBlockedError`; a test marked `enable_socket` can open a local socket.
- [ ] AC8: Given the application, when `/api/v1/openapi.json` is requested, then it is 200 JSON with `/api/v1/health` and `Problem` in its schemas.
- [ ] AC9: Given `GCP_LOG_JSON=true`/`false`, when a log event is emitted, then JSON mode has `event`, `level`, and `timestamp`, and console mode is not JSON.
- [ ] AC10: Given illegal imports in `domain/` or `services/`, when the layering test runs, then it fails; valid dependencies pass.
- [ ] AC11: Given Python 3.14.x pinned by mise, when `mise run verify:python:314` performs `uv sync --locked` and imports all runtime packages, then it succeeds. If not, record the package/error, set `Status: Blocked`, create a Draft fallback ticket, and do not change `mise.toml`.
- [ ] AC12: Given a service raises framework-free `NotFoundError`, when the API handler maps it, then the client receives 404 Problem JSON without the service importing FastAPI or Starlette.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1 | unit | `backend/tests/unit/api/test_health.py::test_health_uses_package_version` |
| AC2 | unit | `backend/tests/unit/api/test_errors.py::test_unknown_route_and_method_not_allowed_use_problem` |
| AC3 | unit | `backend/tests/unit/api/test_errors.py::test_validation_errors_use_field_error_list` |
| AC4 | unit | `backend/tests/unit/api/test_errors.py::test_unhandled_error_is_safe_logged_and_correlated` |
| AC3, AC8 | unit | `backend/tests/unit/api/test_openapi.py::test_openapi_declares_problem_responses` |
| AC5 | unit | `backend/tests/unit/test_config.py::test_config_defaults_and_environment_override`, `backend/tests/unit/test_main.py::test_entry_point_uses_configured_bind` |
| AC6 | CI | `mise run check:backend` |
| AC7 | unit | `backend/tests/unit/test_socket_guard.py::test_network_socket_is_blocked`, `::test_enable_socket_allows_local_socket` |
| AC9 | unit | `backend/tests/unit/test_logging.py::test_json_renderer_when_enabled`, `::test_console_renderer_by_default` |
| AC10 | unit | `backend/tests/unit/test_layering.py::test_domain_and_services_import_boundaries` |
| AC11 | dependency smoke | `mise run verify:python:314` and `backend/tests/unit/test_runtime_dependencies.py::test_runtime_imports` |
| AC12 | unit | `backend/tests/unit/api/test_errors.py::test_domain_not_found_maps_to_404_problem` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] AGENTS.md command table is verified
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Implementation notes
- Use `Annotated[T, Depends(...)]` rather than default-value dependency declarations.
- The 500 error log includes a request identifier shared with `instance`; do not expose exception details to clients. Add one-line comments and defaults for each backend environment variable in `.env.example`.
- API tests that need no database use ASGITransport under `tests/unit/api`; tests requiring PostGIS belong in `tests/integration`.
- The T-003 migration adds the SQLAlchemy typing stubs/configuration; do not enable the deprecated SQLAlchemy mypy plugin.

## Completion notes
- `mise run check` exits 0: ruff, mypy --strict, 21 pytest tests (92.39% coverage, gate 85%), and `verify:python:314` all pass.
- `dev` now runs the backend with `--reload` (`python -m geocaching_planner`). T-003 extends it into the full stack.
- `scripts/verify-bootstrap.sh`: `dev` removed from STUB_TASKS (it is real now). The scaffold check uses `backend/pyproject.toml` instead of `backend/.gitkeep`. The EXIT trap is fixed for bash under `set -u`.
- pre-commit backend mypy hook runs `uv run --directory backend mypy src tests`, so module resolution matches the mise task.
- Open items for owner: default `GCP_DATABASE_URL` in `.env.example` is a proposal; the gitleaks `repo: local` hook (`language: system`) deviation from T-001 needs confirmation; review the `authors` email in `backend/pyproject.toml`.
