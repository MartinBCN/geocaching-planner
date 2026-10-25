# T-014: Cache GPX export

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-013
- **Requirements:** EXP-1, EXP-2, EXP-3
- **Related ADRs:** –

## Goal
Export the currently filtered caches as a GPX file that Garmin devices (geocache mode) and BaseCamp accept.

## Scope
### In
- `adapters/gpx/writer.py`: write GPX 1.0 with the Groundspeak 1.0.1 extension (the most widely supported on Garmin), with streaming output (`lxml.etree.xmlfile`) for large sets.
- Use the effective coordinates. When corrected coordinates exist, add the original coordinates and the user note at the top of the long description. Set `<sym>Geocache</sym>` or `Geocache Found`, and set `<type>Geocache|<Type>`.
- Option `include_waypoints=true` adds child waypoints as separate `<wpt>` entries, following the Garmin naming convention.
- `GET /api/v1/caches/export.gpx?<same filters as /caches>&include_waypoints=` with `Content-Disposition: attachment; filename="geocaches-YYYYMMDD.gpx"`. It reuses `apply_cache_filter`.
- UI: an "Export GPX" button in the list header, with the option to include waypoints. The export uses the current filters.

## Acceptance criteria
- [ ] AC1: The exported file validates against the GPX 1.0 XSD, and the Groundspeak elements are well-formed.
- [ ] AC2: Round-trip: exporting and then importing the file with the T-007 parser gives equal cache data (except user-data fields).
- [ ] AC3: Corrected coordinates are used, and the note and original coordinates appear in the description.
- [ ] AC4: The export respects the filters (same set as the list).
- [ ] AC5: Exporting 10,000 caches streams without loading everything into memory (memory under 200 MB, slow test).
- [ ] AC6: Manual check: the file loads in Garmin BaseCamp or on a device (record the result in the completion notes).

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC3 | unit | `tests/unit/adapters/test_gpx_writer.py` (XSD files in `tests/fixtures/xsd/`) |
| AC4 | integration | `tests/integration/api/test_cache_export.py` |
| AC5 | integration (slow) | `tests/integration/perf/test_export_perf.py` |
| AC6 | manual | Completion notes |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
