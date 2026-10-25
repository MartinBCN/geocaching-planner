# Features / Tickets

The ticket workflow is defined in [ADR-0009](../adr/0009-ticket-workflow.md) and [AGENTS.md](../../AGENTS.md).

| Folder | Meaning |
|---|---|
| `backlog/` | Refined, ready (or `Blocked`/`Draft`) tickets |
| `active/` | The one ticket currently being worked on |
| `complete/` | Done, with completion notes |

- File name: `T-NNN-<slug>.md`, based on [TEMPLATE.md](TEMPLATE.md).
- Pick rule: continue the ticket in `active/` if one exists; otherwise pick the lowest-numbered backlog ticket with `Status: Ready` whose `Depends on` tickets are all in `complete/`. When work starts, move it to `active/` and set `Status: Active`.
- New ideas go to `docs/drafts/` (untracked) first. They become tickets only after they are refined into the template.
- Before `Draft → Ready`, a **council review** is recommended (`council-review` skill, ADR-0010). Link the report in the ticket's `Reviews:` line.

## Ticket index
| ID | Title | Milestone | Depends on |
|---|---|---|---|
| T-001 | Repository and tooling bootstrap | M0 | – |
| T-002 | Backend skeleton and quality gates | M0 | T-001 |
| T-003 | Compose stack, database, and migrations | M0 | T-002 |
| T-004 | Frontend skeleton and quality gates | M0 | T-002, T-003, T-023 |
| T-005 | Continuous integration | M0 | T-003, T-004 |
| T-006 | Cache domain model and schema | M1 | T-005 |
| T-007 | Pocket Query GPX/ZIP parser (`CacheSource`) | M1 | T-006 |
| T-008 | Import service, API, and UI | M1 | T-007, T-024 |
| T-009 | Settings (home location, defaults) | M1 | T-006 |
| T-010 | Cache query API (filters, bbox, paging) | M1 | T-009, T-024 |
| T-011 | Map view with cache markers | M1 | T-010 |
| T-012 | Cache list and filter panel | M1 | T-011 |
| T-013 | Cache details, notes, and corrected coordinates | M1 | T-012 |
| T-014 | Cache GPX export | M1 | T-013 |
| T-015 | BRouter routing adapter | M2 | T-005, T-023 |
| T-016 | Route domain and API | M2 | T-015, T-006 |
| T-017 | Route planning UI | M2 | T-016, T-011 |
| T-018 | Elevation profile and route stats | M2 | T-017 |
| T-019 | Caches along route (corridor) | M2 | T-017, T-012 |
| T-020 | Route GPX export | M2 | T-019, T-014 |
| T-021 | Automatic cache selection and ordering | Phase 2 | T-020 |
| T-022 | Geocaching.com API cache source | Phase 2 | T-008 (**Blocked**) |
| T-023 | BRouter Compose service and segments | M0 | T-003 |
| T-024 | Cache repository and persistence behavior | M1 | T-006 |
