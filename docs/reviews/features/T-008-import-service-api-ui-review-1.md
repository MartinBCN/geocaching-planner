# Council review: T-008-import-service-api-ui (review 1)

- **Target:** `docs/features/backlog/T-008-import-service-api-ui.md` (Ticket, status at review time: Ready)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 9 Major · 11 Minor · 3 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve with changes · Quality & Delivery: Approve with changes

## Context provided
- README.md
- AGENTS.md
- docs/specification.md
- docs/adr/0001-record-architecture-decisions.md
- docs/adr/0002-local-single-user-deployment.md
- docs/adr/0003-gpx-first-pluggable-cache-source.md
- docs/adr/0004-brouter-routing.md
- docs/adr/0005-frontend-react-maplibre.md
- docs/adr/0006-postgis.md
- docs/adr/0007-tooling-uv-mise-monorepo.md
- docs/adr/0008-quality-gates.md
- docs/adr/0009-ticket-workflow.md
- docs/adr/0010-council-review.md
- docs/features/backlog/T-007-pq-gpx-parser.md
- docs/features/TEMPLATE.md
- docs/features/README.md

**Anomalies:** none

## Top actions
1. Define the persistence contract and what T-006 already provides: the `CacheRepository` protocol and adapter, the transaction and batch boundaries, the waypoint replacement rule, the `ImportRun` schema including a waypoint count (with a migration if needed), and log persistence with IMP-5 added to Requirements. Write all of it into the ticket (#1, #2, #3; ARC-1, ARC-2, ARC-3, QDE-5).
2. Make the import ACs verifiable. Give exact fixture counts, define `unchanged` versus `updated`, add an `updated` path AC, and add ACs for history ordering, temp-file cleanup, batching, and query invalidation (#4, #7; QDE-1, QDE-3).
3. Decide the error contract for uploads: the status codes for type, size, and content errors, and whether a mixed multi-file request is all-or-nothing or a partial import. Then split AC5 to match (#6; ARC-7, PRD-2, QDE-2).
4. Add an NFR-1 end-to-end performance AC: a 1,000-cache PQ imported through the API against PostGIS in under 10 s (#5; ARC-4, QDE-4).
5. Specify the UI entry point and accessibility: an `/import` route with a nav entry, plus a keyboard-accessible "Choose files…" button next to the drop zone (#8, #9; PRD-1, PRD-3).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | ARC-2, QDE-5 | T-007 Out: "Persisting data (T-008)." / T-008: "**Requirements:** IMP-1, IMP-4, IMP-6, IMP-7" | The parser produces logs, but no ticket persists them. IMP-5 (dedup by log id) is missing, even though CAC-3 needs recent logs. | Add IMP-5 to Requirements. Add a scope item to upsert `CacheLog` keyed on the source log id, and an AC that re-import does not duplicate logs. Alternatively, move this explicitly to Out and name the owning ticket. |
| 2 | Major | ARC-3, QDE-5 | Spec §7: "`created`, `updated`, `unchanged`, `errors` (jsonb)" vs. "summary card (created, updated, unchanged, waypoints, errors" | `ImportRun` has no waypoints field, and the ticket does not say whether T-006 creates the `import_run` table or the repository methods. | Add a Context section that states what T-006 delivers. If the waypoint count must be persisted, add an Alembic migration (`import_run.waypoints`) with a tested downgrade, and update spec §7 in the same PR. |
| 3 | Major | ARC-1, QDE-5 | Scope/In: "upserts in batches (500), records an `ImportRun`, and returns a summary" | The `CacheRepository` protocol and adapter are not named. The rules for waypoint replacement, transaction boundaries (one transaction or one per batch), and failure behavior (is an ImportRun written on failure?) are not stated. | Define the `CacheRepository` protocol in `services/ports.py` (`upsert_caches`, `add_import_run`) with an adapter in `adapters/db/`. Waypoints of an updated cache are replaced. Each batch is its own transaction. The ImportRun is always written in `finally` with partial counts. Give the `source_factory` signature. |
| 4 | Major | QDE-1, ARC-1 | AC1: "returns 201 with correct counts"; AC2: "reports all caches as `unchanged`" | "Correct counts" is not defined. The `unchanged` versus `updated` rule is not given. No AC or fixture covers the `updated` path (IMP-4, IMP-6). | Rewrite AC1 and AC2 with exact fixture counts. Add AC2b, where a variant fixture with one changed name gives `updated=1`. Define `unchanged` as all source fields, waypoints, and logs equal, timestamps excluded, with `updated_at` not touched. |
| 5 | Major | ARC-4, QDE-4 | Spec NFR-1: "Importing a 1,000-cache PQ takes under 10 s." | No AC checks the end-to-end import budget. T-007 only measures parsing. | Add an AC: a generated 1,000-cache PQ imported through `POST /api/v1/imports` against PostGIS in under 10 s (`slow` marker). Prefer a set-based `INSERT … ON CONFLICT … DO UPDATE … WHERE <differs>`. |
| 6 | Major | PRD-2, QDE-2, ARC-7 | AC5: "Uploading an invalid file type or an oversized file returns 4xx problem+json." | "4xx" is not a specific code, and "invalid type" is not defined. It conflicts with T-007 AC4 (a non-GPX file gives a file-level error). Mixed multi-file batches are undefined. IMP-7 requires "a clear error". | Decide and state the rule: the status codes for type and size rejection, a `.gpx` with broken content → 201 with a file-level error, and partial versus all-or-nothing for mixed batches. Define the error item schema `{file, gc_code?, line?, message}`. Split AC5 and add a mixed-batch AC. See Dissent for the competing proposals. |
| 7 | Major | QDE-3 | Scope In: "`GET /api/v1/imports` lists the history, newest first."; "Files are streamed to a temp dir and deleted afterwards." | History ordering, temp-file cleanup on success and failure, batch size 500, the busy state, and query invalidation have no AC. This violates AGENTS §2.3. | Add ACs: history returned newest first with filenames and counts. The temp dir is empty after both a successful and a failed import. 1,200 caches → 3 upsert calls. A component AC for the busy state and query invalidation. |
| 8 | Major | PRD-1 | Scope/In: "a drag-and-drop file zone" | Drag-and-drop is the only way to add files, so keyboard users cannot import at all. | Add a keyboard-focusable "Choose files…" button (native input, `accept=".gpx,.zip"`, `multiple`) and a component test that selects files with the keyboard. |
| 9 | Major | PRD-3 | Goal: "The user uploads PQ files in the UI and sees an import summary." | No route or nav entry is defined, and there is no next step after a successful import. | Name the route `/import` with a top-level nav entry. Note in Completion notes that the success card will link to the map once T-011 exists. |
| 10 | Minor | ARC-5 | Scope/In: "Files are streamed to a temp dir and deleted afterwards." | Client filenames allow path traversal. ZIP expansion has no limit. The layer that owns staging is unclear. | Use generated names in a `TemporaryDirectory`. Staging lives in an API dependency or adapter, and the service receives `Path`s. Add a configurable cap on total uncompressed size. |
| 11 | Minor | ARC-6, QDE-8 | Scope/In: "(multipart, many files, max 50 MB each; configurable)" | `python-multipart` is an unlisted runtime dependency (AGENTS §3). The setting is unnamed (NFR-4). There is no limit on the number of files. | Name the `python-multipart` dependency. Add the setting `IMPORT_MAX_FILE_MB` (default 50) to `.env.example`. Optionally cap the number of files per request. State that the drop zone needs no new frontend library. |
| 12 | Minor | PRD-4 | Scope/In: "a progress or busy state" with "The import is synchronous" | Long imports give no feedback. Double submits and navigating away mid-import are not handled. | Show the file names and an "Importing…" message. Disable the inputs while the import runs. Warn the user before they leave the page during an import. |
| 13 | Minor | PRD-5 | Scope/In: "a history table" | The history table has no empty state, no defined columns, and no way to open past errors again. | Add an empty-state text. Columns: date/time, files, created, updated, unchanged, error count. Make the errors of each run expandable. |
| 14 | Minor | PRD-6 | Scope/In: "errors with expandable details" | The content of an error entry is undefined. T-007 warnings (orphan waypoints, unknown types) are never shown. | Each error row shows the file, the GC code or line, and the reason. Decide whether warnings appear as a separate "Warnings (n)" group. |
| 15 | Minor | PRD-7 | AC1: "Uploading the `with_waypoints.zip` fixture" | No AC checks that `<pq>.gpx` and `<pq>-wpts.gpx` uploaded as separate files link together (IMP-3). | Add an AC for two separate files in one request. |
| 16 | Minor | QDE-6 | AC3: "After setting a note or corrected coordinates in the DB, re-importing keeps them (end-to-end through the API)." | The user-data API only arrives in T-013, so "end-to-end through the API" conflicts with "in the DB". The word "or" lets the test cover only one field. | Seed both the note and the corrected location through the repository, re-import through the API, and assert that both are unchanged. |
| 17 | Minor | QDE-7 | Scope In: "Invalidate the cache queries when it finishes." | The cache queries arrive in T-010 and T-011, so this ticket has no key to invalidate yet. | Fix the contract: invalidate the `['imports']` and `['caches']` prefixes, and require later queries to use the `['caches', …]` prefix. Test it with a spy. |
| 18 | Minor | QDE-9 | AC6: "Component tests cover success, partial errors, and server error."; AC7: "import a fixture through the UI and see the summary." | AC6 is a compound AC without observable assertions. AC7 does not name the fixture or its path, the expected text, or a DB reset step. | Split AC6 into three Given/When/Then ACs using MSW. For AC7, name `with_waypoints.zip`, its path, the expected count text, and a DB reset step before the suite. |
| 19 | Minor | QDE-10 | Header: "- **Related ADRs:** ADR-0003"; DoD: "All ACs are covered" | The `Reviews:` line, Context, and Implementation notes sections are missing, and the DoD is weaker than the template's. | Add the missing sections and copy the template DoD verbatim. |
| 20 | Minor | QDE-11 | The whole of Scope In | The ticket is large for one PR (ADR-0009), especially once the missing ACs are added. | Optional split: T-008a for the service, API, and `api:gen`; T-008b for the UI and e2e, depending on T-008a. |
| 21 | Nit | ARC-8 | T-007: "`iter_caches() -> Iterator[CacheParseResult]`" | The source identifier for `Cache.source` and `ImportRun.source` is not exposed, so the service would hard-code `"pq"`. | Add `source.name` to the protocol (coordinate with T-007), or have the factory supply it. |
| 22 | Nit | PRD-8 | Scope/In: "summary card (created, updated, unchanged, waypoints, errors…)" | The summary card does not show which files it covers or when the import ran. | Show the file names and the timestamp on the summary card. |
| 23 | Nit | QDE-12 | Scope In: "Run `api:gen`." | This is not the exact command, and it does not say to commit the generated client. | "Run `mise run api:gen` and commit the regenerated client." |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Severity of the upload error contract (#6) | ARC-7: Minor. It is a contract detail that shapes the OpenAPI schema. | PRD-2, QDE-2: Major. "4xx" cannot be verified, the AC conflicts with T-007 AC4, and the user can lose a whole batch. The higher severity, Major, was kept. |
| How to handle a rejected file (#6) | ARC-7: a type or size failure → 422 problem+json, and nothing is imported. Parse errors → 201 with a file-level error. | QDE-2: extension → 415, size → 413, broken content → 201 with an error, with all-or-nothing left to the author. PRD-2: pre-validate in the browser, import the valid files, and use 4xx only when no file in the request is usable. |

## Open questions for the author
- Does T-006 already create the `import_run` table and the `CacheRepository` protocol with a bulk upsert? (ARC, QDE)
- Which ticket persists PQ logs (IMP-5)? (QDE; see ARC-2)
- If a later PQ has fewer additional waypoints for a cache, are the missing ones deleted? This affects what `unchanged` means. (ARC)
- Does a multi-file upload produce one `ImportRun` or one per file? (ARC)
- If one file in a multi-file request is rejected, does the whole request fail? (QDE, PRD)
- If a DB error occurs midway (e.g. batch 3 of 5), are earlier batches rolled back, and is an `ImportRun` still recorded? (QDE)
- If a `-wpts.gpx` file is uploaded alone, should its waypoints link to caches already stored, or be reported as orphans? (PRD)
- Caches that are archived or drop out of a PQ keep their stale data. Should the summary or history show "last seen in import", or is that a follow-up? (PRD)
- Is the 50 MB limit shown in the UI, or only enforced by the server? (PRD)

## Strengths
- `ImportService(source_factory, repo)` injects both ports, which keeps `services/` independent of adapters and lets the tests use fakes (spec §6).
- AC3 protects the core IMP-4/ADR-0003 guarantee that an import never overwrites user data, which is what users trust most.
- Partial success on a corrupt entry (AC4) and an explicit `unchanged` count on re-import (AC2) match how PQ users actually work.
- The synchronous import is an explicit, reversible choice, and Scope Out excludes background jobs and progress streaming.
- The ticket reuses the synthetic T-007 fixtures and has a test plan at every level: unit, integration, component, and e2e.

## Process notes
- All three custom agent types were available, so no fallback was used. All three reviews met the output contract, and no re-prompts were needed.
- The target status was already `Ready` at review time, with no `Reviews:` line. This is noted for information only and is covered by #19.
- Several out-of-lane notes from members (synchronous timeouts for 10k caches, T-010 query ordering, AC3 setup path) are already covered by #5, #12, #16, and #17.

---

## Appendix A: Software Architect (raw)
## Software Architect review: T-008-import-service-api-ui.md

**Member verdict:** Approve with changes
**Rationale:** The ticket follows ADR-0003 and the spec's layering, but it leaves the repository contract, log persistence, the ImportRun schema, and the NFR-1 import budget undefined, so the implementation will likely need rework.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Scope/In: "upserts in batches (500), records an `ImportRun`, and returns a summary" | The ticket names a `repo` but does not name the `CacheRepository` protocol (spec §6) or the SQLAlchemy adapter that implements it. It also leaves the core persistence rules open: how "unchanged" is detected, whether waypoints missing from a re-import are deleted or kept, and the transaction boundary. One transaction, or one per batch? Is the ImportRun written if a batch fails? An agent will make these choices without guidance, and the IMP-4 upsert rules end up hidden inside an adapter. | Add: "**Must:** define the `CacheRepository` protocol in `services/ports.py` with `upsert_caches(batch) -> UpsertCounts` and `add_import_run(run)`, and implement it in `adapters/db/cache_repository.py`. 'Unchanged' means all source fields, waypoints, and logs are equal; `updated_at` is not touched. Waypoints of an updated cache are replaced by the incoming set. Each batch commits in its own transaction, and the ImportRun is always written in `finally` with partial counts." Adjust the rules if you choose differently, but write them down. |
| ARC-2 | Major | T-007 Out: "Persisting data (T-008)." / T-008 header: "**Requirements:** IMP-1, IMP-4, IMP-6, IMP-7" | T-007 hands all persistence to this ticket, and the parser produces logs. But T-008 does not list IMP-5 ("Logs in the PQ are stored, deduplicated by log id"), and no scope item or AC covers logs. As written, no ticket persists logs, yet CAC-3 needs "recent logs". | Add IMP-5 to Requirements. Add the scope item "Upsert `CacheLog` keyed on the source log id (no duplicates on re-import)" and an AC: "Re-importing a fixture does not duplicate logs." |
| ARC-3 | Major | Spec §7: "`created`, `updated`, `unchanged`, `errors` (jsonb)" vs. target: "summary card (created, updated, unchanged, waypoints, errors" | IMP-6 and the UI need a waypoint count, and the history table shows past runs. The `ImportRun` entity in §7 has no `waypoints` field, and the ticket mentions no migration. Either history cannot show waypoints, or the implementer changes the schema without a decision. The ticket also does not say whether T-006 already created the `import_run` table. | State whether T-006 creates the `import_run` table. If the waypoint count must be persisted, add "Alembic migration adding `import_run.waypoints` (int, default 0), with downgrade tested" and update spec §7 in the same PR. |
| ARC-4 | Major | Scope/In: "The import is synchronous (fine for 1,000–10,000 caches)." vs. spec NFR-1: "Importing a 1,000-cache PQ takes under 10 s." | This is the only ticket that can check the end-to-end import budget in NFR-1. T-007 only covers parsing (5k caches in under 5 s). The persistence design (batch size, upsert strategy, change detection) decides whether the 10 s target is met, but nothing checks it, so a slow per-row ORM upsert would go unnoticed. | Add an AC: "Importing a generated 1,000-cache PQ through `POST /api/v1/imports` against PostGIS completes in under 10 s (integration test, `slow` marker)." Prefer a set-based `INSERT … ON CONFLICT (gc_code) DO UPDATE … WHERE <source fields differ>` in the adapter. |
| ARC-5 | Minor | Scope/In: "Files are streamed to a temp dir and deleted afterwards." | Client-supplied filenames written to disk allow path traversal unless they are sanitized. The 50 MB limit applies to the compressed upload, so a ZIP can still expand without bound when T-007 parses it. The ticket also does not say which layer owns staging. `api/` must stay free of logic, and I/O belongs in adapters. | Add: "Staged files use generated names in a `TemporaryDirectory`; the original filename is kept only as metadata. Staging lives in an API dependency or adapter, and the service receives `Path`s through `source_factory`. The total uncompressed ZIP size is capped by a configurable limit and checked before extraction." |
| ARC-6 | Minor | Scope/In: "`POST /api/v1/imports` (multipart, many files, max 50 MB each; configurable)" / AGENTS §3: "A new runtime dependency is not mentioned in the ticket or the ADRs." | FastAPI multipart parsing needs `python-multipart`, and no ticket or ADR mentions it. AGENTS §3 would make the agent stop. The "configurable" limit also has no settings name, which NFR-4 requires. | Add: "New runtime dependency: `python-multipart`. Setting `IMPORT_MAX_FILE_MB` (default 50) in pydantic-settings and `.env.example`." Also state that the drop zone uses native drag-and-drop events with no new frontend library. |
| ARC-7 | Minor | AC5: "Uploading an invalid file type or an oversized file returns 4xx problem+json." vs. IMP-7: "Malformed files fail with a clear error." | The API contract does not cover a file that has a valid extension but broken content (`not_a_gpx.txt` renamed, a truncated ZIP). It also does not say what happens when one of several uploaded files is bad: 4xx for the whole request, or 201 with a file-level error in the summary. This shapes the OpenAPI schema and the generated client. | Specify: "File-type and size checks (extension or magic bytes) → 422 problem+json, and nothing is imported. File-level parse errors after acceptance → 201, with the error recorded in `ImportRun.errors` (`{file, gc_code?, line?, message}`)." Define that error item schema in the response model. |
| ARC-8 | Nit | Spec §7: "`source`, `source_updated_at`" / T-007: "`iter_caches() -> Iterator[CacheParseResult]`" | `Cache.source` and `ImportRun.source` need a source identifier, but the `CacheSource` protocol does not expose one. The service would have to hard-code `"pq"`, which works against IMP-8. | Have the service read `source.name` (add it to the protocol, coordinating with T-007), or state that the factory supplies it. |

### Strengths
- `ImportService(source_factory, repo)` injects both ports, which keeps `services/` independent of adapters and lets the unit tests use fakes, as spec §6 requires.
- AC3 tests end to end, through the API, that an import never overwrites `UserCacheData`. This directly protects the IMP-4/ADR-0003 invariant.
- Making the import synchronous is an explicit choice, background jobs are listed as out of scope, and the limit is documented in code. The decision is easy to reverse later without an ADR.

### Open questions for the author
- Does T-006 already create the `import_run` table and the `CacheRepository` protocol? If so, ARC-1 and ARC-3 shrink to a reference to it.
- When a cache comes back in a later PQ with fewer additional waypoints, should the missing waypoints be deleted? This also affects what "unchanged" means.
- Does a multi-file upload produce one `ImportRun` (spec: `filenames` is plural) or one run per file?

### Out of my lane
- QDE: The template sections "Context", "Implementation notes", and the "Reviews:" line are missing, and the status is already `Ready` without a linked review.
- QDE: The ticket spans the backend service, the API, the frontend feature, and e2e. Check whether it fits one PR (ADR-0009).
- QDE: "Invalidate the cache queries" refers to queries from T-010, which does not depend on T-008. Check the order, or limit invalidation to the import history query.
- QDE: AC3 sets up its state "in the DB" because the user-data API (T-013) comes later. Make sure the test setup path is clear.
- PRD: The UI shows nothing for long synchronous imports (10k caches) beyond a busy state. Check whether that is acceptable UX.

## Appendix B: Product Designer (raw)
## Product Designer review: T-008-import-service-api-ui.md

**Member verdict:** Approve with changes
**Rationale:** The ticket covers the first step of the main user flow and the backend behavior is well specified, but the UI is underspecified: there is no entry or exit point, the action needs a mouse, a mixed batch with one bad file has no defined result, and some UI states are missing.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Major | Scope/In: "a drag-and-drop file zone" | The only way to add files is dragging them. A keyboard user can't import at all, even though this is the first step of the whole flow. Many users also expect a "Browse…" file picker. | Change it to: "A drop zone that also has a keyboard-focusable 'Choose files…' button (native file input, `accept=".gpx,.zip"`, `multiple`)." Add a component test that selects files with the keyboard. |
| PRD-2 | Major | AC5: "Uploading an invalid file type or an oversized file returns 4xx problem+json." | The user uploads "one or more" files (IMP-1). The ticket doesn't say what happens when 5 good PQs are uploaded together with one `.txt` or one oversized file. If the whole request is rejected, the user loses the batch. If the bad file is skipped, it must be reported. IMP-7 also asks for "a clear error". | State the rule explicitly. Recommended: check type and size in the browser before upload and list the rejected files by name, with the reason and the limit (e.g. "max 50 MB"). On the server, report a malformed file as a file-level error in the summary while the other files still import. Use 4xx only when no file in the request is usable. Add an AC for the mixed batch. |
| PRD-3 | Major | Goal: "The user uploads PQ files in the UI and sees an import summary." | The ticket doesn't say where the import screen lives (route or nav entry), so later tickets can't link to it. It also doesn't say what the user does after a successful import. The map (T-011) comes later, so there is no next step yet. | Name the route and nav entry, e.g. `/import`, linked from the app's top-level navigation. Say that the success card's next-step link will point to the map when T-011 exists, and record that follow-up in Completion notes. |
| PRD-4 | Minor | Scope/In: "a progress or busy state" with "The import is synchronous" | The request is synchronous and has no progress, so a large batch shows a spinner with no feedback. The ticket also doesn't define what happens on a second click or when the user leaves the page mid-import. | Specify that the busy state shows the file names and an "Importing… this can take a minute for large PQs" message, that the drop zone and button are disabled while it runs, and that the browser warns before the user leaves the page during an import. |
| PRD-5 | Minor | Scope/In: "a history table" | There is no empty state for a first-time user. The ticket also doesn't define the table's columns or whether errors from past runs can be opened again. | Empty state: "No imports yet. Drop your Pocket Query .zip or .gpx files above." Columns: date/time, files, created, updated, unchanged, error count. Errors should be expandable for each run, because `ImportRun.errors` is stored. |
| PRD-6 | Minor | Scope/In: "errors with expandable details" | The ticket doesn't say what an error entry contains. T-007 gives "GC code or line info", and it also emits warnings ("Orphan waypoints are reported as warnings", unknown types → `Other`), which T-008 never shows. | Each error row should show the file name, the GC code or line, and the reason. Decide whether warnings appear in the summary, for example as a separate "Warnings (n)" group. |
| PRD-7 | Minor | AC1: "Uploading the `with_waypoints.zip` fixture" | GSAK users often unzip PQs and drop `<pqid>.gpx` and `<pqid>-wpts.gpx` as two separate files. IMP-3 names `*-wpts.gpx`, but no AC checks that the waypoints link across separate files in one upload. | Add an AC: "Uploading `<pq>.gpx` and `<pq>-wpts.gpx` as two files in one request links the waypoints to their caches." |
| PRD-8 | Nit | Scope/In: "summary card (created, updated, unchanged, waypoints, errors…)" | The summary doesn't show which files it covers or when the import ran. Data is "only as fresh as the user's last PQ download" (ADR-0003). | Show the file names and the timestamp on the summary card. |

### Strengths
- AC3 checks end to end, through the API, that notes and corrected coordinates survive a re-import. This is the GSAK trust guarantee users care about most (IMP-4).
- Partial success on a corrupt entry (AC4) and the clear "unchanged" count on re-import (AC2) match how experienced PQ users work.
- "Invalidate the cache queries when it finishes" means the list and map will refresh after an import without a manual reload.

### Open questions for the author
- If a user uploads only a `-wpts.gpx` for caches that are already in the database, should those waypoints link to the stored caches, or be reported as orphans?
- A cache that is archived or drops out of a PQ never shows up in later imports, so it stays in the database with old data. Should the summary or history make this visible (e.g. "last seen in import"), or is that a follow-up ticket?
- Is the 50 MB per-file limit shown to the user in the UI, or only enforced by the server?

### Out of my lane
- QDE: AC6 bundles three UI states into one AC, and AC5 covers two conditions. Consider splitting them. The ticket also has no Context or Implementation notes section from the template.
- ARC: The summary includes a waypoint count, but `ImportRun` in spec §7 has no waypoints field. Check whether the history can show it.
- QDE/ARC: Check a synchronous import of 10,000 caches against request timeouts. NFR-1 only gives a target for 1,000 caches (under 10 s).

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: T-008-import-service-api-ui.md

**Member verdict:** Approve with changes
**Rationale:** The ticket is a clear vertical slice with a test plan, but several ACs cannot be checked objectively ("correct counts", "4xx", undefined `unchanged`), half the scope has no AC, and the persistence prerequisites are unclear, so an agent would have to guess.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | AC1: "returns 201 with correct counts and persists the caches and waypoints"; AC2: "reports all caches as `unchanged`" | The ticket never says what the "correct counts" are. It also doesn't define when a cache counts as `unchanged` rather than `updated`. No AC or fixture covers the `updated` path, even though IMP-4 and IMP-6 require it. Without these, an agent can't write the test assertions and might choose a change-detection rule that differs from what you intend. | Add the fixture counts to the ticket and rewrite the ACs. **AC1:** "Given an empty DB, when `with_waypoints.zip` is POSTed to `/api/v1/imports`, then the response is 201 with `created=<N>, updated=0, unchanged=0, waypoints=<M>, errors=[]`, and the DB holds N caches and M waypoints." **AC2:** "Given AC1 is done, when the same file is POSTed again, then `created=0, updated=0, unchanged=N`." **New AC2b:** "Given AC1 is done, when a variant fixture with one changed cache name is imported, then `updated=1, unchanged=N-1`, and the stored name has changed." Define `unchanged` as "every source field is equal (timestamps excluded)". |
| QDE-2 | Major | AC5: "Uploading an invalid file type or an oversized file returns 4xx problem+json."; T-007 AC4: "A non-GPX file yields one file-level error and no crash." | "4xx" is not a specific status code. "Invalid file type" is not defined (extension? content?). It also conflicts with T-007: should `not_a_gpx.txt`, or a `.gpx` file with garbage inside, get a 4xx, or a 201 with a file-level error? And if a request has one bad file among several good ones, the ticket doesn't say whether to reject the whole request. | Split AC5 into three ACs. **AC5a:** "A file whose extension is not `.gpx` or `.zip` → 415, `Content-Type: application/problem+json`, nothing persisted, no `ImportRun`." **AC5b:** "A file larger than `import_max_file_mb` (set to 1 MB in the test) → 413 problem+json, and no temp file is left behind." **AC5c:** "A `.gpx` file with invalid content → 201, with one file-level error in `errors`." Also state whether a multi-file request is all-or-nothing. |
| QDE-3 | Major | Scope In: "`GET /api/v1/imports` lists the history, newest first."; "Files are streamed to a temp dir and deleted afterwards." | Several scope items have no AC and no test: history ordering and fields, temp-file cleanup (on success *and* on failure), batch size 500, the busy state, and query invalidation. Under AGENTS.md §2.3 ("Every acceptance criterion needs at least one automated test"), untested scope can regress silently. | Add ACs. **AC8:** "Given two imports, `GET /api/v1/imports` returns 2 runs ordered by `started_at` desc, each with filenames and counts." **AC9:** "After a successful and after a failed import, the configured temp dir is empty." **AC10 (unit):** "1,200 caches result in 3 repository upsert calls (500/500/200)." **AC11 (component):** "While the POST is pending, the drop zone is disabled and a busy indicator is shown. After success, the `['imports']` and `['caches']` query keys are invalidated." |
| QDE-4 | Major | spec NFR-1: "Importing a 1,000-cache PQ takes under 10 s." | This is the ticket that delivers end-to-end import, but no AC checks the NFR-1 threshold. T-007 AC7 only measures parsing. | Add **AC12:** "A generated 1,000-cache PQ imports through `POST /api/v1/imports` against testcontainers PostGIS in < 10 s (`@pytest.mark.slow`, `tests/integration/api/test_imports_perf.py`)." |
| QDE-5 | Major | Requirements: "IMP-1, IMP-4, IMP-6, IMP-7"; spec §7 ImportRun: "`created`, `updated`, `unchanged`, `errors` (jsonb)"; IMP-5: "Logs in the PQ are stored, deduplicated by log id." | The ticket doesn't say which persistence pieces already exist. It is unclear whether the `ImportRun` table, the `CacheRepository` bulk-upsert method, and log storage come from T-006 or must be built here. Two specific gaps: the spec's `ImportRun` has no `waypoints` field, although the summary needs one, and no ticket in the context covers IMP-5 (logs). If the agent has to add a migration or log upsert, the scope and dependencies are wrong. | Add a Context section that states exactly what T-006 delivers. Either list "Alembic migration adding `import_run.waypoints`" and "log upsert, dedup by log id (IMP-5) + AC" under Scope In, or move them explicitly to Out with the ticket that owns them. Give the `source_factory` signature, e.g. `Callable[[Sequence[Path]], CacheSource]`. |
| QDE-6 | Minor | AC3: "After setting a note or corrected coordinates in the DB, re-importing keeps them (end-to-end through the API)." | The user-data API (`PUT /caches/{gc}/user-data`) only arrives in T-013, so "end-to-end through the API" conflicts with "in the DB". The word "or" also lets the test cover only one of the two fields. | Rewrite: "Given a cache imported from `with_waypoints.zip` and a `UserCacheData` row seeded through the repository with both `note` and `corrected_location`, when the same file is re-imported through `POST /api/v1/imports`, then both values are byte-identical. Test: `test_reimport_preserves_user_note_and_corrected_location`." |
| QDE-7 | Minor | Scope In: "Invalidate the cache queries when it finishes." | The cache list/map queries arrive in T-010/T-011, after this ticket. There is no query key to invalidate yet, so the agent has to invent a key that later tickets must reuse. | Fix the contract: "On success, invalidate query-key prefixes `['imports']` and `['caches']`. Later cache queries must use the `['caches', …]` prefix." Test it with a `QueryClient.invalidateQueries` spy (AC11 above). |
| QDE-8 | Minor | Scope In: "(multipart, many files, max 50 MB each; configurable)" | The setting name, env var, and `.env.example` entry are not given (NFR-4). There is also no limit on the number of files. Without a named setting, AC5b can't override the limit to a small value in tests. | Add an Implementation notes line: "Setting `import_max_file_mb: int = 50` (env `IMPORT_MAX_FILE_MB`), documented in `.env.example`. Max 20 files per request → 413 problem+json." |
| QDE-9 | Minor | AC6: "Component tests cover success, partial errors, and server error."; AC7: "import a fixture through the UI and see the summary." | AC6 is a compound AC without observable assertions. For AC7, the ticket doesn't say which fixture to use, how Playwright reaches `backend/tests/fixtures/pq/`, or how DB state is isolated between e2e runs. | Split AC6 into three Given/When/Then component ACs with MSW handlers: 201 with all counts shown; 201 with 1 error and expandable details showing the GC code; 500 problem+json showing the `title` and keeping the drop zone usable. For AC7, state the fixture (`with_waypoints.zip`), its path, the expected count text, and a DB reset step before the suite. |
| QDE-10 | Minor | Header: "- **Related ADRs:** ADR-0003"; DoD: "All ACs are covered" | The ticket deviates from TEMPLATE.md: it has no `Reviews:` line, no Context section, and no Implementation notes section. The DoD drops "by automated tests" and "Docs are updated" (spec §9.4 items 1 and 3), which weakens the gate. | Add the missing sections. Copy the DoD from the template verbatim, plus "No TODOs without a linked backlog ticket" (§9.4.4). |
| QDE-11 | Minor | Sizing: the whole of Scope In (service, two endpoints, upload handling, a four-part UI feature, e2e) | This is large for one autonomous PR (ADR-0009: "Tickets must be small enough for one PR"), especially after the missing ACs are added. | Optional split. **T-008a:** service + API + `api:gen` (AC1–5, 8–10, 12). **T-008b:** import UI + e2e (AC6, 7, 11), depends on T-008a. |
| QDE-12 | Nit | Scope In: "Run `api:gen`." | Not written as the actual mise command, and it doesn't say to commit the generated client. | "Run `mise run api:gen` and commit the regenerated client (the CI drift check must stay green)." |

### Strengths
- The vertical slice has a clear user-visible goal, and the Scope Out section ("Background jobs or progress streaming") is explicit.
- It reuses the named synthetic T-007 fixtures (`with_waypoints.zip`, `one_corrupt_entry.gpx`), so no network or real geocaching.com data is needed.
- The test plan uses all the right levels: unit tests with fakes, integration tests against PostGIS, component tests, and e2e.

### Open questions for the author
- Does T-006 deliver the `ImportRun` table and a bulk-upsert `CacheRepository` method, or does this ticket add them (with a migration)?
- Which ticket persists PQ logs (IMP-5)? If it is this one, it needs an AC.
- If a multi-file request contains one rejected file, does the whole request fail, or are the valid files imported?
- If a DB error happens midway (e.g. in batch 3 of 5), should the batches already written be rolled back, and should an `ImportRun` still be recorded?

### Out of my lane
- Architect: spec §7 `ImportRun` has no `waypoints` count, but IMP-6 requires one in the summary. Transaction boundaries for batched upserts also need a decision.
- Architect: a synchronous import of up to 10,000 caches in the request may run into HTTP timeouts. The limit should be documented at the design level, not only "in code".
- Product Designer: the busy state of a long synchronous upload (no progress information), and what the expandable error details show the user.
