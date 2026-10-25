# AGENTS.md — Rules for coding agents

Read this file completely before you change anything.

## 1. Sources of truth (in priority order)
1. `docs/adr/` — accepted architecture decisions
2. `docs/specification.md` — requirements (IDs such as `IMP-4`), architecture, standards, Definition of Done
3. The active ticket in `docs/features/active/`
4. `AGENTS.md` (this file) and `README.md`

`docs/reviews/` contains advisory council reports. They are input, not a source of truth.

If the sources conflict, **stop and report the conflict**. Do not pick one yourself.
`docs/drafts/` is untracked scratch space. **Never** implement anything from it.

## 2. Workflow per ticket
1. **Pick:** choose the lowest-numbered ticket in `docs/features/backlog/` where:
   - `Status` is `Ready` (not `Draft` or `Blocked`), and
   - every ticket under `Depends on` is in `docs/features/complete/`.
   If `docs/features/active/` already contains a ticket, continue that one instead.
2. **Start:** `git mv` the ticket to `docs/features/active/`, set `Status: Active`, and create branch `t-<id>-<slug>`.
3. **Implement:** keep to the ticket's scope. Write tests first or alongside the code. Every acceptance criterion needs at least one automated test.
4. **Verify:** run `mise run check` until it is green.
5. **Finish:** fill in the ticket's *Completion notes*, set `Status: Complete`, `git mv` it to `docs/features/complete/`, update the docs, and commit (Conventional Commits, e.g. `feat(import): parse PQ zip [T-007]`).
6. **One ticket at a time.** Do not start the next one in the same branch.

## 3. When to stop and ask
- An architectural change (see ADR-0001): write an ADR with status `Proposed` in `docs/adr/` and stop.
- The ticket is ambiguous or contradicts the spec.
- A new runtime dependency is not mentioned in the ticket or the ADRs.
- You would need to lower a quality gate or disable a lint rule globally.

Found something out of scope? Add a new ticket to `backlog/` (from the template, next free number, `Status: Draft`). Do not fix it in the current ticket.

## 3a. Council review (advisory, ADR-0010)
- Recommended before an ADR moves `Proposed → Accepted` and before a ticket moves `Draft → Ready`.
- Run it with the `council-review` skill (e.g. "run the council on T-007"). The report is written to `docs/reviews/adr/<stem>-review-<n>.md` (ADRs) or `docs/reviews/features/<stem>-review-<n>.md` (tickets).
- Add the report link to the target's `- **Reviews:**` line. **Never** apply findings automatically. The owner decides.
- When you write a new Proposed ADR or Draft ticket, you may run the council and mention the verdict when you stop.

## 4. Commands (all through mise)
| Task | Command |
|---|---|
| Install everything | `mise install && mise run setup` |
| Start the dev stack (compose + backend + frontend) | `mise run dev` |
| All quality gates (same as CI) | `mise run check` |
| Lint / format | `mise run lint` / `mise run fmt` |
| Backend tests | `mise run test:backend` |
| Frontend tests | `mise run test:frontend` |
| E2E smoke | `mise run test:e2e` |
| New migration | `mise run db:revision -- -m "message"` |
| Apply migrations | `mise run db:migrate` |
| Regenerate the API client | `mise run api:gen` |
| Download BRouter segments | `mise run brouter:segments` |

(These tasks are created in T-001 to T-005. Until then, follow the ticket instructions.)

## 5. Code rules (summary; full text in spec §9)
- Python 3.14, fully typed, `mypy --strict` clean, and ruff clean. No bare `# type: ignore` or `# noqa`. Always give the code and a reason.
- Layering: `domain/` is pure; `services/` depends on protocols; `api/` contains no business logic; `adapters/` handle I/O.
- SQLAlchemy 2.0 async with typed `Mapped[]`. Every schema change ships an Alembic migration that can be downgraded.
- Use the **effective location** (corrected coordinates first) for every spatial feature.
- An import must never overwrite `UserCacheData`.
- Frontend: strict TS, Biome clean, server state only through TanStack Query and the generated API client. Feature-folder structure.
- Sanitize cache HTML before rendering it.
- No real geocaching.com data, secrets, or BRouter segment files in git.
- Coverage gates: backend ≥ 85%, frontend ≥ 80%.

## 6. Definition of Done
See `docs/specification.md` §9.4. A ticket is not complete until `mise run check` is green and the ticket file is in `docs/features/complete/` with its completion notes filled in.
