# T-011: Map view with cache markers

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-010
- **Requirements:** MAP-1, MAP-2, MAP-3
- **Related ADRs:** ADR-0005

## Goal
The home page shows a full-screen cycle map with clustered cache markers for the current viewport.

## Scope
### In
- Deps: `maplibre-gl`, `react-map-gl` (maplibre entry).
- A raster style built from the settings tile URL and attribution (default CyclOSM `https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png`, with attribution "© OpenStreetMap contributors, CyclOSM").
- A GeoJSON source from `/caches/markers` with **MapLibre native clustering**. Markers are styled per cache type (colored circles or sprite icons). Found caches get a distinct style (e.g. smiley or a dimmed color). Disabled caches are shown with reduced opacity.
- Data is refetched on `moveend` (debounced 300 ms) with the bbox of the viewport. A query key includes the bbox and filters.
- Clicking a cluster zooms in. Clicking a cache opens a popup (name, GC code, type, D/T, size, link to `/caches/:gc`).
- The initial view is the home location (if set), otherwise the bounds of all caches, otherwise the Netherlands.
- Settings page: the home location can now be picked on the map.
- Encapsulate MapLibre in a `MapView` component. Unit tests mock `react-map-gl`. Real rendering is covered by e2e.
- Show a banner when `truncated` is true ("Zoom in to see all caches").

## Acceptance criteria
- [ ] AC1: After importing a fixture, markers appear at the correct positions (e2e).
- [ ] AC2: Panning triggers one debounced fetch with the new bbox (component test with a mocked map).
- [ ] AC3: Clicking a marker shows a popup with the correct cache data.
- [ ] AC4: Tile attribution is visible.
- [ ] AC5: Found, disabled, and corrected caches are visually distinguishable (style expression unit test).

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1, AC3, AC4 | e2e | `e2e/map.spec.ts` |
| AC2 | component | `src/features/map/MapView.test.tsx` |
| AC5 | unit | `src/features/map/styles.test.ts` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
