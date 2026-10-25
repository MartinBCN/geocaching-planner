# ADR-0004: Self-hosted BRouter for bicycle routing

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
Bicycle route planning needs a routing engine that is bike-aware, works offline, and reports elevation. Building our own is out of scope.

## Decision
We will run **BRouter** as a Docker Compose service with locally downloaded `.rd5` segment files (git-ignored, downloaded with `mise run brouter:segments`). The backend accesses it through a `RoutingProvider` protocol. The BRouter adapter is the only implementation for now. Default profile: `trekking`. Also exposed: `fastbike` and `safety`.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| OpenRouteService API | Easy start | API key, rate limits, needs internet |
| GraphHopper self-hosted | Fast, flexible | Heavier import, bike profiles need more setup |
| Valhalla | Powerful | Larger footprint; less popular with cyclists |

## Consequences
- Fully offline routing. Elevation comes in the GeoJSON output (3D coordinates) and in `filtered ascend`.
- Segment files need disk space (100–500 MB per 5°×5° tile).
- `RoutingProvider` lets us swap engines later.
