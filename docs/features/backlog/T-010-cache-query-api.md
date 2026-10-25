# T-010: Cache query API (filters, bbox, paging)

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-009, T-024
- **Requirements:** CAC-1, CAC-2, MAP-2 (data side), NFR-1
- **Related ADRs:** ADR-0005, ADR-0006
- **Reviews:** [Council review 1](../../reviews/features/T-010-cache-query-api-review-1.md)

## Goal
One filter model that drives the list, map, export, and (later) corridor search, backed by efficient PostGIS queries.

## Context
Spatial predicates must use separate GiST-indexable branches for original and corrected locations (ADR-0006). API query validation uses T-002's RFC 9457 Problem contract. Static `/caches/*` paths, including `/caches/markers`, must be registered before `/caches/{gc}`.

## Scope
### In
- `domain/cache_filter.py`: pure `CacheFilter` value object validates query ranges and bbox. Include repeated `types`/`containers`, inclusive D/T bounds, `found: bool | None`, `include_archived=false`, `include_disabled=true`, `max_distance_km >= 0`, required marker bbox, and `text`.
- `adapters/db/cache_query.py::apply_cache_filter(stmt, filter)` implements database predicates and is called only by `CacheRepository.query(filter, sort, page)` and `CacheRepository.markers(filter, cap)`. `CacheQueryService` obtains home through the settings protocol. A shared `Depends` maps validated query parameters to `CacheFilter` and is reused by export and corridor search.
- Spatial queries use two separate predicate branches: corrected locations and original locations, each usable with its GiST index. Bounding boxes use `&&`/`ST_Intersects` on `::geometry` against `ST_MakeEnvelope(minLon,minLat,maxLon,maxLat,4326)` with expression indexes and downgrade migration if required. Distance uses `ST_DWithin`/`ST_Distance` on geography. Never put `COALESCE` in the spatial predicate.
- Extend `CacheRepository` with `query(filter, sort, page)` and `markers(filter, cap)`; implement `GET /api/v1/caches` using `sort` (`name|gc_code|difficulty|terrain|distance|placed_at`, optional `-` descending; default `gc_code`), `page` (1-based, default 1), and `page_size` (default 50, range 1–500). Every ordering ends with `gc_code`. Response includes `items` (summary: `gc_code`, `name`, `type`, `container`, `difficulty`, `terrain`, `found_by_me`, `is_available`, `is_archived`, `placed_at`, effective lat/lon, `has_corrected`, `distance_km` in straight-line kilometers or null) and `total`.
- `GET /api/v1/caches/markers?bbox=…&<filters>` returns `{items, truncated, total}`. Each item is a typed fixed tuple `[gc_code, name, lat, lon, type, container, difficulty, terrain, found_by_me, is_available, is_archived, has_corrected]`; coordinates are effective coordinates. `bbox` is required. When truncated, return exactly the injectable `MARKER_CAP` items, ordered by `gc_code`; report the untruncated `total`.
- Performance test seeds 50,000 synthetic caches (10% corrected), runs `ANALYZE`, and tests a 0.5°×0.5° bbox with `types` and `found=false` selecting approximately 2,000 caches. Twenty warm HTTP requests measured by the in-process `AsyncClient` have p95 under 300 ms; `EXPLAIN` shows index or bitmap scans on both corrected and original GiST branches. Register and run the slow test in backend CI.

### Out
- UI (T-011, T-012). The detail endpoint (T-013).

