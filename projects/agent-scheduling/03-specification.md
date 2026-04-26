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

*Draft spec extracted from the original 2026-04-22 proposal. **Not yet finalized** — open requirements questions in `02-requirements.md` (especially privacy granularity, hosting model, and auth) may force changes.*

### Surface

- **Chat server (FastAPI + WebSocket).** Hosts rooms; each room is a tuple of human participants and their agents.
- **PWA client.** Joins a room via WebSocket; renders chat history and confirm/override controls.
- **Agent runtime.** One Python process per user; subscribes to its rooms and posts/reads protocol messages.
- **LLM bridge (narrow).** Two directions only:
  - Human NL → structured intent (`"not Mondays"` → `{"avoid": {"weekday": "monday"}}`).
  - Agent state → human summary (`"Proposing Tues 3pm — everyone free"`).

### Agent-to-agent protocol (LLM-free)

JSON messages over the chat room:

| Message | Purpose |
|---------|---------|
| `HELLO` | Identity, capabilities |
| `REQUEST_SLOT` | Purpose, participants, duration, window |
| `FREE_BUSY` | Compact availability bitmap within the window |
| `PROPOSE` | Candidate times |
| `ACCEPT` / `COUNTER` / `DECLINE` | Response to a `PROPOSE` |
| `CONFIRM` | Final time; optionally triggers calendar write |

Each message carries `room_id`, `sender_agent_id`, `sequence_no`, `timestamp`, plus a `body` whose schema is fixed per message type. Detailed body schemas: TBD (see open items below).

### Data model (sketch)

- `Room { id, members: [agent_id], purpose, status }`
- `Meeting { id, purpose, participants, duration, window, status, confirmed_time? }`
- `AgentState { agent_id, calendar_token, preferences, active_meetings }`

### Invariants

- A `CONFIRM` is valid only if the time appears in some prior `PROPOSE` for the same `Meeting.id` and all listed participants have ACCEPTed.
- For a given `Meeting`, an agent's `FREE_BUSY` is monotonically narrowing — never widens after first publish.

### Behavior

For each protocol message: inputs, outputs, side effects, error cases — TBD per message type.

### Examples

TBD — at least one full happy-path trace and one decline-and-counter trace before phase exit.

### Open spec items

- Concrete JSON schemas for each message type.
- Error and timeout behavior (agent unreachable, human idle).
- Calendar adapter interface (Google Calendar first; Outlook later).
- Free/busy granularity and privacy default — gated on requirements decision (linked).
