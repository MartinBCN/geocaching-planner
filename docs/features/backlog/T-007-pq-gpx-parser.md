# T-007: Pocket Query GPX/ZIP parser (`CacheSource`)

- **Status:** Blocked
- **Milestone:** M1
- **Depends on:** T-006
- **Requirements:** IMP-2, IMP-3, IMP-7, IMP-8
- **Related ADRs:** ADR-0003, ADR-0012
- **Reviews:** [Council review 2](../../reviews/features/T-007-pq-gpx-parser-review-2.md)

## Goal
Turn Pocket Query `.gpx` and `.zip` files into domain `Cache` objects (with waypoints and logs) through a `CacheSource` implementation, with errors reported per entry.

## Context
A PQ ZIP usually contains `<pqid>.gpx` (caches) and `<pqid>-wpts.gpx` (additional waypoints). Waypoint `<name>` values look like `PK1234X` (a 2-character prefix plus the GC code without `GC`). Caches use the `groundspeak:cache` extension inside `<wpt>`. Both the GPX 1.0 (`http://www.topografix.com/GPX/1/0`) and GPX 1.1 namespaces exist in the wild, as do Groundspeak schemas 1.0 and 1.0.1. The XML parser dependency is an architectural choice and this ticket remains blocked until ADR-0012 is accepted.

## Scope
### In
- `services/ports.py`: synchronous `CacheSource` with `source_name="pq"` and `iter_caches() -> Iterator[CacheParseResult]`; any async service must consume the parser off the event loop. `CacheParseResult` is `ParsedCache(cache, warnings: tuple[ParseIssue, ...]) | ParseError(issue) | ParseWarning(issue)`. `ParseIssue` has `severity`, `file`, `gc_code | None`, `line | None`, `code`, and actionable `message`.
- `adapters/gpx/pq_source.py`: `PocketQuerySource(files: Sequence[SourceFile])`, where `SourceFile` contains a filename and binary stream. Detect ZIP by magic bytes, not filename alone; accept `.gpx` and `.zip`.
- XML parsing uses the implementation selected by ADR-0012. It must stream GPX entries with entity resolution disabled, `no_network`, DTD loading disabled, and `huge_tree` disabled; reject entity declarations; and keep HTML descriptions raw for sanitization at render time.
- Map `found_by_me` only from `<sym>Geocache Found</sym>`; `found_at` is `None` because the parser has no configured username. Map availability, archived state, attributes, hints, descriptions (including `description_is_html`), source `"pq"`, source update time, and logs deterministically.
- First index waypoint files from all inputs into `dict[gc_code, list[CacheWaypoint]]`, then stream cache files and attach waypoints. Orphans are not emitted and produce a `ParseWarning` with the waypoint code, filename, and missing parent GC code. A waypoint-only import cannot attach to already-persisted caches; it reports those waypoints as orphans.
- Read only `.gpx` ZIP members; reject nested archives and members larger than 100 MB or a ZIP with total uncompressed GPX size over 500 MB. Corrupt/unsupported input yields one file-level result, not an uncaught exception.
- Synthetic fixtures in `backend/tests/fixtures/pq/`: GPX 1.0/1.1 equivalents, Groundspeak 1.0/1.0.1 equivalents, separate cache and waypoint GPX files, Unicode HTML plus `unicode_html.expected.txt`, missing optional fields, corrupt entry, non-GPX input, XXE/billion-laughs payloads, and unknown enum values. Generate ZIP fixtures in tests from source GPX files. **Fixtures must be synthetic**.

### Out
- Persisting data (T-008).

