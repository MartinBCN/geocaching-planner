# Council review: 0005-frontend-react-maplibre (review 1)

- **Target:** `docs/adr/0005-frontend-react-maplibre.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 1 Major · 2 Minor · 0 Nit
- **Member verdicts:** Architect: Approve · Product Designer: Approve · Quality & Delivery: Approve with changes

## Context provided
- `README.md`
- `AGENTS.md`
- `docs/specification.md`
- `docs/adr/0001-record-architecture-decisions.md`
- `docs/adr/0002-local-single-user-deployment.md`
- `docs/adr/0003-gpx-first-pluggable-cache-source.md`
- `docs/adr/0004-brouter-routing.md`
- `docs/adr/0000-template.md`

**Anomalies:** none

## Top actions
1. Define the CI drift check as running client generation and failing if it changes the committed generated client; identify the ticket for implementing the generation task and check (QDE-1).
2. Clarify that the map uses the `Settings.tile_url` override and displays the configured style's required attribution (QDE-2).
3. Either document alternatives and trade-offs for the other major frontend libraries or state that this ADR decides only the framework and map renderer (ARC-1).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | QDE-1 | Consequences: “Regeneration is a mise task, and CI checks for drift.” | The ADR commits to a CI check but does not specify what it compares or identify follow-up work, so implementation may not reliably detect generated-client drift. | Specify that CI runs client generation and fails if it changes the committed generated client; name the ticket responsible for the task and check. |
| 2 | Minor | ARC-1 | Alternatives considered: “SvelteKit” and “Leaflet instead of MapLibre” | The ADR selects other substantial tools, including TanStack Query, Recharts, and dnd-kit, but gives no alternatives or trade-offs for them, leaving the decision basis incomplete. | Briefly document alternatives and trade-offs for the major selected libraries, or clarify that this ADR decides only the framework and map renderer. |
| 3 | Minor | QDE-2 | Decision: “configurable raster style (default: CyclOSM tiles with attribution).” | “Configurable” does not say where the tile URL is configured, and the attribution requirement does not specify how attribution is supplied or displayed. | State that the tile URL uses the specification’s `Settings.tile_url` override and that the configured style’s required attribution is displayed on the map. |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Whether the ADR needs changes | Architect and Product Designer: Approve; Architect records one Minor concern about alternatives. | Quality & Delivery: Approve with changes, identifying a Major gap in making the promised CI drift check verifiable. |

## Open questions for the author
- Should this ADR decide the full frontend library stack, or only the framework and map renderer? (ARC-1)

## Strengths
- The chosen frontend technologies align with the specification’s architecture and user flows.
- The generated OpenAPI client supports contract alignment between backend and frontend.
- The decision specifies a configurable raster map with attribution.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: docs/adr/0005-frontend-react-maplibre.md

**Member verdict:** Approve
**Rationale:** The decision is consistent with the accepted architecture and requirements, with one minor gap in the alternatives considered.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Minor | Alternatives considered: “SvelteKit” and “Leaflet instead of MapLibre” | The ADR selects several other substantial tools—including TanStack Query, Recharts, and dnd-kit—but gives no alternatives or trade-offs for them, making the decision basis incomplete. | Briefly document alternatives and their trade-offs for the major selected libraries, or clarify that this ADR only decides the framework and map renderer. |

### Strengths
- Aligns with the specification’s React, TypeScript, Vite, MapLibre, TanStack Query, and Recharts architecture.
- Keeps API types tied to the OpenAPI contract and names regeneration and CI drift checks.
- Preserves the configurable raster map and attribution requirement.

### Open questions for the author
- Should this ADR decide the full frontend library stack, or only the framework and map renderer?

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: docs/adr/0005-frontend-react-maplibre.md

**Member verdict:** Approve
**Rationale:** The chosen frontend stack aligns with the specification’s map, routing, and export flow, and the stated consequences are consistent with the local-app constraints.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| – | – | – | No findings | – |

### Strengths
- The decision matches the specification’s React, MapLibre, TanStack Query, and elevation-profile choices.
- A configurable raster base map with attribution fits the cycle-map requirement.
- The generated API client supports keeping the UI and backend contract aligned.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: docs/adr/0005-frontend-react-maplibre.md

**Member verdict:** Approve with changes
**Rationale:** The chosen stack aligns with the specification, but the CI drift check and map configuration decision need clearer, verifiable implementation details.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Consequences: “Regeneration is a mise task, and CI checks for drift.” | The ADR commits to a new CI check but does not specify what the check compares or identify follow-up work, so an implementation could claim compliance without reliably detecting generated-client drift. | Specify that CI runs the client-generation task and fails if it changes the committed generated client; name the ticket responsible for adding that task and check. |
| QDE-2 | Minor | Decision: “configurable raster style (default: CyclOSM tiles with attribution).” | “Configurable” does not say where the tile URL is configured, and the attribution requirement does not define how the corresponding attribution is supplied or displayed. | State that the tile URL uses the specification’s `Settings.tile_url` override and that the configured style’s required attribution is displayed on the map. |

### Strengths
- The selected frontend technologies match the specification’s stated architecture.
- The generated OpenAPI client supports contract alignment between the backend and frontend.
- The decision identifies the base map and explicitly retains attribution.

### Open questions for the author
- none

### Out of my lane
- none
