# ADR-0003: Pocket Query GPX import first, pluggable cache sources

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
The Geocaching.com API is only available to approved partners, and we do not have access. Scraping violates the ToS. Premium members can download Pocket Queries (GPX/ZIP with Groundspeak extensions). This is also how GSAK has mainly been used.

## Decision
We will import caches from **Pocket Query GPX/ZIP files**. Import is implemented behind a `CacheSource` protocol that yields domain `Cache` objects (with waypoints and logs). The import service only talks to `CacheSource`, so a future Geocaching.com API source (T-022, blocked) can plug in without changing the domain.

The data flow is **one-way** (read-only from geocaching.com). User data (notes, corrected coordinates) is stored separately and is never overwritten by an import.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Geocaching.com API now | Live data | No access; blocked |
| Scraping | No access needed | ToS violation, fragile |

## Consequences
- Data is only as fresh as the user's last PQ download.
- The parser must tolerate GPX 1.0/1.1 and variations in the Groundspeak schema.
