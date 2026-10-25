# T-022: Geocaching.com API cache source

- **Status:** Blocked: requires Geocaching.com API partner access
- **Milestone:** Phase 2
- **Depends on:** T-008
- **Requirements:** API-1
- **Related ADRs:** ADR-0003; a new ADR is required (OAuth token storage, rate limiting)

## Goal
Implement `CacheSource` for the official Geocaching.com API, so the user can refresh caches without manual PQ downloads.

## Context
Only possible after the project is approved as a Geocaching.com API partner. The API uses OAuth 2.0 (PKCE) and has rate limits. The data flow stays **one-way** (read-only). Do not implement any scraping fallback.

## Unblock criteria
- Partner API credentials are available.
- An ADR covers token storage (local, encrypted at rest), rate limiting, and ToS compliance.

## Acceptance criteria
_To be defined when this ticket is unblocked._

## Completion notes
_…_
