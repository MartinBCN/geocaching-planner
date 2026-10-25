# Geocaching Planner

A local, single-user app for planning **bicycle geocaching trips**. It combines GSAK-style cache management, BaseCamp-style route planning, and a cycle-focused map.

- Import Geocaching.com **Pocket Query** GPX/ZIP files into a local PostGIS database
- Filter and browse caches on a cycling map (MapLibre + CyclOSM tiles)
- Plan bike routes with a self-hosted **BRouter**, including an elevation profile
- Find caches along your route and export everything as GPX for your Garmin

> Status: specification phase. See the [roadmap](docs/specification.md#10-roadmap).

## Quickstart (after M0 is complete)
```bash
mise install            # python 3.14, node, uv, pnpm
mise run setup          # deps, pre-commit hooks, .env from .env.example
mise run brouter:segments   # download routing data for your region
mise run dev            # postgis + brouter + backend + frontend
```
Then open http://localhost:5173.

Requirements: [mise](https://mise.jdx.dev) and Docker.

## Documentation
| Document | Purpose |
|---|---|
| [docs/specification.md](docs/specification.md) | Requirements, architecture, engineering standards |
| [docs/adr/](docs/adr/) | Architecture decision records |
| [docs/features/](docs/features/) | Ticket backlog / active / complete |
| [AGENTS.md](AGENTS.md) | Rules for coding agents |

## Data and licensing notes
- Data flows one way: nothing is ever uploaded to Geocaching.com. No scraping.
- Pocket Query data is for your personal use. Do not commit it.
- Map tiles: follow the tile provider's usage policy and attribution.
