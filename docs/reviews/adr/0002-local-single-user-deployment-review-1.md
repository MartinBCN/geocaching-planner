# Council review: 0002-local-single-user-deployment (review 1)

- **Target:** `docs/adr/0002-local-single-user-deployment.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 1 Major · 1 Minor · 1 Nit
- **Member verdicts:** Architect: Approve · Product Designer: Approve · Quality & Delivery: Approve with changes

## Context provided
- `README.md`
- `AGENTS.md`
- `docs/specification.md`
- `docs/adr/0001-record-architecture-decisions.md`
- `docs/adr/0000-template.md`
- `docs/adr/0002-local-single-user-deployment.md`

**Anomalies:** none

## Top actions
1. Define the host-network boundary for Compose services: host-published ports must bind to `127.0.0.1` or remain unpublished (QDE-1).
2. Add a check that verifies Compose does not publish service ports beyond the local machine (QDE-1).
3. Note in the consequences that BRouter routing requires regional data and map tiles require connectivity (PRD-1).
4. Add the standard `Reviews:` line to the ADR, with the report link when the owner updates the target (QDE-2).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | QDE-1 | Decision: “PostgreSQL/PostGIS plus BRouter in Docker Compose.” | The ADR does not define whether Compose-published host ports are restricted to loopback. Without authentication, services could be exposed beyond the local machine, conflicting with the local-only decision. | Specify that every host-published service port must bind to `127.0.0.1` or remain unpublished, and add a check verifying the Compose configuration follows this rule. |
| 2 | Minor | PRD-1 | Consequences: “Requires Docker on the user's machine.” Spec NFR-2: “Works fully offline except for map tiles.” | The consequences omit setup and connectivity expectations relevant to the user's planning session, including local routing data and online map tiles. | Briefly state that routing is local but requires regional BRouter data, while map tiles still need connectivity. |
| 3 | Nit | QDE-2 | After Date: “- **Date:** 2026-10-25” | The ADR omits the `Reviews` line required by the template and referenced in the review workflow. | Add `- **Reviews:** –` and update it with the council report link as directed by `AGENTS.md`. |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Compose host-port boundary | Architect: no findings; notes the ADR preserves localhost-binding safeguards. | Quality & Delivery: flags the absence of an explicit loopback-or-unpublished rule for Compose-published ports as a Major gap. |
| Reviews line | Architect: no findings. | Quality & Delivery: flags the missing template/workflow `Reviews` line as a Nit. |

## Open questions for the author
- none

## Strengths
- The decision clearly identifies the local backend address, Docker Compose services, and single-user scope.
- It aligns with the specification's local bicycle-planning workflow and avoids the additional complexity of public hosting and multi-user support.
- It calls out XSS sanitization, Docker as a setup requirement, and the need for a new ADR before network exposure.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: docs/adr/0002-local-single-user-deployment.md

**Member verdict:** Approve
**Rationale:** The local, single-user deployment decision is consistent with the specification and does not change an existing architectural decision.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| – | – | – | No findings | – |

### Strengths
- The decision clearly specifies the local backend address and the Docker Compose services.
- It explicitly preserves the XSS-sanitization and localhost-binding safeguards.
- It states that network exposure requires a new ADR.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: docs/adr/0002-local-single-user-deployment.md

**Member verdict:** Approve
**Rationale:** The local, single-user decision fits the specified bicycle-planning flow, but its consequences could better set expectations for setup and offline use.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Minor | Consequences: “Requires Docker on the user's machine.” Spec NFR-2: “Works fully offline except for map tiles.” | The consequences mention Docker but not the additional setup and connectivity expectations that affect a user's first ride-planning session, including local routing data and online map tiles. | Add a brief user-facing consequence noting that routing is local but requires regional BRouter data, while map tiles still need connectivity. |

### Strengths
- The decision supports the spec’s local, single-user scope and excludes public hosting and multi-user complexity.
- The browser UI and local services fit the existing desktop planning workflow.
- Docker is explicitly called out as a user setup requirement.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: docs/adr/0002-local-single-user-deployment.md

**Member verdict:** Approve with changes  
**Rationale:** The local single-user decision aligns with the specification, but the ADR does not make the network boundary of Compose-published ports verifiable.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Decision: “PostgreSQL/PostGIS plus BRouter in Docker Compose.” | The ADR does not say whether Compose-published host ports are restricted to loopback. With no authentication, an implementation could expose services beyond the local machine, conflicting with the local-only decision. | Specify that every host-published service port must bind to `127.0.0.1` or remain unpublished, and add a check that verifies the Compose configuration follows this rule. |
| QDE-2 | Nit | After Date: “- **Date:** 2026-10-25” | The ADR omits the `Reviews` line required by the ADR template and referenced in the review workflow. | Add `- **Reviews:** –` and update it with the council report link as directed by `AGENTS.md`. |

### Strengths
- Clearly states the single-user scope and rules out authentication and multi-tenancy.
- Aligns with the specification’s local deployment and localhost requirements.
- Calls out that exposing the app on a network requires a new ADR.

### Open questions for the author
- none

### Out of my lane
- none
