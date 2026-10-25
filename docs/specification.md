# Geocaching Planner — Specification

> Status: **Accepted** · This document replaces `docs/drafts/project_outline.md`.
> Changes to this document must follow the rules in [`AGENTS.md`](../AGENTS.md). Architectural changes need an ADR first.

## 1. Vision

The Geocaching Planner is a **local, single-user** application for geocachers who plan **bicycle trips**. It combines the best parts of three tools:

| Inspiration | What we take from it |
|---|---|
| GSAK | Offline cache database built from Pocket Query imports, with filtering, user notes, corrected coordinates, and GPX export |
| Garmin BaseCamp | Route planning with waypoints, distance, and elevation profile, plus export to a Garmin device |
| OpenFietsMap | A cycle-focused map style (in the browser: CyclOSM-style raster tiles) |

Main user flow: *import my Pocket Queries → see caches on a cycling map → plan a bike route → find caches along that route → export route + caches to my Garmin.*

## 2. Scope

### 2.1 In scope (Phase 1 = MVP, Phase 2 = planned)
- Phase 1: Import of Pocket Query GPX/ZIP files, including additional-waypoint files.
- Phase 1: Local cache database with filtering, map, list, detail view, user notes, and corrected coordinates.
- Phase 1: Bicycle route planning through user-chosen waypoints, using a self-hosted BRouter.
- Phase 1: Elevation profile and route statistics.
- Phase 1: "Caches along route" (corridor search).
- Phase 1: Garmin-compatible GPX export of caches and routes.
- Phase 2: Automatic selection and ordering of caches along or around a route.
- Phase 2 (blocked): Geocaching.com API as an extra cache source, once partner access is available.

### 2.2 Non-goals
- Uploading anything to Geocaching.com (logs, found status). Data flow is **one-way only**.
- Scraping Geocaching.com. It is forbidden by their ToS.
- Multi-user support, accounts, authentication, or public hosting.
- Native mobile or desktop apps.
- Offline vector tiles or producing Garmin `.img` maps.
- A GSAK-style macro or scripting language.

## 3. Constraints and assumptions
- The user is a Geocaching.com **Premium** member and downloads Pocket Queries manually.
- The app runs on the user's machine: backend on `localhost`, UI in a browser, PostGIS and BRouter in Docker Compose.
- Map tiles come from a configurable tile URL (CyclOSM by default). We follow the tile provider's usage policy: low volume, a proper attribution, and no bulk prefetching.
- No real geocaching.com data is committed to the repository. Test fixtures are synthetic.

## 4. Functional requirements

IDs are stable. Tickets reference them.

### 4.1 Cache import (IMP)
| ID | Requirement |
|---|---|
| IMP-1 | The user can upload one or more `.gpx` or `.zip` Pocket Query files through the UI. |
| IMP-2 | The parser supports GPX 1.0 and 1.1 with Groundspeak cache extensions (`groundspeak:cache` 1.0/1.0.1). |
| IMP-3 | Additional waypoints (`*-wpts.gpx` / waypoints in the same ZIP) are linked to their parent cache by GC code suffix. |
| IMP-4 | Import is an **upsert keyed on GC code**. Re-importing updates source fields but **never overwrites user data** (notes, corrected coordinates). |
| IMP-5 | Logs in the PQ are stored, deduplicated by log id. |
| IMP-6 | An import returns a summary (created, updated, unchanged, waypoints, errors) and is recorded in an import history. |
| IMP-7 | Malformed files fail with a clear error. A single bad cache entry does not abort the whole import. It is reported in the summary. |
| IMP-8 | Import is implemented behind a `CacheSource` interface, so other sources (e.g. the Geocaching.com API) can be added without changing the domain. |

