# Council review: 0008-quality-gates (review 1)

- **Target:** `docs/adr/0008-quality-gates.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 2 Major · 1 Minor · 0 Nit
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
- `docs/adr/0007-tooling-uv-mise-monorepo.md`
- `docs/adr/0000-template.md`

**Anomalies:** none

## Top actions
1. Define and link an enforceable mechanism for requiring the `backend`, `frontend`, and `e2e` checks before merge, and specify how configuration drift is verified (QDE-1).
2. Add an alternatives comparison and link the tickets responsible for implementing the gates and required-check enforcement (ARC-1, QDE-3).
3. State that frontend coverage is measured on `frontend/src/`, excluding the generated client (QDE-2).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | QDE-1 | Decision: “All are required.” | The ADR does not say how the repository ensures these GitHub Actions jobs are required for merging, so the decision cannot be verified from the CI workflow alone. | Specify the enforcement mechanism and link implementation work; for example, a checked-in ruleset requiring the jobs plus a repository check that detects drift. |
| 2 | Major | ARC-1, QDE-3 | ADR-0000 template: “## Alternatives considered”; “Follow-up work (link the backlog tickets).” Neither section appears in ADR-0008. | The ADR chooses tools and thresholds without recording alternatives and trade-offs or identifying implementation ownership. | Add a fair alternatives comparison and link the tickets implementing the quality gates and required-check configuration. |
| 3 | Minor | QDE-2 | Decision: “Vitest + Testing Library + MSW with **≥ 80% line coverage**”; specification §9.2: “Frontend ≥ 80% lines on `src/` excluding generated client” | The ADR omits the coverage measurement scope, leaving ambiguity about whether generated client code is included. | Specify ≥ 80% line coverage on `frontend/src/`, excluding the generated client. |

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Whether the ADR needs changes | Product Designer: Approve, with no findings. | Architect and Quality & Delivery: Approve with changes, citing missing alternatives/follow-up work and unverifiable required-check enforcement. |

## Open questions for the author
- none

## Strengths
- The decision is consistent with the specification’s backend and frontend quality thresholds.
- It names offline test safeguards and the CI jobs expected to block merging.
- It connects local checks to CI and acknowledges setup costs.

## Process notes
- none

---

## Appendix A: Software Architect (raw)
## Software Architect review: 0008-quality-gates.md

**Member verdict:** Approve with changes
**Rationale:** The gates align with the specification, but this ADR omits required decision-record sections for alternatives and follow-up work.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | ADR-0000 template: “## Alternatives considered”; “Follow-up work (link the backlog tickets).” Neither section appears in ADR-0008. | This ADR selects multiple tools and sets coverage and CI requirements without recording alternatives and their trade-offs or linking implementation work, making the decision harder to assess and track. | Add a fair alternatives comparison for the choices made here and identify the tickets that implement the gates. |

### Strengths
- The decision is consistent with the specification’s backend and frontend quality thresholds.
- It names offline test safeguards and required CI jobs.
- It states the operational trade-off of setup cost.

### Open questions for the author
- none

### Out of my lane
- none

## Appendix B: Product Designer (raw)
## Product Designer review: 0008-quality-gates.md

**Member verdict:** Approve
**Rationale:** These gates support a reliable planning and export experience, and the ADR acknowledges their setup cost without introducing user-facing scope.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| – | – | – | No findings | – |

### Strengths
- `mise run check` keeps the local check flow aligned with CI.
- The ADR explicitly acknowledges “Slower first tickets (setup cost)” rather than hiding the trade-off.
- Requiring a reason for per-line lint suppressions helps keep quality safeguards meaningful.

### Open questions for the author
- none

### Out of my lane
- QDE: Please review coverage-gate configuration, CI required-check behavior, and the “mypy (changed files)” pre-commit scope.

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: 0008-quality-gates.md

**Member verdict:** Approve with changes
**Rationale:** The quality thresholds are clear, but the required CI status checks are not objectively enforceable from the stated decision.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Decision: “All are required.” | The ADR does not say how the repository ensures these GitHub Actions jobs are required for merging, so the decision cannot be verified from the CI workflow alone. | Specify the enforcement mechanism and link the follow-up work. For example: “A checked-in ruleset requires `backend`, `frontend`, and `e2e` to pass before merge; a repository check verifies this configuration has not drifted.” |
| QDE-2 | Minor | Decision: “Vitest + Testing Library + MSW with **≥ 80% line coverage**”; specification §9.2: “Frontend ≥ 80% lines on `src/` excluding generated client” | The ADR omits the coverage measurement scope, leaving ambiguity about whether generated client code is included. | Change the decision to: “Vitest + Testing Library + MSW with ≥ 80% line coverage on `frontend/src/`, excluding the generated client.” |
| QDE-3 | Minor | Consequences: “Slower first tickets (setup cost) but safer autonomous work.” | The ADR implies setup work for tooling and CI but does not name follow-up tickets, leaving delivery ownership unclear. | Name the M0 ticket or tickets responsible for implementing these gates, and identify any ticket that configures required CI checks. |

### Strengths
- Gives explicit backend and frontend coverage thresholds.
- Connects local checks to CI through `mise run check`.
- Clearly identifies the CI jobs and the expectation that they block merging.

### Open questions for the author
- None.

### Out of my lane
- None.
