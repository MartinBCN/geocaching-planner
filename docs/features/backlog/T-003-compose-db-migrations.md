# T-003: Compose stack, database, and migrations

- **Status:** Ready
- **Milestone:** M0
- **Depends on:** T-002
- **Requirements:** NFR-2, NFR-3
- **Related ADRs:** ADR-0004, ADR-0006

## Goal
`mise run dev` starts PostGIS and BRouter in Docker. The backend connects asynchronously to PostGIS with Alembic migrations, and integration tests run against a throwaway PostGIS container.

## Scope
### In
- `compose.yaml`:
  - `db`: `postgis/postgis:17-3.5` (pin), with a named volume, a healthcheck, and the port bound to `127.0.0.1:5432`.
  - `brouter`: an image that runs the BRouter server (build from `infra/brouter/Dockerfile` using the official BRouter release JAR if no maintained image exists). It mounts `infra/brouter/segments` and `infra/brouter/profiles`, uses port `127.0.0.1:17777`, and has a healthcheck.
- `mise run brouter:segments`: a script (`infra/brouter/download_segments.sh` or Python) that downloads the configured `.rd5` tiles from `https://brouter.de/brouter/segments4/`. The default set (`E5_N50.rd5`) covers NL/BE/W-DE and can be overridden with `BROUTER_SEGMENTS="E5_N50 E0_N50"`. It skips files that already exist.
- Copy the standard profiles (`trekking.brf`, `fastbike.brf`, `safety.brf`) into `infra/brouter/profiles`, or fetch them in the same task.
- Backend deps: `sqlalchemy[asyncio]`, `asyncpg`, `geoalchemy2`, `alembic`. Dev deps: `testcontainers[postgres]`.
- `adapters/db/`: async engine and session factory, a `get_session` dependency, and a declarative `Base` with a naming convention for constraints.
- Alembic in `backend/migrations` (async env). The first migration runs `CREATE EXTENSION IF NOT EXISTS postgis`.
- `mise run db:migrate` and `mise run db:revision`.
- `mise run dev`: `docker compose up -d --wait`, then migrate, then start the backend (frontend is added in T-004).
- Health endpoint: add `db: ok|error` (and keep `status` `degraded` on failure; still HTTP 200).
- Test fixtures in `tests/integration/conftest.py`: a session-scoped PostGIS testcontainer, migrations to head, and a per-test transaction rollback (or truncate) session.

### Out
- Domain tables (T-006). BRouter API usage (T-015).

## Acceptance criteria
- [ ] AC1: `mise run dev` brings up healthy `db` and `brouter` containers and a running backend.
- [ ] AC2: With segments downloaded, `curl "http://127.0.0.1:17777/brouter?lonlats=5.12,52.09|5.13,52.10&profile=trekking&format=geojson"` returns a route.
- [ ] AC3: `alembic upgrade head` followed by `alembic downgrade base` works on an empty DB (integration test).
- [ ] AC4: `/api/v1/health` reports `db: ok` when the DB is up and `status: degraded, db: error` when it is down.
- [ ] AC5: Integration tests run against a testcontainer and leave no state between tests.
- [ ] AC6: README has a section explaining segment download and disk usage.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC3 | integration | `tests/integration/test_migrations.py::test_upgrade_downgrade_roundtrip` |
| AC4 | unit (fake session) + integration | `tests/unit/api/test_health.py`, `tests/integration/test_health_db.py` |
| AC5 | integration | `tests/integration/test_isolation.py` |
| AC1, AC2, AC6 | manual (record in completion notes); a live BRouter test is added in T-015 |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] README and `.env.example` are updated
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
