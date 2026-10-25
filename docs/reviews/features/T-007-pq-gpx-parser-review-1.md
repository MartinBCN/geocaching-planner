# Council review: T-007-pq-gpx-parser (review 1)

- **Target:** `docs/features/backlog/T-007-pq-gpx-parser.md` (Ticket, status at review time: Ready)
- **Date:** 2026-10-25
- **Council verdict:** **Approve with changes**
- **Findings:** 0 Blocker · 9 Major · 6 Minor · 1 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve with changes · Quality & Delivery: Approve with changes

## Context provided
- README.md
- AGENTS.md
- docs/specification.md
- docs/adr/0001-record-architecture-decisions.md … docs/adr/0010-council-review.md (all Accepted)
- docs/features/backlog/T-006-cache-domain-model.md
- docs/features/TEMPLATE.md
- docs/features/README.md

**Anomalies:** none

## Top actions
1. Define the `CacheParseResult` contract in `services/ports.py`. It needs a parsed/error union, a **warnings channel**, and a `ParseIssue(file incl. ZIP entry, gc_code, line, message)` type. Decide whether the port is sync or async, and add a source identity (#2, #5).
2. Fix the found-status rule: use `<sym>Geocache Found</sym>` only in Phase 1 (no PQ owner identity exists), and add an AC for it (#1).
3. Specify two-pass waypoint linking across **all** inputs of one source, and the PQ string → enum mapping tables (cache, container, waypoint, and log types) (#3, #6).
4. Make the ACs measurable: a golden-object mapping AC, a concrete definition of "corrupt", a reproducible perf/memory method, and observable XXE and entity-expansion assertions (#7, #8, #9, #10).
5. Resolve how `lxml` is governed: write a short ADR, or point to where it is already approved. Also name `types-lxml` (#4).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Major | PRD-1 (Major), QDE-1 (Major), ARC-7 (Minor) | Scope/In: "`groundspeak` found logs by the PQ owner" | The parser has no input that identifies the PQ owner, and no ticket stores a username. `found_at` cannot be derived, and no AC covers found status. A wrong found flag breaks CAC-2 filters and MAP-2 markers. | Phase 1: `found_by_me` comes from `<sym>Geocache Found</sym>` only. `found_at` is null unless a defined rule exists. Move the log-based variant to a follow-up ticket. Add AC: "Given a cache with `<sym>Geocache Found</sym>`, `found_by_me=True`; others `False`." |
| 2 | Major | ARC-3, QDE-2, PRD-2 (Major), PRD-4 (Minor) | Scope/In: "`iter_caches() -> Iterator[CacheParseResult]` (success or error with context)" | The result type is undefined, but T-008 (IMP-6) and T-022 depend on it. There is no warnings channel, although Scope emits warnings. "Context" lacks the file name and ZIP entry, so a user can't act on errors. lxml exceptions could leak through the port. | `ParsedCache(cache, warnings: list[ParseIssue]) \| ParseError(issue)`, with `ParseIssue(file, entry, gc_code \| None, line \| None, message)`. Add a way to report file-level warnings. Adapter exceptions are mapped to `ParseError`. |
| 3 | Major | ARC-2, QDE-6 (Major), PRD-5 (Minor) | Scope/In: "Links waypoints to their parent cache by prefix and code." | It's unclear whether linking works across separate `.gpx` inputs, and how a streaming iterator can attach waypoints that appear in another file. This affects both memory use (AC7) and correctness. | **Must:** parse all `*-wpts.gpx` files across all inputs into `dict[gc_code, list]` first, then stream the caches. Add ACs: separate `x.gpx` + `x-wpts.gpx` are linked, and ZIP entry order doesn't matter. |
| 4 | Major | ARC-1 (Major), QDE-11 (Minor) | Scope/In: "Parse with **`lxml`** using `iterparse`"; ADR-0001: "Significant means: a new dependency" | `lxml` is a new native runtime dependency, and no ADR covers it, so ADR-0001 tells the agent to stop. mypy strict also needs stubs, which aren't named. | Add a short ADR (lxml vs stdlib + `defusedxml`) or cite an existing approval. Name `types-lxml`/`lxml-stubs` as a dev dependency. |
| 5 | Major | ARC-4 | Scope/In: "`iter_caches() -> Iterator[CacheParseResult]`"; ADR-0003: "a future Geocaching.com API source … can plug in" | A sync port blocks the async service in T-008 and forces the T-022 HTTP source to be sync. There is no source identity for `ImportRun.source` or `filenames`. | Decide: an `AsyncIterator`, or a sync port with "callers use `anyio.to_thread`". Add `source_name` and the input filenames to the protocol. |
| 6 | Major | QDE-4 (Major), PRD-3, ARC-6 (Minor) | Scope/In: "maps types and sizes to domain enums" | There are no mapping tables (e.g. "Unknown Cache" → Mystery, "Cache In Trash Out Event", "Letterbox Hybrid", log and waypoint types). Spec §7 fields such as `description_is_html`, `owner`, `placed_at`, `country`, and `source_updated_at` are not mapped. Defaults could later change `source_hash`. | Add Implementation notes tables: PQ string → CacheType, ContainerSize, WaypointType, LogType (case-insensitive, unknown → `OTHER` + warning), plus the full GPX → domain field mapping. Confirm that T-006 provides `OTHER` members. |
| 7 | Major | QDE-3 | AC1: "identical domain objects" is the only mapping AC | The mapping behaviours promised in Scope have no ACs. AC1 passes even when both versions are wrong in the same way. `missing_optional_fields.gpx` is not used. | Add a golden AC against `expected_pq.py`. Add ACs for unknown type → `OTHER` with a warning, an orphan-waypoint warning, and missing optional fields → `None`. |
| 8 | Major | QDE-5 | AC7: "peak memory stays under 200 MB" | No measurement method is given (`tracemalloc` misses lxml's C allocations). The generator is unnamed, the 5 s limit can be flaky on CI, and it's unclear whether `slow` tests run in `check`. | Name the generator (`make_pq(n)` writing to `tmp_path`), measure with `ru_maxrss` delta < 200 MB, require `elem.clear()`, and state whether `slow` runs in `mise run check`. |
| 9 | Major | QDE-7 | AC3: "A corrupt entry yields an error result with GC code or line info" | "Corrupt" is undefined. A semantic error and an XML well-formedness error behave very differently. "or" makes the assertion weak. | Define the fixture: 3 caches, and #2 has `lat="abc"`. The result is 2 `ParsedCache` + 1 `ParseError(gc_code="GC0TEST2", line set)`. Malformed XML becomes a file-level error, or use `recover=True`. Make that decision explicitly. |
| 10 | Minor | ARC-5, QDE-10 | Scope/In: "Disable entity resolution and network access"; AC5: "An XXE payload is not resolved." | Only XXE is covered. Billion-laughs entity expansion and ZIP bombs are not. AC5 has no observable assertion. | Name the parser flags (`resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False`), cap ZIP uncompressed size and entry count, and add an entity-expansion fixture. AC5 asserts that the sentinel is absent, no socket is opened, and parsing takes < 1 s. |
| 11 | Minor | QDE-8 | Scope/In: "files: Sequence[Path \| BinaryIO]" | A `BinaryIO` has no file name, so ZIP vs GPX detection is unspecified. Corrupt ZIPs and non-GPX ZIP entries have no defined result. | Detect ZIP by the magic bytes `PK\x03\x04`. Add a `corrupt.zip` fixture. Extend AC4 to expect a single file-level `ParseError`. |
| 12 | Minor | QDE-9 | AC6: "preserved byte-exact" | Domain fields are decoded strings, so "byte-exact" cannot be tested as written. | Use string equality with the XML-unescaped source. Check that `description_is_html` reflects the `html` attribute. |
| 13 | Minor | PRD-6 | Scope/In: "`PocketQuerySource(files: …)`" | Overlapping PQs are normal. When the same GC code appears in two files, the counts and the result depend on file order. | Rule: one cache per GC code per source. The entry with the latest GPX `<time>` wins, and a warning is emitted. |
| 14 | Minor | QDE-12 | Test plan: "AC1–AC6 \| unit \| `tests/unit/adapters/test_pq_source.py`" | No test names are given, and fixtures are not mapped to ACs. | Add one row per AC with `file::test_name (fixture)`. |
| 15 | Minor | QDE-13 (Minor), ARC-8, PRD-7 (Nit) | Header: "- **Related ADRs:** ADR-0003" then "## Goal" | The `Reviews:` line and the Implementation notes section are missing, and the DoD lacks the "Docs are updated" item. | Follow `TEMPLATE.md`, and move the implementation details from Scope into Implementation notes. |
| 16 | Nit | QDE-14 | "`backend/tests/fixtures/pq/`" vs "`tests/unit/adapters/…`" | The path roots are inconsistent. | Use `backend/tests/...` everywhere. |

Severity raised: none. Where members gave different severities (#1, #2, #3, #4, #6, #15), the highest severity was kept, per the Chair rules.

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Found-status gap (#1) | PRD-1, QDE-1: **Major**. It can't be implemented without guessing, and the result is highly visible to the user. | ARC-7: **Minor**. It's a data-mapping detail. Fall back to `<sym>`. |
| `lxml` choice (#4) | ARC-1: **Major**. It needs an ADR under ADR-0001 before an agent can proceed. | QDE (Strengths): counts the fixed library choice as a strength ("no open choice there"), and only flags the missing stubs (Minor). |
| Warnings channel (#2) | ARC-3, QDE-2: **Major**. It's part of an undefined port contract. | PRD-4: **Minor**. It's mainly about what the user sees in T-008. |
| "Byte-exact" descriptions (#12) | PRD (Strengths): praises AC6 for keeping the owner's HTML faithful. | QDE-9: as worded, AC6 can't be tested. It should use string equality. |
| Cross-file waypoint linking (#3) | ARC-2, QDE-6: **Major**. It drives the streaming design and the memory budget. | PRD-5: **Minor**. It's a missing AC for a common user habit. |

## Open questions for the author
- Do Pocket Queries write the user's **corrected coordinates** into `<wpt lat/lon>`? If they do, the import stores a solved location as the "original", which breaks CAC-5. (PRD) **The Chair flags this as potentially important: it could affect T-006 and T-013 as well.**
- Is `lxml` already approved anywhere? (ARC)
- Should waypoints be linked across separately uploaded files in one import call? (ARC; see #3)
- Will a PQ owner username ever be configured? If not, should `found_at` stay null? (ARC, QDE)
- Should a valid PQ with zero caches be an empty result or a notice? Should non-GPX ZIP entries be ignored or produce a warning? (PRD)
- Does `mise run check` run `slow` tests? Does T-006 guarantee `OTHER` members in every enum? (QDE)

## Strengths
- Fits the layering: the port is in `services/ports.py`, the adapter in `adapters/gpx/` (spec §6, ADR-0003).
- Hostile input (XXE) and memory are considered up front. Fixtures are synthetic and cover real-world variety.
- Errors are reported per entry, so one bad cache does not cost the user the whole PQ (IMP-7).
- HTML is kept raw and sanitized at render time (NFR-6). The goal is clear, Out is crisp, and the T-006 dependency is correct.

## Process notes
- **Fallback used:** the session had started before `.github/agents/council-*` existed, so the members ran as `general-purpose` agents that loaded their profile files (SKILL.md Step 3 fallback).
- All three outputs followed the contract. No re-prompts were needed.
- This review was a trial run for the skill (ADR-0010).

---

## Appendix A: Software Architect (raw)

**Member verdict:** Approve with changes
**Rationale:** The ticket fits ADR-0003 and the spec's layering, but four Major gaps need fixing before an agent implements it: the parser library choice is not recorded in an ADR, the result/warning contract is undefined, the protocol does not say whether it is sync or async, and the cross-file waypoint linking conflicts with the streaming design.

| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Scope/In: "Parse with **`lxml`** using `iterparse`"; ADR-0001: "Significant means: a new dependency or framework" | No Accepted ADR covers `lxml`, a new runtime dependency with native code. ADR-0001 says an agent must write an ADR and stop in this case, so the agent will likely stop or quietly bypass the rule. Choosing `lxml` over the stdlib parser plus `defusedxml` is a real trade-off that should be recorded. | Before Ready, add a short Proposed ADR, e.g. "XML parsing with lxml (hardened)", compare it with stdlib + `defusedxml`, and list it under Related ADRs. If `lxml` was already approved elsewhere (e.g. in T-002), cite that. |
| ARC-2 | Major | Scope/In: "`PocketQuerySource(files: Sequence[Path \| BinaryIO])`" … "Links waypoints to their parent cache by prefix and code." | The source must yield `Cache` objects that already contain their waypoints (ADR-0003), but the waypoints live in a different file (`-wpts.gpx`). That file may come later in the ZIP, or as a separate upload. Streaming caches one by one with `iterparse` then means buffering every cache, which undercuts the "memory-safe" claim and AC7. The ticket also does not say whether linking works across all inputs or only within one ZIP. | Add an implementation note: "Pass 1 (**must**): parse all waypoint files across all `files` into a dict keyed by GC code. Pass 2: stream the cache files and attach the waypoints. Leftovers become orphan warnings." Say that linking covers all inputs of one `PocketQuerySource`. |
| ARC-3 | Major | Scope/In: "`iter_caches() -> Iterator[CacheParseResult]` (success or error with context)" | `CacheParseResult` is the contract T-008 (IMP-6 summary, `ImportRun.errors`) and T-022 depend on, but the ticket does not define it. Undefined: where it lives (domain or services), its fields (file, GC code, line, message), how warnings are carried (the ticket emits warnings for unknown types and orphans, but the result is only "success or error"), and that lxml exceptions must not leak out of the adapter. | Define it, e.g. in `services/ports.py`: `CacheParsed(cache, warnings)` \| `ParseError(file, gc_code \| None, line \| None, message)`, plus source-level warnings. Add: "Adapter exceptions are mapped to `ParseError`. No lxml types appear in the port." |
| ARC-4 | Major | Scope/In: "`CacheSource` protocol, `iter_caches() -> Iterator[CacheParseResult]`"; ADR-0003: "a future Geocaching.com API source (T-022, blocked) can plug in" | A sync `Iterator` port fixes two things that are hard to change later. First, the async service in T-008 will block the event loop unless it moves parsing to a thread. Second, the HTTP-based API source in T-022 would have to be sync. The port also has no source identity, but `ImportRun.source` and `filenames` (spec §7) need one. | Decide explicitly and write it down. Either use `AsyncIterator[CacheParseResult]`, or keep the port sync and state "callers run it via `anyio.to_thread`". Add `source_name: str` (e.g. `"pq"`) and the input filenames to the protocol. |
| ARC-5 | Minor | Scope/In: "Disable entity resolution and network access, so XXE is not possible." | This covers XXE only. Two hostile-input risks remain: entity expansion ("billion laughs") and ZIP bombs (very large uncompressed members or very many members). The importer accepts arbitrary uploads, so these are real risks. | Name the parser flags (`resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False`). Reject a `DOCTYPE` with entity declarations. Cap the uncompressed size and member count of ZIPs. Add an `entity_expansion.gpx` fixture to the AC5 tests. |
| ARC-6 | Minor | Scope/In: "keep HTML raw; sanitizing happens at render time" | The ticket does not map several spec §7 fields: `description_is_html` (from the Groundspeak `html="True"` attribute), `source`, `source_updated_at`, `owner`, `placed_at`, `country`, `state`, and waypoint and log types into `WaypointType`/`LogType`. It only covers fallbacks for cache type and size. The result could be domain objects with defaults, which change `source_hash` later. | List the full GPX → `Cache`/`CacheWaypoint`/`CacheLog` field mapping in implementation notes. Apply the "unknown → `Other` + warning" rule to the waypoint and log types as well. |
| ARC-7 | Minor | Scope/In: "`groundspeak` found logs by the PQ owner" | The parser cannot tell who the PQ owner is: no setting or input provides that identity (spec §7 `Settings` has no username). So `found_at` cannot be derived reliably. | Derive `found_by_me` from `<sym>Geocache Found</sym>` only. Set `found_at` only if a defined rule exists (e.g. the newest "Found it" log when sym is Found). Otherwise leave it null and record this in the completion notes. |
| ARC-8 | Nit | Header: "- **Related ADRs:** ADR-0003" | The `Reviews:` line and the "Implementation notes" section from `TEMPLATE.md` are missing. Several of the recommendations above belong in that section. | Add both, following the template. |

**Strengths:**
- Puts the port in `services/ports.py` and the adapter in `adapters/gpx/`, which matches spec §6 and ADR-0003.
- Takes XXE and memory into account up front, uses synthetic fixtures, and reports errors per entry (IMP-7).
- Keeps HTML raw and sanitizes at render time, consistent with NFR-6.

**Open questions:**
- Is `lxml` already approved anywhere, such as in T-002's dependency list? That decides whether ARC-1 needs a new ADR.
- Should one import call link waypoints across separately uploaded `.gpx` files, or only within one ZIP?
- Is the PQ owner's username ever meant to be configured? If not, should `found_at` stay null for PQ imports?

**Out of my lane:**
- QDE: AC6 says "byte-exact", but the parser decodes entities and normalizes encodings, so "character-exact" may be the testable wording.
- QDE: The test plan has no fixture or AC for entity expansion, orphan-waypoint warnings, or unknown-type warnings.
- QDE: AC7 has no reproducible method for measuring peak memory.

## Appendix B: Product Designer (raw)

**Member verdict:** Approve with changes
**Rationale:** The parser supports the first step of the main user flow, import, but the ticket does not define found-status detection, and its error messages do not tell the user enough to act. Both gaps will show up in what the user sees in T-008 and on the map.

| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Major | Scope/In: "`groundspeak` found logs by the PQ owner" | The ticket never says how the parser knows who the PQ owner is. A PQ has no explicit owner field, and no ticket stores a geocaching username (T-009 covers home location and defaults). The ticket also does not say where `found_at` (spec §7) comes from, and no AC covers found status. If the user's finds are flagged wrongly, the "found/not found" filter (CAC-2) and the found markers (MAP-2) break. For this user, that is one of the most visible failures. | Define the rule. For example: "`found_by_me` = `<sym>Geocache Found</sym>`. `found_at` = date of the newest `Found it`/`Attended`/`Webcam Photo Taken` log whose finder matches the owner, else null." Say where the owner name comes from, or drop the log-based rule. Add an AC: "Given a cache with `<sym>Geocache Found</sym>`, then `found_by_me` is true and `found_at` is set as defined." |
| PRD-2 | Major | AC3: "yields an error result with GC code or line info" | IMP-7 asks for a "clear error", and these results become the error list in the T-008 summary. The context does not include the file name, or the entry name inside a ZIP. A user who uploads 3 ZIPs with 6 GPX files gets "line 4812" with no file, which they cannot act on. The ticket also defines no message text. | Require each error to carry `file` (plus the entry inside the ZIP), plus `gc_code` when known or `line` otherwise, and a short readable `message`. Rewrite AC3: "…error result naming the file, the GC code (or line), and a human-readable reason; parsing continues." Apply the same to AC4. |
| PRD-3 | Minor | Scope/In: "unknown values go to `Other`, with a warning" | The ticket has no table of the exact PQ type strings. PQ uses "Unknown Cache" for Mystery caches, "Cache In Trash Out Event", "Mega-Event Cache", "Letterbox Hybrid", and so on. A naive match could send Mystery or event caches to `Other`, which breaks type filters and marker styles that GSAK users rely on. | Add an explicit mapping table from PQ type/container strings to `CacheType`/`ContainerSize`, including `Unknown Cache → Mystery/Unknown`. Add a parametrized test. |
| PRD-4 | Minor | Goal: "with errors reported per entry"; Scope: "Orphan waypoints are reported as warnings" | `CacheParseResult` is defined as "success or error". It has no place for warnings, so unknown types and orphan waypoints never reach the user, and IMP-6 only counts errors. A user whose waypoints were silently dropped cannot tell. | Add a warnings channel to the result type (for example `warnings: list[ParseIssue]`) so T-008 can show it. Add an AC: "An orphan waypoint yields a warning naming the waypoint code and the expected parent GC code." |
| PRD-5 | Minor | AC2: "A ZIP with caches and waypoints yields caches with linked waypoints" | IMP-3 also covers a separate `*-wpts.gpx`. Users often unzip PQs and pick both GPX files. The ticket does not say whether linking works across separate files in one `files` sequence. | Add an AC: "Given `x.gpx` and `x-wpts.gpx` passed as two separate files, then the waypoints are linked." |
| PRD-6 | Minor | Scope/In: "`PocketQuerySource(files: Sequence[Path \| BinaryIO])`" | Overlapping PQs are normal (many PQs by date or area). The ticket does not say what happens when the same GC code appears in two files. Duplicates would inflate the IMP-6 counts and make the result depend on file order. | State the rule. For example: "a duplicate GC code within one source yields one cache: the entry from the file with the latest GPX `<time>` wins; a warning is emitted." |
| PRD-7 | Nit | Header: "- **Related ADRs:** ADR-0003" | The header has no `Reviews:` line, and the ticket has no "Implementation notes" section, unlike `TEMPLATE.md`. | Add `- **Reviews:** –` and the section, so the ticket is consistent with the other tickets. |

**Strengths:**
- Keeping description HTML raw and byte-exact (AC6), and sanitizing at render time, preserves what the user sees as the cache owner wrote it. This is consistent with NFR-6.
- The per-entry error model (AC3/AC4) fits IMP-7: one bad cache does not cost the user the whole PQ.
- Synthetic fixtures cover the real-world variety: GPX 1.0/1.1, waypoint ZIPs, unicode, and missing fields.

**Open questions:**
- Do Pocket Queries write the user's corrected coordinates into `<wpt lat/lon>`? If they do, the import would store a solved location as the "original", which breaks CAC-5 ("The original coordinates are kept and still visible"). The parser may need to detect or flag this.
- What should a valid PQ with zero caches return? An empty result, or a file-level notice? The user should see "0 caches imported", not an error.
- How should ZIP entries that are not GPX files (for example a readme) be handled: ignore them silently or warn?

**Out of my lane:**
- Architect: adding a warnings channel to the `CacheParseResult` contract in `services/ports.py` affects T-008 and T-022.
- QDE: AC1 "identical domain objects for the same content" needs a defined equality basis, because the namespace or source metadata may differ.
- QDE: AC7 peak memory "under 200 MB" needs a stated measurement method so it is stable in CI.

## Appendix C: Quality & Delivery Engineer (raw)

**Member verdict:** Approve with changes
**Rationale:** The ticket has one clear goal and fits one PR, but several Scope behaviours have no AC, key result and mapping contracts are undefined, and the perf/memory AC cannot be measured as written, so an agent would have to guess.

| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Major | Scope/In: "found logs by the PQ owner" | The parser has no input that identifies the PQ owner. The constructor is `PocketQuerySource(files: …)`, and the home user/settings come later in T-009, which is not a dependency. As written, this cannot be implemented without guessing or pulling in an unlisted ticket. No AC covers found status either. | Restrict Phase 1 to `<sym>Geocache Found</sym>` → `found_by_me=True`. Mark the log-based variant Out, with a follow-up ticket. Add AC: "Given `gpx11_basic.gpx` with one cache whose `<sym>` is `Geocache Found`, when parsed, then that cache has `found_by_me=True` and the others have `False`." |
| QDE-2 | Major | Scope/In: "iter_caches() -> Iterator[CacheParseResult] (success or error with context)" | The result type is undefined, yet Scope needs a **warning** channel ("unknown values go to `Other`, with a warning", "Orphan waypoints are reported as warnings"). The ticket also does not say where the type lives, or which fields "context" has (file name, GC code, line). T-008 will consume this shape, so a guess here causes rework there. | Specify it, e.g. in `services/ports.py`: `CacheParseResult = ParsedCache(cache: Cache, warnings: list[ParseIssue]) \| ParseError(issue: ParseIssue)` with `ParseIssue(file: str, gc_code: str \| None, line: int \| None, message: str)`. Also say how file-level warnings (orphan waypoints) are emitted. |
| QDE-3 | Major | Acceptance criteria: AC1 "identical domain objects" is the only mapping AC | Scope promises the mapping of types/sizes, availability, archived state, attributes, hints, descriptions, logs, unknown→`Other` with a warning, orphan-waypoint warnings, and missing optional fields. None of these has an AC. AC1 also passes if both versions are mapped wrongly in the same way. `missing_optional_fields.gpx` is listed but not used by any AC. | Add a golden AC: "Given `gpx11_basic.gpx`, the parsed `Cache` for `GC0TEST1` equals an expected object in `tests/unit/adapters/expected_pq.py` (all spec §7 source fields incl. attributes, hint, logs)." Add: "An unknown `<groundspeak:type>` maps to `CacheType.OTHER` with one warning." Add: "An orphan waypoint in `with_waypoints.zip` yields one warning naming its code." Add: "`missing_optional_fields.gpx` parses successfully with optional fields `None`." |
| QDE-4 | Major | Scope/In: "maps types and sizes to domain enums" | No mapping table from PQ strings to the T-006 enums is given. Examples: "Unknown Cache" → Mystery/Unknown, "Not chosen", "Wherigo Cache", log types such as "Write note", and waypoint types such as "Parking Area". T-006 does not list `WaypointType`/`LogType` values or say whether they have an `Other` member. | Add an Implementation notes table: PQ string → enum member for CacheType, ContainerSize, WaypointType, and LogType. State that string matching is case-insensitive, and that unknowns map to an `OTHER` member (T-006 must provide one for every enum; check this against T-006). |
| QDE-5 | Major | AC7: "peak memory stays under 200 MB" | The measurement method is not defined. lxml allocates in C, so `tracemalloc` will not see most of it. RSS depends on the platform. It is also unclear whether `slow` tests run inside `mise run check` ("runs in CI"), and the 5 s limit can be flaky on shared CI runners. The generator for the "5,000-cache generated file" is not named. | Rewrite: "Given a 5,000-cache GPX generated at test time by `tests/fixtures/pq/generate.py::make_pq(n)` into `tmp_path`, when fully iterated, then wall time < 5 s and the `resource.getrusage(RUSAGE_SELF).ru_maxrss` increase < 200 MB. The test is marked `slow`, and `mise run check` includes `slow` tests." Also require clearing elements during iterparse (`elem.clear()`, delete earlier siblings). |
| QDE-6 | Major | Scope/In: "Links waypoints to their parent cache by prefix and code" | Two things are unclear. (a) Does linking work across separate `.gpx` inputs in the `Sequence`, or only inside one ZIP? (b) How does a streaming iterator yield a `Cache` with its waypoints when `-wpts.gpx` comes after, or before, the cache file? Both choices affect memory (AC7) and correctness. | State: "Waypoints are linked across all inputs given to one `PocketQuerySource`. Implementation: parse all `*-wpts.gpx` files first into a `dict[gc_code, list[CacheWaypoint]]`, then stream the caches." Add AC: "Given `with_waypoints.zip` with entries in either order, each cache has its waypoints." |
| QDE-7 | Major | AC3: "A corrupt entry yields an error result with GC code or line info" | "Corrupt" is undefined. A semantic error (bad lat, missing GC code) can be recovered. An XML well-formedness error stops `iterparse` unless recovery is used. "or" makes the assertion weak, and "parsing continues" is not counted. | Define it: "`one_corrupt_entry.gpx` has 3 caches. The second has `lat="abc"`. Iteration yields 2 `ParsedCache` and 1 `ParseError` with `gc_code="GC0TEST2"` and `line` set." Handle malformed XML in AC4 as a file-level error, or decide on `recover=True` explicitly. |
| QDE-8 | Minor | Scope/In: "files: Sequence[Path \| BinaryIO]" | For `BinaryIO` there is no file name, so detecting `.gpx` vs `.zip` is not specified. A corrupt ZIP, and a ZIP that contains non-GPX entries, have no defined result (IMP-7 "fail with a clear error"). | Specify "detect ZIP by magic bytes `PK\x03\x04`; otherwise treat as XML". Add fixture `corrupt.zip` and extend AC4: "a non-GPX file or a corrupt ZIP yields exactly one file-level `ParseError` and iteration ends normally." |
| QDE-9 | Minor | AC6: "preserved byte-exact" | Domain fields are decoded `str`, so a byte-level comparison is not defined. PQ descriptions are usually entity-escaped HTML. | Rewrite: "`long_description` equals the XML-unescaped source text exactly (string equality), including emoji and non-Latin characters in `unicode_html.gpx`. `description_is_html` reflects the `html` attribute." |
| QDE-10 | Minor | AC5: "An XXE payload is not resolved." | No observable assertion is given. | Rewrite: "Given `xxe_attempt.gpx` with an external entity that points to a sentinel file in `tmp_path` and an entity-expansion (billion-laughs) payload, the parsed output never contains the sentinel text, no socket is opened (pytest-socket), and parsing ends within 1 s with an error or empty fields." |
| QDE-11 | Minor | Scope/In: "Parse with **`lxml`**" | Under `mypy --strict`, lxml needs stubs (`lxml-stubs`/`types-lxml`) as a dev dependency. Without them the agent would add a `# type: ignore` or stop to ask (AGENTS §3). | Name the runtime dependency (`lxml`) and the dev dependency (`types-lxml` or `lxml-stubs`) explicitly. |
| QDE-12 | Minor | Test plan: "AC1–AC6 \| unit \| `tests/unit/adapters/test_pq_source.py`" | No test names are given (the template expects `tests/...::test_...`), and fixtures are not mapped to ACs. | Add one row per AC with the test name and fixture, e.g. `AC2 \| unit \| test_pq_source.py::test_zip_links_waypoints_to_parent (with_waypoints.zip)`. |
| QDE-13 | Minor | Header/DoD: "- **Related ADRs:** ADR-0003" then "## Goal" | The template is not fully followed. The `Reviews:` line and the `Implementation notes` section are missing (implementation detail sits in Scope), and the DoD leaves out "Docs are updated" (spec §9.4 item 3). | Add `- **Reviews:** –` and an Implementation notes section. Restore the template DoD item "Docs are updated (README / spec / AGENTS / ADR if needed)". |
| QDE-14 | Nit | Scope vs Test plan: "`backend/tests/fixtures/pq/`" vs "`tests/unit/adapters/…`" | The path roots are inconsistent. | Use `backend/tests/...` everywhere. |

**Strengths:**
- One clear goal with a crisp Out boundary ("Persisting data (T-008)"). The dependency on T-006 is correct and complete for the domain types.
- The fixture set is named, synthetic, and covers the spec §9.2 edge cases (GPX 1.0/1.1, unicode/HTML, waypoints, corrupt entry, XXE).
- Library and parsing strategy are fixed (`lxml` `iterparse`, entity resolution and network off), so the agent has no open choice there.

**Open questions:**
- Should the found-status-by-owner-log path exist at all in Phase 1, or is `<sym>Geocache Found</sym>` enough?
- Does `mise run check` (and CI) run `slow`-marked tests, or is there a separate CI step?
- Does T-006 guarantee an `OTHER` member in `WaypointType` and `LogType`?

**Out of my lane:**
- Architect: placing `CacheParseResult` in `services/ports.py` vs `domain/`, and a sync vs async iterator for a future API source (ADR-0003).
- Architect/Security: ZIP-bomb and path-traversal limits for ZIP input (max uncompressed size, max entries).
- Product Designer: how warnings (unknown types, orphan waypoints) are shown to the user in the T-008 import summary.
