# T-023: BRouter Compose service and segments

- **Status:** Complete
- **Milestone:** M0
- **Depends on:** T-003
- **Requirements:** NFR-2, NFR-3, RTE-3
- **Related ADRs:** ADR-0004
- **Reviews:** –

## Goal
Run BRouter locally in Compose and provide a safe, repeatable way to download regional segment data for offline bicycle routing.

## Context
ADR-0004 selects BRouter and requires local `.rd5` segment files. T-003 owns the PostGIS service and database tooling; this ticket separates BRouter container, profiles, and segment download work from the database migration ticket. T-015 depends on this service.

## Scope
### In
- Add the BRouter service to `compose.yaml`, built from `infra/brouter/Dockerfile` with a pinned official release JAR and checksum if no maintained image is suitable. Mount `infra/brouter/segments` and `infra/brouter/profiles`; bind `BROUTER_PORT` (default 17777) to `127.0.0.1`; add a healthcheck.
- Extend `mise run dev` to start the BRouter Compose service alongside the existing database/backend startup without requiring downloaded segments.
- Add `mise run brouter:segments` to download configured tiles from `https://brouter.de/brouter/segments4/`. Default to `E0_N50` and `E5_N50`, providing initial coverage for 0–10°E, 50–55°N. Honor `BROUTER_SEGMENTS`, download to a temporary file and rename on success, skip complete existing files, and report per-file progress and a downloaded/skipped/failed summary.
- Extend the `mise run test:compose:dev` task introduced by T-003 to include BRouter, verifying it reaches health without downloaded routing data.
- Keep segment data git-ignored. If no `.rd5` files exist, the service still starts and reports “No routing data found — run `mise run brouter:segments`”; routing outside downloaded coverage returns an actionable failure.
- Install the `trekking`, `fastbike`, and `safety` profiles into `infra/brouter/profiles`.
- Document tile naming as the south-west corner of a 5°×5° tile, coverage limitations, how to add tiles, disk usage, and that `docker compose down -v` deletes database data.

### Out
- PostGIS, migrations, and database health probe (T-003).
- BRouter API adapter and profile selection in the backend (T-015).

## Implementation notes
- Use Python for the downloader and test HTTP behavior with respx; do not make network requests in tests.
- Pin the BRouter release and SHA-256 checksum as Docker build arguments. Keep exposed host ports loopback-only.
- `E0_N50` covers 0–5°E, 50–55°N; `E5_N50` covers 5–10°E, 50–55°N. Areas outside those bounds require additional tiles.
- The optional `@pytest.mark.brouter` live test is skipped when `E5_N50.rd5` is absent and is excluded from CI because segment downloads are large and network-dependent.

## Acceptance criteria
- [ ] AC1: Given no downloaded segments, when `docker compose up -d --wait brouter` runs, then BRouter is healthy and logs the actionable missing-data message.
- [ ] AC2: Given an installed `E5_N50.rd5`, when the optional live route test requests a short route within coverage, then it returns HTTP 200 with a GeoJSON FeatureCollection containing a LineString with at least two coordinates and elevation.
- [ ] AC3: Given a configured tile list and mocked successful/failed HTTP responses, when the downloader runs, then it downloads to a temporary file, renames only complete files, reports progress and a final summary, and exits non-zero if any tile fails.
- [ ] AC4: Given a complete existing tile, when the downloader runs, then it skips the file without issuing a request; given `BROUTER_SEGMENTS` overrides defaults, then only the configured tiles are processed.
- [ ] AC5: Given the Compose configuration, when port-boundary checks run, then the BRouter host port is published only on `127.0.0.1`.
- [ ] AC6: Given the README routing section, when reviewed by an automated documentation test, then tile naming, coverage gaps, tile download instructions, disk usage, and database volume deletion warning are present.
- [ ] AC7: Given `mise run dev`, when the database, backend, and BRouter services start, then BRouter is included and healthy even when no segments have been downloaded; `mise run test:compose:dev` verifies this behavior.

## Test plan
| AC | Test level | Test (file / name) |
|---|---|---|
| AC1, AC5 | automated compose/config test | `backend/tests/unit/test_brouter_compose.py::test_service_starts_without_segments_and_binds_loopback` |
| AC2 | optional live (`brouter`; skipped without tile) | `backend/tests/contract/test_brouter_live.py::test_short_route_within_segment_coverage` |
| AC3–AC4 | unit (respx) | `backend/tests/unit/test_segment_downloader.py` |
| AC6 | docs | `backend/tests/unit/test_readme_brouter_docs.py::test_brouter_coverage_is_documented` |
| AC7 | automated compose smoke | `mise run test:compose:dev` |

## Definition of Done
- [ ] All ACs are covered by automated tests
- [ ] `mise run check` is green
- [ ] Docs are updated (README / spec / AGENTS / ADR if needed)
- [ ] There are no TODOs without a linked backlog ticket
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_Filled in by the implementer: summary, deviations, follow-up tickets created._