### 4.2 Cache management (CAC)
| ID | Requirement |
|---|---|
| CAC-1 | List caches with paging and sorting (name, GC code, D, T, distance, placed date). |
| CAC-2 | Filter by: cache type, container size, difficulty range, terrain range, found/not found, archived/disabled, distance from home (km), and map bounding box. |
| CAC-3 | Show cache details: description (sanitized HTML), hints (ROT13 toggle), attributes, recent logs, and additional waypoints. |
| CAC-4 | The user can add or edit a free-text **note** per cache. |
| CAC-5 | The user can set or clear **corrected coordinates**. When set, they are used for the map, distance, corridor search, and export. The original coordinates are kept and still visible. |
| CAC-6 | The user can configure a **home location** (lat/lon) in settings. It is used for distance filters and sorting. |

### 4.3 Map (MAP)
| ID | Requirement |
|---|---|
| MAP-1 | A MapLibre GL map with a configurable cycle raster style (default CyclOSM) and correct attribution. |
| MAP-2 | Caches are rendered as clustered markers, styled by type, with found/disabled state visible. They are loaded per viewport (bbox) and respect the active filters. |
| MAP-3 | Clicking a marker opens a popup with key info and a link to the details. |
| MAP-4 | The map, list, and filters share state. A filter change updates both. |

### 4.4 Route planning (RTE)
| ID | Requirement |
|---|---|
| RTE-1 | The user creates a named route by adding waypoints: click on the map, pick a cache, or enter coordinates. |
| RTE-2 | Waypoints can be reordered (drag and drop) and removed. The route recalculates automatically. |
| RTE-3 | Routing uses BRouter with a selectable bike profile (default: `trekking`; also `fastbike` and `safety`). |
| RTE-4 | Route stats: total distance, total ascent, total descent, and estimated duration (configurable average speed). |
| RTE-5 | Elevation profile chart. Hovering over the chart highlights the position on the map. |
| RTE-6 | Routes are saved, listed, opened, renamed, and deleted. |
| RTE-7 | If BRouter is unreachable, the user gets a clear error and the route data is not lost. |

### 4.5 Caches along route (CAR)
| ID | Requirement |
|---|---|
| CAR-1 | Given a route and a corridor width (default 500 m), list all caches within that distance of the route geometry, respecting the active filters. |
| CAR-2 | Results are ordered by position along the route (distance from start), with the off-route distance shown. |
| CAR-3 | The user can select caches from the corridor and include them in the route export. Phase 1 does not reroute through them automatically. |

### 4.6 Export (EXP)
| ID | Requirement |
|---|---|
| EXP-1 | Export a filtered set of caches as GPX with Groundspeak extensions, readable by Garmin devices (geocache mode) and BaseCamp. |
| EXP-2 | The export uses corrected coordinates when set. The user note is added to the description or log section. |
| EXP-3 | Optionally include additional waypoints as separate `<wpt>` entries. |
| EXP-4 | Export a route as GPX 1.1 with a `<trk>` (full geometry with elevation) and, optionally, the selected corridor caches as waypoints. |

### 4.7 Phase 2 (planned, not MVP)
| ID | Requirement |
|---|---|
| AUTO-1 | Given a start point, an end point, and a max extra distance, automatically select caches and order them (TSP heuristic), then route through them. |
| API-1 | A `CacheSource` implementation for the Geocaching.com API. **Blocked:** requires partner access. |

## 5. Non-functional requirements
| ID | Requirement |
|---|---|
| NFR-1 | Handles at least 50,000 caches. A map bbox query returns in under 300 ms. Importing a 1,000-cache PQ takes under 10 s. |
| NFR-2 | Works fully offline except for map tiles. Routing is local. |
| NFR-3 | One-command start: `mise run dev` brings up compose services, backend, and frontend. |
| NFR-4 | All configuration is via environment variables (pydantic-settings) with a documented `.env.example`. There are no secrets in the repo. |
| NFR-5 | API errors use RFC 9457 `application/problem+json`. Logging is structured (JSON in production, readable in development). |
| NFR-6 | Cache description HTML is sanitized before rendering (XSS). |
| NFR-7 | The backend binds to `127.0.0.1` by default. |
| NFR-8 | Code quality gates (section 9) pass in CI before any merge to `main`. |

