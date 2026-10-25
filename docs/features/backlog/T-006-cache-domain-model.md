# T-006: Cache domain model and schema

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-005
- **Requirements:** IMP-4, IMP-5, CAC-4, CAC-5 (data side)
- **Related ADRs:** ADR-0003, ADR-0006

## Goal
Domain entities, ORM models, migration, and a repository for caches, waypoints, logs, user data, and import runs. The "effective location" concept is implemented once and tested.

## Context
Spec §7 defines the model. User data **must** be stored separately from imported data (ADR-0003).

## Scope
### In
- `domain/cache.py`: frozen dataclasses or pydantic models `Cache`, `CacheWaypoint`, `CacheLog`, `UserCacheData`, and `ImportRun`, plus enums `CacheType` (Traditional, Multi, Mystery/Unknown, Letterbox, EarthCache, Wherigo, Virtual, Event, CITO, Mega, Giga, Webcam, Lab, Other), `ContainerSize` (Micro, Small, Regular, Large, Virtual, Other, Not chosen), `WaypointType`, and `LogType`. Include a value object `Coordinates(lat, lon)` with validation.
- `adapters/db/models.py`: ORM models with `geography(Point,4326)` and GiST indexes, and indexes on `type`, `difficulty`, `terrain`, `found_by_me`, and `is_archived`.
- A SQL view or hybrid expression `effective_location = COALESCE(user_cache_data.corrected_location, caches.location)`.
- An Alembic migration (with downgrade).
- `services/ports.py`: `CacheRepository` protocol with `upsert_many(caches) -> UpsertResult`, `get(gc_code)`, `get_user_data`, `set_user_data`, and `add_import_run`.
- `adapters/db/cache_repository.py`: implementation with `INSERT … ON CONFLICT (gc_code) DO UPDATE`. Track created, updated, and unchanged by comparing a content hash column (`source_hash`).
- An in-memory fake `CacheRepository` for unit tests in `tests/fakes/`.

### Out
- Parsing (T-007), querying and filtering (T-010).

## Acceptance criteria
- [ ] AC1: The migration creates all tables and indexes. Upgrade and downgrade round-trip.
- [ ] AC2: Upserting a new cache reports `created`. Upserting it unchanged reports `unchanged`. Upserting with a changed field reports `updated`.
- [ ] AC3: Upsert never modifies `user_cache_data` (note and corrected coordinates survive a re-import).
- [ ] AC4: Logs are deduplicated by log id. Waypoints of a cache are replaced by the latest import set.
- [ ] AC5: The effective location returns the corrected coordinates when they are set, and the original otherwise.
- [ ] AC6: `Coordinates` rejects lat outside [-90, 90] and lon outside [-180, 180].
- [ ] AC7: The fake repository and the DB repository pass the same shared contract test suite.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1 | integration | `tests/integration/test_migrations.py` |
| AC2–AC5, AC7 | integration + unit (parametrized over fake and real) | `tests/integration/repositories/test_cache_repository.py` (shared suite also run against the fake in `tests/unit`) |
| AC6 | unit | `tests/unit/domain/test_coordinates.py` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Spec §7 is updated if any field changed
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
