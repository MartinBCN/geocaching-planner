# T-020: Route GPX export

- **Status:** Ready
- **Milestone:** M2
- **Depends on:** T-019, T-014
- **Requirements:** EXP-4
- **Related ADRs:** –

## Goal
Export a planned route as a Garmin-friendly GPX: the track with elevation, plus (optionally) the selected corridor caches.

## Scope
### In
- `GET /api/v1/routes/{id}/export.gpx?caches=selected|none` (default `selected`). Also `&format=track` (default) or `route`, where `route` emits a `<rte>` with only the waypoints for devices that recalculate.
- GPX 1.1 `<trk><trkseg>` with `<ele>`, and `<metadata>` with the name and time. Garmin limits: a warning (header or response note) if there are more than 10,000 trackpoints. Optionally simplify with Douglas-Peucker (`tolerance_m` param, default off).
- Caches are written as `<wpt>`, reusing the T-014 writer. **Decision for the implementer:** produce **two files in a ZIP** (`route.gpx` with GPX 1.1 track, and `caches.gpx` with GPX 1.0 + Groundspeak) when caches are included, because mixing Groundspeak 1.0 extensions into GPX 1.1 is unreliable on Garmin. Record the choice in the completion notes.
- UI: an "Export" button in the route editor with options.

## Acceptance criteria
- [ ] AC1: The track GPX validates against the GPX 1.1 XSD, and the elevation is present.
- [ ] AC2: With selected caches, the ZIP contains a valid cache GPX with exactly the selected caches (effective coordinates).
- [ ] AC3: `format=route` emits the waypoints in order.
- [ ] AC4: Simplification reduces the point count and stays within the tolerance (unit test).
- [ ] AC5: Manual check: the files load in BaseCamp or on a Garmin device (record the result).

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1, AC3, AC4 | unit | `tests/unit/adapters/test_route_gpx_writer.py` |
| AC2 | integration | `tests/integration/api/test_route_export.py` |
| AC5 | manual | Completion notes |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