## 6. Architecture

```
┌──────────────── Browser ────────────────┐
│ React + TS + Vite + React Router          │
│ MapLibre GL · TanStack Query · Recharts  │
└──────────────┬──────────────────────────┘
               │ JSON / OpenAPI (generated TS client)
┌──────────────▼──────────────────────────┐
│ FastAPI backend (Python 3.14)            │
│  api/        routers, schemas (pydantic) │
│  services/   use cases                   │
│  domain/     entities, pure logic        │
│  adapters/   db (SQLAlchemy+GeoAlchemy2),│
│              gpx (CacheSource),          │
│              brouter (RoutingProvider)   │
└───────┬─────────────────────┬───────────┘
        │                     │ HTTP
┌───────▼────────┐   ┌────────▼─────────┐
│ PostgreSQL 17  │   │ BRouter (Docker) │
│ + PostGIS      │   │ + .rd5 segments  │
└────────────────┘   └──────────────────┘
```

**Layering rules**
- `domain/` has no imports from FastAPI, SQLAlchemy, or HTTP libraries.
- `services/` depends on `domain/` and on **protocols** (`CacheRepository`, `CacheSource`, `RoutingProvider`). It does not depend on concrete adapters.
- `api/` only translates HTTP to service calls. There is no business logic in routers.
- Dependency injection uses FastAPI `Depends`. Tests swap in fakes.

### 6.1 Repository layout
```
/
├── AGENTS.md  README.md  mise.toml  compose.yaml  .env.example  .pre-commit-config.yaml
├── backend/
│   ├── pyproject.toml  uv.lock  alembic.ini
│   ├── src/geocaching_planner/{api,services,domain,adapters,config.py,main.py}
│   ├── migrations/
│   └── tests/{unit,integration,contract,shared,fixtures}
├── frontend/
│   ├── package.json  vite.config.ts  biome.json  tsconfig.json  playwright.config.ts
│   ├── src/{api,components,features,lib}
│   └── e2e/
├── infra/brouter/{segments/,profiles/}
└── docs/{specification.md,adr/,features/,drafts/}
```

## 7. Domain model (initial)

| Entity | Key fields |
|---|---|
| `Cache` | `gc_code` (PK, unique), `name`, `type`, `source_type`, `container`, `source_container`, `difficulty`, `terrain`, `owner`, `placed_at`, `location` (geography Point 4326), `country`, `state`, `short_description`, `long_description`, `description_is_html`, `hint`, `attributes` (jsonb), `is_available`, `is_archived`, `found_by_me`, `found_at`, `source`, `source_updated_at`, `source_hash`, `created_at`, `updated_at`; aggregate root containing logs and optional waypoint input (`None` means waypoint data absent; empty means clear) |
| `CacheWaypoint` | `id`, `cache_gc_code` (FK), `prefix`/`code`, `name`, `type`, raw `source_type`, `location` (nullable), `description` |
| `CacheLog` | `id` (source log id), `cache_gc_code` (FK), `type`, raw `source_type`, `finder`, `logged_at`, `text` |
| `UserCacheData` | `cache_gc_code` (PK/FK), `note`, `corrected_location`. Kept separate so an import never touches it. |
| `ImportRun` | `id`, `started_at`, `finished_at`, `source`, `filenames`, `created`, `updated`, `unchanged`, `waypoints`, `errors` (jsonb entries with severity and parse context) |
| `Route` | `id`, `name`, `profile`, `geometry` (LineStringZ 4326, nullable until computed), `distance_m`, `ascent_m`, `descent_m`, `computed_at`, `created_at`, `updated_at` |
| `RouteWaypoint` | `id`, `route_id`, `position`, `location`, `label`, `cache_gc_code` (nullable) |
| `Settings` | singleton: `home_location`, `avg_speed_kmh`, `corridor_m_default`, `tile_url` override |

