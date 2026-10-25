# ADR-0009: Ticket-driven development in docs/features

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
Work is done by coding agents, one ticket at a time, without a hosted issue tracker.

## Decision
- Each unit of work is a markdown file `T-NNN-<slug>.md` that follows `docs/features/TEMPLATE.md`.
- Lifecycle: `docs/features/backlog/` → `active/` (when work starts, max **one** active ticket) → `complete/` (when the Definition of Done is met).
- `docs/drafts/` is untracked scratch space. Ideas only enter `backlog/` after they are refined into the template.
- An agent picks the **lowest-numbered backlog ticket whose dependencies are all in `complete/`** and whose status is not `Blocked`.

## Consequences
- The git history shows ticket progress.
- Tickets must be small enough for one PR.
