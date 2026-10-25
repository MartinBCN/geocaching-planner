# T-003: Compose stack, database, and migrations

- **Status:** Draft
- **Milestone:** M0
- **Depends on:** T-002
- **Requirements:** NFR-3 (database startup component only; frontend completion in T-004)
- **Related ADRs:** ADR-0006
- **Reviews:** [Council review 1](../../reviews/features/T-003-compose-db-migrations-review-1.md)

## Goal
The backend connects asynchronously to PostGIS with Alembic migrations, and integration tests run against a throwaway PostGIS container. T-004 adds the frontend to complete NFR-3.

## Context
ADR-0002 requires all published ports to remain on loopback. ADR-0006 selects PostGIS. T-002's health endpoint and `AppConfig` are extended here; T-004 adds frontend startup and T-023 adds BRouter startup.

## Scope
### In
- `compose.yaml` database service: `postgis/postgis:17-3.5` (pin), a named volume, healthcheck, and host port bound to `127.0.0.1` using configurable `DB_PORT` (default 5432).
- Compose credentials use documented `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` values from `.env` with development-only defaults; `GCP_DATABASE_URL` matches these values.
- Backend deps: `sqlalchemy[asyncio]`, `asyncpg`, `geoalchemy2`, `alembic`. Dev deps: `testcontainers[postgres]`, `PyYAML` for pure Compose port validation.
- `adapters/db/`: async engine and session factory, a `get_session` dependency, and a declarative `Base` with a naming convention for constraints.
- Alembic in `backend/migrations` (async env). `migrations/env.py` reads `AppConfig.database_url`; `GCP_DATABASE_URL` is documented in `.env.example`. The baseline migration creates PostGIS if needed; its downgrade is a documented no-op because the extension belongs to the database image.
- `mise run db:migrate`, `mise run db:revision`, `mise run test:compose:db`, and `mise run test:compose:dev`.
- `mise run dev` starts the database, waits for health, runs migrations, then starts the backend on `127.0.0.1`; T-004 adds the frontend and T-023 adds BRouter.
- `DatabaseProbe` protocol in `services/health.py`, implemented in `adapters/db/` using `SELECT 1` with a two-second timeout and injected into the health service. `/health` stays HTTP 200 and reports exact `db` status.
- Test fixtures in `tests/integration/conftest.py`: a session-scoped PostGIS testcontainer and migrations to head. Per-test transactions use `join_transaction_mode="create_savepoint"`; a test-only table proves commit isolation.
- Compose host-port validation uses a pure `find_non_loopback_ports(compose: dict) -> list[str]` and PyYAML. It supports short and long syntax, rejects missing host IP, `0.0.0.0`, `localhost`, and `::1`, and permits only explicit `127.0.0.1` published bindings or `expose`-only services.

### Out
- Domain tables and repositories (T-006 and T-024). BRouter service and segment handling (T-023); adapter use (T-015).

## Acceptance criteria
- [ ] AC1: Given Docker is available, when `mise run dev` starts, then the database becomes healthy, migrations complete, and the backend runs on `127.0.0.1`; its Compose host binding is loopback-only.
- [ ] AC2: Given an empty PostGIS test database, when migrations run `upgrade head`, `downgrade -1`, `downgrade base`, and `upgrade head`, then each succeeds, the expected Alembic version state is present, and `postgis_version()` succeeds. Baseline downgrade leaves image-owned extensions untouched.
- [ ] AC3: Given an available database, `/api/v1/health` returns 200 `{"status":"ok","version":<v>,"db":"ok"}`; given a closed-port database URL, it returns 200 `{"status":"degraded","version":<v>,"db":"error"}` within three seconds.
- [ ] AC4: Given test A inserts and commits a row in the test-only isolation table, when test B starts, then the table is empty.
- [ ] AC5: Given short- and long-form published port entries, the checker reports missing host IP, `0.0.0.0`, `localhost`, and `::1`, permits only `127.0.0.1` and expose-only services, and reports no violations for the real compose file.
- [ ] AC6: Given the pinned Python 3.14.x environment, when the automated dependency smoke test installs and imports all T-003 runtime dependencies, then it succeeds; otherwise record the error, block the ticket, and stop without changing the toolchain pin.
- [ ] AC7: Given the README, when its database section is read, then it explains the local volume, that `docker compose down -v` deletes user data, and that normal stop/start preserves it.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1 | automated compose + e2e smoke | `mise run test:compose:db`, `frontend/e2e/smoke.spec.ts::backend_health_is_visible` |
| AC2 | integration | `backend/tests/integration/test_migrations.py::test_baseline_migration_roundtrip` |
| AC3 | unit + integration | `backend/tests/unit/api/test_health.py`, `backend/tests/integration/test_health_db.py` |
| AC4 | integration | `backend/tests/integration/test_isolation.py::test_committed_rows_do_not_leak_between_tests` |
| AC5 | unit/configuration | `backend/tests/unit/test_compose_ports.py::test_port_binding_validation` |
| AC6 | unit/dependency smoke | `backend/tests/unit/test_runtime_dependencies.py::test_database_dependencies_import` |
| AC7 | docs | `backend/tests/unit/test_readme_database_docs.py::test_database_volume_warning_is_documented` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Implementation notes
- Compose publishes the database port only on loopback; keep its host port configurable while preserving that binding.
- Add one-line comments and safe local defaults for `GCP_DATABASE_URL`, `DB_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in `.env.example`.
- Integration test containers use the same pinned PostGIS image as Compose. The baseline extension downgrade is intentionally a no-op.
- Update T-002's `test_health.py` exact response assertion for the added database status.
- T-003 owns the database service only. BRouter container, segments, profiles, and download workflow are moved to T-023.

## Completion notes
_…_
