# Council review: 0009-ticket-workflow (review 1)

- **Target:** `docs/adr/0009-ticket-workflow.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Revise & resubmit**
- **Findings:** 1 Blocker · 0 Major · 1 Minor · 0 Nit
- **Member verdicts:** Architect: Revise & resubmit · Product Designer: Approve with changes · Quality & Delivery: Revise & resubmit

## Context provided
- `README.md`
- `AGENTS.md`
- `docs/specification.md`
- `docs/adr/0001-record-architecture-decisions.md`
- `docs/adr/0002-local-single-user-deployment.md`
- `docs/adr/0003-gpx-first-pluggable-cache-source.md`
- `docs/adr/0004-brouter-routing.md`
- `docs/adr/0005-frontend-react-maplibre.md`
- `docs/adr/0006-postgis.md`
- `docs/adr/0007-tooling-uv-mise-monorepo.md`
- `docs/adr/0008-quality-gates.md`
- `docs/adr/0000-template.md`

**Anomalies:** none

## Top actions
1. Align the pick rule with `AGENTS.md`: continue the existing active ticket; otherwise choose the lowest-numbered backlog ticket with `Status: Ready` and all dependencies complete; set it Active when starting work (ARC-1, QDE-1, PRD-1).
2. Add an `Alternatives considered` section with the options and trade-offs (ARC-2, QDE-2).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Blocker | ARC-1, QDE-1, PRD-1 | Decision: “whose status is not `Blocked`”; AGENTS.md §2: “Status` is `Ready` (not `Draft` or `Blocked`)” | The ADR permits selecting Draft tickets while AGENTS.md requires Ready tickets, and the ADR omits the instruction to continue an existing active ticket. The conflicting rules make the workflow inconsistent and could direct agents to unrefined work. | Continue the existing active ticket if one exists; otherwise select the lowest-numbered backlog ticket with `Status: Ready` and dependencies in `complete/`. State that starting work changes its status to `Active`. |
| 2 | Minor | ARC-2, QDE-2 | ADR-0001: “based on `0000-template.md`”; ADR-0009: `## Decision` | The ADR omits the template’s `Alternatives considered` section and does not explain why this workflow was chosen over alternatives. | Add an alternatives section with the options considered and their trade-offs. |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Severity of the ticket-picking conflict | Architect and Quality & Delivery: Blocker, because it conflicts with the documented agent workflow and can cause agents to select the wrong ticket. | Product Designer: Major, because Draft tickets may be started despite the Ready-only rule. The consolidated finding retains Blocker, the higher severity. |
| Overall verdict | Architect and Quality & Delivery: Revise & resubmit. | Product Designer: Approve with changes. |

## Open questions for the author
- none

## Strengths
- The ticket lifecycle and one-active-ticket limit are explicit.
- The rule that draft ideas must be refined before entering the backlog supports predictable delivery.
- Ticket completion is connected to the Definition of Done.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: 0009-ticket-workflow.md

**Member verdict:** Revise & resubmit  
**Rationale:** The ticket-selection rule conflicts with the agent workflow and could cause agents to start the wrong ticket.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Blocker | Decision: “whose status is not `Blocked`”; AGENTS.md §2: “If `docs/features/active/` already contains a ticket, continue that one instead.” | The ADR permits selecting a Draft ticket and does not say to continue an existing active ticket, while AGENTS.md requires Ready tickets and prioritizes the active ticket. This leaves agents with conflicting instructions. | Align the selection rule with AGENTS.md: continue the active ticket if one exists; otherwise select the lowest-numbered Ready backlog ticket whose dependencies are complete. |
| ARC-2 | Minor | ADR-0001: “based on `0000-template.md`”; ADR-0009: `## Decision` | The ADR omits the template’s `Alternatives considered` section, so it does not explain why this workflow was chosen over alternatives. | Add an alternatives section with the options considered and their trade-offs. |

### Strengths
- Defines a clear ticket lifecycle and a maximum of one active ticket.
- Keeps unrefined ideas in drafts until they are ready to enter the backlog.
- Connects ticket completion to the Definition of Done.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: docs/adr/0009-ticket-workflow.md

**Member verdict:** Approve with changes  
**Rationale:** The lifecycle is easy to follow, but its ticket-picking rule conflicts with the existing Ready-status gate and could send agents to Draft work.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Major | Decision: “whose status is not `Blocked`”; AGENTS.md §2: “Status is `Ready` (not `Draft` or `Blocked`)” | The ADR permits picking Draft tickets, while the existing workflow requires Ready status. This makes it unclear which work is refined enough to start. | Change the picking rule to require `Status` = `Ready`, and state that starting work changes the status to `Active`. |
### Strengths
- The backlog → active → complete lifecycle makes progress visible in git.
- Limiting work to one active ticket supports focused, predictable progress.
- Keeping unrefined ideas in scratch space avoids treating them as implementation-ready.

### Open questions for the author
- None.

### Out of my lane
- None.

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: docs/adr/0009-ticket-workflow.md

**Member verdict:** Revise & resubmit
**Rationale:** The accepted pick rule conflicts with the explicit Ready-only workflow, leaving agents without a consistent way to choose work.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Blocker | Decision: “whose status is not `Blocked`”; AGENTS.md §2: “Status` is `Ready` (not `Draft` or `Blocked`)” | The ADR permits selecting Draft tickets, while AGENTS.md excludes them. AGENTS.md also instructs agents to stop and report conflicts, so the workflow cannot be followed consistently. | Replace the pick rule with: “An agent picks the lowest-numbered backlog ticket whose status is `Ready` and whose dependencies are all in `complete/`.” |
| QDE-2 | Minor | ADR structure: “## Decision”; `docs/adr/0000-template.md`: “## Alternatives considered” | The ADR omits a section required by its stated template. | Add an “Alternatives considered” section, noting alternatives were not considered if applicable. |

### Strengths
- The ticket lifecycle and one-active-ticket limit are explicit.
- The rule that draft ideas must be refined into the ticket template before entering the backlog supports predictable delivery.

### Open questions for the author
- none

### Out of my lane
- none
