# 0007. Email + calendar adapters — pluggable per-user-per-provider

**Status:** Accepted (principle); concrete adapters TBD
**Date:** 2026-04-26

## Context

Users have multiple email/calendar providers: personal Gmail, work email with conditional access (Chip's case), Outlook consumer, and others. The platform must reach all of them. Discovery is incremental — Chip flagged that "we will probably need to connect to" each method we encounter, so the architecture must absorb new providers without churn.

A user may use different identities for different groups (work email for the work circle, personal for cohort/marriage).

## Decision

**Pluggable adapter interface, per-user-per-provider.** Each user can register one or more adapters. Each adapter implements a narrow interface:

```python
class EmailCalendarAdapter(Protocol):
    def list_calendar_events(self, window: TimeWindow) -> list[Event]: ...
    def send_invite(self, invite: MeetingInvite) -> InviteResult: ...
    def get_send_address(self) -> str: ...
    def health(self) -> AdapterHealth: ...
```

The agent picks which adapter to use per-meeting (e.g., "send the work meeting from work email; the cohort meeting from personal").

**First implementation:** Google (Gmail + Calendar) via OAuth + Google API client.

**Subsequent implementations:** added on demand. Candidates: Outlook consumer, Outlook work (conditional access), Apple Calendar (CalDAV), manual-ICS-paste fallback for closed ecosystems.

## Consequences

- One user, multiple adapters. Per-group default adapter, per-meeting override allowed.
- Discovery is incremental: each new provider = a new adapter, not a refactor.
- Adapter health surfaces as setup-needed in the UI when auth is broken.
- Test strategy: a `MockAdapter` for unit/integration tests; real-API tests gated by env credentials in a separate CI job.
- Work-email adapters may have stricter constraints (conditional access, restricted scopes, IT review). The architecture absorbs this by treating each as an isolated adapter.
