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

*Rewritten 2026-04-26 against the resolved requirements (`02-requirements.md`) and accepted ADRs 0001–0007. Detail-level message and adapter schemas are still TBD; flagged below.*

### Surfaces

The system exposes four surfaces:

1. **Web app / PWA** — user-facing UI for sign-in, group management, chat, settings.
2. **Platform HTTP API** — REST endpoints for users, groups, memberships, privacy policies, adapters.
3. **Chat-server WebSocket protocol** — for live group chat including agent posts.
4. **Agent-to-agent protocol** — LLM-free JSON messages exchanged over the chat-server (within a group room).

Plus two **boundary integrations**:

5. **Per-user email/calendar adapters** — implementations of the adapter interface (ADR 0007); Gmail/Google Calendar first.
6. **LLM bridge** — narrow translation layer (NL ↔ structured intent; structured state → human summary; post-negotiation chat mining).

### Data model

**Platform-level**

- `User { id, oauth_identities: [OAuthIdentity], preference_context_ref }`
- `OAuthIdentity { provider, external_id, display_name, scopes }`
- `Adapter { id, user_id, provider, config_ref }` — one per (user, provider).
- `Group { id, name, scheduling_pattern_ref }`
- `Membership { user_id, group_id, role, default_adapter_id }`
- `PrivacyPolicy { subject_user_id, viewer_user_id, level }` — directional, per-edge.
- `MeetingPattern { id, group_id, recurring_meetings: [RecurringMeetingSpec] }` — declares the scheduling rhythm.
- `Negotiation { id, group_id, batch: [MeetingRequest], status, created_at }`
- `Proposal { id, negotiation_id, meetings: [ProposedMeeting], status }`
- `ProposedMeeting { id, time, duration, participants, source_adapter_id, source_user_id, status }`

**Agent-level (per user)**

- `AgentContext { user_id, preferences: dict, hard_constraints: list, learned_history: list, version }`
  - Read at start of every negotiation.
  - Written after negotiation by post-mining (and optionally during, on direct user input).

### Invariants

- Every `(subject, viewer)` pair where both share at least one group has exactly one `PrivacyPolicy` (default `decision_only` if not explicitly set).
- A `BATCH_SCHEDULE` produces exactly one `Proposal` per call; each `ProposedMeeting` has exactly one `source_adapter_id` assigned.
- A `CONFIRM` is valid only if every participant agent has emitted `ACCEPT` for the same proposal id.
- For a given negotiation, an agent's `FREE_BUSY` data is monotonically narrowing — never widens after first publish.
- Any outbound agent message destined for `viewer` is filtered through `PrivacyPolicy(subject=sender_user, viewer=recipient_user)` before send.

### Agent-to-agent protocol

JSON messages over the chat-server room. **Every message is LLM-free.**

| Message | Purpose |
|---------|---------|
| `HELLO` | Identity + capabilities advertisement. |
| `BATCH_SCHEDULE` | Initiate a negotiation over N meetings (N ≥ 1). Carries `meeting_pattern_ref` or explicit `[MeetingRequest]`. |
| `FREE_BUSY` | Filtered availability over the relevant window. Filtered per ADR 0004. |
| `PROPOSE` | Candidate proposal: a set of `(time, duration, participants, source_adapter_id)` tuples for the batch. |
| `ACCEPT` / `COUNTER` / `DECLINE` | Response to a `PROPOSE`. |
| `CONFIRM` | All agents agreed; triggers send-invite via the `source_adapter_id` for each meeting. |
| `DEADLOCK_ASK` | Targeted question from solver to a user (visible to all in chat). Carries the binding-constraint context. |
| `DEADLOCK_RELAX` | A user/agent's response offering a relaxation. |

Common envelope on every message: `room_id`, `negotiation_id`, `sender_agent_id`, `sender_user_id`, `sequence_no`, `timestamp`, `body` (per-type). Detailed body schemas: TBD.

### Chat-server WebSocket protocol

- A user joins a group room → server pushes recent history.
- Posts have `kind ∈ { user, agent }` for visual distinction.
- Agent-protocol messages (`HELLO`, `BATCH_SCHEDULE`, etc.) are emitted into the room with `kind: agent` and a `protocol_message_type` field.
- Clients render protocol messages as expandable details by default (per `04-design.md`).

### Adapter interface (ADR 0007)

```
EmailCalendarAdapter:
  list_calendar_events(window: TimeWindow) -> list[Event]
  send_invite(invite: MeetingInvite) -> InviteResult
  get_send_address() -> str
  health() -> AdapterHealth
```

`Event`, `MeetingInvite`, `InviteResult`, `TimeWindow`, `AdapterHealth` schemas: TBD during phase-1 implementation.

### Behavior

For each protocol message and adapter call: inputs, outputs, side effects, error/timeout behavior — **TBD per item** as we drive them out via TDD in phase 05.

### Examples (TBD; required before phase exit)

- **Cohort monthly batch.** Full trace: leader emits `BATCH_SCHEDULE` for 1 cohort meeting + 6 triad meetings; all 7 agents respond with filtered `FREE_BUSY`; solver runs in each agent; `PROPOSE` from leader; unanimous `ACCEPT`; `CONFIRM`; per-meeting source-adapter sends invite.
- **Triad-only.** Degenerate batch of 3 meetings.
- **Deadlock resolution.** Solver returns slack analysis; `DEADLOCK_ASK` to user X about meeting M; user posts a relaxation; re-solve; `PROPOSE` accepted; post-mining updates user X's context.

### Open spec items

- Concrete JSON body schemas per message type.
- Concrete `Event` / `MeetingInvite` / `InviteResult` / `TimeWindow` / `AdapterHealth` types.
- Privacy filter level definitions (concrete shapes for `full_details`, `decision_only`, `busy_only`).
- Solver algorithm specification (constraint encoding, weight model).
- `MeetingPattern` config schema.
- Error / timeout values (agent unreachable, human idle, adapter rate-limit retry, etc.).
- Invite payload format (iCalendar payload, email subject/body conventions, RSVP-link handling).

These resolve during phase-1 implementation in `05-implementation.md`.
