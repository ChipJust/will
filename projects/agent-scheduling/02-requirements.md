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

*Updated 2026-04-26 with answers to all prior open questions. The drafted spec/design downstream are now load-bearing.*

### Scope

This is **the first of multiple use cases** for the same infrastructure. The cohort is one example; Chip already sees similar needs in the marriage context and expects more. Design for groups in general; ship the cohort use case first.

### Users / actors

- **Users.** Members of one or more groups (cohort, marriage, work circle, etc.). Mixed technical literacy — onboarding must clear the "Chip's wife glazes over" bar. Phone-first.
- **Personal agents.** One per user. Represents the user's preferences across all of that user's groups. Maintains a per-user preference context that the agent reads before negotiating and writes after observing.
- **Groups.** Named scopes (cohort, marriage, etc.). Each group declares a scheduling pattern (e.g., "1 cohort meeting + 3 triad meetings per triad per month").

### Behavior list

**Onboarding & membership**
- A user can join a group via invite link (single click → OAuth → in).
- A user can belong to multiple groups under one identity. Identity is OAuth-bound.
- A user can register multiple email/calendar adapters (e.g. personal Gmail + work Outlook) and pick which adapter to use for which group/meeting.
- The platform hosts groups, memberships, privacy policies, and chat persistence. Calendar/email content lives in users' existing apps.

**Calendar access**
- Agents have **full event-level read** access to the user's calendar(s) via the registered adapter(s). Opt-in at setup.
- Agents do not write calendars directly. The output of negotiation is a meeting invite **sent via email API** from a designated participant's account. The "from" account is decided during negotiation (typically the meeting's leader/owner).
- Manual edits to a meeting flow through the leader's normal calendar app; agents observe via subsequent reads.

**Privacy**
- Privacy is **directional and per-relationship**. For every (subject, viewer) pair, subject configures what subject's agent reveals to viewer's agent.
- Asymmetric is allowed by design (Chip shares more with his wife than with a work peer; she may share differently back).
- Default for any new pair: most-restrictive useful level (`decision_only`).

**Negotiation**
- Agents negotiate **batches of related meetings** together (e.g., the cohort's monthly schedule of 1 cohort meeting + N triad meetings, optimized across interdependencies).
- Agents fully represent their user's preferences in negotiation. The user's gate is the **email/calendar invite that arrives at the end** — accept/decline/tentative through normal mechanics.
- The system records the agreed schedule as a set of sent invites.

**Chat & deadlock**
- Each group has a chat room. Both users and their agents post; **agent posts are visually distinct** from user posts.
- When a user is offline or their agent is unreachable, others can still chat manually — the room functions as a normal group chat.
- When negotiation reaches a deadlock, agents surface a **targeted ask** in the chat ("if you could skip this one") aimed at the most-binding users. After the negotiation completes, chat exchanges are **mined to update the relevant users' preference contexts**.

**Preference context**
- Each user's preference context is a persistent document the agent reads before negotiating and writes after.
- Preferences are private to the (user, agent) relationship — never exposed to peers, and not subject to the directional filter (which governs only schedule-data exchange).
- Preferences are configured via context — initialized at setup, augmented by chat exchanges and deadlock-resolution mining over time.

**Cohort scheduling rhythm (first instance)**
- Full cohort meets the **first Monday of each month**. The cohort leader owns that calendar invite; the agent can send updates.
- Triad meetings (3 per triad per month, ~21 interrelated meetings depending on triad structure) are scheduled at the cohort meeting in a single batch.
- Users prepare by marking **tentative-accept** blocks on their calendars ahead of the cohort meeting, so each agent's read is accurate.

### Success criteria

- A user can join their first group and participate in a scheduled meeting in **<10 minutes** from clicking the invite, including OAuth.
- The cohort's monthly batch (cohort meeting + triad meetings) is set in a single negotiation pass with **≤2 user interventions per user** across the whole batch in steady state.
- An agent **never reveals data exceeding the configured directional filter** to any peer agent.
- **≥95%** of confirmed meetings honored without double-booking.
- Per-user monthly LLM cost **<$1**.
- **Prototype usable by Jun 1, 2026** — Chip can schedule a real cohort batch with it.

### Non-functional requirements

- **Phone-first UX.** PWA installable to home screen; no native app.
- **Multi-tenant cloud hosting** (ADR 0001). Onboarding optimized for non-technical users.
- **Pluggable email/calendar adapters** (ADR 0007). Gmail/Google Calendar first; architecture supports adding adapters as new providers (including conditional-access work email) are discovered.
- **Token economy.** Agent-to-agent protocol is LLM-free. LLM only at the human↔agent boundary and during deadlock-mining.
- **Persistent agent context per user.** JSON document, agent-readable and agent-writable.
- **Privacy by directional filter** at the agent boundary (ADR 0004).
- **OAuth-first auth** (ADR 0002). No password storage.

### Explicit non-goals

- Slack / Teams / other-chat-platform integration.
- Voice / video.
- General-purpose agent tasks. This agent only schedules within configured groups.
- Direct calendar writes (output is an emailed invite).
- Self-hosting in v1 (revisit post-prototype).
- End-to-end encryption of chat content in v1 (encryption at rest is required; E2E is a v2 question).

### Open questions

*(All previously-open requirements questions resolved 2026-04-26. New questions emerging during spec/design get logged to STATUS.md.)*

### Note on `will` vs. application repo

For the planning phase, this project lives at `projects/agent-scheduling/` inside the `will` repo, with code under `code/`. Chip's framing — "users install will" — conflates the meta-agent framework with a multi-user platform. Carry that conflation through the prototype; **graduate to a standalone repo (provisional name placeholder: `convene`) when the application ships or when the public/private surface area starts forcing the split.**
