# T-008: Import service, API, and UI

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-007
- **Requirements:** IMP-1, IMP-4, IMP-6, IMP-7
- **Related ADRs:** ADR-0003

## Goal
The user uploads PQ files in the UI and sees an import summary. The data ends up in the database, and the import history is visible.

## Scope
### In
- `services/import_service.py`: `ImportService(source_factory, repo)`. It consumes the `CacheSource`, upserts in batches (500), records an `ImportRun`, and returns a summary.
- `POST /api/v1/imports` (multipart, many files, max 50 MB each; configurable). Files are streamed to a temp dir and deleted afterwards.
- `GET /api/v1/imports` lists the history, newest first.
- The import is synchronous (fine for 1,000–10,000 caches). Document the limit in code.
- Frontend `features/import`: a drag-and-drop file zone, a progress or busy state, a summary card (created, updated, unchanged, waypoints, errors with expandable details), and a history table. Invalidate the cache queries when it finishes.
- Run `api:gen`.

### Out
- Background jobs or progress streaming.

## Acceptance criteria
- [ ] AC1: Uploading the `with_waypoints.zip` fixture returns 201 with correct counts and persists the caches and waypoints.
- [ ] AC2: Re-uploading the same file reports all caches as `unchanged`.
- [ ] AC3: After setting a note or corrected coordinates in the DB, re-importing keeps them (end-to-end through the API).
- [ ] AC4: Uploading `one_corrupt_entry.gpx` returns 201. The summary lists one error, and the other caches are imported.
- [ ] AC5: Uploading an invalid file type or an oversized file returns 4xx problem+json.
- [ ] AC6: The UI shows the summary and the history. Component tests cover success, partial errors, and server error.
- [ ] AC7: The e2e smoke test is extended: import a fixture through the UI and see the summary.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC5 | integration (API + PostGIS) | `tests/integration/api/test_imports.py` |
| service logic | unit (fake repo, fake source) | `tests/unit/services/test_import_service.py` |
| AC6 | component | `src/features/import/*.test.tsx` |
| AC7 | e2e | `e2e/import.spec.ts` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
