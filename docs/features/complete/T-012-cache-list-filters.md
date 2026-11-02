# T-012: Cache list and filter panel

- **Status:** Complete
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
- [x] AC1: Changing a filter updates both the list and the map markers (one shared query parameter set).
- [x] AC2: Filter state survives a page reload through the URL.
- [x] AC3: Sorting and paging call the API with the correct params.
- [x] AC4: The distance filter is disabled when no home location is set.
- [x] AC5: Hovering over a row highlights the corresponding marker.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC4 | component (MSW) | `frontend/src/features/map/CacheBrowser.test.tsx`, `frontend/src/features/map/MapView.test.tsx` |
| AC1, AC2, AC5 | e2e | `frontend/e2e/filters.spec.ts` |

## Definition of Done
- [x] All ACs are covered
- [x] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
- Added the resizable map/sidebar workspace, cache filter panel, sortable 50-item list, match total, row navigation, and distance/home-location hint.
- Filter state uses a React context backed directly by React Router URL search parameters; no new dependency was added. The same parsed filters drive cache-list and marker requests and survive reloads.
- Hovering or keyboard-focusing a row pans to its cache when needed and displays a dedicated marker highlight, including when that cache is outside the current map viewport.
- Added MSW component coverage for shared filters, URL restoration, API sort/paging parameters, no-home distance behavior, and marker highlighting, plus `e2e/filters.spec.ts`.
- Updated the README map overview.
- Validation: `mise run check` passed; `mise exec -- pnpm --dir frontend e2e e2e/filters.spec.ts` passed.
