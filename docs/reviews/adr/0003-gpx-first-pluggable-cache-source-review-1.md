# Council review: 0003-gpx-first-pluggable-cache-source (review 1)

- **Target:** `docs/adr/0003-gpx-first-pluggable-cache-source.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Revise & resubmit**
- **Findings:** 1 Blocker · 0 Major · 2 Minor · 0 Nit
- **Member verdicts:** Architect: Revise & resubmit · Product Designer: Approve · Quality & Delivery: Approve

## Context provided
- `README.md`
- `AGENTS.md`
- `docs/specification.md`
- `docs/adr/0001-record-architecture-decisions.md`
- `docs/adr/0002-local-single-user-deployment.md`
- `docs/adr/0000-template.md`

**Anomalies:** none

## Top actions
1. Clarify that `CacheSource` supplies imported domain data and the import service also uses `CacheRepository` to persist it without overwriting user data (ARC-1).
2. Link the relevant implementation ticket(s) for parser and protocol work, or state where the follow-up work is tracked (ARC-2).
3. Add the `Reviews:` front-matter line and link the council report (QDE-1).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Blocker | ARC-1 | Decision: “The import service only talks to `CacheSource`” | The specification says services depend on protocols including `CacheRepository`. As written, the import service has no stated persistence boundary for the imported data. | Clarify that `CacheSource` supplies imported domain data and that the import service also uses `CacheRepository` to persist it while preserving user data. |
| 2 | Minor | ARC-2 | Consequences: “The parser must tolerate GPX 1.0/1.1 and variations in the Groundspeak schema.” | The consequences identify parser work but do not link the follow-up implementation work to backlog tickets, as requested by the ADR template. | Link the relevant import/protocol ticket or tickets, or state where that work is tracked. |
| 3 | Minor | QDE-1 | Front matter: “- **Status:** Accepted”; ADR-0000 template: “**Reviews:** – (links to docs/reviews/… once council-reviewed)” | The ADR has no `Reviews` line, so the council review cannot be linked as required by the review workflow. | Add a `- **Reviews:**` line and link this review report. |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Whether the ADR has issues requiring revision | Product Designer: Approve, with no findings. | Architect: Revise & resubmit for the missing persistence boundary; Quality & Delivery: Approve, but identifies a missing `Reviews` line as a Minor finding. |

## Open questions for the author
- none

## Strengths
- The GPX-first decision is grounded in the lack of API access and the prohibition on scraping.
- The decision supports the existing Pocket Query workflow, one-way data flow, and protection of user edits.
- It identifies the `CacheSource` boundary and blocked future API source as T-022.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: 0003-gpx-first-pluggable-cache-source.md

**Member verdict:** Revise & resubmit
**Rationale:** The decision’s description of the import service conflicts with the specified service boundaries and leaves persistence unaccounted for.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Blocker | Decision: “The import service only talks to `CacheSource`” | The specification says services depend on protocols including `CacheRepository`. As written, the import service has no stated persistence boundary for the imported data. | Clarify that `CacheSource` supplies imported domain data and that the import service also uses `CacheRepository` to persist it while preserving user data. |
| ARC-2 | Minor | Consequences: “The parser must tolerate GPX 1.0/1.1 and variations in the Groundspeak schema.” | The consequences identify parser work but do not link the follow-up implementation work to backlog tickets, as requested by the ADR template. | Link the relevant import/protocol ticket or tickets, or state where that work is tracked. |

### Strengths
- The GPX-first choice is grounded in the lack of API access and the prohibition on scraping.
- The one-way data flow and separation of user data align with the specification.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: docs/adr/0003-gpx-first-pluggable-cache-source.md

**Member verdict:** Approve  
**Rationale:** The decision supports the specified Pocket Query import flow, protects user data, and acknowledges the user-visible consequence of cache data freshness.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| – | – | – | No findings | – |

### Strengths
- Keeps the cache source aligned with the user’s existing Pocket Query workflow: “Premium members can download Pocket Queries”.
- Makes the one-way data flow and protection of user edits explicit: “User data (notes, corrected coordinates) is stored separately”.
- Acknowledges that cache freshness depends on the user’s last Pocket Query download.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: 0003-gpx-first-pluggable-cache-source.md

**Member verdict:** Approve  
**Rationale:** The decision is verifiable and aligns with the accepted project constraints; adding the review-tracking metadata would complete the ADR’s traceability.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Minor | Front matter: “- **Status:** Accepted”; ADR-0000 template: “**Reviews:** – (links to docs/reviews/… once council-reviewed)” | The ADR has no `Reviews` line, so the council review cannot be linked as required by the review workflow. | Add a `- **Reviews:**` line and link this review report. |

### Strengths
- The `CacheSource` boundary and separate user-data handling are stated clearly enough to verify in the implementation.
- The decision aligns with the spec’s one-way data flow and the API’s blocked status.
- It names the future API follow-up as T-022.

### Open questions for the author
- none

### Out of my lane
- none
