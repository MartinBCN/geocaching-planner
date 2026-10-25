# T-010: Cache query API (filters, bbox, paging)

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-009
- **Requirements:** CAC-1, CAC-2, MAP-2 (data side), NFR-1
- **Related ADRs:** ADR-0006

## Goal
One filter model that drives the list, the map, the export, and (later) the corridor search, backed by efficient PostGIS queries.

## Scope
### In
- `domain/cache_filter.py`: `CacheFilter` with `types[]`, `sizes[]`, `difficulty_min/max`, `terrain_min/max`, `found: bool|None`, `include_archived` (default false), `include_disabled` (default true), `max_distance_km` (needs a home location; return 422 if it is not set), `bbox (minLon,minLat,maxLon,maxLat)`, and `text` (GC code or name, ILIKE).
- One reusable query builder `apply_cache_filter(stmt, f)` that uses the **effective location**. Later tickets (T-014, T-019) **must** reuse it.
- `GET /api/v1/caches`: query params map to `CacheFilter`, plus `sort` (`name|gc_code|difficulty|terrain|distance|placed_at`, with `-` prefix for descending), `page`, and `page_size` (max 500). The response includes `items` (summary: gc_code, name, type, size, D, T, found, available, archived, effective lat/lon, has_corrected, distance_km|null) and `total`.
- `GET /api/v1/caches/markers?bbox=…&<filters>`: a lightweight array `[gc, lat, lon, type, found, available]`, capped at 20,000 with a `truncated` flag.
- A performance test seeds 50,000 synthetic caches and asserts that a bbox and filter query takes under 300 ms (marked `slow`).

### Out
- UI (T-011, T-012). The detail endpoint (T-013).

## Acceptance criteria
- [ ] AC1: Each filter field narrows the results correctly. Combined filters are ANDed.
- [ ] AC2: The distance filter and sort use the home location and the effective location.
- [ ] AC3: The bbox filter uses the effective location. A cache whose corrected coordinates move it outside the bbox is excluded.
- [ ] AC4: Paging and `total` are correct. `page_size` above 500 returns 422.
- [ ] AC5: `max_distance_km` without a home location returns 422 problem+json.
- [ ] AC6: The markers endpoint respects the filters and the 20k cap.
- [ ] AC7: The 50k-cache bbox query takes under 300 ms on CI hardware (slow marker). `EXPLAIN` shows GiST index use.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC6 | integration | `tests/integration/api/test_caches_query.py` (parametrized filter cases) |
| filter parsing | unit | `tests/unit/domain/test_cache_filter.py` |
| AC7 | integration (slow) | `tests/integration/perf/test_cache_query_perf.py` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] `api:gen` is run
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
