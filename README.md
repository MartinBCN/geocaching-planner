# Geocaching Planner

[![CI](https://github.com/MartinBCN/geocaching-planner/actions/workflows/ci.yml/badge.svg)](https://github.com/MartinBCN/geocaching-planner/actions/workflows/ci.yml)

A local, single-user app for planning **bicycle geocaching trips**. It combines GSAK-style cache management, BaseCamp-style route planning, and a cycle-focused map.

- Import Geocaching.com **Pocket Query** GPX/ZIP files into a local PostGIS database
- Filter and browse caches on a cycling map (MapLibre + CyclOSM tiles)
- Plan bike routes with a self-hosted **BRouter**, including an elevation profile
- Find caches along your route and export everything as GPX for your Garmin

> Status: specification phase. See the [roadmap](docs/specification.md#10-roadmap).

## Quickstart (after M0 is complete)
```bash
mise trust
mise install            # python 3.14, node, uv, pnpm
mise run setup          # pre-commit hooks, .env from .env.example (a missing .env is fine on a clean clone)
mise run brouter:segments   # download routing data for your region
mise run dev            # postgis + brouter + backend + frontend
```
Then open http://localhost:5173.

Requirements: [mise](https://mise.jdx.dev) and Docker.

## Development / CI
Before merging, require the `backend`, `frontend`, and `pre-commit` GitHub Actions checks. Playwright E2E is available locally with `mise run test:e2e` and is not run on GitHub-hosted runners.

## Local services and data
The PostGIS database uses a named Docker volume (`db-data`). Stopping the stack normally preserves your data, so `docker compose stop` and `docker compose start` keep it. **`docker compose down -v` deletes the database volume and its data.**

BRouter only routes in areas covered by downloaded segment tiles. Tile names use the south-west corner of a 5°×5° area: `E0_N50` covers 0–5°E, 50–55°N, and `E5_N50` covers 5–10°E, 50–55°N. These defaults provide initial coverage for 0–10°E, 50–55°N; areas outside those bounds need additional tiles. Configure `BROUTER_SEGMENTS` and run `mise run brouter:segments` to download them. Each tile uses approximately 100–500 MB of disk space. Segment data is git-ignored.

## Documentation
| Document | Purpose |
|---|---|
| [docs/specification.md](docs/specification.md) | Requirements, architecture, engineering standards |
| [docs/adr/](docs/adr/) | Architecture decision records |
| [docs/features/](docs/features/) | Ticket backlog / active / complete |
| [AGENTS.md](AGENTS.md) | Rules for coding agents |
| [docs/reviews/](docs/reviews/) | Council of the Wise review reports (advisory) |

## Data and licensing notes
- Data flows one way: nothing is ever uploaded to Geocaching.com. No scraping.
- Pocket Query data is for your personal use. Do not commit it.
- Map tiles: follow the tile provider's usage policy and attribution.
