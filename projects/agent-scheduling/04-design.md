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

*Architectural sketch extracted from the 2026-04-22 proposal. **Major decisions are still Proposed**, not Accepted — see ADRs listed below.*

### Architecture sketch

```
┌──────────┐    WebSocket    ┌──────────────────┐
│  PWA     │ ◀──────────────▶│  Chat server     │
│ (client) │                  │  (FastAPI + WS)  │
└──────────┘                  │  + SQLite        │
                              └─────┬────────────┘
                                    │ pub/sub
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
            ┌──────────┐      ┌──────────┐      ┌──────────┐
            │ Agent A  │      │ Agent B  │      │ Agent C  │
            │ (Python) │      │ (Python) │      │ (Python) │
            └──────────┘      └──────────┘      └──────────┘
                  │                 │                 │
                  └────── Calendar adapter (per-user) ┘
                  └────── LLM bridge (per-user, on demand)
```

### Components

1. **Chat server.** FastAPI + WebSocket, SQLite persistence. Hosts rooms.
2. **Agent runtime.** One Python process per user. State machine for negotiation; LLM calls only at the human boundary.
3. **Calendar adapter.** Per-user OAuth to Google Calendar (Outlook later). Reads free/busy in a rolling window.
4. **LLM bridge.** Narrow translation layer (NL ↔ structured intent, structured state → human summary).
5. **PWA client.** Served by the chat server, installable on phone home screen.

### Data flow (request → confirm)

1. Human posts an NL request in the room → LLM bridge → structured intent → agent.
2. Agent emits `REQUEST_SLOT`. Other agents respond with `FREE_BUSY`.
3. Solver intersects free/busy + preferences, emits `PROPOSE`.
4. Each agent runs auto-accept rules; surfaces to its human if ambiguous → `ACCEPT` or `COUNTER`.
5. On unanimous `ACCEPT`, originating agent emits `CONFIRM`. Optional calendar write.

### Storage

- **Server-side.** Rooms, message history (configurable retention), per-user OAuth refresh tokens (encrypted).
- **Client-side.** Cached preferences, draft messages.

### Failure model

- **Agent down.** Other agents back off after timeout; humans can still chat manually in the room.
- **LLM bridge down.** Agent functions on structured input only; bridge degradation is visible in the UI.
- **Calendar API rate limit.** Cached free/busy with TTL; retry with jitter.

### Token minimization

- Protocol exchange is LLM-free.
- LLM bridge receives a tight reusable system prompt (prompt-cacheable), the current human message, and the compact state snapshot (~1KB).
- Summaries generated once per negotiation round, not per protocol message.
- Default model tier: Haiku for the bridge; escalate to Sonnet only for ambiguous free-form parsing.

### Human UX

- The chat room view shows: agent proposals/questions, other humans' free-form messages, confirm/override control on proposed times.
- Agent-to-agent protocol messages are hidden by default, expandable for debugging.

### Decisions (open)

ADR placeholders — lock after requirements close out:

- [`0001-hosting-model.md`](decisions/0001-hosting-model.md) — Centralized vs. federated. *(seeded as Proposed)*
- `0002-auth-and-identity.md` — Account model and how members discover each other.
- `0003-calendar-write-scope.md` — Read-only vs. read/write; dedicated calendar vs. primary.
- `0004-privacy-granularity.md` — What an agent reveals to peer agents.
- `0005-agent-autonomy-default.md` — Auto-accept policy when the human is offline.
- `0006-group-negotiation-pattern.md` — N-way native vs. leader-elected scheduler.

### Implementation phases

1. Protocol spec lock + calendar adapter interface + minimal UI wireframe + LLM API skeleton with caching.
2. Walking skeleton: FastAPI + WS rooms + SQLite; two headless agents negotiating a fixed scenario with in-memory calendars; print transcripts; verify deterministic logic.
3. Human loop (single user): PWA client; LLM bridge wired in; one human + agent negotiating against a scripted counter-agent.
4. Multi-user + real calendars: magic-link auth; Google Calendar OAuth; Web Push; three-way (triad) negotiation.
5. Pilot with the cohort; observe failures; iterate.
6. Beyond: calendar write (event creation), Outlook support, federation if it matters.
