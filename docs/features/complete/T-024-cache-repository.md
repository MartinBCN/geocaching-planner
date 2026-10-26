# T-024: Cache repository and persistence behavior

- **Status:** Complete
- **Milestone:** M1
- **Depends on:** T-006
- **Requirements:** IMP-4, IMP-5, IMP-6 (persistence), CAC-4, CAC-5 (persistence)
- **Related ADRs:** ADR-0003, ADR-0006
- **Reviews:** [Council review 1](../../reviews/features/T-024-cache-repository-review-1.md)

## Goal
Persist cache aggregates through one asynchronous repository contract that is shared by imports, queries, and unit tests.

## Context
T-006 provides frozen domain aggregates and the database schema. `Cache` is the aggregate root and carries its logs and optional waypoint set. T-007 parses cache aggregates; T-008 depends on this ticket for repository upserts and import history.

## Scope
### In
- Define `CacheRepository` in `services/ports.py` with typed asynchronous signatures: `upsert_many(caches: Sequence[Cache]) -> UpsertResult`, `get(gc_code: str) -> Cache | None`, `get_user_data(gc_code: str) -> UserCacheData | None`, `set_user_data(gc_code: str, update: UserCacheDataUpdate) -> UserCacheData`, and `add_import_run(run: ImportRun) -> ImportRun`.
- Define `UserCacheDataUpdate`: omitted fields remain unchanged; explicit `None` clears a field (a note clears to `""`); at least one field must be supplied.
- Define `UpsertResult` with created, updated, and unchanged GC-code collections and a waypoint count.
- Implement the protocol in `adapters/db/cache_repository.py`. Compute `source_hash` using T-006's pure domain function; collapse duplicate GC codes in a batch with last occurrence winning before PostgreSQL upsert.
- Upsert logs by source log id. A `None` waypoint collection keeps stored waypoints; a provided collection replaces them; an empty collection clears them.
- Never update `UserCacheData` during an import. Partial user-data updates retain the untouched field; clearing corrected coordinates restores the original effective location and never changes `caches.location`.
- `updated_at` changes only when source content changes; `created_at` is immutable. Identical source content does not update timestamps.
- Transaction boundaries: each `upsert_many` call is atomic and commits once (T-008 calls once per 500-cache batch); `set_user_data` and `add_import_run` commit independently; `get` and `get_user_data` are read-only.
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
- [x] AC1: Given a new cache, when upserted, then its GC code is created; when the same source content is upserted, then it is unchanged and timestamps are untouched; when a source field changes, then it is updated, `created_at` is preserved, and `updated_at` changes.
- [x] AC2: Given a batch with duplicate GC codes, when upserted, then the last aggregate wins and PostgreSQL does not raise a duplicate conflict error.
- [x] AC3: Given logs with overlapping source IDs, when re-imported, then log IDs are deduplicated and changed log content is updated.
- [x] AC4: Given `waypoints=None`, a non-empty waypoint set, or an empty set, when upserted, then stored waypoints are kept, replaced, or cleared respectively.
- [x] AC5: Given a note and corrected coordinates, when import upsert runs, then both survive; when only one user-data field is updated, then the other is retained; omitted update fields are unchanged and explicit `None` clears the value (a note clears to `""`); clearing correction restores the original effective location and never changes `caches.location`.
- [x] AC6: Given both fake and PostGIS repositories, when the shared behavior suite runs, then both satisfy AC1–AC5 and round-trip an `ImportRun`; the PostGIS integration test also verifies that `errors` round-trip as JSON.

## Test plan
| AC | Test level | Test (file / name) |
|---|---|---|
| AC1–AC5 | shared behavior | `backend/tests/shared/cache_repository_suite.py`, run by unit fake and PostGIS integration wrappers |
| AC6 | unit + integration | shared import-run behavior plus `backend/tests/integration/test_cache_repository.py::test_import_run_errors_round_trip_as_json` |

## Definition of Done
- [x] All ACs are covered by automated tests
- [x] `mise run check` is green
- [x] Docs are updated (README / spec / AGENTS / ADR if needed)
- [x] There are no TODOs without a linked backlog ticket
- [x] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
- Added the typed cache repository protocol and PostgreSQL implementation, including cache/log/waypoint upserts, partial user-data updates, and import-run persistence. No schema change was needed.
- Added a fake repository and a shared behavior suite, run against both the fake and PostGIS adapter; covered `UserCacheDataUpdate` validation and JSONB error round-tripping.
- Clarified partial-update, transaction, timestamp, and test responsibilities in this ticket in response to its advisory review. No follow-up tickets were needed.
- `mise run check` passes, including the full backend suite and PostGIS integration tests.
