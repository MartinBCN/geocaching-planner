# ADR-0010: Council review for ADRs and tickets

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
ADRs and tickets are implemented by autonomous coding agents (ADR-0009). Gaps in architecture, user value, or testability are cheap to fix on paper and expensive to fix in code. A single reviewer, human or AI, tends to see the document from one angle.

## Decision
We will provide an on-demand **Council of the Wise** review as a Copilot CLI project skill (`.github/skills/council-review/`). It is backed by three read-only custom agents (`.github/agents/council-*.agent.md`):

| Member | Lens |
|---|---|
| Software Architect | Consistency with Accepted ADRs and the spec, layering, data model, NFRs, reversibility |
| Product Designer | User value for the bicycle geocacher, flows, UI states, scope fit |
| Quality & Delivery Engineer | Testable ACs, test plan coverage, sizing, dependencies, agent executability |

- The members run **in parallel and independently**. The skill acts as Chair and combines their output. It never lowers a severity, and it reports dissent explicitly.
- The context is fixed by rule (`context-rules.md`): base docs, plus lower-numbered Accepted ADRs (for an ADR), or all Accepted ADRs, the dependency tickets, and the template (for a ticket).
- The output is a report in `docs/reviews/adr/<stem>-review-<n>.md` (ADRs) or `docs/reviews/features/<stem>-review-<n>.md` (tickets), with a verdict of **Approve / Approve with changes / Revise & resubmit**. The verdict is deterministic: any Blocker → Revise; any Major → Approve with changes.
- The review is **advisory**: it is recommended before an ADR becomes Accepted and before a ticket moves Draft→Ready. It is not a hard gate. The council never edits the reviewed document.
- All members use the default model (no model pinning).

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| A single agent playing three personas | Cheap, fast | Members agree with each other; less real disagreement |
| A mandatory gate | Enforced quality | Friction for small changes; agents could get stuck |
| Different models per member | More diverse opinions | Ties the setup to specific model names; maintenance |
| Auto-applying fixes | Fast | Hides decisions from the owner; risk of silent drift |

## Consequences
- A review costs about four agent runs. It is used deliberately, not on every edit.
- Reviews are tracked in git, which gives an audit trail of how decisions and tickets evolved.
- Changing the members, the verdict rule, or the gate status needs a new ADR.