`source_hash` is a deterministic domain hash over canonical source fields, waypoints, and logs; it excludes user data and persistence timestamps.
`ImportRun.errors` contains records with `severity`, `file`, optional `gc_code` and `line`, `code`, and human-readable `message`. Warnings use `severity: "warning"` and are presented separately from errors.

The **effective location** of a cache is `coalesce(user.corrected_location, cache.location)`. It may be projected or ordered by as a SQL expression; spatial predicates use separate corrected-location and original-location branches so both GiST indexes remain usable (ADR-0006).

## 8. API outline (`/api/v1`)
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness, plus DB and BRouter status |
| POST | `/imports` | multipart upload → `ImportRun` summary |
| GET | `/imports` | import history |
| GET | `/caches` | list with filters, `bbox`, paging, sort |
| GET | `/caches/markers` | viewport marker tuples with required bbox, filters, truncation flag, and total |
| GET | `/caches/{gc}` | details incl. waypoints, logs, user data |
| PUT | `/caches/{gc}/user-data` | note and corrected coordinates |
| GET | `/caches/export.gpx` | export with the same filters as the list |
| GET/PUT | `/settings` | user settings |
| GET/POST | `/routes` | list/create |
| GET/PATCH/DELETE | `/routes/{id}` | read/update (name, profile, waypoints)/delete |
| POST | `/routes/{id}/compute` | (re)compute via BRouter |
| GET | `/routes/{id}/caches` | corridor search (`width_m`, plus cache filters) |
| GET | `/routes/{id}/export.gpx` | track plus optional caches (`include=gc1,gc2`) |

The OpenAPI schema is the contract. The frontend client is generated from it (`openapi-typescript` + `openapi-fetch`).

## 9. Engineering standards

### 9.1 Tooling
| Concern | Tool |
|---|---|
| Tool versions and task runner | **mise** (`mise.toml` pins exact versions per ADR-0007: Python 3.14.9, Node 24.22.1 (Active LTS), uv 0.13.5, pnpm 12.15.0, gitleaks 8.30.1; all commands are `mise run <task>`) |
| Python deps | **uv** (`uv sync`, `uv.lock` committed) |
| Node deps | **pnpm** (lockfile committed) |
| Python lint + format | **ruff** (`ruff check`, `ruff format`). Rule sets: `E,F,W,I,N,UP,B,A,C4,SIM,RUF,S,PT,ASYNC,TID` |
| Python types | **mypy --strict** (with the pydantic plugin; do not enable the deprecated SQLAlchemy plugin, use local GeoAlchemy2 stubs if needed) |
| TS lint + format | **Biome** |
| TS types | `tsc --noEmit` with `strict: true` and `noUncheckedIndexedAccess` |
| Git hooks | **pre-commit** (ruff, ruff-format, mypy on changed files, biome, end-of-file, trailing whitespace, a large-file check, gitleaks) |
| CI | **GitHub Actions**: backend, frontend, e2e, and required pre-commit jobs on PRs, `main`, and manual dispatch |
| XML parsing | T-007 must use a dependency selected by an accepted ADR; parsing must disable entity/network access and bound ZIP expansion |

### 9.2 Testing strategy
| Level | Location | Tooling | What |
|---|---|---|---|
| Unit | `backend/tests/unit` | pytest | Domain logic and services with in-memory fakes. No I/O. Fast. |
| Integration | `backend/tests/integration` | pytest + **testcontainers** (`postgis/postgis`) + httpx `AsyncClient` | Repositories, migrations, API endpoints against a real PostGIS. |
| Contract | `backend/tests/contract` | pytest + **respx** with recorded BRouter responses | BRouter adapter request/response mapping. An optional `@pytest.mark.brouter` live test runs against the compose BRouter. |
| Frontend unit/component | `frontend/src/**/*.test.tsx` | **Vitest** + Testing Library + **MSW** | Components, hooks, and state. The map is mocked. |
| E2E smoke | `frontend/e2e` | **Playwright** (Chromium) | Happy path: import fixture → see markers → create route → export. Runs against the compose stack. |

