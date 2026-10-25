# Council review: T-006-cache-domain-model (review 1)

- **Target:** `docs/features/backlog/T-006-cache-domain-model.md` (Ticket, status at review time: Ready)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 8 Major · 7 Minor · 1 Nit
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
- docs/features/backlog/T-005-ci.md
- docs/features/TEMPLATE.md
- docs/features/README.md

**Anomalies:** none

## Top actions
1. Define the re-import rule for waypoints so a partial re-import (no `*-wpts.gpx`) cannot silently delete them: distinguish "no waypoint data" (keep) from "empty list" (clear), and rewrite AC4 with explicit log and waypoint cases. (ARC-1, PRD-1, QDE-6)
2. Pin the persistence port: `Cache` as aggregate root with `waypoints`/`logs`, async method signatures, and a defined `UpsertResult` (created/updated/unchanged GC codes plus waypoint count) that T-008 can use for the IMP-6 summary. Specify what `source_hash` covers, compute it in a pure domain function, and add it to spec §7. (ARC-2, QDE-2, ARC-4, PRD-4, QDE-3)
3. List the indexes explicitly in AC1, including GiST on `user_cache_data.corrected_location` (ADR-0006). Bind the effective-location view/expression choice, keep spatial predicates on separate indexed branches, and give AC5 its own integration test with set/clear cases. (ARC-3, QDE-5, QDE-4)
4. Add ACs for `set_user_data`: partial updates keep the other field, clearing corrected coordinates restores the original location, and the original `caches.location` is never changed. (PRD-2)
5. Reduce delivery risk: split into a "domain model and schema" ticket and a "cache repository" ticket, and specify how the shared suite runs against both the fake (unit) and the DB (integration). (QDE-1, QDE-7, ARC-7)

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | ARC-1, PRD-1, QDE-6 | AC4: "Waypoints of a cache are replaced by the latest import set." | Waypoints may arrive in a separate `*-wpts.gpx` file (IMP-3). Re-importing only the main GPX would, read literally, delete all waypoints (including Parking/Final, which matter most to cyclists). The ticket does not distinguish "no waypoint data supplied" from "zero waypoints". Log edge cases are also undefined (logs missing from a newer PQ; known log id with changed text). | Model `waypoints: tuple[CacheWaypoint, ...] \| None`: `None` keeps existing waypoints, a list replaces them, an empty list clears. Rewrite AC4 with Given/When/Then cases, e.g. logs {1,2} + {2,3} → {1,2,3} with log 2 updated; waypoints {P1,P2} + {P2} → {P2}; plus the "no waypoint data" case. Add a test such as `test_reimport_without_wpts_file_keeps_waypoints`. |
| 2 | Major | ARC-2, QDE-2 | Scope/In: "`CacheRepository` protocol with `upsert_many(caches) -> UpsertResult`" / "`get(gc_code)`, `get_user_data`, `set_user_data`, and `add_import_run`" | The aggregate boundary is not stated (ADR-0003: `CacheSource` yields `Cache` "with waypoints and logs"). Four of five methods have no signature, sync vs. async is open (spec §9.3: async DB access), and `UpsertResult` is undefined, although T-008 needs created/updated/unchanged/waypoints/errors for IMP-6. | State that `Cache` is the aggregate root and `upsert_many` persists it whole. Add **must** async signatures and define `UpsertResult` (e.g. lists of GC codes for created/updated/unchanged with count properties, plus a waypoint count) in `domain/` or `services/ports.py`. |
| 3 | Major | ARC-4, PRD-4, QDE-3 | Scope/In: "Track created, updated, and unchanged by comparing a content hash column (`source_hash`)." | The hash inputs are undefined (waypoints? logs? `found_by_me`? timestamps?), as is where it is computed. Per-repository computation would make the fake and DB disagree and break AC7. If new logs/waypoints don't count, the IMP-6 summary misleadingly says "unchanged". `source_hash` is not in spec §7. AC2 does not define a "changed field". | Add a pure `domain` function `content_hash(cache)` over a documented, canonically ordered set of source fields; state whether waypoint/log changes count as `updated`; add `source_hash` to spec §7; state that `created_at` is never changed by `ON CONFLICT DO UPDATE`. Rewrite AC2 as Given/When/Then for created → unchanged (with `updated_at` unchanged) → updated. |
| 4 | Major | ARC-3, QDE-5 | AC1: "The migration creates all tables and indexes. Upgrade and downgrade round-trip." / Scope: "ORM models with `geography(Point,4326)` and GiST indexes" | "All" is undefined, so the test can pass with an index missing. ADR-0006 requires a GiST index on `user_cache_data.corrected_location`, which the ticket does not name. "Round-trip" is vaguer than spec §9.3. | Rewrite AC1 naming the tables (`caches`, `cache_waypoints`, `cache_logs`, `user_cache_data`, `import_runs`), GiST indexes on `caches.location` and `user_cache_data.corrected_location`, and the btree indexes; verify via `pg_indexes`; `downgrade -1` then `upgrade head` both succeed with identical schema. |
| 5 | Major | QDE-4 (related: ARC-3) | Scope/In: "SQL view or hybrid expression `effective_location = COALESCE(...)`"; Test plan: "AC2–AC5, AC7 … (shared suite also run against the fake…)" | The view vs. expression choice is left open with no criterion, and the test depends on it. No protocol method returns the effective location, so the fake cannot be checked against AC5. A bare `COALESCE` in a `WHERE` clause cannot use either GiST index, risking NFR-1 in T-010 (ADR-0006: "spatial predicates use separate indexed branches"). | Make the choice binding or state the criterion (usable in `WHERE`/`ORDER BY` by T-010/T-019). State that COALESCE is for projection/ordering only and that the two-branch indexed predicate is owned by T-010 (or provide a helper). Move AC5 to `tests/integration/repositories/test_effective_location.py` with cases: no user data → A; corrected B → B; correction cleared → A. |
| 6 | Major | PRD-2 | Requirements: "CAC-4, CAC-5 (data side)"; Scope: "`get_user_data`, `set_user_data`" | CAC-5 says the user can "set or clear" corrected coordinates, but no AC covers `set_user_data` or clearing. A partial update (saving a note) could null out a solved mystery's corrected coordinates. AC5 covers only "never set". | Add ACs: setting only the note keeps corrected coordinates (and vice versa); clearing corrected coordinates restores the original effective location and keeps the note; `caches.location` is unchanged while a correction is set. |
| 7 | Major | QDE-1 | Scope › In: "Domain entities, ORM models, migration, and a repository for caches, waypoints, logs, user data, and import runs" | Too large for one PR (ADR-0009: "Tickets must be small enough for one PR"); more code means more guessed decisions. | Split into T-006a "Cache domain model and schema" (AC1, AC5, AC6) and T-006b "Cache repository" (AC2–AC4, AC7), and update the `Depends on` lines of T-007, T-009, T-016. |
| 8 | Major | QDE-7, ARC-7 | AC7: "The fake repository and the DB repository pass the same shared contract test suite."; Scope: "in-memory fake `CacheRepository` for unit tests in `tests/fakes/`" | It is unspecified how one suite runs at two levels (pytest-socket blocks network in `tests/unit`). "Contract" collides with the spec §9.2 Contract level. `tests/fakes/` is not in the spec §6.1 layout. | Specify an abstract `CacheRepositoryContract` in `backend/tests/shared/cache_repository_suite.py` with an abstract `repo` fixture, subclassed in `tests/unit/repositories/…` and `tests/integration/repositories/…`. Rename to "shared behaviour suite". Either add `fakes/` to spec §6.1 or place the fake under `tests/unit/fakes/`. |
| 9 | Minor | QDE-8 | Scope › In: "`add_import_run`" / Requirements: "IMP-4, IMP-5, CAC-4, CAC-5 (data side)" | `ImportRun` persistence and `get` have no AC or test; IMP-6 (history) is not listed though storage is added here. | Add AC8: an `ImportRun` with counts/errors is persisted with an id and `errors` round-trips as JSON; add to the shared suite; add "IMP-6 (data side)" to Requirements. |
| 10 | Minor | PRD-3, QDE-10 | Scope: "`CacheType` (… Mega, Giga, Webcam, Lab, Other)"; "`WaypointType`, and `LogType`" | Closed enums lose unlisted Groundspeak types (e.g. Community Celebration Event, HQ, GPS Adventures, Locationless), which affects map icons (MAP-2) and GPX export to Garmin (EXP-1). `WaypointType`/`LogType` members are not listed, there is no unknown-value rule, and D/T validation (1–5 in 0.5 steps) has no AC. | List enum members (or "per the Groundspeak schema, plus `Other`") with a fallback rule; store the raw source type/container strings or document an exact two-way mapping so T-014 can write originals back; add an AC rejecting D/T outside {1.0, 1.5, …, 5.0}. |
| 11 | Minor | ARC-5, QDE-9 | Scope/In: "frozen dataclasses or pydantic models" | The representation is left open without criteria, which may pull a validation framework into `domain/`. The ticket does not say whether `Cache` contains waypoints/logs. Enum DB storage is unspecified; native PG ENUMs are hard to extend/downgrade. | Either pin frozen stdlib dataclasses in `domain/` (pydantic only in `api/`, spec §9.3) or state the criterion (`domain/` imports no SQLAlchemy/FastAPI, `mypy --strict` clean). **must**: `Cache` has `waypoints` and `logs` tuples. Store enums as `VARCHAR` (optionally with CHECK), not native PG ENUMs. |
| 12 | Minor | ARC-6 | Scope/In: "value object `Coordinates(lat, lon)`" | PostGIS/WKT use (lon, lat). A swap in the adapter would pass AC6 but misplace every cache; AC5 only catches it with asymmetric fixtures. | State that the adapter maps to `POINT(lon lat)`; add a round-trip test with asymmetric coordinates (e.g. lat 52.1, lon 4.3). |
| 13 | Minor | QDE-11 | AC6: "`Coordinates` rejects lat outside [-90, 90] and lon outside [-180, 180]." | Error type unstated; NaN/inf not covered. | Parametrized AC: lat ∈ {-90.0001, 90.0001, NaN} or lon ∈ {-180.0001, 180.0001, inf} → `ValueError`; ±90/±180 accepted. |
| 14 | Minor | QDE-12 | Scope › In: "`INSERT … ON CONFLICT (gc_code) DO UPDATE`" | A batch with the same GC code twice (overlapping PQs in one ZIP) makes PostgreSQL raise "cannot affect row a second time", aborting the import under IMP-7. | **must**: collapse duplicate GC codes within one `upsert_many` call (last wins) before insert; add a shared-suite test. |
| 15 | Minor | QDE-13 | Test plan: no fixtures named | Without a shared builder every test hand-builds large `Cache` objects. | Name a synthetic factory `backend/tests/factories.py::make_cache(**overrides)` (no real GC data, spec §3). |
| 16 | Nit | QDE-14 | Header and sections vs. TEMPLATE.md: "- **Reviews:**", "## Implementation notes" | The `Reviews:` line and Implementation notes section are missing; DoD says "All ACs are covered" instead of "covered by automated tests". | Align with TEMPLATE.md; move file/library hints (e.g. GeoAlchemy2 local stubs per ADR-0006) to Implementation notes. |

