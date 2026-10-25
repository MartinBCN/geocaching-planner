# Council review: 0004-brouter-routing (review 2)

- **Target:** `docs/adr/0004-brouter-routing.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 2 Major · 2 Minor · 0 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve · Quality & Delivery: Approve with changes

## Context provided
- `README.md`
- `AGENTS.md`
- `docs/specification.md`
- `docs/adr/0001-record-architecture-decisions.md`
- `docs/adr/0002-local-single-user-deployment.md`
- `docs/adr/0003-gpx-first-pluggable-cache-source.md`
- `docs/adr/0000-template.md`

**Anomalies:** none

## Top actions
1. Justify the BRouter choice against the alternatives using the decision's bike-aware, offline-routing, and elevation criteria (ARC-1).
2. Link the specific tickets for BRouter service setup, segment downloading, adapter integration, and profile support (QDE-1, ARC-2).
3. Clarify that routing needs segment coverage for the route area and ensure missing coverage produces an actionable message (PRD-1).
4. Add the `Reviews:` line and link this council report (QDE-2).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | ARC-1 | Alternatives considered: “OpenRouteService API \| Easy start”; “GraphHopper self-hosted \| Fast, flexible”; “Valhalla \| Powerful” | The alternatives are listed, but the ADR does not compare BRouter against them or explain why it best meets the stated needs for bike-aware offline routing and elevation. This leaves the central choice insufficiently justified. | Add BRouter to the comparison and explain the decision against the relevant criteria, including material trade-offs. |
| 2 | Major | QDE-1, ARC-2 | Consequences: “Segment files need disk space (100–500 MB per 5°×5° tile).” | The ADR implies implementation and operational work for BRouter setup, segment downloads, adapter behavior, and profile support, but does not link the delivery tickets. | Link the existing or new specific tickets covering the work; do not invent ticket IDs. If tickets do not exist, create them before treating the ADR as Accepted. |
| 3 | Minor | PRD-1 | Decision: “locally downloaded `.rd5` segment files”; Specification §4.4 RTE-7: “If BRouter is unreachable, the user gets a clear error” | The consequences of planning outside downloaded segment coverage are unstated, so route failure may be confusing even when BRouter is running. | Clarify that routing requires segment coverage for the route area, and ensure the user gets an actionable message when coverage is missing. |
| 4 | Minor | QDE-2 | Header: “**Status:** Accepted”; compare the template’s “**Reviews:** –” field | The ADR omits the template's Reviews field, so it provides no place to record the council review link. | Add `- **Reviews:** –` and update it with the review report link when available. |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Severity of missing implementation-ticket links | Architect: Minor (ARC-2). | Quality & Delivery: Major (QDE-1), because multiple substantial implementation areas are unmapped. The consolidated finding retains Major, the higher severity. |
| Whether the ADR needs changes | Product Designer: Approve, with one Minor finding. | Architect and Quality & Delivery: Approve with changes, citing Major findings. |

## Open questions for the author
- Which specific tickets will deliver the BRouter service, segment-download task, adapter, and profile support? (QDE-1)
- How will the adapter map BRouter’s elevation output to the specification’s ascent and descent statistics? (ARC-1)

## Strengths
- The decision names BRouter, the deployment approach, local segment files, and the supported profiles.
- The `RoutingProvider` protocol preserves the option to change routing engines later.
- The choice and consequences align with the specification’s self-hosted routing and offline goals, while acknowledging segment storage requirements.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: docs/adr/0004-brouter-routing.md

**Member verdict:** Approve with changes
**Rationale:** The choice fits the specification, but the ADR does not explain why BRouter is preferred over the alternatives or identify implementation follow-up tickets.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Alternatives considered: “OpenRouteService API \| Easy start”; “GraphHopper self-hosted \| Fast, flexible”; “Valhalla \| Powerful” | The alternatives are listed, but the ADR does not compare BRouter against them or explain why it best meets the stated needs for bike-aware offline routing and elevation. That leaves the central choice insufficiently justified. | Add BRouter to the comparison and explain the decision against the relevant criteria, including material trade-offs. |
| ARC-2 | Minor | Consequences: “Segment files need disk space (100–500 MB per 5°×5° tile).” | The ADR notes operational work and storage costs but names no follow-up tickets, as the ADR template requests. | Link the existing or new tickets for the Compose service, segment setup, and adapter integration; do not invent ticket IDs. |

### Strengths
- The decision uses the `RoutingProvider` protocol, preserving the option to change engines later.
- The chosen profiles and local segment files align with the specification’s routing requirements.
- The consequences acknowledge disk usage and the need for regional routing data.

### Open questions for the author
- How will the adapter map BRouter’s elevation output to the specification’s ascent and descent statistics?

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: docs/adr/0004-brouter-routing.md

**Member verdict:** Approve
**Rationale:** The decision supports the bicycle-planning flow and aligns with the specified routing profiles and offline behavior, with one small user-facing clarity gap.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Minor | Decision: “locally downloaded `.rd5` segment files”; Specification §4.4 RTE-7: “If BRouter is unreachable, the user gets a clear error” | The consequences of planning outside the downloaded segment coverage are not stated, so a route failure may be confusing even when BRouter itself is running. | Clarify that routing requires segment coverage for the route area, and ensure the user gets an actionable message when coverage is missing. |

### Strengths
- The default and selectable profiles match the route-planning requirements.
- Local routing supports the offline-first use case while acknowledging the segment storage cost.
- The `RoutingProvider` decision leaves room to change engines without making that a user-facing requirement now.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: docs/adr/0004-brouter-routing.md

**Member verdict:** Approve with changes  
**Rationale:** The routing decision is clear at a high level, but its implied implementation work is not mapped to specific follow-up tickets.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Consequences: “Segment files need disk space (100–500 MB per 5°×5° tile).” | The ADR implies implementation work—BRouter setup, segment downloads, adapter behavior, and profile support—but names no tickets for it. The specification only groups T-015–T-020 under “Plan routes with BRouter, elevation, caches along route, route export,” which does not show where this ADR’s work will be delivered. | Add links to the specific tickets covering each implied item. If tickets do not yet exist, create them before treating the ADR as Accepted. |
| QDE-2 | Minor | Header: “**Status:** Accepted”; compare the template’s “**Reviews:** –” field | The ADR omits the template’s Reviews field, so it does not provide a place to record the council review link. | Add `- **Reviews:** –` and update it with the review report link when available. |

### Strengths
- The decision names the routing engine, deployment approach, local segment files, and profiles.
- The `RoutingProvider` boundary gives a concrete seam for the backend integration.
- The decision aligns with the specification’s self-hosted BRouter requirement and offline-routing goal.

### Open questions for the author
- Which specific tickets will deliver the BRouter service, segment-download task, adapter, and profile support?

### Out of my lane
- none
