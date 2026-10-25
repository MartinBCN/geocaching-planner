# ADR-0012: Hardened XML parsing for Pocket Query imports

- **Status:** Proposed
- **Date:** 2026-10-25
- **Reviews:** –

## Context
T-007 parses user-supplied GPX files, including GPX files inside ZIP uploads. The parser must stream large inputs, avoid resolving external entities or loading network resources, and resist entity expansion and oversized-document attacks. Python's standard library does not provide the required streaming and hardening combination without an additional package. A runtime XML dependency also needs to be verified against the pinned Python 3.14.x toolchain.

## Decision
We propose using **`lxml`** and its streaming `iterparse` API for Pocket Query XML. Parser calls must disable entity resolution, network access, DTD loading, and huge-tree mode; documents containing entity declarations are rejected. ZIP member and total uncompressed-size limits remain the responsibility of T-007.

Before this ADR can be accepted, verify that the selected `lxml` release installs under the pinned Python 3.14.x toolchain. T-007 must add it as a runtime dependency and test the hardened parser behavior, including external entities, entity expansion, and ZIP limits.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| `lxml` with hardened streaming parser (proposed) | Mature streaming API; explicit controls for entity resolution, network access, DTD loading, and huge trees | Adds a compiled runtime dependency; Python 3.14 installation compatibility must be verified |
| `xml.etree` plus `defusedxml` | Standard-library tree API with defenses against XML entity attacks; avoids a libxml2 binding | Streaming behavior and the required security controls are less direct to configure and verify together |
| `xml.etree` alone | No additional dependency | Does not provide the complete explicit hardening contract required for untrusted uploads |

## Consequences
- T-007 remains Blocked until this ADR is accepted.
- If accepted, T-007 owns adding the runtime dependency and proving Python 3.14.x installation compatibility as well as the parser security and performance tests.
- Any Ruff `S` suppression must be per-line, name the exact rule, and explain the safe parser configuration; no global rule changes are permitted.
- If the selected release cannot be installed under Python 3.14.x, revisit the alternatives before accepting this ADR.
