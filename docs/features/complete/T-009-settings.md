# T-009: Settings (home location, defaults)

- **Status:** Complete
- **Milestone:** M1
- **Depends on:** T-006
- **Requirements:** CAC-6, RTE-4 (avg speed), CAR-1 (default corridor), MAP-1 (tile URL)
- **Related ADRs:** –

## Goal
The user can set a home location and app defaults, which are persisted and used by other features.

## Scope
### In
- A singleton `settings` table and migration. Fields: `home_location` (nullable point), `avg_speed_kmh` (default 18), `corridor_m_default` (default 500), `default_profile` (default `trekking`), and `tile_url` (nullable; falls back to the env default `GCP_TILE_URL`, CyclOSM) plus `tile_attribution`.
- `GET/PUT /api/v1/settings` with validation (speed 5–50, corridor 50–5000).
- Frontend `/settings` page: a form, with the home location entered as lat/lon (a map picker is added in T-011). Use `react-hook-form` + `zod`, or simple controlled inputs. Do not add a new dependency without noting it in the completion notes.

## Acceptance criteria
- [x] AC1: GET returns defaults on a fresh DB.
- [x] AC2: PUT with valid data persists it. Invalid data returns 422 problem+json.
- [x] AC3: The UI loads, edits, and saves the settings, and shows validation errors.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC2 | integration | `tests/integration/api/test_settings.py` |
| AC3 | component | `src/features/settings/SettingsPage.test.tsx` |

## Definition of Done
- [x] All ACs are covered
- [x] `mise run check` is green
- [x] `.env.example` documents `GCP_TILE_URL`
- [x] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
- Added a singleton `settings` table in migration `0003` with a tested downgrade, and persisted home coordinates, cycling defaults, tile URL override, and attribution.
- Added `GET/PUT /api/v1/settings`, with RFC 9457 validation errors and configured CyclOSM URL/attribution defaults.
- Replaced the Settings placeholder with an accessible form that loads, validates, saves, and reports errors using the generated API client.
- Documented `GCP_TILE_URL` in `.env.example` and the settings model in specification §7.
- `mise run api:gen` and `mise run check` pass; the settings API, migration round-trip, and frontend form are covered by automated tests.
