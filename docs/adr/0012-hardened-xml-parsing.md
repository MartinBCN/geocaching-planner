# ADR-0012: Hardened XML parsing for Pocket Query imports

- **Status:** Accepted
- **Date:** 2026-10-26
- **Reviews:** –

## Context
T-007 parses user-supplied GPX files, including GPX files inside ZIP uploads. The parser must stream large inputs, avoid resolving external entities or loading network resources, and resist entity expansion and oversized-document attacks. Python's standard library does not provide the required streaming and hardening combination without an additional package. A runtime XML dependency also needs to be verified against the pinned Python 3.14.x toolchain.

## Decision
Use **`lxml`** and its streaming `iterparse` API for Pocket Query XML. Parser calls must disable entity resolution, network access, DTD loading, and huge-tree mode; documents containing entity declarations are rejected. ZIP member and total uncompressed-size limits remain the responsibility of T-007.

The selected `lxml` release must install under the pinned Python 3.14.x toolchain. T-007 adds it as a runtime dependency and tests the hardened parser behavior, including external entities, entity expansion, and ZIP limits.

## Alternatives considered
| Option | Pros | Cons |
|---|---|---|
| `lxml` with hardened streaming parser (chosen) | Mature streaming API; explicit controls for entity resolution, network access, DTD loading, and huge trees | Adds a compiled runtime dependency; Python 3.14 installation compatibility must be verified |
| `xml.etree` plus `defusedxml` | Standard-library tree API with defenses against XML entity attacks; avoids a libxml2 binding | Streaming behavior and the required security controls are less direct to configure and verify together |
| `xml.etree` alone | No additional dependency | Does not provide the complete explicit hardening contract required for untrusted uploads |

## Consequences
- `lxml` 6.1.3 was installed and imported successfully under pinned Python 3.14.9 during T-007.
- T-007 adds the runtime dependency and verifies Python 3.14.9 compatibility as well as parser security and performance.
- Any Ruff `S` suppression must be per-line, name the exact rule, and explain the safe parser configuration; no global rule changes are permitted.
- If a future pinned Python release cannot install the selected `lxml`, revisit the alternatives in a superseding ADR.
