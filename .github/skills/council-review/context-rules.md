# Context selection rules

Context is passed as **paths**. Members read the files themselves. The order matters: list the files in the order below.

## Base context (always)
1. `README.md`
2. `AGENTS.md`
3. `docs/specification.md`

## Target type: ADR (`docs/adr/NNNN-*.md`)
4. Every ADR in `docs/adr/` with a number **lower than the target's number** (excluding `0000-template.md`) whose status line `- **Status:**` starts with `Accepted`. List them in ascending order.
5. `docs/adr/0000-template.md` (so the members can check the structure).

Do **not** include higher-numbered ADRs, Proposed, Superseded, or Deprecated ADRs, or any tickets.

## Target type: Ticket (`docs/features/*/T-NNN-*.md`)
4. **Every** ADR in `docs/adr/` (excluding the template) whose status starts with `Accepted`, in ascending order.
5. Every ticket listed in the target's `- **Depends on:**` line. Resolve each `T-XXX` across `backlog/`, `active/`, and `complete/`. If one cannot be found, record the anomaly `Dependency T-XXX not found`. Do not search further.
6. `docs/features/TEMPLATE.md`
7. `docs/features/README.md` (ticket index and pick rule)

## Parsing notes
- Status line format: `- **Status:** <value>`. Treat a missing or unparseable status as **not Accepted**, and record it as an anomaly.
- The `Depends on` value may be `–`, `-`, or empty, which means none. IDs can appear with extra text such as `T-008 (**Blocked**)`. Extract every `T-\d{3}`.
- Never include `docs/drafts/` or anything under `docs/reviews/` (including `adr/` and `features/`). Previous reviews must not anchor the new one.
