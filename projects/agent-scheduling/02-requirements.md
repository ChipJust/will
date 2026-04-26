# 02 — Requirements

## Prompt

You are entering the requirements phase.

**Goal:** Capture *what* the system must do and for whom, in language that doesn't pre-judge the design.

**Activities:**
- **Users / actors.** Who interacts with this? What is their context (device, attention level, expertise)?
- **Behavior list.** Bullet list of capabilities, each phrased as a user-facing outcome ("the user can …", "the system records …"). One bullet per capability; nest sub-points if needed.
- **Success criteria.** How do we know it's working? Quantitative where possible (latency, accuracy, cost).
- **Non-functional requirements.** Performance, privacy, cost ceiling, availability, observability, accessibility.
- **Explicit non-goals.** Things this does *not* try to do — write them down so design doesn't drift into them.

**Exit criteria:**
- An implementer who never read the research could write the spec from this file.
- Each requirement is independently checkable.

**Out of scope:**
- API/protocol details (that's `03-specification`).
- Internal structure (that's `04-design`).

---

## Saved response

### Users / actors

- **Cohort members** — seven humans, mixed technical literacy, primarily reaching the system from their phone.
- **Personal agents** — one Python process per user. Runs whenever the user is reachable for negotiation.

### Behavior list

- The user can request a meeting (purpose, duration, participants, target window).
- The user's agent reads their calendar's free/busy and exchanges availability with other agents.
- Agents propose candidate times; the human can confirm, override, or counter from their phone.
- The agent surfaces to the human only when input is genuinely required (ambiguity, conflict, exception to stored preferences).
- Once confirmed, the agreed time is recorded and (optionally) written back to participants' calendars.
- Members can also chat directly in the room (free-form) when they want to talk human-to-human, not via agent.

### Success criteria

- Reduce cohort coordination effort to ≤2 user interactions per scheduled meeting in the steady state.
- A scheduled meeting time is honored by all participants' calendars (no double-booking) ≥95% of confirmations.
- Per-user monthly LLM cost < $1 in steady state.

### Non-functional requirements

- **Phone-first UX.** PWA installable to home screen; no native app.
- **Low token cost.** Protocol exchange is deterministic; LLM calls happen only at the human boundary.
- **Small per-call context.** Agent state is a compact JSON blob (~1KB), not accumulated history.
- **Python only.** Reuse the ecosystem's existing stack.
- **Privacy by default.** Agents share availability decisions, not raw calendar contents, unless explicitly opted in.

### Non-goals (current draft)

- Slack / Teams / other-chat-platform integration.
- Voice or video.
- General-purpose agent tasks. This agent only schedules.

### Open questions

**Scope**
- Cohort-only, or wider use from day one?
- Does it ship before the cohort starts, or can the cohort coordinate manually for the first months while the tool catches up?

**Hosting** *(see decisions/0001-hosting-model.md)*
- Centralized (one server) vs. federated (each user runs their own agent)?
- If centralized: home lab, cloud, free tier?

**Auth & identity**
- How do members find each other's agents — shared cohort ID, invite link, other?
- Account model: email + magic link, OAuth, passkeys?

**Calendar integration**
- Read-only free/busy, or write access for event creation?
- If write: dedicated "cohort" calendar or primary?
- Lookahead window: rolling two weeks, full year?
- How to treat existing recurring events the agent should respect?

**Privacy**
- Do agents share full free/busy slots with peers, or only "I can do X, Y, Z"?
- What's stored server-side vs. client-side?

**Agent autonomy**
- Auto-accept proposals matching stored preferences, or always check with the human?
- When the human is offline/traveling, what authority does the agent have?
- How are preferences expressed — free-form once, structured settings, both?

**Protocol**
- N-way native group negotiation, or one agent acts as scheduler while others respond?
- How are deadlocks broken when three agents each have one hard constraint?

**LLM usage**
- Which prompts are cacheable? (Likely agent persona + protocol description.)
- How to measure and cap monthly token spend per user?

**Fallback**
- If an agent is down, can humans still chat manually in the room?
- If the LLM bridge fails, can the agent function with structured input only?

**Security**
- End-to-end encryption, or trust the server?
- Data retention: how long are messages and calendar snapshots kept?
