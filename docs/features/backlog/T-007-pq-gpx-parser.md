# T-007: Pocket Query GPX/ZIP parser (`CacheSource`)

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-006
- **Requirements:** IMP-2, IMP-3, IMP-7, IMP-8
- **Related ADRs:** ADR-0003

## Goal
Turn Pocket Query `.gpx` and `.zip` files into domain `Cache` objects (with waypoints and logs) through a `CacheSource` implementation, with errors reported per entry.

## Context
A PQ ZIP usually contains `<pqid>.gpx` (caches) and `<pqid>-wpts.gpx` (additional waypoints). Waypoint `<name>` values look like `PK1234X` (a 2-character prefix plus the GC code without `GC`). Caches use the `groundspeak:cache` extension inside `<wpt>`. Both the GPX 1.0 (`http://www.topografix.com/GPX/1/0`) and the GPX 1.1 namespaces exist in the wild, and so do Groundspeak schema 1.0 and 1.0.1.

## Scope
### In
- `services/ports.py`: `CacheSource` protocol, `iter_caches() -> Iterator[CacheParseResult]` (success or error with context).
- `adapters/gpx/pq_source.py`: `PocketQuerySource(files: Sequence[Path | BinaryIO])`. It handles `.gpx` and `.zip`, detects namespaces, and maps types and sizes to domain enums (unknown values go to `Other`, with a warning).
- Parse with **`lxml`** using `iterparse` (memory-safe for large files). Disable entity resolution and network access, so XXE is not possible.
- Maps found status (`<sym>Geocache Found</sym>` / `groundspeak` found logs by the PQ owner), availability, archived state, attributes, hints, descriptions (keep HTML raw; sanitizing happens at render time), and logs.
- Links waypoints to their parent cache by prefix and code. Orphan waypoints are reported as warnings.
- Synthetic fixtures in `backend/tests/fixtures/pq/`: `gpx10_basic.gpx`, `gpx11_basic.gpx`, `with_waypoints.zip`, `unicode_html.gpx`, `missing_optional_fields.gpx`, `one_corrupt_entry.gpx`, `not_a_gpx.txt`, and `xxe_attempt.gpx`. **Fixtures must be synthetic** (invented caches and coordinates).

### Out
- Persisting data (T-008).

## Acceptance criteria
- [ ] AC1: GPX 1.0 and 1.1 fixtures parse into identical domain objects for the same content.
- [ ] AC2: A ZIP with caches and waypoints yields caches with linked waypoints.
- [ ] AC3: A corrupt entry yields an error result with GC code or line info, and parsing continues.
- [ ] AC4: A non-GPX file yields one file-level error and no crash.
- [ ] AC5: An XXE payload is not resolved.
- [ ] AC6: Unicode and HTML descriptions are preserved byte-exact.
- [ ] AC7: A 5,000-cache generated file parses in under 5 s, and peak memory stays under 200 MB (perf test, marked `slow`).

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC6 | unit | `tests/unit/adapters/test_pq_source.py` |
| AC7 | unit (slow marker; runs in CI) | `tests/unit/adapters/test_pq_source_perf.py` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
