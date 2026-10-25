# T-006: Cache domain model and schema

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-005
- **Requirements:** IMP-4, CAC-4, CAC-5 (data model)
- **Related ADRs:** ADR-0003, ADR-0006
- **Reviews:** [Council review 1](../../reviews/features/T-006-cache-domain-model-review-1.md)

## Goal
Define the cache domain entities and their PostGIS schema, including the effective-location projection. Persistence behavior is implemented separately in T-024.

## Context
Spec §7 defines the model. User data **must** be stored separately from imported data (ADR-0003). `Cache` is the aggregate root with `waypoints` and `logs`; a missing waypoint collection (`None`) means no waypoint data was supplied, while an empty collection means clear all waypoints.

## Scope
### In
- `domain/cache.py`: frozen stdlib dataclasses `Cache`, `CacheWaypoint`, `CacheLog`, `UserCacheData`, and `ImportRun`, plus `CacheType` (Traditional, Multi, Mystery, Letterbox, EarthCache, Wherigo, Virtual, Event, CITO, Mega, Giga, Webcam, Lab, Other), `ContainerSize` (Micro, Small, Regular, Large, Virtual, Other, Not chosen), and `WaypointType`/`LogType` per the Groundspeak GPX schema with an `Other` fallback. Preserve raw source type/container strings on imported entities. `Cache` has `waypoints: tuple[CacheWaypoint, ...] | None` and `logs: tuple[CacheLog, ...]`. Include `Coordinates(lat, lon)` with finite-value/range validation and `content_hash(cache)` over canonically ordered source fields, waypoints, and logs (excluding persistence timestamps and user data).
- `adapters/db/models.py`: ORM models with `geography(Point,4326)`, GiST indexes `ix_caches_location_gist` and `ix_user_cache_data_corrected_location_gist`, and btree indexes `ix_caches_type`, `ix_caches_difficulty`, `ix_caches_terrain`, `ix_caches_found_by_me`, and `ix_caches_is_archived`. Store enums as strings, not native PostgreSQL enums. Map coordinates as `POINT(lon lat)`.
- A SQL projection for `effective_location = COALESCE(user_cache_data.corrected_location, caches.location)` for selected output and ordering only. T-010 owns spatial predicates as separate indexed branches for corrected and original locations.
- An Alembic migration (with downgrade).
- `Cache.source_hash` stores the pure domain content hash; `created_at` is immutable on database updates.
- This ticket creates the `ImportRun` schema including a persisted waypoint count and JSON `errors` records containing severity and parse context.

### Out
- Repository behavior and fakes (T-024), parsing (T-007), querying and filtering (T-010).

## Acceptance criteria
- [ ] AC1: Given a fresh PostGIS database, when the migration is applied, then it creates `caches`, `cache_waypoints`, `cache_logs`, `user_cache_data`, and `import_runs`; `pg_indexes` contains both named GiST indexes and all named btree indexes; and `downgrade -1` followed by `upgrade head` restores the same schema.
- [ ] AC2: Given asymmetric coordinates `(lat=52.1, lon=4.3)`, when mapped to and from PostGIS, then the returned coordinates are unchanged and the point is stored in `POINT(4.3 52.1)` order.
- [ ] AC3: Given invalid or non-finite latitude/longitude values, when `Coordinates` is constructed, then `ValueError` is raised; valid boundary values are accepted.
- [ ] AC4: Given cache aggregates with identical canonical source fields, waypoints, and logs, when `content_hash` is computed, then hashes match regardless of input ordering; a change to a source field, waypoint, or log changes the hash, while user data and timestamps do not.
- [ ] AC5: Given D/T values in `{1.0, 1.5, …, 5.0}`, when a cache is constructed, then it is accepted; values outside the range or increments raise `ValueError`.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC2 | integration | `backend/tests/integration/test_migrations.py`, `backend/tests/integration/test_effective_location.py::test_coordinates_round_trip` |
| AC3–AC5 | unit | `backend/tests/unit/domain/test_coordinates.py`, `backend/tests/unit/domain/test_content_hash.py`, `backend/tests/unit/domain/test_cache_ratings.py` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Implementation notes
- Use frozen stdlib dataclasses in `domain/`; keep Pydantic in `api/` and SQLAlchemy in `adapters/db/`.
- Required GiST indexes include both original and corrected geography columns. COALESCE is a projection only; T-010 handles indexable spatial filtering.
- Enum values are persisted as VARCHAR so adding values does not require PostgreSQL ENUM type lifecycle management.

## Completion notes
_…_
