# 0004. Privacy granularity — directional per-edge filter

**Status:** Accepted (principle); concrete level definitions TBD
**Date:** 2026-04-26

## Context

Privacy can't be a global toggle. Chip is willing to share full calendar details with his wife but only minimal information with a work peer. The model needs **per-edge directional filters**: for every (subject, viewer) pair, the subject configures what their agent reveals to the viewer's agent. Asymmetric is allowed by design (subject reveals more than viewer reveals back).

## Decision

**Directional per-relationship privacy filter.** For every (subject_user, viewer_user) pair where subject and viewer share at least one group, the subject configures a filter `level` that determines what subject's agent reveals to viewer's agent during negotiations.

Initial level enumeration (refinement expected):

| Level | Subject's agent reveals … |
|-------|---------------------------|
| `full_details` | Calendar events including titles, attendees, locations |
| `decision_only` | Only the time slots the agent considers acceptable for this meeting |
| `busy_only` | Time slots blocked vs. free, no event metadata |

**Default for any new (subject, viewer) pair: `decision_only`.** Subject overrides per-relationship in settings.

The filter applies whenever subject's agent emits a `FREE_BUSY` (or analogous) message destined for viewer's agent.

## Consequences

- Data model: a `privacy_policy(subject_user, viewer_user, level)` record (or per-user privacy doc keyed by viewer).
- Agent protocol: every outbound message is filtered at send-time by sender's per-recipient policy.
- UX: setup must include a relationship-management surface where subject sets per-viewer levels. Defaults must be safe.
- Future refinement: tighter filters (calendar-specific exclusions, time-of-day rules, per-group overrides) can layer on top of this model without breaking it.
- Cost: more rounds of negotiation may be needed when many edges are at `decision_only` and constraints are tight.
