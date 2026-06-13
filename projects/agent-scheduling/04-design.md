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

*Rewritten 2026-04-26 against `02-requirements.md` and ADRs 0001–0007.*

### Architecture sketch

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  Platform (multi-tenant cloud) — ADR 0001               │
│                                                                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│   │ Auth + user  │  │ Group +      │  │ Privacy      │  │ Chat server│  │
│   │ mgmt (OAuth) │  │ membership   │  │ policy svc   │  │ (FastAPI + │  │
│   │ — ADR 0002   │  │ svc          │  │ — ADR 0004   │  │  WebSocket)│  │
│   └──────────────┘  └──────────────┘  └──────────────┘  └─────┬──────┘  │
│                                                               │         │
│   ┌───────────────────────────────────────────────────────────┴───────┐ │
│   │                  Per-user agent runtime                           │ │
│   │  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐     │ │
│   │  │ Negotiator   │  │ Solver           │  │ Agent context    │     │ │
│   │  │ state        │  │ (batch CSP +     │  │ store (per-user  │     │ │
│   │  │ machine      │  │  preference      │  │  preference doc, │     │ │
│   │  │ (LLM-free)   │  │  weighting)      │  │  agent-writable) │     │ │
│   │  └──────────────┘  └──────────────────┘  └──────────────────┘     │ │
│   │  ┌──────────────────────────────────┐  ┌──────────────────┐       │ │
│   │  │ Adapter registry (per-user-per-  │  │ LLM bridge       │       │ │
│   │  │ provider) — ADR 0007             │  │ (Haiku default,  │       │ │
│   │  │  • GoogleAdapter (Gmail+Cal)     │  │  Sonnet escal.)  │       │ │
│   │  │  • OutlookAdapter, …             │  └──────────────────┘       │ │
│   │  │  • MockAdapter (tests)           │                             │ │
│   │  └──────────────────────────────────┘                             │ │
│   └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│   Encrypted-at-rest store: users, groups, privacy, OAuth tokens,        │
│   chat history, agent contexts.                                         │
└─────────────────────────────────────────────────────────────────────────┘
                       ▲                                ▲
                       │ HTTPS                          │ WebSocket
                       │                                │
              ┌────────┴────────┐               ┌───────┴────────┐
              │  User's email/  │               │  PWA client    │
              │  calendar APIs  │               │  (browser/     │
              │  (Gmail, Cal,   │               │   phone)       │
              │   Outlook, …)   │               │                │
              └─────────────────┘               └────────────────┘
