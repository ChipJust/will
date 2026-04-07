---
name: wake
description: Session start skill. Use when the user says "wake", "wake up", "pick up where we left off", "/wake", or opens a session and wants to re-establish context. Reads HANDOFF.md and the most recent reflection, presents the current state, and helps triage next steps.
argument-hint: [repo-name]
version: 1.0.0
---

# Skill: /wake — Session Start Review

Run this at the start of any session to re-establish context and agree on what to work on.

---

## Step 1 — Identify the repo

Determine which repo we're working in:
- If a repo name was passed as an argument, use that
- Otherwise detect from the current working directory

---

## Step 2 — Load context

Read the following in order:

**a) HANDOFF.md** in the current repo (e.g. `D:\_code\<repo>\HANDOFF.md`):
- Thinking frame from the last session
- Open next steps split into "Agent can do immediately" and "Needs Chip"

If HANDOFF.md does not exist, note it and skip to the reflection.

**b) Most recent reflection** from `D:\_code\will-personal\reflections\`:
```
ls D:\_code\will-personal\reflections\ | grep <repo> | sort | tail -1
```
Read it and extract the **Next Steps** section. This may have more detail or newer
items than HANDOFF.md if they diverged.

---

## Step 3 — Present the briefing

Output a concise briefing in this structure:

```
## Session Brief — <Repo> — <Date>

**Thinking frame:**
<1-3 sentences from the Handoff — the mental model to carry into this session>

**Open next steps:**

Agent can start immediately:
- [ ] <item>

Needs Chip:
- [ ] <item>

**Suggested starting point:**
<One sentence: what to tackle first and why — pick the highest-value item the agent can do without blocking on Chip>
```

Keep it short. This is a brief, not a report.

---

## Step 4 — Triage with Chip

After presenting the brief, ask:

> "Want to start there, or is there something else on your mind for this session?"

Then wait. Let Chip redirect if needed. Do not propose a plan or start work until he confirms the direction.

Once direction is confirmed:
- If working through the next steps list: start on the first item, mark it in progress
- If a new direction: note that the existing next steps are on hold and focus on the new thing

---

## Step 5 — Update HANDOFF.md after triage (optional)

If Chip explicitly closes out items during triage ("that's done", "drop that one"),
update HANDOFF.md to reflect the new state before starting work:
```
cd D:\_code\<repo> && git add HANDOFF.md && git commit -m "Update handoff: triage YYYY-MM-DD" && git push
```

---

## Notes

- This skill is fast — it should take under a minute to run
- The goal is to re-establish the thinking frame and agree on direction, not to do a full review
- If HANDOFF.md is stale or missing, suggest running `/reflect` at the end of this session to regenerate it
- For a deeper mid-session review of next steps, use `/reflect review`
