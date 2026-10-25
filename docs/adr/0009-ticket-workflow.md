# ADR-0009: Ticket-driven development in docs/features

- **Status:** Accepted
- **Date:** 2026-10-25
- **Reviews:** [Council review 1](../reviews/adr/0009-ticket-workflow-review-1.md)

## Context
Work is done by coding agents, one ticket at a time, without a hosted issue tracker.

## Decision
- Each unit of work is a markdown file `T-NNN-<slug>.md` that follows `docs/features/TEMPLATE.md`.
- Lifecycle: `docs/features/backlog/` → `active/` (when work starts, max **one** active ticket) → `complete/` (when the Definition of Done is met).
- `docs/drafts/` is untracked scratch space. Ideas only enter `backlog/` after they are refined into the template.
- If `docs/features/active/` contains a ticket, the agent continues that ticket. Otherwise, the agent picks the **lowest-numbered backlog ticket whose status is `Ready` and whose dependencies are all in `complete/`**. When work starts, the ticket is moved to `active/` and its status is changed to `Active`.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Hosted issue tracker | Built-in assignment, discussion, and status views | Adds an external system and separates work tracking from the repository |
| One unstructured backlog document | Minimal file overhead | Harder to scope, review, move, and track completion of individual work items |
| Ticket files with a single active item | Versioned with code and supports one-ticket-at-a-time delivery | Requires maintaining ticket files and moving them through lifecycle folders |

## Consequences
- The git history shows ticket progress.
- Tickets must be small enough for one PR.
