# ADR-0011: Client-side frontend routing

- **Status:** Accepted
- **Date:** 2026-10-25
- **Reviews:** –

## Context
The frontend needs stable URLs for the map, cache details, routes, route details, settings, and imports. T-004 introduces these routes before the feature pages are implemented, and later tickets depend on the route scheme. ADR-0005 selects the frontend framework and libraries but does not select a routing library.

## Decision
We will use **React Router** for client-side routing, with `/` for the map, `/caches/:gc` for cache details, `/routes` and `/routes/:id` for route pages, `/settings` for settings, and `/import` for imports. Unknown paths render a not-found page with a link back to the map.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| React Router (chosen) | Established React routing library; supports the required route structure and nested layouts | Adds a frontend dependency and routing conventions |
| TanStack Router | Strong TypeScript route inference and integration with the existing TanStack stack | Adds a separate route-definition workflow and dependency |
| No routing library | Avoids a dependency for a small initial shell | Requires custom URL/history handling as feature pages are added |

## Consequences
- T-004 lists ADR-0011 as a related ADR and uses the route paths defined here.
- The application shell needs a not-found state and links that work with browser navigation.
- This decision does not specify how the production server provides SPA history fallback; that remains to be specified by the owning ticket.
