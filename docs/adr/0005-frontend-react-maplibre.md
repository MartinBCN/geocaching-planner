# ADR-0005: Frontend with React, TypeScript, Vite, MapLibre GL

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
The UI is map-heavy: thousands of clustered markers, route drawing, drag-and-drop waypoints, and an elevation chart. Coding agents will build most of it.

## Decision
We will use **React + TypeScript (strict) + Vite**, with **MapLibre GL JS** for the map (via `react-map-gl/maplibre`), **TanStack Query** for server state, **Recharts** for the elevation profile, **dnd-kit** for drag-and-drop, and **pnpm** as the package manager. API types and client are generated from the backend OpenAPI schema (`openapi-typescript` + `openapi-fetch`). The base map is a configurable raster style (default: CyclOSM tiles with attribution).

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| SvelteKit | Less boilerplate | Smaller ecosystem, agents know it less well |
| Vue 3 | Approachable | Same |
| HTMX + Leaflet | No build step | Rich map interactions get awkward |
| Leaflet instead of MapLibre | Simple | Slower with many markers; no GPU clustering |

## Consequences
- Needs a Node toolchain (pinned by mise).
- An OpenAPI-generated client keeps the frontend and backend contracts in sync. Regeneration is a mise task, and CI checks for drift.
