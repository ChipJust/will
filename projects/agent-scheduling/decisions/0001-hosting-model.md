# 0001. Hosting model — centralized vs. federated

**Status:** Proposed
**Date:** 2026-04-26

## Context

The chat server, agent runtime, and PWA client need to live somewhere. Two main shapes:

- **Centralized.** One server hosts the chat rooms and (optionally) all agent processes. Cohort members join as clients.
- **Federated.** Each user runs their own agent (and possibly their own server). Rooms are pub/sub topics shared across servers.

Forces:
- The cohort is 7 people; centralized is operationally simplest.
- Federated reduces server-side trust burden (calendar tokens, message contents) and aligns with the "privacy by default" non-functional requirement.
- Mobile-first UX makes self-hosting per user impractical without a managed option.
- Cost: a single small VPS handles 7 users centrally; federated multiplies that, though the per-user agent could run on the user's own laptop intermittently.
- Any future "wider than this cohort" scope (still an open requirements question) tilts toward federated; cohort-only tilts toward centralized.

## Decision

*TBD — pending requirements close-out on auth, privacy granularity, and per-user trust assumptions.*

## Consequences

*TBD.*
