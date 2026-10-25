# T-019: Caches along route (corridor)

- **Status:** Ready
- **Milestone:** M2
- **Depends on:** T-017, T-012
- **Requirements:** CAR-1, CAR-2, CAR-3
- **Related ADRs:** ADR-0006

## Goal
Show which caches lie within X m of the planned route, ordered along the route, so the user can pick which ones to do.

## Scope
### In
- `GET /api/v1/routes/{id}/caches?width_m=500&<cache filters>`: uses `ST_DWithin(effective_location, route.geometry, width_m)` plus `apply_cache_filter`. Returns the cache summary plus `along_m` (`ST_LineLocatePoint` × route length) and `off_route_m` (`ST_Distance`), ordered by `along_m`. Returns 409 if the route is not computed or is stale.
- A selection is persisted per route: a table `route_selected_caches(route_id, gc_code)` with migration, and `PUT /api/v1/routes/{id}/selected-caches` with `{gc_codes: []}`.
- UI in the route editor: a corridor width slider (100–2,000 m, default from settings), a toggle to show the corridor buffer on the map (a client-side buffer via `@turf/buffer` is acceptable for display only), a corridor cache list with checkboxes (select all or none), and the counts "N in corridor / M selected". Selected caches are highlighted on the map. The active global filters apply.

### Out
- Automatic rerouting through the selected caches (T-021).

## Acceptance criteria
- [ ] AC1: Only caches within the width are returned. A cache just inside or just outside the boundary is handled correctly (fixtures with known distances).
- [ ] AC2: The ordering by `along_m` matches the position along the route.
- [ ] AC3: Corrected coordinates are used.
- [ ] AC4: Global filters (e.g. not found, D ≤ 3) narrow the corridor results.
- [ ] AC5: A stale or uncomputed route returns 409 problem+json.
- [ ] AC6: The selection persists and is restored when the route is reopened.
- [ ] AC7: Corridor query for a 100 km route with 50k caches takes under 500 ms (slow test).

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC6 | integration | `tests/integration/api/test_route_corridor.py` |
| AC7 | integration (slow) | `tests/integration/perf/test_corridor_perf.py` |
| UI | component + e2e | `src/features/routes/CorridorPanel.test.tsx`, `e2e/corridor.spec.ts` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
