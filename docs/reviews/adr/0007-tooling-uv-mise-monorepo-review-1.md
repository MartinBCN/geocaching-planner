# Council review: 0007-tooling-uv-mise-monorepo (review 1)

- **Target:** `docs/adr/0007-tooling-uv-mise-monorepo.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 2 Major · 3 Minor · 0 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve · Quality & Delivery: Approve with changes

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
- `docs/adr/0000-template.md`

**Anomalies:** none

## Top actions
1. Define precise tool versions and how their pins are updated; “node LTS” and unspecified uv/pnpm versions are not reproducible (QDE-1).
2. Narrow the `mise run` requirement to project tasks so it does not conflict with necessary Git/system workflow commands (ARC-1).
3. Add an Alternatives considered table for the tooling and monorepo decisions (ARC-2, QDE-2).
4. Add a `Reviews:` line and link the council report (QDE-3).
5. Clarify the minimum setup expected of someone installing and running the application (PRD-1).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | QDE-1 | Decision: “pins tool versions (`python 3.14`, `node` LTS, `uv`, `pnpm`)” | “node LTS” is a moving target, and no versions are specified for uv or pnpm, so the toolchain cannot be reliably reproduced or objectively checked. | Specify exact versions for Python, Node, uv, and pnpm, and state how and when those pins are updated. |
| 2 | Major | ARC-1 | Decision: “every developer or agent command is `mise run <task>`”; AGENTS.md §2: “`git mv` the ticket” | Read literally, the rule conflicts with workflow commands that are not mise tasks, leaving unclear whether those commands are permitted. | Narrow the rule to project task commands; allow Git and other system commands required by the workflow. |
| 3 | Minor | ARC-2, QDE-2 | ADR-0007 proceeds from Decision to Consequences without an `Alternatives considered` section; ADR-0000 template: “## Alternatives considered” | The ADR records tooling, repository layout, and package naming decisions without documenting plausible alternatives and trade-offs. | Add concise alternatives and trade-offs for the tooling/task-runner and monorepo choices; consider whether package naming belongs in this ADR's scope. |
| 4 | Minor | QDE-3 | Target has no Reviews line; AGENTS.md says: “Add the report link to the target's `- **Reviews:**` line.” | The ADR lacks the review-tracking field needed to link this report. | Add a `- **Reviews:**` line and link the council report. |
| 5 | Minor | PRD-1 | Consequences: “One entry point for agents (`mise tasks` lists everything).” | The consequence describes the agent benefit but not setup expectations for the intended user, while the README directs users to install mise and the toolchain. | Clarify whether users are expected to install mise and pinned tools, and state the minimum setup required to run the app. |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Whether the ADR needs changes | Product Designer: Approve, with one Minor finding about user setup clarity. | Architect and Quality & Delivery: Approve with changes, citing Major issues with the command rule and reproducible version pins. |
| Importance of documenting alternatives | Architect: Minor; document tooling/task-runner and monorepo trade-offs, and reconsider scope. | Quality & Delivery: Minor; the ADR template requires an alternatives table. Both identify a gap, but emphasize different reasons. |

## Open questions for the author
- Does “every developer or agent command” mean only project task invocations, or is it intended to include Git and other system commands? (ARC-1)

## Strengths
- Clearly separates mise, uv, and pnpm responsibilities.
- The monorepo layout aligns with the specification’s repository structure.
- It explicitly ties scaffold migration to T-001 and records the Python package name correction.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: 0007-tooling-uv-mise-monorepo.md

**Member verdict:** Approve with changes
**Rationale:** The tooling choices align with the accepted architecture, but the command rule is broader than the project workflow can consistently follow.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Decision: “every developer or agent command is `mise run <task>`”; AGENTS.md §2: “`git mv` the ticket” | Read literally, the rule conflicts with workflow commands that are not mise tasks, leaving unclear whether those commands are permitted. | Narrow this to project task commands, e.g. “Run project-defined tasks through `mise run <task>`; use Git and other system commands as required by the workflow.” |
| ARC-2 | Minor | ADR-0000 template: “## Alternatives considered”; ADR-0007 has no alternatives section. | This records several choices—tooling, repository layout, and package naming—without documenting why plausible alternatives were rejected, making the decision harder to revisit. | Add concise alternatives and trade-offs for the tooling/task-runner and monorepo choices; consider whether package naming belongs in this ADR’s scope. |

### Strengths
- Separates mise’s tool/task role from uv’s Python dependency role and pnpm’s frontend dependency role.
- The backend/frontend layout is consistent with the specification’s architecture and repository layout.
- Explicitly records the package name correction and the scaffold migration follow-up in T-001.

### Open questions for the author
- Does “every developer or agent command” mean only project task invocations, or is it intended to include Git and other system commands?

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: docs/adr/0007-tooling-uv-mise-monorepo.md

**Member verdict:** Approve
**Rationale:** The tooling choices support the project’s local development flow, but the ADR should clarify their setup impact for the geocacher running the app.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Minor | Consequences: “One entry point for agents (`mise tasks` lists everything).” | The consequence describes the benefit to agents but not the setup burden for the intended user: the README quickstart also directs users to install the pinned toolchain before running the app. | Clarify whether installing mise and the pinned tools is expected for someone running the app, and state the minimal setup needed for that user. |

### Strengths
- The division of responsibilities between mise, uv, and pnpm is clear.
- The monorepo layout aligns with the specification’s repository structure.
- The Python package name correction is a useful consistency improvement.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: docs/adr/0007-tooling-uv-mise-monorepo.md

**Member verdict:** Approve with changes
**Rationale:** The decision aligns with the specification, but the claimed tool-version pinning is not reproducible as written and the ADR omits required decision and review-record sections.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Decision: “pins tool versions (`python 3.14`, `node` LTS, `uv`, `pnpm`)” | “node LTS” is a moving target, and no versions are specified for `uv` or `pnpm`; therefore, the ADR’s toolchain cannot be reliably reproduced or objectively checked. | Specify exact versions for Python, Node, uv, and pnpm, and state how and when those pins are updated. |
| QDE-2 | Minor | Between Decision and Consequences: the ADR proceeds to “## Consequences” without an Alternatives considered section. | The ADR template requires alternatives, so the decision record does not document what other tooling or layout options were considered. | Add an `## Alternatives considered` table, including relevant options such as other task runners or package-management arrangements and their pros and cons. |
| QDE-3 | Minor | Target has no Reviews line; AGENTS.md says: “Add the report link to the target's `- **Reviews:**` line.” | The ADR does not provide the review-tracking field needed to link this council report. | Add a `- **Reviews:**` line and link this review report once it is saved. |

### Strengths
- Clearly separates mise, uv, and pnpm responsibilities.
- Names the monorepo layout and explicitly ties the scaffold migration to T-001.
- Aligns the tooling choices with specification §9.1.

### Open questions for the author
- none

### Out of my lane
- none
