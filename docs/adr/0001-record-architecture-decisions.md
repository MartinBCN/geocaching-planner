# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-10-25

## Context
Coding agents and humans both work on this project. Decisions must be explicit and discoverable, or agents will make conflicting choices.

## Decision
We will record every significant architectural decision as an ADR in `docs/adr/`, numbered sequentially and based on `0000-template.md`. Significant means: a new dependency or framework, a new external service, a data model restructure, a change to layering, a change to quality gates, or a change to anything that an existing ADR decides.

An agent that needs such a change must **write the ADR with status `Proposed` and stop**. Only a human sets it to `Accepted`.

ADRs may be edited in place until they are merged to `main`. After that, a change requires a new ADR that supersedes the old one.

## Consequences
- There is a small overhead per decision.
- Superseded ADRs are kept and marked `Superseded by ADR-XXXX`. They are never deleted.
