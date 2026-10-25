# ADR-0002: Local single-user deployment

- **Status:** Accepted
- **Date:** 2026-10-25
- **Reviews:** [Council review 1](../reviews/adr/0002-local-single-user-deployment-review-1.md)

## Context
The tools we want to replace (GSAK, BaseCamp) are personal desktop tools. The sketch chose FastAPI and PostgreSQL, which imply a server process.

## Decision
We will run the app **locally for a single user**: a FastAPI backend bound to `127.0.0.1`, a React UI in the browser, and PostgreSQL/PostGIS plus BRouter in Docker Compose. Any Compose service port published on the host must bind to `127.0.0.1`; services that do not need host access must remain unpublished. Automated checks must verify this boundary. There is no authentication and no multi-tenancy.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| Self-hosted web app (VPS) | Access from anywhere | Needs auth, TLS, hosting, ops |
| Multi-user SaaS | Shareable | Large scope; data licensing issues with geocaching.com content |
| Desktop app (Tauri/Electron) | Native feel | Extra packaging complexity; we can add it later around the same web UI |

## Consequences
- Simple security model. We must still sanitize HTML (XSS) and bind to localhost.
- Requires Docker on the user's machine.
- Routing is local but requires regional BRouter data; map tiles require an internet connection.
- If we ever expose it on a network, that needs a new ADR (auth).
