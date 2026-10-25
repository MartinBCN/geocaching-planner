# T-017: Route planning UI

- **Status:** Ready
- **Milestone:** M2
- **Depends on:** T-016, T-011
- **Requirements:** RTE-1, RTE-2, RTE-3, RTE-6, RTE-7
- **Related ADRs:** ADR-0005

## Goal
The user plans a bike route on the map: add waypoints, reorder them, change the profile, and see the route line, similar to BaseCamp.

## Scope
### In
- `/routes`: a list of saved routes (name, distance, ascent, updated). Create, rename, and delete.
- `/routes/:id`: the map with the route editor sidebar.
  - Add a waypoint by clicking the map (in "add mode"), through a "Add to route" action in the cache popup, or by entering coordinates (reuse the parser from T-013).
  - A waypoint list with **dnd-kit** drag-to-reorder, delete, and rename label. Waypoint markers can be dragged on the map to move them.
  - A profile selector (trekking, fastbike, safety).
  - Debounced auto-recompute (500 ms) after changes. Show a loading state on the line, keep the previous line until the new one arrives, and show an error toast with retry on 503/422.
  - The route line is drawn as a GeoJSON line layer. Show distance and ascent in the sidebar.
- Optimistic updates through TanStack Query mutations, with rollback on error.

### Out
- Elevation chart (T-018) and corridor (T-019).

## Acceptance criteria
- [ ] AC1: Clicking the map in add mode appends a waypoint and triggers a compute.
- [ ] AC2: Dragging in the list changes the order and triggers a recompute (PATCH payload order is checked).
- [ ] AC3: "Add to route" from a cache popup adds a cache-linked waypoint.
- [ ] AC4: A routing error shows a non-blocking error with retry, and no edits are lost.
- [ ] AC5: The route list supports create, rename, and delete.
- [ ] AC6: E2E with the BRouter adapter stubbed: create a route with 3 points and see the line and distance.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC5 | component (MSW, mocked map) | `src/features/routes/*.test.tsx` |
| AC6 | e2e | `e2e/route-planning.spec.ts`. The backend runs with `GCP_ROUTING_PROVIDER=fake` (deterministic straight-line provider, **added in this ticket for test use only**). |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] The fake provider is documented in AGENTS.md (test usage)
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
