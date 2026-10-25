# T-015: BRouter routing adapter

- **Status:** Ready
- **Milestone:** M2
- **Depends on:** T-005
- **Requirements:** RTE-3, RTE-7, NFR-2
- **Related ADRs:** ADR-0004

## Goal
A typed `RoutingProvider` that turns an ordered list of points and a profile into a route geometry with elevation and stats, implemented against the local BRouter.

## Context
BRouter HTTP API: `GET /brouter?lonlats=lon,lat|lon,lat|...&profile=trekking&alternativeidx=0&format=geojson`. The GeoJSON feature has 3D coordinates `[lon, lat, ele]` and properties such as `track-length`, `filtered ascend`, `plain-ascend`, and `total-time`. Errors come back as HTTP 400/500 with a plain-text message (e.g. "position not mapped in existing datafile").

## Scope
### In
- `services/ports.py`: `RoutingProvider` protocol, `async route(points: Sequence[Coordinates], profile: str) -> RouteResult` (`geometry: list[(lon, lat, ele|None)]`, `distance_m`, `ascent_m`, `descent_m`, `duration_s|None`).
- Domain errors: `RoutingUnavailable` (connection or timeout), `RoutingFailed(reason)` (no route, or point not in the segment data), and `InvalidProfile`.
- `adapters/brouter/client.py` using `httpx.AsyncClient`, with a configurable base URL (`GCP_BROUTER_URL`), a timeout (`GCP_BROUTER_TIMEOUT_S`, default 30), and a profile allowlist (`trekking`, `fastbike`, `safety`). It handles at most BRouter's waypoint limit, and splits and stitches if needed. **Compute descent** from the elevation series, using the same hysteresis-filtered approach as BRouter's ascent (document the threshold, e.g. 10 m).
- Health endpoint: add `brouter: ok|error` (a cheap request or a TCP check).
- **Contract tests** use recorded BRouter responses (`tests/fixtures/brouter/*.json` and error texts) through `respx`. Record them once from the local BRouter using a script `tests/contract/record_brouter.py`.
- A live test `@pytest.mark.brouter` runs against compose BRouter. It is skipped when BRouter is unreachable and is opt-in in CI.

## Acceptance criteria
- [ ] AC1: A successful response maps to `RouteResult` with correct distance, ascent, and descent, and a 3D geometry.
- [ ] AC2: A connection error or timeout raises `RoutingUnavailable`. A BRouter "not mapped" error raises `RoutingFailed` with the message.
- [ ] AC3: An unknown profile raises `InvalidProfile` without calling BRouter.
- [ ] AC4: The descent calculation is correct on synthetic elevation series (flat, monotonic, noisy).
- [ ] AC5: Health reports the BRouter status.
- [ ] AC6: The live test passes locally with segments downloaded.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC3 | contract (respx) | `tests/contract/test_brouter_client.py` |
| AC4 | unit | `tests/unit/domain/test_elevation.py` |
| AC5 | unit | `tests/unit/api/test_health.py` |
| AC6 | live (marker `brouter`) | `tests/contract/test_brouter_live.py` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] `.env.example` is updated
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
