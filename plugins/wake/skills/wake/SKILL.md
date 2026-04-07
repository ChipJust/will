---
name: wake
description: Session start skill. Use when the user says "wake", "wake up", "pick up where we left off", "/wake", or opens a session and wants to re-establish context. Loads will system context then subject-repo context, presents a two-layer briefing, and helps triage next steps.
argument-hint: [repo-name]
version: 1.1.0
---

# Skill: /wake — Session Start Review

Run this at the start of any session to re-establish context and agree on what to work on.

Every briefing has two layers:
1. **System context** — from `will/HANDOFF.md` — the architecture and cross-cutting state
2. **Repo context** — from the subject repo's `HANDOFF.md` — the thinking frame and next steps

---

## Step 1 — Identify the repo

Determine which repo we're working in:
- If a repo name was passed as an argument, use that
- Otherwise detect from the current working directory

If we're in `will` itself, skip Layer 2 — Layer 1 is the only context needed.

---

## Step 2 — Load Layer 1: System context

Read `D:\_code\will\HANDOFF.md`.

Extract:
- Current state of the repo ecosystem
- Cross-cutting concerns (Python version, encoding, commit conventions, etc.)
- Open system-level items

---

## Step 3 — Load Layer 2: Repo context

Read `D:\_code\<repo>\HANDOFF.md`.

Extract:
- Thinking frame from the last session in this repo
- Open next steps: "Agent can start immediately" and "Needs Chip"

If HANDOFF.md does not exist in the subject repo:
- Note it — this means `/reflect` was never run here
- Fall back to the most recent reflection from `will-personal/reflections/`:
  ```
  ls D:\_code\will-personal\reflections\ | grep <repo> | sort | tail -1
  ```
- Suggest writing a HANDOFF.md at end of this session via `/reflect`

---

## Step 4 — Present the briefing

Output a concise briefing in this structure:

```
## Session Brief — <Repo> — <Date>

### System
<2-3 bullet points from will/HANDOFF.md that are relevant to this session>
<Any open system-level items that touch this repo>

### This repo
**Thinking frame:** <1-2 sentences — the mental model to carry into this session>

**Open next steps:**

Agent can start immediately:
- [ ] <item>

Needs Chip:
- [ ] <item>

**Suggested starting point:**
<One sentence: highest-value item the agent can do without blocking on Chip>
```

Keep it short. This is a brief, not a report. The System section should be 3 lines max
unless there's something directly relevant to the work at hand.

---

## Step 5 — Triage with Chip

After presenting the brief, ask:

> "Want to start there, or is there something else on your mind for this session?"

Then wait. Let Chip redirect if needed. Do not propose a plan or start work until he confirms direction.

Once direction is confirmed:
- If working through the next steps list: start on the first item
- If a new direction: note that the existing next steps are on hold and focus on the new thing

---

## Step 6 — Update HANDOFF.md after triage (optional)

If Chip explicitly closes out items during triage ("that's done", "drop that one"),
update the subject repo's HANDOFF.md before starting work:
```
cd D:\_code\<repo> && git add HANDOFF.md && git commit -m "Update handoff: triage YYYY-MM-DD" && git push
```

---

## Notes

- Fast — should take under a minute
- System section is context, not a task list — don't let it derail the session
- If either HANDOFF.md is stale or missing, flag it and suggest `/reflect` at session end
- For mid-session next-steps review: `/reflect review`
