# T-021: Automatic cache selection and ordering

- **Status:** Draft
- **Milestone:** Phase 2
- **Depends on:** T-020
- **Requirements:** AUTO-1
- **Related ADRs:** a new ADR is required (algorithm choice)

## Goal
Given a start point, an end point (or a loop), a maximum extra distance, and the active filters, the app proposes a set of caches and an order, and routes through them.

## Context
This is an orienteering problem (prize-collecting TSP), so a heuristic is needed. A likely approach: get candidate caches from a corridor around the direct route, use a greedy insertion with the cheapest detour (using straight-line distance), refine with 2-opt, and then validate with real BRouter routing. The BRouter call count must be limited.

## Open questions (resolve before this becomes Ready)
- How to score caches (all equal, or weighted by type, D/T, or favorites — favorites are not in PQ data)?
- Loop routes vs A→B?
- Is a time budget allowed instead of a distance budget?
- Is the result applied as waypoints (editable) or as a separate suggestion layer?

## Acceptance criteria
_To be defined when this ticket is refined._

## Completion notes
_…_