Rules:
- **Coverage gate:** backend ≥ 85% line+branch (`pytest --cov --cov-fail-under=85`). Frontend ≥ 80% lines on `src/` excluding generated client (Vitest v8 coverage).
- Registered `slow` performance tests run in `mise run check:backend` and the CI backend job.
- Every ticket's acceptance criteria map to at least one automated test.
- Bug fixes start with a failing test.
- Fixtures are **synthetic** PQ GPX/ZIP files in `backend/tests/fixtures/` (including edge cases: GPX 1.0 vs 1.1, missing fields, unicode, HTML descriptions, waypoint files, a corrupt entry).
- Test names describe behavior: `test_reimport_preserves_user_note`.
- No network in unit tests (`pytest-socket` blocks it, except for integration and contract markers).

### 9.3 Conventions
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`), referencing the ticket ID, e.g. `feat(import): parse PQ zip [T-007]`.
- **Branches:** `t-<id>-<slug>`. One ticket per branch/PR.
- **Python:** fully typed. Pydantic v2 models for API schemas. SQLAlchemy 2.0 typed ORM (`Mapped[]`). Async DB access (`asyncpg`).
- **Frontend:** feature folders (`src/features/<feature>`). Server state only via TanStack Query. No ad-hoc `fetch`. All API types come from the generated client.
- **Migrations:** every schema change ships an Alembic revision, and `alembic upgrade head` plus `downgrade -1` must work in the integration tests.

### 9.4 Definition of Done (for every ticket)
1. All acceptance criteria are met and covered by automated tests.
2. `mise run check` passes locally: lint, format check, type check, tests, and coverage gates for backend and frontend.
3. Docs are updated (README/spec/AGENTS if behavior or commands changed). A new ADR exists if an architectural decision was made.
4. There are no TODOs without a linked backlog ticket.
5. The ticket file is moved to `docs/features/complete/`, with the completion notes section filled in.

## 10. Roadmap
| Milestone | Tickets | Outcome |
|---|---|---|
| **M0 Foundation** | T-001 – T-005, T-023 | Repo, tooling, skeletons, database, BRouter service, CI all green |
| **M1 Cache management** | T-006 – T-014, T-024 | Import PQs, browse/filter on the map and list, notes and corrected coordinates, GPX export |
| **M2 Bike planning** | T-015 – T-020 | Plan routes with BRouter, elevation, caches along route, route export |
| **Phase 2** | T-021 – T-022 | Auto cache selection; Geocaching.com API (blocked) |

## 11. Open risks
| Risk | Mitigation |
|---|---|
| No Geocaching.com API access | GPX-first design with `CacheSource` abstraction (ADR-0003) |
| BRouter segment files are large (~100–500 MB per 5°×5° tile) | Download only the needed tiles via `mise run brouter:segments`. They are git-ignored. |
| Tile provider usage policy | Configurable tile URL and attribution, no prefetching. Document how to self-host tiles if needed. |
| Variations in the PQ GPX format | Tolerant parser, wide fixture set, error reporting per entry |
| Python 3.14 is new | All dependencies are verified in T-002. The fallback to 3.13 is a one-line change in `mise.toml`/`backend/pyproject.toml`. |

## 12. Glossary
- **PQ (Pocket Query):** a saved geocaching.com search that is delivered as a GPX/ZIP to Premium members.
- **GC code:** the unique cache identifier (`GC1234X`).
- **D/T:** difficulty/terrain rating, from 1 to 5 in 0.5 steps.
- **Corrected coordinates:** user-supplied final coordinates (e.g. a solved mystery cache).
- **Corridor:** the area within X m of a route line.
- **BRouter profile:** a routing cost model (e.g. `trekking`, `fastbike`).
