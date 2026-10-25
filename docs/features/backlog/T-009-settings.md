# T-009: Settings (home location, defaults)

- **Status:** Ready
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
- [ ] AC1: GET returns defaults on a fresh DB.
- [ ] AC2: PUT with valid data persists it. Invalid data returns 422 problem+json.
- [ ] AC3: The UI loads, edits, and saves the settings, and shows validation errors.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC2 | integration | `tests/integration/api/test_settings.py` |
| AC3 | component | `src/features/settings/SettingsPage.test.tsx` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] `.env.example` documents `GCP_TILE_URL`
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