Severity for #3 taken as Major (highest of the sources, QDE-3); ARC-4 and PRD-4 rated it Minor. Severity for #8 taken as Major (QDE-7); ARC-7 rated its part Nit. No severities were raised by the Chair.

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Severity of the `source_hash` definition gap (#3) | ARC-4, PRD-4: Minor; low risk, fix by documenting hash inputs. | QDE-3: Major; fake/DB divergence breaks AC7 and forces T-008 rework. |
| Severity of test-suite placement (#8) | ARC-7: Nit; only the `tests/fakes/` location deviates from spec §6.1. | QDE-7: Major; how the shared suite runs at unit and integration level is unspecified, and "contract" collides with spec §9.2. |
| Domain representation (#11) | ARC-5: pin frozen stdlib dataclasses in `domain/`; pydantic only in `api/`. | QDE-9: leave it as implementer's choice, but state the criterion (no SQLAlchemy/FastAPI imports, `mypy --strict` clean). |
| Unknown enum values (#10) | PRD-3: preserve raw source strings (or an exact two-way mapping) so export can write originals back. | QDE-10: map unknown values to `Other` via a fallback rule. |
| Ticket sizing (#7) | QDE-1: split into two tickets (Major). | ARC (Out of my lane): only flags sizing for QDE to check; no position on splitting. |

## Open questions for the author
- Who owns the transaction boundary for `upsert_many` plus `add_import_run`: the repository or the T-008 service? Does a DB error roll back the whole batch or get reported per entry (IMP-7)? (ARC)
- Should the `CacheLog` key be the source log id alone or `(source, id)` to avoid collisions with the future Geocaching.com API source (T-022)? (ARC)
- Should `add_import_run` and a later history read sit on `CacheRepository` or a separate `ImportRunRepository` port? (ARC)
- When a re-import has no waypoints for a cache, should existing waypoints be kept or deleted? (QDE, see #1)
- Should changes to waypoints or logs alone count as `updated` in the import summary? (QDE, see #3)
- Does T-003 already create `tests/integration/test_migrations.py`? If so, AC1 should extend it. (QDE)
- When a cache stops appearing in PQs, how will the user notice stale data? Should this ticket record a "last seen in import" date? (PRD)
- Should `Coordinates` also parse/format the `N 52° 05.123 E 004° 12.345` notation, shared by T-013 and T-017? (PRD)
- Must D/T values follow "1 to 5 in 0.5 steps"? (PRD, see #10)

## Strengths
- AC3 explicitly guarantees that a re-import never overwrites user notes or corrected coordinates, in a separate `user_cache_data` table (IMP-4, ADR-0003, AGENTS.md).
- The effective location is defined once and tested (AC5), so map, distance, corridor search and export stay consistent (CAC-5, ADR-0006).
- The persistence port lives in `services/ports.py`, and one shared suite runs against both the fake and the DB repository, keeping fakes honest.
- Log deduplication by id lets log history accumulate across PQs, as GSAK users expect.
- The dependency chain is correct: T-005 transitively covers T-003 (PostGIS, testcontainers).

## Process notes
- All three custom agent types (`council-architect`, `council-product-designer`, `council-quality-delivery`) were available; no fallback used.
- All three reviews met the output contract; no re-prompts were needed.
- Context was verified against `context-rules.md`: ADR-0001…0010 all have status `Accepted`; target `Depends on: T-005` resolved to `docs/features/backlog/T-005-ci.md`.

---

## Appendix A: Software Architect (raw)
## Software Architect review: T-006-cache-domain-model.md

**Member verdict:** Approve with changes
**Rationale:** The ticket follows ADR-0003 and ADR-0006 and keeps the layering right, but four persistence points are unclear and would likely cause rework in T-007, T-008 or T-010: the aggregate boundary, the waypoint replacement rule, the effective-location indexes and the change-detection hash.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | AC4: "Waypoints of a cache are replaced by the latest import set." | IMP-3 says additional waypoints can arrive in a separate `*-wpts.gpx` file. If someone re-imports only the main GPX, a literal "replace" deletes all of that cache's waypoints. That is silent data loss. The ticket does not distinguish "this import carried no waypoint data" from "this cache has zero waypoints". | Change AC4 to: "If the incoming `Cache.waypoints` is `None` (the source supplied no waypoint data), existing waypoints are kept. If it is a list, it replaces the stored set, and an empty list clears it." Model `waypoints: tuple[CacheWaypoint, ...] \| None` in the domain and add a contract test for each case. |
| ARC-2 | Major | Scope/In: "`CacheRepository` protocol with `upsert_many(caches) -> UpsertResult`" | The aggregate boundary is not stated. ADR-0003 says `CacheSource` "yields domain `Cache` objects (with waypoints and logs)". The ticket lists `Cache`, `CacheWaypoint` and `CacheLog` as separate classes and only has an `upsert_many(caches)` method. It does not say whether `Cache` carries its waypoints and logs, or what `UpsertResult` contains. IMP-6 needs "created, updated, unchanged, waypoints, errors" for T-008. | State that `Cache` is the aggregate root with `waypoints` and `logs` collections, and that `upsert_many` persists the whole aggregate. Define `UpsertResult(created, updated, unchanged, waypoints)` in `domain/` or `services/ports.py` so T-008 can fill `ImportRun` without changing the protocol. |
| ARC-3 | Major | Scope/In: "ORM models with `geography(Point,4326)` and GiST indexes" / "SQL view or hybrid expression `effective_location = COALESCE(...)`" | ADR-0006 requires GiST indexes on `cache.location` and `user.corrected_location`, and says "spatial predicates use separate indexed branches". The ticket does not name the GiST index on `user_cache_data.corrected_location`. A bare `COALESCE` used in a `WHERE` clause cannot use either index, which puts the NFR-1 target (bbox query in under 300 ms with 50k caches) at risk in T-010. AC1 says "all tables and indexes" but does not list them. | List the indexes explicitly: GiST on `caches.location`, GiST on `user_cache_data.corrected_location`, plus the btree indexes already listed. State that the COALESCE expression is for projection and ordering only, and that the index-friendly predicate with two branches is owned by T-010 (or provide a helper for it here). Make AC1 check for these named indexes. |
| ARC-4 | Minor | Scope/In: "comparing a content hash column (`source_hash`)" | The ticket does not say which fields the hash covers (cache fields only, or waypoints and logs too), whether timestamps such as `source_updated_at` and `updated_at` are excluded, or where the hash is computed. If the adapter computes it, the in-memory fake must duplicate the logic, which works against AC7's shared contract suite. `source_hash` is also not in spec §7. | Put a pure `content_hash(cache) -> str` function in `domain/` over a documented, canonically ordered set of source fields, and say whether waypoint and log changes count as `updated`. Add `source_hash` to spec §7 in this ticket. Also state that `created_at` is never changed by `ON CONFLICT DO UPDATE`. |
| ARC-5 | Minor | Scope/In: "frozen dataclasses or pydantic models" / enums `CacheType`, `ContainerSize` | Two open choices weaken the boundaries. (a) Leaving dataclass vs. pydantic to the implementer pulls a validation framework into `domain/` without a decision. (b) The ticket does not say how enums are stored. Native PostgreSQL ENUM types are hard to extend and to downgrade, and the type list will grow ("Lab", "Other"). | Use frozen stdlib dataclasses in `domain/` and keep pydantic for `api/` schemas (spec §9.3). Store enums as `VARCHAR` with a CHECK constraint or no DB constraint, not as native PG ENUMs, so new types only need a small migration that can be downgraded. |
| ARC-6 | Minor | Scope/In: "value object `Coordinates(lat, lon)`" | PostGIS and WKT use (lon, lat) axis order. A lat/lon swap in the adapter would pass AC6 but put every cache in the wrong place, and AC5 would only catch it if its fixtures are asymmetric. | Say that the adapter must map `Coordinates` to `POINT(lon lat)`. Add a round-trip contract test that uses asymmetric coordinates, for example lat 52.1 and lon 4.3. |
| ARC-7 | Nit | Scope/In: "An in-memory fake `CacheRepository` for unit tests in `tests/fakes/`" | Spec §6.1 defines `tests/{unit,integration,contract,fixtures}`. `tests/fakes/` is a new top-level test folder that the spec does not list. | Either add `fakes/` to spec §6.1 or place the fake under `tests/unit/fakes/`. |

### Strengths
- User data is kept in a separate `user_cache_data` table, and AC3 explicitly tests that an upsert never modifies it. This matches ADR-0003 and the AGENTS.md rule on user data.
- The ticket defines the effective location once, in one place, as spec §7 and ADR-0006 require, and AC5 tests it.
- The persistence port is defined in `services/ports.py`, and the shared contract suite (AC7) runs against both the fake and the DB repository. This keeps services independent of the adapter and keeps the fakes honest.

### Open questions for the author
- Who owns the transaction boundary for `upsert_many` plus `add_import_run`: the repository or the T-008 service (unit of work)? If a database error happens while a batch is upserted, does it roll back the whole batch, or is it reported per entry as IMP-7 requires?
- Should the `CacheLog` primary key be only the source log id, or `(source, id)`, so that the future Geocaching.com API source (T-022) cannot collide with PQ log ids?
- Should `add_import_run`, and a later history read for `GET /imports`, sit on `CacheRepository`, or on a separate `ImportRunRepository` port?

### Out of my lane
- QDE: the template's `- **Reviews:**` line is missing, and the ticket is already `Ready` without a linked council review.
- QDE: the scope is large for one PR (domain, ORM, migration, port, adapter, fake and shared suite). Check the sizing.
- QDE: the test plan paths leave out the `backend/` prefix, and AC2 does not define which "changed field" counts as a change.

## Appendix B: Product Designer (raw)
## Product Designer review: T-006-cache-domain-model.md

**Member verdict:** Approve with changes
**Rationale:** The ticket protects the user's notes and corrected coordinates on re-import, which supports the main flow. But two gaps could still lose or hide user data: waypoints can be silently deleted on a partial re-import, and nothing tests that clearing or partly updating user data keeps the other value.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Major | AC4: "Waypoints of a cache are replaced by the latest import set." | The ticket doesn't say what happens when an import has no waypoint set for a cache. For example, the user re-imports only the main PQ `.gpx` without the `*-wpts.gpx` file (IMP-3). A literal reading deletes the Parking and Final waypoints, which matter most to a cyclist deciding where to leave the bike. GSAK users don't expect a partial re-import to wipe waypoints. | Rewrite AC4: "Waypoints of a cache are replaced only when the import contains a waypoint set for that cache. An import without additional waypoints for a cache leaves its existing waypoints unchanged." Add a test such as `test_reimport_without_wpts_file_keeps_waypoints`. |
| PRD-2 | Major | Requirements: "CAC-4, CAC-5 (data side)"; Scope: "`get_user_data`, `set_user_data`" | CAC-5 says the user can "set or clear" corrected coordinates, but no AC covers `set_user_data` or clearing. A partial update could also destroy data. For example, saving a note could overwrite a solved mystery's corrected coordinates with null. AC5 only covers the "never set" case, not "set, then cleared". | Add ACs: (a) "Setting only the note keeps the existing corrected coordinates, and the reverse." (b) "Clearing corrected coordinates makes the effective location return the original location, and the note stays." (c) "The original `caches.location` is unchanged while corrected coordinates are set" (CAC-5: "original coordinates are kept"). |
| PRD-3 | Minor | Scope: "`CacheType` (… Mega, Giga, Webcam, Lab, Other)" | Mapping types into a closed enum loses Groundspeak types it doesn't list, such as Community Celebration Event, HQ, GPS Adventures, and Locationless. The type is used for map icons (MAP-2) and for the GPX the Garmin reads in geocache mode (EXP-1). If export later writes "Other", the device shows the wrong icon. | Also store the raw source type and container strings, or document an exact two-way mapping between the enum and Groundspeak strings so T-014 can write the original values back. |
| PRD-4 | Minor | Scope: "Track created, updated, and unchanged by comparing a content hash column (`source_hash`)." | The ticket doesn't say what the hash covers. If new logs or changed waypoints don't count, the import summary (IMP-6) says "unchanged" even though new logs were added. Users read that as "nothing new came in." Waypoint counts aren't reported either, but IMP-6 promises them in the summary. | State whether `source_hash` covers logs and waypoints. Add a waypoint count (and optionally new logs) to `UpsertResult` so T-008 can show the full IMP-6 summary without rework. |

### Strengths
- AC3 is written from the user's side: "note and corrected coordinates survive a re-import". That is the most important GSAK-style guarantee.
- The effective location is defined once and tested (AC5), so the map, distance, corridor search, and export all use the corrected coordinates consistently (CAC-5).
- Logs are deduplicated by log id (AC4/IMP-5). Because each PQ carries only a few recent logs, this lets log history build up across imports, as GSAK users expect.

### Open questions for the author
- When a cache stops appearing in PQs (often because it was archived), how will the user notice its data is stale? ADR-0003 says "Data is only as fresh as the user's last PQ download". Should this ticket record a "last seen in import" or last-GPX date, the way GSAK does, while the schema is being created?
- Should `Coordinates` also parse and format the Garmin/GSAK `N 52° 05.123 E 004° 12.345` notation? Putting it in the domain now would let T-013 (corrected-coordinate entry) and T-017 (entering coordinates as a route waypoint) share one implementation.
- Must D/T values follow the glossary's "1 to 5 in 0.5 steps"? Invalid values would make CAC-2 range filters behave unexpectedly.

### Out of my lane
- QDE: the template's `- **Reviews:**` line is missing from the ticket header.
- QDE: AC2 and AC4 need fixture-level definitions of "changed field" and of the waypoint replacement case so the tests are deterministic.
- ARC: ADR-0006 requires a GiST index on `user.corrected_location` and separate indexed branches for spatial predicates, but the Scope lists GiST indexes only generically. Please check that the migration covers both.
- ARC: the ticket lets the implementer choose "frozen dataclasses or pydantic models" in `domain/`. Consider pinning one choice now for consistency with later tickets.

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: T-006-cache-domain-model.md

**Member verdict:** Approve with changes
**Rationale:** The ticket covers the right scope, and its test plan maps every AC except one. But an agent would have to guess too much: the `UpsertResult` shape, what the content hash covers, how waypoints and logs behave on re-import, how the shared suite is wired up, and which tables and indexes AC1 means. The ticket is also large for one PR.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Scope › In: "Domain entities, ORM models, migration, and a repository for caches, waypoints, logs, user data, and import runs" | This is a lot for one ticket: 5 entities, 4 enums, a value object, ORM, a view, a migration, a protocol, a real repository with hash-based upsert, log deduplication and waypoint replacement, a fake, and a shared suite. ADR-0009 says "Tickets must be small enough for one PR." More code also means more decisions the agent has to guess. | Split it into two tickets. **T-006a "Cache domain model and schema"**: `domain/cache.py`, `Coordinates`, enums, ORM models, the effective-location view or expression, and the migration (AC1, AC5, AC6). **T-006b "Cache repository"** (depends on T-006a): `CacheRepository` protocol, DB implementation, fake, and the shared suite (AC2–AC4, AC7). Update the `Depends on` lines of T-007, T-009 and T-016 to match. |
| QDE-2 | Major | Scope › In: "`upsert_many(caches) -> UpsertResult`, `get(gc_code)`, `get_user_data`, `set_user_data`, and `add_import_run`" | Four of the five methods have no signature, and `UpsertResult` is not defined. AC2 says "reports `created`" but doesn't say whether that is a count or a status per cache. Sync vs. async is not stated, although spec §9.3 says "Async DB access". T-008 (IMP-6 summary) will depend on this interface, so a guess here causes rework later. | Add **must** signatures, for example: `async def upsert_many(self, caches: Sequence[Cache]) -> UpsertResult`, where `UpsertResult(created: list[str], updated: list[str], unchanged: list[str])` holds GC codes and exposes count properties. Also `async def get(gc_code: str) -> Cache \| None`, `async def get_user_data(gc_code) -> UserCacheData \| None`, `async def set_user_data(data: UserCacheData) -> None`, `async def add_import_run(run: ImportRun) -> ImportRun`. |
| QDE-3 | Major | Scope › In: "Track created, updated, and unchanged by comparing a content hash column (`source_hash`)" | The ticket doesn't say what goes into the hash. Waypoints? Logs? `found_by_me`? Timestamps like `source_updated_at`? It also doesn't say where the hash is computed. If each repository computes it separately, the fake and the DB will disagree and AC7 fails. `source_hash` is also not in spec §7. | Add: "**must**: `source_hash` = SHA-256 of a canonical JSON of all source fields of `Cache` plus its waypoints, excluding `created_at`/`updated_at`/logs. It is computed by a pure function `domain.cache.content_hash(cache)` that both repositories use. Add `source_hash` to spec §7." Then rewrite AC2: "Given an empty repo, when cache X is upserted, then `result.created == ['X']`; when X is upserted again unchanged, then `result.unchanged == ['X']` and `updated_at` is unchanged; when X is upserted with a different `name`, then `result.updated == ['X']`." |
| QDE-4 | Major | Test plan: "AC2–AC5, AC7 … (shared suite also run against the fake in `tests/unit`)" | AC5 is about a SQL view or hybrid expression. The protocol has no method that returns the effective location, so the fake can't be checked against AC5. The ticket also leaves "A SQL view or hybrid expression" open without saying how to choose, and the test depends on that choice. | Make the choice binding, or state the criterion (for example, "must be usable in `WHERE`/`ORDER BY` by T-010 and T-019"). Move AC5 to its own integration test, `tests/integration/repositories/test_effective_location.py`. Rewrite AC5: "Given cache X at A with no user data, when selecting `effective_location`, then A; given `corrected_location` B is set, then B; given the correction is cleared, then A again." |
| QDE-5 | Major | AC1: "The migration creates all tables and indexes. Upgrade and downgrade round-trip." | "All" is not defined. The agent decides what counts as done, so the test can pass even if an index is missing. It is also unclear whether the GiST index on `user_cache_data.corrected_location` (required by ADR-0006) is included. "Round-trip" is vaguer than spec §9.3. | Rewrite AC1: "Given an empty PostGIS DB, when `alembic upgrade head` runs, then tables `caches`, `cache_waypoints`, `cache_logs`, `user_cache_data`, `import_runs` exist, plus GiST indexes on `caches.location` and `user_cache_data.corrected_location` and B-tree indexes on `caches.type`, `difficulty`, `terrain`, `found_by_me`, `is_archived` (checked through `pg_indexes`). When `downgrade -1` and then `upgrade head` run, both succeed and the schema is the same." |
| QDE-6 | Major | AC4: "Logs are deduplicated by log id. Waypoints of a cache are replaced by the latest import set." | The edge cases are not defined. Does an empty waypoint set (a PQ without a `-wpts` file) delete existing waypoints? Are logs that are missing from a newer PQ kept? (PQs contain only recent logs.) Does a known log id with changed text get updated or ignored? Different agents will guess differently. | Rewrite AC4: "Given cache X with logs {1,2}, when re-upserted with logs {2,3}, then stored logs are {1,2,3} and log 2 has the newest text. Given X with waypoints {P1,P2}, when re-upserted with {P2}, then stored waypoints are {P2}; when re-upserted with an empty set, then [state the chosen behaviour explicitly]." |
| QDE-7 | Major | AC7: "The fake repository and the DB repository pass the same shared contract test suite." | The ticket doesn't say how one suite runs at two levels. The test file sits under `tests/integration`, but the fake must run under `tests/unit` (pytest-socket blocks the network there). "Contract" also collides with the spec §9.2 Contract level (BRouter/respx). And `tests/fakes/` is not in the spec §6.1 layout. | Specify: "the shared suite is an abstract class `CacheRepositoryContract` in `backend/tests/shared/cache_repository_suite.py` with an abstract `repo` fixture. It is subclassed in `tests/unit/repositories/test_fake_cache_repository.py` and `tests/integration/repositories/test_cache_repository.py`. The fake lives in `backend/tests/fakes/cache_repository.py`." Call it a "shared behaviour suite" rather than a "contract" suite. |
| QDE-8 | Minor | Scope › In: "`add_import_run`" / Requirements: "IMP-4, IMP-5, CAC-4, CAC-5 (data side)" | `ImportRun` persistence and `get` are in scope but have no AC and no test. They are exercised only incidentally. IMP-6 (import history) is not listed even though this ticket adds its storage. | Add AC8: "Given an `ImportRun` with counts and errors, when `add_import_run` is called, then it is persisted with an assigned id and `errors` round-trips as JSON." Add AC8 to the shared suite and add "IMP-6 (data side)" to Requirements. |
| QDE-9 | Minor | Scope › In: "frozen dataclasses or pydantic models" | The choice is left open without criteria, and the ticket doesn't say whether `Cache` contains its waypoints and logs. ADR-0003 says `CacheSource` "yields domain `Cache` objects (with waypoints and logs)", and `upsert_many(caches)` needs them. | State: "Implementer's choice; criterion: `domain/` must not import SQLAlchemy/FastAPI and must stay `mypy --strict` clean. **must**: `Cache` has `waypoints: tuple[CacheWaypoint, ...]` and `logs: tuple[CacheLog, ...]`." |
| QDE-10 | Minor | Scope › In: "`WaypointType`, and `LogType`" | Unlike the other enums, no members are listed. There is no rule for unknown values, which T-007 will run into. D/T range validation (spec §12: "from 1 to 5 in 0.5 steps") has no AC. | List the members (or say "per the Groundspeak schema, plus `Other`") and add a fallback rule ("unknown values map to `Other`"). Add AC: "`Cache` rejects difficulty/terrain outside {1.0, 1.5, …, 5.0}" and add it to `tests/unit/domain/test_cache.py`. |
| QDE-11 | Minor | AC6: "`Coordinates` rejects lat outside [-90, 90] and lon outside [-180, 180]." | The error type is not stated, and NaN/inf are not covered. | "Given lat ∈ {-90.0001, 90.0001, NaN} or lon ∈ {-180.0001, 180.0001, inf}, when constructing `Coordinates`, then `ValueError` is raised; boundary values ±90/±180 are accepted." Use a parametrized test. |
| QDE-12 | Minor | Scope › In: "`INSERT … ON CONFLICT (gc_code) DO UPDATE`" | If one batch contains the same GC code twice (for example from overlapping PQs in one ZIP), PostgreSQL raises "cannot affect row a second time". Under IMP-7 that would abort the whole import. | Add: "**must**: duplicate GC codes within one `upsert_many` call are collapsed (the last one wins) before the insert", plus a test in the shared suite. |
| QDE-13 | Minor | Test plan: no fixtures named | The ticket does not name any test data. Without a shared builder, every test hand-builds large `Cache` objects. | Name a synthetic factory, `backend/tests/factories.py::make_cache(**overrides)` (no real GC data, spec §3). |
| QDE-14 | Nit | Header and sections vs. TEMPLATE.md: "- **Reviews:**", "## Implementation notes" | The `Reviews:` line and the Implementation notes section are missing. The DoD says "All ACs are covered" instead of "covered by automated tests". | Align with TEMPLATE.md. Move the file and library hints (for example, GeoAlchemy2 local stubs are allowed per ADR-0006) into Implementation notes. |

### Strengths
- AC3 checks directly that an import never overwrites user data (IMP-4, ADR-0003), and that is a high-risk regression area.
- Running the same suite against the fake and the real repository is a good way to keep unit-test fakes honest.
- The dependency chain is correct: T-005 is the only `Depends on`, it transitively covers T-003 (PostGIS and testcontainers), and T-006 is the next ticket to pick.

### Open questions for the author
- Does T-003 already create `tests/integration/test_migrations.py`? If so, AC1 should extend that file, not replace it.
- When a re-import has no waypoints for a cache, should existing waypoints be kept or deleted? (This decides QDE-6.)
- Should changes to waypoints or logs alone count as `updated` in the import summary? (This decides QDE-3.)

### Out of my lane
- Architect: check that the view or expression choice supports the ADR-0006 rule "separate indexed branches" for corrected and original locations.
- Architect: `source_hash` adds a field not listed in spec §7. Confirm that it belongs on `caches`.
- Product Designer: deleting waypoints on a re-import without waypoints could lose data the user sees. Confirm the expected behaviour.