## Acceptance criteria
- [ ] AC1: Given equivalent GPX 1.0/1.1 and Groundspeak 1.0/1.0.1 fixtures, when parsed, then each pair produces equal domain objects.
- [ ] AC2: Given cache GPX and `-wpts.gpx` supplied as separate named files or inside a ZIP, when parsed together, then each cache includes its matching additional waypoints; an unmatched waypoint produces one warning and is not emitted.
- [ ] AC3: Given a three-cache fixture whose middle entry has non-numeric difficulty, when parsed, then results are `ParsedCache(GC0001A)`, `ParseError(gc_code=GC0002B, line=<n>)`, and `ParsedCache(GC0003C)` in source order.
- [ ] AC4: Given a non-GPX file or ZIP without `.gpx` members, when parsed, then exactly one file-level `ParseError(gc_code=None, file=...)` is returned and nothing is raised.
- [ ] AC5: Given XXE and billion-laughs fixtures targeting a temporary secret file, when parsed, then no field contains the secret, no external entity/network access occurs, and the parser returns a safe result or `ParseError`.
- [ ] AC6: Given the Unicode/HTML fixture, when parsed, then `long_description` equals the decoded expected string (including tags and Unicode) and `description_is_html` is true; sanitization is not performed by the parser.
- [ ] AC7: Given found, not-found, disabled (`available="False"`), and archived fixtures, when parsed, then `found_by_me` is derived only from `<sym>Geocache Found</sym>`, `found_at` is `None`, and availability/archive fields match the GPX source.
- [ ] AC8: Given a fixture with all optional fields, when parsed, then cache type/size, D/T, attributes, hints, logs, description flags, source, and source-updated time match expected values; missing optional fields map to `None` or empty collections as specified.
- [ ] AC9: Given an unrecognized type/container string, when parsed, then the enum is `Other` and exactly one `unknown_type`/`unknown_container` warning names the file and GC code.
- [ ] AC10: Given a waypoint without usable coordinates, when parsed, then it is linked with `location=None`.
- [ ] AC11: Given a 5,000-cache GPX 1.0 file with about four logs per cache generated by `backend/tests/fixtures/pq/generate.py::make_pq(5000)`, when the complete iterator is consumed, then elapsed time is under five seconds and `tracemalloc` peak is under 200 MB. The registered `slow` test runs in the backend CI job.
- [ ] AC12: Given a ZIP containing a nested archive or over-limit GPX members, when parsed, then it is rejected with one file-level error and does not extract content to disk.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_namespace_and_schema_versions_are_equivalent` |
| AC2, AC10 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_links_separate_waypoint_files_and_reports_orphans` |
| AC3 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_recovers_after_corrupt_cache_entry` |
| AC4 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_non_gpx_and_zip_without_gpx_return_file_error` |
| AC5 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_xxe_content_is_never_resolved` |
| AC6 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_unicode_html_description_is_decoded_and_flagged` |
| AC7 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_cache_status_mapping` |
| AC8 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_all_fields_and_optional_defaults` |
| AC9 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_unknown_values_report_warnings` |
| AC10 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_waypoint_without_coordinates_is_linked` |
| AC11 | slow unit | `backend/tests/unit/adapters/test_pq_source_perf.py::test_large_pq_time_and_memory`; run in `mise run check:backend` and CI |
| AC12 | unit | `backend/tests/unit/adapters/test_pq_source.py::test_zip_limits_and_nested_archives_are_rejected` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Implementation notes
- `ParseIssue` is shared through `services/ports.py`; warnings are persisted by T-008 in the import run `errors` JSON with `severity:"warning"` and shown separately from errors in the UI.
- Map Groundspeak strings to domain types using this table; unlisted values map to `Other` with a warning. Keep attributes and logs in deterministic order for `source_hash`.

| Groundspeak value | Domain value |
|---|---|
| `Traditional Cache` | `Traditional` |
| `Multi-cache` | `Multi` |
| `Unknown Cache` | `Mystery` |
| `Letterbox Hybrid` | `Letterbox` |
| `Earthcache` | `EarthCache` |
| `Wherigo Cache` | `Wherigo` |
| `Virtual Cache` | `Virtual` |
| `Event Cache` | `Event` |
| `Cache In Trash Out Event` | `CITO` |
| `Mega-Event Cache` | `Mega` |
| `Giga-Event Cache` | `Giga` |
| `Webcam Cache` | `Webcam` |
| `Lab Cache` | `Lab` |
| Groundspeak container text | case-insensitive mapping to matching `ContainerSize`; `Not chosen` stays `Not chosen` |
| Waypoint/log types | map known Groundspeak GPX schema values to `WaypointType`/`LogType`; unknown values map to `Other`, with the original source string preserved |

- The parser iterator is synchronous. Callers in async services must offload complete parsing to a worker thread rather than block the event loop.
- ADR-0012 must be accepted before implementation. If accepted as proposed, add `lxml` to `backend/pyproject.toml` runtime dependencies and verify installation under the pinned Python 3.14.x toolchain. If Ruff `S` flags parser calls, use only a per-line suppression naming the exact rule and reason; do not weaken rules globally.

## Completion notes
_…_
