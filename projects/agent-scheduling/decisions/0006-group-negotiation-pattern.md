# 0006. Group negotiation — batch-first, deadlock via targeted chat asks

**Status:** Accepted
**Date:** 2026-04-26

## Context

The cohort's monthly schedule is a batch: 1 full-cohort meeting + N triad meetings, with overlapping memberships. Optimizing one meeting at a time misses inter-meeting interdependencies — the whole point of this push is to navigate those interdependencies optimally. The protocol must be batch-aware.

When the solver fails to find a fully-satisfying schedule, the question is how to break ties without bouncing the user-experience back to "everyone please reply manually." Chip's resolution: target the chat ask at the **users whose constraints are most binding**, with concrete suggestions ("if you could skip this one"), and **mine those exchanges post-negotiation to update preferences**.

## Decision

### Batch-first negotiation primitive

A `BATCH_SCHEDULE` request initiates a negotiation over multiple meetings with shared participants. Agents collectively run a constraint-satisfaction solver across the batch, weighted by user preferences from each agent's context store.

Single-meeting negotiation is a degenerate case — `BATCH_SCHEDULE` with batch size 1.

The batch output is a set of meeting proposals; each proposal has a designated source-account (decided during negotiation, typically the leader/owner of that meeting) for sending the invite.

### Deadlock resolution

When the solver cannot satisfy all hard constraints:

1. **Identify** the user(s) whose constraints are most binding via the solver's slack analysis.
2. **Surface** a targeted ask in the group chat ("could user X skip meeting M, or shift their constraint Y?"). Targeted at the binding user(s), visible to all.
3. **Wait** a configurable window (default: 24h).
4. **Re-solve** if a relaxation is offered. If not, propose the best-available partial solution.
5. **Mine** the chat exchanges from this negotiation post-completion: feed into the LLM bridge with each user's context, extract preference updates, write back to the user's agent context store.

### Pre-negotiation preparation

Per the cohort flow: users mark **tentative-accept** on their calendars ahead of the cohort meeting (where the next month's batch is scheduled). This gives agents accurate read input.

## Consequences

- Solver handles meeting-time selection AND source-account selection in a single pass.
- Chat is part of the negotiation loop, not just a UI surface.
- Preference learning is built into the deadlock path — the system gets smarter the more it negotiates.
- Solver complexity: tractable for cohort scale (≤ ~25 meetings/batch); revisit if scale changes.
- A declined invite post-send is a re-negotiation trigger, going through the same deadlock flow.
