# 03 — Specification

## Prompt

You are entering the specification phase.

**Goal:** Define the *externally observable behavior* of the system. An external integrator should be able to implement against this without reading internals.

**Activities:**
- **Surface.** API endpoints, CLI commands, file formats, message schemas — whatever the boundary is.
- **Data model.** Entities, fields, types, relationships. Include enums and value ranges.
- **Invariants.** What must always be true (uniqueness, ordering, conservation laws).
- **Behavior.** For each surface element: inputs, outputs, side effects, error behavior, rate limits.
- **Examples.** At least one concrete request/response or input/output trace per major surface.

**Exit criteria:**
- A second implementer building from this spec independently produces an interoperable system.
- Each behavior is testable without seeing the implementation.

**Out of scope:**
- How it's built internally (that's `04-design`).
- Code (that's `05-implementation`).

---

## Saved response

*(filled in by the agent)*
