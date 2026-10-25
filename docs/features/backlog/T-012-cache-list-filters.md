# T-012: Cache list and filter panel

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-011
- **Requirements:** CAC-1, CAC-2, MAP-4
- **Related ADRs:** –

## Goal
A filter panel and a sortable, paged cache list next to the map, which share one filter state with the map.

## Scope
### In
- A filter state store (React context or `zustand`; note the dependency choice) that is **synced to URL search params**, so filters can be shared and restored when the page reloads.
- Filter panel: type multi-select, size multi-select, D and T range sliders (1–5, 0.5 steps), found tri-state, include archived and disabled toggles, max distance (disabled with a hint if no home location is set), and a text search.
- List: columns GC code, name, type icon, D, T, size, distance, and found. Sort by clicking a header. Server-side paging (page size 50). Clicking a row opens the cache details. Hovering over a row highlights the marker.
- Layout: a resizable split between map and sidebar (list and filters), usable at ≥1280 px wide. Mobile is out of scope.
- Show "X caches match" using `total`.

## Acceptance criteria
- [ ] AC1: Changing a filter updates both the list and the map markers (one shared query parameter set).
- [ ] AC2: Filter state survives a page reload through the URL.
- [ ] AC3: Sorting and paging call the API with the correct params.
- [ ] AC4: The distance filter is disabled when no home location is set.
- [ ] AC5: Hovering over a row highlights the corresponding marker.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC4 | component (MSW) | `src/features/caches/*.test.tsx`, `src/features/filters/*.test.tsx` |
| AC1, AC2, AC5 | e2e | `e2e/filters.spec.ts` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
