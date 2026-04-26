# 0005. Agent autonomy — full representation; user gate is the invite RSVP

**Status:** Accepted
**Date:** 2026-04-26

## Context

The original draft framed autonomy as "auto-accept matching preferences vs. always check." Resolved 2026-04-26 with a different model: agents **negotiate to a complete proposal autonomously** using stored preferences, and the user's checkpoint is the resulting **email/calendar invite**. This decouples negotiation from human availability and treats the chat as a transparency surface, not a confirmation gate.

## Decision

**Full agent representation.** The agent represents the user during the entire negotiation, drawing on the agent context store (ADR 0007's preference doc; updated continuously per ADR 0006's deadlock-resolution mining). The user does not need to be online for a proposal to land.

The user's gate is the **invite RSVP** — accept / decline / tentative through their normal calendar app. Decline triggers a re-negotiation round.

If the user wants to influence an in-flight negotiation, they post in the group chat. The chat is part of the negotiation environment; the agent treats user posts as new preference data and re-runs.

## Consequences

- Removes the "agent waits for user to confirm" failure mode.
- Increases the criticality of accurate stored preferences. Preference quality is a first-class concern, not an afterthought.
- The chat is a transparency surface, not a confirmation gate. Both human and agent posts appear; visual distinction is required (per `02-requirements.md`).
- Edge case: a user who declines an invite triggers re-negotiation (handled by ADR 0006 deadlock flow).
- Edge case: a user who never opens the chat can still receive valid proposals — the agent runs without them.
