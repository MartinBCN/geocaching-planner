# ADR-0005: Frontend with React, TypeScript, Vite, MapLibre GL

- **Status:** Accepted
- **Date:** 2026-10-25
- **Reviews:** [Council review 1](../reviews/adr/0005-frontend-react-maplibre-review-1.md)

## Context
The UI is map-heavy: thousands of clustered markers, route drawing, drag-and-drop waypoints, and an elevation chart. Coding agents will build most of it.

## Decision
We will use **React + TypeScript (strict) + Vite**, with **MapLibre GL JS** for the map (via `react-map-gl/maplibre`), **TanStack Query** for server state, **Recharts** for the elevation profile, **dnd-kit** for drag-and-drop, and **pnpm** as the package manager. API types and client are generated from the backend OpenAPI schema (`openapi-typescript` + `openapi-fetch`). The map tile URL is configured through the `Settings.tile_url` override; the map displays the attribution required by the configured tile provider. `mise run api:gen` generates the committed client schema; CI runs this task and fails if it changes the generated schema (T-004, T-005).

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| SvelteKit | Less boilerplate | Smaller ecosystem, agents know it less well |
| Vue 3 | Approachable | Same |
| HTMX + Leaflet | No build step | Rich map interactions get awkward |
| Leaflet instead of MapLibre | Simple | Slower with many markers; no GPU clustering |
| Redux Toolkit Query instead of TanStack Query | Integrated with Redux state | Adds Redux state-management overhead for this app's server state |
| Custom SVG instead of Recharts | No charting dependency | More implementation and accessibility work for the elevation chart |
| Native HTML drag-and-drop instead of dnd-kit | No additional library | More work to provide the route editor's consistent pointer and keyboard interactions |

## Consequences
- Needs a Node toolchain (pinned by mise).
- An OpenAPI-generated client keeps the frontend and backend contracts in sync. Regeneration is a mise task, and CI checks for drift.
