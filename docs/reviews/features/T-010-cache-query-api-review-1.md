# Council review: T-010-cache-query-api (review 1)

- **Target:** `docs/features/backlog/T-010-cache-query-api.md` (Ticket, status at review time: Ready)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 9 Major · 5 Minor · 1 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve with changes · Quality & Delivery: Approve with changes

## Context provided
- README.md
- AGENTS.md
- docs/specification.md
- docs/adr/0001-record-architecture-decisions.md
- docs/adr/0002-local-single-user-deployment.md
- docs/adr/0003-gpx-first-pluggable-cache-source.md
- docs/adr/0004-brouter-routing.md
- docs/adr/0005-frontend-react-maplibre.md
- docs/adr/0006-postgis.md
- docs/adr/0007-tooling-uv-mise-monorepo.md
- docs/adr/0008-quality-gates.md
- docs/adr/0009-ticket-workflow.md
- docs/adr/0010-council-review.md
- docs/features/backlog/T-009-settings.md
- docs/features/TEMPLATE.md
- docs/features/README.md

**Anomalies:** none

## Top actions
1. Pin down the effective-location spatial predicate (ADR-0006 indexed branches, bbox on `::geometry`, distance on geography), and rewrite AC7 as a measurable p95 test on a defined dataset and bbox that CI actually runs (#3, #4; ARC-2, QDE-3).
2. Define the `/caches/markers` contract: an object `{items, truncated, total}`, `bbox` required, a deterministic order under an injectable cap, and enough fields for MAP-2/MAP-3 (archived, has_corrected, popup info) or a named popup source (#1, #8; QDE-2, PRD-2, ARC-4, PRD-1).
3. Name the layering: `CacheFilter` in `domain/`, `apply_cache_filter` in `adapters/db/` behind `CacheRepository` methods, a service that reads home through a settings protocol, and a shared `Depends` for query params (#2; ARC-1, QDE-7).
4. Add a filter-semantics table and split AC1 per field. Specify paging defaults, validation rules returning 422 problem+json, a `gc_code` tie-breaker, and `sort=distance` without home → 422 with an actionable `detail` (#5, #6, #7; QDE-1, QDE-4, QDE-5, PRD-3, PRD-5, ARC-5, ARC-6).
5. Give the test plan a synthetic data factory (including corrected coordinates) and name a test per AC. Align the ticket with TEMPLATE.md (Reviews line, Context, Implementation notes, full DoD, spec §8 update for `/caches/markers`) (#9, #10, #11; QDE-6, QDE-8, QDE-9, ARC-3, ARC-7).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | QDE-2, PRD-2, ARC-4 | Scope/In: "a lightweight array `[gc, lat, lon, type, found, available]`, capped at 20,000 with a `truncated` flag" | A bare array can't carry `truncated`, so the shape contradicts itself and the generated OpenAPI is ambiguous. The ticket doesn't say whether `bbox` is required or which 20k rows are kept, so results are nondeterministic and tests could be flaky. Without `total`, the UI can't tell the user that caches are missing, and silent gaps look like "no caches here". | Specify `{"items": [[gc, lat, lon, type, found, available], …], "truncated": bool, "total": int}` with a typed tuple schema. lat/lon are the effective location. `bbox` is required (missing or malformed → 422 problem+json). When truncated, return exactly `MARKER_CAP` items in a deterministic order (e.g. `gc_code`). Add this to AC6. |
| 2 | Major | ARC-1, QDE-7 | Scope/In: "One reusable query builder `apply_cache_filter(stmt, f)`… Later tickets (T-014, T-019) **must** reuse it." | No layer or file is named. The builder takes a SQLAlchemy statement, so it can't go in pure `domain/`. As written, the router could run the query directly, or later tickets could import an adapter helper, which would break the spec §6 dependency rule. The ticket also doesn't say how home location is obtained from T-009. | `CacheFilter` (pure, `domain/`) validates ranges and bbox. `adapters/db/cache_query.py::apply_cache_filter` is used only by `CacheRepository.query(filter, sort, page)` and `CacheRepository.markers(filter, cap)`. A `CacheQueryService` reads home through a settings protocol. Query params → `CacheFilter` is one shared `Depends` in `api/`, reused by export and the corridor search. |
| 3 | Major | ARC-2 (QDE-3 partial) | Scope/In: "uses the **effective location**"; ADR-0006: "spatial predicates use separate indexed branches for corrected locations and for original locations…" | The ticket doesn't pass on the ADR-0006 rule. A plain `COALESCE` predicate can't use GiST, so AC7 would fail. The bbox predicate type is unspecified: on geography, edges follow great circles, which can wrongly include or exclude caches near the top or bottom of a wide viewport (AC3). | Add a **must** note: two predicate branches, one for corrected and one for original locations, each able to use its GiST index. The bbox uses `&&`/`ST_Intersects` on `::geometry` against `ST_MakeEnvelope(…, 4326)`, with expression indexes plus a downgrade migration if needed. Distance uses `ST_DWithin`/`ST_Distance` on geography. Confirm T-006 indexes `corrected_location`, or add the index to this ticket's scope. |
| 4 | Major | QDE-3 | AC7: "takes under 300 ms on CI hardware (slow marker). `EXPLAIN` shows GiST index use." | The threshold can't be measured objectively. The ticket doesn't define single run vs p95, warm vs cold cache, DB time vs HTTP round-trip, which endpoint is measured, the bbox size, or whether `slow` tests run in CI. Either AC7 is never verified, or it becomes a flaky gate. | Rewrite: "Given 50,000 synthetic caches (10% corrected) after `ANALYZE`, `GET /api/v1/caches/markers` with a ~0.5°×0.5° bbox (~2,000 caches) plus `types` and `found=false` has p95 of 20 warm runs < 300 ms. `EXPLAIN` shows index or bitmap scans on both GiST indexes." State that the `slow` marker is registered and the CI `backend` job runs it. |
| 5 | Major | PRD-3, QDE-4, ARC-5 | AC5: "`max_distance_km` without a home location returns 422 problem+json."; Scope: "`sort` (…`distance`…)", "`distance_km\|null`" | `sort=distance` without a home location is undefined. `distance_km` has no unit or tolerance, so a test assertion has no reference value. A bare 422 gives the user no next step. | Extend AC5: "`max_distance_km` **or** `sort=distance` without home → 422 problem+json with a stable `type` URI and a `detail` such as 'Set a home location in Settings…'. `distance_km` is `null` in all items." Rewrite AC2 with a concrete case: corrected location 10 km away, original location 1 km away, `max_distance_km=5` → excluded, and `distance_km` is 10.0 ± 0.01 (geodesic). |
| 6 | Major | QDE-5, PRD-5, ARC-5, ARC-6 | AC4: "Paging and `total` are correct. `page_size` above 500 returns 422." | The ticket doesn't define page base, defaults, minimums, behavior past the last page, or validation of `sort`, D/T ranges, and bbox. It gives no tie-breaker, so offset paging can repeat or skip caches. AC4 doesn't require problem+json (NFR-5), and FastAPI's default validation response isn't RFC 9457. | Add: "`page` is 1-based (default 1, min 1). `page_size` defaults to 50 (1–500). Past the last page → `items=[]` with a correct `total`. Every sort ends with `gc_code`. Unknown `sort`, D/T outside 1–5 or not in 0.5 steps, min > max, or an invalid bbox → 422 `application/problem+json`." Add one parametrized test per case. |
| 7 | Major | QDE-1 | AC1: "Each filter field narrows the results correctly. Combined filters are ANDed." | "Correctly" is subjective. Undefined: whether bounds are inclusive, what disabled/available and `found: None` mean, how `text` matches, OR within list fields, the param encoding (repeated vs comma-separated), and the allowed `type`/`size` values. T-012 and the generated client depend on all of these. | Add a "Filter semantics" table and split AC1 into one Given/When/Then per field. For example: inclusive D/T bounds. Repeated `types` params are OR'd within the field and ANDed across fields. `text` matches `gc_code ILIKE 'abc%'` OR `name ILIKE '%abc%'`. |
| 8 | Major | PRD-1 | Scope/In: "a lightweight array `[gc, lat, lon, type, found, available]`" | MAP-2 requires a visible found/disabled state, and MAP-3 requires "a popup with key info". With `include_archived`, archived caches can't be told apart from disabled ones, and solved caches (corrected coordinates) can't be marked. The popup has no data source before T-013. | Add `name, D, T, size, archived, has_corrected` to the marker tuple, or name the endpoint that supplies popup info and exists before T-011. |
| 9 | Major | QDE-6 | Test plan: "AC1–AC6 \| integration \| `tests/integration/api/test_caches_query.py`" | AC6 needs more than 20k rows in the normal integration suite. The ticket names no seed factory for the 50k performance data or for corrected coordinates (which have no write API until T-013). | Make the cap injectable (`MARKER_CAP`, overridden to 5 in tests). Add `backend/tests/fixtures/cache_factory.py::make_caches(n, seed)` that writes `Cache` and `UserCacheData` rows directly. Name one test per AC (e.g. `test_bbox_excludes_cache_moved_out_by_correction`). |
| 10 | Minor | ARC-3, QDE-8 | Scope/In: "`GET /api/v1/caches/markers?bbox=…`"; DoD: "All ACs are covered" | The new endpoint isn't in spec §8. Static `/caches/*` paths must be registered before `/caches/{gc}` (T-013). The DoD drops parts of the template DoD (automated tests, docs updated, no orphan TODOs). | Use the template DoD verbatim, plus "`mise run api:gen` run and client committed" and "spec §8 lists `GET /caches/markers`". Note the route-order requirement. |
| 11 | Minor | QDE-9, ARC-7 | Header: "**Related ADRs:** ADR-0006" (no `Reviews:` line); no `## Context` / `## Implementation notes` | The ticket deviates from TEMPLATE.md. ADR-0005 (`api:gen`) is missing from Related ADRs, and there is no place for the gotchas from #2, #3, and #6. | Add `- **Reviews:** –` and ADR-0005. Add `## Context` (spec §7 effective location, ADR-0006 branches, NFR-1) and `## Implementation notes`. |
| 12 | Minor | PRD-4 | Scope/In: "`sort` (… `placed_at` …)" vs summary "(gc_code, name, type, size, D, T, found, available, archived, …)" | The list can sort by placed date, but the summary items don't include it, so T-012 can't show the sorted column. | Add `placed_at` to the summary items. |
| 13 | Minor | PRD-6 | Scope/In: "`sizes[]`", "`include_disabled`", "available" vs spec §7 "`container`", "`is_available`" | The same concepts have different names, and the inconsistency will reach the filter labels and the generated TS types. | Choose one term per concept (spec glossary). State that `available=false` is shown as "disabled". |
| 14 | Minor | QDE-10 | Test plan: "filter parsing \| unit \| `tests/unit/domain/test_cache_filter.py`" | This row maps to no AC, and the paths omit the `backend/` prefix (spec §9.2). | Map it to the validation AC from #6 and use `backend/tests/...` paths. |
| 15 | Nit | PRD-7 | Scope/In: "`max_distance_km` (needs a home location …)" | A cyclist could read this as ride distance, not straight-line distance. | Add "(straight-line distance from home, using the effective location)". |

No severities were raised by the Chair.

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Marker response shape and cap (#1) | ARC-4: Minor. It's a contract ambiguity, fixed by an object wrapper. | QDE-2, PRD-2: Major. Nondeterministic truncation and a missing `total` cause flaky tests and a misleading UI. |
| Layering of `apply_cache_filter` (#2) | ARC-1: Major. Spec §6 layering and reuse by T-014/T-019 are at risk. | QDE-7: Minor. It only needs a file path stated. |
| `sort=distance` without home (#5) | ARC-5: Minor. | PRD-3, QDE-4: Major. QDE also asks whether to return 422 or put nulls last. ARC and PRD both recommend 422. |
| Paging, validation, and tie-break (#6) | ARC-5, ARC-6, PRD-5: Minor. | QDE-5: Major. Many undefined parameters would force an agent to guess. |
| Template conformance (#11) | ARC-7: Nit. | QDE-9: Minor. |
| Marker payload richness (#8) | PRD-1: Major. MAP-2/MAP-3 need more fields. | ARC raises only an open question about adding `archived` and `has_corrected`. The ticket calls the payload deliberately "lightweight". |

## Open questions for the author
- Did T-006 create a GiST index on `user_cache_data.corrected_location`, and does it expose the effective location as a single SQL expression or view? If not, which ticket owns that? (ARC)
- Should the marker tuple include `archived` and `has_corrected`, and where does the MAP-3 popup get its data? (ARC, PRD-1)
- Should `sort=distance` without a home location return 422, or degrade to nulls last? (QDE, PRD-3)
- Do `@slow` tests run in `mise run check` and the CI `backend` job? If not, how is NFR-1 verified? (QDE)
- Do the `include_archived`/`include_disabled` defaults apply identically to `/caches/markers`? (QDE)
- Should the summary include a `has_note` flag? Should CAC-2 be updated to list the `text` filter? (PRD)

## Strengths
- A single `CacheFilter`/`apply_cache_filter` that T-014 and T-019 must reuse prevents filter drift across the map, list, export, and corridor search (all three members).
- AC3 tests concretely that corrected coordinates move a cache out of the bbox, which supports CAC-5 and the effective-location rule.
- AC7 makes NFR-1 testable through an `EXPLAIN` GiST check, not only a timing.
- The defaults (`include_archived` false, `include_disabled` true) and text search match how GSAK users work.
- The dependencies are correct and the scope fits one PR.

## Process notes
- All three custom agent types were available, and no fallback was used.
- All member outputs met the contract, so no re-prompts were needed.
- ARC-5 covers two issues and is listed under both #5 and #6. QDE-3 overlaps with ARC-2 on the GiST/`COALESCE` point; it is listed as partial under #3 and kept as its own entry (#4) for measurability.

---

## Appendix A: Software Architect (raw)
