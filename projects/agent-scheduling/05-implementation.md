# 05 — Implementation

## Prompt

You are entering the implementation phase. Build the system using **test-driven development**.

**The TDD cycle (Kent Beck — red / green / refactor):**
1. Pick the smallest behavior from the spec that isn't yet implemented.
2. Write a failing test that asserts that behavior. Run it, watch it fail (red).
3. Write the minimum code that makes the test pass (green).
4. Refactor with tests green: extract, rename, dedupe.
5. Commit at green. Repeat.

**Activities:**
- For each phase from `04-design`, work through the TDD cycle until that phase's behaviors are covered.
- Maintain a running log in the saved response — one entry per cycle (test name, what it drove out, any surprise).
- Track deferred work explicitly: if you skip a behavior, record it under "Deferred" with reason and conditions for picking it back up.
- When you discover the spec or design is wrong, stop, fix the upstream document, then continue. Do not patch silently.

**Exit criteria:**
- Every spec behavior has at least one test.
- All tests are green on `main`.
- Deferred-work list is current and triaged.

**Out of scope:**
- Architectural rework (return to `04-design` and add an ADR).
- Net-new features beyond the spec (return to `02-requirements` first).

---

## Saved response

*Code skeleton seeded 2026-04-26 at `code/`. Implementation has not begun. Pre-conditions met: requirements resolved, ADRs 0001–0007 Accepted, design complete with phased plan.*

### How to start (next agent)

```bash
cd D:/_code/will/projects/agent-scheduling/code
uv sync
uv run pytest          # current state: one failing test (driven by the first slice below)
```

Then walk down the slice list below in order. Commit at each green using `commit_push.py`.

### TDD slices — phase 1: skeleton + adapter interface + agent context (week 1)

Each slice has: a target test, the minimal behavior to drive, and exit criteria. Follow them in order.

1. **`AgentContext` empty + JSON round-trip.** *(seeded — failing test exists at `tests/test_context.py`.)*
   - Drive out: `src/agent_scheduling/context.py` with `AgentContext.empty()`, `.preferences`, `.save(path)`, `.load(path)`.
   - Exit: `tests/test_context.py` green.
2. **`AgentContext.update_from_chat`.** Take a list of chat exchanges + a current context, produce an updated context. (At this slice, the "update" is rule-based — LLM mining comes later.)
3. **`MockAdapter.list_calendar_events`.** Adapter Protocol in `adapters/base.py`; `MockAdapter` in `adapters/mock.py` that returns events from a constructor-supplied list. Drive `Event` and `TimeWindow` types.
4. **`MockAdapter.send_invite`.** Adds `MeetingInvite` and `InviteResult` types; mock records the invite in an in-memory log.
5. **`MockAdapter.health` + `get_send_address`.** Round out the adapter Protocol.
6. **Privacy filter — `decision_only`.** `privacy.py:apply_filter(events, level)` returning the filtered set. Test `decision_only` first; `full_details` is a passthrough; `busy_only` strips event metadata.
7. **Privacy policy lookup.** Given a `(subject_user, viewer_user)` pair and a policy store, return the level. Default `decision_only` for unset pairs.
8. **`MeetingPattern`.** Declares the cohort rhythm (1 cohort + N triads, with triad memberships). Drives a config schema; serialize/deserialize.
9. **Protocol envelope.** `protocol.py` — common envelope (`room_id`, `negotiation_id`, `sender_*`, `sequence_no`, `timestamp`). Round-trip through JSON.

### TDD slices — phase 2: negotiator + solver (week 1–2)

10. **`HELLO` exchange.** Two negotiators advertise capabilities to each other.
11. **`BATCH_SCHEDULE` carrying a single meeting.** Solver returns a single proposal slot. Use mock adapters with hand-crafted free/busy.
12. **`FREE_BUSY` filtered through privacy.** Sender filters before emit; receiver consumes filtered.
13. **`BATCH_SCHEDULE` carrying multiple interrelated meetings.** Solver optimizes across them — minimal CSP. Verify with an oracle test (compare solver output to a brute-force enumerator on a small instance).
14. **Source-adapter assignment in proposals.** Each `ProposedMeeting` has a `source_adapter_id`. Test that the leader's adapter is assigned for cohort meetings; per-triad rules for triads.
15. **`ACCEPT` / `COUNTER` / `DECLINE` flow.** End-to-end: negotiate → propose → unanimous accept → confirm.
16. **`CONFIRM` triggers `MockAdapter.send_invite`.** Verify the right adapter was called for each meeting.
17. **Deadlock detection.** When the solver returns infeasible, emit `DEADLOCK_ASK` targeted at the most-binding user(s).
18. **`DEADLOCK_RELAX` re-solve.** A relaxation message triggers a re-solve.
19. **Persist negotiation state to disk (crash recovery).** Write at each milestone; reload on agent restart.

### TDD slices — phase 3: chat server + WebSocket (week 2)

20. **FastAPI app boots with one `/health` endpoint.**
21. **WebSocket room-join + history replay.** Client connects → server replays last N messages.
22. **User vs agent post distinction.** `kind` field round-trips through WebSocket frames.
23. **Agent emits a protocol message into a room.** Verify it reaches all connected clients with the `protocol_message_type` field.
24. **Chat history persistence (SQLite).** Messages survive a server restart.

