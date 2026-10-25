# ADR-0006: PostgreSQL with PostGIS

- **Status:** Accepted
- **Date:** 2026-10-25
- **Reviews:** [Council review 1](../reviews/adr/0006-postgis-review-1.md)

## Context
Core queries are spatial: viewport bbox, distance from home, and caches within X m of a route line.

## Decision
We will use **PostgreSQL 17 + PostGIS** (`postgis/postgis` image), **SQLAlchemy 2.0 (async, asyncpg)**, **GeoAlchemy2**, and **Alembic**. Locations are stored as `geography(Point, 4326)`. Route geometry is stored as `geography(LineStringZ, 4326)`. Cache spatial queries use the effective location (`COALESCE(user.corrected_location, cache.location)`). GiST indexes cover `route.geometry`, `cache.location`, and `user.corrected_location`; spatial predicates use separate indexed branches for corrected locations and for original locations when no correction exists. Corridor search filters with `ST_DWithin` on geography and orders by route fraction using `ST_LineLocatePoint(route.geometry::geometry, effective_location::geometry)`.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Plain Postgres + Python math | Fewer extensions | Slow at 50k caches, reinvents GIS |
| SQLite + SpatiaLite | No Docker | Async/geo tooling weaker; diverges from the sketch |

## Consequences
- Integration tests need a PostGIS container (testcontainers), set up in T-003.
- Requires GeoAlchemy2 typing workarounds under mypy strict (local stubs allowed).
