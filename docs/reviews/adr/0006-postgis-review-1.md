# Council review: 0006-postgis (review 1)

- **Target:** `docs/adr/0006-postgis.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Revise & resubmit**
- **Findings:** 1 Blocker · 1 Major · 1 Minor · 0 Nit
- **Member verdicts:** Architect: Revise & resubmit · Product Designer: Approve · Quality & Delivery: Approve with changes

## Context provided
- `README.md`
- `AGENTS.md`
- `docs/specification.md`
- `docs/adr/0001-record-architecture-decisions.md`
- `docs/adr/0002-local-single-user-deployment.md`
- `docs/adr/0003-gpx-first-pluggable-cache-source.md`
- `docs/adr/0004-brouter-routing.md`
- `docs/adr/0005-frontend-react-maplibre.md`
- `docs/adr/0000-template.md`

**Anomalies:** none

## Top actions
1. Specify a supported route-position calculation for corridor results that works with the declared geography types, including the necessary geometry casts or projection and correct route-position semantics (ARC-1, QDE-1).
2. State that all spatial cache queries use the effective location and specify how it is indexed for those queries (ARC-2, PRD-1).
3. Link the ticket responsible for setting up the PostGIS test container (QDE-2).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Blocker | ARC-1, QDE-1 | Decision: “Route geometry is stored as `geography(LineStringZ, 4326)`” and “orders by `ST_LineLocatePoint`.” | `ST_LineLocatePoint` operates on geometry, not geography; the decision does not establish a supported operation for these stored types. | Specify a supported route-position calculation, including any casts or projections needed, and ensure the result correctly represents position along the route. |
| 2 | Major | ARC-2, PRD-1 | Decision: “Locations are stored as `geography(Point, 4326)`”; specification §7: “The **effective location** of a cache is `coalesce(user.corrected_location, cache.location)`.” | The ADR does not state that spatial queries use or index effective locations. Using only imported cache locations would make spatial features ignore corrected coordinates, contrary to the specification. | Specify how the effective-location expression is used in spatial queries and how it is indexed for those queries. |
| 3 | Minor | QDE-2 | Consequences: “Integration tests need a PostGIS container (testcontainers).” | The ADR identifies integration-test work but does not link the backlog ticket responsible for delivering it, as the template requests. | Link the ticket that sets up the PostGIS test container; if covered by a foundation ticket, name it here. |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Severity of route-position/geography mismatch | Architect: Blocker (ARC-1), because the specified operation cannot be called with the stored types as stated. | Quality & Delivery: Major (QDE-1), recommending explicit geography filtering and geometry casts for ordering. The consolidated finding retains Blocker, the higher severity. |
| Severity of missing effective-location behavior | Architect: Major (ARC-2), including use and indexing. | Product Designer: Minor (PRD-1), focused on the user-visible risk of ignoring corrected coordinates. The consolidated finding retains Major, the higher severity. |
| Overall verdict | Architect: Revise & resubmit. | Product Designer: Approve; Quality & Delivery: Approve with changes. |

## Open questions for the author
- Which supported method will compute route position for corridor results while using the stored geography types? (ARC-1)

## Strengths
- The ADR identifies the core spatial query patterns motivating the database choice.
- It names the database, spatial, persistence, and migration tools consistently with the specification.
- It records the test-container and strict-typing consequences.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: docs/adr/0006-postgis.md

**Member verdict:** Revise & resubmit  
**Rationale:** The route-position operation is incompatible with the chosen geography types, and the ADR does not establish that spatial queries use the required effective location.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Blocker | Decision: “Route geometry is stored as `geography(LineStringZ, 4326)`”; “orders by `ST_LineLocatePoint`.” | `ST_LineLocatePoint` accepts geometry, not geography, so this operation cannot be called with the stored route and point types as stated. | Specify a supported route-position calculation, including any casts or projections needed, and ensure the result correctly represents position along the route. |
| ARC-2 | Major | Decision: “Locations are stored as `geography(Point, 4326)`”; specification §7: “The **effective location** of a cache is `coalesce(user.corrected_location, cache.location)`.” | The ADR does not state that spatial queries use or index the effective location. Using only the imported cache location would make spatial features ignore corrected coordinates, contrary to the specification. | Specify how the effective-location expression is used in spatial queries and how it is indexed for those queries. |

### Strengths
- The ADR identifies the core spatial query patterns motivating the database choice.
- It names the persistence and migration tools consistently with the specification.
- It records the test-container and strict-typing consequences.

### Open questions for the author
- Which supported method will compute route position for corridor results while using the stored geography types?

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: docs/adr/0006-postgis.md

**Member verdict:** Approve  
**Rationale:** The decision supports the map and corridor-search flow, with one clarification that would help protect corrected-coordinate behavior.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Minor | Decision: “Corridor search uses `ST_DWithin` and orders by `ST_LineLocatePoint`.” | The spatial-query description does not say that corridor search uses the cache’s effective location. If it uses original coordinates instead, solved caches could be missing from results or shown at the wrong position, contrary to the user’s expectation. | Clarify that spatial queries use the effective location—corrected coordinates when set, otherwise original coordinates—as specified in CAC-5 and §7. |

### Strengths
- The decision directly supports the map, distance, and caches-along-route parts of the main user flow.
- PostGIS is consistent with the specification’s local PostGIS deployment and spatial-query needs.
- The alternatives explain why a spatial database is preferred over plain Postgres or SQLite.

### Open questions for the author
- None.

### Out of my lane
- Architect: please verify that `ST_LineLocatePoint` is compatible with the declared geography route type, or specify any needed conversion.

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: docs/adr/0006-postgis.md

**Member verdict:** Approve with changes
**Rationale:** The database decision is specific, but corridor ordering needs an explicit geometry conversion to be implementable without guesswork.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Decision: “Route geometry is stored as `geography(LineStringZ, 4326)`” and “orders by `ST_LineLocatePoint`.” | `ST_LineLocatePoint` operates on geometry, not geography; the decision does not specify how to use it with the declared geography columns. | State explicitly: “Corridor search filters with `ST_DWithin` on geography values and orders by `ST_LineLocatePoint(route.geometry::geometry, effective_location::geometry)`.” |
| QDE-2 | Minor | Consequences: “Integration tests need a PostGIS container (testcontainers).” | The ADR identifies integration-test work but does not link the backlog ticket responsible for delivering it, as the ADR template requests. | Link the ticket that sets up the PostGIS test container; if already covered by a foundation ticket, name that ticket here. |

### Strengths
- Specifies concrete database, spatial, and migration libraries.
- Names GiST indexes and the corridor-search functions.
- Calls out integration-test and strict-typing consequences.

### Open questions for the author
- None.

### Out of my lane
- None.
