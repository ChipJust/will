# 0002. Auth and identity — OAuth-first, invite-link group binding

**Status:** Accepted
**Date:** 2026-04-26

## Context

Per ADR 0001, we host. Users need to sign in fast and bind their email/calendar APIs simultaneously. A separate password layer is friction without value when OAuth identity is already established. Group membership has to feel like "click invite, you're in."

## Decision

**OAuth-first.** First supported provider: Google (Gmail + Calendar). Add additional providers per ADR 0007 as adapters are built. The OAuth identity is the user's account.

**Invite links** mediate group membership. A new user clicking a group invite triggers OAuth on first sign-in and binds the account to the group atomically.

A single user may have multiple linked OAuth identities (personal + work); see ADR 0007 for the per-provider adapter model.

## Consequences

- No password storage.
- Account portability and multi-identity support are first-class.
- Every supported provider must offer an OAuth flow. Closed-ecosystem providers may force fallback adapters (e.g. CalDAV-paste, manual ICS), flagged as a gap.
- Invite-link security: links must be single-use or short-lived to avoid replay; group admins can revoke.
