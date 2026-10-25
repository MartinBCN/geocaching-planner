# T-016: Route domain and API

- **Status:** Ready
- **Milestone:** M2
- **Depends on:** T-015, T-006
- **Requirements:** RTE-1, RTE-2, RTE-4, RTE-6, RTE-7
- **Related ADRs:** ADR-0004, ADR-0006

## Goal
Persisted routes with ordered waypoints that can be (re)computed through the `RoutingProvider`, with stats.

## Scope
### In
- Domain: `Route`, `RouteWaypoint` (position, location, label, optional `cache_gc_code`, which uses the cache's effective location at compute time).
- Tables and migration: `routes` (geometry `geography(LineStringZ,4326)` nullable, stats, profile, `computed_at`, `stale` flag) and `route_waypoints`.
- `services/route_service.py`: create, update (name, profile, full waypoint list replacement), delete, and compute. A waypoint or profile change sets `stale=true`. Compute calls the provider and stores the geometry and stats (`duration_s = distance / settings.avg_speed_kmh` if the provider has no time). **If compute fails, the waypoints are kept** and the error is returned (RTE-7).
- API:
  - `GET/POST /api/v1/routes`
  - `GET/PATCH/DELETE /api/v1/routes/{id}`. PATCH accepts `name`, `profile`, and `waypoints[]`, and recomputes automatically if `auto_compute=true` (default).
  - `POST /api/v1/routes/{id}/compute`
  - BRouter errors map to `503` (`RoutingUnavailable`) or `422` (`RoutingFailed`) problem+json.
  - The route GET returns the geometry as a GeoJSON LineString with elevation.
- Validation: 2 to 50 waypoints for compute. A route can be saved with fewer.

## Acceptance criteria
- [ ] AC1: CRUD works. Waypoint order is preserved.
- [ ] AC2: Compute stores the geometry and stats. The response includes GeoJSON with z values.
- [ ] AC3: A waypoint linked to a cache uses its corrected coordinates when they are set.
- [ ] AC4: When the provider is unavailable, the API returns 503, the waypoints stay saved, and the route stays `stale`.
- [ ] AC5: Changing the waypoints marks the route stale until it is recomputed.
- [ ] AC6: Duration falls back to avg speed from settings.

## Test plan
| AC | Level | Test |
|---|---|---|
| service logic | unit (fake provider, fake repo) | `tests/unit/services/test_route_service.py` |
| AC1–AC5 | integration (PostGIS + fake provider injected) | `tests/integration/api/test_routes.py` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] `api:gen` is run
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