## Acceptance criteria
- [ ] AC1: Given repeated `types` or `containers`, when filtering, then values within each list are ORed and different filter fields are ANDed. D/T bounds are inclusive; `found=None` means no found filter; `include_disabled=false` means `is_available=true`; `available=false` is presented as disabled. `text=abc` matches `gc_code ILIKE 'abc%' OR name ILIKE '%abc%'`.
- [ ] AC2: Given a corrected location 10 km from home and its original location 1 km from home, when `max_distance_km=5` is applied, then the cache is excluded; in a separate unfiltered request its `distance_km` is `10.0 ± 0.01` straight-line kilometers.
- [ ] AC3: Given a cache whose corrected location moves it outside a supplied bbox, when bbox filtering runs, then it is excluded; bbox edges are evaluated in geometry coordinate space.
- [ ] AC4: Given no paging parameters, then page 1 and page size 50 are used. Given page 2 and size 2, results are stable with `gc_code` tie-break; a page past the end is empty with correct total. Page is 1-based/minimum 1 and page size is 1–500.
- [ ] AC5: Given `max_distance_km` or `sort=distance` without a home location, when requested, then return 422 problem+json with stable type URI and actionable detail to set a home location. Given no distance filter/sort and no home location, each item's `distance_km` is null.
- [ ] AC6: Given either caches endpoint is requested without a valid marker bbox where required, with unknown sort, D/T outside 1–5 or not in 0.5 increments, or a minimum greater than its maximum, when requested, then return 422 `application/problem+json`.
- [ ] AC7: Given the markers endpoint with a bbox and filters, when there are fewer than `MARKER_CAP` matches, then all matching items return in the documented tuple shape with `truncated=false` and exact total; when more matches exist, exactly `MARKER_CAP` deterministic GC-code-ordered items return with `truncated=true` and the total before truncation.
- [ ] AC8: Given 50,000 synthetic caches (10% corrected) after `ANALYZE`, when the marker API is requested 20 warm times for a 0.5°×0.5° bbox, `types`, and `found=false`, then p95 is under 300 ms and EXPLAIN uses index or bitmap scans on both GiST branches.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1 | integration | `backend/tests/integration/api/test_caches_query.py::test_each_filter_field_semantics` (parametrized by field) |
| AC2–AC3 | integration | `backend/tests/integration/api/test_caches_query.py::test_distance_uses_effective_location`, `::test_bbox_excludes_cache_moved_out_by_correction` |
| AC4 | integration | `backend/tests/integration/api/test_caches_query.py::test_paging_defaults_tiebreak_and_past_end` |
| AC5 | integration | `backend/tests/integration/api/test_caches_query.py::test_distance_without_home_is_problem` |
| AC6 | integration | `backend/tests/integration/api/test_caches_query.py::test_invalid_sort_ranges_and_bbox_are_problem` |
| AC7 | integration | `backend/tests/integration/api/test_caches_query.py::test_markers_have_stable_cap_and_total` |
| AC1, AC6 | unit | `backend/tests/unit/domain/test_cache_filter.py` |
| AC8 | integration (slow; runs in CI backend job) | `backend/tests/integration/perf/test_cache_query_perf.py` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] `mise run api:gen` is run and the generated client is committed
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Implementation notes
- Add `name`, `container`, `difficulty`, `terrain`, `placed_at`, `is_archived`, and `has_corrected` to marker data so MAP-2 can distinguish found, disabled, archived, and corrected caches and MAP-3 can show key popup information without an additional endpoint.
- Make `MARKER_CAP` injectable and override it to 5 in tests. Seed fixtures through `backend/tests/fixtures/cache_factory.py::make_caches(n, seed)`, including corrected locations.
- Filter semantics: repeated `types` and `containers` values are ORed within their field and ANDed with other fields; D/T bounds are inclusive; absent `found` means no found restriction; `include_archived=false` excludes archived rows; `include_disabled=true` includes unavailable rows and `false` requires `is_available=true`; text uses the GC-code prefix/name substring rule in AC1. Valid types and containers are the complete T-006 enum sets.
- Validate bbox longitude/latitude ranges and ordering (`min < max` on both axes); query-param lists are represented by repeated keys, not comma-separated strings. Past-end pages return an empty item list and the exact total.
- Filter semantics table:

| Query field | Semantics |
|---|---|
| repeated `types` | OR within the complete `CacheType` enum; AND with other fields |
| repeated `containers` | OR within the complete `ContainerSize` enum; AND with other fields |
| `difficulty_min/max`, `terrain_min/max` | Inclusive, values 1–5 in 0.5 increments; each min must not exceed its max |
| `found` | Omitted means no restriction; `true`/`false` match `found_by_me` |
| `include_archived` | Defaults false; false excludes archived caches |
| `include_disabled` | Defaults true; false requires `is_available=true`; unavailable is displayed as disabled |
| `max_distance_km` | Straight-line geodesic distance from configured home to effective location; no home is 422 |
| `bbox` | `minLon,minLat,maxLon,maxLat`, valid geographic ranges with minimum strictly below maximum |
| `text` | Case-insensitive GC-code prefix OR name substring |

- Return all invalid query input through T-002's RFC 9457 Problem handler; FastAPI's default 422 schema is not the contract. Register static cache routes before `/caches/{gc}`.
- `CacheFilter` is domain-pure; SQLAlchemy query composition stays in the DB adapter. T-014 and T-019 must reuse `CacheRepository` query methods and the shared filter dependency.
- Update spec §8 with `GET /caches/markers`. `slow` is registered and included in `mise run check:backend` and the CI backend job.

## Completion notes
_…_
