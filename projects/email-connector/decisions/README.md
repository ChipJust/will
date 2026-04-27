# Architecture Decision Records (ADRs)

One file per load-bearing decision. Format: Michael Nygard's lightweight ADR.

## Naming

`NNNN-short-kebab-title.md` — zero-padded, monotonic. Example: `0001-hosting-model.md`, `0002-calendar-write-scope.md`.

## Template

```markdown
# NNNN. <Decision title>

**Status:** Proposed | Accepted | Superseded by NNNN | Deprecated
**Date:** YYYY-MM-DD

## Context

What is the situation that demands a decision? What forces are at play (technical, organizational, political)?

## Decision

The choice we made, in one or two sentences. Active voice — "We will …".

## Consequences

What becomes easier? What becomes harder? What new constraints does this impose? What did we give up?
```

## When to write one

A decision warrants an ADR when:
- Reversing it later is expensive.
- A future contributor would reasonably ask "why this and not the obvious alternative?"
- It commits the project to a particular vendor, protocol, or model.

A decision does *not* need an ADR when it's local, easily reversed, and obvious from the code.

## Lifecycle

- A decision starts as `Proposed`. Reference it from `04-design.md` while it's open.
- When committed to, change status to `Accepted` and stamp the date.
- Never edit an Accepted ADR's Decision section. If it changes, write a new ADR with `Status: Supersedes NNNN` and update the old one to `Status: Superseded by NNNN`.
