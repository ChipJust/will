# 0003. Calendar write scope — read full events, send via email invite

**Status:** Accepted
**Date:** 2026-04-26

## Context

Initial draft considered direct `calendar.write` OAuth scope. Chip clarified: agents have **full event-level read access** (not just free/busy) — opt-in at setup — and the platform does **not** write calendars directly. The deliverable of negotiation is a meeting invite **sent via email API** from one of the participants' accounts. Calendar updates flow through the recipients' normal RSVP processing.

This keeps the platform out of the calendar-edit business and uses the email→RSVP pipeline as the canonical update channel.

## Decision

- **Read scope:** event-level calendar read (e.g. `calendar.events.readonly` for Google), opt-in at setup. Inter-agent `FREE_BUSY` messages may carry filtered event objects per ADR 0004's directional privacy filter.
- **Write scope:** `mail.send` only. The agreed proposal is converted to a calendar invite (iCalendar payload in the email body / standard provider invite) and sent from a designated participant's account. The "from" account is decided during negotiation, typically the meeting's leader/owner.
- Manual edits to a scheduled meeting flow through the leader's normal calendar app. The agent observes via subsequent reads and can propose corrections via chat if drift is detected.

## Consequences

- OAuth scopes per provider: `calendar.readonly` + `mail.send`.
- No event-management UX in the platform; less surface area to maintain, fewer permissions to ask for.
- Conflict avoidance is strong: agents see participants' full calendars during negotiation.
- Privacy is enforced at the agent boundary (ADR 0004), not at the OAuth scope.
- Edge case: declines after invite-send trigger a re-negotiation round (ADR 0006 deadlock flow).