```

### Components

1. **Platform service.** FastAPI. Owns user accounts (OAuth identities), groups, memberships, privacy policies, and `MeetingPattern` configs. Encrypted-at-rest store (SQLite for prototype; Postgres path forward).

2. **Chat server.** FastAPI + WebSocket. Hosts group rooms. Persists chat history (configurable retention). Both human posts and agent protocol messages flow here. Visual distinction is enforced by the `kind` field on each post.

3. **Per-user agent runtime.** A Python process (or coroutine in shared runtime) representing each user. Contains:
   - **Negotiator** — LLM-free state machine driving the agent-to-agent protocol.
   - **Solver** — batch constraint-satisfaction over the meeting set, weighted by user preferences from the agent context.
   - **Agent context store** — JSON document per user. Read at start of each negotiation; written after via post-mining and direct user input.
   - **Adapter registry** — per-user-per-provider; agent picks the right adapter per meeting.
   - **LLM bridge** — narrow scope: NL→intent, state→summary, post-mining of chat exchanges. Haiku default; Sonnet on parse ambiguity.

4. **PWA client.** Group list, group chat, settings (preferences, privacy per-edge, adapter management). Magic-link / OAuth onboarding.

### Data flow

**Onboarding (new user joining a group)**

1. User clicks invite link → platform validates token.
2. OAuth (Google) → platform binds account to user record + creates default `GoogleAdapter`.
3. Platform creates `Membership(user, group)` and seeds `PrivacyPolicy` rows with `decision_only` for every existing member.
4. User lands in the group's chat room.

**Batch scheduling (cohort monthly)**

1. Trigger (cohort meeting time, leader pushes button, or scheduled job): leader's agent emits `BATCH_SCHEDULE` for the next month's `MeetingPattern`.
2. Each participant's agent:
   - Reads its user's calendar via the registered adapter for the relevant time window.
   - Filters the data per `PrivacyPolicy` for each peer recipient.
   - Emits `FREE_BUSY` to the room.
3. Solver in each agent runs the batch CSP locally on the available data; one agent (the negotiation initiator) collates and emits `PROPOSE`.
4. Each agent responds `ACCEPT` / `COUNTER` / `DECLINE`. If unanimous accept → `CONFIRM`.
5. On `CONFIRM`, each `ProposedMeeting`'s `source_adapter` sends the invite via email API (per ADR 0003).
6. Recipients RSVP via normal calendar mechanics.
7. Post-batch: LLM bridge mines the chat exchanges from this negotiation and writes preference updates back to the relevant agent contexts.

**Deadlock**

1. Solver returns slack analysis: which user(s)' constraints are most binding.
2. Negotiator emits `DEADLOCK_ASK` targeted at those user(s) with concrete suggestions.
3. Wait window (default 24h).
4. `DEADLOCK_RELAX` from a user → re-solve. Else propose best-available partial.
5. Mining post-resolution.

### Storage

- **Platform-side, encrypted at rest:** users, groups, memberships, privacy policies, OAuth refresh tokens, chat history (configurable retention), agent contexts.
- **User's apps:** calendar events, email, the actual sent invites — never duplicated server-side.
- **Ephemeral:** in-flight negotiation state in agent runtime memory; persisted to platform store on negotiation milestones for crash recovery.

### Failure model

| Failure | Behavior |
|---------|----------|
| Adapter auth broken | Health surfaces in UI as "reconnect [provider]"; agent operates degraded for that user. |
| Agent runtime down | Chat continues to work; humans chat manually. Negotiation pauses; resumes on agent revival. |
| LLM bridge down | Agent still negotiates via structured state; users see degraded mode in UI; preference mining queued for later. |
| Solver infeasible | Deadlock-resolution flow (ADR 0006). |
| Calendar API rate-limit | Cached free/busy with TTL; retry with jitter. |
| Invite-send failure | Surface to source user; allow manual resend or alternate source-account selection. |
| OAuth refresh failure | Re-auth prompt at next user touch; agent degraded until resolved. |

### Token minimization

- Agent-to-agent protocol exchange is fully LLM-free.
- LLM bridge is invoked at:
  - User's free-form NL inputs in chat (parse to structured intent).
  - Generating human-readable summaries of in-flight negotiation state (one per round, not per message).
  - Post-negotiation mining (one batched call per user with chat exchanges + their context).
- Default model tier: **Haiku.** Escalate to **Sonnet** only when Haiku reports parse ambiguity.
- All LLM calls use prompt caching with the agent persona + protocol description as the cacheable prefix.

### Decisions (all Accepted)

- [`0001-hosting-model.md`](decisions/0001-hosting-model.md) — Multi-tenant cloud.
- [`0002-auth-and-identity.md`](decisions/0002-auth-and-identity.md) — OAuth-first, invite-link group binding.
- [`0003-calendar-write-scope.md`](decisions/0003-calendar-write-scope.md) — Read full events; output is emailed invite.
- [`0004-privacy-granularity.md`](decisions/0004-privacy-granularity.md) — Directional per-edge filter.
- [`0005-agent-autonomy-default.md`](decisions/0005-agent-autonomy-default.md) — Full agent representation; user gate is invite RSVP.
- [`0006-group-negotiation-pattern.md`](decisions/0006-group-negotiation-pattern.md) — Batch-first; deadlock via targeted chat asks; preference mining.
- [`0007-email-calendar-adapter-pattern.md`](decisions/0007-email-calendar-adapter-pattern.md) — Pluggable adapters; Gmail first.

### Implementation phases (5-week plan toward Jun 1 prototype)

| Wk | Phase | Output |
|----|-------|--------|
| 1 | **Skeleton + adapter interface + agent context** | `code/` Python package; pyproject; pytest; `MockAdapter`; `AgentContext` load/save/update; first failing tests passing. |
| 1–2 | **Negotiator + solver against mocks** | Protocol messages, batch CSP, deterministic logic with unit tests. End-to-end: two agents negotiate a cohort batch with mocked calendars; transcript inspectable. |
| 2 | **Chat server + WebSocket rooms** | FastAPI + WS; SQLite chat persistence; user vs agent post distinction; protocol messages routed correctly. |
| 3 | **Real Google adapter + OAuth** | `GoogleAdapter` reads calendar, sends invites. End-to-end: agents negotiate against real Google Calendar in a test account. |
| 3–4 | **PWA + onboarding** | Group list, chat view, settings (preferences, privacy per edge, adapter management). Invite-link flow. Magic-link or OAuth-only sign-in. |
| 4 | **Cohort dry run** | Three real users + agents schedule a batch (cohort meeting + several triads). Iterate on preference setup, deadlock UX, mining quality. |
| 5 | **Polish + deploy** | Bug fixes, deploy to a small VPS, document the prototype. **Demo Jun 1.** |

### Code layout

```
projects/agent-scheduling/code/
├── pyproject.toml
├── src/agent_scheduling/
│   ├── __init__.py
│   ├── context.py        # AgentContext load/save/update
│   ├── adapters/         # adapter interface + impls
│   │   ├── __init__.py
│   │   ├── base.py       # Protocol/ABC
│   │   ├── mock.py       # MockAdapter for tests
│   │   └── google.py     # later
│   ├── protocol.py       # message envelopes + body types
│   ├── negotiator.py     # state machine
│   ├── solver.py         # batch CSP
│   ├── privacy.py        # filter application
│   ├── llm_bridge.py     # narrow LLM I/O
│   ├── chat.py           # client wrapper for chat server
│   └── platform/         # platform-service + chat-server (added wk 2)
│       ├── api.py
│       └── ws.py
└── tests/
    ├── test_context.py
    ├── test_adapter_mock.py
    ├── test_negotiator.py
    ├── test_solver.py
    └── test_privacy.py
```

When this project graduates from `will/projects/` to its own repo, this layout is the seed.
