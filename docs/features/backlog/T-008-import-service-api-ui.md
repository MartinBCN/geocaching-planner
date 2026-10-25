# T-008: Import service, API, and UI

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-007, T-024
- **Requirements:** IMP-1, IMP-4, IMP-5, IMP-6, IMP-7
- **Related ADRs:** ADR-0003
- **Reviews:** [Council review 1](../../reviews/features/T-008-import-service-api-ui-review-1.md)

## Goal
The user uploads Pocket Query files at `/import`, sees an accurate summary including logs and warnings, and can review import history.

## Context
T-006 defines the cache aggregate, schema, and content hash. T-024 supplies the async `CacheRepository` protocol and its PostGIS adapter. T-007 supplies named source files, parsed cache/warning/error results, and synthetic fixtures.

## Scope
### In
- `services/import_service.py`: `ImportService(source_factory, repo)`. It consumes the `CacheSource` off the event loop, upserts in batches (500), records an `ImportRun`, and returns a summary.
- `CacheSource` exposes `source_name` (`"pq"` for the Pocket Query parser); use it for `Cache.source` and `ImportRun.source` rather than hard-coding source identity in import orchestration.
- `CacheRepository` protocol in `services/ports.py` and implementation in `adapters/db/cache_repository.py` are delivered by T-024. Each batch commits in its own transaction. On parse or persistence failure, persist an `ImportRun` with partial counts in a separate transaction when the database remains available; propagate persistence failures explicitly.
- Persist `CacheLog` keyed by source log id; re-import never duplicates a log. Waypoint `None` preserves existing waypoints, a supplied set replaces them, and an empty set clears them.
- `ImportRun` stores counts for created, updated, unchanged, and waypoints. `errors` JSON stores parse errors and warnings, each with severity and parse context; update spec §7.
- One multi-file `POST /api/v1/imports` request creates one `ImportRun` covering all submitted filenames and aggregate counts.
- `POST /api/v1/imports` (multipart, many named `.gpx`/`.zip` files; `python-multipart`; max 50 MB per input, configured by `IMPORT_MAX_FILE_MB`; total archive expanded size capped at 500 MB). Stage files under generated names in a temporary directory; never use client filenames as paths. Always clean up on success and failure.
- Validate all uploaded input types and sizes before processing: unsupported extension/content returns 415, over-limit input returns 413, and neither imports any files. A valid GPX with malformed entries returns 201 with per-entry errors; mixed parse success is partial success.
- `GET /api/v1/imports` lists the history, newest first.
- The import is synchronous (fine for 1,000–10,000 caches). Document the limit in code.
- Frontend `features/import` at `/import`, with top-level nav entry, drag-and-drop and keyboard-accessible “Choose files…” button (`accept=".gpx,.zip"`, `multiple`). Show filenames and “Importing…”, disable controls and warn before leaving while active. Summary shows filenames, timestamp, counts, errors and warnings; history is newest first with date, files, counts and expandable errors/warnings. Empty history has an explanatory state.
- Invalidate `['imports']` and `['caches']` TanStack Query prefixes after completion; cache query keys in later tickets must begin with `['caches', ...]`.
- Run `api:gen`.

### Out
- Background jobs or progress streaming.

## Acceptance criteria
- [ ] AC1: Given the synthetic `with_waypoints.zip` fixture contains 3 caches, 2 additional waypoints, and 2 logs, when uploaded, then `POST /api/v1/imports` returns 201 with `created=3`, `updated=0`, `unchanged=0`, `waypoints=2`, persists all records, and returns the filenames and run timestamp.
- [ ] AC2: Given the same fixture is uploaded again with unchanged source fields, logs, and waypoints, when imported, then `created=0`, `updated=0`, `unchanged=3`, existing `updated_at` values remain unchanged, and no log duplicates are created.
- [ ] AC3: Given one cache's name is changed in a variant fixture, when re-imported, then it reports `updated=1`; given both note and corrected coordinates are stored through the repository, then re-import preserves both.
- [ ] AC4: Given `<pq>.gpx` and `<pq>-wpts.gpx` are uploaded together, when imported, then matching waypoints are stored; a waypoint-only upload reports unmatched waypoints as warnings rather than attaching them to an arbitrary cache.
- [ ] AC5: Given `one_corrupt_entry.gpx` contains three entries with the middle one malformed, when imported, then the endpoint returns 201, one file/entry error is reported, and the valid entries are persisted.
- [ ] AC6: Given an unsupported extension/content, when uploaded, then the endpoint returns 415 `application/problem+json` and imports nothing; given an input over `IMPORT_MAX_FILE_MB`, then it returns 413 problem+json and imports nothing.
- [ ] AC7: Given a mixed request with one valid file and one file failing pre-validation, when uploaded, then the whole request is rejected before import; given valid files with individual parse errors, then valid entries are imported and represented in the 201 summary.
- [ ] AC8: Given 1,200 parsed caches, when the service runs, then repository upsert is called in batches of 500, 500, and 200; an `ImportRun` records partial counts on a batch failure when the database remains available.
- [ ] AC9: Given import history exists, when `GET /api/v1/imports` is requested, then results are newest first and include filenames, timestamps, counts, and errors; an empty history is represented explicitly.
- [ ] AC10: Given upload processing succeeds or fails, when it completes, then its temporary directory is removed.
- [ ] AC11: Given import completes in the UI, when queries are observed, then `['imports']` and `['caches']` are invalidated; during upload, buttons are disabled, filenames and “Importing…” are shown, and navigation warns before leaving.
- [ ] AC12: Given a 1,000-cache synthetic PQ, when imported through the API against PostGIS after migrations, then the complete request finishes under 10 seconds (`slow` marker).
- [ ] AC13: Given component tests, when API responses represent success, partial errors/warnings, or server failure, then the UI renders the appropriate summary and actionable error details.
- [ ] AC14: Given the import page, when navigated to through `/import`, then the nav entry and keyboard-focusable “Choose files…” control are available and selecting multiple files works.
- [ ] AC15: Given the synthetic fixture is uploaded through the UI against a reset test database, when import completes, then the page shows `3 created`, `2 waypoints`, and the filenames.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC10, AC12 | integration (API + PostGIS) | `backend/tests/integration/api/test_imports.py` and `backend/tests/integration/perf/test_import_perf.py` |
| AC8 | unit | `backend/tests/unit/services/test_import_service.py::test_upserts_in_batches_and_records_partial_counts` |
| AC11, AC13–AC14 | component | `frontend/src/features/import/ImportPage.test.tsx` |
| AC15 | e2e | `frontend/e2e/import.spec.ts::imports_synthetic_pq_and_shows_summary` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] `mise run api:gen` was run and the generated client was committed
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Implementation notes
- Use the accepted Problem JSON error contract from T-002. Parser warnings and errors keep `severity`, `file`, `gc_code`, `line`, `code`, and `message`; the UI displays warnings separately.
- New staged files use generated safe names in `TemporaryDirectory`; preserve the original filename only as metadata. Enforce per-input size before staging and archive expanded-size limits during parsing.
- The API validates every file's type and size before starting import. Malformed GPX entries are not pre-validation failures; they are reported in partial-success summaries.
- The service uses T-024's async repository. Synchronous parser work must be offloaded from the async request path. API validation names `python-multipart` and documents `IMPORT_MAX_FILE_MB` default 50 in `.env.example`.
- The parser's `source_name` is persisted on every imported cache and corresponding `ImportRun`.
- Add `IMPORT_MAX_FILE_MB` to backend configuration and run `mise run api:gen`; commit the regenerated client.

## Completion notes
_…_
