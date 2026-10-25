# Council review: T-003-compose-db-migrations (review 1)

- **Target:** `docs/features/backlog/T-003-compose-db-migrations.md` (Ticket, status at review time: Ready)
- **Date:** 2026-10-25
- **Council verdict:** **Revise & resubmit**
- **Findings:** 1 Blocker · 7 Major · 9 Minor · 2 Nit
- **Member verdicts:** Architect: Approve with changes · Product Designer: Approve with changes · Quality & Delivery: Revise & resubmit

## Context provided
- README.md
- AGENTS.md
- docs/specification.md
- docs/adr/0001-record-architecture-decisions.md
- docs/adr/0002-local-single-user-deployment.md
- docs/adr/0003-gpx-first-pluggable-cache-source.md
- docs/adr/0004-brouter-routing.md
- docs/adr/0005-frontend-react-maplibre.md
- docs/adr/0006-postgis.md
- docs/adr/0007-tooling-uv-mise-monorepo.md
- docs/adr/0008-quality-gates.md
- docs/adr/0009-ticket-workflow.md
- docs/adr/0010-council-review.md
- docs/features/backlog/T-002-backend-skeleton.md
- docs/features/TEMPLATE.md
- docs/features/README.md

**Anomalies:** none

## Top actions
1. Make every AC automatically testable and put back the template DoD line "covered by automated tests": a compose smoke test for AC1, an optional `@pytest.mark.brouter` live test for AC2 (skipped without segments, with a written reason it is excluded from CI), and a docs test for AC6, or an explicit, justified exception (#1).
2. Specify the health check: a `DatabaseProbe` protocol in `services/`, implemented in `adapters/db/` with a ≤ 2 s timeout, an exact JSON body for up/down, and a note to update T-002's `test_health.py` (#3).
3. Define the baseline migration's downgrade contract for `postgis` (no-op vs. drop-if-created) and test `upgrade head` → `downgrade -1` → `downgrade base` → `upgrade head`, matching spec §9.3 (#2).
4. Make AC5 and AC7 verifiable: a test-only table with commit-safe savepoint rollback for AC5, and a pure `find_non_loopback_ports` function with fixture cases plus a named YAML dev dependency for AC7 (#6, #7).
5. Decide on scope and first-run UX: split off the BRouter service/segments work into its own ticket (or justify keeping it), fix the default tile coverage claim (`E0_N50` vs `E5_N50`), and define first-run failure messages and configurable host ports (#4, #5, #8).

## Consolidated findings
| # | Severity | Source IDs | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|---|
| 1 | Blocker | QDE-1 | Test plan: "AC1, AC2, AC6 \| manual (record in completion notes)"; DoD: "All ACs are covered" | Spec §9.4 and AGENTS.md §2 require every AC to have an automated test. Three ACs are manual-only, and the DoD drops the template's "by automated tests". Per AGENTS.md §1 an agent must stop on this conflict, so the ticket cannot be completed as written. (ARC and PRD flagged the same in "Out of my lane".) | Restore the template DoD line. AC1: automated compose smoke (`docker compose up -d --wait` within 180 s, `docker compose ps --format json` shows `db`/`brouter` healthy), run by T-005's compose job. AC2: `@pytest.mark.brouter`, skipped when `E5_N50.rd5` is missing, with a documented reason for CI exclusion. AC6: a docs test for the README "BRouter segments" heading, or an explicit justified exception. |
| 2 | Major | ARC-1 (Major), QDE-6 (Minor) | Scope/In: "The first migration runs `CREATE EXTENSION IF NOT EXISTS postgis`"; AC3: "`alembic upgrade head` followed by `alembic downgrade base` works on an empty DB" | The downgrade behaviour is undefined. The `postgis/postgis` image already creates `postgis` (and dependent extensions), so a plain `DROP EXTENSION` fails and `CASCADE` drops extensions the migration never created. "Works" is subjective, and spec §9.3 also requires `downgrade -1`. The pattern will be copied by later migrations. | State the contract: baseline downgrade is a documented no-op (extension belongs to the image) or drops `postgis` only if this revision created it. Rewrite AC3: given an empty PostGIS testcontainer, `upgrade head` sets `alembic_version` to head and `SELECT postgis_version()` succeeds; `downgrade -1` and `downgrade base` exit cleanly and leave `alembic_version` empty; a second `upgrade head` succeeds. |
| 3 | Major | ARC-2 (Major), QDE-3 (Major) | Scope/In: "Health endpoint: add `db: ok\|error`"; Test plan: "unit (fake session)"; AC4: "reports `db: ok` when the DB is up and `status: degraded, db: error` when it is down" | A fake session in an API unit test implies the router runs DB queries, breaking spec §6 ("`api/` only translates HTTP to service calls"); T-015 will copy the pattern. No timeout is set, so an unreachable DB can hang the endpoint. AC4 omits the HTTP status, exact JSON body, the `status` value when up, and how "down" is simulated; T-002's exact-body health assertion will break and the ticket doesn't say so. | Add `services/health.py: DatabaseProbe` (`async def ping() -> bool`), implemented in `adapters/db/` with `SELECT 1` and a ≤ 2 s timeout, injected via `Depends`; unit tests use a fake probe. Rewrite AC4: reachable → 200 `{"status":"ok","version":<v>,"db":"ok"}`; DB URL on a closed port → 200 `{"status":"degraded","version":<v>,"db":"error"}` within 3 s. Note the T-002 `test_health.py` update. |
| 4 | Major | PRD-1 | Scope/In: "The default set (`E5_N50.rd5`) covers NL/BE/W-DE" | BRouter tiles are 5°×5° named by the SW corner, so `E5_N50` covers 5–10°E, 50–55°N. Most of Belgium and the western Netherlands are in `E0_N50`. Users get routing failures in areas the docs claim are covered. | Either default to `E0_N50 E5_N50` (≈2× disk) or describe `E5_N50` accurately. Extend AC6: README explains tile naming with an example, what happens outside coverage, and how to add tiles with `BROUTER_SEGMENTS`. |
| 5 | Major | PRD-2 | AC1: "`mise run dev` brings up healthy `db` and `brouter` containers and a running backend." | First-run failure states are undefined: no segments yet, Docker not running, host port 5432/17777 already in use. With `--wait` these abort the one-command start (NFR-3) with raw Docker errors. It is not stated whether AC1 must work without segments. (ARC also noted the port conflict in "Out of my lane".) | Add an AC: without `.rd5` files `mise run dev` still starts and prints "No routing data found — run `mise run brouter:segments`"; if Docker is unreachable the task fails with a one-line actionable message. Make host ports configurable via `.env` (`DB_PORT`, `BROUTER_PORT`, still bound to `127.0.0.1`). |
| 6 | Major | QDE-2 | AC7: "An automated check rejects Compose host-published service ports that are not bound to `127.0.0.1`" | No file, test level, input method, or syntax rules. The agent must choose between parsing YAML (no parser listed) and `docker compose config` (needs Docker), and decide which forms (short/long syntax, `0.0.0.0`, `localhost`, `[::1]`) to cover, and whether it is part of `mise run check`. (ARC raised the same question in open questions.) | Specify `backend/tests/unit/test_compose_ports.py` with a pure `find_non_loopback_ports(compose: dict) -> list[str]`, fed by fixture dicts and the real `compose.yaml`; name the YAML parser as a dev dependency. Rewrite AC7 to cover short and long syntax, missing host IP, `0.0.0.0`, `localhost`, `expose`-only services, and zero violations for the real file. |
| 7 | Major | QDE-4 | AC5: "leave no state between tests"; Scope: "per-test transaction rollback (or truncate) session" | Not verifiable: there are no tables yet, the rollback/truncate choice has no criteria, and code that calls `commit()` escapes a plain outer rollback. (ARC also noted that AC3's `downgrade base` on the shared session container can break this isolation.) | Rewrite AC5 with a test-only table created by the session fixture: test A inserts and commits, test B sees it empty. Prefer rollback with `join_transaction_mode="create_savepoint"`; allow truncate only with a reason in completion notes. Run the AC3 migration roundtrip on its own database/container. |
| 8 | Major | QDE-5 | Scope/In: compose `db` + `brouter` (custom Dockerfile), segment downloader, profiles, deps, `adapters/db/`, Alembic, mise tasks, health, fixtures, AC7 checker | Two separate goals in one PR (DB/migrations/test infra and BRouter container/data tooling), against ADR-0009's "small enough for one PR". | Split: T-003 keeps compose `db`, `adapters/db`, Alembic, health, fixtures, AC1 (db), AC3–AC5, AC7. A new ticket "BRouter compose service and segments" (depends on T-003; T-015 depends on it) takes `brouter`, `brouter:segments`, profiles, AC2, AC6. Record that ADR-0004's "delivered in T-003" now spans two tickets. |
| 9 | Minor | ARC-3 | Scope/In: "Backend deps: `sqlalchemy[asyncio]`, `asyncpg`, `geoalchemy2`, `alembic`"; spec §11: "All dependencies are verified in T-002" | These deps are added here, not in T-002; asyncpg has C extensions and may fail on Python 3.14. No "verify and stop" rule. | Copy T-002's rule: verify each new dependency on Python 3.14; if one fails, document and stop (spec §11). |
| 10 | Minor | ARC-4 | Spec §9.1: "mypy --strict (with pydantic and sqlalchemy plugins)"; ADR-0006: "Requires GeoAlchemy2 typing workarounds under mypy strict (local stubs allowed)" | The deprecated SQLAlchemy mypy plugin conflicts with 2.0-style `Mapped[]` and recent mypy; following the spec literally forces a stop (AGENTS §1). | State: do not enable the sqlalchemy mypy plugin; record the deviation from §9.1 and update the spec. Allow local GeoAlchemy2 stubs under e.g. `backend/typings/`. |
| 11 | Minor | ARC-5 | Scope/In: "`postgis/postgis:17-3.5` (pin)" vs "an image that runs the BRouter server (build … using the official BRouter release JAR…)" | BRouter version, JAR checksum, and the testcontainer image tag are not pinned; compose, tests, and CI can drift (ADR-0007). Overlaps with #15 on the shared image tag. | Pin the BRouter release and SHA-256 as Dockerfile build args. Keep the PostGIS tag in one shared place used by `compose.yaml` and `tests/integration/conftest.py`. |
| 12 | Minor | ARC-6, QDE-9 | DoD: "README and `.env.example` are updated"; Scope lists no setting names | No env/setting names are given (DB URL, BRouter URL, compose credentials/ports), so Alembic `env.py` may read a different URL than the app; hard-coded credentials blur NFR-4. | Name them: `GCP_DATABASE_URL` / `Settings.database_url`, `GCP_BROUTER_URL`, compose `POSTGRES_*` / `DB_PORT` from `.env` with dev-only defaults. `migrations/env.py` **must** read `Settings`, not `alembic.ini`. |
| 13 | Minor | PRD-3 | Scope/In: "It skips files that already exist." | An interrupted download leaves a partial `.rd5` that is then skipped forever, causing silent routing failures; no progress feedback on 100–500 MB downloads. | Download to a temp file and rename on success; show per-file progress and a final summary (downloaded/skipped/failed). |
| 14 | Minor | PRD-4 | Scope/In: "`db`: … with a named volume" | The volume will hold the user's personal data (imports, notes, corrected coordinates); nothing warns that `docker compose down -v` deletes it. | Add one README sentence: where data lives, that `down -v` deletes it, and that normal stop/start keeps it. |
| 15 | Minor | QDE-7 | Scope: "Integration tests run against a throwaway PostGIS container"; T-002: "`--disable-socket --allow-unix-socket` by default" | Per-test socket opt-in is fragile with a session fixture; it is unclear whether `mise run check` runs integration tests (affects the 85% coverage gate); testcontainer tag not tied to the compose pin (see #11). | Auto-apply `integration` and `enable_socket` markers in `tests/integration/conftest.py`. State that `mise run check` runs integration tests (Docker required) and counts them for coverage. Use one `POSTGIS_IMAGE` constant. |
| 16 | Minor | QDE-8 | Scope: "It skips files that already exist"; "can be overridden with `BROUTER_SEGMENTS=…`"; "`mise run db:revision`" | In-scope behaviours have no AC or test; "`.sh` or Python" leaves the language open, and shell falls outside ruff/mypy. | Require Python (`infra/brouter/download_segments.py` or an importable module). Add an AC for skip-existing and `BROUTER_SEGMENTS` override, tested with respx and no network. |
| 17 | Minor | QDE-10 | Header/sections: no `Reviews:` line, no `## Context`, no `## Implementation notes` | Does not follow `docs/features/TEMPLATE.md`; gotchas have nowhere to go, yet status is already Ready. (ARC and PRD noted the same in "Out of my lane".) | Add the missing sections; move file paths and library choices into Implementation notes, marked **must** where binding. |
| 18 | Nit | PRD-5 | Goal: "`mise run dev` starts PostGIS and BRouter in Docker." | NFR-3 includes the frontend; the deferral is only in a parenthetical in Scope. | Add "(frontend is added in T-004; NFR-3 is completed there)" to the Goal. |
| 19 | Nit | QDE-11 | AC2: "returns a route" | Not observable. | "Returns HTTP 200 with a GeoJSON `FeatureCollection` whose first feature is a `LineString` with ≥ 2 coordinates including elevation." |

No severities were raised by the Chair.

## Dissent
| Topic | Position A | Position B |
|---|---|---|
| Severity of the baseline downgrade issue (#2) | ARC-1: Major — AC3 can fail on the pinned image or be "fixed" dangerously with `CASCADE`, and the pattern is copied by every later migration. | QDE-6: Minor — mainly a wording/measurability issue; asks only to state whether downgrade drops the extension. Merged at Major. |
| Ticket scope (#8) | ARC (Strengths): "Scope stays tight: no domain tables until T-006, and no BRouter adapter until T-015." | QDE-5: Major — DB and BRouter work are two goals in one PR and should be split per ADR-0009. |
| Health test with a fake session (#3) | QDE (Strengths): the test plan's "unit with a fake session plus integration for health" levels are sensible. | ARC-2: a fake session implies DB I/O in `api/`, violating spec §6; use a fake probe instead. |
| Overall member verdict | ARC, PRD: Approve with changes (no Blockers found). | QDE: Revise & resubmit, because manual-only ACs conflict with spec §9.4 and AGENTS.md (QDE-1 Blocker). ARC and PRD noted the manual ACs only as out-of-lane remarks. |

## Open questions for the author
- Will the AC7 check parse `compose.yaml` with a YAML library (named dev dependency) or use `docker compose config --format json`? (ARC; see #6)
- If no maintained BRouter image exists, can the implementer decide alone to build one, or should ADR-0004's follow-ups record it? (ARC; QDE out-of-lane also suggests an ADR note for the custom Dockerfile)
- Which region should the default segments target: the owner's riding area, or NL/BE/W-DE as written? (PRD; see #4)
- Should users be able to back up/restore personal data (notes, corrected coordinates)? If so, as a future ticket. (PRD)
- Does `mise run check` need Docker (integration tests in the gate), or are integration tests a separate task? (QDE; see #15)
- Should the first migration's downgrade drop the `postgis` extension? (QDE, ARC; see #2)
- Will you accept splitting off the BRouter work, given ADR-0004 names T-003 as the delivery ticket? (QDE; see #8)
- Is `BROUTER_SEGMENTS` intentionally without the `GCP_` prefix (NFR-4/T-002)? (PRD out-of-lane)
- Does copying standard `.brf` profiles into the repo have licensing/attribution implications? (QDE out-of-lane)

## Strengths
- Compose ports bound to loopback, and AC7 turns ADR-0002's "automated checks must verify this boundary" into an AC, including the negative case (ARC, QDE).
- DB access lives in `adapters/db/`, with a constraint naming convention on the declarative `Base` from the start (ARC).
- Integration tests use a throwaway testcontainer, so tests never touch the user's real data (PRD).
- Local routing with `trekking`/`fastbike`/`safety` profiles supports the offline bike-planning promise (NFR-2, RTE-3) (PRD).
- Health reports `degraded` instead of failing hard, giving later UI a clear signal (PRD).
- Image tag, ports, segment URL, default tile, and env override are pinned concretely; test files named for AC3–AC5 (QDE).

## Process notes
- All three custom agent types (`council-architect`, `council-product-designer`, `council-quality-delivery`) were available; no fallback used.
- All member outputs met the contract; no re-prompts were needed.
- Partial overlaps kept as separate findings with cross-references: #11 and #15 (shared PostGIS image tag); #13 and #16 (segment downloader, different issues).

---

## Appendix A: Software Architect (raw)
## Software Architect review: T-003-compose-db-migrations.md

**Member verdict:** Approve with changes
**Rationale:** The ticket matches ADR-0002, ADR-0004 and ADR-0006, but the downgrade behaviour of the first migration and the health-check layering are unclear and likely to cause rework in a ticket that sets patterns for later work.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| ARC-1 | Major | Scope/In: "The first migration runs `CREATE EXTENSION IF NOT EXISTS postgis`"; AC3: "`alembic upgrade head` followed by `alembic downgrade base` works on an empty DB" | The ticket does not say what the downgrade does. The `postgis/postgis` image already creates `postgis` (plus `postgis_topology` and `postgis_tiger_geocoder`, which depend on it) in the default database at init. So the migration often does not own the extension. A plain `DROP EXTENSION postgis` downgrade then fails because other extensions depend on it, and adding `CASCADE` would drop extensions the migration never created. AC3 can then fail on the very image the ticket pins, or someone "fixes" it in a dangerous way. Spec §9.3 also asks for "`downgrade -1` must work", and this test will be copied for every later migration. | State the downgrade contract explicitly. For example: "The downgrade of the baseline revision is a documented no-op; the extension belongs to the database image." Or: "The downgrade drops `postgis` only if this revision created it." Add `downgrade -1` from head to the roundtrip test so it matches spec §9.3. |
| ARC-2 | Major | Scope/In: "Health endpoint: add `db: ok\|error`"; Test plan: "unit (fake session)" | A "fake session" in an API unit test means the router itself would run a query on a SQLAlchemy session. That puts I/O in `api/`, which breaks spec §6: "`api/` only translates HTTP to service calls." T-015 will then copy the pattern for BRouter status. The ticket also does not cap how long the check waits when the DB is down, so a hanging connect makes the health endpoint hang too. | Add a protocol such as `services/health.py: DatabaseProbe` (`async def ping() -> bool`). Implement it in `adapters/db/` (`SELECT 1` with a short timeout, e.g. 2 s). Inject it with `Depends` and have the unit test use a fake probe instead of a fake session. T-015 then adds a `RoutingProvider`/BRouter probe the same way. |
| ARC-3 | Minor | Scope/In: "Backend deps: `sqlalchemy[asyncio]`, `asyncpg`, `geoalchemy2`, `alembic`"; spec §11: "All dependencies are verified in T-002" | These dependencies are added here, not in T-002. asyncpg has compiled C extensions, so it is the most likely to fail on Python 3.14. The spec's risk mitigation does not cover them, and this ticket has no "verify on 3.14 and stop" rule. | Copy T-002's rule: "Verify that every new dependency installs and works on Python 3.14; if one does not, document it and stop (spec §11)." |
| ARC-4 | Minor | Spec §9.1: "mypy --strict (with pydantic and sqlalchemy plugins)"; ADR-0006: "Requires GeoAlchemy2 typing workarounds under mypy strict (local stubs allowed)" | This is the ticket that brings in SQLAlchemy and GeoAlchemy2, but it says nothing about mypy setup. The SQLAlchemy mypy plugin is deprecated for 2.0-style `Mapped[]` code and does not work with recent mypy versions. An agent following the spec literally will hit this conflict and has to stop (AGENTS §1). | Say what to do. For example: "Do not enable the deprecated sqlalchemy mypy plugin; typed `Mapped[]` is sufficient. Record the deviation from §9.1 and update the spec." Also allow local GeoAlchemy2 stubs under a named path such as `backend/typings/`. |
| ARC-5 | Minor | Scope/In: "`postgis/postgis:17-3.5` (pin)" vs "an image that runs the BRouter server (build … using the official BRouter release JAR…)" | Only PostGIS is pinned. The BRouter version (and a checksum for the JAR download), and the image tag used by the testcontainer, are not pinned. Compose, tests and CI (T-005) can drift apart, which goes against ADR-0007's "exact, concrete versions" approach. | Pin the BRouter release version and its SHA-256 in the Dockerfile as a build arg. Keep the PostGIS image tag in one shared place (e.g. a constant or env default) used by both `compose.yaml` and `tests/integration/conftest.py`. |
| ARC-6 | Minor | DoD: "README and `.env.example` are updated"; Scope/In: "port bound to `127.0.0.1:5432`" | NFR-4 requires all configuration to come from environment variables, but the ticket names none: no DB URL, no BRouter base URL, no Compose credentials or host ports. Alembic's `env.py` might then read a different URL from `alembic.ini` than the app does. Hard-coded Postgres credentials in `compose.yaml` also blur the NFR-4 "no secrets in the repo" rule. | List the settings, e.g. `GCP_DATABASE_URL` and `GCP_BROUTER_URL` in `Settings`, and Compose `POSTGRES_*` / `DB_PORT` read from `.env` with dev-only defaults. Require `migrations/env.py` to read the URL from `Settings`, not from `alembic.ini`. |

### Strengths
- Compose ports are bound to loopback, and AC7 adds the automated check that ADR-0002 requires, including the "unpublished service" case.
- DB access lives in `adapters/db/`, and the declarative `Base` uses a constraint naming convention from the start. That keeps later Alembic autogenerate and downgrades stable.
- Scope stays tight: no domain tables until T-006, and no BRouter adapter until T-015, which matches the hand-offs in ADR-0004 and ADR-0006.

### Open questions for the author
- Will the AC7 check parse `compose.yaml` with a YAML library (a new dev dependency that AGENTS §3 requires the ticket to name), or use `docker compose config --format json`?
- If no maintained BRouter image exists, is building it ourselves a choice the implementer can make alone, or should a short note in ADR-0004's follow-ups record which way was taken?

### Out of my lane
- QDE: AC3's `downgrade base` running against the session-scoped container used by all integration tests can break the isolation AC5 asks for. It probably needs its own database or container.
- QDE: AC1, AC2 and AC6 are manual-only, but AGENTS §2.3 and spec §9.2 say every AC needs an automated test.
- QDE: the ticket has no `Context`, `Implementation notes` or `Reviews:` line from the template, and it is already `Ready` without a linked review.
- PRD: a user who already runs a local Postgres on host port 5432 will get a port conflict. The README should explain how to change the port.

## Appendix B: Product Designer (raw)
## Product Designer review: T-003-compose-db-migrations.md

**Member verdict:** Approve with changes
**Rationale:** This ticket delivers the "one command, works offline" setup the user expects. But the default routing data does not cover the region it claims to cover, and first-run failures of `mise run dev` have no defined messages.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| PRD-1 | Major | Scope/In: "The default set (`E5_N50.rd5`) covers NL/BE/W-DE" | BRouter tiles are 5°×5° and named by their south-west corner, so `E5_N50` covers 5–10°E, 50–55°N. Most of Belgium and the western Netherlands (Amsterdam ≈4.9°E, Rotterdam, The Hague, Zeeland) are in `E0_N50`. A cyclist planning a ride there gets routing failures (ADR-0004: "errors for points outside segment coverage") even though the docs promise coverage. | Either make the default `E0_N50 E5_N50` and say it covers NL/BE/W-DE (about 2× the disk space), or keep `E5_N50` and describe it accurately (e.g. "eastern NL, W-DE"). Extend AC6: "README explains how to work out the tiles for a trip area (5°×5° naming by SW corner, with an example), what happens when a route leaves the covered area, and how to add tiles with `BROUTER_SEGMENTS`." |
| PRD-2 | Major | AC1: "`mise run dev` brings up healthy `db` and `brouter` containers and a running backend." | The ticket does not define the first-run error states: segments not downloaded yet, Docker not running, or port 5432/17777 already in use (common for anyone with a local Postgres). With `--wait`, any of these can abort the one-command start (NFR-3) with a raw Docker error, and the user doesn't know what to do next. AC2's "With segments downloaded" suggests AC1 should also work without segments, but this isn't stated. | Add an AC: "If no `.rd5` files are present, `mise run dev` still starts (BRouter healthy without segments) and prints: 'No routing data found — run `mise run brouter:segments`'. If Docker is not reachable, the task fails with a one-line actionable message." Make the host ports configurable through `.env` (e.g. `DB_PORT`, `BROUTER_PORT`, still bound to `127.0.0.1`). |
| PRD-3 | Minor | Scope/In: "It skips files that already exist." | An interrupted download (large files, 100–500 MB each) leaves a partial `.rd5`. The next run skips it as "existing", and routing then fails silently or strangely in that region with no hint why. The user also gets no progress feedback during a long download. | Download to a temp file and rename it on success. Show per-file progress and size, and print a summary at the end (downloaded, skipped, failed). |
| PRD-4 | Minor | Scope/In: "`db`: … with a named volume" | The named volume will hold the user's PQ imports, notes, and corrected coordinates (GSAK-style personal data, CAC-4/CAC-5). Nothing warns that `docker compose down -v` or removing the volume deletes all of it. | Add one sentence to the README section (AC6 or the DoD README update): where the data lives, that `down -v` deletes it, and that `mise run dev` and stopping the stack keep it. |
| PRD-5 | Nit | Goal: "`mise run dev` starts PostGIS and BRouter in Docker." | NFR-3 includes the frontend. The deferral is mentioned only in parentheses in Scope ("frontend is added in T-004"). | Add "(frontend is added in T-004; NFR-3 is completed there)" to the Goal so the partial delivery of NFR-3 is clear. |

### Strengths
- Routing is local, and profiles (`trekking`, `fastbike`, `safety`) match RTE-3. This directly supports the offline bike-planning promise (NFR-2).
- Integration tests use a throwaway testcontainer, so tests can never touch the user's real cache database.
- The health check reports `degraded` instead of failing hard, which gives later UI tickets a clear signal for an actionable "database unavailable" state.

### Open questions for the author
- Which region should the default target: the owner's actual riding area, or "NL/BE/W-DE" as written? This decides between PRD-1's two options and their disk-space cost.
- Should the user be able to back up and restore their personal data (notes, corrected coordinates), as GSAK users are used to? If so, it belongs in a future ticket, not here.

### Out of my lane
- QDE: AC1, AC2 and AC6 are manual only, while AGENTS.md says "Every acceptance criterion needs at least one automated test". The ticket is also missing the template's `Reviews:`, Context, and Implementation notes sections, yet it is already `Status: Ready`.
- ARC: `BROUTER_SEGMENTS` doesn't use the `GCP_` prefix (NFR-4/T-002). Check whether that's intended for non-backend settings.
- ARC: AC3 tests `downgrade base`, but spec §9.3 requires `upgrade head` plus `downgrade -1`. Confirm both are covered.
- Nit (docs): `docs/features/README.md` repeats the "Before `Draft → Ready`" bullet.

## Appendix C: Quality & Delivery Engineer (raw)
## Quality & Delivery Engineer review: T-003-compose-db-migrations.md

**Member verdict:** Revise & resubmit
**Rationale:** The DB work is mostly concrete, but three ACs are manual-only and the DoD drops the "automated tests" rule, so the ticket conflicts with the spec and AGENTS.md; AC4, AC5 and AC7 also leave key behaviour for the agent to guess.

### Findings
| ID | Severity | Location & evidence | Issue | Recommendation |
|---|---|---|---|---|
| QDE-1 | Blocker | Test plan: "AC1, AC2, AC6 \| manual (record in completion notes)"; DoD: "All ACs are covered" | Spec §9.4 says ACs must be "covered by automated tests", and AGENTS.md §2 says "Every acceptance criterion needs at least one automated test." The ticket plans three ACs as manual-only and drops "by automated tests" from the DoD (TEMPLATE has it). AGENTS.md §1 says to "stop and report the conflict", so an agent cannot finish this ticket as written. Only AC2 has a partial reason ("live BRouter test is added in T-015"). | Put the template DoD line back. Then pick one fix per AC: **AC1:** rewrite it as "Given Docker is running, when `docker compose up -d --wait` exits 0 within 180 s, then `docker compose ps --format json` reports `db` and `brouter` as `healthy`", and test it with an automated compose smoke (a `@pytest.mark.compose` test or a `mise run test:compose` task) that T-005's compose job runs. **AC2:** mark it `@pytest.mark.brouter` (the spec already defines this optional live marker), skip it when `infra/brouter/segments/E5_N50.rd5` is missing, and write down why it is excluded from CI (segments are a large network download). **AC6:** add a docs test that checks the README has a heading "BRouter segments" that mentions `mise run brouter:segments` and a disk-size figure, or give an explicit reason for keeping it manual. |
| QDE-2 | Major | AC7: "An automated check rejects Compose host-published service ports that are not bound to `127.0.0.1`"; Test plan: "automated configuration test \| Check the Compose port bindings…" | The test plan names no file, no level from §9.2, no input method, and no rules for each syntax. The agent must decide: parse YAML (PyYAML is not listed as a dependency) or run `docker compose config` (needs Docker in a unit test)? Cover short syntax (`"5432:5432"`, `"127.0.0.1:5432:5432"`), long syntax (`host_ip`), `0.0.0.0`, `localhost`, `[::1]`? Is it part of `mise run check`? | Specify `backend/tests/unit/test_compose_ports.py` with a pure function `find_non_loopback_ports(compose: dict) -> list[str]`, fed by fixture dicts and by the real `compose.yaml`. Name the YAML parser as a dev dependency. AC7 rewrite: "Given a compose mapping, when a published port has a host IP other than `127.0.0.1` (including none, `0.0.0.0` and `localhost`) in short or long syntax, then it is reported; services with no `ports` and `expose`-only services pass; the real `compose.yaml` yields no violations." |
| QDE-3 | Major | AC4: "reports `db: ok` when the DB is up and `status: degraded, db: error` when it is down"; Scope: "still HTTP 200" | AC4 does not give the HTTP status, the exact JSON shape, the `status` value when the DB is up, how "down" is simulated, or a time limit. Without a timeout, an unreachable DB can block the request for asyncpg's default connect timeout. T-002 AC1's exact-body assertion (`{"status":"ok","version":…}`) will also break, and the ticket does not say so. | Rewrite AC4: "Given the DB is reachable, `GET /api/v1/health` returns 200 `{"status":"ok","version":<v>,"db":"ok"}`. Given the DB URL points to a closed port, it returns 200 `{"status":"degraded","version":<v>,"db":"error"}` within 3 s (the DB check uses a ≤ 2 s timeout)." Add a note to update T-002's `test_health.py` assertion. |
| QDE-4 | Major | AC5: "leave no state between tests"; Scope: "per-test transaction rollback (or truncate) session"; Out: "Domain tables (T-006)" | "Leave no state" cannot be checked as written. There are no tables yet, so the agent must invent something to write. The rollback/truncate choice has no selection criteria, and code that calls `commit()` will escape a plain outer-transaction rollback. | Rewrite AC5: "Given test A inserts a row into a test-only table (created by the session fixture, not by a migration) and commits, when test B in the same module runs afterwards, then the table is empty." Say that rollback is preferred, using `join_transaction_mode="create_savepoint"` so commits inside code under test are undone too. Truncate is allowed only if that fails, and the reason goes in the completion notes. |
| QDE-5 | Major | Scope In: compose `db` + `brouter` (custom Dockerfile), segment downloader, profiles, deps, `adapters/db/`, Alembic, 3 mise tasks, health, fixtures, AC7 checker | This is two separate goals in one PR: (a) DB, migrations and test infrastructure, and (b) the BRouter container and data tooling. ADR-0009 says "Tickets must be small enough for one PR." The BRouter half adds a Dockerfile, a network downloader and licensing/profile decisions that have nothing to do with the DB tests. | Split it. T-003 keeps compose `db`, `adapters/db`, Alembic, health, fixtures, AC1 (db part), AC3–AC5 and AC7. A new ticket "BRouter compose service and segments" (depends on T-003, and T-015 depends on it) takes `brouter`, `brouter:segments`, profiles, AC2 and AC6. Note in the completion notes that ADR-0004's "delivered in T-003" now covers two tickets. |
| QDE-6 | Minor | AC3: "`alembic upgrade head` followed by `alembic downgrade base` works on an empty DB" | "Works" is subjective. It is also unclear whether the first migration's downgrade drops `postgis`; the `postgis/postgis` image may already have it installed. Spec §9.3 also requires `downgrade -1`. | Rewrite: "Given an empty PostGIS testcontainer, when `upgrade head` runs, then `alembic_version` equals the head revision and `SELECT postgis_version()` succeeds; when `downgrade -1` and then `downgrade base` run, then both exit without error and `alembic_version` is empty; a second `upgrade head` succeeds." State whether downgrade runs `DROP EXTENSION`. |
| QDE-7 | Minor | Scope: "Integration tests run against a throwaway PostGIS container"; T-002: "`--disable-socket --allow-unix-socket` by default (integration/contract tests opt in with `@pytest.mark.enable_socket`)" | Three gaps: (1) A session-scoped fixture opens TCP to the container, so per-test opt-in is fragile. (2) The ticket does not say whether `mise run check`/`test:backend` runs integration tests. If they are excluded, the `adapters/db` code may not count toward the 85% coverage gate. (3) The testcontainer image tag is not tied to the compose pin. | Require `tests/integration/conftest.py` to auto-apply the `integration` and `enable_socket` markers. State that `mise run check` runs integration tests (Docker required) and counts them for coverage. Use one constant `POSTGIS_IMAGE = "postgis/postgis:17-3.5"` for both. |
| QDE-8 | Minor | Scope: "It skips files that already exist"; "can be overridden with `BROUTER_SEGMENTS=…`"; "`mise run db:revision`" | These behaviours are in scope but have no AC or test. "`.sh` or Python" leaves the language open, and a shell script falls outside the ruff/mypy gates. | Make Python **must** (`infra/brouter/download_segments.py`, or a module the backend tests can import). Add an AC: "Given `E5_N50.rd5` exists, when the task runs, then no HTTP request is made for it; given `BROUTER_SEGMENTS="E5_N50 E0_N50"`, then exactly those two URLs are requested." Test it with respx and no network. |
| QDE-9 | Minor | DoD: "README and `.env.example` are updated"; Scope lists no setting names | The agent must invent the DB settings name (e.g. `GCP_DATABASE_URL`), the compose credentials (`POSTGRES_USER`/`PASSWORD`/`DB`), and how Alembic `env.py` reads them. Alembic and the app could drift apart. | Name them: `Settings.database_url` (`GCP_DATABASE_URL`, default `******127.0.0.1:5432/gcp`), and Alembic `env.py` **must** read `Settings`. |
| QDE-10 | Minor | Header/sections: no `Reviews:` line, no `## Context`, no `## Implementation notes` | Does not follow `docs/features/TEMPLATE.md`. Gotchas (pytest-socket, the T-002 health test change, image pin reuse) have nowhere to go. | Add the missing sections and move the file paths and library choices into Implementation notes, marked **must** where they bind. |
| QDE-11 | Nit | AC2: "returns a route" | Not observable. | Change to "returns HTTP 200 with a GeoJSON `FeatureCollection` whose first feature is a `LineString` with ≥ 2 coordinates that include elevation." |

### Strengths
- The test plan names concrete test files for AC3–AC5, with sensible levels (unit with a fake session plus integration for health).
- Image tag, ports, segment URL, default tile and the env override are pinned exactly, which leaves little room for guessing.
- AC7 turns the ADR-0002 rule ("Automated checks must verify this boundary") into an AC, including the negative case.

### Open questions for the author
- Does `mise run check` need Docker (integration tests in the gate), or are integration tests a separate task? This decides whether the coverage gate can be met.
- Should the first migration's downgrade drop the `postgis` extension?
- Will you accept splitting off the BRouter work, given ADR-0004 names T-003 as the delivery ticket?

### Out of my lane
- Architect: decide whether the DB health check in `api/` should go through a protocol/service rather than using the session directly, to keep the layering rules.
- Architect: the custom BRouter Dockerfile (building from the release JAR) is long-term maintenance; consider whether it needs an ADR note.
- Product Designer: the default segment set (NL/BE/W-DE) and the README's disk-usage guidance shape the first-run experience.
- Product Designer/Architect: copying standard `.brf` profiles into the repo may have licensing or attribution implications.
