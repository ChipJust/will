# 04 — Design

## Prompt

You are entering the design phase.

**Goal:** Decide *how* the system will be built. Capture the architecture, the major component boundaries, and the load-bearing decisions.

**Activities:**
- **Architecture sketch.** Components, what each one owns, how they connect. ASCII boxes-and-arrows is fine.
- **Data flow.** For each major user action, trace the path through the components.
- **Storage.** Where state lives, what's persistent, what's ephemeral, what's encrypted.
- **Failure model.** What can break, what happens when it does, what's the recovery path.
- **Decisions.** Each meaningful choice gets an ADR in `decisions/` (one file per decision, Nygard format: Context → Decision → Consequences). Reference them inline here.
- **Implementation phases.** Outline the order code will be written. This is what `05-implementation` will execute against.

**Exit criteria:**
- An implementer can begin TDD on the first phase without major architectural questions.
- Every load-bearing choice has an ADR or is declared trivial.

**Out of scope:**
- Code (that's `05-implementation`).

---

## Saved response

*(filled in by the agent)*

### Locked-in decisions (carried forward from discussion)

These were decided before phase 03/04 was written and are documented as ADRs in `decisions/`:
- ADR 0001 — Ubuntu 24.04 LTS as base distro
- ADR 0002 — Tailscale for cross-device mesh networking
- ADR 0003 — Samba (SMB) for NAS file sharing
- ADR 0004 — Navidrome + Symfonium for music streaming

The full design (component diagram, data flow, failure model, storage layout, implementation phases) is to be filled in this phase.
