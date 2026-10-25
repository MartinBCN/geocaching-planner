# T-018: Elevation profile and route stats

- **Status:** Ready
- **Milestone:** M2
- **Depends on:** T-017
- **Requirements:** RTE-4, RTE-5
- **Related ADRs:** ADR-0005

## Goal
An elevation profile chart for the active route, linked to the map, plus a stats panel.

## Scope
### In
- `frontend/src/lib/geo.ts`: cumulative distance (haversine) along the geometry, and downsampling for charting (e.g. at most 1,000 points with min/max preservation).
- An elevation chart (Recharts area chart) with x = distance (km) and y = elevation (m). Hovering shows a tooltip and **puts a marker on the map** at that position. Hovering over the route on the map highlights the chart position (nice to have; make it a separate AC).
- Stats panel: distance, ascent, descent, estimated duration (from avg speed in settings), min/max elevation, and number of waypoints.
- Gracefully hide the chart if the geometry has no elevation.

## Acceptance criteria
- [ ] AC1: Cumulative distance and downsampling are correct (unit tests with known geometries).
- [ ] AC2: The chart renders with the correct axis domains for a fixture route.
- [ ] AC3: Hovering over the chart moves the map hover marker to the matching coordinate.
- [ ] AC4: The stats panel shows correctly formatted values (km with 1 decimal, m as integers, duration as h:mm).
- [ ] AC5 (optional): Hovering over the route line highlights the chart.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1 | unit | `src/lib/geo.test.ts` |
| AC2–AC4 | component | `src/features/routes/ElevationProfile.test.tsx`, `RouteStats.test.tsx` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
