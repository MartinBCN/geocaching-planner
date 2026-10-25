# T-024: Cache repository and persistence behavior

- **Status:** Draft
- **Milestone:** M1
- **Depends on:** T-006
- **Requirements:** IMP-4, IMP-5, IMP-6 (persistence), CAC-4, CAC-5 (persistence)
- **Related ADRs:** ADR-0003, ADR-0006
- **Reviews:** –

## Goal
Persist cache aggregates through one asynchronous repository contract that is shared by imports, queries, and unit tests.

## Context
T-006 provides frozen domain aggregates and the database schema. `Cache` is the aggregate root and carries its logs and optional waypoint set. T-007 parses cache aggregates; T-008 depends on this ticket for repository upserts and import history.

## Scope
### In
- Define `CacheRepository` in `services/ports.py` with typed asynchronous signatures: `upsert_many(caches: Sequence[Cache]) -> UpsertResult`, `get(gc_code: str) -> Cache | None`, `get_user_data(gc_code: str) -> UserCacheData | None`, `set_user_data(gc_code: str, update: UserCacheDataUpdate) -> UserCacheData`, and `add_import_run(run: ImportRun) -> ImportRun`.
- Define `UpsertResult` with created, updated, and unchanged GC-code collections and a waypoint count.
- Implement the protocol in `adapters/db/cache_repository.py`. Compute `source_hash` using T-006's pure domain function; collapse duplicate GC codes in a batch with last occurrence winning before PostgreSQL upsert.
- Upsert logs by source log id. A `None` waypoint collection keeps stored waypoints; a provided collection replaces them; an empty collection clears them.
- Never update `UserCacheData` during an import. Partial user-data updates retain the untouched field; clearing corrected coordinates restores the original effective location and never changes `caches.location`.
- `updated_at` changes only when source content changes; `created_at` is immutable. Identical source content does not update timestamps.
- `CacheRepository` is extended by T-010 with `query(filter, sort, page)` and `markers(filter, cap)` methods; T-010 owns their query implementation and response behavior.
- Provide a fake under `backend/tests/unit/fakes/` and a shared behavior suite at `backend/tests/shared/cache_repository_suite.py`, run for the fake and PostGIS repository.
- Add migration support only if repository needs a schema change; every change has a tested downgrade.

### Out
- Domain and initial schema definitions (T-006).
- GPX parsing (T-007).
- Import orchestration and API/UI (T-008).
- Cache query filters (T-010).

## Implementation notes
- Each repository operation is asynchronous and owns its transaction boundary as documented. Import batch transaction and failure policy are specified by T-008.
- Use a shared suite fixture contract rather than calling DB-backed code from unit tests.
- Keep user-owned data in `user_cache_data`; imported cache source hashes exclude user data and persistence timestamps.

## Acceptance criteria
- [ ] AC1: Given a new cache, when upserted, then its GC code is created; when the same source content is upserted, then it is unchanged and timestamps are untouched; when a source field changes, then it is updated and `created_at` is preserved.
- [ ] AC2: Given a batch with duplicate GC codes, when upserted, then the last aggregate wins and PostgreSQL does not raise a duplicate conflict error.
- [ ] AC3: Given logs with overlapping source IDs, when re-imported, then log IDs are deduplicated and changed log content is updated.
- [ ] AC4: Given `waypoints=None`, a non-empty waypoint set, or an empty set, when upserted, then stored waypoints are kept, replaced, or cleared respectively.
- [ ] AC5: Given a note and corrected coordinates, when import upsert runs, then both survive; when only one user-data field is updated, then the other is retained; clearing correction restores the original location without changing `caches.location`.
- [ ] AC6: Given both fake and PostGIS repositories, when the shared behavior suite runs, then both satisfy AC1–AC5 and persist an `ImportRun` whose errors round-trip as JSON.

## Test plan
| AC | Test level | Test (file / name) |
|---|---|---|
| AC1–AC5 | shared behavior | `backend/tests/shared/cache_repository_suite.py` with unit fake and integration PostGIS fixtures |
| AC6 | integration | `backend/tests/integration/repositories/test_cache_repository.py` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_Filled in by the implementer: summary, deviations, follow-up tickets created._
