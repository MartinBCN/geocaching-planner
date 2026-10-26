# Council review: T-024-cache-repository (review 1)

- **Target:** `docs/features/backlog/T-024-cache-repository.md` (Ticket, status at review time: Draft)
- **Date:** 2026-10-26
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 3 Major · 1 Minor · 0 Nit
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
- docs/adr/0011-frontend-routing.md
- docs/adr/0012-hardened-xml-parsing.md
- docs/features/complete/T-006-cache-domain-model.md
- docs/features/TEMPLATE.md
- docs/features/README.md

**Anomalies:** none

## Top actions
1. Define user-data update semantics for omitted versus explicitly cleared fields, including note clearing, and test each case (ARC-1, PRD-1, QDE-1).
2. Specify transaction boundaries for every repository operation, especially batch upserts and import-run persistence (QDE-2).
3. Separate shared fake/PostGIS behavior coverage from database-specific `ImportRun.errors` JSON round-trip verification (QDE-3).
4. Verify that `updated_at` changes when source content changes while `created_at` remains fixed (QDE-4).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | ARC-1, PRD-1, QDE-1 | Scope: “`set_user_data(gc_code: str, update: UserCacheDataUpdate) -> UserCacheData`” and “Partial user-data updates retain the untouched field” | `UserCacheDataUpdate` and its field-presence semantics are not defined. The repository cannot reliably distinguish an omitted field from an explicit clear, risking loss of notes or corrected coordinates. | Define the update type: omitted fields retain their stored values; explicit null clears the corresponding field. Cover independent updates and explicit clearing of both note and corrected coordinates in tests. |
| 2 | Major | QDE-2 | Implementation notes: “Each repository operation is asynchronous and owns its transaction boundary as documented.” | The ticket does not specify those transaction boundaries or identify where they are documented. Atomicity of `upsert_many` and its relationship to T-008's import-batch policy are unclear. | Specify the boundary for each operation, including whether `upsert_many` is atomic for its input and whether `add_import_run` commits independently. |
| 3 | Major | QDE-3 | AC6: “Given both fake and PostGIS repositories” | AC6 appears to require both repositories to persist `ImportRun.errors` as JSON, while the test plan assigns AC6 only to an integration test. The fake cannot verify database JSON serialization. | Require the shared suite to test ImportRun behavior for both repositories, and the PostGIS integration test to verify JSON serialization and round-trip. |
| 4 | Minor | QDE-4 | AC1: “when a source field changes, then it is updated and `created_at` is preserved.” | AC1 does not verify the in-scope behavior that `updated_at` changes when source content changes. | Add that `updated_at` changes and compare timestamps so the test verifies the behavior. |

## Dissent
No dissent: the members agreed on the findings and severities.

## Open questions for the author
- What value or operation explicitly clears a note, and how is that distinguished from leaving it unchanged? (PRD-1, QDE-1)

## Strengths
- Keeps user-owned data separate from imported data, consistent with ADR-0003 and the specification.
- Clearly distinguishes absent waypoint data from an empty set that clears stored waypoints.
- Avoids unnecessary timestamp updates for unchanged source content and assigns query implementation to T-010.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: T-024-cache-repository.md

**Member verdict:** Approve with changes  
**Rationale:** The persistence contract aligns with the accepted architecture, but it should define how partial updates distinguish an omitted field from an explicit clear.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Scope: “Partial user-data updates retain the untouched field” | The `UserCacheDataUpdate` contract does not specify how callers represent an omitted field versus an explicit clear. Without that distinction, repository and service implementations may handle corrected-coordinate clearing inconsistently. | Define the update type’s field-presence semantics, including how a caller explicitly clears corrected coordinates while leaving other fields unchanged. |

### Strengths
- Keeps user-owned data separate from imported cache data, consistent with ADR-0003 and the specification.
- Explicitly addresses waypoint replacement semantics and preserves the original location when corrected coordinates are cleared.
- Keeps database I/O in the adapter and gives T-010 ownership of query implementation.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: T-024-cache-repository.md

**Member verdict:** Approve with changes
**Rationale:** The ticket supports import persistence and protects user-owned data, but needs explicit update semantics so editing one field cannot accidentally erase another.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Major | Scope: “Partial user-data updates retain the untouched field” | `UserCacheDataUpdate` does not specify how an omitted field differs from an explicitly cleared one. That ambiguity risks losing a note or corrected coordinates during an edit. | Define the update semantics for each field (for example, omitted means unchanged and an explicit clear value means clear), including how a note is cleared. Add acceptance coverage for updating either field while preserving the other, and for explicitly clearing each field. |

### Strengths
- Keeps imported cache data separate from user-owned notes and corrected coordinates.
- Clearly distinguishes absent waypoint data from an empty set that clears stored waypoints.
- Treats unchanged source content as a no-op for timestamps, avoiding unnecessary updates.

### Open questions for the author
- What value or operation explicitly clears a note, and how is that distinguished from leaving the note unchanged?

### Out of my lane
- none

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: T-024-cache-repository.md

**Member verdict:** Approve with changes  
**Rationale:** The ticket has a clear persistence goal and test direction, but leaves important update and transaction semantics underspecified and does not align AC6’s fake-versus-database requirement with its test plan.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Scope: “`set_user_data(gc_code: str, update: UserCacheDataUpdate) -> UserCacheData`” | `UserCacheDataUpdate` is not defined here or in T-006, and the contract does not specify how omitted fields differ from fields explicitly set to `None`. An implementer could choose incompatible partial-update and clearing behavior. | Define the update type and its field-presence semantics. For example: “`note` and `corrected_location` may each be omitted to retain the stored value; an explicit `null` clears that field. Tests cover updating either field independently and clearing each field.” |
| QDE-2 | Major | Implementation notes: “Each repository operation is asynchronous and owns its transaction boundary as documented.” | The ticket does not identify where those boundaries are documented or specify them. This leaves unclear whether operations such as `upsert_many` commit atomically and how repository transactions relate to T-008’s import-batch policy. | State the boundary for each operation in this ticket, or identify the authoritative document. For example, specify whether `upsert_many` is atomic for its entire input and whether `add_import_run` commits independently. |
| QDE-3 | Major | AC6: “Given both fake and PostGIS repositories” | AC6 appears to require both repositories to persist errors as JSON, but the test plan assigns AC6 only to a PostGIS integration test. An in-memory fake does not itself verify JSON persistence. | Separate the guarantees: require the shared suite to verify `ImportRun` behavior for both repositories, and require the PostGIS integration test to verify JSON serialization and round-trip of `errors`. |
| QDE-4 | Minor | AC1: “when a source field changes, then it is updated and `created_at` is preserved.” | The criterion does not verify the in-scope rule that `updated_at` changes when source content changes. As written, the test could pass without checking that behavior. | Add: “and `updated_at` changes.” Have the test compare timestamps using a controlled clock or otherwise ensure the change is observable. |

### Strengths
- Keeps imported cache data separate from user-owned data, consistent with the stated requirements.
- Explicitly covers the distinction between absent, replaced, and cleared waypoint collections.
- Provides a shared repository behavior suite and names the fake and PostGIS test locations.

### Open questions for the author
- Should clearing a note be supported by `UserCacheDataUpdate`, or is only clearing corrected coordinates in scope?

### Out of my lane
- none
