# T-013: Cache details, notes, and corrected coordinates

- **Status:** Ready
- **Milestone:** M1
- **Depends on:** T-012
- **Requirements:** CAC-3, CAC-4, CAC-5, NFR-6
- **Related ADRs:** ADR-0003

## Goal
A cache detail page shows everything that was imported, and lets the user keep a note and set corrected coordinates.

## Scope
### In
- `GET /api/v1/caches/{gc}`: the full cache, waypoints, the latest 20 logs, and user data. Returns 404 problem+json if the cache does not exist.
- `PUT /api/v1/caches/{gc}/user-data`: `{note: str|null (max 10k chars), corrected: {lat, lon}|null}`.
- A coordinate input that accepts the common geocaching formats: `N 52° 05.123 E 005° 07.456` (DDM), decimal degrees, and DMS. Put the parser and formatter in `frontend/src/lib/coords.ts`. Mirror the parser in the backend `domain/coords.py` for validation. Both have extensive tests that use the **same shared test vectors**: `docs/test-vectors/coords.json` (create it).
- Detail page `/caches/:gc`:
  - Header: name, GC code (links to `https://coord.info/<gc>`), type, size, D/T, and status.
  - Coordinates: original and corrected (editable, can be cleared), and a mini map that shows both.
  - The description is sanitized with **DOMPurify** (images allowed, scripts, iframes, and event handlers stripped, and links opened with `rel="noopener noreferrer"` `target="_blank"`).
  - A ROT13 toggle for the hint, the attributes list, the waypoints table, and logs.
  - A note editor (textarea, explicit save button, unsaved-changes indicator).
- The map shows a cache with corrected coordinates at its new position, with a distinct marker.

## Acceptance criteria
- [ ] AC1: The detail endpoint returns the full data. An unknown GC code returns 404.
- [ ] AC2: Saving a note and corrected coordinates persists them. Clearing them works.
- [ ] AC3: The coordinate parser handles DDM, DD, and DMS with N/S/E/W, negative values, and whitespace variants, and rejects garbage (shared vectors pass in both Python and TS).
- [ ] AC4: A malicious description (`<script>`, `onerror=`, `javascript:` URLs) is neutralized.
- [ ] AC5: After setting corrected coordinates, the map marker moves and the distance updates.
- [ ] AC6: The hint ROT13 toggle works.

## Test plan
| AC | Level | Test |
|---|---|---|
| AC1–AC2 | integration | `tests/integration/api/test_cache_detail.py` |
| AC3 | unit (both stacks) | `tests/unit/domain/test_coords.py`, `src/lib/coords.test.ts` |
| AC4, AC6 | component | `src/features/cache-detail/*.test.tsx` |
| AC5 | e2e | `e2e/cache-detail.spec.ts` |

## Definition of Done
- [ ] All ACs are covered
- [ ] `mise run check` is green
- [ ] Completion notes are filled in and the file is moved to `docs/features/complete/`

## Completion notes
_…_
