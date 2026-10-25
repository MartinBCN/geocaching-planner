# Council review: 0004-brouter-routing (review 1)

- **Target:** `docs/adr/0004-brouter-routing.md` (ADR, status at review time: Accepted)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 7 Major · 6 Minor · 2 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve with changes · Quality & Delivery: Approve with changes

## Context provided
- README.md
- AGENTS.md
- docs/specification.md
- docs/adr/0001-record-architecture-decisions.md
- docs/adr/0002-local-single-user-deployment.md
- docs/adr/0003-gpx-first-pluggable-cache-source.md
- docs/adr/0000-template.md

**Anomalies:** none

## Top actions
1. Pin the BRouter release and image source, and tie the recorded contract fixtures and segment set to that pin (#1).
2. Make `RoutingProvider` engine-neutral in the Decision: domain `RouteResult` and a domain profile enum, with BRouter fields kept inside the adapter. Settle the profile-naming dissent (#2, #14).
3. Add the user-facing consequences of segment data: what happens outside the downloaded tiles, and how the user picks a region (#4, #5).
4. State the test and CI position: CI never needs BRouter, contract tests use respx, and the live test runs only on request (#7).
5. Link the follow-up tickets (T-003, T-015, T-016, T-018), and add BRouter's own cons, including the missing matrix API for AUTO-1 (#3, #6).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | ARC-3, QDE-1 | Decision: "We will run **BRouter** as a Docker Compose service with locally downloaded `.rd5` segment files" | No version or image pin, and no segment/engine compatibility rule. Offline routing can't be reproduced, and recorded contract fixtures will drift from the live server. | Pin the release (e.g. `BROUTER_VERSION` in `infra/brouter/Dockerfile`), name the image source and the segment source, and re-record fixtures only when the pin changes. |
| 2 | Major | ARC-1 | Consequences: "`RoutingProvider` lets us swap engines later." | The swap claim fails if the protocol is defined in BRouter terms (GeoJSON, `filtered ascend`, BRouter profile names stored in `Route.profile`). | The Decision states `route(waypoints, profile) -> RouteResult` with domain types. `profile` is a domain enum that the adapter maps. BRouter fields stay in `adapters/brouter`. |
| 3 | Major | ARC-2 | Alternatives: the BRouter row is missing (no cons listed), and spec AUTO-1 says "TSP heuristic, then route through them" | BRouter has no matrix API. AUTO-1 will need N² calls or a second engine. This trade-off is hidden. | Add a "BRouter (chosen)" row with its cons (no matrix, JVM service, one route per request). Add a consequence about a possible future `matrix()` method through a new ADR. |
| 4 | Major | PRD-1 (Major), QDE-6 (Minor) | Consequences: "Fully offline routing." / "Segment files need disk space…" | Points outside the downloaded tiles fail ("position not mapped"). This user-facing failure is not acknowledged, and RTE-7 only covers "unreachable". | Add a consequence: the failure becomes `RoutingFailed` (422), with an actionable message naming the missing tile and the fetch command, and the waypoints are kept. Link a follow-up ticket. |
| 5 | Major | PRD-2 | Decision: "downloaded with `mise run brouter:segments`" | The ADR doesn't say how a user chooses a region or tiles, or what the download size and time are. This is the main setup cost the user sees. | Specify region selection (tile list in `.env`, bbox, or derived from the home location) and the expected size and time. |
| 6 | Major | QDE-2 (Major), ARC-8 (Minor) | Consequences: no follow-up tickets; the template asks to "link the backlog tickets" | Delivery of the decision can't be traced. ADR-0002 (which already places BRouter in compose) is not referenced. | Add Follow-up: T-003, T-015, T-016, T-018. Reference ADR-0002 in Context. |
| 7 | Major | QDE-3 | Consequences: "Fully offline routing." (no test or CI stance) | T-005 ("skipped in CI unless tests need it") and T-015 ("opt-in in CI") don't define an opt-in mechanism, so an agent has to guess. | State: "CI never needs BRouter or segments. respx contract tests (spec §9.2). The `brouter` marker is excluded by default (`-m 'not brouter'`) and runs locally only." |
| 8 | Minor | ARC-4, PRD-4, QDE-5 | Consequences: "Elevation comes in … `filtered ascend`" | BRouter gives ascent but no descent. RTE-4 needs both. Mixing sources risks inconsistent stats and a chart that doesn't match them. | Compute ascent and descent with one pure `domain/` function from the Z series, with a documented hysteresis threshold. Duration comes from `Settings.avg_speed_kmh`. |
| 9 | Minor | ARC-5 | Consequences: no failure-mode item vs RTE-7 | Behavior when BRouter is unavailable or times out, the error mapping (RFC 9457), and health reporting are not covered. | Add: a timeout leads to `RoutingUnavailable`, which maps to 503 problem+json. Waypoints are persisted before compute. `/health` reports BRouter status. |
| 10 | Minor | ARC-6, QDE-7 | Decision: "run **BRouter** as a Docker Compose service" vs ADR-0002 binding to `127.0.0.1` | No port or binding is stated, which risks weakening the localhost-only security model. | "Port bound to `127.0.0.1:17777` (or not published). The backend reads `GCP_BROUTER_URL`." |
| 11 | Minor | PRD-3 | Consequences: "Segment files need disk space…" | Freshness of the routing data is not acknowledged (ADR-0003 does this for caches). | "Routing data is only as fresh as the last segment download. Re-run the task to refresh." |
| 12 | Minor | ARC-7 | Alternatives: "OpenRouteService API … needs internet"; Valhalla "less popular with cyclists" | Unfair comparison. ORS can be self-hosted, and "popularity" is not an architectural criterion. | Add a row for self-hosted ORS, or say why it is excluded. Replace the Valhalla con with a concrete reason. |
| 13 | Minor | QDE-4 (Minor), PRD-5 (Nit) | Decision: "Default profile: `trekking`. Also exposed: `fastbike` and `safety`." | "Exposed" is ambiguous: a UI choice, an API enum, or an adapter allowlist? Where the `.brf` files live, and whether they are committed, is unclear. The UI shows raw engine names. | Define the allowlist (rejected with `InvalidProfile` if not on it), commit the `.brf` files from the pinned release, and show user-facing labels in the UI (e.g. "Touring", "Fast road", "Safest"). |
| 14 | Nit | QDE-8 | Consequences: "Fully offline routing." | Routing needs internet once, to download segments. | "Fully offline routing after a one-time segment download." |
| 15 | Nit | ARC-9, QDE-9 | Header: "- **Status:** Accepted" | The `Reviews:` line is missing, and the ADR was accepted before a council review (AGENTS §3a). | Add `- **Reviews:** docs/reviews/0004-brouter-routing-review-1.md`. |

Severity raised: none. For #4 and #6 the members gave different severities, so the highest severity (Major) was kept, per the Chair rules.

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Missing-segment failure (#4) | PRD-1: **Major**. A predictable dead end for the user, with no guidance on what to do. | QDE-6: **Minor**. A consequence to document. The error path is already specified in T-016. |
| Follow-up ticket links (#6) | QDE-2: **Major**. Without links, nobody can check that the decision was delivered. | ARC-8: **Minor**. A documentation gap. |
| Profile vocabulary (#2, #13) | ARC-1: profiles should be a **domain enum** that the adapter maps to BRouter names, so the DB and API don't depend on BRouter. | QDE-4: the backend should accept **exactly** `trekking`/`fastbike`/`safety` (the BRouter names) as the allowlist. PRD-5 only asks for friendlier UI labels. |
| Quality of the alternatives table (#12) | ARC-7: the comparison is unfair (ORS only judged as a hosted API, Valhalla con not an architectural criterion). | PRD (Strengths): praises the table for framing cons from the user's point of view. |

## Open questions for the author
- Stock profiles, or custom profiles in `infra/brouter/profiles/` (e.g. avoiding unpaved roads)? Who owns them? (ARC, PRD)
- How is the segment region chosen? Are missing segments detected up front (health check, or when a waypoint is added) or only when the route is computed? (ARC, PRD)
- Should `RoutingProvider` already reserve a place for matrix or multi-leg support for AUTO-1, or is that left to a later ADR? (ARC)
- Which BRouter release should be pinned? A maintained image, or a self-built JAR image? (QDE)
- What is the waypoint limit? Should the ADR state it so the adapter's split/stitch logic can be tested? (QDE)
- This ADR was Accepted before review. Should the findings be an amendment, or go into a new ADR? (QDE)

## Strengths
- The `RoutingProvider` protocol keeps the vendor behind an interface and keeps services testable with fakes (spec §6, §9.2).
- It meets NFR-2 (offline routing) and fits the ADR-0002 deployment model.
- It is honest about the disk cost of segments, and segments are git-ignored and downloaded through a mise task (AGENTS §5).
- The profile set matches RTE-3, with `trekking` as the default.

## Process notes
- **Fallback used:** the session had started before `.github/agents/council-*` existed, so the members ran as `general-purpose` agents that loaded their profile files (SKILL.md Step 3 fallback).
- All three outputs followed the contract. No re-prompts were needed.
- This review was a trial run for the skill (ADR-0010).

---

## Appendix A: Software Architect (raw)

**Member verdict:** Approve with changes
**Rationale:** Choosing BRouter fits ADR-0002, NFR-2 and RTE-3, but the ADR claims engines can be swapped without defining an engine-neutral contract, leaves out a known Phase 2 limitation, and does not pin the runtime artifact.

| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Consequences: "`RoutingProvider` lets us swap engines later." and "Elevation comes in the GeoJSON output (3D coordinates) and in `filtered ascend`" | The swap claim only holds if the protocol is engine-neutral. The ADR defines the protocol through BRouter output (GeoJSON, `filtered ascend`). The profile names `trekking`/`fastbike`/`safety` are BRouter vocabulary, and they would be stored in `Route.profile` (spec §7). This is how vendor coupling leaks into `services/`, `domain/` and the database. | In the Decision, state that `RoutingProvider.route(waypoints, profile) -> RouteResult` returns domain types: a LineStringZ in 4326, `distance_m`, `ascent_m`, `descent_m`. Say that `profile` is a domain enum that the adapter maps to BRouter profile names. Say that BRouter-specific fields (GeoJSON, `filtered ascend`) stay in `adapters/brouter`. |
| ARC-2 | Major | Alternatives considered: the table lists no cons for BRouter, and spec §4.7 says "automatically select caches and order them (TSP heuristic), then route through them" | The trade-off is incomplete. AUTO-1 (Phase 2) needs many pairwise distances. BRouter is built for point-to-point routing, while GraphHopper, Valhalla and ORS offer matrix endpoints. Leaving this out hides a likely future cost: many sequential calls or a second engine. That decides how much the protocol must support. | Add a "BRouter (chosen)" row with honest cons: no matrix API, Java service, one route per request. Add a consequence: "AUTO-1 will need N² route calls or a separate matrix capability; `RoutingProvider` may gain a `matrix()` method via a later ADR." |
| ARC-3 | Major | Decision: "We will run **BRouter** as a Docker Compose service with locally downloaded `.rd5` segment files" | The ADR names no image source and no version pin. It also does not say how segment files are kept compatible with the engine version. An unpinned image or unpinned segments make offline routing hard to reproduce and break the contract tests in spec §9.2 ("recorded BRouter responses"). AGENTS §3 would also make an agent stop on an unspecified runtime dependency. | Add: "The image is <name>:<pinned tag>, built from `infra/brouter/` if no maintained image exists. `brouter:segments` downloads from <source>. The segment set must match the pinned BRouter version, and the version is recorded in `.env.example`." |
| ARC-4 | Minor | Consequences: "Elevation comes in … `filtered ascend`" vs spec RTE-4 "total ascent, total descent" | BRouter reports an ascent figure but not a matching descent. The ADR does not say where `descent_m` comes from. This risks two inconsistent ascent/descent methods. | State that ascent and descent are computed by one pure function in `domain/` from the Z coordinates (with stated smoothing). Alternatively, document that the adapter derives descent and why. |
| ARC-5 | Minor | Consequences: there is no item on failure modes, while spec RTE-7 says "If BRouter is unreachable, the user gets a clear error and the route data is not lost" | The ADR does not cover what happens when the router is unavailable or times out. It also does not say how errors map to NFR-5 (RFC 9457) or how `/health` reports BRouter status. | Add a consequence: "Adapter applies a timeout and raises a domain `RoutingUnavailable`. The API maps it to a 503 problem+json, and waypoints are persisted before compute." |
| ARC-6 | Minor | Decision: "run **BRouter** as a Docker Compose service", and ADR-0002: "a FastAPI backend bound to `127.0.0.1`" | The ADR does not say whether the BRouter port is published on all interfaces. That would weaken the localhost-only security model in ADR-0002. | Add: "The BRouter port is not published, or is published as `127.0.0.1:17777`. The backend reaches it on the compose network or on localhost." |
| ARC-7 | Minor | Alternatives considered: "OpenRouteService API \| Easy start \| API key, rate limits, needs internet" and "Valhalla \| … less popular with cyclists" | The comparison is not fair. ORS can be self-hosted (offline, no key), so it is judged here only as a hosted API. "Less popular with cyclists" is not an architectural criterion. | Add a row for self-hosted ORS, or state why it was excluded. Replace the Valhalla con with something concrete, such as the quality of its bike costing or the size of its tile build. |
| ARC-8 | Minor | Consequences section; the template says "Positive, negative, and follow-up work (link the backlog tickets)" | No follow-up tickets are named, for example the compose service, the segment task, the adapter with contract tests, and route compute (M2, T-015–T-020). The ADR also does not reference ADR-0002, which already places "BRouter in Docker Compose". | Link ADR-0002 in Context. List the T-0xx tickets that implement this ADR. |
| ARC-9 | Nit | Header: "- **Status:** Accepted" | The `- **Reviews:**` line from the template is missing, and the ADR is Accepted before a council review (AGENTS §3a recommends review before Proposed→Accepted). | Add `- **Reviews:** docs/reviews/0004-brouter-routing-review-1.md`. |

**Strengths:**
- The vendor sits behind a `RoutingProvider` protocol, as spec §6 requires, and the BRouter adapter is the only implementation.
- The choice meets NFR-2 (fully offline routing) and fits the ADR-0002 deployment model.
- It is honest about segment-file disk cost, and segments are kept out of git, in line with AGENTS §5.

**Open questions:**
- Will we use the stock BRouter profiles or custom ones in `infra/brouter/profiles/`? Who owns changes to those profiles?
- How is the segment region chosen (from config, the home location, or a manual tile list)? What happens when a route crosses a tile that is not downloaded?
- Should `RoutingProvider` already reserve a place for a matrix or multi-leg capability for AUTO-1, or is that left to a later ADR?

**Out of my lane:**
- Product: is the choice of profiles exposed to users (`trekking`/`fastbike`/`safety`) meaningful to them, and should they see display names instead of engine names?
- QDE: contract tests need pinned recorded responses that match the pinned BRouter version, and the live `@pytest.mark.brouter` test needs segments in CI or must be skipped.

## Appendix B: Product Designer (raw)

**Member verdict:** Approve with changes
**Rationale:** BRouter fits the main "plan a bike route" flow and the offline promise, but the ADR leaves out what the user notices: which region to download, routing outside that region, and how fresh the map data is.

| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Major | Consequences: "Fully offline routing." | Routing only works where `.rd5` tiles were downloaded. A rider who plans a trip in a new region, or crosses a 5°×5° tile border (for example NL/DE), will get a failed route. The ADR does not acknowledge this. RTE-7 only covers "BRouter is unreachable", not "no routing data for this area". Without this, the error state will likely be a generic failure, and the user won't know what to do next. | Add a consequence: "Routing fails for waypoints outside the downloaded segments. The user gets an actionable message naming the missing tile (e.g. `E5_N50`) and the command to fetch it. Route waypoints are kept (as in RTE-7)." Link a follow-up ticket. |
| PRD-2 | Major | Decision: "downloaded with `mise run brouter:segments`" | The ADR does not say how the user picks the region or tiles, or how long the download takes. This is the main setup cost of the decision for the user, and README Quickstart only says "for your region". A GSAK/BaseCamp user expects to choose "my area", not to know tile names. | State how a region is chosen (bbox, home location from CAC-6, or a tile list in `.env`) and note the expected download size and time as a user-facing consequence. |
| PRD-3 | Minor | Consequences: "Segment files need disk space (100–500 MB per 5°×5° tile)." | Data freshness is missing. Segments are an OSM snapshot, so new or closed cycle paths only show up after the user downloads again. ADR-0003 acknowledges freshness for caches ("Data is only as fresh as the user's last PQ download"), so this ADR should do the same for routing. | Add: "Routing data is only as fresh as the last segment download. Re-run `mise run brouter:segments` to refresh." |
| PRD-4 | Minor | Consequences: "Elevation comes in the GeoJSON output (3D coordinates) and in `filtered ascend`." | RTE-4 needs total ascent **and descent** plus estimated duration. The ADR only names an ascent source. If the stats disagree with the elevation chart (RTE-5) or with what BaseCamp shows, users will lose trust in them. | State that descent is derived from the same 3D geometry, and that duration uses `Settings.avg_speed_kmh` (not BRouter's time estimate), so the numbers stay consistent. |
| PRD-5 | Nit | Decision: "Default profile: `trekking`. Also exposed: `fastbike` and `safety`." | These are internal BRouter names. "Exposed" does not say whether users see these raw labels. | Add a note that the UI shows user-facing labels (e.g. "Touring", "Fast road", "Safest"). Leave the details to the route-planning ticket. |

**Strengths:**
- It is honest about the disk-space cost, and it matches the spec's offline goal (NFR-2: "Routing is local").
- The profile set matches RTE-3 exactly, with `trekking` as the default, which suits loaded touring and cache trips.
- The alternatives table frames the cons from the user's point of view ("API key, rate limits, needs internet").

**Open questions:**
- Does the app detect missing segments up front (for example in `/health`, or when the user adds a waypoint) or only when the route is computed? This changes which UI states the route tickets need.
- Will the user ever need custom profiles (`infra/brouter/profiles/`), such as avoiding unpaved roads with a loaded bike, or are the three stock profiles final for Phase 1?

**Out of my lane:**
- QDE: The status is already "Accepted" without the template's "**Reviews:**" line, so this council review runs after acceptance, not before (AGENTS.md §3a).
- ARC: Check that the `RoutingProvider` protocol returns provider-neutral elevation and stats, not BRouter-specific fields like `filtered ascend`.
- ARC: The ADR does not mention `infra/brouter/profiles/` from spec §6.1. Clarify whether profiles are stock or vendored.

## Appendix C: Quality & Delivery Engineer (raw)

**Member verdict:** Approve with changes
**Rationale:** The decision is sound and mostly traceable to tickets, but it leaves out the facts that make compliance checkable: version pin, port, image source, follow-up tickets and the CI/test stance. Agents will have to guess these in T-003, T-005 and T-015.

| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Decision: "We will run **BRouter** as a Docker Compose service with locally downloaded `.rd5` segment files" | There is no BRouter version or image pin. T-003 leaves the image open ("build from `infra/brouter/Dockerfile` … if no maintained image exists"). T-015 contract tests replay recorded responses and depend on property names such as `filtered ascend`. If BRouter is not pinned, the recordings and the live server can drift apart, and nobody can tell from the repo which version is in use. | Add: "We pin BRouter to release `<x.y.z>` (`BROUTER_VERSION` in `infra/brouter/Dockerfile`). Recorded fixtures in `backend/tests/fixtures/brouter/` are re-recorded only when that pin changes." |
| QDE-2 | Major | Consequences: "`RoutingProvider` lets us swap engines later." | The template asks for "follow-up work (link the backlog tickets)". No tickets are named, although T-003 (compose service, segments task, profiles), T-015 (adapter), T-016 (error mapping) and T-018 (elevation) implement this decision. Without links, nobody can check whether the decision has been fully delivered. | Add a "Follow-up" bullet: "T-003 compose service + `brouter:segments`; T-015 `RoutingProvider` + BRouter adapter; T-016 503/422 error mapping; T-018 elevation profile." |
| QDE-3 | Major | Consequences: "Fully offline routing." | The ADR adds a Java service to the stack, but it says nothing about tests or CI. The context files disagree with each other: T-005 says "BRouter is skipped in CI unless tests need it; see T-015", and T-015 only says "opt-in in CI". Neither defines the opt-in mechanism, so an agent must guess. Spec §9.2 defines the contract-test approach, and the ADR does not repeat it. | Add: "CI never needs BRouter or segment files. Adapter behaviour is verified by respx contract tests (spec §9.2). The `@pytest.mark.brouter` live test is excluded by default (`-m 'not brouter'`) and runs locally only." |
| QDE-4 | Minor | Decision: "Default profile: `trekking`. Also exposed: `fastbike` and `safety`." | "Exposed" is ambiguous. It could mean a UI choice, an API enum or an adapter allowlist. The ADR also does not say where the `.brf` files live or whether they are committed. `.gitignore` ignores only `segments/*`, and T-003 says "Copy … or fetch them". | Rewrite: "The backend accepts exactly `trekking` (default), `fastbike` and `safety` and rejects anything else with `InvalidProfile`. The matching `.brf` files are committed in `infra/brouter/profiles/` from the pinned release." |
| QDE-5 | Minor | Consequences: "Elevation comes in the GeoJSON output (3D coordinates) and in `filtered ascend`." | BRouter reports ascent but not descent. RTE-4 needs total descent, so we must compute it ourselves (T-015 AC4, with a hysteresis threshold). The ADR does not mention this extra domain logic. | Add: "BRouter does not report descent. We compute it in `domain/` from the elevation series, with a documented hysteresis threshold (T-015)." |
| QDE-6 | Minor | Consequences: "Segment files need disk space (100–500 MB per 5°×5° tile)." | The ADR does not say what happens when a point falls outside the downloaded tiles. In that case BRouter returns "position not mapped in existing datafile", and RTE-7 requires a clear error. This is a predictable user-facing failure, and it should be stated as a consequence. | Add: "Routing outside the downloaded tiles fails with `RoutingFailed` (HTTP 422, per T-016). The user downloads more tiles with `BROUTER_SEGMENTS=… mise run brouter:segments`." |
| QDE-7 | Minor | Decision: "run **BRouter** as a Docker Compose service" | ADR-0002 requires localhost-only binding ("bind to localhost"), but this ADR gives no port or binding for the new service. T-003 picks `127.0.0.1:17777`, and the ADR cannot be checked against it. | Add: "Port bound to `127.0.0.1:17777`. The backend reads `GCP_BROUTER_URL`." |
| QDE-8 | Nit | Consequences: "Fully offline routing." | Routing needs internet once, to download the segments. | "Fully offline routing after a one-time segment download." |
| QDE-9 | Nit | Header: "- **Status:** Accepted" | The `- **Reviews:**` line from `0000-template.md` is missing. | Add `- **Reviews:** –` and link this council report once it is written. |

**Strengths:**
- The `RoutingProvider` protocol keeps services testable with fakes, which fits the spec §6 layering and the §9.2 contract-test level.
- The segment files are git-ignored and downloaded through a named mise task, which matches the `.gitignore` and AGENTS.md §5 ("no … BRouter segment files in git").
- The profile names match RTE-3 exactly, so the ADR, the spec and T-015's allowlist agree.

**Open questions:**
- Was this ADR set to Accepted before a council review? AGENTS.md §3a recommends a review before `Proposed → Accepted`. Should the findings be applied as an amendment or in a new ADR?
- Which BRouter release should be pinned? Is a maintained Docker image acceptable, or is the self-built JAR image the decision?
- How many waypoints is the route limited to? T-015 says the adapter "splits and stitches" at "BRouter's waypoint limit". Should the ADR state the limit so the adapter can be tested against it?

**Out of my lane:**
- Architect: the ADR does not weigh JVM memory or startup cost of BRouter against Valhalla or GraphHopper, and the "less popular with cyclists" con for Valhalla has no source.
- Product Designer: there is no guidance on how users choose and download segment regions beyond the `BROUTER_SEGMENTS` environment variable.
