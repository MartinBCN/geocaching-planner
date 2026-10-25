# ADR-0006: PostgreSQL with PostGIS

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
Core queries are spatial: viewport bbox, distance from home, and caches within X m of a route line.

## Decision
We will use **PostgreSQL 17 + PostGIS** (`postgis/postgis` image), **SQLAlchemy 2.0 (async, asyncpg)**, **GeoAlchemy2**, and **Alembic**. Locations are stored as `geography(Point, 4326)`. Route geometry is stored as `geography(LineStringZ, 4326)`. Both have GiST indexes. Corridor search uses `ST_DWithin` and orders by `ST_LineLocatePoint`.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Plain Postgres + Python math | Fewer extensions | Slow at 50k caches, reinvents GIS |
| SQLite + SpatiaLite | No Docker | Async/geo tooling weaker; diverges from the sketch |

## Consequences
- Integration tests need a PostGIS container (testcontainers).
- Requires GeoAlchemy2 typing workarounds under mypy strict (local stubs allowed).
