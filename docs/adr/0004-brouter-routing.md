# ADR-0004: Self-hosted BRouter for bicycle routing

- **Status:** Accepted
- **Date:** 2026-10-25
- **Reviews:** [Council review 2](../reviews/adr/0004-brouter-routing-review-2.md)

## Context
Bicycle route planning needs a routing engine that is bike-aware, works offline, and reports elevation. Building our own is out of scope.

## Decision
We will run **BRouter** as a Docker Compose service with locally downloaded `.rd5` segment files (git-ignored, downloaded with `mise run brouter:segments`). The backend accesses it through a `RoutingProvider` protocol. The BRouter adapter is the only implementation for now. Default profile: `trekking`. Also exposed: `fastbike` and `safety`. Routing requires segment coverage for the route area; when coverage is missing, the adapter reports a routing failure that the UI presents with an actionable error.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| BRouter (chosen) | Bike-aware profiles; local routing works offline; GeoJSON includes elevation | Requires regional segment downloads and disk space; errors for points outside segment coverage |
| OpenRouteService API | Easy start | API key, rate limits, needs internet; does not meet offline-routing requirement |
| GraphHopper self-hosted | Fast, flexible | Heavier import; bike profiles need more setup |
| Valhalla | Powerful | Larger footprint; less popular with cyclists |

BRouter best fits the requirement for local, bike-aware routing with elevation without requiring us to build an engine or depend on an online routing API.

## Consequences
- Fully offline routing when the route area has downloaded segment coverage. Elevation comes in the GeoJSON output (3D coordinates); the adapter computes ascent and descent from the elevation series (T-015), and route persistence and statistics are handled by T-016.
- Segment files need disk space (100–500 MB per 5°×5° tile). The Compose service and segment downloader are delivered in T-023; adapter and profile support in T-015; route API integration in T-016; and user-facing route errors in T-017. T-003 owns PostGIS and database migrations.
- `RoutingProvider` lets us swap engines later.