### TDD slices — phase 4: real Google adapter + OAuth (week 3)

25. **OAuth flow stub** with a test account; obtain refresh token.
26. **`GoogleAdapter.list_calendar_events`** against a controlled test calendar.
27. **`GoogleAdapter.send_invite`** sends an iCalendar invite via Gmail send.
28. **End-to-end real-API negotiation** between two test accounts.

### TDD slices — phase 5: PWA + onboarding (week 3–4)

29. Invite-link generation + redemption.
30. OAuth sign-in + account binding.
31. Group list + chat view (basic).
32. Settings: preferences entry, privacy per-edge, adapter management.
33. Magic-link fallback for non-OAuth invitees (TBD — may be skipped if OAuth-only is acceptable).

### TDD slices — phase 6: cohort dry run (week 4)

34. Real cohort batch with three real users; observe; iterate.

### TDD slices — phase 7: polish + deploy (week 5)

35. Bug fixes from the dry run.
36. VPS deploy script.
37. Demo on Jun 1.

### TDD log

Phases 1–3 completed in one autonomous session on 2026-04-26.

**Phase 1 — Skeleton, adapter interface, agent context (slices 1–9)**

| # | Behavior | Drove out |
|---|----------|-----------|
| 1 | `AgentContext.empty()` + JSON round-trip | `context.py`, dataclass, save/load |
| 2 | `update_from_chat` rule-based (prefer/avoid) | `ChatExchange`, regex extractor, immutability |
| 3 | `MockAdapter.list_calendar_events` filters by window | `adapters/base.py` Protocol, `Event`, `TimeWindow`, half-open overlap |
| 4 | `MockAdapter.send_invite` records to log | `MeetingInvite`, `InviteResult`, send-id assignment |
| 5 | `MockAdapter.health` + `get_send_address` | `AdapterHealth`, full Protocol surface |
| 6 | `apply_filter(events, level)` for full_details / busy_only / decision_only | `PrivacyLevel` enum, metadata stripping |
| 7 | `PrivacyPolicyStore` with directional lookup, default `decision_only` | per-edge get/set, asymmetry by design |
| 8 | `MeetingPattern` + `RecurringMeetingSpec` JSON round-trip | group rhythm config |
| 9 | `Envelope` + `MessageType` enum, datetime-as-iso | full protocol surface (10 message types) |

**Phase 2 — Negotiator + solver (slices 10–19)**

| # | Behavior | Drove out |
|----|----------|-----------|
| 10 | `Negotiator` HELLO emit/receive + capability tracking | `negotiator.py`, sequence-no, injectable clock |
| 11 | Single-meeting solver + `BATCH_SCHEDULE` emission | `solver.py`, candidate enumeration, granularity stepping |
| 12 | `FREE_BUSY` filtered per-recipient with directional privacy | event encode/decode helpers, viewer routing |
| 13 | Multi-meeting batch solver with shared-participant constraint | backtracking + brute-force oracle |
| 14 | `assign_sources` produces `ProposedMeeting` with source_user/adapter | per-meeting override + default fallback |
| 15 | PROPOSE / ACCEPT / COUNTER / DECLINE flow + response tracking | unanimous-accept check |
| 16 | CONFIRM emit/receive triggers `send_invite` for owned meetings | adapter registry on negotiator, idempotent send tracking |
| 17 | `analyze_deadlock` + DEADLOCK_ASK | block-score heuristic, feasibility precheck |
| 18 | DEADLOCK_RELAX + `apply_relaxations(drop_meeting)` | relaxation envelope, kind dispatcher |
| 19 | Persist negotiator state to JSON for crash recovery | save_state/load_state with idempotency preservation |

**Phase 3 — Chat server (slices 20–24)**

| # | Behavior | Drove out |
|----|----------|-----------|
| 20 | FastAPI `/health` endpoint | `platform/api.py` factory + TestClient |
| 21 | `/ws/{room_id}` WebSocket with history replay | `ChatRoom`, `RoomRegistry`, single-client echo |
| 22 | `kind` field validation (user / agent only) | reject + report invalid, no persistence of bad msgs |
| 23 | Broadcast to all clients in a room | per-room connection registry, `protocol_message_type` round-trip |
| 24 | SQLite chat persistence across app restart | `SqliteChatStore`, registry write-through, history reload on first access |

### Deferred

Phase 4+ (slices 25–37) requires external credentials (Google OAuth) and frontend tooling beyond what this session had access to:

- **Slice 25–28 (Google adapter + OAuth):** awaiting Google API client credentials path. The `MockAdapter` proves the Protocol interface; `GoogleAdapter` is a parallel implementation against the same Protocol.
- **Slice 29–33 (PWA + onboarding):** frontend stack not provisioned in this session. The platform-API-side surface area needed is `/groups`, `/users/me`, `/privacy-policies`, `/adapters`, plus a simple HTML shell — drive it out from a real browser environment.
- **Slice 34–37 (cohort dry run, polish, deploy):** depends on 25–33.

### Operational notes

- Python 3.14.3 via uv. `uv sync` then `uv run pytest`.
- 135 tests pass at 0.3–1.3s wall time depending on fastapi/websocket spool-up.
- Dependencies: `fastapi`, `httpx` (TestClient). Dev: `pytest`.
- No persistent state outside the agent's own JSON file (slice 19) and the optional SQLite chat DB (slice 24) — both opt-in.
