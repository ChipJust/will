# 0001. Hosting model — multi-tenant cloud

**Status:** Accepted
**Date:** 2026-04-26

## Context

Scope was originally framed as cohort-only. Resolved 2026-04-26: this is the **first of multiple** use cases (cohort, marriage, work circle, etc.). Onboarding non-technical users (e.g., Chip's wife) must be effectively zero-ceremony — she "glazed over really fast" when walked through a self-hosted setup. Group membership data needs central storage so members can be hooked up via simple invites. Federated/self-hosted operation may revisit later, but does not fit the onboarding bar today.

## Decision

**Multi-tenant cloud hosting.** The platform hosts:
- User accounts and identities (OAuth-bound).
- Groups, group memberships, privacy policies.
- Per-user agent runtimes.
- Chat-server persistence for negotiation rooms.
- Per-user OAuth refresh tokens for email/calendar APIs (encrypted at rest).

User calendar and email data live in their existing apps and are accessed via API; we never duplicate that data server-side beyond what's needed for an in-flight negotiation.

## Consequences

- Onboarding: invite-link → OAuth → in. One sign-in covers all groups a user belongs to.
- Server-side trust is heightened — we hold OAuth refresh tokens and chat content. Encrypt at rest; declare retention; treat E2E for chat as a v2 question.
- Data model: every record carries `group_id` scoping.
- Cost: a small VPS handles the prototype-and-cohort scale; scale linearly.
- Federation/self-hosting deferred. Revisit if usage demands it.
- Sets the stage for separating `will` (Chip's meta-agent) from the deployed application repo when this graduates.
