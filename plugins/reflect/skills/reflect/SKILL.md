---
name: reflect
description: End-of-session reflection skill. Use when the user says "reflect", "end of session", "wrap up", "/reflect", or asks to write a session summary or reflection note. Also handles mid-session review when user says "review", "update next steps", or "/reflect review". Writes a dated reflection file to will-personal and updates memory.
argument-hint: [repo-name] [review]
version: 1.1.0
---

# Skill: /reflect — End-of-Session Reflection + Mid-Session Review

Two modes:
- **End of session** (`/reflect [repo]`): Write a full reflection, carry forward open next steps.
- **Mid-session review** (`/reflect review`): Update the running Next Steps list for this session without writing a new reflection.

---

## Step 0 — Load prior context (both modes)

Find the most recent reflection for this repo in `D:\_code\will-personal\reflections\`:
```
ls D:\_code\will-personal\reflections\ | grep <repo> | sort | tail -1
```

Read it and extract:
1. **Handoff to Next Agent** — re-establishes the thinking frame for this session
2. **Next Steps** — the carried-forward action list from the prior session

These two sections together are the **running next steps** for the current session.
Hold them in context. They inform both review and end-of-session reflection.

If no prior reflection exists for this repo, start fresh with an empty Next Steps list.

---

## If mode = review (`/reflect review`)

Update the Next Steps section of the **current session's reflection file** if one already
exists for today. If no reflection has been written yet for today, write the running next
steps to a scratch note at `D:\_code\will-personal\reflections\<date>-<repo>-next-steps.md`.

For each item in the running Next Steps list, determine its current status:
- **Done** — completed this session → mark `[x]` and note what was done
- **Dismissed** — no longer relevant → remove it
- **In progress** — partially done → update the description to reflect current state
- **Still open** — unchanged → carry forward as-is

Then add any new items that surfaced since the last review.

Output the updated list to the file. Do not write a full reflection. Commit the update:
```
cd D:\_code\will-personal && git add reflections/ && git commit -m "Update next steps: YYYY-MM-DD <repo>" && git push
```

---

## If mode = end of session (`/reflect [repo]`)

### Step 1 — Determine context

- What repo were we working in? (default: detect from current working directory)
- What date is it? (use today's date from context)
- Output file: `D:\_code\will-personal\reflections\YYYY-MM-DD-<repo>.md`
  - If a file for today's date and repo already exists, append a `-2` suffix

---

### Step 2 — Write the reflection file

Use this structure:

```markdown
# Session Reflection — <Repo Name>
**Date:** YYYY-MM-DD
**Repo:** `<repo>` (ChipJust/<repo>)

## What Was Built / Decided
<Bullet list of concrete outputs: files created, features added, decisions made>

## What Worked Well
<What to repeat in future sessions>

## What Could Be Improved
<Friction points, wrong assumptions, things that slowed us down>

## Decisions Made
<Non-obvious choices that future sessions should know about, with brief rationale>

## Things to Follow Up
- [ ] <Unfinished items or questions that surfaced>

## System Observations
<Anything about how the Claude Code system itself (skills, memory, hooks, tooling)
 could be improved based on this session>

## Handoff to Next Agent
<This is the most important section. Write it directly to the next Claude agent
that will work in this repo. Capture:
- The thinking frame that made this session productive — not just what was built
  but how to *think* about this space
- What the user responds well to (specific framing, level of detail, initiative)
- Anti-patterns to avoid (e.g. "don't propose to rebuild X — it already exists")
- The design philosophy of key systems, in a sentence each
- Any implicit contract established this session that isn't written elsewhere

This section should let the next agent pick up mid-thought, not start over.>

## Next Steps
<Build this section in two passes:

Pass 1 — carry forward from prior session's Next Steps:
- Items marked [x] (done) or explicitly dismissed → drop them
- Items still open or in progress → carry forward, updating description if state changed

Pass 2 — scan session context with Handoff notes in mind:
- What new actionable items surfaced this session?
- What did we leave half-done?
- What gaps in the system did we notice but not fix?

Split the final list into:

**Agent can do immediately:**
- [ ] <Tasks the next agent can start without asking>

**Needs Chip:**
- [ ] <Items requiring a decision, credential, or confirmation>

**Structural notes:**
- <Observations about the system — stale files, missing ORIENTATION.md, superseded reflections, etc.>

Be specific. Vague items belong in Things to Follow Up. This is the startup checklist for the next session.>
```

Be specific and honest. Future sessions will read this to re-establish context.
Avoid generic statements like "the session went well."
The Handoff section is the most important for continuity; Next Steps is the immediate action list.

---

### Step 3 — Update memory

After writing the reflection, review whether any memory files need updating:

- Did you learn something new about how Chip prefers to work? → `feedback_*.md`
- Did the project state change significantly? → `project_*.md`
- Did you discover a new tool, convention, or preference? → appropriate memory type

Update or create memory files as needed. Do not duplicate what's already in memory.

---

### Step 4 — Update PLAN.md in will repo

If the session revealed a gap in the system architecture, a new repo is needed, or a
problem was logged or resolved, update `D:\_code\will\PLAN.md` accordingly:
- Add to revision history table
- Update repo status if applicable
- Add or close items in the open problems section

---

### Step 5 — Commit the reflection

```
cd D:\_code\will-personal && git add reflections/ && git commit -m "Add session reflection: YYYY-MM-DD <repo>" && git push
```

---

## Notes

- Reflections live in `D:\_code\will-personal\reflections\` (private repo), not will (public)
- If will-personal isn't cloned on this machine, flag it and write the reflection
  to a temp location, noting where it should go
- Reflections accumulate into an institutional memory of how the system was built
  and why — treat them as first-class artifacts
- The running Next Steps list is the thread of continuity across sessions —
  it should never be blank at the start of a session if prior reflections exist
